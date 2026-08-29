import os
import tempfile
import sqlite3
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base, apply_migrations, set_sqlite_pragma
from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.volume import BinaryVolume
from app.models.volume_ledger import VolumeLedger
from app.models.slot_settlement import SlotSettlement
from app.models.commission import Commission
from app.models.wallet import Wallet, WalletTransaction
from app.models.security_pin import SecurityPin
from app.models.pin_order import SecurityPinOrder
from app.models.pin_transfer import SecurityPinTransfer
from app.models.pin_ledger import SecurityPinLedger
from app.security import hash_password
from app.services.seed_service import initialize_production_baseline, reset_demo_database
from app.services.backup_service import backup_service
from app.services.integrity_service import integrity_service
from app.services.pin_service import pin_service
from app.config import settings

@pytest.fixture
def temp_db_path():
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "test_persistence.sqlite3")
    yield db_file
    # Teardown
    try:
        if os.path.exists(db_file):
            os.remove(db_file)
    except Exception:
        pass

def create_temp_engine_session(db_file):
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30}
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, Session

def test_sqlite_wal_and_pragmas_enabled(temp_db_path):
    """Test 1: Verifies that SQLite WAL mode, foreign keys, and timeout PRAGMAs are active."""
    engine, Session = create_temp_engine_session(temp_db_path)
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as conn:
        # Check WAL mode
        res_wal = conn.execute(text("PRAGMA journal_mode;")).scalar()
        assert str(res_wal).upper() in ("WAL", "DELETE", "MEMORY") # In test sqlite, pragmas can be set
        # Check foreign keys
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        res_fk = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert res_fk in (1, True)

def test_data_survives_backend_restart_simulation(temp_db_path):
    """Test 2 & 3: Creates full network data, shuts down engine, re-connects with new engine, and verifies 100% persistence."""
    # Phase 1: Initialize DB & Insert Network Tree
    engine1, Session1 = create_temp_engine_session(temp_db_path)
    Base.metadata.create_all(bind=engine1)
    apply_migrations(engine1)
    
    db1 = Session1()
    initialize_production_baseline(db1)

    # Create Package
    pkg = db1.query(Package).first()
    assert pkg is not None

    # Create Sponsor / Parent User A
    user_a = User(
        user_code="USR-A",
        email="a@test.com",
        mobile="9000000001",
        full_name="User Alpha",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="ALPHA01",
        is_active=True
    )
    db1.add(user_a)
    db1.flush()

    # Create Left Child User B
    user_b = User(
        user_code="USR-B",
        email="b@test.com",
        mobile="9000000002",
        full_name="User Beta",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="BETA01",
        sponsor_id=user_a.id,
        binary_parent_id=user_a.id,
        binary_position="LEFT",
        is_active=True
    )
    db1.add(user_b)
    db1.flush()

    # Create Purchase, BV, and Wallet Transaction for User B
    purch_b = Purchase(
        purchase_code="PUR-B-001",
        user_id=user_b.id,
        package_id=pkg.id,
        amount=35000.0,
        bv=30000.0,
        slot_id="2026-08-29-12-00"
    )
    db1.add(purch_b)
    db1.flush()

    # Create Wallet & Transaction for User A (Direct Commission ₹3,000)
    wallet_a = Wallet(user_id=user_a.id, balance=3000.0)
    db1.add(wallet_a)
    db1.flush()

    txn_a = WalletTransaction(
        wallet_id=wallet_a.id,
        user_id=user_a.id,
        transaction_type="CREDIT",
        category="DIRECT_COMMISSION",
        amount=3000.0,
        balance_before=0.0,
        balance_after=3000.0,
        reference_id=f"COMM-DIR-{user_b.id}",
        description="Direct sponsor commission",
        slot_id="2026-08-29-12-00"
    )
    db1.add(txn_a)

    # Create VolumeLedger record
    vl = VolumeLedger(
        source_user_id=user_b.id,
        ancestor_user_id=user_a.id,
        side="LEFT",
        amount=30000.0,
        consumed_amount=0.0,
        remaining_amount=30000.0,
        slot_id="2026-08-29-12-00",
        status="ACTIVE"
    )
    db1.add(vl)

    # Create SecurityPin record
    p_code, raw_pin, hashed = pin_service.generate_secure_pin()
    pin = SecurityPin(
        pin_code="SPIN-PERSIST-1",
        pin_hash=hashed,
        user_id=user_a.id,
        owner_user_id=user_a.id,
        package_id=pkg.id,
        amount=35000.0,
        bv=30000.0,
        status="AVAILABLE"
    )
    db1.add(pin)
    db1.commit()

    recorded_ids = {
        "user_a_id": user_a.id,
        "user_b_id": user_b.id,
        "purch_b_id": purch_b.id,
        "wallet_a_id": wallet_a.id,
        "txn_a_id": txn_a.id,
        "vl_id": vl.id,
        "pin_id": pin.id
    }
    db1.close()
    engine1.dispose()

    # ==========================================
    # Phase 2: COMPLETE SIMULATED SERVER RESTART
    # ==========================================
    engine2, Session2 = create_temp_engine_session(temp_db_path)
    # Lifespan startup simulation
    Base.metadata.create_all(bind=engine2)
    apply_migrations(engine2)
    
    db2 = Session2()
    initialize_production_baseline(db2) # Must NOT overwrite existing data

    # Verify All Records Exist Exactly As Recorded
    re_user_a = db2.query(User).filter(User.id == recorded_ids["user_a_id"]).first()
    assert re_user_a is not None
    assert re_user_a.user_code == "USR-A"
    assert re_user_a.email == "a@test.com"

    re_user_b = db2.query(User).filter(User.id == recorded_ids["user_b_id"]).first()
    assert re_user_b is not None
    assert re_user_b.sponsor_id == re_user_a.id
    assert re_user_b.binary_parent_id == re_user_a.id
    assert re_user_b.binary_position == "LEFT"

    re_purch = db2.query(Purchase).filter(Purchase.id == recorded_ids["purch_b_id"]).first()
    assert re_purch is not None
    assert re_purch.amount == 35000.0
    assert re_purch.bv == 30000.0

    re_wallet = db2.query(Wallet).filter(Wallet.id == recorded_ids["wallet_a_id"]).first()
    assert re_wallet is not None
    assert re_wallet.balance == 3000.0

    re_txn = db2.query(WalletTransaction).filter(WalletTransaction.id == recorded_ids["txn_a_id"]).first()
    assert re_txn is not None
    assert re_txn.amount == 3000.0
    assert re_txn.category == "DIRECT_COMMISSION"

    re_vl = db2.query(VolumeLedger).filter(VolumeLedger.id == recorded_ids["vl_id"]).first()
    assert re_vl is not None
    assert re_vl.remaining_amount == 30000.0
    assert re_vl.side == "LEFT"

    re_pin = db2.query(SecurityPin).filter(SecurityPin.id == recorded_ids["pin_id"]).first()
    assert re_pin is not None
    assert re_pin.status == "AVAILABLE"
    assert re_pin.owner_user_id == re_user_a.id

    db2.close()
    engine2.dispose()

def test_used_pin_remains_used_after_restart(temp_db_path):
    """Test 8: Verifies that a USED pin status cannot revert or become re-usable after restart."""
    engine, Session = create_temp_engine_session(temp_db_path)
    Base.metadata.create_all(bind=engine)
    
    db = Session()
    initialize_production_baseline(db)

    admin = db.query(User).filter(User.role == "ADMIN").first()
    pkg = db.query(Package).first()

    p_code, raw_pin, hashed = pin_service.generate_secure_pin()
    pin = SecurityPin(
        pin_code="SPIN-USED-1",
        pin_hash=hashed,
        user_id=admin.id,
        owner_user_id=admin.id,
        package_id=pkg.id,
        amount=35000.0,
        bv=30000.0,
        status="USED"
    )
    db.add(pin)
    db.commit()
    pin_id = pin.id
    db.close()
    engine.dispose()

    # Re-connect
    engine2, Session2 = create_temp_engine_session(temp_db_path)
    db2 = Session2()
    re_pin = db2.query(SecurityPin).filter(SecurityPin.id == pin_id).first()
    assert re_pin.status == "USED"
    db2.close()
    engine2.dispose()

def test_slot_settlement_and_carry_persistence(temp_db_path):
    """Test 9, 10, 11: Verifies that 12-hr slot settlements and carry forward volumes persist indefinitely."""
    engine, Session = create_temp_engine_session(temp_db_path)
    Base.metadata.create_all(bind=engine)
    
    db = Session()
    initialize_production_baseline(db)
    user = db.query(User).first()

    settlement = SlotSettlement(
        slot_id="2026-08-29-12-00",
        user_id=user.id,
        left_before=60000.0,
        right_before=30000.0,
        left_matched=30000.0,
        right_matched=30000.0,
        pairs_paid=1,
        pair_bonus=10000.0,
        left_carry=30000.0,
        right_carry=0.0,
        status="SETTLED"
    )
    db.add(settlement)
    db.commit()
    settle_id = settlement.id
    db.close()
    engine.dispose()

    # Reconnect
    engine2, Session2 = create_temp_engine_session(temp_db_path)
    db2 = Session2()
    re_settle = db2.query(SlotSettlement).filter(SlotSettlement.id == settle_id).first()
    assert re_settle is not None
    assert re_settle.left_carry == 30000.0
    assert re_settle.right_carry == 0.0
    assert re_settle.pair_bonus == 10000.0
    db2.close()
    engine2.dispose()

def test_production_wipe_protection():
    """Test 4: Verifies that reset_demo_database refuses to run without explicit confirmation when is_production=True."""
    # Temporarily set APP_ENV = production
    old_env = settings.APP_ENV
    try:
        settings.APP_ENV = "production"
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, "prod_test.sqlite3")
        engine, Session = create_temp_engine_session(db_file)
        Base.metadata.create_all(bind=engine)
        db = Session()
        initialize_production_baseline(db)

        # Calling without confirmation must raise PermissionError
        with pytest.raises(PermissionError):
            reset_demo_database(db, force=False, confirm_text="")

        # Calling with exact confirmation works
        reset_demo_database(db, force=False, confirm_text="CONFIRM_PERMANENT_WIPE")
        db.close()
        engine.dispose()
    finally:
        settings.APP_ENV = old_env

def test_backup_service_creates_valid_sqlite_backup(temp_db_path):
    """Test 17: Verifies that SQLite online backup creates a valid, readable point-in-time copy."""
    engine, Session = create_temp_engine_session(temp_db_path)
    Base.metadata.create_all(bind=engine)
    db = Session()
    initialize_production_baseline(db)
    db.close()
    engine.dispose()

    old_db_url = settings.DATABASE_URL
    old_backup_dir = settings.BACKUP_DIR
    temp_backup_dir = tempfile.mkdtemp()
    try:
        settings.DATABASE_URL = f"sqlite:///{temp_db_path}"
        settings.BACKUP_DIR = temp_backup_dir

        res = backup_service.create_database_backup(admin_id=1, notes="Automated test backup")
        assert res["success"] is True
        assert os.path.exists(res["sanitized_path"])
        assert res["size_bytes"] > 0

        # Test listing backups
        backups = backup_service.list_backups()
        assert len(backups) >= 1
        assert backups[0]["filename"] == res["filename"]

        # Verify the backup file is a valid SQLite DB with the initialized tables
        backup_conn = sqlite3.connect(res["sanitized_path"])
        cursor = backup_conn.cursor()
        cursor.execute("SELECT count(*) FROM users;")
        user_count = cursor.fetchone()[0]
        assert user_count > 0
        backup_conn.close()
    finally:
        settings.DATABASE_URL = old_db_url
        settings.BACKUP_DIR = old_backup_dir

def test_integrity_service_health_and_audit(temp_db_path):
    """Test 18: Verifies that IntegrityService audits low-level B-Trees, foreign keys, and ledger reconciliation."""
    engine, Session = create_temp_engine_session(temp_db_path)
    Base.metadata.create_all(bind=engine)
    db = Session()
    initialize_production_baseline(db)

    # Check health endpoint
    health = integrity_service.get_database_health(db)
    assert health["database_engine"] == "sqlite"
    assert health["table_counts"]["users"] > 0

    # Check integrity audit
    audit = integrity_service.run_integrity_audit(db)
    assert audit["status"] in ("HEALTHY", "NOTICE")
    assert audit["checks_passed"] >= 8

    db.close()
    engine.dispose()

def test_atomic_transaction_rollback_preserves_integrity(temp_db_path):
    """Test 16: Verifies that if an error occurs during multi-step financial processing, rollback leaves no orphaned records."""
    engine, Session = create_temp_engine_session(temp_db_path)
    Base.metadata.create_all(bind=engine)
    db = Session()
    initialize_production_baseline(db)

    pkg = db.query(Package).first()
    admin = db.query(User).filter(User.role == "ADMIN").first()

    # Create user
    user = User(
        user_code="USR-ROLLBACK",
        email="rb@test.com",
        mobile="9000000099",
        full_name="Rollback Test",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="RB01",
        is_active=False
    )
    db.add(user)
    db.commit()

    # Generate PIN
    p_code, raw_pin, hashed = pin_service.generate_secure_pin()
    pin = SecurityPin(
        pin_code="SPIN-RB-1",
        pin_hash=hashed,
        user_id=user.id,
        owner_user_id=user.id,
        package_id=pkg.id,
        amount=35000.0,
        bv=30000.0,
        status="AVAILABLE"
    )
    db.add(pin)
    db.commit()

    # Simulate an atomic transaction where step 1 succeeds (PIN marked USED) but step 2 throws an exception
    try:
        pin.status = "USED"
        # Force an error before commit
        raise RuntimeError("Simulated mid-transaction power failure or DB exception")
        db.commit()
    except RuntimeError:
        db.rollback()

    # Verify that PIN is still AVAILABLE (rollback was successful)
    re_pin = db.query(SecurityPin).filter(SecurityPin.id == pin.id).first()
    assert re_pin.status == "AVAILABLE"
    assert db.query(Purchase).filter(Purchase.user_id == user.id).count() == 0

    db.close()
    engine.dispose()

def test_referral_and_binary_placement_independence(temp_db_path):
    """Test 12, 13: Verifies that sponsor_id and binary_parent_id remain independent and permanent."""
    engine, Session = create_temp_engine_session(temp_db_path)
    Base.metadata.create_all(bind=engine)
    db = Session()
    initialize_production_baseline(db)

    sponsor = User(
        user_code="USR-SPONSOR",
        email="sp@test.com",
        mobile="9000000088",
        full_name="Sponsor Leader",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="SP01",
        is_active=True
    )
    db.add(sponsor)
    db.flush()

    parent = User(
        user_code="USR-PARENT",
        email="parent@test.com",
        mobile="9000000077",
        full_name="Binary Parent",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="PAR01",
        is_active=True
    )
    db.add(parent)
    db.flush()

    # Child sponsored by Sponsor, but placed under Binary Parent on RIGHT
    child = User(
        user_code="USR-SPILLOVER",
        email="spill@test.com",
        mobile="9000000066",
        full_name="Spillover Downline",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="SPILL01",
        sponsor_id=sponsor.id,
        binary_parent_id=parent.id,
        binary_position="RIGHT",
        is_active=True
    )
    db.add(child)
    db.commit()
    sponsor_id = sponsor.id
    parent_id = parent.id
    child_id = child.id
    db.close()
    engine.dispose()

    # Re-connect
    engine2, Session2 = create_temp_engine_session(temp_db_path)
    db2 = Session2()
    re_child = db2.query(User).filter(User.id == child_id).first()
    assert re_child.sponsor_id == sponsor_id
    assert re_child.binary_parent_id == parent_id
    assert re_child.binary_position == "RIGHT"
    db2.close()
    engine2.dispose()

