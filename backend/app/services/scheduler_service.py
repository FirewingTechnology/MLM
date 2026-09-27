import asyncio
import logging
import datetime
from collections import deque
from typing import Dict, Any, List, Optional
from datetime import time
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.time_service import time_provider, IST
from app.services.daily_reward_service import daily_reward_service, SettlementTimingError
from app.services.backup_service import BackupService
from app.services.excel_backup_service import excel_backup_service
from app.services.audit_service import log_action

logger = logging.getLogger("mlm.scheduler")

class ScheduledJob:
    def __init__(
        self,
        job_id: str,
        name: str,
        description: str,
        schedule_display: str,
        enabled: bool = True
    ):
        self.job_id = job_id
        self.name = name
        self.description = description
        self.schedule_display = schedule_display
        self.enabled = enabled
        self.last_run_at: Optional[str] = None
        self.next_run_at: Optional[str] = None
        self.last_status: str = "PENDING"  # PENDING, SUCCESS, FAILED, RUNNING
        self.last_message: Optional[str] = None
        self.last_duration_ms: Optional[int] = None
        self.run_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "description": self.description,
            "schedule_display": self.schedule_display,
            "enabled": self.enabled,
            "last_run_at": self.last_run_at,
            "next_run_at": self.next_run_at,
            "last_status": self.last_status,
            "last_message": self.last_message,
            "last_duration_ms": self.last_duration_ms,
            "run_count": self.run_count
        }


class BackgroundSchedulerService:
    """Asynchronous background scheduler for automated recurring platform operations.
    Handles:
    - 07:00 AM IST Daily Package Refund / Reward Settlement
    - 05:00 AM IST Nightly Multi-Sheet Excel & Database Backups
    - 8-Hour Slot Volume & Binary Settlement Maintenance
    """

    def __init__(self):
        self.is_running: bool = False
        self.enabled: bool = True
        self._task: Optional[asyncio.Task] = None
        self.history: deque = deque(maxlen=50)

        # Registered Jobs
        self.jobs: Dict[str, ScheduledJob] = {
            "daily_reward_settlement": ScheduledJob(
                job_id="daily_reward_settlement",
                name="Daily Package Refund Settlement",
                description="Credits eligible daily package refund increments (INR 50 base + INR 50/pair) to member wallets at 07:00 AM IST.",
                schedule_display="Daily at 07:00:00 AM IST",
                enabled=True
            ),
            "automated_backup": ScheduledJob(
                job_id="automated_backup",
                name="Automated Database & Excel Backup",
                description="Creates consistent point-in-time database snapshot and multi-sheet Excel (.xlsx) archive.",
                schedule_display="Daily at 05:00:00 AM IST",
                enabled=True
            ),
            "slot_settlement_maintenance": ScheduledJob(
                job_id="slot_settlement_maintenance",
                name="Slot Volume Settlement Maintenance",
                description="Checks and settles binary volume ledgers at slot boundaries (00:00, 08:00, 16:00 IST).",
                schedule_display="Every 8 Hours (00:00, 08:00, 16:00 IST)",
                enabled=True
            )
        }

        # Track dates executed to prevent multiple runs on same day
        self._last_reward_settled_date: Optional[datetime.date] = None
        self._last_backup_date: Optional[datetime.date] = None

    def start(self):
        """Starts background worker task inside FastAPI event loop."""
        if self.is_running:
            return
        self.is_running = True
        self.enabled = True
        self._update_next_runs()
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("[Scheduler] Background scheduler worker started successfully.")

    def stop(self):
        """Gracefully cancels the background worker task."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("[Scheduler] Background scheduler worker stopped.")

    def toggle(self, enabled: bool) -> bool:
        self.enabled = enabled
        return self.enabled

    def get_status(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """Returns comprehensive status, job states, and execution history."""
        close_db = False
        if not db:
            db = SessionLocal()
            close_db = True

        try:
            current_ist = time_provider.get_current_ist_time(db)
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            self._update_next_runs(current_ist)

            return {
                "is_running": self.is_running,
                "is_enabled": self.enabled,
                "current_time_utc": now_utc.isoformat(),
                "current_time_ist": current_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                "total_jobs": len(self.jobs),
                "jobs": [job.to_dict() for job in self.jobs.values()],
                "history": list(self.history)
            }
        finally:
            if close_db:
                db.close()

    def _update_next_runs(self, current_ist: Optional[datetime.datetime] = None):
        """Calculates next projected execution timestamps for each job."""
        if not current_ist:
            now = datetime.datetime.now(IST)
        else:
            now = current_ist

        today = now.date()

        # 1. Daily Reward Settlement (07:00 AM IST)
        target_7am = datetime.datetime.combine(today, time(7, 0, 0), tzinfo=IST)
        if now >= target_7am:
            next_reward = target_7am + datetime.timedelta(days=1)
        else:
            next_reward = target_7am
        self.jobs["daily_reward_settlement"].next_run_at = next_reward.strftime("%Y-%m-%d %H:%M:%S IST")

        # 2. Automated Backup (05:00 AM IST)
        target_5am = datetime.datetime.combine(today, time(5, 0, 0), tzinfo=IST)
        if now >= target_5am:
            next_backup = target_5am + datetime.timedelta(days=1)
        else:
            next_backup = target_5am
        self.jobs["automated_backup"].next_run_at = next_backup.strftime("%Y-%m-%d %H:%M:%S IST")

        # 3. Slot Settlement Maintenance (00:00, 08:00, 16:00 IST)
        slot_hours = [0, 8, 16]
        next_slot = None
        for h in slot_hours:
            target_slot = datetime.datetime.combine(today, time(h, 0, 0), tzinfo=IST)
            if target_slot > now:
                next_slot = target_slot
                break
        if not next_slot:
            next_slot = datetime.datetime.combine(today + datetime.timedelta(days=1), time(0, 0, 0), tzinfo=IST)
        self.jobs["slot_settlement_maintenance"].next_run_at = next_slot.strftime("%Y-%m-%d %H:%M:%S IST")

    async def _scheduler_loop(self):
        """Infinite async tick loop that polls every 20 seconds."""
        logger.info("[Scheduler] Polling loop entered.")
        while self.is_running:
            try:
                if self.enabled:
                    await self._evaluate_and_run_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Scheduler] Error during polling tick: {e}", exc_info=True)

            try:
                await asyncio.sleep(20)
            except asyncio.CancelledError:
                break

    async def _evaluate_and_run_jobs(self):
        """Evaluates whether any registered job is due to execute."""
        db = SessionLocal()
        try:
            current_ist = time_provider.get_current_ist_time(db)
            today_ist = current_ist.date()
            current_time = current_ist.time()

            # 1. Daily Package Refund Settlement (at or after 07:00 AM IST)
            reward_job = self.jobs["daily_reward_settlement"]
            if reward_job.enabled:
                if current_time >= time(7, 0, 0) and self._last_reward_settled_date != today_ist:
                    logger.info("[Scheduler] Triggering scheduled Daily Reward Settlement for date %s", today_ist)
                    await self.run_job_async("daily_reward_settlement", db=db, force=False)
                    self._last_reward_settled_date = today_ist

            # 2. Automated Backup (at or after 05:00 AM IST)
            backup_job = self.jobs["automated_backup"]
            if backup_job.enabled:
                if current_time >= time(5, 0, 0) and self._last_backup_date != today_ist:
                    logger.info("[Scheduler] Triggering scheduled Automated Backup for date %s", today_ist)
                    await self.run_job_async("automated_backup", db=db)
                    self._last_backup_date = today_ist

            self._update_next_runs(current_ist)
        finally:
            db.close()

    async def run_job_async(
        self,
        job_id: str,
        db: Optional[Session] = None,
        admin_id: Optional[int] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """Executes a job asynchronously and records execution history."""
        if job_id not in self.jobs:
            raise ValueError(f"Unknown scheduled job: {job_id}")

        job = self.jobs[job_id]
        close_db = False
        if not db:
            db = SessionLocal()
            close_db = True

        start_time = datetime.datetime.now(datetime.timezone.utc)
        job.last_status = "RUNNING"
        job.last_run_at = start_time.isoformat()

        status = "SUCCESS"
        result_message = ""
        details = {}

        try:
            if job_id == "daily_reward_settlement":
                summary = daily_reward_service.settle_daily_rewards(db, force=force)
                db.commit()
                credited = summary.get('credited_count', 0)
                amount = summary.get('total_credited_amount', 0.0)
                result_message = f"Daily Refund Settled: {credited} cycles credited (INR {amount:,.2f})."
                details = summary
                self._last_reward_settled_date = summary.get('business_date')

            elif job_id == "automated_backup":
                # Create SQLite backup
                try:
                    BackupService.create_database_backup(admin_id=admin_id, notes="Automated Scheduled SQLite Backup")
                except Exception:
                    pass
                # Create Excel backup
                _, fn, meta = excel_backup_service.export_database_to_excel(
                    db,
                    admin_id=admin_id,
                    notes="Automated Scheduled Excel Backup",
                    save_copy_to_disk=True
                )
                db.commit()
                result_message = f"Automated Backup Created: {fn} ({meta['total_records']} rows, {meta['size_mb']} MB)."
                details = meta
                self._last_backup_date = datetime.datetime.now(IST).date()

            elif job_id == "slot_settlement_maintenance":
                # Run slot volume check and binary settlement
                from app.services.time_service import slot_service
                settlement_result = slot_service.settle_current_slot(db)
                db.commit()
                pairs_settled = len(settlement_result.get('settlements', []))
                result_message = f"Slot Maintenance Complete: {pairs_settled} user slot settlements evaluated."
                details = settlement_result

        except SettlementTimingError as ste:
            status = "SKIPPED"
            result_message = str(ste)
            details = {"notice": str(ste)}
        except Exception as e:
            db.rollback()
            status = "FAILED"
            result_message = f"Execution error: {str(e)}"
            logger.error(f"[Scheduler] Job {job_id} failed: {e}", exc_info=True)
            details = {"error": str(e)}
        finally:
            end_time = datetime.datetime.now(datetime.timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            job.last_status = status
            job.last_message = result_message
            job.last_duration_ms = duration_ms
            job.run_count += 1

            history_entry = {
                "id": f"{job_id}-{int(start_time.timestamp())}",
                "job_id": job_id,
                "job_name": job.name,
                "status": status,
                "started_at": start_time.isoformat(),
                "duration_ms": duration_ms,
                "message": result_message,
                "triggered_by": f"Admin #{admin_id}" if admin_id else "Scheduler"
            }
            self.history.appendleft(history_entry)

            # Audit log
            try:
                log_action(
                    db,
                    'SCHEDULED_JOB_EXECUTED',
                    'System',
                    None,
                    admin_id,
                    {
                        'job_id': job_id,
                        'status': status,
                        'duration_ms': duration_ms,
                        'message': result_message
                    }
                )
                db.commit()
            except Exception:
                pass

            if close_db:
                db.close()

        return {
            "success": status in ("SUCCESS", "SKIPPED"),
            "status": status,
            "job_id": job_id,
            "message": result_message,
            "duration_ms": duration_ms,
            "details": details
        }

scheduler_service = BackgroundSchedulerService()
