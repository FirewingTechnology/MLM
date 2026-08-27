from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

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
    except Exception as e:
        print(f"[Migration Warning] {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

