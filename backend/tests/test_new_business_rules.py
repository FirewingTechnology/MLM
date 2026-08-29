import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.wallet import Wallet, WalletTransaction
from app.models.commission import Commission
from app.models.volume_ledger import VolumeLedger
from app.models.slot_settlement import SlotSettlement
from app.models.volume import BinaryVolume
from app.services.commission_service import process_package_purchase
from app.services.pair_service import pair_service
from app.services.wallet_service import get_or_create_wallet
from app.services.mlm_service import get_or_create_binary_volume
from app.services.time_service import time_provider
from app.security import hash_password


def create_user_helper(db: Session, email: str, full_name: str, sponsor_id=None, binary_parent_id=None, binary_position=None, role="USER"):
    code = f"USR{abs(hash(email)) % 1000000:06d}"
    user = User(
        email=email,
        mobile=f"+91{abs(hash(email)) % 10000000000:010d}",
        full_name=full_name,
        user_code=code,
        referral_code=code,
        password_hash=hash_password("password123"),
        sponsor_id=sponsor_id,
        binary_parent_id=binary_parent_id,
        binary_position=binary_position,
        role=role,
        is_active=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    get_or_create_wallet(db, user.id)
    get_or_create_binary_volume(db, user.id)
    return user


def get_default_package(db: Session):
    pkg = db.query(Package).filter(Package.price == 35000.0).first()
    if not pkg:
        pkg = Package(
            name="Alpha Starter Package",
            price=35000.0,
            bv=30000.0,
            direct_commission_rate=0.10,
            pair_bonus_amount=10000.0,
            is_active=True
        )
        db.add(pkg)
        db.commit()
        db.refresh(pkg)
    return pkg


# =========================================================================
# TEST 1: Registration Alone Pays Nothing
# =========================================================================
def test_1_registration_alone_pays_nothing(db_session: Session):
    root = create_user_helper(db_session, "t1_root@mlm.local", "T1 Root")
    child = create_user_helper(db_session, "t1_child@mlm.local", "T1 Child", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")

    root_wallet = get_or_create_wallet(db_session, root.id)
    child_wallet = get_or_create_wallet(db_session, child.id)
    root_volume = get_or_create_binary_volume(db_session, root.id)

    assert root_wallet.balance == 0.0
    assert root_wallet.total_earned == 0.0
    assert child_wallet.balance == 0.0
    assert root_volume.accumulated_left_bv == 0.0
    assert root_volume.accumulated_right_bv == 0.0
    assert db_session.query(Commission).count() == 0


# =========================================================================
# TEST 2: Direct Sponsor Purchase Pays 10% Direct Commission
# =========================================================================
def test_2_direct_sponsor_purchase_pays_10_percent(db_session: Session):
    root = create_user_helper(db_session, "t2_root@mlm.local", "T2 Root")
    child = create_user_helper(db_session, "t2_child@mlm.local", "T2 Child", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    pkg = get_default_package(db_session)

    purchase, events = process_package_purchase(db_session, child.id, pkg.id, slot_id="SLOT-T2")
    assert purchase is not None
    assert len(events) > 0

    root_wallet = get_or_create_wallet(db_session, root.id)
    assert root_wallet.balance == 3000.0
    assert root_wallet.total_earned == 3000.0

    direct_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])
    ).first()
    assert direct_comm is not None
    assert direct_comm.amount == 3000.0
    assert direct_comm.source_user_id == child.id


# =========================================================================
# TEST 3: Multiple Direct Purchases Pay 10% Each Time
# =========================================================================
def test_3_multiple_direct_purchases_pay_each_time(db_session: Session):
    root = create_user_helper(db_session, "t3_root@mlm.local", "T3 Root")
    c1 = create_user_helper(db_session, "t3_c1@mlm.local", "T3 Child 1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    c2 = create_user_helper(db_session, "t3_c2@mlm.local", "T3 Child 2", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    process_package_purchase(db_session, c1.id, pkg.id, slot_id="SLOT-T3")
    process_package_purchase(db_session, c2.id, pkg.id, slot_id="SLOT-T3")

    root_wallet = get_or_create_wallet(db_session, root.id)
    # Direct commission from c1 (3000) + from c2 (3000) + Pair bonus from pairing c1 & c2 (10000) = 16000
    assert root_wallet.balance == 16000.0
    direct_comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])
    ).all()
    assert len(direct_comms) == 2
    assert sum(c.amount for c in direct_comms) == 6000.0


# =========================================================================
# TEST 4: Own First Pair Pays ₹10,000 Pair Bonus (30k L / 30k R)
# =========================================================================
def test_4_own_first_pair_pays_10000(db_session: Session):
    root = create_user_helper(db_session, "t4_root@mlm.local", "T4 Root")
    left_child = create_user_helper(db_session, "t4_left@mlm.local", "T4 Left", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    right_child = create_user_helper(db_session, "t4_right@mlm.local", "T4 Right", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    process_package_purchase(db_session, left_child.id, pkg.id, slot_id="SLOT-T4")
    process_package_purchase(db_session, right_child.id, pkg.id, slot_id="SLOT-T4")

    pair_bonus = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert pair_bonus is not None
    assert pair_bonus.amount == 10000.0

    root_wallet = get_or_create_wallet(db_session, root.id)
    # 3000 + 3000 direct + 10000 pair bonus = 16000
    assert root_wallet.balance == 16000.0


# =========================================================================
# TEST 5: Second Pair in Same Slot Does Not Pay (Max 1 Pair Bonus / Slot)
# =========================================================================
def test_5_second_pair_in_same_slot_capped(db_session: Session):
    root = create_user_helper(db_session, "t5_root@mlm.local", "T5 Root")
    l1 = create_user_helper(db_session, "t5_l1@mlm.local", "T5 L1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    r1 = create_user_helper(db_session, "t5_r1@mlm.local", "T5 R1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    l2 = create_user_helper(db_session, "t5_l2@mlm.local", "T5 L2", sponsor_id=root.id, binary_parent_id=l1.id, binary_position="LEFT")
    r2 = create_user_helper(db_session, "t5_r2@mlm.local", "T5 R2", sponsor_id=root.id, binary_parent_id=r1.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    # 4 purchases in the same slot
    process_package_purchase(db_session, l1.id, pkg.id, slot_id="SLOT-T5-1")
    process_package_purchase(db_session, r1.id, pkg.id, slot_id="SLOT-T5-1")
    process_package_purchase(db_session, l2.id, pkg.id, slot_id="SLOT-T5-1")
    process_package_purchase(db_session, r2.id, pkg.id, slot_id="SLOT-T5-1")

    pair_bonuses = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == "SLOT-T5-1"
    ).all()
    # Exactly 1 Pair Bonus paid in this slot
    assert len(pair_bonuses) == 1
    assert pair_bonuses[0].amount == 10000.0

    # Check that excess BV is carried forward
    summary = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-T5-1")
    assert summary['ending_carry_left'] == 30000.0
    assert summary['ending_carry_right'] == 30000.0


# =========================================================================
# TEST 6: Next Slot Pair Evaluation with Carried BV
# =========================================================================
def test_6_next_slot_pair_evaluation(db_session: Session):
    root = create_user_helper(db_session, "t6_root@mlm.local", "T6 Root")
    l1 = create_user_helper(db_session, "t6_l1@mlm.local", "T6 L1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    r1 = create_user_helper(db_session, "t6_r1@mlm.local", "T6 R1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    l2 = create_user_helper(db_session, "t6_l2@mlm.local", "T6 L2", sponsor_id=root.id, binary_parent_id=l1.id, binary_position="LEFT")
    r2 = create_user_helper(db_session, "t6_r2@mlm.local", "T6 R2", sponsor_id=root.id, binary_parent_id=r1.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    # Slot 1: L1 & R1 & L2 & R2 buy in Slot 1 -> 60k L / 60k R -> 1 pair paid, 30k L / 30k R carry
    process_package_purchase(db_session, l1.id, pkg.id, slot_id="SLOT-T6-1")
    process_package_purchase(db_session, r1.id, pkg.id, slot_id="SLOT-T6-1")
    process_package_purchase(db_session, l2.id, pkg.id, slot_id="SLOT-T6-1")
    process_package_purchase(db_session, r2.id, pkg.id, slot_id="SLOT-T6-1")

    # Slot 2 rollover: evaluate pairs in Slot 2
    res = pair_service.evaluate_and_award_pair(db_session, root.id, slot_id="SLOT-T6-2")
    assert res is not None
    assert res['amount'] == 10000.0
    assert res['slot_id'] == "SLOT-T6-2"

    pair_bonuses = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).all()
    assert len(pair_bonuses) == 2


# =========================================================================
# TEST 7: Sponsor Gets Matching Commission When Child Pairs (10% = ₹1,000)
# =========================================================================
def test_7_sponsor_gets_matching_commission_when_child_pairs(db_session: Session):
    root = create_user_helper(db_session, "t7_root@mlm.local", "T7 Root")
    # Child A is sponsored by root
    child_a = create_user_helper(db_session, "t7_a@mlm.local", "T7 Child A", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    # A sponsors and places A1 (LEFT) and A2 (RIGHT)
    a1 = create_user_helper(db_session, "t7_a1@mlm.local", "T7 A1", sponsor_id=child_a.id, binary_parent_id=child_a.id, binary_position="LEFT")
    a2 = create_user_helper(db_session, "t7_a2@mlm.local", "T7 A2", sponsor_id=child_a.id, binary_parent_id=child_a.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    process_package_purchase(db_session, a1.id, pkg.id, slot_id="SLOT-T7")
    process_package_purchase(db_session, a2.id, pkg.id, slot_id="SLOT-T7")

    # Child A completed a pair
    a_pair = db_session.query(Commission).filter(
        Commission.beneficiary_id == child_a.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert a_pair is not None
    assert a_pair.amount == 10000.0

    # Root gets Matching Commission of ₹1,000 (10% of A's ₹10,000 Pair Bonus)
    root_matching = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])
    ).first()
    assert root_matching is not None
    assert root_matching.amount == 1000.0
    assert root_matching.source_user_id == child_a.id

    # Check Root wallet includes the ₹1,000 matching commission
    root_txn = db_session.query(WalletTransaction).filter(
        WalletTransaction.user_id == root.id,
        WalletTransaction.category.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])
    ).first()
    assert root_txn is not None
    assert root_txn.amount == 1000.0


# =========================================================================
# TEST 8: Child Pair is NOT Parent Pair
# =========================================================================
def test_8_child_pair_is_not_parent_pair(db_session: Session):
    root = create_user_helper(db_session, "t8_root@mlm.local", "T8 Root")
    # Child A is on Root's LEFT
    child_a = create_user_helper(db_session, "t8_a@mlm.local", "T8 Child A", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    # A sponsors A1 and A2 under A
    a1 = create_user_helper(db_session, "t8_a1@mlm.local", "T8 A1", sponsor_id=child_a.id, binary_parent_id=child_a.id, binary_position="LEFT")
    a2 = create_user_helper(db_session, "t8_a2@mlm.local", "T8 A2", sponsor_id=child_a.id, binary_parent_id=child_a.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    # Root has nothing on RIGHT leg
    process_package_purchase(db_session, a1.id, pkg.id, slot_id="SLOT-T8")
    process_package_purchase(db_session, a2.id, pkg.id, slot_id="SLOT-T8")

    # A paired
    a_pair = db_session.query(Commission).filter(
        Commission.beneficiary_id == child_a.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert a_pair is not None

    # Root MUST NOT have a PAIR_BONUS
    root_pair = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert root_pair is None

    # Root volume: 60,000 on LEFT, 0 on RIGHT
    root_vol = get_or_create_binary_volume(db_session, root.id)
    assert root_vol.accumulated_left_bv == 60000.0
    assert root_vol.accumulated_right_bv == 0.0


# =========================================================================
# TEST 9: Both Parent and Child Can Pair in Same Slot
# =========================================================================
def test_9_both_parent_and_child_pair_in_same_slot(db_session: Session):
    root = create_user_helper(db_session, "t9_root@mlm.local", "T9 Root")
    # Child A is on Root's LEFT
    child_a = create_user_helper(db_session, "t9_a@mlm.local", "T9 Child A", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    # Child B is on Root's RIGHT
    child_b = create_user_helper(db_session, "t9_b@mlm.local", "T9 Child B", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    # A has A1 (L) and A2 (R)
    a1 = create_user_helper(db_session, "t9_a1@mlm.local", "T9 A1", sponsor_id=child_a.id, binary_parent_id=child_a.id, binary_position="LEFT")
    a2 = create_user_helper(db_session, "t9_a2@mlm.local", "T9 A2", sponsor_id=child_a.id, binary_parent_id=child_a.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    # Purchases in same slot
    process_package_purchase(db_session, a1.id, pkg.id, slot_id="SLOT-T9")
    process_package_purchase(db_session, a2.id, pkg.id, slot_id="SLOT-T9")
    process_package_purchase(db_session, child_b.id, pkg.id, slot_id="SLOT-T9")

    # A gets ₹10,000 Pair Bonus
    a_pair = db_session.query(Commission).filter(Commission.beneficiary_id == child_a.id, Commission.commission_type == 'PAIR_BONUS').first()
    assert a_pair is not None and a_pair.amount == 10000.0

    # Root gets ₹10,000 Pair Bonus (from Left 60k / Right 30k -> 30k matched)
    root_pair = db_session.query(Commission).filter(Commission.beneficiary_id == root.id, Commission.commission_type == 'PAIR_BONUS').first()
    assert root_pair is not None and root_pair.amount == 10000.0

    # Root also gets ₹1,000 Matching Commission for A's pair
    root_matching = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])
    ).first()
    assert root_matching is not None and root_matching.amount == 1000.0


# =========================================================================
# TEST 10: Multi-Level Sponsoring Lineage
# =========================================================================
def test_10_multi_level_sponsoring_lineage(db_session: Session):
    root = create_user_helper(db_session, "t10_root@mlm.local", "T10 Root")
    # Root sponsors A; A sponsors B; B sponsors B1 and B2
    user_a = create_user_helper(db_session, "t10_a@mlm.local", "T10 A", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    user_b = create_user_helper(db_session, "t10_b@mlm.local", "T10 B", sponsor_id=user_a.id, binary_parent_id=user_a.id, binary_position="LEFT")
    b1 = create_user_helper(db_session, "t10_b1@mlm.local", "T10 B1", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="LEFT")
    b2 = create_user_helper(db_session, "t10_b2@mlm.local", "T10 B2", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    process_package_purchase(db_session, b1.id, pkg.id, slot_id="SLOT-T10")
    process_package_purchase(db_session, b2.id, pkg.id, slot_id="SLOT-T10")

    # B paired -> gets ₹10,000
    b_pair = db_session.query(Commission).filter(Commission.beneficiary_id == user_b.id, Commission.commission_type == 'PAIR_BONUS').first()
    assert b_pair is not None and b_pair.amount == 10000.0

    # A is direct sponsor of B -> A gets ₹1,000 Matching Commission
    a_match = db_session.query(Commission).filter(Commission.beneficiary_id == user_a.id, Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])).first()
    assert a_match is not None and a_match.amount == 1000.0

    # Root is NOT direct sponsor of B -> Root gets NO Matching Commission for B's pair
    root_match_for_b = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.source_user_id == user_b.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])
    ).first()
    assert root_match_for_b is None


# =========================================================================
# TEST 11: Commission Never Becomes BV
# =========================================================================
def test_11_commission_never_becomes_bv(db_session: Session):
    root = create_user_helper(db_session, "t11_root@mlm.local", "T11 Root")
    child = create_user_helper(db_session, "t11_child@mlm.local", "T11 Child", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    pkg = get_default_package(db_session)

    process_package_purchase(db_session, child.id, pkg.id, slot_id="SLOT-T11")

    # Root earned ₹3,000 direct commission
    root_wallet = get_or_create_wallet(db_session, root.id)
    assert root_wallet.balance == 3000.0

    # Root's personal BV must remain 0 (unless Root bought a package)
    root_vol = get_or_create_binary_volume(db_session, root.id)
    assert root_vol.personal_bv == 0.0

    # Commission tables do not create VolumeLedger entries
    vl_entries = db_session.query(VolumeLedger).filter(VolumeLedger.source_reference.like("COMM-%")).all()
    assert len(vl_entries) == 0


# =========================================================================
# TEST 12: Placement Anywhere, Sponsor Gets Direct & Matching Commission
# =========================================================================
def test_12_placement_anywhere_sponsor_gets_commission(db_session: Session):
    root = create_user_helper(db_session, "t12_root@mlm.local", "T12 Root")
    # A is placed LEFT of root
    a = create_user_helper(db_session, "t12_a@mlm.local", "T12 A", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    # B is placed RIGHT of root
    b = create_user_helper(db_session, "t12_b@mlm.local", "T12 B", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    # Spillover: Root sponsors X, but places X under B on RIGHT
    x = create_user_helper(db_session, "t12_x@mlm.local", "T12 X", sponsor_id=root.id, binary_parent_id=b.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    process_package_purchase(db_session, x.id, pkg.id, slot_id="SLOT-T12")

    # Root gets the 10% direct commission even though X is placed deep under B
    direct_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.source_user_id == x.id,
        Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])
    ).first()
    assert direct_comm is not None
    assert direct_comm.amount == 3000.0

    # B gets NO direct commission, but gets BV on B's RIGHT leg
    b_comm = db_session.query(Commission).filter(Commission.beneficiary_id == b.id).first()
    assert b_comm is None
    b_vol = get_or_create_binary_volume(db_session, b.id)
    assert b_vol.accumulated_right_bv == 30000.0


# =========================================================================
# TEST 13: Volume Propagation from Root Perspective
# =========================================================================
def test_13_volume_propagation_root_perspective(db_session: Session):
    root = create_user_helper(db_session, "t13_root@mlm.local", "T13 Root")
    # Left Branch
    l1 = create_user_helper(db_session, "t13_l1@mlm.local", "T13 L1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    # Right child of L1
    l1_r = create_user_helper(db_session, "t13_l1_r@mlm.local", "T13 L1 R", sponsor_id=l1.id, binary_parent_id=l1.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    process_package_purchase(db_session, l1_r.id, pkg.id, slot_id="SLOT-T13")

    # L1 sees 30k on RIGHT
    l1_vol = get_or_create_binary_volume(db_session, l1.id)
    assert l1_vol.accumulated_right_bv == 30000.0
    assert l1_vol.accumulated_left_bv == 0.0

    # Root sees 30k on LEFT (because L1 is Root's LEFT child)
    root_vol = get_or_create_binary_volume(db_session, root.id)
    assert root_vol.accumulated_left_bv == 30000.0
    assert root_vol.accumulated_right_bv == 0.0


# =========================================================================
# TEST 14: Side-Specific Carry Forward
# =========================================================================
def test_14_side_specific_carry_forward(db_session: Session):
    root = create_user_helper(db_session, "t14_root@mlm.local", "T14 Root")
    l1 = create_user_helper(db_session, "t14_l1@mlm.local", "T14 L1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    l2 = create_user_helper(db_session, "t14_l2@mlm.local", "T14 L2", sponsor_id=root.id, binary_parent_id=l1.id, binary_position="LEFT")
    r1 = create_user_helper(db_session, "t14_r1@mlm.local", "T14 R1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    # 2 Left purchases (60k) + 1 Right purchase (30k)
    process_package_purchase(db_session, l1.id, pkg.id, slot_id="SLOT-T14")
    process_package_purchase(db_session, l2.id, pkg.id, slot_id="SLOT-T14")
    process_package_purchase(db_session, r1.id, pkg.id, slot_id="SLOT-T14")

    # Matched 30k L / 30k R -> 1 Pair Bonus (10k)
    # Ending Carry: 30k L / 0k R
    summary = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-T14")
    assert summary['pair_completed'] is True
    assert summary['pair_bonus_earned'] == 10000.0
    assert summary['ending_carry_left'] == 30000.0
    assert summary['ending_carry_right'] == 0.0


# =========================================================================
# TEST 15: Cross-Slot Permanent Network
# =========================================================================
def test_15_cross_slot_permanent_network(db_session: Session):
    root = create_user_helper(db_session, "t15_root@mlm.local", "T15 Root")
    l1 = create_user_helper(db_session, "t15_l1@mlm.local", "T15 L1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    r1 = create_user_helper(db_session, "t15_r1@mlm.local", "T15 R1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    pkg = get_default_package(db_session)

    # Slot 1: L1 purchases (30k L for root)
    process_package_purchase(db_session, l1.id, pkg.id, slot_id="SLOT-T15-1")
    s1_sum = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-T15-1")
    assert s1_sum['ending_carry_left'] == 30000.0
    assert s1_sum['ending_carry_right'] == 0.0

    # Slot 2: R1 purchases (30k R for root)
    process_package_purchase(db_session, r1.id, pkg.id, slot_id="SLOT-T15-2")
    s2_sum = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-T15-2")
    # Combined with 30k carried from slot 1, root completes pair in Slot 2!
    assert s2_sum['pair_completed'] is True
    assert s2_sum['pair_bonus_earned'] == 10000.0


# =========================================================================
# FINAL ACCEPTANCE SCENARIO: Complete Multi-Level 4-Tier Simulation
# =========================================================================
def test_final_acceptance_multi_tier_scenario(db_session: Session):
    """
    Simulates complete hierarchical tree:
    Root -> sponsors A (Left), B (Right)
    A -> sponsors A1 (Left), A2 (Right)
    B -> sponsors B1 (Left)
    All purchase ₹35,000 Package (30,000 BV).
    Verify all 4 tiers:
    1. Direct Commissions (10% to respective sponsors)
    2. Pair Bonuses (₹10,000 each for qualified nodes)
    3. Matching Commissions (10% = ₹1,000 to sponsors of pairing nodes)
    4. Carry Forward BV balances & VolumeLedger lineage
    """
    root = create_user_helper(db_session, "fa_root@mlm.local", "FA Root")
    a = create_user_helper(db_session, "fa_a@mlm.local", "FA A", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    b = create_user_helper(db_session, "fa_b@mlm.local", "FA B", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")
    a1 = create_user_helper(db_session, "fa_a1@mlm.local", "FA A1", sponsor_id=a.id, binary_parent_id=a.id, binary_position="LEFT")
    a2 = create_user_helper(db_session, "fa_a2@mlm.local", "FA A2", sponsor_id=a.id, binary_parent_id=a.id, binary_position="RIGHT")
    b1 = create_user_helper(db_session, "fa_b1@mlm.local", "FA B1", sponsor_id=b.id, binary_parent_id=b.id, binary_position="LEFT")
    pkg = get_default_package(db_session)

    # 1. Purchases
    process_package_purchase(db_session, a.id, pkg.id, slot_id="SLOT-FA-1")
    process_package_purchase(db_session, b.id, pkg.id, slot_id="SLOT-FA-1")
    process_package_purchase(db_session, a1.id, pkg.id, slot_id="SLOT-FA-1")
    process_package_purchase(db_session, a2.id, pkg.id, slot_id="SLOT-FA-1")
    process_package_purchase(db_session, b1.id, pkg.id, slot_id="SLOT-FA-1")

    # 2. Check A:
    # A received direct commission on A1 (3,000) + A2 (3,000) = 6,000
    # A received Pair Bonus (10,000) from A1 & A2
    # Total A wallet = 16,000
    w_a = get_or_create_wallet(db_session, a.id)
    assert w_a.balance == 16000.0

    # 3. Check B:
    # B received direct commission on B1 (3,000)
    # B has 30k on LEFT, 0 on RIGHT -> No Pair Bonus
    # Total B wallet = 3,000
    w_b = get_or_create_wallet(db_session, b.id)
    assert w_b.balance == 3000.0

    # 4. Check Root:
    # Direct commission on A (3,000) + on B (3,000) = 6,000
    # Root Pair Bonus: Left has A (30k) + A1 (30k) + A2 (30k) = 90k BV.
    # Right has B (30k) + B1 (30k) = 60k BV.
    # Root matches 30k/30k in Slot 1 -> ₹10,000 Pair Bonus.
    # Root gets Matching Commission on A's pair (10% of A's 10,000 = 1,000).
    # Total Root wallet = 6,000 (direct) + 10,000 (pair) + 1,000 (matching) = 17,000.
    w_root = get_or_create_wallet(db_session, root.id)
    assert w_root.balance == 17000.0

    # Check Root carry forward: 90k L - 30k matched = 60k L; 60k R - 30k matched = 30k R.
    root_summary = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-FA-1")
    assert root_summary['ending_carry_left'] == 60000.0
    assert root_summary['ending_carry_right'] == 30000.0
