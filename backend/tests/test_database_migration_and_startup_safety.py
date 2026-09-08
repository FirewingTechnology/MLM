import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, apply_migrations, get_db
from app.config import Settings
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.commission import Commission
from app.security import hash_password
from app.services.seed_service import initialize_production_baseline
from app.main import app

@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine

def test_apply_migrations_success(test_engine):
    """Verify that apply_migrations executes cleanly and ensures all columns and tables exist."""
    apply_migrations(test_engine)
    # Re-running apply_migrations must be completely idempotent
    apply_migrations(test_engine)

def test_production_migration_failure_causes_startup_failure(test_engine, monkeypatch):
    """Verify that in production mode, if apply_migrations encounters a DB error, an exception is NOT swallowed and raises RuntimeError."""
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")

    # Mock connection execute to simulate a DDL/database failure
    with patch.object(test_engine, "begin", side_effect=Exception("Database connection timeout or locked table")):
        with pytest.raises(RuntimeError) as exc_info:
            apply_migrations(test_engine)
        assert "CRITICAL: Database schema migration failed" in str(exc_info.value)

def test_production_rejects_sqlite_database_url():
    """Verify that Settings.validate_production_configuration strictly rejects SQLite in production."""
    prod_sqlite_settings = Settings(
        APP_ENV="production",
        DATABASE_URL="sqlite:///./data/mlm.sqlite3",
        SECRET_KEY="a-secure-production-secret-key-32chars-long-minimum"
    )
    with pytest.raises(RuntimeError) as exc_info:
        prod_sqlite_settings.validate_production_configuration()
    assert "SQLite fallback is strictly prohibited in production" in str(exc_info.value)

def test_production_rejects_missing_or_default_secret_key():
    """Verify that Settings.validate_production_configuration rejects missing or default SECRET_KEY in production."""
    # 1. Default dev secret key in production -> must raise
    prod_default_secret = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://dbuser:secretpass@mystatus-postgres.ap-south-1.rds.amazonaws.com:5432/mystatus_db",
        SECRET_KEY="partner-network-rewards-super-secret-key-2026"
    )
    with pytest.raises(RuntimeError) as exc_info:
        prod_default_secret.validate_production_configuration()
    assert "requires a strong, unique SECRET_KEY" in str(exc_info.value)

    # 2. Empty secret key in production -> must raise
    prod_empty_secret = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://dbuser:secretpass@mystatus-postgres.ap-south-1.rds.amazonaws.com:5432/mystatus_db",
        SECRET_KEY=""
    )
    with pytest.raises(RuntimeError) as exc_info:
        prod_empty_secret.validate_production_configuration()
    assert "requires a strong, unique SECRET_KEY" in str(exc_info.value)

def test_production_accepts_valid_postgresql_and_secure_secret_key():
    """Verify that Settings.validate_production_configuration accepts a valid PostgreSQL URL and secure SECRET_KEY."""
    prod_pg_settings = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://dbuser:secretpass@mystatus-postgres.ap-south-1.rds.amazonaws.com:5432/mystatus_db",
        SECRET_KEY="super-secure-production-jwt-signing-secret-key-2026"
    )
    # Must not raise
    prod_pg_settings.validate_production_configuration()
    assert prod_pg_settings.is_production is True
    assert prod_pg_settings.is_postgres is True

def test_cors_origins_production_isolation_and_development_support():
    """Verify that get_cors_origins properly parses ALLOWED_ORIGINS and includes production web.mystatusads333.com."""
    from app.main import get_cors_origins

    # 1. Production config with ALLOWED_ORIGINS from Elastic Beanstalk
    prod_cfg = Settings(
        APP_ENV="production",
        ALLOWED_ORIGINS="http://web.mystatusads333.com,https://web.mystatusads333.com",
        CORS_ORIGINS="https://admin.mynetwork.com",
        DATABASE_URL="postgresql+psycopg://dbuser:secretpass@mystatus-postgres.ap-south-1.rds.amazonaws.com:5432/mystatus_db",
        SECRET_KEY="super-secure-production-jwt-signing-secret-key-2026"
    )
    prod_origins = get_cors_origins(prod_cfg)
    assert "http://web.mystatusads333.com" in prod_origins
    assert "https://web.mystatusads333.com" in prod_origins
    assert "https://admin.mynetwork.com" in prod_origins

    # 2. Development config: Must include localhost and production origins
    dev_cfg = Settings(
        APP_ENV="development",
        FRONTEND_URL="http://localhost:5173"
    )
    dev_origins = get_cors_origins(dev_cfg)
    assert "http://localhost:5173" in dev_origins
    assert "http://localhost:3000" in dev_origins
    assert "http://web.mystatusads333.com" in dev_origins

def test_cors_live_http_and_preflight_headers():
    """Verify that requests from http://web.mystatusads333.com receive proper CORS headers."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.testclient import TestClient
    from app.main import get_cors_origins

    test_app = FastAPI()
    test_origins = get_cors_origins(Settings(APP_ENV="production"))
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=test_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,
    )

    @test_app.get("/api/time/current")
    def get_time():
        return {"status": "success"}

    client = TestClient(test_app)

    # 1. GET /api/time/current with Origin
    res = client.get("/api/time/current", headers={"Origin": "http://web.mystatusads333.com"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://web.mystatusads333.com"
    assert res.headers.get("access-control-allow-credentials") == "true"

    # 2. OPTIONS preflight request for /api/time/current
    preflight_res = client.options(
        "/api/time/current",
        headers={
            "Origin": "http://web.mystatusads333.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert preflight_res.status_code == 200
    assert preflight_res.headers.get("access-control-allow-origin") == "http://web.mystatusads333.com"
    assert preflight_res.headers.get("access-control-allow-credentials") == "true"
    assert "GET" in preflight_res.headers.get("access-control-allow-methods", "")


def test_existing_data_and_financial_records_preserved(test_engine):
    """Verify that baseline initialization preserves existing users, wallets, balances, and transactions without alteration."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = Session()
    try:
        # Create an existing user with wallet balance and transactions
        user = User(
            user_code="USR-PRE01",
            email="existing_user@domain.com",
            mobile="9876540001",
            full_name="Existing User",
            password_hash=hash_password("UserPass123!"),
            role="USER",
            referral_code="PRE01",
            is_active=True
        )
        db.add(user)
        db.flush()

        wallet = Wallet(user_id=user.id, balance=25000.0, total_earned=25000.0, total_withdrawn=0.0)
        db.add(wallet)
        db.flush()

        txn = WalletTransaction(
            wallet_id=wallet.id,
            user_id=user.id,
            transaction_type='CREDIT',
            amount=25000.0,
            balance_before=0.0,
            balance_after=25000.0,
            category='DIRECT_COMMISSION',
            description='Historical Commission',
            reference_id='HIST-001'
        )
        db.add(txn)
        db.commit()

        # Run baseline initialization
        initialize_production_baseline(db)

        # Verify all existing records remain exact
        refetched_user = db.query(User).filter(User.id == user.id).first()
        refetched_wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
        refetched_txns = db.query(WalletTransaction).filter(WalletTransaction.user_id == user.id).all()

        assert refetched_user.email == "existing_user@domain.com"
        assert refetched_wallet.balance == 25000.0
        assert refetched_wallet.total_earned == 25000.0
        assert len(refetched_txns) == 1
        assert refetched_txns[0].amount == 25000.0
    finally:
        db.close()

def test_production_startup_does_not_seed_demo_data(test_engine, monkeypatch):
    """Verify that in production mode with INITIAL_ADMIN_BOOTSTRAP=false, zero dummy/demo accounts are inserted."""
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    monkeypatch.setattr("app.config.settings.INITIAL_ADMIN_BOOTSTRAP", False)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = Session()
    try:
        # Clear any users
        db.query(User).delete()
        db.commit()

        initialize_production_baseline(db)

        # In production mode without bootstrap, 0 users exist
        assert db.query(User).count() == 0
    finally:
        db.close()

def test_health_check_endpoint_reports_status_cleanly(test_engine):
    """Verify that /api/health reports connected status and dialect without leaking passwords."""
    from unittest.mock import patch
    with patch("app.main.engine", test_engine):
        client = TestClient(app)
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "dialect" in data
        assert "password" not in str(data)

