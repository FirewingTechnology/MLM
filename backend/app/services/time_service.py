from dataclasses import dataclass
from datetime import datetime, timedelta, date, time
from zoneinfo import ZoneInfo
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.demo_time import DemoTimeConfig

try:
    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")

@dataclass
class SlotInfo:
    mode: str                    # 'REAL' or 'DEMO'
    timezone: str                # 'Asia/Kolkata'
    current_time: datetime       # Timezone-aware IST
    date_str: str                # 'YYYY-MM-DD'
    time_formatted: str          # '10:42:17 AM'
    slot_id: str                 # '2026-08-26-S1'
    slot_number: int             # 1 or 2
    slot_name: str               # 'SLOT 1' or 'SLOT 2'
    slot_start: datetime         # Timezone-aware IST
    slot_end: datetime           # Timezone-aware IST
    slot_start_formatted: str    # '12:00 AM'
    slot_end_formatted: str      # '12:00 PM'
    remaining_seconds: int       # e.g. 4663
    remaining_formatted: str     # '01:17:43'
    next_slot_id: str            # '2026-08-26-S2'

    def to_dict(self) -> dict:
        return {
            'mode': self.mode,
            'timezone': self.timezone,
            'current_time': self.current_time.isoformat(),
            'date': self.date_str,
            'time_formatted': self.time_formatted,
            'slot_id': self.slot_id,
            'slot_number': self.slot_number,
            'slot_name': self.slot_name,
            'slot_start': self.slot_start.isoformat(),
            'slot_end': self.slot_end.isoformat(),
            'slot_start_formatted': self.slot_start_formatted,
            'slot_end_formatted': self.slot_end_formatted,
            'remaining_seconds': self.remaining_seconds,
            'remaining_formatted': self.remaining_formatted,
            'next_slot_id': self.next_slot_id,
        }

class SlotService:
    @staticmethod
    def ensure_ist(dt: datetime) -> datetime:
        """Converts naive or foreign timezone datetimes into timezone-aware IST datetime."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=IST)
        return dt.astimezone(IST)

    @staticmethod
    def get_slot_number(dt: datetime) -> int:
        """
        Slot 1: 12:00 AM (00:00:00) to 12:00 PM (11:59:59.999)
        Slot 2: 12:00 PM (12:00:00) to 12:00 AM (23:59:59.999)
        """
        ist_dt = SlotService.ensure_ist(dt)
        if 0 <= ist_dt.hour < 12:
            return 1
        return 2

    @staticmethod
    def get_slot_id(dt: datetime) -> str:
        """Returns deterministic slot ID like '2026-08-26-S1' or '2026-08-26-S2'."""
        ist_dt = SlotService.ensure_ist(dt)
        slot_num = SlotService.get_slot_number(ist_dt)
        return f"{ist_dt.strftime('%Y-%m-%d')}-S{slot_num}"

    @staticmethod
    def get_slot_boundaries(dt: datetime) -> Tuple[datetime, datetime]:
        """Returns (slot_start, slot_end) as timezone-aware IST datetimes."""
        ist_dt = SlotService.ensure_ist(dt)
        slot_num = SlotService.get_slot_number(ist_dt)
        curr_date = ist_dt.date()

        if slot_num == 1:
            start = datetime.combine(curr_date, time(0, 0, 0), tzinfo=IST)
            end = datetime.combine(curr_date, time(12, 0, 0), tzinfo=IST)
        else:
            start = datetime.combine(curr_date, time(12, 0, 0), tzinfo=IST)
            next_day = curr_date + timedelta(days=1)
            end = datetime.combine(next_day, time(0, 0, 0), tzinfo=IST)

        return start, end

    @staticmethod
    def get_remaining_seconds(dt: datetime, slot_end: datetime) -> int:
        """Calculates remaining seconds until slot_end."""
        ist_dt = SlotService.ensure_ist(dt)
        ist_end = SlotService.ensure_ist(slot_end)
        remaining = int((ist_end - ist_dt).total_seconds())
        return max(0, remaining)

    @staticmethod
    def format_duration(seconds: int) -> str:
        """Formats seconds into HH:MM:SS string."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def get_next_slot_start(dt: datetime) -> datetime:
        """
        Returns the exact start datetime of the next 12-hour slot.
        If in S1 (e.g. 10:30 AM) -> today 12:00 PM (S2 start).
        If in S2 (e.g. 04:30 PM) -> tomorrow 12:00 AM (S1 start next day).
        """
        ist_dt = SlotService.ensure_ist(dt)
        slot_num = SlotService.get_slot_number(ist_dt)
        curr_date = ist_dt.date()

        if slot_num == 1:
            return datetime.combine(curr_date, time(12, 0, 0), tzinfo=IST)
        else:
            next_day = curr_date + timedelta(days=1)
            return datetime.combine(next_day, time(0, 0, 0), tzinfo=IST)

    @staticmethod
    def get_previous_slot_start(dt: datetime) -> datetime:
        """
        Returns the start datetime of the previous slot.
        If in S1 -> yesterday 12:00 PM (S2 start of previous day).
        If in S2 -> today 12:00 AM (S1 start of today).
        """
        ist_dt = SlotService.ensure_ist(dt)
        slot_num = SlotService.get_slot_number(ist_dt)
        curr_date = ist_dt.date()

        if slot_num == 1:
            prev_day = curr_date - timedelta(days=1)
            return datetime.combine(prev_day, time(12, 0, 0), tzinfo=IST)
        else:
            return datetime.combine(curr_date, time(0, 0, 0), tzinfo=IST)

    @staticmethod
    def get_slot_info(dt: datetime, mode: str = 'REAL') -> SlotInfo:
        """Builds a complete SlotInfo instance for the given datetime and mode."""
        ist_dt = SlotService.ensure_ist(dt)
        slot_num = SlotService.get_slot_number(ist_dt)
        slot_id = SlotService.get_slot_id(ist_dt)
        start, end = SlotService.get_slot_boundaries(ist_dt)
        remaining = SlotService.get_remaining_seconds(ist_dt, end)
        next_slot_dt = SlotService.get_next_slot_start(ist_dt)
        next_slot_id = SlotService.get_slot_id(next_slot_dt)

        start_fmt = "12:00 AM" if slot_num == 1 else "12:00 PM"
        end_fmt = "12:00 PM" if slot_num == 1 else "12:00 AM"

        return SlotInfo(
            mode=mode,
            timezone="Asia/Kolkata",
            current_time=ist_dt,
            date_str=ist_dt.strftime("%Y-%m-%d"),
            time_formatted=ist_dt.strftime("%I:%M:%S %p"),
            slot_id=slot_id,
            slot_number=slot_num,
            slot_name=f"SLOT {slot_num}",
            slot_start=start,
            slot_end=end,
            slot_start_formatted=start_fmt,
            slot_end_formatted=end_fmt,
            remaining_seconds=remaining,
            remaining_formatted=SlotService.format_duration(remaining),
            next_slot_id=next_slot_id
        )

class TimeProvider:
    @staticmethod
    def _get_config(db: Optional[Session]) -> Optional[DemoTimeConfig]:
        if db is None:
            return None
        try:
            return db.query(DemoTimeConfig).filter(DemoTimeConfig.id == 1).first()
        except Exception:
            return None

    @staticmethod
    def get_mode(db: Optional[Session] = None) -> str:
        cfg = TimeProvider._get_config(db)
        if cfg and cfg.mode == 'DEMO':
            return 'DEMO'
        return 'REAL'

    @staticmethod
    def get_current_ist_time(db: Optional[Session] = None) -> datetime:
        """
        Returns the application's current effective IST datetime.
        If mode is 'REAL', returns actual current IST time.
        If mode is 'DEMO', returns the configured virtual IST time.
        """
        cfg = TimeProvider._get_config(db)
        if cfg and cfg.mode == 'DEMO' and cfg.virtual_datetime is not None:
            return SlotService.ensure_ist(cfg.virtual_datetime)
        return datetime.now(IST)

    @staticmethod
    def get_current_slot_info(db: Optional[Session] = None) -> SlotInfo:
        """Returns the SlotInfo for the current effective time."""
        mode = TimeProvider.get_mode(db)
        current_dt = TimeProvider.get_current_ist_time(db)
        return SlotService.get_slot_info(current_dt, mode=mode)

    @staticmethod
    def set_demo_time(db: Session, target_dt: datetime, user_id: Optional[int] = None) -> SlotInfo:
        """Sets the application clock into DEMO mode with the specified virtual datetime."""
        ist_dt = SlotService.ensure_ist(target_dt)
        cfg = db.query(DemoTimeConfig).filter(DemoTimeConfig.id == 1).first()
        if not cfg:
            cfg = DemoTimeConfig(id=1, mode='DEMO', virtual_datetime=ist_dt.replace(tzinfo=None), updated_by=user_id)
            db.add(cfg)
        else:
            cfg.mode = 'DEMO'
            cfg.virtual_datetime = ist_dt.replace(tzinfo=None)
            cfg.updated_at = datetime.utcnow()
            cfg.updated_by = user_id
        db.commit()
        return TimeProvider.get_current_slot_info(db)

    @staticmethod
    def advance_demo_time(db: Session, minutes: int, user_id: Optional[int] = None) -> SlotInfo:
        """Advances demo clock by given minutes. If in REAL mode, sets demo mode starting from now + minutes."""
        current_dt = TimeProvider.get_current_ist_time(db)
        new_dt = current_dt + timedelta(minutes=minutes)
        return TimeProvider.set_demo_time(db, new_dt, user_id)

    @staticmethod
    def next_slot(db: Session, user_id: Optional[int] = None) -> SlotInfo:
        """Jumps demo clock to the beginning of the next slot."""
        current_dt = TimeProvider.get_current_ist_time(db)
        next_start = SlotService.get_next_slot_start(current_dt)
        return TimeProvider.set_demo_time(db, next_start, user_id)

    @staticmethod
    def previous_slot(db: Session, user_id: Optional[int] = None) -> SlotInfo:
        """Jumps demo clock to the beginning of the previous slot."""
        current_dt = TimeProvider.get_current_ist_time(db)
        prev_start = SlotService.get_previous_slot_start(current_dt)
        return TimeProvider.set_demo_time(db, prev_start, user_id)

    @staticmethod
    def reset_to_real_time(db: Session, user_id: Optional[int] = None) -> SlotInfo:
        """Resets the application clock back to live REAL TIME."""
        cfg = db.query(DemoTimeConfig).filter(DemoTimeConfig.id == 1).first()
        if not cfg:
            cfg = DemoTimeConfig(id=1, mode='REAL', virtual_datetime=None, updated_by=user_id)
            db.add(cfg)
        else:
            cfg.mode = 'REAL'
            cfg.virtual_datetime = None
            cfg.updated_at = datetime.utcnow()
            cfg.updated_by = user_id
        db.commit()
        return TimeProvider.get_current_slot_info(db)

# Singletons for convenient importing
slot_service = SlotService()
time_provider = TimeProvider()
