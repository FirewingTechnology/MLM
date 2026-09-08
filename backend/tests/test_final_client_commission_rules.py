import pytest
import os
import re
from sqlalchemy.orm import Session

from app.config import settings
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
from app.services.earning_cap_service import apply_commission_with_cap, get_or_create_active_cycle
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
            pair_bonus_amount=15000.0,
            is_active=True
        )
        db.add(pkg)
        db.commit()
        db.refresh(pkg)
    return pkg


# =========================================================================
# TEST 1: A sponsors B. B purchases ₹35,000 / BV ₹30,000.
# Expected: A = ₹3,000 Direct Commission. No upline commission.
# =========================================================================
def test_1_a_sponsors_b_direct_commission_only(db_session: Session):
    # Grandparent / upline of A
    upline_root = create_user_helper(db_session, "t1_upline@mlm.local", "T1 Upline Root")
    # A sponsored by upline_root
    user_a = create_user_helper(db_session, "t1_a@mlm.local", "T1 User A", sponsor_id=upline_root.id, binary_parent_id=upline_root.id, binary_position="LEFT")
    # B sponsored by A
    user_b = create_user_helper(db_session, "t1_b@mlm.local", "T1 User B", sponsor_id=user_a.id, binary_parent_id=user_a.id, binary_position="LEFT")
    pkg = get_default_package(db_session)

    purchase, events = process_package_purchase(db_session, user_b.id, pkg.id, slot_id="SLOT-T1")

    # A gets exactly ₹3,000 Direct Commission (10% of 30,000 BV)
    a_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == user_a.id,
        Commission.purchase_id == purchase.id
    ).first()
    assert a_comm is not None
    assert a_comm.amount == 3000.0
    assert a_comm.commission_type in ['DIRECT_REFERRAL', 'DIRECT_COMMISSION']

    # Check A's wallet
    a_wallet = get_or_create_wallet(db_session, user_a.id)
    assert a_wallet.balance == 3000.0

    # Upline of A receives NOTHING from B's purchase
    upline_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == upline_root.id,
        Commission.purchase_id == purchase.id
    ).all()
    assert len(upline_comm) == 0

    upline_wallet = get_or_create_wallet(db_session, upline_root.id)
    assert upline_wallet.balance == 0.0


# =========================================================================
# TEST 2: B sponsors C. C purchases ₹35,000 / BV ₹30,000.
# Expected: B = ₹3,000 Direct Commission. A = ₹0.
# =========================================================================
def test_2_b_sponsors_c_direct_commission_to_b_only_a_gets_zero(db_session: Session):
    user_a = create_user_helper(db_session, "t2_a@mlm.local", "T2 User A")
    user_b = create_user_helper(db_session, "t2_b@mlm.local", "T2 User B", sponsor_id=user_a.id, binary_parent_id=user_a.id, binary_position="LEFT")
    user_c = create_user_helper(db_session, "t2_c@mlm.local", "T2 User C", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="LEFT")
    pkg = get_default_package(db_session)

    # Initial purchase by B so B is active
    process_package_purchase(db_session, user_b.id, pkg.id, slot_id="SLOT-T2-1")

    # Clear/record A's balance before C's purchase
    a_wallet_before = get_or_create_wallet(db_session, user_a.id).balance

    # C purchases
    purchase_c, _ = process_package_purchase(db_session, user_c.id, pkg.id, slot_id="SLOT-T2-2")

    # B gets ₹3,000 Direct Commission
    b_comm_c = db_session.query(Commission).filter(
        Commission.beneficiary_id == user_b.id,
        Commission.purchase_id == purchase_c.id
    ).first()
    assert b_comm_c is not None
    assert b_comm_c.amount == 3000.0

    # A gets ₹0 from C's purchase
    a_comm_c = db_session.query(Commission).filter(
        Commission.beneficiary_id == user_a.id,
        Commission.purchase_id == purchase_c.id
    ).all()
    assert len(a_comm_c) == 0

    # A's wallet balance did not increase from C's purchase
    a_wallet_after = get_or_create_wallet(db_session, user_a.id).balance
    assert a_wallet_after == a_wallet_before


# =========================================================================
# TEST 3: B completes a valid Matching pair.
# Expected: B = Pair Bonus (₹15,000). A = ₹0. No MATCHING_COMMISSION transaction.
# =========================================================================
def test_3_b_completes_pair_b_gets_pair_bonus_a_gets_zero_no_matching(db_session: Session):
    user_a = create_user_helper(db_session, "t3_a@mlm.local", "T3 User A")
    # B sponsored by A
    user_b = create_user_helper(db_session, "t3_b@mlm.local", "T3 User B", sponsor_id=user_a.id, binary_parent_id=user_a.id, binary_position="LEFT")
    pkg = get_default_package(db_session)
    process_package_purchase(db_session, user_b.id, pkg.id, slot_id="SLOT-T3-0")

    # B sponsors B1 (LEFT) and B2 (RIGHT) -> B is Matching qualified
    b1 = create_user_helper(db_session, "t3_b1@mlm.local", "T3 B1", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="LEFT")
    b2 = create_user_helper(db_session, "t3_b2@mlm.local", "T3 B2", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="RIGHT")

    a_wallet_before = get_or_create_wallet(db_session, user_a.id).balance

    process_package_purchase(db_session, b1.id, pkg.id, slot_id="SLOT-T3-1")
    process_package_purchase(db_session, b2.id, pkg.id, slot_id="SLOT-T3-1")

    # B completed a pair -> B gets Pair Bonus of ₹15,000
    b_pair_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == user_b.id,
        Commission.commission_type == 'PAIR_BONUS'
    ).first()
    assert b_pair_comm is not None
    assert b_pair_comm.amount == 15000.0

    # A gets ₹0 from B's pair:
    # 1. No Commission for A on B's pair
    a_match_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == user_a.id,
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING', 'CARRY_COMMISSION'])
    ).all()
    assert len(a_match_comm) == 0

    # 2. No MATCHING_COMMISSION transactions anywhere in the DB for this slot
    all_matching = db_session.query(Commission).filter(
        Commission.commission_type.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING', 'CARRY_COMMISSION']),
        Commission.slot_id == "SLOT-T3-1"
    ).all()
    assert len(all_matching) == 0


# =========================================================================
# TEST 4: Verify database/wallet ledger after pair.
# There must be exactly one Pair Bonus earning for B.
# There must be ZERO new upline/matching commission.
# =========================================================================
def test_4_wallet_ledger_audit_after_pair(db_session: Session):
    user_a = create_user_helper(db_session, "t4_a@mlm.local", "T4 User A")
    user_b = create_user_helper(db_session, "t4_b@mlm.local", "T4 User B", sponsor_id=user_a.id, binary_parent_id=user_a.id, binary_position="LEFT")
    pkg = get_default_package(db_session)
    process_package_purchase(db_session, user_b.id, pkg.id, slot_id="SLOT-T4-0")

    b1 = create_user_helper(db_session, "t4_b1@mlm.local", "T4 B1", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="LEFT")
    b2 = create_user_helper(db_session, "t4_b2@mlm.local", "T4 B2", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="RIGHT")

    process_package_purchase(db_session, b1.id, pkg.id, slot_id="SLOT-T4-1")
    process_package_purchase(db_session, b2.id, pkg.id, slot_id="SLOT-T4-1")

    # Exactly ONE Pair Bonus earning for B
    b_pair_txns = db_session.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_b.id,
        WalletTransaction.category == 'PAIR_BONUS',
        WalletTransaction.slot_id == "SLOT-T4-1"
    ).all()
    assert len(b_pair_txns) == 1
    assert b_pair_txns[0].amount == 15000.0

    # ZERO upline/matching commission transactions in WalletTransaction table
    matching_txns = db_session.query(WalletTransaction).filter(
        WalletTransaction.category.in_(['MATCHING_COMMISSION', 'BINARY_MATCHING', 'CARRY_COMMISSION', 'UPLINE_COMMISSION']),
        WalletTransaction.slot_id == "SLOT-T4-1"
    ).all()
    assert len(matching_txns) == 0


# =========================================================================
# TEST 5: Verify placement parent receives nothing merely because a user is placed underneath them.
# =========================================================================
def test_5_placement_parent_receives_nothing_merely_for_placement(db_session: Session):
    sponsor = create_user_helper(db_session, "t5_sponsor@mlm.local", "T5 Sponsor")
    placement_parent = create_user_helper(db_session, "t5_parent@mlm.local", "T5 Placement Parent")
    
    # New user is sponsored by sponsor, but placed under placement_parent
    placed_user = create_user_helper(
        db_session,
        "t5_placed@mlm.local",
        "T5 Placed User",
        sponsor_id=sponsor.id,
        binary_parent_id=placement_parent.id,
        binary_position="LEFT"
    )
    pkg = get_default_package(db_session)

    purchase, _ = process_package_purchase(db_session, placed_user.id, pkg.id, slot_id="SLOT-T5")

    # Placement parent gets NO direct commission and NO wallet credit
    parent_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == placement_parent.id,
        Commission.purchase_id == purchase.id
    ).all()
    assert len(parent_comm) == 0

    parent_wallet = get_or_create_wallet(db_session, placement_parent.id)
    assert parent_wallet.balance == 0.0

    # Sponsor got the direct commission
    sponsor_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == sponsor.id,
        Commission.purchase_id == purchase.id
    ).first()
    assert sponsor_comm is not None
    assert sponsor_comm.amount == 3000.0


# =========================================================================
# TEST 6: Verify Direct Commission remains exactly 10% of purchase BV.
# =========================================================================
def test_6_direct_commission_is_exactly_10_percent_of_bv(db_session: Session):
    sponsor = create_user_helper(db_session, "t6_sponsor@mlm.local", "T6 Sponsor")
    member = create_user_helper(db_session, "t6_member@mlm.local", "T6 Member", sponsor_id=sponsor.id)
    pkg = get_default_package(db_session)

    purchase, _ = process_package_purchase(db_session, member.id, pkg.id, slot_id="SLOT-T6")

    comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == sponsor.id,
        Commission.purchase_id == purchase.id
    ).first()
    assert comm is not None

    expected_rate = 0.10
    expected_amount = pkg.bv * expected_rate
    assert comm.bv_basis == pkg.bv
    assert comm.percentage == 10.0
    assert comm.amount == expected_amount == 3000.0


# =========================================================================
# TEST 7: Verify Pair Bonus respects existing pair volume, carry-forward
# and one-pair-per-slot rules.
# =========================================================================
def test_7_pair_bonus_respects_volume_carry_and_slot_limits(db_session: Session):
    user_b = create_user_helper(db_session, "t7_b@mlm.local", "T7 B")
    pkg = get_default_package(db_session)
    process_package_purchase(db_session, user_b.id, pkg.id, slot_id="SLOT-T7-0")

    # B sponsors B1 (LEFT) and B2 (RIGHT) -> B is Matching qualified
    b1 = create_user_helper(db_session, "t7_b1@mlm.local", "T7 B1", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="LEFT")
    b2 = create_user_helper(db_session, "t7_b2@mlm.local", "T7 B2", sponsor_id=user_b.id, binary_parent_id=user_b.id, binary_position="RIGHT")

    # Add a second member on LEFT: B11 under B1
    b11 = create_user_helper(db_session, "t7_b11@mlm.local", "T7 B11", sponsor_id=user_b.id, binary_parent_id=b1.id, binary_position="LEFT")

    # In SLOT-T7-1:
    # Left receives 2 x 30,000 = 60,000 BV (b1 and b11)
    # Right receives 1 x 30,000 = 30,000 BV (b2)
    process_package_purchase(db_session, b1.id, pkg.id, slot_id="SLOT-T7-1")
    process_package_purchase(db_session, b11.id, pkg.id, slot_id="SLOT-T7-1")
    process_package_purchase(db_session, b2.id, pkg.id, slot_id="SLOT-T7-1")

    # Pair completed in SLOT-T7-1
    slot_1_comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == user_b.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == "SLOT-T7-1"
    ).all()
    assert len(slot_1_comms) == 1
    assert slot_1_comms[0].amount == 15000.0

    # Verify Carry Forward:
    # Left started with 60k, consumed 30k -> Ending carry left = 30k
    # Right started with 30k, consumed 30k -> Ending carry right = 0
    vol_summary = pair_service.get_user_pair_summary(db_session, user_b.id, "SLOT-T7-1")
    assert vol_summary['consumed_left_bv'] == 30000.0
    assert vol_summary['consumed_right_bv'] == 30000.0
    assert vol_summary['ending_carry_left'] == 30000.0
    assert vol_summary['ending_carry_right'] == 0.0

    # Now in NEXT SLOT (SLOT-T7-2):
    # Add a member on Right: B22 under B2 (30k BV)
    b22 = create_user_helper(db_session, "t7_b22@mlm.local", "T7 B22", sponsor_id=user_b.id, binary_parent_id=b2.id, binary_position="RIGHT")
    process_package_purchase(db_session, b22.id, pkg.id, slot_id="SLOT-T7-2")

    # B forms a new pair using the 30k carry-forward on Left + 30k new BV on Right
    slot_2_comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == user_b.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == "SLOT-T7-2"
    ).all()
    assert len(slot_2_comms) == 1
    assert slot_2_comms[0].amount == 15000.0

    vol_summary_2 = pair_service.get_user_pair_summary(db_session, user_b.id, "SLOT-T7-2")
    assert vol_summary_2['ending_carry_left'] == 0.0
    assert vol_summary_2['ending_carry_right'] == 0.0

    # Verify Max 1 Pair Per Slot:
    # If another purchase occurs in SLOT-T7-2, it must NOT pay a second pair bonus in the same slot
    b23 = create_user_helper(db_session, "t7_b23@mlm.local", "T7 B23", sponsor_id=user_b.id, binary_parent_id=b22.id, binary_position="RIGHT")
    process_package_purchase(db_session, b23.id, pkg.id, slot_id="SLOT-T7-2")

    slot_2_comms_after = db_session.query(Commission).filter(
        Commission.beneficiary_id == user_b.id,
        Commission.commission_type == 'PAIR_BONUS',
        Commission.slot_id == "SLOT-T7-2"
    ).all()
    assert len(slot_2_comms_after) == 1  # Still exactly 1 pair paid in slot 2


# =========================================================================
# TEST 8: Verify Direct Commission + Pair Bonus both respect ₹3,00,000 earning cap.
# =========================================================================
def test_8_direct_and_pair_bonus_respect_300k_earning_cap(db_session: Session):
    user = create_user_helper(db_session, "t8_cap@mlm.local", "T8 Capped User")
    cycle = get_or_create_active_cycle(db_session, user.id, for_update=True)
    assert cycle.earning_cap == 300000.0

    # Simulate existing earnings of ₹2,95,000 (direct ₹1,45,000 + pairing ₹1,50,000)
    cycle.direct_income = 145000.0
    cycle.pairing_income = 150000.0
    cycle.total_eligible_income = 295000.0
    db_session.flush()

    # 1. Apply Direct Commission of ₹3,000 -> Should be allowed in full (295k + 3k = 298k <= 300k)
    comm_1, _, summary_1 = apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type='DIRECT_REFERRAL',
        requested_amount=3000.0,
        slot_id="SLOT-T8"
    )
    assert summary_1['allowed_amount'] == 3000.0
    assert summary_1['blocked_amount'] == 0.0
    assert summary_1['is_capped'] is False
    assert cycle.total_eligible_income == 298000.0

    # 2. Apply Pair Bonus of ₹15,000 -> Capacity remaining is ₹2,000
    # Expected: Allowed = ₹2,000, Blocked = ₹13,000, Cycle becomes RETOPUP_REQUIRED
    comm_2, _, summary_2 = apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type='PAIR_BONUS',
        requested_amount=15000.0,
        slot_id="SLOT-T8"
    )
    assert summary_2['allowed_amount'] == 2000.0
    assert summary_2['blocked_amount'] == 13000.0
    assert summary_2['is_capped'] is True
    assert cycle.total_eligible_income == 300000.0
    assert cycle.status == 'RETOPUP_REQUIRED'

    # 3. Any subsequent commission is 100% blocked
    comm_3, _, summary_3 = apply_commission_with_cap(
        db=db_session,
        user_id=user.id,
        commission_type='DIRECT_REFERRAL',
        requested_amount=3000.0,
        slot_id="SLOT-T8"
    )
    assert summary_3['allowed_amount'] == 0.0
    assert summary_3['blocked_amount'] == 3000.0
    assert summary_3['is_capped'] is True


# =========================================================================
# TEST 9: Search all backend paths and confirm no active path can create:
# MATCHING_COMMISSION, UPLINE_COMMISSION, SINGLE_COMMISSION
# =========================================================================
def test_9_static_audit_no_active_creation_of_matching_or_upline_commission():
    backend_services_dir = os.path.join(os.path.dirname(__file__), "..", "app", "services")
    
    # Patterns that indicate active creation of matching/upline commission:
    forbidden_creation_patterns = [
        re.compile(r"commission_type\s*=\s*['\"]MATCHING_COMMISSION['\"]"),
        re.compile(r"commission_type\s*=\s*['\"]UPLINE_COMMISSION['\"]"),
        re.compile(r"commission_type\s*=\s*['\"]SINGLE_COMMISSION['\"]"),
        re.compile(r"category\s*=\s*['\"]MATCHING_COMMISSION['\"]"),
        re.compile(r"category\s*=\s*['\"]UPLINE_COMMISSION['\"]"),
        re.compile(r"category\s*=\s*['\"]SINGLE_COMMISSION['\"]"),
    ]

    for root, _, files in os.walk(backend_services_dir):
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                with open(file_path, "r", encoding="utf-8") as py_file:
                    content = py_file.read()
                    for pattern in forbidden_creation_patterns:
                        match = pattern.search(content)
                        assert match is None, f"Forbidden commission creation pattern {pattern.pattern} found in {file_path}"
