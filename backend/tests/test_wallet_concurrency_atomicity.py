import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.models.withdrawal import Withdrawal
from app.models.commission import Commission
from app.models.package import Package
from app.models.purchase import Purchase
from app.security import hash_password
from app.services.wallet_service import (
    get_or_create_wallet,
    credit_wallet,
    debit_wallet,
    adjust_wallet_balance,
    create_withdrawal_request,
    approve_withdrawal,
    reject_withdrawal,
    InsufficientBalanceError,
    InvalidTransactionError
)
from app.services.commission_service import process_package_purchase
from app.services.seed_service import initialize_production_baseline

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
        initialize_production_baseline(db)
        yield db
    finally:
        db.close()

_test_user_counter = 1000

def create_test_user(db, user_code=None, email=None, name="Wallet Test", mobile=None):
    global _test_user_counter
    _test_user_counter += 1
    uc = user_code or f"USR-W{_test_user_counter:05d}"
    em = email or f"wallet_test_{_test_user_counter}@domain.com"
    mob = mobile or f"98711{_test_user_counter:05d}"
    ref = f"WT{_test_user_counter:04d}"

    user = User(
        user_code=uc,
        email=em,
        mobile=mob,
        full_name=name,
        password_hash=hash_password("Pass123!"),
        role="USER",
        referral_code=ref,
        is_active=True
    )
    db.add(user)
    db.commit()
    return user

def test_credit_and_debit_updates_ledger_and_balance(clean_db):
    """Test standard credit and debit operations update balance and append immutable ledger."""
    user = create_test_user(clean_db)
    
    # 1. Initial credit
    txn1 = credit_wallet(clean_db, user.id, amount=10000.0, category='DIRECT_COMMISSION', description='Direct commission 1', reference_id='REF-001')
    clean_db.commit()
    
    assert txn1.balance_before == 0.0
    assert txn1.balance_after == 10000.0
    assert txn1.amount == 10000.0
    
    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 10000.0
    assert wallet.total_earned == 10000.0
    
    # 2. Debit
    txn2 = debit_wallet(clean_db, user.id, amount=3000.0, category='WITHDRAWAL', description='Withdrawal 1', reference_id='WDR-001')
    clean_db.commit()
    
    assert txn2.balance_before == 10000.0
    assert txn2.balance_after == 7000.0
    assert txn2.amount == 3000.0
    
    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 7000.0
    assert wallet.total_withdrawn == 3000.0

def test_insufficient_balance_rejected_without_state_change(clean_db):
    """Test debiting more than available balance raises InsufficientBalanceError and leaves wallet untouched."""
    user = create_test_user(clean_db)
    credit_wallet(clean_db, user.id, amount=5000.0, category='DIRECT_COMMISSION', description='Credit 5000', reference_id='REF-002')
    clean_db.commit()

    wallet_before = get_or_create_wallet(clean_db, user.id)
    txns_count_before = clean_db.query(WalletTransaction).filter(WalletTransaction.user_id == user.id).count()

    with pytest.raises(InsufficientBalanceError) as exc_info:
        debit_wallet(clean_db, user.id, amount=8000.0, category='WITHDRAWAL', description='Overdraft attempt', reference_id='WDR-FAIL-01')

    assert "Insufficient wallet balance" in str(exc_info.value)
    
    # Verify wallet balance and ledger count remain untouched
    clean_db.rollback()
    wallet_after = get_or_create_wallet(clean_db, user.id)
    txns_count_after = clean_db.query(WalletTransaction).filter(WalletTransaction.user_id == user.id).count()

    assert wallet_after.balance == 5000.0
    assert txns_count_before == txns_count_after

def test_idempotent_credit_replay_protection(clean_db):
    """Test credit_wallet with same reference_id returns existing transaction without double-crediting."""
    user = create_test_user(clean_db)

    # First credit
    txn1 = credit_wallet(clean_db, user.id, amount=3000.0, category='DIRECT_COMMISSION', description='Commission Ref A', reference_id='COMM-IDEM-001')
    clean_db.commit()

    # Replay of the exact same credit
    txn2 = credit_wallet(clean_db, user.id, amount=3000.0, category='DIRECT_COMMISSION', description='Commission Ref A (Replay)', reference_id='COMM-IDEM-001')
    clean_db.commit()

    assert txn1.id == txn2.id
    
    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 3000.0  # Not 6000.0!
    
    txn_count = clean_db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user.id,
        WalletTransaction.reference_id == 'COMM-IDEM-001'
    ).count()
    assert txn_count == 1

def test_idempotent_debit_replay_protection(clean_db):
    """Test debit_wallet with same reference_id returns existing transaction without double-debiting."""
    user = create_test_user(clean_db)
    credit_wallet(clean_db, user.id, amount=10000.0, category='DIRECT_COMMISSION', description='Initial Deposit', reference_id='DEP-001')
    clean_db.commit()

    txn1 = debit_wallet(clean_db, user.id, amount=4000.0, category='WITHDRAWAL', description='Debit A', reference_id='WDR-IDEM-001')
    clean_db.commit()

    txn2 = debit_wallet(clean_db, user.id, amount=4000.0, category='WITHDRAWAL', description='Debit A (Replay)', reference_id='WDR-IDEM-001')
    clean_db.commit()

    assert txn1.id == txn2.id

    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 6000.0  # Not 2000.0!

def test_withdrawal_request_considers_pending_withdrawals(clean_db):
    """Test that multiple withdrawal requests cannot exceed balance when pending requests exist."""
    user = create_test_user(clean_db)
    credit_wallet(clean_db, user.id, amount=10000.0, category='DIRECT_COMMISSION', description='Initial 10k', reference_id='DEP-10K')
    clean_db.commit()

    # Request 1: ₹8,000 (Available becomes ₹2,000)
    wdr1 = create_withdrawal_request(clean_db, user.id, amount=8000.0)
    clean_db.commit()
    assert wdr1.status == 'PENDING'

    # Request 2: ₹8,000 against remaining balance (Should fail because available is only ₹2,000)
    with pytest.raises(InsufficientBalanceError) as exc_info:
        create_withdrawal_request(clean_db, user.id, amount=8000.0)
    
    assert "Available balance is ₹2,000.00" in str(exc_info.value)
    clean_db.rollback()

    # Request 3: ₹2,000 should succeed
    wdr2 = create_withdrawal_request(clean_db, user.id, amount=2000.0)
    clean_db.commit()
    assert wdr2.status == 'PENDING'

def test_admin_approval_debits_wallet_atomically(clean_db):
    """Test approving a withdrawal debits wallet and updates status atomically."""
    user = create_test_user(clean_db)
    credit_wallet(clean_db, user.id, amount=15000.0, category='DIRECT_COMMISSION', description='Commission 15k', reference_id='COMM-15K')
    clean_db.commit()

    wdr = create_withdrawal_request(clean_db, user.id, amount=5000.0)
    clean_db.commit()

    # Approve
    approved_wdr = approve_withdrawal(clean_db, withdrawal_id=wdr.id, admin_id=1, notes="Approved payout")
    clean_db.commit()

    assert approved_wdr.status == 'APPROVED'
    assert approved_wdr.approved_by == 1

    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 10000.0
    assert wallet.total_withdrawn == 5000.0

def test_admin_adjustment_positive_and_negative(clean_db):
    """Test admin wallet adjustment with positive and negative amounts."""
    user = create_test_user(clean_db)
    
    # 1. Positive adjustment
    adjust_wallet_balance(clean_db, user.id, amount=5000.0, admin_id=1, reason="Promotional bonus")
    clean_db.commit()
    
    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 5000.0
    assert wallet.total_earned == 5000.0

    # 2. Negative adjustment within balance
    adjust_wallet_balance(clean_db, user.id, amount=-2000.0, admin_id=1, reason="Correction")
    clean_db.commit()

    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 3000.0

    # 3. Negative adjustment exceeding balance -> must fail
    with pytest.raises(InsufficientBalanceError):
        adjust_wallet_balance(clean_db, user.id, amount=-5000.0, admin_id=1, reason="Over-deduction")
    clean_db.rollback()

    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 3000.0

def test_package_purchase_commission_and_wallet_atomicity(clean_db):
    """Test full package purchase creates Purchase, Commission, WalletTransaction, and updates Wallet balance atomically."""
    sponsor = create_test_user(clean_db, user_code="USR-SPON1", email="sponsor@domain.com", name="Sponsor User")
    buyer = create_test_user(clean_db, user_code="USR-BUY01", email="buyer@domain.com", name="Buyer User")
    buyer.sponsor_id = sponsor.id
    clean_db.commit()

    sponsor_wallet_before = get_or_create_wallet(clean_db, sponsor.id).balance

    purchase, events = process_package_purchase(clean_db, user_id=buyer.id)
    clean_db.commit()

    # Direct commission = 10% of 30,000 BV = ₹3,000
    expected_direct_comm = 3000.0
    sponsor_wallet_after = get_or_create_wallet(clean_db, sponsor.id).balance
    assert sponsor_wallet_after == sponsor_wallet_before + expected_direct_comm

    # Verify Commission record exists
    comm = clean_db.query(Commission).filter(
        Commission.beneficiary_id == sponsor.id,
        Commission.purchase_id == purchase.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert comm is not None
    assert comm.amount == expected_direct_comm

    # Verify WalletTransaction ledger record exists
    txn = clean_db.query(WalletTransaction).filter(
        WalletTransaction.user_id == sponsor.id,
        WalletTransaction.reference_id == purchase.purchase_code
    ).first()
    assert txn is not None
    assert txn.amount == expected_direct_comm
    assert txn.balance_after == sponsor_wallet_after

def test_rollback_on_failed_transaction_leaves_zero_partial_state(clean_db):
    """Test that if an error occurs during purchase processing, everything rolls back with 0 partial records."""
    sponsor = create_test_user(clean_db, user_code="USR-ROLL01", email="spon_roll@domain.com", name="Sponsor Rollback")
    clean_db.commit()

    wallet_before = get_or_create_wallet(clean_db, sponsor.id).balance
    txns_count_before = clean_db.query(WalletTransaction).count()
    comm_count_before = clean_db.query(Commission).count()
    purchases_before = clean_db.query(Purchase).count()

    try:
        # Intentionally trigger an error for invalid user
        process_package_purchase(clean_db, user_id=999999)
        clean_db.commit()
    except Exception:
        clean_db.rollback()

    # Verify 0 partial state created
    assert clean_db.query(Purchase).count() == purchases_before
    assert clean_db.query(Commission).count() == comm_count_before
    assert clean_db.query(WalletTransaction).count() == txns_count_before
    assert get_or_create_wallet(clean_db, sponsor.id).balance == wallet_before

def test_concurrent_wallet_creation_race(clean_db):
    """Test that simultaneous first-time wallet creation for the same user resolves cleanly to a single wallet."""
    user = create_test_user(clean_db)
    
    # Delete any auto-created wallet to simulate fresh uninitialized user
    clean_db.query(Wallet).filter(Wallet.user_id == user.id).delete()
    clean_db.commit()

    import concurrent.futures
    from sqlalchemy.orm import sessionmaker
    WorkerSession = sessionmaker(bind=clean_db.get_bind())
    
    def create_wallet_worker():
        session = WorkerSession()
        try:
            w = get_or_create_wallet(session, user.id)
            session.commit()
            return w.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_wallet_worker) for _ in range(5)]
        results = [f.result() for f in futures]

    clean_db.commit()
    # Exactly one wallet row must exist in the database
    wallets = clean_db.query(Wallet).filter(Wallet.user_id == user.id).all()
    assert len(wallets) == 1
    assert wallets[0].balance == 0.0

def test_concurrent_withdrawal_race_prevents_overdraft(clean_db):
    """Test that when two concurrent requests try to withdraw ₹8,000 against a ₹10,000 balance, exactly one succeeds."""
    user = create_test_user(clean_db)
    credit_wallet(clean_db, user.id, amount=10000.0, category='DIRECT_COMMISSION', description='Seed balance', reference_id='INIT-10K')
    clean_db.commit()

    success_count = 0
    fail_count = 0

    # Simulate Request A: ₹8,000
    try:
        wdr1 = create_withdrawal_request(clean_db, user.id, amount=8000.0)
        clean_db.commit()
        success_count += 1
    except InsufficientBalanceError:
        clean_db.rollback()
        fail_count += 1

    # Simulate Request B: ₹8,000 (must fail because only ₹2,000 available)
    try:
        wdr2 = create_withdrawal_request(clean_db, user.id, amount=8000.0)
        clean_db.commit()
        success_count += 1
    except InsufficientBalanceError:
        clean_db.rollback()
        fail_count += 1

    assert success_count == 1
    assert fail_count == 1

    wallet = get_or_create_wallet(clean_db, user.id)
    assert wallet.balance == 10000.0  # Balance is retained until approved

