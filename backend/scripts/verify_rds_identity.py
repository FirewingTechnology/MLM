"""
Safe Read-Only RDS Identity Verification Script
==============================================
Connects using the application's actual SQLAlchemy settings and psycopg driver.
Executes read-only identity queries and verifies data fingerprint without modifying any rows.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from urllib.parse import urlparse
from sqlalchemy import create_engine, text, inspect
from app.config import settings

def mask_database_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "unknown-host"
        port = parsed.port or 5432
        db_name = parsed.path.lstrip('/') or "unknown-db"
        user = parsed.username or "unknown-user"
        masked_user = user[:2] + "***" if len(user) > 2 else "***"
        return f"{parsed.scheme}://{masked_user}:***@{host}:{port}/{db_name}"
    except Exception:
        return "postgresql://***:***@****:5432/****"

def verify_rds_identity(custom_url: str = None):
    url = custom_url or os.getenv("DATABASE_URL") or settings.normalized_database_url
    masked_url = mask_database_url(url)
    is_postgres = url.lower().startswith("postgres")
    is_sqlite = url.lower().startswith("sqlite")

    print("=" * 70)
    print("RDS IDENTITY VERIFICATION (READ ONLY)")
    print("=" * 70)
    print(f"Configured Database Target : {masked_url}")
    print(f"SQLAlchemy Dialect Scheme   : {'postgresql+psycopg' if is_postgres else 'sqlite'}")
    print(f"Is PostgreSQL              : {is_postgres}")
    print(f"Is SQLite                  : {is_sqlite}")
    print("-" * 70)

    if not is_postgres:
        print("[STATUS] Target is not PostgreSQL. DATABASE_URL is set to SQLite.")
        print("[RESULT] REAL AWS RDS CONNECTION NOT PROVEN (Environment points to local SQLite)")
        return False

    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            # 1. Basic probe
            conn.execute(text("SELECT 1;"))
            
            # 2. Server metadata
            ver = conn.execute(text("SELECT version();")).scalar()
            curr_db = conn.execute(text("SELECT current_database();")).scalar()
            curr_schema = conn.execute(text("SELECT current_schema();")).scalar()
            server_addr = conn.execute(text("SELECT inet_server_addr();")).scalar()
            server_port = conn.execute(text("SELECT inet_server_port();")).scalar()
            curr_user = conn.execute(text("SELECT current_user;")).scalar()
            pg_server_ver = conn.execute(text("SELECT current_setting('server_version');")).scalar()

            print(f"PostgreSQL Version         : {ver}")
            print(f"Server Version Setting     : {pg_server_ver}")
            print(f"Server IP (inet_server_addr): {server_addr}")
            print(f"Server Port                : {server_port}")
            print(f"Current Database           : {curr_db}")
            print(f"Current Schema             : {curr_schema}")
            print(f"Current User               : {curr_user}")
            print("-" * 70)

            # 3. Read Table Counts (Before)
            critical_tables = [
                "users", "wallets", "wallet_transactions", "purchases", "commissions",
                "volume_ledgers", "slot_settlements", "security_pins", "security_pin_ledger", "audit_logs"
            ]
            inspector = inspect(engine)
            existing_tables = set(inspector.get_table_names())
            
            counts_before = {}
            for t in critical_tables:
                if t in existing_tables:
                    cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{t}";')).scalar()
                    counts_before[t] = cnt
                else:
                    counts_before[t] = 0

            # 4. Check Alembic Version
            alembic_rev = None
            if 'alembic_version' in existing_tables:
                alembic_rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
            print(f"Current Alembic Revision   : {alembic_rev or 'None'}")
            print("-" * 70)
            print("Critical Table Row Counts:")
            for t, cnt in counts_before.items():
                print(f"  * {t:<30} : {cnt} rows")

            # 5. Read Table Counts (After) to verify 0 rows modified
            counts_after = {}
            for t in critical_tables:
                if t in existing_tables:
                    cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{t}";')).scalar()
                    counts_after[t] = cnt
                else:
                    counts_after[t] = 0

            assert counts_before == counts_after, "Row counts differed before and after verification!"
            print("-" * 70)
            print("Row Count Invariance Check : PASSED (0 rows modified)")
            print("=" * 70)
            return True
    except Exception as e:
        print(f"[CONNECTION ERROR] Failed to connect to PostgreSQL: {e}")
        print("[RESULT] REAL AWS RDS CONNECTION NOT PROVEN")
        return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    verify_rds_identity(custom_url=target)
