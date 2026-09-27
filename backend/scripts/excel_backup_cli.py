"""
Enterprise Excel Database Backup & Restoration CLI Utility
===========================================================
Supports exporting all 26 relational database tables into a structured Excel (.xlsx) file,
and restoring/populating an empty or crashed database from that Excel file.

Usage:
    # 1. Export database to Excel file
    python -m scripts.excel_backup_cli export [--output backup.xlsx] [--notes "Disaster recovery"]

    # 2. Restore database from Excel file
    python -m scripts.excel_backup_cli restore --file backup.xlsx [--overwrite]

    # 3. List existing backups
    python -m scripts.excel_backup_cli list
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, engine
from app.services.excel_backup_service import excel_backup_service

def main():
    parser = argparse.ArgumentParser(description="Partner Network Database Disaster Recovery CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: export
    p_export = subparsers.add_parser("export", help="Export full database to Excel (.xlsx)")
    p_export.add_argument("--output", type=str, help="Target output filepath (default: backend/data/backups/mlm_database_backup_<timestamp>.xlsx)")
    p_export.add_argument("--notes", type=str, default="CLI Manual Export", help="Notes or audit reason")

    # Subcommand: restore
    p_restore = subparsers.add_parser("restore", help="Restore / populate database from Excel (.xlsx)")
    p_restore.add_argument("--file", type=str, required=True, help="Path to source .xlsx backup file")
    p_restore.add_argument("--no-overwrite", action="store_true", help="Do not overwrite existing records with same ID")

    # Subcommand: list
    subparsers.add_parser("list", help="List all backup archives available in the backup directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    db = SessionLocal()
    try:
        if args.command == "export":
            print("[Excel Backup CLI] Exporting all 26 relational database tables to Excel...")
            content, filename, meta = excel_backup_service.export_database_to_excel(
                db=db,
                notes=args.notes,
                save_copy_to_disk=True
            )
            out_path = args.output or meta.get("disk_path")
            if args.output:
                with open(out_path, "wb") as f:
                    f.write(content)

            print("\n================ EXPORT SUCCESSFUL ================")
            print(f"File Name:     {filename}")
            print(f"Saved Path:    {out_path}")
            print(f"Total Tables:  {meta['total_tables']}")
            print(f"Total Rows:    {meta['total_records']}")
            print(f"File Size:     {meta['size_mb']} MB ({meta['size_bytes']:,} bytes)")
            print("===================================================\n")

        elif args.command == "restore":
            if not os.path.exists(args.file):
                print(f"Error: File '{args.file}' not found.")
                sys.exit(1)

            print(f"[Excel Backup CLI] Restoring database from '{args.file}'...")
            with open(args.file, "rb") as f:
                content = f.read()

            result = excel_backup_service.import_database_from_excel(
                db=db,
                file_bytes=content,
                overwrite=not args.no_overwrite
            )

            print("\n================ RESTORE SUCCESSFUL ================")
            print(f"Result:          {result['message']}")
            print(f"Inserted Rows:   {result['total_inserted']}")
            print(f"Updated Rows:    {result['total_updated']}")
            print(f"Tables Synced:   {result['total_tables']}")
            print(f"Duration:        {result['duration_seconds']}s")
            print("====================================================\n")

        elif args.command == "list":
            backups = excel_backup_service.list_backups()
            print("\n================ AVAILABLE BACKUP ARCHIVES ================")
            if not backups:
                print("No backup files found in backup directory.")
            else:
                print(f"{'Filename':<45} | {'Type':<6} | {'Size (MB)':<10} | {'Created At'}")
                print("-" * 90)
                for b in backups:
                    print(f"{b['filename']:<45} | {b['type']:<6} | {b['size_mb']:<10.2f} | {b['created_at']}")
            print("===========================================================\n")

    except Exception as e:
        print(f"\n[CLI ERROR] Operation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
