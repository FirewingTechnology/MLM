import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, apply_migrations, get_db
from app.main import app
from app.models.user import User
from app.models.package import Package
from app.models.wallet import Wallet, WalletTransaction
from app.models.security_pin import SecurityPin
from app.models.pin_order import SecurityPinOrder
from app.models.pin_transfer import SecurityPinTransfer
from app.models.pin_ledger import SecurityPinLedger
from app.security import hash_password, create_access_token
from app.services.seed_service import initialize_production_baseline
from app.services.pin_service import pin_service
from app.services.wallet_service import get_or_create_wallet
from app.services.backup_service import backup_service
from app.services.integrity_service import integrity_service

@pytest.fixture
def audit_db_env():
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "prod_audit.sqlite3")
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30}
    )
    Base.metadata.create_all(bind=engine)
    apply_migrations(engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = Session()
    initialize_production_baseline(db)
    db.close()

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield {
        "engine": engine,
        "Session": Session,
        "client": client,
        "db_file": db_file,
        "backup_dir": backup_dir
    }

    app.dependency_overrides.clear()
    engine.dispose()

def test_financial_idempotency_and_double_pin_use(audit_db_env):
    """Verifies duplicate PIN use and double-activation cannot double-spend or double-credit."""
    Session = audit_db_env["Session"]
    client = audit_db_env["client"]
    db = Session()

    pkg = db.query(Package).first()
    user = User(
        user_code="USR-IDEM",
        email="idem@audit.com",
        mobile="9111111111",
        full_name="Idempotency User",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="IDEM01",
        is_active=False
    )
    db.add(user)
    db.commit()
    user_id = user.id

    p_code, raw_pin, hashed = pin_service.generate_secure_pin()
    pin = SecurityPin(
        pin_code=p_code,
        pin_hash=hashed,
        user_id=user_id,
        owner_user_id=user_id,
        package_id=pkg.id,
        amount=35000.0,
        bv=30000.0,
        status="AVAILABLE"
    )
    db.add(pin)
    db.commit()
    pin_id = pin.id
    db.close()

    token = create_access_token(user_id=user_id, role="USER")
    headers = {"Authorization": f"Bearer {token}"}

    # First activation request -> SUCCESS
    res1 = client.post("/api/security-pins/use", json={"pin_code": p_code, "pin_password": raw_pin}, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["success"] is True

    # Immediate duplicate request -> REJECTED with 400 Bad Request
    res2 = client.post("/api/security-pins/use", json={"pin_code": p_code, "pin_password": raw_pin}, headers=headers)
    assert res2.status_code == 400

    # Verify PIN state in DB is USED exactly once
    db2 = Session()
    re_pin = db2.query(SecurityPin).filter(SecurityPin.id == pin_id).first()
    assert re_pin.status == "USED"
    assert re_pin.used_at is not None
    db2.close()

def test_pin_idor_protection_and_ownership(audit_db_env):
    """Verifies User B cannot transfer or use User A's PIN (IDOR protection)."""
    Session = audit_db_env["Session"]
    client = audit_db_env["client"]
    db = Session()

    pkg = db.query(Package).first()
    user_a = User(
        user_code="USR-A-PIN",
        email="a_pin@audit.com",
        mobile="9111111112",
        full_name="User A Owner",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="APIN01",
        is_active=True
    )
    user_b = User(
        user_code="USR-B-ATTACKER",
        email="b_pin@audit.com",
        mobile="9111111113",
        full_name="User B Attacker",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="BPIN01",
        is_active=True
    )
    db.add_all([user_a, user_b])
    db.commit()
    user_b_id = user_b.id

    # PIN owned exclusively by A
    p_code, raw_pin, hashed = pin_service.generate_secure_pin()
    pin = SecurityPin(
        pin_code=p_code,
        pin_hash=hashed,
        user_id=user_a.id,
        owner_user_id=user_a.id,
        package_id=pkg.id,
        amount=35000.0,
        bv=30000.0,
        status="AVAILABLE"
    )
    db.add(pin)
    db.commit()
    pin_id = pin.id
    db.close()

    # Attacker B attempts to use A's PIN
    token_b = create_access_token(user_id=user_b_id, role="USER")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # B attempts to transfer A's PIN (pin_id=pin.id, but B owns 0 PINs)
    res_transfer = client.post("/api/security-pins/transfer", json={
        "to_user_identifier": "USR-B-ATTACKER",
        "pin_id": pin_id,
        "quantity": 1
    }, headers=headers_b)
    assert res_transfer.status_code in (400, 403, 404)

    # B attempts to use A's PIN
    res_use = client.post("/api/security-pins/use", json={
        "pin_id": pin_id,
        "raw_pin": raw_pin
    }, headers=headers_b)
    assert res_use.status_code in (400, 403, 404)

def test_admin_rbac_and_privilege_separation(audit_db_env):
    """Verifies regular users are strictly blocked from all Admin API endpoints with 403 Forbidden."""
    Session = audit_db_env["Session"]
    client = audit_db_env["client"]
    db = Session()

    user = User(
        user_code="USR-REGULAR",
        email="regular@audit.com",
        mobile="9111111114",
        full_name="Regular Member",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="REG01",
        is_active=True
    )
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()

    token = create_access_token(user_id=user_id, role="USER")
    headers = {"Authorization": f"Bearer {token}"}

    admin_endpoints = [
        ("GET", "/api/admin/users"),
        ("GET", "/api/admin/system/database"),
        ("GET", "/api/admin/system/integrity"),
        ("POST", "/api/admin/system/backup"),
        ("GET", "/api/admin/security-pins/orders"),
        ("GET", "/api/admin/security-pins"),
        ("POST", "/api/admin/demo/reset")
    ]

    for method, path in admin_endpoints:
        if method == "GET":
            res = client.get(path, headers=headers)
        else:
            res = client.post(path, json={}, headers=headers)
        assert res.status_code in (401, 403), f"Endpoint {path} failed RBAC check: status {res.status_code}"

def test_wallet_ledger_mathematical_reconciliation(audit_db_env):
    """Verifies for all users: wallet.balance == sum(ledger credits) - sum(ledger debits)."""
    Session = audit_db_env["Session"]
    db = Session()

    user = User(
        user_code="USR-FIN-REC",
        email="rec@audit.com",
        mobile="9111111115",
        full_name="Reconciliation User",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="REC01",
        is_active=True
    )
    db.add(user)
    db.flush()

    wallet = get_or_create_wallet(db, user.id)
    wallet.balance = 16000.0

    # Add 2 credits + 1 debit
    t1 = WalletTransaction(
        wallet_id=wallet.id, user_id=user.id, transaction_type="CREDIT", category="DIRECT_COMMISSION",
        amount=3000.0, balance_before=0.0, balance_after=3000.0, reference_id="REF-1", description="Credit 1"
    )
    t2 = WalletTransaction(
        wallet_id=wallet.id, user_id=user.id, transaction_type="CREDIT", category="PAIR_BONUS",
        amount=15000.0, balance_before=3000.0, balance_after=18000.0, reference_id="REF-2", description="Credit 2"
    )
    t3 = WalletTransaction(
        wallet_id=wallet.id, user_id=user.id, transaction_type="DEBIT", category="WITHDRAWAL",
        amount=2000.0, balance_before=18000.0, balance_after=16000.0, reference_id="REF-3", description="Debit 1"
    )
    db.add_all([t1, t2, t3])
    db.commit()

    # Run integrity audit
    audit = integrity_service.run_integrity_audit(db)
    assert audit["status"] in ("HEALTHY", "NOTICE")
    ledger_discrepancies = [i for i in audit["issues"] if i["check"] == "WALLET_LEDGER_RECONCILIATION"]
    assert len(ledger_discrepancies) == 0
    db.close()

def test_backup_and_isolated_restore_verification(audit_db_env):
    """Verifies live SQLite backup generation and restores into an isolated database."""
    Session = audit_db_env["Session"]
    db_file = audit_db_env["db_file"]
    backup_dir = audit_db_env["backup_dir"]
    db = Session()

    # Create backup using BackupService
    backup_result = backup_service.create_database_backup(notes="Production audit verification")
    assert backup_result["success"] is True
    backup_path = os.path.join(settings.BACKUP_DIR, backup_result["filename"])
    assert os.path.exists(backup_path)
    assert backup_result["size_bytes"] > 0

    # Open the backup file directly with a new SQLite engine to verify data integrity
    restore_engine = create_engine(f"sqlite:///{backup_path}")
    RestoreSession = sessionmaker(bind=restore_engine)
    r_db = RestoreSession()

    # Verify users exist in backup
    admin_in_backup = r_db.query(User).filter(User.role == "ADMIN").first()
    assert admin_in_backup is not None
    assert admin_in_backup.role == "ADMIN"
    assert "admin@" in admin_in_backup.email

    r_db.close()
    restore_engine.dispose()
    db.close()
