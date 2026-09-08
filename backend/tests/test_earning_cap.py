import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.package import Package
from app.models.commission import Commission
from app.models.wallet import Wallet, WalletTransaction
from app.models.earning_cycle import EarningCycle
from app.security import hash_password, create_access_token
from app.services.wallet_service import credit_wallet, debit_wallet
from app.services.commission_service import process_package_purchase
from app.services.earning_cap_service import (
    get_or_create_active_cycle,
    apply_commission_with_cap,
    activate_or_renew_earning_cycle,
    get_user_earning_cap_overview,
    get_admin_earning_caps,
    admin_override_reset_cycle
)

def test_earning_cap_direct_and_pairing_accumulation(db_session):
    """
    Test 1: User earns ₹1,00,000 direct + ₹1,00,000 pairing.
    Expected: ₹2,00,000 cycle total, status remains ACTIVE, remaining capacity ₹1,00,000.
    """
    user = User(
        user_code="USR-CAP-1",
        email="cap1@test.com",
        mobile="9810000001",
        full_name="Cap User 1",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="CAP001",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    # Credit ₹1,00,000 Direct Commission
    comm1, txn1, sum1 = apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type="DIRECT_REFERRAL",
        requested_amount=100000.0,
        wallet_category="DIRECT_COMMISSION",
        description="Direct bonus 100k"
    )
    assert sum1['allowed_amount'] == 100000.0
    assert sum1['blocked_amount'] == 0.0
    assert not sum1['is_capped']
    assert txn1.amount == 100000.0

    # Credit ₹1,00,000 Pairing Commission
    comm2, txn2, sum2 = apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type="PAIR_BONUS",
        requested_amount=100000.0,
        wallet_category="PAIR_BONUS",
        description="Pairing bonus 100k"
    )
    assert sum2['allowed_amount'] == 100000.0
    assert sum2['blocked_amount'] == 0.0

    cycle = get_or_create_active_cycle(db_session, user.id)
    assert cycle.direct_income == 100000.0
    assert cycle.pairing_income == 100000.0
    assert cycle.total_eligible_income == 200000.0
    assert cycle.remaining_capacity == 100000.0
    assert cycle.status == 'ACTIVE'
    assert user.earning_status == 'ACTIVE'

def test_exact_earning_cap_reached_retopup_required(db_session):
    """
    Test 2 & 3: User earns exactly ₹3,00,000.
    Expected: Status becomes RETOPUP_REQUIRED.
    Attempting another ₹1,000 commission credits ₹0 and records ₹1,000 blocked.
    """
    user = User(
        user_code="USR-CAP-2",
        email="cap2@test.com",
        mobile="9810000002",
        full_name="Cap User 2",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="CAP002",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    # Credit ₹3,00,000 in one or two hits
    apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type="DIRECT_REFERRAL",
        requested_amount=300000.0,
        wallet_category="DIRECT_COMMISSION",
        description="Direct bonus 300k"
    )

    db_session.refresh(user)
    cycle = get_or_create_active_cycle(db_session, user.id)
    assert cycle.total_eligible_income == 300000.0
    assert cycle.remaining_capacity == 0.0
    assert cycle.status == 'RETOPUP_REQUIRED'
    assert user.earning_status == 'RETOPUP_REQUIRED'
    assert cycle.capped_at is not None

    # Check user wallet balance is ₹300,000
    wallet = db_session.query(Wallet).filter(Wallet.user_id == user.id).first()
    assert wallet.balance == 300000.0

    # Attempt another ₹1,000 commission
    comm_blocked, txn_blocked, sum_blocked = apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type="PAIR_BONUS",
        requested_amount=1000.0,
        wallet_category="PAIR_BONUS",
        description="Pair bonus blocked"
    )
    assert sum_blocked['allowed_amount'] == 0.0
    assert sum_blocked['blocked_amount'] == 1000.0
    assert sum_blocked['is_capped'] is True
    assert txn_blocked is None

    # Verify commission row recorded
    assert comm_blocked.amount == 0.0
    assert comm_blocked.requested_amount == 1000.0
    assert comm_blocked.blocked_amount == 1000.0
    assert comm_blocked.is_capped is True
    assert "re-topup required" in comm_blocked.cap_reason.lower()

    # Wallet balance MUST remain strictly ₹300,000 (no leakage)
    db_session.refresh(wallet)
    assert wallet.balance == 300000.0

def test_partial_commission_capping_at_boundary(db_session):
    """
    Test 4: User at ₹2,95,000 gets a ₹12,000 commission.
    Expected:
    - Allowed / Credited: ₹5,000
    - Blocked: ₹7,000
    - Cycle Total: ₹3,00,000
    - Status: RETOPUP_REQUIRED
    """
    user = User(
        user_code="USR-CAP-3",
        email="cap3@test.com",
        mobile="9810000003",
        full_name="Cap User 3",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="CAP003",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    # Pre-fill cycle with ₹2,95,000
    apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type="DIRECT_REFERRAL",
        requested_amount=295000.0,
        wallet_category="DIRECT_COMMISSION",
        description="Initial 295k"
    )

    # Now generate a ₹12,000 commission
    comm, txn, summary = apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type="PAIR_BONUS",
        requested_amount=12000.0,
        wallet_category="PAIR_BONUS",
        description="12k commission near boundary"
    )

    assert summary['allowed_amount'] == 5000.0
    assert summary['blocked_amount'] == 7000.0
    assert summary['is_capped'] is True
    assert txn.amount == 5000.0

    cycle = get_or_create_active_cycle(db_session, user.id)
    assert cycle.total_eligible_income == 300000.0
    assert cycle.status == 'RETOPUP_REQUIRED'
    assert comm.amount == 5000.0
    assert comm.requested_amount == 12000.0
    assert comm.blocked_amount == 7000.0
    assert comm.is_capped is True

def test_repurchase_creates_new_cycle_and_resets_counter(db_session):
    """
    Test 5: Repurchase successfully completed via process_package_purchase.
    Expected:
    - Old cycle marked COMPLETED.
    - New cycle (Cycle 2) created with counter ₹0.
    - Status reset to ACTIVE.
    - Lifetime earnings preserved.
    """
    user = User(
        user_code="USR-CAP-4",
        email="cap4@test.com",
        mobile="9810000004",
        full_name="Cap User 4",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="CAP004",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    # First package purchase
    process_package_purchase(db_session, user.id)

    # Earn ₹3,00,000
    apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type="DIRECT_REFERRAL",
        requested_amount=300000.0,
        wallet_category="DIRECT_COMMISSION",
        description="Cycle 1 300k"
    )
    cycle1 = get_or_create_active_cycle(db_session, user.id)
    assert cycle1.status == 'RETOPUP_REQUIRED'
    assert cycle1.cycle_number == 1

    # Now repurchase package
    process_package_purchase(db_session, user.id)
    db_session.refresh(user)

    # Verify Cycle 1 completed and Cycle 2 active
    c1 = db_session.query(EarningCycle).filter(EarningCycle.user_id == user.id, EarningCycle.cycle_number == 1).first()
    assert c1.status == 'COMPLETED'
    assert c1.reset_at is not None

    c2 = db_session.query(EarningCycle).filter(EarningCycle.user_id == user.id, EarningCycle.cycle_number == 2).first()
    assert c2.status == 'ACTIVE'
    assert c2.direct_income == 0.0
    assert c2.pairing_income == 0.0
    assert c2.total_eligible_income == 0.0
    assert c2.remaining_capacity == 300000.0
    assert user.earning_status == 'ACTIVE'

    # Verify overview shows lifetime earnings intact
    overview = get_user_earning_cap_overview(db_session, user.id)
    assert overview['cycle_number'] == 2
    assert overview['total_eligible_income'] == 0.0
    assert overview['lifetime_eligible_income'] == 300000.0
    assert overview['completed_cycles_count'] == 1

def test_unrelated_wallet_operations_do_not_affect_cap(db_session):
    """
    Test 9, 10, 11, 12, 13, 14:
    - Wallet deposits / admin adjustments do NOT count toward earning cap.
    - Withdrawals do NOT reduce earning cap counter.
    - Only Direct + Pairing commissions count.
    """
    user = User(
        user_code="USR-CAP-5",
        email="cap5@test.com",
        mobile="9810000005",
        full_name="Cap User 5",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="CAP005",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    cycle = get_or_create_active_cycle(db_session, user.id)

    # 1. Direct wallet credit of ₹50,000 (deposit / manual credit)
    credit_wallet(db_session, user.id, 50000.0, category='DEPOSIT', description='Bank Deposit')
    db_session.refresh(cycle)
    assert cycle.total_eligible_income == 0.0  # Must NOT count

    # 2. Add ₹1,00,000 Direct Commission
    apply_commission_with_cap(db_session, user.id, 'DIRECT_REFERRAL', 100000.0, wallet_category='DIRECT_COMMISSION', description='Direct')
    db_session.refresh(cycle)
    assert cycle.total_eligible_income == 100000.0

    # 3. Withdraw ₹40,000
    debit_wallet(db_session, user.id, 40000.0, category='WITHDRAWAL', description='Bank Withdrawal')
    db_session.refresh(cycle)
    # Withdrawal must NOT reduce the ₹1,00,000 earning counter
    assert cycle.total_eligible_income == 100000.0
    assert cycle.remaining_capacity == 200000.0

def test_admin_earning_cap_endpoints_and_override_reset(client, db_session):
    """
    Test Admin Earning Cap visibility, filters, and audited override reset.
    """
    # Create Admin
    admin = User(
        user_code="ADM-CAP",
        email="admin_cap@test.com",
        mobile="9900000001",
        full_name="Admin Cap",
        password_hash=hash_password("Admin@123"),
        role="ADMIN",
        referral_code="ADMCAP",
        is_active=True
    )
    # Create User
    target_user = User(
        user_code="USR-TGT-1",
        email="target1@test.com",
        mobile="9900000002",
        full_name="Target User",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="TGT001",
        is_active=True
    )
    db_session.add_all([admin, target_user])
    db_session.commit()

    # Cap target user at ₹3,00,000
    apply_commission_with_cap(db_session, target_user.id, 'DIRECT_REFERRAL', 300000.0, wallet_category='DIRECT_COMMISSION', description='Capping')
    db_session.commit()

    admin_token = create_access_token(user_id=admin.id, role="ADMIN")
    user_token = create_access_token(user_id=target_user.id, role="USER")

    # 1. User Overview Endpoint
    res_user = client.get("/api/earning-cap/overview", headers={"Authorization": f"Bearer {user_token}"})
    assert res_user.status_code == 200
    data_user = res_user.json()
    assert data_user['is_retopup_required'] is True
    assert data_user['remaining_capacity'] == 0.0
    assert data_user['status'] == 'RETOPUP_REQUIRED'

    # 2. Admin List Endpoint
    res_admin = client.get("/api/earning-cap/admin/list?status=RETOPUP_REQUIRED", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert data_admin['total'] >= 1
    item = next(i for i in data_admin['items'] if i['user_id'] == target_user.id)
    assert item['status'] == 'RETOPUP_REQUIRED'

    # 3. Admin User History Endpoint
    res_hist = client.get(f"/api/earning-cap/admin/{target_user.id}/history", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_hist.status_code == 200
    assert len(res_hist.json()['cycles']) >= 1

    # 4. Admin Override Reset (Requires Reason)
    res_override_invalid = client.post(
        f"/api/earning-cap/admin/{target_user.id}/override-reset",
        json={"reason": "bad"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_override_invalid.status_code == 422 or res_override_invalid.status_code == 400

    res_override = client.post(
        f"/api/earning-cap/admin/{target_user.id}/override-reset",
        json={"reason": "Approved administrative top-up grace period exception"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_override.status_code == 200
    new_c = res_override.json()['new_cycle']
    assert new_c['cycle_number'] == 2
    assert new_c['status'] == 'ACTIVE'
    assert new_c['total_eligible_income'] == 0.0

def test_concurrency_safe_capping_near_boundary(db_session):
    """
    Test Concurrency / Sequential boundary safety:
    User has ₹2,90,000.
    Three simultaneous/sequential commission events of ₹10,000 each arrive.
    Expected:
    - Event 1: ₹10,000 credited (Total: ₹3,00,000, Status: RETOPUP_REQUIRED)
    - Event 2: ₹0 credited, ₹10,000 blocked
    - Event 3: ₹0 credited, ₹10,000 blocked
    - Cycle total remains EXACTLY ₹3,00,000 and NEVER exceeds it.
    """
    user = User(
        user_code="USR-CONC-1",
        email="conc1@test.com",
        mobile="9900000011",
        full_name="Concurrency User",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="CONC01",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    # Pre-fill with ₹2,90,000
    apply_commission_with_cap(db_session, user.id, 'DIRECT_REFERRAL', 290000.0, wallet_category='DIRECT_COMMISSION', description='290k')

    results = []
    for i in range(3):
        _, _, sumry = apply_commission_with_cap(
            db=db_session,
            user_id=user.id,
            commission_type='PAIR_BONUS',
            requested_amount=10000.0,
            wallet_category='PAIR_BONUS',
            description=f'Batch pair bonus {i}'
        )
        results.append(sumry)

    assert results[0]['allowed_amount'] == 10000.0
    assert results[0]['blocked_amount'] == 0.0

    assert results[1]['allowed_amount'] == 0.0
    assert results[1]['blocked_amount'] == 10000.0
    assert results[1]['is_capped'] is True

    assert results[2]['allowed_amount'] == 0.0
    assert results[2]['blocked_amount'] == 10000.0
    assert results[2]['is_capped'] is True

    cycle = get_or_create_active_cycle(db_session, user.id)
    assert cycle.total_eligible_income == 300000.0
    assert cycle.status == 'RETOPUP_REQUIRED'
