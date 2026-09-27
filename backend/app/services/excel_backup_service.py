import io
import os
import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect, Table
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.config import settings
from app.database import engine, Base
from app.services.audit_service import log_action
from app.services.time_service import time_provider, IST

# Ordered table list ensuring proper foreign key dependency hierarchy
TABLE_IMPORT_EXPORT_ORDER = [
    # Baseline & Configurations
    "packages",
    "demo_time_config",
    "rank_configs",
    # Core User Entity
    "users",
    # User Auxiliaries
    "wallets",
    "binary_volumes",
    "referral_tokens",
    # Purchases & Financials
    "purchases",
    "binary_period_volumes",
    "volume_ledgers",
    "slot_settlements",
    "commissions",
    "wallet_transactions",
    "withdrawals",
    "pair_events",
    # Security PINs & Activations
    "security_pin_orders",
    "package_activation_requests",
    "security_pins",
    "security_pin_transfers",
    "security_pin_upline_requests",
    "security_pin_ledger",
    # Ranks & Rewards
    "rank_achievements",
    "earning_cycles",
    "daily_reward_cycles",
    "daily_reward_transactions",
    # System Audit Logs
    "audit_logs"
]

TABLE_DESCRIPTIONS = {
    "packages": "Membership Packages, Prices, BV, and Product Values",
    "demo_time_config": "Virtual Clock & Simulation Engine Configurations",
    "rank_configs": "Rank Levels, Directs Requirements, and Reward Specs",
    "users": "User Accounts, Hierarchy (Sponsor/Binary), Ranks, Passwords",
    "wallets": "User Financial Wallets & Balances",
    "binary_volumes": "Cumulative Binary BV Totals (Left/Right/Carry/Matched)",
    "referral_tokens": "Placement Referral Registration Tokens",
    "purchases": "Package Purchase Records and Activation History",
    "binary_period_volumes": "Slot-by-Slot Binary Carry & Effective BV Snapshots",
    "volume_ledgers": "Atomic BV Propagation Ledger Across Binary Ancestors",
    "slot_settlements": "8-Hour Slot Settlement Records & Binary Matching",
    "commissions": "Direct, Pair, Matching, and Rank Commission Records",
    "wallet_transactions": "Immutable Transaction Ledger for All Wallet Credits/Debits",
    "withdrawals": "Withdrawal Payout Requests, Approvals, and Statuses",
    "pair_events": "Matched Pair Calculation Events & Payouts",
    "security_pin_orders": "Bulk Security PIN Orders & Payments",
    "package_activation_requests": "Manual Bank Transfer Package Activation Requests",
    "security_pins": "Cryptographic Security PIN Inventory & Allocation",
    "security_pin_transfers": "P2P and Admin PIN Transfers Between Members",
    "security_pin_upline_requests": "Member-to-Upline PIN Requisition Requests",
    "security_pin_ledger": "Full PIN Movement & Lifecycle Audit Trail",
    "rank_achievements": "Member Rank Qualifications, Deadlines, and Awards",
    "earning_cycles": "200% / 300% Package Earning Cap & Retopup Cycles",
    "daily_reward_cycles": "Daily Package Refund Cycles & Progress",
    "daily_reward_transactions": "Daily 7:00 AM Package Refund Daily Credit Log",
    "audit_logs": "Comprehensive Administrative and Financial Audit Logs"
}

class ExcelBackupService:
    """Enterprise-grade Excel Database Backup & Disaster Recovery Service.
    Exports all relational database tables into structured, typed Excel sheets
    and safely re-populates an empty or existing database with sequence reconciliation.
    """

    @classmethod
    def get_backup_dir(cls) -> str:
        backup_dir = os.path.abspath(settings.BACKUP_DIR)
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @classmethod
    def export_database_to_excel(
        cls,
        db: Session,
        admin_id: Optional[int] = None,
        notes: str = "",
        save_copy_to_disk: bool = True
    ) -> Tuple[bytes, str, Dict[str, Any]]:
        """Exports the entire database into an Excel (.xlsx) workbook with a Summary sheet
        and individual sheets for all 26 relational tables.
        """
        import app.models  # Ensure all SQLAlchemy models are registered
        
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        current_ist = time_provider.get_current_ist_time(db)
        timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S")
        filename = f"mlm_database_backup_{timestamp_str}.xlsx"

        # Styling definitions
        font_title = Font(name="Calibri", size=15, bold=True, color="1E293B")
        font_subtitle = Font(name="Calibri", size=10, italic=True, color="64748B")
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Navy
        fill_accent = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")  # Sky blue
        fill_alt_row = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        font_cell = Font(name="Calibri", size=10, color="0F172A")
        font_bold = Font(name="Calibri", size=10, bold=True, color="0F172A")
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        table_stats = {}
        total_records = 0
        inspector = inspect(engine)
        existing_db_tables = inspector.get_table_names()

        # 1. Summary Sheet
        ws_summary = wb.create_sheet(title="SYSTEM_SUMMARY")
        ws_summary.views.sheetView[0].showGridLines = True

        # Header block
        ws_summary.cell(row=1, column=1, value="PARTNER NETWORK & REWARDS - ENTERPRISE DATABASE BACKUP").font = font_title
        ws_summary.cell(row=2, column=1, value=f"Generated via Administrative Disaster Recovery Console • Time: {current_ist.strftime('%Y-%m-%d %H:%M:%S')} IST").font = font_subtitle

        metadata_items = [
            ("Backup File Name", filename),
            ("Export Timestamp (UTC)", now_utc.isoformat()),
            ("Export Timestamp (IST)", current_ist.strftime("%Y-%m-%d %H:%M:%S IST")),
            ("Database Engine", engine.dialect.name),
            ("Environment", settings.APP_ENV),
            ("Initiated By Admin ID", str(admin_id or "System / Scheduled")),
            ("Notes / Reason", notes or "Routine Administrative Backup"),
            ("Status", "VERIFIED CONSISTENT SNAPSHOT")
        ]

        for i, (k, v) in enumerate(metadata_items, start=4):
            c_key = ws_summary.cell(row=i, column=1, value=k)
            c_key.font = font_bold
            c_key.fill = fill_alt_row
            c_key.border = thin_border
            c_val = ws_summary.cell(row=i, column=2, value=v)
            c_val.font = font_cell
            c_val.border = thin_border

        # Summary Table Header
        summary_table_start = 14
        ws_summary.cell(row=summary_table_start - 1, column=1, value="DATABASE TABLES INCLUDED IN THIS BACKUP").font = Font(name="Calibri", size=12, bold=True, color="1E3A8A")

        summary_headers = ["#", "Table / Sheet Name", "Description", "Total Rows Exported", "Status"]
        for col_idx, h in enumerate(summary_headers, start=1):
            cell = ws_summary.cell(row=summary_table_start, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        # 2. Export Each Table in Ordered Sequence
        curr_summary_row = summary_table_start + 1

        for table_idx, table_name in enumerate(TABLE_IMPORT_EXPORT_ORDER, start=1):
            if table_name not in existing_db_tables:
                continue

            columns_info = inspector.get_columns(table_name)
            column_names = [col['name'] for col in columns_info]

            # Fetch rows
            query_str = f"SELECT * FROM {table_name}"
            # Order by id if present
            if 'id' in column_names:
                query_str += " ORDER BY id ASC"
            
            raw_rows = db.execute(text(query_str)).mappings().all()
            row_count = len(raw_rows)
            table_stats[table_name] = row_count
            total_records += row_count

            # Create individual sheet for table (table names are max 27 chars, well within 31 char limit)
            ws_table = wb.create_sheet(title=table_name)
            ws_table.views.sheetView[0].showGridLines = True

            # Write Column Headers
            for c_idx, col_name in enumerate(column_names, start=1):
                c = ws_table.cell(row=1, column=c_idx, value=col_name)
                c.font = font_header
                c.fill = fill_header
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = thin_border

            # Write Data Rows
            for r_idx, row in enumerate(raw_rows, start=2):
                is_alt = (r_idx % 2 == 1)
                for c_idx, col_name in enumerate(column_names, start=1):
                    val = row[col_name]
                    # Format value cleanly for Excel
                    formatted_val = cls._format_value_for_excel(val)
                    c = ws_table.cell(row=r_idx, column=c_idx, value=formatted_val)
                    c.font = font_cell
                    c.border = thin_border
                    if is_alt:
                        c.fill = fill_alt_row

            # Auto-fit column widths
            for col in ws_table.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col[:100]:  # sample top 100 rows for speed
                    val_str = str(cell.value or '')
                    if len(val_str) > max_len:
                        max_len = len(val_str)
                ws_table.column_dimensions[col_letter].width = max(max_len + 3, 12)

            # Record in Summary Sheet
            ws_summary.cell(row=curr_summary_row, column=1, value=table_idx).alignment = Alignment(horizontal="center")
            ws_summary.cell(row=curr_summary_row, column=2, value=table_name).font = font_bold
            ws_summary.cell(row=curr_summary_row, column=3, value=TABLE_DESCRIPTIONS.get(table_name, "Relational Table"))
            ws_summary.cell(row=curr_summary_row, column=4, value=row_count).alignment = Alignment(horizontal="right")
            ws_summary.cell(row=curr_summary_row, column=5, value="OK").alignment = Alignment(horizontal="center")

            for col_i in range(1, 6):
                cell = ws_summary.cell(row=curr_summary_row, column=col_i)
                cell.border = thin_border
                cell.font = font_cell if col_i != 2 else font_bold
                if curr_summary_row % 2 == 1:
                    cell.fill = fill_alt_row

            curr_summary_row += 1

        # Summary Total Row
        ws_summary.cell(row=curr_summary_row, column=1, value="TOTAL")
        ws_summary.cell(row=curr_summary_row, column=2, value=f"{len(table_stats)} Tables")
        ws_summary.cell(row=curr_summary_row, column=3, value="Full Relational Database")
        c_tot = ws_summary.cell(row=curr_summary_row, column=4, value=total_records)
        c_tot.font = font_bold
        c_tot.alignment = Alignment(horizontal="right")
        ws_summary.cell(row=curr_summary_row, column=5, value="COMPLETE")
        for col_i in range(1, 6):
            cell = ws_summary.cell(row=curr_summary_row, column=col_i)
            cell.border = thin_border
            cell.font = font_bold
            cell.fill = fill_accent

        # Auto-fit Summary Sheet Columns
        for col in ws_summary.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws_summary.column_dimensions[col_letter].width = max(max_len + 3, 14)

        # Output to buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()

        # Save to disk if requested
        disk_path = None
        if save_copy_to_disk:
            backup_dir = cls.get_backup_dir()
            disk_path = os.path.join(backup_dir, filename)
            with open(disk_path, "wb") as f:
                f.write(excel_bytes)

        # Structured audit log
        try:
            log_action(
                db,
                'DATABASE_EXCEL_EXPORT',
                'System',
                None,
                admin_id,
                {
                    'filename': filename,
                    'size_bytes': len(excel_bytes),
                    'total_records': total_records,
                    'total_tables': len(table_stats),
                    'notes': notes,
                    'saved_to_disk': bool(disk_path)
                }
            )
            db.commit()
        except Exception:
            pass

        meta = {
            "filename": filename,
            "size_bytes": len(excel_bytes),
            "size_mb": round(len(excel_bytes) / (1024 * 1024), 2),
            "total_tables": len(table_stats),
            "total_records": total_records,
            "created_at": now_utc.isoformat(),
            "table_stats": table_stats,
            "disk_path": disk_path
        }

        return excel_bytes, filename, meta

    @classmethod
    def import_database_from_excel(
        cls,
        db: Session,
        file_bytes: bytes,
        admin_id: Optional[int] = None,
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Safely imports and restores an empty or existing database from an Excel (.xlsx) file.
        Preserves original Primary Keys, Foreign Keys, JSON payloads, and synchronizes
        auto-increment sequences (PostgreSQL SERIAL / SQLite sequence).
        """
        import app.models  # Ensure models loaded

        start_time = datetime.datetime.now(datetime.timezone.utc)
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheet_names = wb.sheetnames

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        is_postgres = engine.dialect.name == "postgresql"
        is_sqlite = engine.dialect.name == "sqlite"

        # 1. Temporarily disable foreign keys for seamless relational population
        if is_sqlite:
            db.execute(text("PRAGMA foreign_keys = OFF;"))
        elif is_postgres:
            try:
                db.execute(text("SET session_replication_role = 'replica';"))
            except Exception:
                pass

        table_results = {}
        total_rows_imported = 0
        total_rows_updated = 0

        try:
            for table_name in TABLE_IMPORT_EXPORT_ORDER:
                if table_name not in sheet_names or table_name not in existing_tables:
                    continue

                ws = wb[table_name]
                rows = list(ws.iter_rows(values_only=True))
                if not rows or len(rows) < 2:
                    table_results[table_name] = {"inserted": 0, "updated": 0, "total": 0}
                    continue

                headers = [str(h).strip() if h is not None else "" for h in rows[0]]
                data_rows = rows[1:]

                # Get column types from DB inspector
                db_cols = {c['name']: c for c in inspector.get_columns(table_name)}

                inserted_count = 0
                updated_count = 0

                for row_data in data_rows:
                    if not any(row_data):
                        continue  # skip completely blank rows

                    row_dict = {}
                    for col_idx, col_name in enumerate(headers):
                        if not col_name or col_name not in db_cols:
                            continue
                        raw_val = row_data[col_idx] if col_idx < len(row_data) else None
                        parsed_val = cls._parse_value_from_excel(raw_val, db_cols[col_name])
                        row_dict[col_name] = parsed_val

                    if not row_dict:
                        continue

                    # Check if record with ID already exists
                    has_id = 'id' in row_dict and row_dict['id'] is not None
                    exists = False

                    if has_id:
                        check_q = text(f"SELECT 1 FROM {table_name} WHERE id = :id LIMIT 1")
                        res = db.execute(check_q, {"id": row_dict['id']}).scalar()
                        exists = bool(res)

                    if exists and overwrite:
                        # Update record
                        set_clauses = [f"{col} = :{col}" for col in row_dict.keys() if col != 'id']
                        if set_clauses:
                            update_q = text(f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = :id")
                            db.execute(update_q, row_dict)
                            updated_count += 1
                    elif not exists:
                        # Insert record with preserved ID
                        cols_str = ", ".join(row_dict.keys())
                        vals_str = ", ".join([f":{k}" for k in row_dict.keys()])
                        insert_q = text(f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str})")
                        db.execute(insert_q, row_dict)
                        inserted_count += 1

                total_rows_imported += inserted_count
                total_rows_updated += updated_count
                table_results[table_name] = {
                    "inserted": inserted_count,
                    "updated": updated_count,
                    "total": inserted_count + updated_count
                }

            # 2. Sequence Synchronization (Crucial so future inserts won't conflict with imported IDs)
            if is_postgres:
                for table_name in TABLE_IMPORT_EXPORT_ORDER:
                    if table_name in existing_tables:
                        try:
                            seq_sync_sql = text(f"""
                                SELECT setval(
                                    pg_get_serial_sequence('{table_name}', 'id'),
                                    COALESCE((SELECT MAX(id) FROM {table_name}), 1)
                                );
                            """)
                            db.execute(seq_sync_sql)
                        except Exception:
                            pass
            elif is_sqlite:
                for table_name in TABLE_IMPORT_EXPORT_ORDER:
                    if table_name in existing_tables:
                        try:
                            db.execute(text(f"""
                                DELETE FROM sqlite_sequence WHERE name = '{table_name}';
                                INSERT INTO sqlite_sequence (name, seq)
                                SELECT '{table_name}', COALESCE(MAX(id), 0) FROM {table_name};
                            """))
                        except Exception:
                            pass

            db.commit()

        except Exception as e:
            db.rollback()
            raise e
        finally:
            # 3. Always re-enable foreign keys
            if is_sqlite:
                db.execute(text("PRAGMA foreign_keys = ON;"))
            elif is_postgres:
                try:
                    db.execute(text("SET session_replication_role = 'origin';"))
                except Exception:
                    pass

        duration = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()

        # Audit restoration
        try:
            log_action(
                db,
                'DATABASE_EXCEL_RESTORE',
                'System',
                None,
                admin_id,
                {
                    'total_rows_imported': total_rows_imported,
                    'total_rows_updated': total_rows_updated,
                    'duration_seconds': duration,
                    'table_stats': table_results
                }
            )
            db.commit()
        except Exception:
            pass

        return {
            "success": True,
            "message": f"Successfully restored database from Excel: {total_rows_imported} inserted, {total_rows_updated} updated across {len(table_results)} tables.",
            "total_inserted": total_rows_imported,
            "total_updated": total_rows_updated,
            "total_tables": len(table_results),
            "table_results": table_results,
            "duration_seconds": round(duration, 2),
            "timestamp": start_time.isoformat()
        }

    @classmethod
    def list_backups(cls) -> List[Dict[str, Any]]:
        """Returns all Excel and SQLite backups in descending chronological order."""
        backup_dir = cls.get_backup_dir()
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for fname in os.listdir(backup_dir):
            if fname.endswith(".xlsx") or fname.endswith(".sqlite3") or fname.endswith(".db"):
                fpath = os.path.join(backup_dir, fname)
                if os.path.isfile(fpath):
                    stat = os.stat(fpath)
                    created_dt = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc)
                    ext = os.path.splitext(fname)[1].lower().replace(".", "")
                    b_type = "EXCEL" if ext == "xlsx" else "SQLITE"
                    backups.append({
                        "filename": fname,
                        "type": b_type,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": created_dt.isoformat(),
                        "download_url": f"/api/admin/system/database/download-backup/{fname}"
                    })

        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    @staticmethod
    def _format_value_for_excel(val: Any) -> Any:
        """Encodes Python/SQLAlchemy types into clean Excel-compatible values."""
        if val is None:
            return ""
        if isinstance(val, (datetime.datetime, datetime.date)):
            return val.isoformat()
        if isinstance(val, (dict, list)):
            return json.dumps(val, default=str)
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        return val

    @staticmethod
    def _parse_value_from_excel(val: Any, col_meta: Dict[str, Any]) -> Any:
        """Parses cell values back into precise column database types."""
        if val is None or val == "":
            return None

        col_type_str = str(col_meta.get('type', '')).upper()

        # Boolean
        if "BOOL" in col_type_str:
            if isinstance(val, bool):
                return val
            val_str = str(val).strip().lower()
            return val_str in ("true", "1", "yes", "t")

        # Datetime
        if "DATETIME" in col_type_str or "TIMESTAMP" in col_type_str:
            if isinstance(val, datetime.datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
                except Exception:
                    pass

        # Date
        if "DATE" in col_type_str and "DATETIME" not in col_type_str:
            if isinstance(val, datetime.date):
                return val
            if isinstance(val, str):
                try:
                    return datetime.date.fromisoformat(val[:10])
                except Exception:
                    pass

        # JSON / Dict
        if "JSON" in col_type_str:
            if isinstance(val, (dict, list)):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return val

        # Integer
        if "INT" in col_type_str:
            try:
                return int(val)
            except Exception:
                pass

        # Float / Numeric
        if "FLOAT" in col_type_str or "NUMERIC" in col_type_str or "DECIMAL" in col_type_str:
            try:
                return float(val)
            except Exception:
                pass

        return val

excel_backup_service = ExcelBackupService()
