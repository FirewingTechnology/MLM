from app import create_app
from app.extensions import db
from app.services.seed_service import seed_database

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Seeding demo database with initial network...")
        seed_database()
        print("Seed completed successfully! Demo accounts ready.")
