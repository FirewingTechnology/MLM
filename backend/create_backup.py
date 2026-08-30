"""
Database Snapshot Utility
-------------------------
Creates an instant, 100% consistent point-in-time backup snapshot of the
active SQLite database using SQLite's native live backup API.

Usage:
    python create_backup.py [optional notes]
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.backup_service import BackupService

if __name__ == "__main__":
    notes = sys.argv[1] if len(sys.argv) > 1 else "Manual CLI snapshot"
    print(f"Creating database snapshot (Notes: '{notes}')...")
    try:
        res = BackupService.create_database_backup(notes=notes)
        print("\n[SUCCESS] Database snapshot created successfully!")
        print(f"  • File: {res['filename']}")
        print(f"  • Path: {res['sanitized_path']}")
        print(f"  • Size: {res['size_mb']} MB ({res['size_bytes']} bytes)")
        print(f"  • Timestamp: {res['created_at']}")
        
        print("\nRecent Backups:")
        backups = BackupService.list_backups()
        for b in backups[:5]:
            print(f"  - {b['filename']} ({b['size_mb']} MB, created {b['created_at']})")
    except Exception as e:
        print(f"\n[ERROR] Failed to create backup: {e}")
        sys.exit(1)
