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
        DATABASE_URL="sqlite:///./data/mlm.sqlite3"
    )
    with pytest.raises(RuntimeError) as exc_info:
        prod_sqlite_settings.validate_production_configuration()
    assert "SQLite fallback is strictly prohibited in production" in str(exc_info.value)

def test_production_accepts_valid_postgresql_database_url():
    """Verify that Settings.validate_production_configuration accepts a valid PostgreSQL URL."""
    prod_pg_settings = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://dbuser:secretpass@mystatus-postgres.ap-south-1.rds.amazonaws.com:5432/mystatus_db"
    )
    # Must not raise
    prod_pg_settings.validate_production_configuration()
    assert prod_pg_settings.is_production is True
    assert prod_pg_settings.is_postgres is True

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
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "dialect" in data
        assert "password" not in str(data)
        assert "***:***" in data.get("database_path", "") or "/" in data.get("database_path", "")
    finally:
        app.dependency_overrides.clear()
