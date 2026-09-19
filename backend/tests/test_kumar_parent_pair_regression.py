import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.wallet import Wallet, WalletTransaction
from app.models.commission import Commission
from app.models.volume import BinaryVolume
from app.models.period_volume import BinaryPeriodVolume
from app.models.pair_event import PairEvent
from app.services.commission_service import process_package_purchase
from app.services.pair_service import pair_service
from app.services.wallet_service import get_or_create_wallet
from app.services.mlm_service import get_or_create_binary_volume
from app.security import hash_password


def create_test_user(db: Session, email: str, full_name: str, referral_code: str, sponsor_id=None, binary_parent_id=None, binary_position=None, is_active=True):
    user = User(
        email=email,
        mobile=f"+91{abs(hash(email)) % 10000000000:010d}",
        full_name=full_name,
        user_code=referral_code,
        referral_code=referral_code,
        password_hash=hash_password("Demo@123"),
        sponsor_id=sponsor_id,
        binary_parent_id=binary_parent_id,
        binary_position=binary_position,
        role="USER",
        is_active=is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    get_or_create_wallet(db, user.id)
    get_or_create_binary_volume(db, user.id)
    return user


def get_or_create_package(db: Session):
    pkg = db.query(Package).filter(Package.is_active == True).first()
    if not pkg:
        pkg = Package(
            name="Premium Sub Franchise",
            price=35400.0,
            product_value=30000.0,
            gst_amount=5400.0,
            bv=30000.0,
            is_active=True
        )
        db.add(pkg)
        db.commit()
        db.refresh(pkg)
    return pkg


# =========================================================================
# TEST 1: Unqualified Parent with 30k Left & 30k Right Gets ₹0 Pair Bonus
# =========================================================================
def test_1_unqualified_parent_left_right_volume_pays_zero_pair_bonus(db_session: Session):
    """
    Root places B (LEFT) and C (RIGHT) under Parent A.
    A did NOT personally sponsor B or C.
    B & C buy 30k BV.
    Expected: A has 30k Left and 30k Right, but A Pair Bonus = ₹0.
    """
    root = create_test_user(db_session, "t1_root@demo.com", "Root", "ROOT001")
    parent_a = create_test_user(db_session, "t1_a@demo.com", "Parent A", "PA001", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    
    # Root sponsors B and C, but places them under Parent A
    b = create_test_user(db_session, "t1_b@demo.com", "Child B", "B001", sponsor_id=root.id, binary_parent_id=parent_a.id, binary_position="LEFT", is_active=False)
    c = create_test_user(db_session, "t1_c@demo.com", "Child C", "C001", sponsor_id=root.id, binary_parent_id=parent_a.id, binary_position="RIGHT", is_active=False)
    pkg = get_or_create_package(db_session)

    process_package_purchase(db_session, b.id, pkg.id, slot_id="SLOT-T1")
    process_package_purchase(db_session, c.id, pkg.id, slot_id="SLOT-T1")

    # Verify Parent A volume vs commissions
    summary_a = pair_service.get_user_pair_summary(db_session, parent_a.id, slot_id="SLOT-T1")
    assert summary_a['effective_left_bv'] == 30000.0
    assert summary_a['effective_right_bv'] == 30000.0
    assert summary_a['pair_completed'] is False
    assert summary_a['pair_bonus_earned'] == 0.0

    wallet_a = get_or_create_wallet(db_session, parent_a.id)
    assert wallet_a.balance == 0.0
    assert wallet_a.total_earned == 0.0

    pair_comms_a = db_session.query(Commission).filter(
        Commission.beneficiary_id == parent_a.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).all()
    assert len(pair_comms_a) == 0


# =========================================================================
# TEST 2: Child Actually Pairs -> Child gets ₹15,000, Upline gets Matching Commission (₹1,500), NOT ₹15,000
# =========================================================================
def test_2_child_pairs_pays_child_pair_bonus_and_upline_matching_only(db_session: Session):
    root = create_test_user(db_session, "t2_root@demo.com", "Root", "ROOT002")
    child_b = create_test_user(db_session, "t2_b@demo.com", "Child B", "B002", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    
    # B sponsors C (LEFT) and D (RIGHT)
    c = create_test_user(db_session, "t2_c@demo.com", "Leaf C", "C002", sponsor_id=child_b.id, binary_parent_id=child_b.id, binary_position="LEFT", is_active=False)
    d = create_test_user(db_session, "t2_d@demo.com", "Leaf D", "D002", sponsor_id=child_b.id, binary_parent_id=child_b.id, binary_position="RIGHT", is_active=False)
    pkg = get_or_create_package(db_session)

    process_package_purchase(db_session, c.id, pkg.id, slot_id="SLOT-T2")
    process_package_purchase(db_session, d.id, pkg.id, slot_id="SLOT-T2")

    # 1. Child B earned ₹15,000 Pair Bonus
    b_pair_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == child_b.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert b_pair_comm is not None
    assert b_pair_comm.amount == 15000.0

    # 2. Upline Root earned ₹0 Matching Commission (no upline commission per final rule)
    root_matching = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])
    ).all()
    assert len(root_matching) == 0

    root_pair_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert root_pair_comm is None


# =========================================================================
# TEST 3: Child Registration Alone Pays Nothing
# =========================================================================
def test_3_child_registration_alone_pays_nothing(db_session: Session):
    root = create_test_user(db_session, "t3_root@demo.com", "Root", "ROOT003")
    child = create_test_user(db_session, "t3_child@demo.com", "Child", "CHILD003", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT", is_active=False)

    root_wallet = get_or_create_wallet(db_session, root.id)
    assert root_wallet.balance == 0.0
    assert root_wallet.total_earned == 0.0
    assert db_session.query(Commission).count() == 0


# =========================================================================
# TEST 4: Direct Sponsored Package Purchase Pays ₹3,000 Direct Commission Only
# =========================================================================
def test_4_direct_sponsored_purchase_pays_direct_commission_only(db_session: Session):
    root = create_test_user(db_session, "t4_root@demo.com", "Root", "ROOT004")
    child = create_test_user(db_session, "t4_child@demo.com", "Child", "CHILD004", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT", is_active=False)
    pkg = get_or_create_package(db_session)

    process_package_purchase(db_session, child.id, pkg.id, slot_id="SLOT-T4")

    root_wallet = get_or_create_wallet(db_session, root.id)
    assert root_wallet.balance == 3000.0
    assert root_wallet.total_earned == 3000.0

    # No Pair Bonus for Root
    assert db_session.query(Commission).filter(Commission.commission_type == 'PAIR_BONUS').count() == 0


# =========================================================================
# TEST 5: One Pair Per User Per Slot Max Limit
# =========================================================================
def test_5_one_pair_per_user_per_slot_max_limit(db_session: Session):
    root = create_test_user(db_session, "t5_root@demo.com", "Root", "ROOT005")
    # Root sponsors L1, L2 on LEFT, R1, R2 on RIGHT
    l1 = create_test_user(db_session, "t5_l1@demo.com", "L1", "L005_1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT", is_active=False)
    r1 = create_test_user(db_session, "t5_r1@demo.com", "R1", "R005_1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT", is_active=False)
    l2 = create_test_user(db_session, "t5_l2@demo.com", "L2", "L005_2", sponsor_id=root.id, binary_parent_id=l1.id, binary_position="LEFT", is_active=False)
    r2 = create_test_user(db_session, "t5_r2@demo.com", "R2", "R005_2", sponsor_id=root.id, binary_parent_id=r1.id, binary_position="RIGHT", is_active=False)
    pkg = get_or_create_package(db_session)

    process_package_purchase(db_session, l1.id, pkg.id, slot_id="SLOT-T5")
    process_package_purchase(db_session, r1.id, pkg.id, slot_id="SLOT-T5")
    process_package_purchase(db_session, l2.id, pkg.id, slot_id="SLOT-T5")
    process_package_purchase(db_session, r2.id, pkg.id, slot_id="SLOT-T5")

    pair_bonuses = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == "SLOT-T5"
    ).all()
    assert len(pair_bonuses) == 1
    assert pair_bonuses[0].amount == 15000.0

    summary = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-T5")
    assert summary['ending_carry_left'] == 30000.0
    assert summary['ending_carry_right'] == 30000.0


# =========================================================================
# TEST 6: Carry Volume Only + Opposite Leg Volume in Next Slot
# =========================================================================
def test_6_carry_volume_only_and_next_slot_pair(db_session: Session):
    root = create_test_user(db_session, "t6_root@demo.com", "Root", "ROOT006")
    l1 = create_test_user(db_session, "t6_l1@demo.com", "L1", "L006_1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT", is_active=False)
    r1 = create_test_user(db_session, "t6_r1@demo.com", "R1", "R006_1", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT", is_active=False)
    pkg = get_or_create_package(db_session)

    # Slot 1: L1 purchases (30k Left only)
    process_package_purchase(db_session, l1.id, pkg.id, slot_id="SLOT-T6-1")
    summary1 = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-T6-1")
    assert summary1['effective_left_bv'] == 30000.0
    assert summary1['effective_right_bv'] == 0.0
    assert summary1['pair_completed'] is False
    assert summary1['pair_bonus_earned'] == 0.0
    assert summary1['ending_carry_left'] == 30000.0

    # Slot 2: R1 purchases (30k Right)
    process_package_purchase(db_session, r1.id, pkg.id, slot_id="SLOT-T6-2")
    summary2 = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-T6-2")
    assert summary2['pair_completed'] is True
    assert summary2['pair_bonus_earned'] == 15000.0
    assert summary2['ending_carry_left'] == 0.0
    assert summary2['ending_carry_right'] == 0.0


# =========================================================================
# TEST 7: Parent and Child Pair Limit Independence
# =========================================================================
def test_7_parent_and_child_independent_pair_limits(db_session: Session):
    root = create_test_user(db_session, "t7_root@demo.com", "Root", "ROOT007")
    b = create_test_user(db_session, "t7_b@demo.com", "Child B", "B007", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    r_root = create_test_user(db_session, "t7_r@demo.com", "Right Root", "R007", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT", is_active=False)

    # B sponsors C (LEFT) and D (RIGHT)
    c = create_test_user(db_session, "t7_c@demo.com", "C", "C007", sponsor_id=b.id, binary_parent_id=b.id, binary_position="LEFT", is_active=False)
    d = create_test_user(db_session, "t7_d@demo.com", "D", "D007", sponsor_id=b.id, binary_parent_id=b.id, binary_position="RIGHT", is_active=False)
    pkg = get_or_create_package(db_session)

    process_package_purchase(db_session, c.id, pkg.id, slot_id="SLOT-T7")
    process_package_purchase(db_session, d.id, pkg.id, slot_id="SLOT-T7")
    process_package_purchase(db_session, r_root.id, pkg.id, slot_id="SLOT-T7")

    # B completed its pair
    b_summary = pair_service.get_user_pair_summary(db_session, b.id, slot_id="SLOT-T7")
    assert b_summary['pair_completed'] is True
    assert b_summary['pair_bonus_earned'] == 15000.0

    # Root also completed its own pair (Left from B's subtree + Right from r_root)
    root_summary = pair_service.get_user_pair_summary(db_session, root.id, slot_id="SLOT-T7")
    assert root_summary['pair_completed'] is True
    assert root_summary['pair_bonus_earned'] == 15000.0


# =========================================================================
# TEST 8: Sponsor and Placement Separation
# =========================================================================
def test_8_sponsor_and_placement_separation(db_session: Session):
    root = create_test_user(db_session, "t8_root@demo.com", "Root", "ROOT008")
    kumar = create_test_user(db_session, "t8_kumar@demo.com", "Kumar", "KUMAR008", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    
    # Root sponsors B, placed under Kumar
    b = create_test_user(db_session, "t8_b@demo.com", "B", "B008", sponsor_id=root.id, binary_parent_id=kumar.id, binary_position="LEFT", is_active=False)
    pkg = get_or_create_package(db_session)

    process_package_purchase(db_session, b.id, pkg.id, slot_id="SLOT-T8")

    # Root gets ₹3,000 direct commission + ₹2,100 Star Rank Reward
    root_wallet = get_or_create_wallet(db_session, root.id)
    assert root_wallet.balance == 5100.0

    # Kumar gets ₹0 direct commission
    kumar_wallet = get_or_create_wallet(db_session, kumar.id)
    assert kumar_wallet.balance == 0.0
    assert kumar_wallet.total_earned == 0.0


# =========================================================================
# TEST 9: Exact Screenshot Bug Reproduction Scenario
# =========================================================================
def test_9_exact_screenshot_bug_reproduction(db_session: Session):
    """
    Network:
                    Amol
                      |
                    Kumar
                   /     \
              Aditi       Praju
              LEFT        RIGHT
              30k BV      30k BV

    Aditi: sponsor=Amol, placement_parent=Kumar, 30k BV
    Praju: sponsor=Amol, placement_parent=Kumar, 30k BV

    Expected:
    Kumar Direct Commission = ₹0
    Kumar Pair Bonus = ₹0
    Kumar Matching Commission = ₹0
    Kumar Carry Commission = ₹0
    Kumar Total Wallet = ₹0

    Amol:
    Direct Commission = ₹6,000 (2 x ₹3,000)
    Star Rank Reward = ₹2,100 (2 Directs)
    Total Wallet = ₹8,100
    """
    amol = create_test_user(db_session, "t9_amol@demo.com", "Amol Sharma", "AMOL009")
    kumar = create_test_user(db_session, "t9_kumar@demo.com", "Kumar", "KUMAR009", sponsor_id=amol.id, binary_parent_id=amol.id, binary_position="LEFT")

    aditi = create_test_user(db_session, "t9_aditi@demo.com", "Aditi", "ADITI009", sponsor_id=amol.id, binary_parent_id=kumar.id, binary_position="LEFT", is_active=False)
    praju = create_test_user(db_session, "t9_praju@demo.com", "Praju", "PRAJU009", sponsor_id=amol.id, binary_parent_id=kumar.id, binary_position="RIGHT", is_active=False)
    pkg = get_or_create_package(db_session)

    # Both purchase 30k packages
    process_package_purchase(db_session, aditi.id, pkg.id, slot_id="SLOT-T9")
    process_package_purchase(db_session, praju.id, pkg.id, slot_id="SLOT-T9")

    # 1. Verify Kumar's commissions & wallet (MUST BE EXACTLY ₹0)
    kumar_wallet = get_or_create_wallet(db_session, kumar.id)
    assert kumar_wallet.balance == 0.0
    assert kumar_wallet.total_earned == 0.0

    kumar_pair_comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == kumar.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).all()
    assert len(kumar_pair_comms) == 0

    kumar_matching_comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == kumar.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])
    ).all()
    assert len(kumar_matching_comms) == 0

    kumar_direct_comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == kumar.id,
        Commission.commission_type.in_(['DIRECT_REFERRAL', 'DIRECT_COMMISSION'])
    ).all()
    assert len(kumar_direct_comms) == 0

    # 2. Verify Amol's direct commission (₹6,000) + Star Rank Reward (₹2,100) = ₹8,100
    amol_wallet = get_or_create_wallet(db_session, amol.id)
    assert amol_wallet.balance == 8100.0
    assert amol_wallet.total_earned == 8100.0


# =========================================================================
# TEST 10: Deep Network / Actual Child Pair Event
# =========================================================================
def test_10_deep_network_actual_child_pair_event(db_session: Session):
    """
    Kumar
     /   \
  Aditi Praju
   /   \
  D     E

  Aditi sponsors D (LEFT, 30k) and E (RIGHT, 30k).
  Aditi completes pair.
  Expected:
  - Aditi = ₹15,000 Pair Bonus
  - Amol (Aditi's sponsor) = ₹0 Matching Commission (no upline commission per final rule)
  - Kumar = ₹0 Pair Bonus
  """
    amol = create_test_user(db_session, "t10_amol@demo.com", "Amol", "AMOL010")
    kumar = create_test_user(db_session, "t10_kumar@demo.com", "Kumar", "KUMAR010", sponsor_id=amol.id, binary_parent_id=amol.id, binary_position="LEFT")
    aditi = create_test_user(db_session, "t10_aditi@demo.com", "Aditi", "ADITI010", sponsor_id=amol.id, binary_parent_id=kumar.id, binary_position="LEFT")
    praju = create_test_user(db_session, "t10_praju@demo.com", "Praju", "PRAJU010", sponsor_id=amol.id, binary_parent_id=kumar.id, binary_position="RIGHT")

    # Aditi sponsors D and E
    d = create_test_user(db_session, "t10_d@demo.com", "D", "D010", sponsor_id=aditi.id, binary_parent_id=aditi.id, binary_position="LEFT", is_active=False)
    e = create_test_user(db_session, "t10_e@demo.com", "E", "E010", sponsor_id=aditi.id, binary_parent_id=aditi.id, binary_position="RIGHT", is_active=False)
    pkg = get_or_create_package(db_session)

    process_package_purchase(db_session, d.id, pkg.id, slot_id="SLOT-T10")
    process_package_purchase(db_session, e.id, pkg.id, slot_id="SLOT-T10")

    # Aditi earned ₹15,000 Pair Bonus + ₹6,000 Direct (total ₹21,000)
    aditi_pair = db_session.query(Commission).filter(
        Commission.beneficiary_id == aditi.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert aditi_pair is not None
    assert aditi_pair.amount == 15000.0

    # Amol (Aditi's direct sponsor) earned ₹0 Matching Commission (no upline commission)
    amol_matching = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING'])
    ).all()
    assert len(amol_matching) == 0

    # Kumar earned ₹0 Pair Bonus
    kumar_pair = db_session.query(Commission).filter(
        Commission.beneficiary_id == kumar.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert kumar_pair is None

    # Check PairEvent table has explicit record for Aditi's pair
    pair_event = db_session.query(PairEvent).filter(
        PairEvent.pair_earner_user_id == aditi.id,
        PairEvent.slot_id == "SLOT-T10"
    ).first()
    assert pair_event is not None
    assert pair_event.pair_bonus == 15000.0
    assert pair_event.matching_commission == 0.0
