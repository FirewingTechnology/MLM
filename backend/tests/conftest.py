import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so Base knows all tables
import app.models.user
import app.models.package
import app.models.purchase
import app.models.volume
import app.models.period_volume
import app.models.commission
import app.models.wallet
import app.models.withdrawal
import app.models.audit_log
import app.models.demo_time
import app.models.referral_token


from app.database import Base, get_db
from app.main import app
from app.services.seed_service import seed_database

# Use in-memory SQLite with StaticPool so all connections share the same in-memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_test_fixtures(db):
    seed_database(db)
    from app.models.user import User
    from app.security import hash_password
    from app.services.wallet_service import get_or_create_wallet
    from app.services.mlm_service import get_or_create_binary_volume

    admin = db.query(User).filter(User.role == "ADMIN").first()
    if admin and admin.email != "admin@demo.com":
        admin.email = "admin@demo.com"
        db.flush()

    if not db.query(User).filter(User.referral_code == "AMOL001").first():
        amol = User(
            user_code="USR-00002",
            email="amol@demo.com",
            mobile="9876500002",
            full_name="Amol Sharma",
            password_hash=hash_password("Demo@123"),
            role="USER",
            referral_code="AMOL001",
            sponsor_id=None,
            binary_parent_id=None,
            binary_position=None,
            is_active=True
        )
        db.add(amol)
        db.flush()
        get_or_create_wallet(db, amol.id)
        get_or_create_binary_volume(db, amol.id)
    db.commit()

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_test_fixtures(db)
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
