import pytest
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
# ADVANCED Matching MLM ENGINE TEST SUITE (29 TESTS + ACCEPTANCE TEST)
# ====================================================================

def test_1_exact_pair(client, db_session):
    """1. Exact pair: 30k Left, 30k Right -> ₹10,000 pair bonus, 0 carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['effective_left_bv'] == 30000.0
    assert summary['effective_right_bv'] == 30000.0
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 10000.0
    assert summary['ending_carry_left'] == 0.0
    assert summary['ending_carry_right'] == 0.0

def test_2_unequal_pair(client, db_session):
    """2. Unequal pair: 60k Left, 30k Right -> ₹10,000 pair bonus, Left 30k carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 10000.0
    assert summary['ending_carry_left'] == 30000.0
    assert summary['ending_carry_right'] == 0.0

def test_3_large_left_carry(client, db_session):
    """3. Large left carry: 90k Left, 30k Right -> ₹10,000 bonus, Left 60k carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 90000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 10000.0
    assert summary['ending_carry_left'] == 60000.0
    assert summary['ending_carry_right'] == 0.0

def test_4_large_right_carry(client, db_session):
    """4. Large right carry: 30k Left, 90k Right -> ₹10,000 bonus, Right 60k carry."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 90000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 10000.0
    assert summary['ending_carry_left'] == 0.0
    assert summary['ending_carry_right'] == 60000.0

def test_5_carry_across_slot(client, db_session):
    """5. Carry across slot: Carry forward survives intact into next 12-hour slot."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_1.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_1.slot_id)
    db_session.commit()

    slot_2 = time_provider.next_slot(db_session, admin.id)
    s2_summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_2.slot_id)
    assert s2_summary['carry_forward_left'] == 30000.0
    assert s2_summary['carry_forward_right'] == 0.0
    assert s2_summary['effective_left_bv'] == 30000.0
    assert s2_summary['effective_right_bv'] == 0.0

def test_6_child_volume_propagation(client, db_session):
    """6. Child volume propagation: C under B Left, B under A Left. C purchase 30k -> B Left 30k, A Left 30k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register B under Amol LEFT
    client.post("/api/auth/register", json={
        "full_name": "User B",
        "email": "user_b_6@demo.com",
        "mobile": "9870000001",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "user_b_6@demo.com").first()

    # Register C under B LEFT
    client.post("/api/auth/register", json={
        "full_name": "User C",
        "email": "user_c_6@demo.com",
        "mobile": "9870000002",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": b.referral_code,
        "binary_parent_code": b.user_code,
        "binary_position": "LEFT"
    })
    c = db_session.query(User).filter(User.email == "user_c_6@demo.com").first()

    # C purchases package
    process_package_purchase(db_session, c.id)
    db_session.commit()

    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)

    assert b_sum['effective_left_bv'] == 30000.0
    assert a_sum['effective_left_bv'] == 30000.0

def test_7_multilevel_propagation(client, db_session):
    """7. Multi-level propagation: D -> C Left -> B Left -> A Left: 30k reaches all ancestors."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register B under Amol LEFT
    client.post("/api/auth/register", json={
        "full_name": "Node B", "email": "node_b_7@demo.com", "mobile": "9870000003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "node_b_7@demo.com").first()

    # Register C under B LEFT
    client.post("/api/auth/register", json={
        "full_name": "Node C", "email": "node_c_7@demo.com", "mobile": "9870000004",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": b.referral_code, "binary_parent_code": b.user_code, "binary_position": "LEFT"
    })
    c = db_session.query(User).filter(User.email == "node_c_7@demo.com").first()

    # Register D under C LEFT
    client.post("/api/auth/register", json={
        "full_name": "Node D", "email": "node_d_7@demo.com", "mobile": "9870000005",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": c.referral_code, "binary_parent_code": c.user_code, "binary_position": "LEFT"
    })
    d = db_session.query(User).filter(User.email == "node_d_7@demo.com").first()

    process_package_purchase(db_session, d.id)
    db_session.commit()

    assert pair_service.get_user_pair_summary(db_session, c.id, slot_info.slot_id)['effective_left_bv'] == 30000.0
    assert pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)['effective_left_bv'] == 30000.0
    assert pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)['effective_left_bv'] == 30000.0

def test_8_no_duplicate_propagation(client, db_session):
    """8. No duplicate propagation: Single source purchase creates exactly one 30k VolumeLedger entry per ancestor."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "User 8", "email": "user8@demo.com", "mobile": "9870000006",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    u8 = db_session.query(User).filter(User.email == "user8@demo.com").first()

    purchase, _ = process_package_purchase(db_session, u8.id)
    db_session.commit()

    entries = db_session.query(VolumeLedger).filter(
        VolumeLedger.source_user_id == u8.id,
        VolumeLedger.ancestor_user_id == amol.id
    ).all()
    assert len(entries) == 1
    assert entries[0].amount == 30000.0
    assert entries[0].side == 'LEFT'

def test_9_child_pair_completion(client, db_session):
    """9. Child pair completion: B completes Left 30k, Right 30k -> earns ₹10,000 pair bonus."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register B under Amol LEFT
    client.post("/api/auth/register", json={
        "full_name": "User B 9", "email": "user_b_9@demo.com", "mobile": "9870000007",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "user_b_9@demo.com").first()

    # B gets Left 30k and Right 30k
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    assert b_sum['pair_completed'] is True
    assert b_sum['pair_bonus_earned'] == 10000.0

def test_10_parent_receives_correct_propagated_volume(client, db_session):
    """10. Parent receives correct propagated volume: A receives D's 30k + E's 30k as Left 60k volume."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register B under Amol LEFT
    client.post("/api/auth/register", json={
        "full_name": "B10", "email": "b10@demo.com", "mobile": "9870000008",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b10@demo.com").first()

    # Register D under B LEFT
    client.post("/api/auth/register", json={
        "full_name": "D10", "email": "d10@demo.com", "mobile": "9870000009",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": b.referral_code, "binary_parent_code": b.user_code, "binary_position": "LEFT"
    })
    d = db_session.query(User).filter(User.email == "d10@demo.com").first()

    # Register E under B RIGHT
    client.post("/api/auth/register", json={
        "full_name": "E10", "email": "e10@demo.com", "mobile": "9870000010",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": b.referral_code, "binary_parent_code": b.user_code, "binary_position": "RIGHT"
    })
    e = db_session.query(User).filter(User.email == "e10@demo.com").first()

    process_package_purchase(db_session, d.id)
    process_package_purchase(db_session, e.id)
    db_session.commit()

    # B matched 30k Left, 30k Right -> B pairs
    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    assert b_sum['pair_completed'] is True
    assert b_sum['pair_bonus_earned'] == 10000.0

    # Amol sees D (on B Left) and E (on B Right) both as Amol's LEFT volume (total 60k)
    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum['effective_left_bv'] == 60000.0
    assert a_sum['effective_right_bv'] == 0.0

def test_11_one_pair_per_slot(client, db_session):
    """11. One pair per slot: Max 1 pair paid during a 12-hour slot."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 60000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 10000.0

def test_12_two_or_more_possible_pairs_still_pay_one(client, db_session):
    """12. Two or more possible pairs still pay only one: 90k/90k pays 1 pair (₹10,000), carries 60k/60k."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 90000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 90000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert summary['pair_bonus_earned'] == 10000.0
    assert summary['consumed_left_bv'] == 30000.0
    assert summary['consumed_right_bv'] == 30000.0
    assert summary['ending_carry_left'] == 60000.0
    assert summary['ending_carry_right'] == 60000.0

def test_13_carry_commission(client, db_session):
    """13. Carry commission: 10% override (₹1,000) paid to sponsor on child's pair completion."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Amol sponsors B
    client.post("/api/auth/register", json={
        "full_name": "B13", "email": "b13@demo.com", "mobile": "9870000011",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b13@demo.com").first()

    # B completes a pair
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    # Check Amol receives ZERO Matching / Carry Commission (no upline commission per final rule)
    carry_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.source_user_id == b.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'CARRY_COMMISSION']),
        Commission.slot_id == slot_info.slot_id
    ).all()
    assert len(carry_comm) == 0

def test_14_carry_commission_idempotency(client, db_session):
    """14. Carry commission idempotency: Duplicate evaluate call does not pay carry commission twice."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B14", "email": "b14@demo.com", "mobile": "9870000012",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b14@demo.com").first()

    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    # Re-evaluate
    pair_service.evaluate_and_award_pair(db_session, b.id, slot_info.slot_id)
    db_session.commit()

    comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.source_user_id == b.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'CARRY_COMMISSION']),
        Commission.slot_id == slot_info.slot_id
    ).all()
    assert len(comms) == 0

def test_15_slot_settlement_idempotency(client, db_session):
    """15. Slot settlement idempotency: Calling slot settlement twice does not duplicate records or payouts."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    s1 = pair_service.record_slot_settlement(db_session, amol.id, slot_info.slot_id)
    s2 = pair_service.record_slot_settlement(db_session, amol.id, slot_info.slot_id)
    db_session.commit()

    settlements = db_session.query(SlotSettlement).filter(
        SlotSettlement.user_id == amol.id,
        SlotSettlement.slot_id == slot_info.slot_id
    ).all()
    assert len(settlements) == 1
    assert settlements[0].pairs_paid == 1
    assert settlements[0].pair_bonus == 10000.0

def test_16_permanent_network_survives_slot_rollover(client, db_session):
    """16. Permanent network survives slot rollover: Binary tree members and placement edges remain intact across slot rollover."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "B16", "email": "b16@demo.com", "mobile": "9870000013",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b16@demo.com").first()

    time_provider.next_slot(db_session, admin.id)

    # Verify B still exists and is on Amol's Left
    b_refreshed = db_session.get(User, b.id)
    assert b_refreshed is not None
    assert b_refreshed.binary_parent_id == amol.id
    assert b_refreshed.binary_position == 'LEFT'

def test_17_active_slot_view_resets_correctly(client, db_session):
    """17. Active slot view resets correctly: Active slot view resets current slot volume while carry is preserved."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_1.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_1.slot_id)
    db_session.commit()

    slot_2 = time_provider.next_slot(db_session, admin.id)

    node_s2 = build_binary_tree_node(db_session, amol, depth=2, view_mode='active_slot', slot_id=slot_2.slot_id)
    assert node_s2['current_left_bv'] == 0.0
    assert node_s2['current_right_bv'] == 0.0
    assert node_s2['starting_carry_left'] == 30000.0
    assert node_s2['starting_carry_right'] == 0.0
    assert node_s2['pair_completed'] is False

def test_18_left_carry_stays_left(client, db_session):
    """18. LEFT carry stays LEFT: Never shifts to Right leg."""
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_1.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_1.slot_id)
    db_session.commit()

    slot_2 = time_provider.next_slot(db_session, admin.id)
    s2 = pair_service.get_user_pair_summary(db_session, amol.id, slot_2.slot_id)
    assert s2['carry_forward_left'] == 30000.0
    assert s2['carry_forward_right'] == 0.0

def test_19_right_carry_stays_right(client, db_session):
    """19. RIGHT carry stays RIGHT: Never shifts to Left leg."""
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

def test_20_no_pair_bonus_converted_into_bv(client, db_session):
    """20. No pair bonus converted into BV: ₹10,000 Pair Bonus is wallet commission, does not add to BV."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    # Effective BV was 30k/30k, consumed was 30k/30k, ending carry is 0/0
    assert summary['consumed_left_bv'] == 30000.0
    assert summary['consumed_right_bv'] == 30000.0
    assert summary['ending_carry_left'] == 0.0
    assert summary['ending_carry_right'] == 0.0

def test_21_acceptance_scenario_multilevel(client, db_session):
    """
    21. VERY IMPORTANT ACCEPTANCE TEST:
    Tree:
                 A
                / \
               B   C
              / \
             D   E
    D and E generate 30k BV each -> B completes 30k/30k pair -> B earns ₹10,000 Pair Bonus.
    A receives Left 60k BV (from D on B Left and E on B Right).
    Then C generates 30k BV on Right -> A pairs using Left carry/volume + Right volume -> A receives ₹10,000.
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # 1. Register B under Amol LEFT
    client.post("/api/auth/register", json={
        "full_name": "Acc User B", "email": "acc_b@demo.com", "mobile": "9870000020",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "acc_b@demo.com").first()

    # 2. Register C under Amol RIGHT
    client.post("/api/auth/register", json={
        "full_name": "Acc User C", "email": "acc_c@demo.com", "mobile": "9870000021",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    c = db_session.query(User).filter(User.email == "acc_c@demo.com").first()

    # 3. Register D under B LEFT
    client.post("/api/auth/register", json={
        "full_name": "Acc User D", "email": "acc_d@demo.com", "mobile": "9870000022",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": b.referral_code, "binary_parent_code": b.user_code, "binary_position": "LEFT"
    })
    d = db_session.query(User).filter(User.email == "acc_d@demo.com").first()

    # 4. Register E under B RIGHT
    client.post("/api/auth/register", json={
        "full_name": "Acc User E", "email": "acc_e@demo.com", "mobile": "9870000023",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": b.referral_code, "binary_parent_code": b.user_code, "binary_position": "RIGHT"
    })
    e = db_session.query(User).filter(User.email == "acc_e@demo.com").first()

    # D & E purchase
    process_package_purchase(db_session, d.id)
    process_package_purchase(db_session, e.id)
    db_session.commit()

    # B gets ₹10,000 Pair Bonus
    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    assert b_sum['pair_completed'] is True
    assert b_sum['pair_bonus_earned'] == 10000.0

    # Amol sees 60k Left volume, 0 Right volume -> Amol not paired yet
    a_sum_mid = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum_mid['effective_left_bv'] == 60000.0
    assert a_sum_mid['effective_right_bv'] == 0.0
    assert a_sum_mid['pair_completed'] is False

    # Now C purchases 30k package
    process_package_purchase(db_session, c.id)
    db_session.commit()

    # Amol now has 60k Left, 30k Right -> Amol completes Pair and receives ₹10,000!
    a_sum_final = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum_final['pair_completed'] is True
    assert a_sum_final['pair_bonus_earned'] == 10000.0
    assert a_sum_final['consumed_left_bv'] == 30000.0
    assert a_sum_final['consumed_right_bv'] == 30000.0
    assert a_sum_final['ending_carry_left'] == 30000.0
    assert a_sum_final['ending_carry_right'] == 0.0

def test_22_direct_commission_only_to_actual_sponsor(client, db_session):
    """22. Direct commission only to actual sponsor: A sponsors B -> B purchase -> A gets ₹3,000."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "User 22", "email": "user22@demo.com", "mobile": "9870000030",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "user22@demo.com").first()

    purchase, events = process_package_purchase(db_session, b.id)
    db_session.commit()

    direct_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.source_user_id == b.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert direct_comm is not None
    assert direct_comm.amount == 3000.0

def test_23_placement_parent_is_not_sponsor(client, db_session):
    """23. Placement parent is not sponsor: X sponsors B, A places B -> X gets ₹3,000, A gets ₹0 direct commission."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register sponsor X under Amol
    client.post("/api/auth/register", json={
        "full_name": "Sponsor X", "email": "sponsor_x@demo.com", "mobile": "9870000031",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    x = db_session.query(User).filter(User.email == "sponsor_x@demo.com").first()

    # Register placement parent P under Amol
    client.post("/api/auth/register", json={
        "full_name": "Placement P", "email": "placement_p@demo.com", "mobile": "9870000032",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    p = db_session.query(User).filter(User.email == "placement_p@demo.com").first()

    # Register B: sponsor is X, but Matching parent is P (LEFT)
    client.post("/api/auth/register", json={
        "full_name": "Spillover B", "email": "spillover_b@demo.com", "mobile": "9870000033",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": x.referral_code, "binary_parent_code": p.user_code, "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "spillover_b@demo.com").first()

    process_package_purchase(db_session, b.id)
    db_session.commit()

    # X gets Direct Commission ₹3,000
    x_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == x.id,
        Commission.source_user_id == b.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert x_comm is not None
    assert x_comm.amount == 3000.0

    # P gets NO direct commission
    p_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == p.id,
        Commission.source_user_id == b.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert p_comm is None

def test_24_Matching_volume_still_reaches_placement_ancestors(client, db_session):
    """24. Matching volume still reaches placement ancestors: X sponsors B, P places B LEFT -> P LEFT BV = ₹30,000."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register sponsor X under Amol
    client.post("/api/auth/register", json={
        "full_name": "Sponsor X 24", "email": "sponsor_x24@demo.com", "mobile": "9870000034",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    x = db_session.query(User).filter(User.email == "sponsor_x24@demo.com").first()

    # Register placement parent P under Amol
    client.post("/api/auth/register", json={
        "full_name": "Placement P 24", "email": "placement_p24@demo.com", "mobile": "9870000035",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    p = db_session.query(User).filter(User.email == "placement_p24@demo.com").first()

    # Register B: sponsor is X, Matching parent is P (LEFT)
    client.post("/api/auth/register", json={
        "full_name": "Spillover B 24", "email": "spillover_b24@demo.com", "mobile": "9870000036",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": x.referral_code, "binary_parent_code": p.user_code, "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "spillover_b24@demo.com").first()

    process_package_purchase(db_session, b.id)
    db_session.commit()

    p_sum = pair_service.get_user_pair_summary(db_session, p.id, slot_info.slot_id)
    assert p_sum['effective_left_bv'] == 30000.0

def test_25_direct_commission_and_pair_bonus_independent(client, db_session):
    """25. Direct commission and pair bonus independent: A receives ₹3,000 Direct Commission + ₹10,000 Pair Bonus when both satisfied."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Amol sponsors and places L25 on Left
    client.post("/api/auth/register", json={
        "full_name": "L25", "email": "l25@demo.com", "mobile": "9870000048",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    l25 = db_session.query(User).filter(User.email == "l25@demo.com").first()

    # Amol sponsors and places R25 on Right
    client.post("/api/auth/register", json={
        "full_name": "R25", "email": "r25@demo.com", "mobile": "9870000049",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    r25 = db_session.query(User).filter(User.email == "r25@demo.com").first()

    process_package_purchase(db_session, l25.id)
    process_package_purchase(db_session, r25.id)
    db_session.commit()

    direct_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.source_user_id == l25.id,
        Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])
    ).first()
    pair_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).first()

    assert direct_comm is not None and direct_comm.amount == 3000.0
    assert pair_comm is not None and pair_comm.amount == 10000.0

def test_26_child_pair_does_not_consume_parent_pair(client, db_session):
    """26. Child pair does not consume parent pair: B pair count = 1, A pair count = 0. A can still pair in same slot."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register B under Amol LEFT
    client.post("/api/auth/register", json={
        "full_name": "B26", "email": "b26@demo.com", "mobile": "9870000050",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b26@demo.com").first()

    # Register C under Amol RIGHT
    client.post("/api/auth/register", json={
        "full_name": "C26", "email": "c26@demo.com", "mobile": "9870000059",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })

    # B completes a pair
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    b_sum = pair_service.get_user_pair_summary(db_session, b.id, slot_info.slot_id)
    assert b_sum['pair_completed'] is True

    # Give Amol Left volume and verify Amol has not paired yet (0 Right)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    db_session.commit()

    a_sum = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum['pair_completed'] is False

    # Give Amol Right volume -> Amol pairs independently!
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    a_sum_after = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert a_sum_after['pair_completed'] is True
    assert a_sum_after['pair_bonus_earned'] == 10000.0

def test_27_parent_gets_only_configured_carry_commission(client, db_session):
    """27. Parent gets only configured carry commission from child pair: Child Pair Bonus = ₹10,000 -> Parent gets ₹1,000, not ₹10,000."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B27", "email": "b27@demo.com", "mobile": "9870000060",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b27@demo.com").first()

    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, b.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    # Parent gets ₹0 carry/matching commission per final rule
    carry_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.source_user_id == b.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'CARRY_COMMISSION']),
        Commission.slot_id == slot_info.slot_id
    ).all()
    assert len(carry_comm) == 0

def test_28_parent_one_pair_per_slot(client, db_session):
    """28. Parent one-pair-per-slot: Even if multiple children generate enough volume, parent pair count <= 1."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 120000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 120000.0, slot_info.slot_id)
    db_session.commit()

    comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).all()
    assert len(comms) == 1
    assert comms[0].amount == 10000.0

def test_29_direct_referral_does_not_create_automatic_pair(client, db_session):
    """29. Direct referral does not create automatic pair: A directly recruits B -> A gets ₹3,000, NOT ₹10,000 unless Right leg also qualifies."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    client.post("/api/auth/register", json={
        "full_name": "B29", "email": "b29@demo.com", "mobile": "9870000070",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b = db_session.query(User).filter(User.email == "b29@demo.com").first()

    process_package_purchase(db_session, b.id)
    db_session.commit()

    direct_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.source_user_id == b.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert direct_comm is not None
    assert direct_comm.amount == 3000.0

    pair_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == slot_info.slot_id
    ).first()
    assert pair_comm is None
