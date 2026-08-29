from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sqlite3
import os
from app.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 30
    }

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce production SQLite PRAGMA parameters for WAL mode, foreign keys, and concurrency safety."""
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
    """Automatically adds newly defined columns (like slot_id) to existing tables without data loss."""
    try:
        inspector = inspect(target_engine)
        tables = inspector.get_table_names()
        with target_engine.connect() as conn:
            if 'purchases' in tables:
                cols = [c['name'] for c in inspector.get_columns('purchases')]
                if 'slot_id' not in cols:
                    conn.execute(text("ALTER TABLE purchases ADD COLUMN slot_id VARCHAR(32)"))
                    conn.commit()

            if 'commissions' in tables:
                cols = [c['name'] for c in inspector.get_columns('commissions')]
                if 'slot_id' not in cols:
                    conn.execute(text("ALTER TABLE commissions ADD COLUMN slot_id VARCHAR(32)"))
                    conn.commit()

            if 'wallet_transactions' in tables:
                cols = [c['name'] for c in inspector.get_columns('wallet_transactions')]
                if 'slot_id' not in cols:
                    conn.execute(text("ALTER TABLE wallet_transactions ADD COLUMN slot_id VARCHAR(32)"))
                    conn.commit()

            if 'slot_settlements' in tables:
                cols = [c['name'] for c in inspector.get_columns('slot_settlements')]
                if 'matching_commission' not in cols:
                    conn.execute(text("ALTER TABLE slot_settlements ADD COLUMN matching_commission FLOAT DEFAULT 0.0"))
                    conn.commit()

            # Ensure binary_period_volumes table exists
            if 'binary_period_volumes' not in tables:
                Base.metadata.tables['binary_period_volumes'].create(conn, checkfirst=True)
                conn.commit()

            # Ensure pair_events table exists
            if 'pair_events' not in tables:
                Base.metadata.tables['pair_events'].create(conn, checkfirst=True)
                conn.commit()

            # Ensure referral_tokens table exists
            if 'referral_tokens' not in tables:
                if 'referral_tokens' in Base.metadata.tables:
                    Base.metadata.tables['referral_tokens'].create(conn, checkfirst=True)
                    conn.commit()

            # Ensure package_activation_requests table exists
            if 'package_activation_requests' not in tables:
                if 'package_activation_requests' in Base.metadata.tables:
                    Base.metadata.tables['package_activation_requests'].create(conn, checkfirst=True)
                    conn.commit()

            # Ensure security_pins table exists and has latest columns
            if 'security_pins' not in tables:
                if 'security_pins' in Base.metadata.tables:
                    Base.metadata.tables['security_pins'].create(conn, checkfirst=True)
                    conn.commit()
            else:
                pin_cols = [c['name'] for c in inspector.get_columns('security_pins')]
                if 'owner_user_id' not in pin_cols:
                    conn.execute(text("ALTER TABLE security_pins ADD COLUMN owner_user_id INTEGER REFERENCES users(id)"))
                    conn.execute(text("UPDATE security_pins SET owner_user_id = user_id WHERE owner_user_id IS NULL"))
                    conn.commit()
                if 'original_owner_user_id' not in pin_cols:
                    conn.execute(text("ALTER TABLE security_pins ADD COLUMN original_owner_user_id INTEGER REFERENCES users(id)"))
                    conn.commit()
                if 'order_id' not in pin_cols:
                    conn.execute(text("ALTER TABLE security_pins ADD COLUMN order_id INTEGER REFERENCES security_pin_orders(id)"))
                    conn.commit()
                if 'transferred_at' not in pin_cols:
                    conn.execute(text("ALTER TABLE security_pins ADD COLUMN transferred_at DATETIME"))
                    conn.commit()

            # Ensure security_pin_orders table exists
            if 'security_pin_orders' not in tables:
                if 'security_pin_orders' in Base.metadata.tables:
                    Base.metadata.tables['security_pin_orders'].create(conn, checkfirst=True)
                    conn.commit()

            # Ensure security_pin_transfers table exists
            if 'security_pin_transfers' not in tables:
                if 'security_pin_transfers' in Base.metadata.tables:
                    Base.metadata.tables['security_pin_transfers'].create(conn, checkfirst=True)
                    conn.commit()

            # Ensure security_pin_upline_requests table exists
            if 'security_pin_upline_requests' not in tables:
                if 'security_pin_upline_requests' in Base.metadata.tables:
                    Base.metadata.tables['security_pin_upline_requests'].create(conn, checkfirst=True)
                    conn.commit()

            # Ensure security_pin_ledger table exists
            if 'security_pin_ledger' not in tables:
                if 'security_pin_ledger' in Base.metadata.tables:
                    Base.metadata.tables['security_pin_ledger'].create(conn, checkfirst=True)
                    conn.commit()
    except Exception as e:
        print(f"[Migration Warning] {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

