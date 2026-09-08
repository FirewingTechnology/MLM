import pytest
from app.models.user import User
from app.models.commission import Commission
from app.models.wallet import Wallet, WalletTransaction
from app.models.period_volume import BinaryPeriodVolume
from app.services.pair_service import pair_service
from app.services.commission_service import process_package_purchase
from app.services.time_service import time_provider, slot_service

def test_no_pair_zero_volume(client, db_session):
    """1. No pair: 0 BV Left, 0 BV Right -> ₹0 bonus, 0 carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)
    
    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 0.0
    assert summary['effective_right_bv'] == 0.0
    assert summary['pair_completed'] is False
    assert summary['pair_bonus_earned'] == 0.0
    assert summary['ending_carry_left'] == 0.0
    assert summary['ending_carry_right'] == 0.0

def test_left_only_volume(client, db_session):
    """2. Left only: 30k BV Left, 0 BV Right -> ₹0 bonus, Left 30k carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register user under Amol LEFT
    reg_left = client.post("/api/auth/register", json={
        "full_name": "Left User",
        "email": "left1@demo.com",
        "mobile": "9999900001",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    assert reg_left.status_code == 201
    user_left = db_session.query(User).filter(User.email == "left1@demo.com").first()

    # Left user purchases 30k package
    process_package_purchase(db_session, user_left.id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 30000.0
    assert summary['effective_right_bv'] == 0.0
    assert summary['pair_completed'] is False
    assert summary['pair_bonus_earned'] == 0.0
    assert summary['ending_carry_left'] == 30000.0
    assert summary['ending_carry_right'] == 0.0

def test_right_only_volume(client, db_session):
    """3. Right only: 0 BV Left, 30k BV Right -> ₹0 bonus, Right 30k carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register user under Amol RIGHT
    reg_right = client.post("/api/auth/register", json={
        "full_name": "Right User",
        "email": "right1@demo.com",
        "mobile": "9999900002",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "RIGHT"
    })
    assert reg_right.status_code == 201
    user_right = db_session.query(User).filter(User.email == "right1@demo.com").first()

    process_package_purchase(db_session, user_right.id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 0.0
    assert summary['effective_right_bv'] == 30000.0
    assert summary['pair_completed'] is False
    assert summary['pair_bonus_earned'] == 0.0
    assert summary['ending_carry_left'] == 0.0
    assert summary['ending_carry_right'] == 30000.0

def test_exact_pair_left_and_right(client, db_session):
    """4. Exact pair: 30k Left, 30k Right -> ₹10,000 pair bonus, 0 carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register Left
    client.post("/api/auth/register", json={
        "full_name": "Left User 4",
        "email": "left4@demo.com",
        "mobile": "9999900003",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    # Register Right
    client.post("/api/auth/register", json={
        "full_name": "Right User 4",
        "email": "right4@demo.com",
        "mobile": "9999900004",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "RIGHT"
    })

    user_left = db_session.query(User).filter(User.email == "left4@demo.com").first()
    user_right = db_session.query(User).filter(User.email == "right4@demo.com").first()

    # Left purchases
    process_package_purchase(db_session, user_left.id)
    # Right purchases
    process_package_purchase(db_session, user_right.id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 30000.0
    assert summary['effective_right_bv'] == 30000.0
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 15000.0
    assert summary['consumed_left_bv'] == 30000.0
    assert summary['consumed_right_bv'] == 30000.0
    assert summary['ending_carry_left'] == 0.0
    assert summary['ending_carry_right'] == 0.0

    # Verify commission record
    pair_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).first()
    assert pair_comm is not None
    assert pair_comm.amount == 15000.0

def test_unequal_pair_left_surplus(client, db_session):
    """5. Unequal pair: 60k Left, 30k Right -> ₹15,000 pair bonus, Left 30k carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register L1 under Amol LEFT
    client.post("/api/auth/register", json={
        "full_name": "L1 User",
        "email": "l1@demo.com",
        "mobile": "9999900005",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    l1 = db_session.query(User).filter(User.email == "l1@demo.com").first()

    # Register L2 under L1 LEFT (bubbles 30k to Amol LEFT)
    client.post("/api/auth/register", json={
        "full_name": "L2 User",
        "email": "l2@demo.com",
        "mobile": "9999900006",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": l1.user_code,
        "binary_position": "LEFT"
    })
    l2 = db_session.query(User).filter(User.email == "l2@demo.com").first()

    # Register R1 under Amol RIGHT
    client.post("/api/auth/register", json={
        "full_name": "R1 User",
        "email": "r1@demo.com",
        "mobile": "9999900007",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "RIGHT"
    })
    r1 = db_session.query(User).filter(User.email == "r1@demo.com").first()

    process_package_purchase(db_session, l1.id)
    process_package_purchase(db_session, l2.id)
    process_package_purchase(db_session, r1.id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 60000.0
    assert summary['effective_right_bv'] == 30000.0
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 15000.0
    assert summary['consumed_left_bv'] == 30000.0
    assert summary['consumed_right_bv'] == 30000.0
    assert summary['ending_carry_left'] == 30000.0
    assert summary['ending_carry_right'] == 0.0

def test_opposite_unequal_pair_right_surplus(client, db_session):
    """6. Opposite unequal pair: 30k Left, 60k Right -> ₹15,000 pair bonus, Right 30k carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register L1
    client.post("/api/auth/register", json={
        "full_name": "L1 User 6",
        "email": "l1_6@demo.com",
        "mobile": "9999900008",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    l1 = db_session.query(User).filter(User.email == "l1_6@demo.com").first()

    # Register R1
    client.post("/api/auth/register", json={
        "full_name": "R1 User 6",
        "email": "r1_6@demo.com",
        "mobile": "9999900009",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "RIGHT"
    })
    r1 = db_session.query(User).filter(User.email == "r1_6@demo.com").first()

    # Register R2 under R1 RIGHT
    client.post("/api/auth/register", json={
        "full_name": "R2 User 6",
        "email": "r2_6@demo.com",
        "mobile": "9999900010",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": r1.user_code,
        "binary_position": "RIGHT"
    })
    r2 = db_session.query(User).filter(User.email == "r2_6@demo.com").first()

    process_package_purchase(db_session, l1.id)
    process_package_purchase(db_session, r1.id)
    process_package_purchase(db_session, r2.id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 30000.0
    assert summary['effective_right_bv'] == 60000.0
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 15000.0
    assert summary['consumed_left_bv'] == 30000.0
    assert summary['consumed_right_bv'] == 30000.0
    assert summary['ending_carry_left'] == 0.0
    assert summary['ending_carry_right'] == 30000.0

def test_large_volume_capped_at_one_pair(client, db_session):
    """7. Large volume: 90k Left, 90k Right in same period -> ₹15,000 only (1 pair cap), 60k/60k carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 90000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 90000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 90000.0
    assert summary['effective_right_bv'] == 90000.0
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 15000.0  # Max 1 pair
    assert summary['consumed_left_bv'] == 30000.0
    assert summary['consumed_right_bv'] == 30000.0
    assert summary['ending_carry_left'] == 60000.0
    assert summary['ending_carry_right'] == 60000.0

def test_duplicate_retry_idempotency(client, db_session):
    """8. Duplicate / Retry request idempotency: Calling evaluate multiple times does not double credit."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    # Re-evaluate
    res2 = pair_service.evaluate_and_award_pair(db_session, amol.id, slot_info.slot_id)
    assert res2 is None

    # Count pair commissions
    comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).all()
    assert len(comms) == 1

def test_period_transition_carry_persistence(client, db_session):
    """9. Period transition: Carry forward survives intact into next 12-hour period."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    # In Slot 1: Add 60k Left, 30k Right -> Pays 1 pair, 30k Left carry, 0 Right carry
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_1.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_1.slot_id)
    db_session.commit()

    s1_summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_1.slot_id)
    assert s1_summary['ending_carry_left'] == 30000.0
    assert s1_summary['ending_carry_right'] == 0.0

    # Advance to next slot
    slot_2 = time_provider.next_slot(db_session, admin.id)
    assert slot_2.slot_id != slot_1.slot_id

    # Check Slot 2 summary before any new purchases
    s2_summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_2.slot_id)
    assert s2_summary['carry_forward_left'] == 30000.0
    assert s2_summary['carry_forward_right'] == 0.0
    assert s2_summary['current_left_bv'] == 0.0
    assert s2_summary['current_right_bv'] == 0.0
    assert s2_summary['effective_left_bv'] == 30000.0
    assert s2_summary['effective_right_bv'] == 0.0
    assert s2_summary['pair_completed'] is False
    assert s2_summary['pair_bonus_earned'] == 0.0

def test_carry_plus_new_bv_pair_completion(client, db_session):
    """10. Carry + New BV: 30k carry Left + 30k new BV Right in new period -> ₹15,000 pair bonus."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    # In Slot 1: 30k Left only
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_1.slot_id)
    db_session.commit()

    # Move to Slot 2
    slot_2 = time_provider.next_slot(db_session, admin.id)

    # In Slot 2: Add 30k Right
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_2.slot_id)
    db_session.commit()

    s2_summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_2.slot_id)
    assert s2_summary['carry_forward_left'] == 30000.0
    assert s2_summary['current_right_bv'] == 30000.0
    assert s2_summary['effective_left_bv'] == 30000.0
    assert s2_summary['effective_right_bv'] == 30000.0
    assert s2_summary['pair_completed'] is True
    assert s2_summary['pair_bonus_earned'] == 15000.0
    assert s2_summary['ending_carry_left'] == 0.0
    assert s2_summary['ending_carry_right'] == 0.0

def test_wallet_consistency(client, db_session):
    """11. Wallet consistency: Exactly ₹15,000 credited to wallet ledger per pair payout."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)
    wallet = db_session.query(Wallet).filter(Wallet.user_id == amol.id).first()
    initial_balance = wallet.balance

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    db_session.refresh(wallet)
    assert wallet.balance == initial_balance + 15000.0

    # Verify wallet transaction record
    txn = db_session.query(WalletTransaction).filter(
        WalletTransaction.user_id == amol.id,
        WalletTransaction.category == 'PAIR_BONUS',
        WalletTransaction.slot_id == slot_info.slot_id
    ).first()
    assert txn is not None
    assert txn.amount == 15000.0
    assert txn.transaction_type == 'CREDIT'

def test_commission_consistency(client, db_session):
    """12. Commission consistency: Exactly 1 PAIR_BONUS commission record created with full audit details."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).first()
    assert comm is not None
    assert comm.amount == 15000.0
    assert comm.bv_basis == 30000.0
    assert round(comm.percentage, 2) == 50.0   # 15000 / 30000 = 50%
    assert 'effective_left_bv' in comm.calculation_details
    assert 'ending_carry_left' in comm.calculation_details
