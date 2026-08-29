import os
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.audit_service import log_action

class BackupService:
    @staticmethod
    def get_db_file_path() -> Optional[str]:
        if settings.DATABASE_URL.startswith("sqlite:///"):
            raw_path = settings.DATABASE_URL.replace("sqlite:///", "")
            return os.path.abspath(raw_path)
        return None

    @staticmethod
    def create_database_backup(admin_id: Optional[int] = None, notes: str = "") -> Dict[str, Any]:
        """Creates a consistent, live, transactional SQLite backup using SQLite's native backup API.
        Does not block concurrent readers and captures an exact point-in-time snapshot."""
        db_file = BackupService.get_db_file_path()
        if not db_file or not os.path.exists(db_file):
            raise FileNotFoundError(f"Database file not found at: {settings.sanitized_db_path}")

        # Ensure backup directory exists
        backup_dir = os.path.abspath(settings.BACKUP_DIR)
        os.makedirs(backup_dir, exist_ok=True)

        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp_str = now.strftime("%Y-%m-%d-%H-%M-%S")
        backup_filename = f"mlm-backup-{timestamp_str}.sqlite3"
        backup_dest_path = os.path.join(backup_dir, backup_filename)

        # Use SQLite Online Backup API for 100% consistent live snapshot
        src_conn = sqlite3.connect(db_file)
        try:
            # Checkpoint WAL first to flush committed transactions
            try:
                src_conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
            except Exception:
                pass

            dest_conn = sqlite3.connect(backup_dest_path)
            try:
                with dest_conn:
                    src_conn.backup(dest_conn, pages=100, sleep=0.01)
            finally:
                dest_conn.close()
        finally:
            src_conn.close()

        size_bytes = os.path.getsize(backup_dest_path) if os.path.exists(backup_dest_path) else 0

        # Structured audit log
        try:
            from app.database import SessionLocal
            db = SessionLocal()
            try:
                log_action(
                    db,
                    'DATABASE_BACKUP_CREATED',
                    'System',
                    None,
                    admin_id,
                    {
                        'backup_filename': backup_filename,
                        'size_bytes': size_bytes,
                        'notes': notes,
                        'timestamp': now.isoformat()
                    }
                )
                db.commit()
            finally:
                db.close()
        except Exception:
            pass

        return {
            "success": True,
            "filename": backup_filename,
            "sanitized_path": Path(backup_dest_path).as_posix(),
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "created_at": now.isoformat(),
            "notes": notes
        }

    @staticmethod
    def list_backups() -> List[Dict[str, Any]]:
        """Returns a list of all existing database backups in descending chronological order."""
        backup_dir = os.path.abspath(settings.BACKUP_DIR)
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for fname in os.listdir(backup_dir):
            if fname.endswith(".sqlite3") or fname.endswith(".db"):
                fpath = os.path.join(backup_dir, fname)
                if os.path.isfile(fpath):
                    stat = os.stat(fpath)
                    created_dt = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc)
                    backups.append({
                        "filename": fname,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": created_dt.isoformat()
                    })

        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

backup_service = BackupService()
