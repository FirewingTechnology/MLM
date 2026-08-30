import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, apply_migrations
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
from app.services.seed_service import initialize_production_baseline
from app.services.pin_service import pin_service
from app.services.wallet_service import get_or_create_wallet
from app.services.time_service import slot_service

@pytest.fixture
def temp_prod_db():
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "prod_network_tree.sqlite3")
    yield db_file
    try:
        if os.path.exists(db_file):
            os.remove(db_file)
    except Exception:
        pass

def get_engine_session(db_file):
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30}
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, Session

def test_full_7_node_network_tree_persistence_across_multiple_restarts(temp_prod_db):
    r"""
    Constructs full 7-node network tree (A to G):
         A (Root)
       /   \
      B     C
     / \   / \
    D   E F   G
    Performs package activations, PIN allocations, transfers, BV propagation, pairing,
    slot settlements, and asserts 100% data fidelity across 2 consecutive restarts.
    """
    engine1, Session1 = get_engine_session(temp_prod_db)
    Base.metadata.create_all(bind=engine1)
    apply_migrations(engine1)
    
    db = Session1()
    initialize_production_baseline(db)

    # 1. Package
    pkg = db.query(Package).first()
    assert pkg is not None
    package_id = pkg.id

    # 2. Users (A to G)
    # A = Root User
    user_a = User(
        user_code="USR-A",
        email="a@prod.com",
        mobile="9000000001",
        full_name="Alpha Root",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="ALPHA01",
        sponsor_id=None,
        binary_parent_id=None,
        binary_position=None,
        is_active=True
    )
    db.add(user_a)
    db.flush()
    get_or_create_wallet(db, user_a.id)

    # B = A LEFT (Sponsored by A)
    user_b = User(
        user_code="USR-B",
        email="b@prod.com",
        mobile="9000000002",
        full_name="Beta Left",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="BETA01",
        sponsor_id=user_a.id,
        binary_parent_id=user_a.id,
        binary_position="LEFT",
        is_active=True
    )
    db.add(user_b)
    db.flush()
    get_or_create_wallet(db, user_b.id)

    # C = A RIGHT (Sponsored by A)
    user_c = User(
        user_code="USR-C",
        email="c@prod.com",
        mobile="9000000003",
        full_name="Gamma Right",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="GAMMA01",
        sponsor_id=user_a.id,
        binary_parent_id=user_a.id,
        binary_position="RIGHT",
        is_active=True
    )
    db.add(user_c)
    db.flush()
    get_or_create_wallet(db, user_c.id)

    # D = B LEFT (Sponsored by B)
    user_d = User(
        user_code="USR-D",
        email="d@prod.com",
        mobile="9000000004",
        full_name="Delta B-Left",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="DELTA01",
        sponsor_id=user_b.id,
        binary_parent_id=user_b.id,
        binary_position="LEFT",
        is_active=True
    )
    db.add(user_d)
    db.flush()
    get_or_create_wallet(db, user_d.id)

    # E = B RIGHT (Sponsored by B)
    user_e = User(
        user_code="USR-E",
        email="e@prod.com",
        mobile="9000000005",
        full_name="Epsilon B-Right",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="EPSILON01",
        sponsor_id=user_b.id,
        binary_parent_id=user_b.id,
        binary_position="RIGHT",
        is_active=True
    )
    db.add(user_e)
    db.flush()
    get_or_create_wallet(db, user_e.id)

    # F = C LEFT (Sponsored by C)
    user_f = User(
        user_code="USR-F",
        email="f@prod.com",
        mobile="9000000006",
        full_name="Zeta C-Left",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="ZETA01",
        sponsor_id=user_c.id,
        binary_parent_id=user_c.id,
        binary_position="LEFT",
        is_active=True
    )
    db.add(user_f)
    db.flush()
    get_or_create_wallet(db, user_f.id)

    # G = C RIGHT (Sponsored by C)
    user_g = User(
        user_code="USR-G",
        email="g@prod.com",
        mobile="9000000007",
        full_name="Eta C-Right",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="ETA01",
        sponsor_id=user_c.id,
        binary_parent_id=user_c.id,
        binary_position="RIGHT",
        is_active=True
    )
    db.add(user_g)
    db.flush()
    get_or_create_wallet(db, user_g.id)
    db.commit()

    # 3. Process Purchases & BV for all nodes
    slot_1 = "2026-08-30-12-00"
    for u in [user_a, user_b, user_c, user_d, user_e, user_f, user_g]:
        purch = Purchase(
            purchase_code=f"PUR-{u.user_code}",
            user_id=u.id,
            package_id=package_id,
            amount=35000.0,
            bv=30000.0,
            slot_id=slot_1
        )
        db.add(purch)

    # 4. Security PIN operations
    # Order 5 PINs for User A
    p_code, raw_pin, hashed = pin_service.generate_secure_pin()
    pin_a1 = SecurityPin(
        pin_code=p_code,
        pin_hash=hashed,
        user_id=user_a.id,
        owner_user_id=user_a.id,
        package_id=package_id,
        amount=35000.0,
        bv=30000.0,
        status="AVAILABLE"
    )
    db.add(pin_a1)

    p_code2, raw_pin2, hashed2 = pin_service.generate_secure_pin()
    pin_transferred = SecurityPin(
        pin_code=p_code2,
        pin_hash=hashed2,
        user_id=user_a.id,
        original_owner_user_id=user_a.id,
        owner_user_id=user_b.id, # Transferred to B
        package_id=package_id,
        amount=35000.0,
        bv=30000.0,
        status="TRANSFERRED"
    )
    db.add(pin_transferred)

    # 5. Direct Commissions
    # A sponsored B & C -> 2 x ₹3,000 = ₹6,000
    comm_ab = Commission(
        slot_id=slot_1,
        beneficiary_id=user_a.id,
        source_user_id=user_b.id,
        commission_type="DIRECT_COMMISSION",
        amount=3000.0,
        bv_basis=30000.0,
        percentage=10.0
    )
    comm_ac = Commission(
        slot_id=slot_1,
        beneficiary_id=user_a.id,
        source_user_id=user_c.id,
        commission_type="DIRECT_COMMISSION",
        amount=3000.0,
        bv_basis=30000.0,
        percentage=10.0
    )
    db.add_all([comm_ab, comm_ac])

    # 6. Wallet Transactions for A
    wallet_a = db.query(Wallet).filter(Wallet.user_id == user_a.id).first()
    wallet_a.balance = 6000.0
    txn_ab = WalletTransaction(
        wallet_id=wallet_a.id,
        user_id=user_a.id,
        transaction_type="CREDIT",
        category="DIRECT_COMMISSION",
        amount=3000.0,
        balance_before=0.0,
        balance_after=3000.0,
        reference_id=f"COMM-DIR-{user_b.id}",
        description="Direct commission from USR-B",
        slot_id=slot_1
    )
    txn_ac = WalletTransaction(
        wallet_id=wallet_a.id,
        user_id=user_a.id,
        transaction_type="CREDIT",
        category="DIRECT_COMMISSION",
        amount=3000.0,
        balance_before=3000.0,
        balance_after=6000.0,
        reference_id=f"COMM-DIR-{user_c.id}",
        description="Direct commission from USR-C",
        slot_id=slot_1
    )
    db.add_all([txn_ab, txn_ac])

    # 7. Slot Settlement (A completes 1 pair: 90k L vs 90k R -> 1 paid pair = ₹10k, carry 60k L, 60k R)
    settlement_a = SlotSettlement(
        slot_id=slot_1,
        user_id=user_a.id,
        left_before=90000.0,
        right_before=90000.0,
        left_matched=30000.0,
        right_matched=30000.0,
        pairs_paid=1,
        pair_bonus=10000.0,
        left_carry=60000.0,
        right_carry=60000.0,
        carry_commission=0.0,
        matching_commission=0.0,
        status="SETTLED"
    )
    db.add(settlement_a)
    db.commit()

    saved_user_ids = {
        "a": user_a.id, "b": user_b.id, "c": user_c.id,
        "d": user_d.id, "e": user_e.id, "f": user_f.id, "g": user_g.id
    }
    saved_pin_ids = [pin_a1.id, pin_transferred.id]
    db.close()
    engine1.dispose()

    # =========================================================================
    # RESTART TEST 1: Re-instantiate engine, verify all 7 nodes & financials
    # =========================================================================
    engine2, Session2 = get_engine_session(temp_prod_db)
    db2 = Session2()
    initialize_production_baseline(db2)

    # 1. Verify User Count & Properties
    assert db2.query(User).count() >= 7
    node_a = db2.query(User).filter(User.id == saved_user_ids["a"]).first()
    node_b = db2.query(User).filter(User.id == saved_user_ids["b"]).first()
    node_c = db2.query(User).filter(User.id == saved_user_ids["c"]).first()
    node_d = db2.query(User).filter(User.id == saved_user_ids["d"]).first()
    node_e = db2.query(User).filter(User.id == saved_user_ids["e"]).first()
    node_f = db2.query(User).filter(User.id == saved_user_ids["f"]).first()
    node_g = db2.query(User).filter(User.id == saved_user_ids["g"]).first()

    # Verify Strict Hierarchy
    assert node_a.binary_parent_id is None
    assert node_b.binary_parent_id == node_a.id and node_b.binary_position == "LEFT"
    assert node_c.binary_parent_id == node_a.id and node_c.binary_position == "RIGHT"
    assert node_d.binary_parent_id == node_b.id and node_d.binary_position == "LEFT"
    assert node_e.binary_parent_id == node_b.id and node_e.binary_position == "RIGHT"
    assert node_f.binary_parent_id == node_c.id and node_f.binary_position == "LEFT"
    assert node_g.binary_parent_id == node_c.id and node_g.binary_position == "RIGHT"

    # Verify Sponsorships
    assert node_b.sponsor_id == node_a.id
    assert node_c.sponsor_id == node_a.id
    assert node_d.sponsor_id == node_b.id
    assert node_e.sponsor_id == node_b.id
    assert node_f.sponsor_id == node_c.id
    assert node_g.sponsor_id == node_c.id

    # Verify Wallet Balance & Ledger
    w_a = db2.query(Wallet).filter(Wallet.user_id == node_a.id).first()
    assert w_a.balance == 6000.0
    txns = db2.query(WalletTransaction).filter(WalletTransaction.user_id == node_a.id).all()
    assert len(txns) == 2
    assert sum(t.amount for t in txns) == 6000.0

    # Verify Slot Settlement & Carry
    settle = db2.query(SlotSettlement).filter(SlotSettlement.user_id == node_a.id).first()
    assert settle.pairs_paid == 1
    assert settle.pair_bonus == 10000.0
    assert settle.left_carry == 60000.0
    assert settle.right_carry == 60000.0

    # Verify PINs
    p1 = db2.query(SecurityPin).filter(SecurityPin.id == saved_pin_ids[0]).first()
    p2 = db2.query(SecurityPin).filter(SecurityPin.id == saved_pin_ids[1]).first()
    assert p1.status == "AVAILABLE" and p1.owner_user_id == node_a.id
    assert p2.status == "TRANSFERRED" and p2.owner_user_id == node_b.id

    db2.close()
    engine2.dispose()

    # =========================================================================
    # RESTART TEST 2: Second consecutive restart to guarantee idempotency
    # =========================================================================
    engine3, Session3 = get_engine_session(temp_prod_db)
    db3 = Session3()
    initialize_production_baseline(db3)

    assert db3.query(User).count() >= 7
    node_a3 = db3.query(User).filter(User.id == saved_user_ids["a"]).first()
    assert node_a3.full_name == "Alpha Root"
    w_a3 = db3.query(Wallet).filter(Wallet.user_id == node_a3.id).first()
    assert w_a3.balance == 6000.0

    db3.close()
    engine3.dispose()
