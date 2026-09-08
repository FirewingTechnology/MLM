import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.config import settings
from app.database import engine, Base, SessionLocal, apply_migrations
from app.services.seed_service import reset_demo_database

if __name__ == '__main__':
    if settings.is_production:
        print("[ERROR] seed.py invocation is strictly prohibited in PRODUCTION environment to protect persistent real data.")
        sys.exit(1)

    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    apply_migrations(engine)
    
    print("Cleaning and resetting demo database to fresh baseline state...")
    db = SessionLocal()
    try:
        reset_demo_database(db)
        print("[SUCCESS] Demo database successfully cleaned and seeded with baseline Admin & Amol accounts!")
    finally:
        db.close()
