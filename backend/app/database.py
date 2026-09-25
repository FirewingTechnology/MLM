from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sqlite3
import os
from app.config import settings

db_url = settings.normalized_database_url

def create_configured_engine() -> Engine:
    db_url = settings.normalized_database_url
    if settings.is_postgres:
        try:
            eng = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_recycle=1800,
                pool_timeout=15,
                connect_args={"connect_timeout": 5}
            )
            # Verify connectivity immediately
            with eng.connect() as conn:
                conn.execute(text("SELECT 1;"))
            return eng
        except Exception as e:
            import logging
            logging.getLogger("uvicorn").error(
                "[Database Warning] Could not connect to PostgreSQL (%s). Falling back to persistent SQLite.", e
            )
            sqlite_file = settings.DATABASE_URL.replace("sqlite:///", "") if settings.is_sqlite else settings.SQLITE_DB_PATH
            sqlite_path = os.path.abspath(sqlite_file or "./data/mlm.sqlite3")
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
            return create_engine(
                f"sqlite:///{sqlite_path}",
                connect_args={"check_same_thread": False, "timeout": 30},
                pool_pre_ping=True
            )
    elif settings.is_sqlite:
        sqlite_file = settings.DATABASE_URL.replace("sqlite:///", "")
        sqlite_path = os.path.abspath(sqlite_file or "./data/mlm.sqlite3")
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        return create_engine(
            f"sqlite:///{sqlite_path}",
            connect_args={"check_same_thread": False, "timeout": 30},
            pool_pre_ping=True
        )
    else:
        return create_engine(db_url, pool_pre_ping=True)

engine = create_configured_engine()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce SQLite PRAGMA parameters for WAL mode, foreign keys, and concurrency safety ONLY on SQLite connections."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA busy_timeout = 30000;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA cache_size = -64000;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def apply_migrations(target_engine):
    """Automatically adds newly defined columns (like slot_id) to existing tables without data loss across supported dialects.
    In production, any migration error raises an exception immediately to prevent startup in an inconsistent state."""
    try:
        inspector = inspect(target_engine)
        tables = inspector.get_table_names()
        with target_engine.begin() as conn:
            if 'purchases' in tables:
                cols = [c['name'] for c in inspector.get_columns('purchases')]
                if 'slot_id' not in cols:
                    conn.execute(text("ALTER TABLE purchases ADD COLUMN slot_id VARCHAR(32)"))

            if 'commissions' in tables:
                cols = [c['name'] for c in inspector.get_columns('commissions')]
                if 'slot_id' not in cols:
                    conn.execute(text("ALTER TABLE commissions ADD COLUMN slot_id VARCHAR(32)"))

            if 'wallet_transactions' in tables:
                cols = [c['name'] for c in inspector.get_columns('wallet_transactions')]
                if 'slot_id' not in cols:
                    conn.execute(text("ALTER TABLE wallet_transactions ADD COLUMN slot_id VARCHAR(32)"))

            if 'slot_settlements' in tables:
                cols = [c['name'] for c in inspector.get_columns('slot_settlements')]
                if 'matching_commission' not in cols:
                    conn.execute(text("ALTER TABLE slot_settlements ADD COLUMN matching_commission FLOAT DEFAULT 0.0"))

            if 'users' in tables:
                user_cols = [c['name'] for c in inspector.get_columns('users')]
                if 'current_rank' not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN current_rank VARCHAR(32) DEFAULT 'DISTRIBUTOR'"))
                if 'earning_status' not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN earning_status VARCHAR(32) DEFAULT 'ACTIVE'"))

            # Ensure commissions table has capping fields
            if 'commissions' in tables:
                comm_cols = [c['name'] for c in inspector.get_columns('commissions')]
                if 'requested_amount' not in comm_cols:
                    conn.execute(text("ALTER TABLE commissions ADD COLUMN requested_amount FLOAT"))
                if 'blocked_amount' not in comm_cols:
                    conn.execute(text("ALTER TABLE commissions ADD COLUMN blocked_amount FLOAT DEFAULT 0.0"))
                if 'is_capped' not in comm_cols:
                    is_pg = target_engine.dialect.name == 'postgresql'
                    bool_type = "BOOLEAN" if is_pg else "BOOLEAN"
                    conn.execute(text(f"ALTER TABLE commissions ADD COLUMN is_capped {bool_type} DEFAULT FALSE"))
                if 'cap_reason' not in comm_cols:
                    conn.execute(text("ALTER TABLE commissions ADD COLUMN cap_reason VARCHAR(255)"))

            # Ensure tables exist
            for table_name in [
                'binary_period_volumes',
                'pair_events',
                'referral_tokens',
                'package_activation_requests',
                'security_pin_orders',
                'security_pins',
                'security_pin_transfers',
                'security_pin_upline_requests',
                'security_pin_ledger',
                'rank_configs',
                'rank_achievements',
                'earning_cycles',
                'daily_reward_cycles',
                'daily_reward_transactions'
            ]:
                if table_name not in tables and table_name in Base.metadata.tables:
                    Base.metadata.tables[table_name].create(conn, checkfirst=True)

            # Ensure security_pins has latest columns
            if 'security_pins' in tables:
                pin_cols = [c['name'] for c in inspector.get_columns('security_pins')]
                if 'owner_user_id' not in pin_cols:
                    conn.execute(text("ALTER TABLE security_pins ADD COLUMN owner_user_id INTEGER REFERENCES users(id)"))
                    conn.execute(text("UPDATE security_pins SET owner_user_id = user_id WHERE owner_user_id IS NULL"))
                if 'original_owner_user_id' not in pin_cols:
                    conn.execute(text("ALTER TABLE security_pins ADD COLUMN original_owner_user_id INTEGER REFERENCES users(id)"))
                if 'order_id' not in pin_cols:
                    conn.execute(text("ALTER TABLE security_pins ADD COLUMN order_id INTEGER REFERENCES security_pin_orders(id)"))
                if 'transferred_at' not in pin_cols:
                    is_pg = target_engine.dialect.name == 'postgresql'
                    ts_type = "TIMESTAMP" if is_pg else "DATETIME"
                    conn.execute(text(f"ALTER TABLE security_pins ADD COLUMN transferred_at {ts_type}"))
    except Exception as e:
        if settings.is_production:
            raise RuntimeError(f"CRITICAL: Database schema migration failed on target database: {e}") from e
        else:
            print(f"[Migration Error] {e}")
            raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
