import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.config import Settings
from app.models.user import User
from app.models.wallet import Wallet
from app.models.volume import BinaryVolume
from app.security import hash_password, verify_password, create_access_token
from app.services.seed_service import initialize_production_baseline
from app.main import app

@pytest.fixture
def clean_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()

def test_existing_admin_password_not_overwritten_on_startup(clean_db):
    """Verify that an existing admin's custom password is NEVER overwritten by startup."""
    # 1. Create an admin with a custom password
    custom_pwd = "MySecretAdminPass2026!"
    admin = User(
        user_code="USR-00001",
        email="custom_admin@domain.com",
        mobile="9876543210",
        full_name="Custom Admin",
        password_hash=hash_password(custom_pwd),
        role="ADMIN",
        referral_code="ADMIN001",
        is_active=True
    )
    clean_db.add(admin)
    clean_db.commit()

    saved_hash_before = admin.password_hash

    # 2. Run startup baseline initialization multiple times
    initialize_production_baseline(clean_db)
    initialize_production_baseline(clean_db)

    # 3. Verify the password hash is completely unchanged and password still verifies
    admin_after = clean_db.query(User).filter(User.id == admin.id).first()
    assert admin_after.password_hash == saved_hash_before
    assert verify_password(custom_pwd, admin_after.password_hash) is True
    assert verify_password("Admin@123", admin_after.password_hash) is False

def test_production_bootstrap_false_does_not_create_admin(clean_db, monkeypatch):
    """In production mode with INITIAL_ADMIN_BOOTSTRAP=false, no admin should be created."""
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_BOOTSTRAP", False)

    initialize_production_baseline(clean_db)

    admin_count = clean_db.query(User).filter(User.role == "ADMIN").count()
    assert admin_count == 0

def test_production_bootstrap_true_creates_admin_when_empty(clean_db, monkeypatch):
    """In production mode with INITIAL_ADMIN_BOOTSTRAP=true and valid credentials, admin is created."""
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_BOOTSTRAP", True)
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_EMAIL", "prod_admin@enterprise.com")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_PASSWORD", "SuperSecure2026!")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_NAME", "Enterprise Admin")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_MOBILE", "9999888877")

    initialize_production_baseline(clean_db)

    admin = clean_db.query(User).filter(User.email == "prod_admin@enterprise.com").first()
    assert admin is not None
    assert admin.role == "ADMIN"
    assert admin.full_name == "Enterprise Admin"
    assert verify_password("SuperSecure2026!", admin.password_hash) is True
    assert verify_password("Admin@123", admin.password_hash) is False

    # Check that wallet and binary volume exist for admin
    wallet = clean_db.query(Wallet).filter(Wallet.user_id == admin.id).first()
    bv = clean_db.query(BinaryVolume).filter(BinaryVolume.user_id == admin.id).first()
    assert wallet is not None
    assert bv is not None

def test_production_bootstrap_true_idempotent_no_modification(clean_db, monkeypatch):
    """If an admin already exists, running bootstrap=true again does NOT modify it."""
    # 1. First run creates admin
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_BOOTSTRAP", True)
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_EMAIL", "admin@initial.com")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_PASSWORD", "PasswordOne123!")

    initialize_production_baseline(clean_db)

    admin = clean_db.query(User).filter(User.email == "admin@initial.com").first()
    initial_hash = admin.password_hash
    initial_id = admin.id

    # 2. Re-run with different password in environment
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_PASSWORD", "DifferentPassword456!")
    initialize_production_baseline(clean_db)

    # 3. Assert password was NOT changed to the new one
    admin_refetched = clean_db.query(User).filter(User.id == initial_id).first()
    assert admin_refetched.password_hash == initial_hash
    assert verify_password("PasswordOne123!", admin_refetched.password_hash) is True
    assert verify_password("DifferentPassword456!", admin_refetched.password_hash) is False

def test_production_bootstrap_invalid_credentials_fails_safely(clean_db, monkeypatch, capsys):
    """If bootstrap=true but password is too short or email is invalid, fails safely without creating admin."""
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_BOOTSTRAP", True)
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_EMAIL", "not-an-email")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_PASSWORD", "short")

    initialize_production_baseline(clean_db)

    admin_count = clean_db.query(User).filter(User.role == "ADMIN").count()
    assert admin_count == 0

    captured = capsys.readouterr()
    assert "Bootstrap Warning" in captured.out
    assert "short" not in captured.out  # Plaintext password must NOT be logged

def test_api_change_password_success_and_validation(clean_db):
    """Test /api/auth/change-password endpoint for authentication, current password check, and new password validation."""
    # 1. Create a user
    user = User(
        user_code="USR-00010",
        email="user_pwd_test@domain.com",
        mobile="9876543299",
        full_name="Pwd Test User",
        password_hash=hash_password("OldPassword123!"),
        role="USER",
        referral_code="PWDTEST01",
        is_active=True
    )
    clean_db.add(user)
    clean_db.commit()

    token = create_access_token(user.id, user.role)

    def override_get_db():
        try:
            yield clean_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # A. Wrong current password
        res = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "WrongPassword!",
                "new_password": "NewSecretPassword2026!",
                "confirm_new_password": "NewSecretPassword2026!"
            }
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "INVALID_PASSWORD"

        # B. Mismatched confirmation
        res = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewSecretPassword2026!",
                "confirm_new_password": "DifferentPassword!"
            }
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "VALIDATION_ERROR"

        # C. Password too short (< 8 chars)
        res = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "OldPassword123!",
                "new_password": "short",
                "confirm_new_password": "short"
            }
        )
        assert res.status_code == 400
        assert "at least 8 characters" in res.json()["error"]["message"]

        # D. Successful password update
        res = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewSecretPassword2026!",
                "confirm_new_password": "NewSecretPassword2026!"
            }
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Verify new password can be used to log in
        login_res = client.post(
            "/api/auth/login",
            json={
                "identifier": "user_pwd_test@domain.com",
                "password": "NewSecretPassword2026!"
            }
        )
        assert login_res.status_code == 200
        assert login_res.json()["success"] is True

        # Verify old password is now rejected
        old_login_res = client.post(
            "/api/auth/login",
            json={
                "identifier": "user_pwd_test@domain.com",
                "password": "OldPassword123!"
            }
        )
        assert old_login_res.status_code == 401
    finally:
        app.dependency_overrides.clear()
