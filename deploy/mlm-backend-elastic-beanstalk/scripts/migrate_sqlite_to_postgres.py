"""
Production SQLite to PostgreSQL Migration & Reconciliation Utility
===================================================================
Transfers all persistent data from SQLite to AWS RDS PostgreSQL.
Preserves original Primary Keys, Foreign Keys, Money/BV precision,
Timestamps, and Concurrency Constraints.

Usage:
    python backend/scripts/migrate_sqlite_to_postgres.py [options]

Options:
    --source PATH           Path to SQLite source database (default: backend/data/mlm.sqlite3)
    --target URL            PostgreSQL target DATABASE_URL (default: from env)
    --backup-dir PATH       Path to backup directory (default: backend/data/backups)
    --dry-run               Simulate migration in a transaction and rollback
    --verify-only           Skip data transfer and only verify / reconcile SQLite vs PostgreSQL
    --sync-sequences-only   Synchronize PostgreSQL SERIAL / IDENTITY sequences only
    --batch-size N          Batch size for bulk insertion (default: 1000)
"""

import os
import sys
import argparse
import datetime
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add project root and backend to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(backend_dir)
for p in [backend_dir, project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import create_engine, text, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker, declarative_base
import app.models
from app.database import Base
from app.config import settings

# Ordered list of tables to respect foreign key dependency hierarchy
TABLE_MIGRATION_ORDER = [
    "packages",
    "demo_time_config",
    "users",
    "wallets",
    "binary_volumes",
    "referral_tokens",
    "purchases",
    "binary_period_volumes",
    "volume_ledgers",
    "slot_settlements",
    "commissions",
    "wallet_transactions",
    "withdrawals",
    "pair_events",
    "security_pin_orders",
    "package_activation_requests",
    "security_pins",
    "security_pin_transfers",
    "security_pin_upline_requests",
    "security_pin_ledger",
    "audit_logs"
]

def create_sqlite_backup(source_path: str, backup_dir: str) -> str:
    """Creates a consistent, point-in-time snapshot backup of the source SQLite database."""
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source SQLite database not found at: {source_path}")

    os.makedirs(backup_dir, exist_ok=True)
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"mlm_sqlite_pre_postgres_{now_str}.sqlite3"
    backup_path = os.path.join(backup_dir, backup_filename)

    print(f"\n[BACKUP] Creating pre-migration snapshot of source SQLite database...")
    src_conn = sqlite3.connect(source_path)
    try:
        try:
            src_conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        except Exception:
            pass
        dst_conn = sqlite3.connect(backup_path)
        try:
            src_conn.backup(dst_conn, pages=100, sleep=0.01)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()

    size_bytes = os.path.getsize(backup_path)
    print(f"[BACKUP] Backup created successfully: {backup_path} ({size_bytes:,} bytes)")
    return backup_path

def normalize_pg_url(url: str) -> str:
    """Normalizes PostgreSQL connection string for SQLAlchemy with psycopg3/psycopg2."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

def sync_postgres_sequences(engine) -> Dict[str, Any]:
    """Synchronizes all PostgreSQL SERIAL sequences to MAX(primary_key) + 1."""
    results = {}
    print("\n[SEQUENCES] Synchronizing PostgreSQL sequence values...")
    with engine.connect() as conn:
        for table_name in TABLE_MIGRATION_ORDER:
            try:
                # Find max id
                max_id_query = text(f'SELECT MAX(id) FROM "{table_name}";')
                max_id = conn.execute(max_id_query).scalar()
                
                # Reset sequence via pg_get_serial_sequence
                seq_sql = text(f"""
                    DO $$
                    DECLARE
                        seq_name text;
                        current_max bigint;
                    BEGIN
                        seq_name := pg_get_serial_sequence('{table_name}', 'id');
                        IF seq_name IS NOT NULL THEN
                            SELECT COALESCE(MAX(id), 0) INTO current_max FROM "{table_name}";
                            IF current_max > 0 THEN
                                PERFORM setval(seq_name, current_max, true);
                            ELSE
                                PERFORM setval(seq_name, 1, false);
                            END IF;
                        END IF;
                    END $$;
                """)
                conn.execute(seq_sql)
                conn.commit()
                results[table_name] = {"status": "SYNCED", "max_id": max_id}
                print(f"  • {table_name:<30} -> MAX(id) = {max_id or 0} (Sequence synchronized)")
            except Exception as e:
                results[table_name] = {"status": "ERROR", "error": str(e)}
                print(f"  • {table_name:<30} -> Sequence sync error: {e}")
    return results

def get_sqlite_rows(sqlite_conn: sqlite3.Connection, table_name: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Reads all rows and column names from an SQLite table."""
    sqlite_conn.row_factory = sqlite3.Row
    cur = sqlite_conn.cursor()
    cur.execute(f'PRAGMA table_info("{table_name}");')
    cols = [r["name"] for r in cur.fetchall()]
    
    cur.execute(f'SELECT * FROM "{table_name}" ORDER BY rowid ASC;')
    rows = [dict(r) for r in cur.fetchall()]
    return cols, rows

def migrate_data(source_path: str, target_url: str, batch_size: int = 1000, dry_run: bool = False) -> Dict[str, Any]:
    """Migrates all tables from SQLite to PostgreSQL with exact ID and FK preservation."""
    norm_target_url = normalize_pg_url(target_url)
    target_engine = create_engine(norm_target_url, pool_pre_ping=True)
    
    # 1. Ensure schema exists on PostgreSQL
    print(f"\n[SCHEMA] Initializing PostgreSQL schema from SQLAlchemy models...")
    Base.metadata.create_all(bind=target_engine)
    print(f"[SCHEMA] Schema initialization complete.")

    src_conn = sqlite3.connect(source_path)
    report = {
        "migration_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_db": source_path,
        "target_db": target_engine.url.render_as_string(hide_password=True),
        "tables": {},
        "dry_run": dry_run,
        "success": False
    }

    target_metadata = MetaData()
    target_metadata.reflect(bind=target_engine)

    print(f"\n{'='*75}")
    print(f"{'TABLE NAME':<32} | {'SOURCE ROWS':<12} | {'TARGET ROWS':<12} | {'STATUS'}")
    print(f"{'='*75}")

    # Temporary storage for deferred circular reference updates
    # package_activation_requests.security_pin_id -> security_pins.id
    deferred_activation_pins: List[Tuple[int, int]] = []

    with target_engine.connect() as pg_conn:
        trans = pg_conn.begin()
        try:
            for table_name in TABLE_MIGRATION_ORDER:
                if table_name not in target_metadata.tables:
                    print(f"Warning: Table '{table_name}' not in reflected PostgreSQL metadata, skipping.")
                    continue

                pg_table = target_metadata.tables[table_name]
                cols, src_rows = get_sqlite_rows(src_conn, table_name)
                src_count = len(src_rows)

                if src_count == 0:
                    report["tables"][table_name] = {
                        "source_count": 0,
                        "target_count": 0,
                        "status": "EMPTY"
                    }
                    print(f"{table_name:<32} | {0:<12} | {0:<12} | EMPTY")
                    continue

                # Prepare records for insertion
                prepared_records = []
                for row in src_rows:
                    record = {}
                    for col_name in cols:
                        if col_name in pg_table.columns:
                            val = row[col_name]
                            
                            # Handle deferred circular foreign key for package_activation_requests
                            if table_name == "package_activation_requests" and col_name == "security_pin_id":
                                if val is not None:
                                    deferred_activation_pins.append((row["id"], val))
                                val = None  # Insert as NULL first

                            record[col_name] = val
                    prepared_records.append(record)

                # Batch insert into PostgreSQL
                for i in range(0, len(prepared_records), batch_size):
                    batch = prepared_records[i : i + batch_size]
                    pg_conn.execute(pg_table.insert(), batch)

                # Count inserted rows in transaction
                tgt_count = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}";')).scalar()

                report["tables"][table_name] = {
                    "source_count": src_count,
                    "target_count": tgt_count,
                    "status": "MIGRATED" if src_count == tgt_count else "COUNT_MISMATCH"
                }
                status_str = "MIGRATED" if src_count == tgt_count else f"MISMATCH ({src_count} != {tgt_count})"
                print(f"{table_name:<32} | {src_count:<12} | {tgt_count:<12} | {status_str}")

            # Apply deferred circular foreign key references for package_activation_requests
            if deferred_activation_pins:
                print(f"\n[CIRCULAR REFS] Resolving {len(deferred_activation_pins)} deferred activation request PIN references...")
                act_table = target_metadata.tables["package_activation_requests"]
                for req_id, pin_id in deferred_activation_pins:
                    pg_conn.execute(
                        act_table.update().where(act_table.c.id == req_id).values(security_pin_id=pin_id)
                    )
                print(f"[CIRCULAR REFS] Circular references resolved successfully.")

            if dry_run:
                trans.rollback()
                print("\n[DRY RUN] Transaction rolled back. Target database unchanged.")
                report["success"] = True
            else:
                trans.commit()
                print("\n[COMMIT] All table data committed successfully to PostgreSQL.")
                report["success"] = True

        except Exception as e:
            trans.rollback()
            print(f"\n[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            report["error"] = str(e)
            report["success"] = False
            raise
        finally:
            src_conn.close()

    if not dry_run and report["success"]:
        sync_postgres_sequences(target_engine)

    return report

def reconcile_databases(source_path: str, target_url: str) -> Dict[str, Any]:
    """Comprehensive financial, volume, user, and referential reconciliation between SQLite and PostgreSQL."""
    norm_target_url = normalize_pg_url(target_url)
    target_engine = create_engine(norm_target_url, pool_pre_ping=True)
    src_conn = sqlite3.connect(source_path)

    reconciliation = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "table_counts": {},
        "financial_checks": {},
        "integrity_checks": {},
        "all_match": True
    }

    print(f"\n{'='*85}")
    print(f"{'DATA RECONCILIATION SUMMARY':^85}")
    print(f"{'='*85}")
    print(f"{'TABLE NAME':<32} | {'SQLITE':<10} | {'POSTGRES':<10} | {'DIFF':<8} | {'STATUS'}")
    print(f"{'-'*85}")

    with target_engine.connect() as pg_conn:
        # 1. Table Row Counts
        for table_name in TABLE_MIGRATION_ORDER:
            src_cur = src_conn.cursor()
            try:
                src_cur.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                src_cnt = src_cur.fetchone()[0]
            except Exception:
                src_cnt = 0

            try:
                pg_cnt = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}";')).scalar()
            except Exception:
                pg_cnt = 0

            diff = pg_cnt - src_cnt
            status = "MATCH (OK)" if diff == 0 else f"DIFF ({diff:+d})"
            if diff != 0:
                reconciliation["all_match"] = False

            reconciliation["table_counts"][table_name] = {
                "sqlite": src_cnt,
                "postgres": pg_cnt,
                "diff": diff,
                "status": "MATCH" if diff == 0 else "MISMATCH"
            }
            print(f"{table_name:<32} | {src_cnt:<10} | {pg_cnt:<10} | {diff:<8} | {status}")

        # 2. Financial Metrics Reconciliation
        print(f"\n{'-'*85}")
        print(f"{'FINANCIAL & BUSINESS METRIC RECONCILIATION':^85}")
        print(f"{'-'*85}")
        print(f"{'METRIC DESCRIPTION':<40} | {'SQLITE':<15} | {'POSTGRES':<15} | {'STATUS'}")
        print(f"{'-'*85}")

        financial_queries = [
            ("Total Wallets Balance (₹)", "SELECT COALESCE(SUM(balance), 0.0) FROM wallets"),
            ("Total Wallet Credited (₹)", "SELECT COALESCE(SUM(amount), 0.0) FROM wallet_transactions WHERE transaction_type = 'CREDIT'"),
            ("Total Wallet Debited (₹)", "SELECT COALESCE(SUM(amount), 0.0) FROM wallet_transactions WHERE transaction_type = 'DEBIT'"),
            ("Total Purchase Amount (₹)", "SELECT COALESCE(SUM(amount), 0.0) FROM purchases"),
            ("Total Purchase BV", "SELECT COALESCE(SUM(bv), 0.0) FROM purchases"),
            ("Total Direct Commission (₹)", "SELECT COALESCE(SUM(amount), 0.0) FROM commissions WHERE commission_type = 'DIRECT_REFERRAL'"),
            ("Total Pair Bonus (₹)", "SELECT COALESCE(SUM(pair_bonus), 0.0) FROM slot_settlements"),
            ("Total Matching Commission (₹)", "SELECT COALESCE(SUM(matching_commission), 0.0) FROM slot_settlements"),
            ("Total VolumeLedger Amount", "SELECT COALESCE(SUM(amount), 0.0) FROM volume_ledgers"),
            ("Total Consumed VolumeLedger", "SELECT COALESCE(SUM(consumed_amount), 0.0) FROM volume_ledgers"),
            ("Total Remaining VolumeLedger", "SELECT COALESCE(SUM(remaining_amount), 0.0) FROM volume_ledgers"),
            ("Total Security Pins (Count)", "SELECT COUNT(*) FROM security_pins"),
            ("Total Available Security Pins", "SELECT COUNT(*) FROM security_pins WHERE status = 'AVAILABLE'"),
            ("Total Used Security Pins", "SELECT COUNT(*) FROM security_pins WHERE status = 'USED'"),
            ("Total Security Pin Transfers", "SELECT COUNT(*) FROM security_pin_transfers"),
            ("Total Security Pin Ledger Rows", "SELECT COUNT(*) FROM security_pin_ledger"),
        ]

        for desc, query_sql in financial_queries:
            src_cur = src_conn.cursor()
            try:
                src_cur.execute(query_sql)
                src_val = src_cur.fetchone()[0]
            except Exception:
                src_val = 0

            try:
                pg_val = pg_conn.execute(text(query_sql)).scalar()
            except Exception:
                pg_val = 0

            # Compare floats with small epsilon
            if isinstance(src_val, (int, float)) and isinstance(pg_val, (int, float)):
                match = abs(float(src_val) - float(pg_val)) < 0.001
            else:
                match = (src_val == pg_val)

            if not match:
                reconciliation["all_match"] = False

            status_str = "MATCH (OK)" if match else "MISMATCH"
            reconciliation["financial_checks"][desc] = {
                "sqlite": src_val,
                "postgres": pg_val,
                "match": match
            }
            print(f"{desc:<40} | {str(src_val):<15} | {str(pg_val):<15} | {status_str}")

        # 3. Foreign Key & Relational Integrity Checks on PostgreSQL
        print(f"\n{'-'*85}")
        print(f"{'POSTGRESQL RELATIONAL INTEGRITY AUDIT':^85}")
        print(f"{'-'*85}")

        integrity_checks = [
            ("Orphan Purchases (Invalid user_id)", "SELECT COUNT(*) FROM purchases WHERE user_id NOT IN (SELECT id FROM users);"),
            ("Orphan Wallets (Invalid user_id)", "SELECT COUNT(*) FROM wallets WHERE user_id NOT IN (SELECT id FROM users);"),
            ("Orphan Sponsor IDs (Invalid sponsor_id)", "SELECT COUNT(*) FROM users WHERE sponsor_id IS NOT NULL AND sponsor_id NOT IN (SELECT id FROM users);"),
            ("Orphan Matching Parent IDs (Invalid parent_id)", "SELECT COUNT(*) FROM users WHERE binary_parent_id IS NOT NULL AND binary_parent_id NOT IN (SELECT id FROM users);"),
            ("Binary Leg Collisions (Duplicate placement)", "SELECT COUNT(*) FROM (SELECT binary_parent_id, binary_position FROM users WHERE binary_parent_id IS NOT NULL AND binary_position IS NOT NULL GROUP BY binary_parent_id, binary_position HAVING COUNT(*) > 1) t;"),
            ("Orphan VolumeLedger Source (Invalid source_user_id)", "SELECT COUNT(*) FROM volume_ledgers WHERE source_user_id NOT IN (SELECT id FROM users);"),
            ("Orphan VolumeLedger Ancestor (Invalid ancestor_user_id)", "SELECT COUNT(*) FROM volume_ledgers WHERE ancestor_user_id NOT IN (SELECT id FROM users);"),
            ("Orphan SlotSettlement (Invalid user_id)", "SELECT COUNT(*) FROM slot_settlements WHERE user_id NOT IN (SELECT id FROM users);"),
            ("Orphan Wallet Transactions (Invalid wallet_id)", "SELECT COUNT(*) FROM wallet_transactions WHERE wallet_id NOT IN (SELECT id FROM wallets);"),
            ("Orphan Security Pins (Invalid owner_user_id)", "SELECT COUNT(*) FROM security_pins WHERE owner_user_id NOT IN (SELECT id FROM users);"),
        ]

        for check_desc, check_sql in integrity_checks:
            try:
                violation_count = pg_conn.execute(text(check_sql)).scalar()
                passed = (violation_count == 0)
            except Exception as e:
                violation_count = -1
                passed = False

            if not passed:
                reconciliation["all_match"] = False

            status_str = "PASSED (0 violations)" if passed else f"FAILED ({violation_count} violations)"
            reconciliation["integrity_checks"][check_desc] = {
                "violations": violation_count,
                "passed": passed
            }
            print(f"{check_desc:<55} | {status_str}")

    src_conn.close()

    print(f"\n{'='*85}")
    if reconciliation["all_match"]:
        print(f"{'OVERALL RECONCILIATION RESULT: PASSED (100% RECONCILED)':^85}")
    else:
        print(f"{'OVERALL RECONCILIATION RESULT: FAILED (DISCREPANCIES DETECTED)':^85}")
    print(f"{'='*85}\n")

    return reconciliation

def main():
    parser = argparse.ArgumentParser(description="Migrate MLM database from SQLite to PostgreSQL on AWS RDS.")
    parser.add_argument("--source", default=os.getenv("SQLITE_DB_PATH", os.path.abspath("backend/data/mlm.sqlite3")), help="Source SQLite database path")
    parser.add_argument("--target", default=os.getenv("DATABASE_URL"), help="Target PostgreSQL connection URL")
    parser.add_argument("--backup-dir", default=os.getenv("BACKUP_DIR", os.path.abspath("backend/data/backups")), help="Backup directory for SQLite snapshot")
    parser.add_argument("--dry-run", action="store_true", help="Run migration in a transaction and rollback")
    parser.add_argument("--verify-only", action="store_true", help="Only verify and reconcile SQLite vs PostgreSQL without data transfer")
    parser.add_argument("--sync-sequences-only", action="store_true", help="Only synchronize PostgreSQL sequence values")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for insertion")

    args = parser.parse_args()

    source_path = os.path.abspath(args.source)
    target_url = args.target

    if not target_url:
        print("\n[ERROR] No target PostgreSQL DATABASE_URL provided. Specify via --target or DATABASE_URL environment variable.")
        sys.exit(1)

    if not (target_url.startswith("postgresql") or target_url.startswith("postgres")):
        print(f"\n[ERROR] Target database URL must be PostgreSQL: {target_url}")
        sys.exit(1)

    print("\n" + "="*80)
    print(" " * 20 + "MLM PRODUCTION DATABASE MIGRATION")
    print(" " * 24 + "SQLite → AWS RDS PostgreSQL")
    print("="*80)
    print(f"Source Database: {source_path}")
    print(f"Target Database: {normalize_pg_url(target_url).split('@')[-1] if '@' in target_url else 'PostgreSQL'}")
    print(f"Mode: {'VERIFY ONLY' if args.verify_only else ('DRY RUN' if args.dry_run else 'LIVE MIGRATION')}")

    if args.sync_sequences_only:
        engine = create_engine(normalize_pg_url(target_url))
        sync_postgres_sequences(engine)
        return

    if args.verify_only:
        reconcile_databases(source_path, target_url)
        return

    # Step 1: Pre-migration backup
    create_sqlite_backup(source_path, args.backup_dir)

    # Step 2: Migrate data
    migrate_data(source_path, target_url, batch_size=args.batch_size, dry_run=args.dry_run)

    # Step 3: Reconcile
    if not args.dry_run:
        reconcile_databases(source_path, target_url)

if __name__ == "__main__":
    main()
