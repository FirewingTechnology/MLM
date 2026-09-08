import pytest
from datetime import datetime
from app.config import settings
from app.models.user import User
from app.models.commission import Commission
from app.models.wallet import Wallet, WalletTransaction
from app.models.period_volume import BinaryPeriodVolume
from app.models.volume_ledger import VolumeLedger
from app.models.slot_settlement import SlotSettlement
from app.services.pair_service import pair_service
from app.services.commission_service import process_package_purchase
from app.services.time_service import time_provider, slot_service
from app.services.mlm_service import build_binary_tree_node

# ====================================================================
# ROOT-PERSPECTIVE Matching LEG PROPAGATION & MLM ENGINE TEST SUITE
# TESTS 1 - 20 + SECTION 25 REQUIRED ACCEPTANCE SCENARIO
# ====================================================================

def test_1_a_to_b_left(client, db_session):
    """TEST 1: A -> B LEFT. B purchase ₹30k BV -> Expected: A LEFT = ₹30k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B1", "email": "b1@demo.com", "mobile": "9870010001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b1 = db_session.query(User).filter(User.email == "b1@demo.com").first()

    process_package_purchase(db_session, b1.id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 30000.0
    assert summary['effective_right_bv'] == 0.0

def test_2_a_to_c_right(client, db_session):
    """TEST 2: A -> C RIGHT. C purchase ₹30k BV -> Expected: A RIGHT = ₹30k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "C2", "email": "c2@demo.com", "mobile": "9870010002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    c2 = db_session.query(User).filter(User.email == "c2@demo.com").first()

    process_package_purchase(db_session, c2.id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 0.0
    assert summary['effective_right_bv'] == 30000.0

def test_3_a_has_b_left_and_c_right(client, db_session):
    """TEST 3: A has B LEFT and C RIGHT. B ₹30k, C ₹30k -> Expected: A pair = ₹10k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B3", "email": "b3@demo.com", "mobile": "9870010003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    client.post("/api/auth/register", json={
        "full_name": "C3", "email": "c3@demo.com", "mobile": "9870010004",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    b3 = db_session.query(User).filter(User.email == "b3@demo.com").first()
    c3 = db_session.query(User).filter(User.email == "c3@demo.com").first()

    process_package_purchase(db_session, b3.id)
    process_package_purchase(db_session, c3.id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 15000.0

def test_4_a_to_b_left_to_d_right(client, db_session):
    """TEST 4: A -> B LEFT -> D RIGHT. D ₹30k -> Expected: B RIGHT = ₹30k, A LEFT = ₹30k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B4", "email": "b4@demo.com", "mobile": "9870010005",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b4 = db_session.query(User).filter(User.email == "b4@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "D4", "email": "d4@demo.com", "mobile": "9870010006",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": b4.user_code, "binary_position": "RIGHT"
    })
    d4 = db_session.query(User).filter(User.email == "d4@demo.com").first()

    process_package_purchase(db_session, d4.id)
    db_session.commit()

    b_sum = pair_service.get_user_pair_summary(db_session, b4.id, slot_info.slot_id)
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)

    assert b_sum['effective_right_bv'] == 30000.0
    assert b_sum['effective_left_bv'] == 0.0
    assert a_sum['effective_left_bv'] == 30000.0
    assert a_sum['effective_right_bv'] == 0.0

def test_5_a_to_b_left_to_d_right_to_e_left(client, db_session):
    """TEST 5: A -> B LEFT -> D RIGHT -> E LEFT. E ₹30k -> Expected: D LEFT = ₹30k, B RIGHT = ₹30k, A LEFT = ₹30k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B5", "email": "b5@demo.com", "mobile": "9870010007",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b5 = db_session.query(User).filter(User.email == "b5@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "D5", "email": "d5@demo.com", "mobile": "9870010008",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": b5.user_code, "binary_position": "RIGHT"
    })
    d5 = db_session.query(User).filter(User.email == "d5@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "E5", "email": "e5@demo.com", "mobile": "9870010009",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": d5.user_code, "binary_position": "LEFT"
    })
    e5 = db_session.query(User).filter(User.email == "e5@demo.com").first()

    process_package_purchase(db_session, e5.id)
    db_session.commit()

    d_sum = pair_service.get_user_pair_summary(db_session, d5.id, slot_info.slot_id)
    b_sum = pair_service.get_user_pair_summary(db_session, b5.id, slot_info.slot_id)
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)

    assert d_sum['effective_left_bv'] == 30000.0
    assert d_sum['effective_right_bv'] == 0.0

    assert b_sum['effective_right_bv'] == 30000.0
    assert b_sum['effective_left_bv'] == 0.0

    assert a_sum['effective_left_bv'] == 30000.0
    assert a_sum['effective_right_bv'] == 0.0

def test_6_a_to_c_right_to_f_left_to_g_right(client, db_session):
    """TEST 6: A -> C RIGHT -> F LEFT -> G RIGHT. G ₹30k -> Expected: F RIGHT = ₹30k, C LEFT = ₹30k, A RIGHT = ₹30k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "C6", "email": "c6@demo.com", "mobile": "9870010010",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    c6 = db_session.query(User).filter(User.email == "c6@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "F6", "email": "f6@demo.com", "mobile": "9870010011",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": c6.user_code, "binary_position": "LEFT"
    })
    f6 = db_session.query(User).filter(User.email == "f6@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "G6", "email": "g6@demo.com", "mobile": "9870010012",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": f6.user_code, "binary_position": "RIGHT"
    })
    g6 = db_session.query(User).filter(User.email == "g6@demo.com").first()

    process_package_purchase(db_session, g6.id)
    db_session.commit()

    f_sum = pair_service.get_user_pair_summary(db_session, f6.id, slot_info.slot_id)
    c_sum = pair_service.get_user_pair_summary(db_session, c6.id, slot_info.slot_id)
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)

    assert f_sum['effective_right_bv'] == 30000.0
    assert f_sum['effective_left_bv'] == 0.0

    assert c_sum['effective_left_bv'] == 30000.0
    assert c_sum['effective_right_bv'] == 0.0

    assert a_sum['effective_right_bv'] == 30000.0
    assert a_sum['effective_left_bv'] == 0.0

def test_7_deep_extreme_left_and_extreme_right_pair(client, db_session):
    """TEST 7: Deep extreme-left purchase + deep extreme-right purchase -> Expected: A LEFT >= 30k, A RIGHT >= 30k, A gets ₹15k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Left chain: A -> B -> D -> E (all LEFT)
    client.post("/api/auth/register", json={
        "full_name": "B7", "email": "b7@demo.com", "mobile": "9870010013",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b7 = db_session.query(User).filter(User.email == "b7@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "D7", "email": "d7@demo.com", "mobile": "9870010014",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": b7.user_code, "binary_position": "LEFT"
    })
    d7 = db_session.query(User).filter(User.email == "d7@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "E7", "email": "e7@demo.com", "mobile": "9870010015",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": d7.user_code, "binary_position": "LEFT"
    })
    e7 = db_session.query(User).filter(User.email == "e7@demo.com").first()

    # Right chain: A -> C -> F -> G (all RIGHT)
    client.post("/api/auth/register", json={
        "full_name": "C7", "email": "c7@demo.com", "mobile": "9870010016",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    c7 = db_session.query(User).filter(User.email == "c7@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "F7", "email": "f7@demo.com", "mobile": "9870010017",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": c7.user_code, "binary_position": "RIGHT"
    })
    f7 = db_session.query(User).filter(User.email == "f7@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "G7", "email": "g7@demo.com", "mobile": "9870010018",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": f7.user_code, "binary_position": "RIGHT"
    })
    g7 = db_session.query(User).filter(User.email == "g7@demo.com").first()

    process_package_purchase(db_session, e7.id)
    process_package_purchase(db_session, g7.id)
    db_session.commit()

    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum['effective_left_bv'] == 30000.0
    assert a_sum['effective_right_bv'] == 30000.0
    assert a_sum['pair_completed'] is True
    assert a_sum['pair_bonus_earned'] == 15000.0

def test_8_90k_left_and_90k_right_only_one_pair_per_slot(client, db_session):
    """TEST 8: 90k LEFT + 90k RIGHT -> Expected: Only one pair paid in slot. Carry: LEFT 60k, RIGHT 60k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 90000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 90000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 15000.0
    assert summary['ending_carry_left'] == 60000.0
    assert summary['ending_carry_right'] == 60000.0

def test_9_slot_rollover_preserves_left_and_right_carry(client, db_session):
    """TEST 9: Slot rollover -> Expected: LEFT carry remains LEFT, RIGHT carry remains RIGHT."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 90000.0, slot_1.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_1.slot_id)
    db_session.commit()

    slot_2 = time_provider.next_slot(db_session, admin.id)
    s2_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_2.slot_id)

    assert s2_sum['carry_forward_left'] == 60000.0
    assert s2_sum['carry_forward_right'] == 0.0
    assert s2_sum['effective_left_bv'] == 60000.0
    assert s2_sum['effective_right_bv'] == 0.0

def test_10_direct_sponsor_different_from_placement_parent(client, db_session):
    """TEST 10: Direct sponsor different from placement parent -> Only sponsor gets ₹3,000 direct commission, placement ancestors receive BV only."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Sponsor X
    client.post("/api/auth/register", json={
        "full_name": "Sponsor X 10", "email": "x10@demo.com", "mobile": "9870010019",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    x = db_session.query(User).filter(User.email == "x10@demo.com").first()

    # Placement parent P
    client.post("/api/auth/register", json={
        "full_name": "Placement P 10", "email": "p10@demo.com", "mobile": "9870010020",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    p = db_session.query(User).filter(User.email == "p10@demo.com").first()

    # Member B sponsored by X, placed under P (LEFT)
    client.post("/api/auth/register", json={
        "full_name": "Member B 10", "email": "b10@demo.com", "mobile": "9870010021",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": x.referral_code, "binary_parent_code": p.user_code, "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b10@demo.com").first()

    process_package_purchase(db_session, b.id)
    db_session.commit()

    # X gets ₹3,000 DIRECT_COMMISSION
    x_direct = db_session.query(Commission).filter(
        Commission.beneficiary_id == x.id,
        Commission.source_user_id == b.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert x_direct is not None
    assert x_direct.amount == 3000.0

    # P gets NO direct commission
    p_direct = db_session.query(Commission).filter(
        Commission.beneficiary_id == p.id,
        Commission.source_user_id == b.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert p_direct is None

    # P gets BV on LEFT
    p_sum = pair_service.get_user_pair_summary(db_session, p.id, slot_info.slot_id)
    assert p_sum['effective_left_bv'] == 30000.0

def test_11_child_pair_awards_override_carry_commission(client, db_session):
    """TEST 11: Child pair -> Expected: Child gets ₹15,000. Eligible upline gets configured ₹1,000 carry commission."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Amol sponsors B
    client.post("/api/auth/register", json={
        "full_name": "B11", "email": "b11@demo.com", "mobile": "9870010022",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b11@demo.com").first()

    # B completes a pair
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    # B gets ₹15,000 PAIR_BONUS
    b_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == b.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).first()
    assert b_comm is not None
    assert b_comm.amount == 15000.0

    # Amol gets ₹0 Matching / Carry Commission (no upline commission per final rule)
    a_carry_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.source_user_id == b.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'CARRY_COMMISSION']),
        Commission.slot_id == slot_info.slot_id
    ).all()
    assert len(a_carry_comm) == 0

def test_12_child_pair_does_not_consume_parent_pair_limit(client, db_session):
    """TEST 12: Child pair does not consume parent's pair limit."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B12", "email": "b12@demo.com", "mobile": "9870010023",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b12@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "C12", "email": "c12@demo.com", "mobile": "9870010029",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })

    # B pairs
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    assert b_sum['pair_completed'] is True

    # Amol gets volume and can still complete his own pair in the same slot
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum['pair_completed'] is True
    assert a_sum['pair_bonus_earned'] == 15000.0

def test_13_duplicate_purchase_does_not_duplicate_bv(client, db_session):
    """TEST 13: Duplicate purchase processing does not duplicate BV."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B13", "email": "b13@demo.com", "mobile": "9870010024",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b13@demo.com").first()

    # Process purchase with idempotency key
    p1, _ = process_package_purchase(db_session, b.id, idempotency_key="IDEMP-PUR-13")
    db_session.commit()

    # Process again with same key
    p2, _ = process_package_purchase(db_session, b.id, idempotency_key="IDEMP-PUR-13")
    db_session.commit()

    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum['effective_left_bv'] == 30000.0  # NOT 60,000

def test_14_duplicate_pair_evaluation_does_not_duplicate_payout(client, db_session):
    """TEST 14: Duplicate pair evaluation does not duplicate ₹15,000."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    # Run evaluation again
    pair_service.evaluate_and_award_pair(db_session, amol.id, slot_info.slot_id)
    db_session.commit()

    comm_count = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).count()
    assert comm_count == 1

def test_15_duplicate_settlement_does_not_duplicate_payout(client, db_session):
    """TEST 15: Duplicate settlement does not duplicate payout."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    # Record settlement multiple times
    pair_service.record_slot_settlement(db_session, amol.id, slot_info.slot_id)
    pair_service.record_slot_settlement(db_session, amol.id, slot_info.slot_id)
    db_session.commit()

    settlement_count = db_session.query(SlotSettlement).filter(
        SlotSettlement.user_id == amol.id,
        SlotSettlement.slot_id == slot_info.slot_id
    ).count()
    assert settlement_count == 1

def test_16_permanent_network_remains_unchanged_after_rollover(client, db_session):
    """TEST 16: Permanent network remains unchanged after slot rollover."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "B16", "email": "b16@demo.com", "mobile": "9870010025",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b16@demo.com").first()

    time_provider.next_slot(db_session, admin.id)

    b_refreshed = db_session.get(User, b.id)
    assert b_refreshed is not None
    assert b_refreshed.binary_parent_id == amol.id
    assert b_refreshed.binary_position == 'LEFT'

def test_17_pair_bonus_never_becomes_bv(client, db_session):
    """TEST 17: Pair bonus money never becomes BV."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    # Verify no unexpected extra BV was created
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum['effective_left_bv'] == 30000.0
    assert a_sum['effective_right_bv'] == 30000.0
    assert a_sum['consumed_left_bv'] == 30000.0
    assert a_sum['consumed_right_bv'] == 30000.0
    assert a_sum['ending_carry_left'] == 0.0
    assert a_sum['ending_carry_right'] == 0.0

def test_18_direct_commission_never_becomes_bv(client, db_session):
    """TEST 18: Direct commission money never becomes BV."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B18", "email": "b18@demo.com", "mobile": "9870010026",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b18@demo.com").first()

    process_package_purchase(db_session, b.id)
    db_session.commit()

    # Direct commission is ₹3,000, BV is ₹30,000 (not 33,000)
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum['effective_left_bv'] == 30000.0

def test_19_left_volume_never_becomes_right(client, db_session):
    """TEST 19: LEFT volume never becomes RIGHT."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_1.slot_1 if hasattr(slot_1, 'slot_1') else slot_1.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_1.slot_1 if hasattr(slot_1, 'slot_1') else slot_1.slot_id)
    db_session.commit()

    slot_2 = time_provider.next_slot(db_session, admin.id)
    s2 = pair_service.get_user_pair_summary(db_session, amol.id, slot_2.slot_id)

    assert s2['carry_forward_left'] == 30000.0
    assert s2['carry_forward_right'] == 0.0

def test_20_right_volume_never_becomes_left(client, db_session):
    """TEST 20: RIGHT volume never becomes LEFT."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_1.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 60000.0, slot_1.slot_id)
    db_session.commit()

    slot_2 = time_provider.next_slot(db_session, admin.id)
    s2 = pair_service.get_user_pair_summary(db_session, amol.id, slot_2.slot_id)

    assert s2['carry_forward_left'] == 0.0
    assert s2['carry_forward_right'] == 30000.0

def test_21_required_acceptance_scenario_deep_extreme_descendants(client, db_session):
    """
    SECTION 25 REQUIRED ACCEPTANCE SCENARIO:
                    A
                  /   \
                 B     C
                /       \
               D         F
              /           \
             E             G

    E generates ₹30,000 BV.
    G generates ₹30,000 BV.

    Expected for A:
    LEFT = ₹30,000
    RIGHT = ₹30,000
    A receives: PAIR_BONUS = ₹15,000
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # 1. Build Left Branch: A -> B (LEFT) -> D (LEFT) -> E (LEFT)
    client.post("/api/auth/register", json={
        "full_name": "B Acceptance", "email": "b_acc@demo.com", "mobile": "9870020001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b_acc@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "D Acceptance", "email": "d_acc@demo.com", "mobile": "9870020002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": b.user_code, "binary_position": "LEFT"
    })
    d = db_session.query(User).filter(User.email == "d_acc@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "E Acceptance", "email": "e_acc@demo.com", "mobile": "9870020003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": d.user_code, "binary_position": "LEFT"
    })
    e = db_session.query(User).filter(User.email == "e_acc@demo.com").first()

    # 2. Build Right Branch: A -> C (RIGHT) -> F (RIGHT) -> G (RIGHT)
    client.post("/api/auth/register", json={
        "full_name": "C Acceptance", "email": "c_acc@demo.com", "mobile": "9870020004",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    c = db_session.query(User).filter(User.email == "c_acc@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "F Acceptance", "email": "f_acc@demo.com", "mobile": "9870020005",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": c.user_code, "binary_position": "RIGHT"
    })
    f = db_session.query(User).filter(User.email == "f_acc@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "G Acceptance", "email": "g_acc@demo.com", "mobile": "9870020006",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": f.user_code, "binary_position": "RIGHT"
    })
    g = db_session.query(User).filter(User.email == "g_acc@demo.com").first()

    # 3. E purchases virtual package (₹30,000 BV)
    pur_e, _ = process_package_purchase(db_session, e.id)
    db_session.commit()

    # Check that A has LEFT BV = ₹30,000
    a_sum_after_e = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum_after_e['effective_left_bv'] == 30000.0
    assert a_sum_after_e['effective_right_bv'] == 0.0
    assert a_sum_after_e['pair_completed'] is False

    # Check VolumeLedger entry for E -> A
    v_ea = db_session.query(VolumeLedger).filter(
        VolumeLedger.source_user_id == e.id,
        VolumeLedger.ancestor_user_id == amol.id
    ).first()
    assert v_ea is not None
    assert v_ea.side == 'LEFT'
    assert v_ea.amount == 30000.0

    # 4. G purchases virtual package (₹30,000 BV)
    pur_g, _ = process_package_purchase(db_session, g.id)
    db_session.commit()

    # Check VolumeLedger entry for G -> A
    v_ga = db_session.query(VolumeLedger).filter(
        VolumeLedger.source_user_id == g.id,
        VolumeLedger.ancestor_user_id == amol.id
    ).first()
    assert v_ga is not None
    assert v_ga.side == 'RIGHT'
    assert v_ga.amount == 30000.0

    # Check that A has completed PAIR_BONUS = ₹15,000
    a_sum_final = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum_final['effective_left_bv'] == 30000.0
    assert a_sum_final['effective_right_bv'] == 30000.0
    assert a_sum_final['consumed_left_bv'] == 30000.0
    assert a_sum_final['consumed_right_bv'] == 30000.0
    assert a_sum_final['pair_completed'] is True
    assert a_sum_final['pair_bonus_earned'] == 15000.0
    assert a_sum_final['ending_carry_left'] == 0.0
    assert a_sum_final['ending_carry_right'] == 0.0

    # Check that A received PAIR_BONUS Commission record
    a_pair_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).first()
    assert a_pair_comm is not None
    assert a_pair_comm.amount == 15000.0

    # Check VolumeLedger consumption for A
    db_session.refresh(v_ea)
    db_session.refresh(v_ga)
    assert v_ea.consumed_amount == 30000.0
    assert v_ea.status == 'CONSUMED'
    assert v_ga.consumed_amount == 30000.0
    assert v_ga.status == 'CONSUMED'

    # Verify B and C did NOT receive pairs (only 1-sided volume)
    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    c_sum = pair_service.get_user_pair_summary(db_session, c.id, slot_info.slot_id)
    assert b_sum['pair_completed'] is False
    assert c_sum['pair_completed'] is False

def test_22_acceptance_next_slot_a_does_nothing_descendants_pair_a(client, db_session):
    """
    SECTION 22 SECOND ACCEPTANCE TEST — NEXT SLOT:
    Slot 1: A has B (LEFT, 30k) and C (RIGHT, 30k) -> A pairs (₹15,000).
    Slot 2: A performs NOTHING personally.
    B creates D (LEFT under B, 30k BV).
    C creates F (RIGHT under C, 30k BV).
    A receives LEFT 30k from B subtree, RIGHT 30k from C subtree -> A pairs in Slot 2 (₹15,000).
    B (LEFT 30k, RIGHT 0) and C (RIGHT 30k, LEFT 0) do NOT pair.
    """
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    # Slot 1: Register B and C
    client.post("/api/auth/register", json={
        "full_name": "B22", "email": "b22@demo.com", "mobile": "9870030001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b22@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "C22", "email": "c22@demo.com", "mobile": "9870030002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    c = db_session.query(User).filter(User.email == "c22@demo.com").first()

    process_package_purchase(db_session, b.id)
    process_package_purchase(db_session, c.id)
    db_session.commit()

    # Verify A paired in Slot 1
    a_sum_s1 = pair_service.get_user_pair_summary(db_session, amol.id, slot_1.slot_id)
    assert a_sum_s1['pair_completed'] is True
    assert a_sum_s1['pair_bonus_earned'] == 15000.0

    # Advance to Slot 2
    slot_2 = time_provider.next_slot(db_session, admin.id)

    # In Slot 2, A does nothing. B creates D (LEFT), C creates F (RIGHT)
    client.post("/api/auth/register", json={
        "full_name": "D22", "email": "d22@demo.com", "mobile": "9870030003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": b.user_code, "binary_position": "LEFT"
    })
    d = db_session.query(User).filter(User.email == "d22@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "F22", "email": "f22@demo.com", "mobile": "9870030004",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": c.user_code, "binary_position": "RIGHT"
    })
    f = db_session.query(User).filter(User.email == "f22@demo.com").first()

    process_package_purchase(db_session, d.id)
    process_package_purchase(db_session, f.id)
    db_session.commit()

    # Check A in Slot 2: A completes ANOTHER pair in Slot 2!
    a_sum_s2 = pair_service.get_user_pair_summary(db_session, amol.id, slot_2.slot_id)
    assert a_sum_s2['effective_left_bv'] == 30000.0
    assert a_sum_s2['effective_right_bv'] == 30000.0
    assert a_sum_s2['pair_completed'] is True
    assert a_sum_s2['pair_bonus_earned'] == 15000.0

    # Check B in Slot 2: B has LEFT 30k, RIGHT 0 -> NO pair for B
    b_sum_s2 = pair_service.get_user_pair_summary(db_session, b.id, slot_2.slot_id)
    assert b_sum_s2['effective_left_bv'] == 30000.0
    assert b_sum_s2['effective_right_bv'] == 0.0
    assert b_sum_s2['pair_completed'] is False

    # Check C in Slot 2: C has RIGHT 30k, LEFT 0 -> NO pair for C
    c_sum_s2 = pair_service.get_user_pair_summary(db_session, c.id, slot_2.slot_id)
    assert c_sum_s2['effective_right_bv'] == 30000.0
    assert c_sum_s2['effective_left_bv'] == 0.0
    assert c_sum_s2['pair_completed'] is False

def test_23_acceptance_multiple_child_pairs_independent(client, db_session):
    """
    SECTION 23 THIRD ACCEPTANCE TEST — MULTIPLE CHILD PAIRS:
                    A
                  /   \
                 B     C
                / \   / \
               D   E F   G

    D/E allow B to complete one pair (₹15,000).
    F/G allow C to complete one pair (₹15,000).
    A receives 60k Left and 60k Right -> A completes one pair (₹15,000) and carries 30k Left, 30k Right.
    B gets max 1 pair, C gets max 1 pair, A gets max 1 pair.
    All three pairing calculations are completely independent!
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register B (LEFT of A) and C (RIGHT of A)
    client.post("/api/auth/register", json={
        "full_name": "B23", "email": "b23@demo.com", "mobile": "9870040001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b23@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "C23", "email": "c23@demo.com", "mobile": "9870040002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    c = db_session.query(User).filter(User.email == "c23@demo.com").first()

    # Under B: D (LEFT) and E (RIGHT) sponsored by B
    client.post("/api/auth/register", json={
        "full_name": "D23", "email": "d23@demo.com", "mobile": "9870040003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": b.referral_code, "binary_parent_code": b.user_code, "binary_position": "LEFT"
    })
    d = db_session.query(User).filter(User.email == "d23@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "E23", "email": "e23@demo.com", "mobile": "9870040004",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": b.referral_code, "binary_parent_code": b.user_code, "binary_position": "RIGHT"
    })
    e = db_session.query(User).filter(User.email == "e23@demo.com").first()

    # Under C: F (LEFT) and G (RIGHT) sponsored by C
    client.post("/api/auth/register", json={
        "full_name": "F23", "email": "f23@demo.com", "mobile": "9870040005",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": c.referral_code, "binary_parent_code": c.user_code, "binary_position": "LEFT"
    })
    f = db_session.query(User).filter(User.email == "f23@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "G23", "email": "g23@demo.com", "mobile": "9870040006",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": c.referral_code, "binary_parent_code": c.user_code, "binary_position": "RIGHT"
    })
    g = db_session.query(User).filter(User.email == "g23@demo.com").first()

    # D, E, F, G all purchase virtual packages (₹30,000 BV each)
    process_package_purchase(db_session, d.id)
    process_package_purchase(db_session, e.id)
    process_package_purchase(db_session, f.id)
    process_package_purchase(db_session, g.id)
    db_session.commit()

    # 1. Verify B completed exactly 1 pair (30k L / 30k R) -> ₹15,000
    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    assert b_sum['effective_left_bv'] == 30000.0
    assert b_sum['effective_right_bv'] == 30000.0
    assert b_sum['pair_completed'] is True
    assert b_sum['pair_bonus_earned'] == 15000.0
    assert b_sum['ending_carry_left'] == 0.0
    assert b_sum['ending_carry_right'] == 0.0

    # 2. Verify C completed exactly 1 pair (30k L / 30k R) -> ₹15,000
    c_sum = pair_service.get_user_pair_summary(db_session, c.id, slot_info.slot_id)
    assert c_sum['effective_left_bv'] == 30000.0
    assert c_sum['effective_right_bv'] == 30000.0
    assert c_sum['pair_completed'] is True
    assert c_sum['pair_bonus_earned'] == 15000.0
    assert c_sum['ending_carry_left'] == 0.0
    assert c_sum['ending_carry_right'] == 0.0

    # 3. Verify A completed exactly 1 pair (60k L / 60k R effective, 30k consumed) -> ₹15,000, 30k carry on both sides
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum['effective_left_bv'] == 60000.0
    assert a_sum['effective_right_bv'] == 60000.0
    assert a_sum['consumed_left_bv'] == 30000.0
    assert a_sum['consumed_right_bv'] == 30000.0
    assert a_sum['pair_completed'] is True
    assert a_sum['pair_bonus_earned'] == 15000.0
    assert a_sum['ending_carry_left'] == 30000.0
    assert a_sum['ending_carry_right'] == 30000.0
