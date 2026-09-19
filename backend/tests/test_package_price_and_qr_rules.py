import os
import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.wallet import Wallet, WalletTransaction
from app.models.commission import Commission
from app.models.security_pin import SecurityPin
from app.models.pin_order import SecurityPinOrder
from app.services.commission_service import process_package_purchase
from app.services.wallet_service import get_or_create_wallet
from app.services.mlm_service import get_or_create_binary_volume
from app.services.pin_service import pin_service, PinValidationError
from app.security import hash_password, create_access_token


def make_user(db: Session, email: str, full_name: str, sponsor_id=None, binary_parent_id=None, binary_position=None):
    code = f"USR{abs(hash(email)) % 1000000:06d}"
    user = User(
        email=email,
        mobile=f"+91{abs(hash(email)) % 10000000000:010d}",
        full_name=full_name,
        user_code=code,
        referral_code=code,
        password_hash=hash_password("Pass123!"),
        sponsor_id=sponsor_id,
        binary_parent_id=binary_parent_id,
        binary_position=binary_position,
        role="USER",
        is_active=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    get_or_create_wallet(db, user.id)
    get_or_create_binary_volume(db, user.id)
    return user


# =========================================================================
# TEST 1: GET active package configuration
# Expected: price = 35400, product_value = 30000, gst_amount = 5400, bv = 30000
# =========================================================================
def test_1_get_active_package_configuration(client, db_session: Session):
    res = client.get("/api/packages")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    pkg = data[0]
    assert pkg["name"] == "Premium Sub Franchise"
    assert pkg["price"] == 35400.0
    assert pkg["product_value"] == 30000.0
    assert pkg["gst_amount"] == 5400.0
    assert pkg["bv"] == 30000.0
    assert pkg["is_active"] is True


# =========================================================================
# TEST 2: New purchase uses authoritative snapshot:
# ₹35,400 total, ₹30,000 product, ₹5,400 GST, 30,000 BV
# =========================================================================
def test_2_new_purchase_uses_authoritative_snapshot(db_session: Session):
    user = make_user(db_session, "buyer_test2@mlm.local", "Test Buyer 2")
    active_pkg = db_session.query(Package).filter(Package.is_active == True).first()

    purchase, events = process_package_purchase(db_session, user_id=user.id, package_id=active_pkg.id)

    assert purchase.amount == 35400.0
    assert purchase.product_value == 30000.0
    assert purchase.gst_amount == 5400.0
    assert purchase.bv == 30000.0
    assert purchase.status == "COMPLETED"


# =========================================================================
# TEST 3: Frontend activation-status endpoint displays authoritative ₹35,400
# =========================================================================
def test_3_activation_status_authoritative_package_amount(client, db_session: Session):
    user = make_user(db_session, "buyer_test3@mlm.local", "Test Buyer 3")
    token = create_access_token(user.id, user.role)

    res = client.get("/api/package/activation-status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["package"]["price"] == 35400.0
    assert data["package"]["product_value"] == 30000.0
    assert data["package"]["gst_amount"] == 5400.0
    assert data["package"]["bv"] == 30000.0
    assert data["upi_details"]["amount"] == 35400.0
    assert data["upi_details"]["qr_image_url"] == "/payment-qr.png"


# =========================================================================
# TEST 4: Backend rejects a manipulated purchase amount of ₹35,000
# =========================================================================
def test_4_backend_rejects_manipulated_amount_35000(client, db_session: Session):
    user = make_user(db_session, "buyer_test4@mlm.local", "Test Buyer 4")
    token = create_access_token(user.id, user.role)

    # Client passes old price ₹35,000
    res = client.post(
        "/api/purchases",
        json={"amount": 35000.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 400
    err = res.json()
    assert err["error"]["code"] == "INVALID_PACKAGE_AMOUNT"
    assert "35,400" in err["error"]["message"] or "35400" in err["error"]["message"]


# =========================================================================
# TEST 5: Backend rejects arbitrary manipulated purchase amounts (30k, 40k)
# =========================================================================
def test_5_backend_rejects_arbitrary_manipulated_amounts(client, db_session: Session):
    user = make_user(db_session, "buyer_test5@mlm.local", "Test Buyer 5")
    token = create_access_token(user.id, user.role)

    for bad_amount in [30000.0, 40000.0, 1.0, 99999.0]:
        res = client.post(
            "/api/purchases",
            json={"amount": bad_amount},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "INVALID_PACKAGE_AMOUNT"


# =========================================================================
# TEST 6: Historical ₹35,000 purchase remains ₹35,000 intact (immutability)
# =========================================================================
def test_6_historical_purchase_remains_35000(db_session: Session):
    user = make_user(db_session, "historical_user@mlm.local", "Historical User")
    pkg = db_session.query(Package).filter(Package.is_active == True).first()

    # Create historical purchase recorded before update
    hist_purchase = Purchase(
        purchase_code="PUR-HIST-001",
        user_id=user.id,
        package_id=pkg.id,
        amount=35000.0,
        product_value=30000.0,
        gst_amount=5000.0,
        bv=30000.0,
        status="COMPLETED"
    )
    db_session.add(hist_purchase)
    db_session.commit()
    db_session.refresh(hist_purchase)

    # Re-fetch from DB and verify it was not modified
    fetched = db_session.query(Purchase).filter(Purchase.purchase_code == "PUR-HIST-001").first()
    assert fetched.amount == 35000.0
    assert fetched.product_value == 30000.0
    assert fetched.gst_amount == 5000.0
    assert fetched.bv == 30000.0


# =========================================================================
# TEST 7: Historical purchase BV remains its original BV
# =========================================================================
def test_7_historical_purchase_bv_remains_original(db_session: Session):
    user = make_user(db_session, "hist_bv_user@mlm.local", "Hist BV User")
    pkg = db_session.query(Package).filter(Package.is_active == True).first()

    custom_bv = 25000.0
    hist_purchase = Purchase(
        purchase_code="PUR-HIST-BV-001",
        user_id=user.id,
        package_id=pkg.id,
        amount=30000.0,
        product_value=25000.0,
        gst_amount=5000.0,
        bv=custom_bv,
        status="COMPLETED"
    )
    db_session.add(hist_purchase)
    db_session.commit()

    fetched = db_session.query(Purchase).filter(Purchase.purchase_code == "PUR-HIST-BV-001").first()
    assert fetched.bv == custom_bv


# =========================================================================
# TEST 8: Direct Commission: ₹30,000 BV × 10% = ₹3,000 to personal sponsor ONLY
# =========================================================================
def test_8_direct_commission_is_10_percent_of_bv_3000(db_session: Session):
    upline_root = make_user(db_session, "root_sponsor@mlm.local", "Root Sponsor")
    sponsor_a = make_user(db_session, "sponsor_a@mlm.local", "Sponsor A", sponsor_id=upline_root.id)
    buyer_b = make_user(db_session, "buyer_b@mlm.local", "Buyer B", sponsor_id=sponsor_a.id)

    pkg = db_session.query(Package).filter(Package.is_active == True).first()
    purchase, events = process_package_purchase(db_session, user_id=buyer_b.id, package_id=pkg.id)

    # Sponsor A receives ₹3,000 (10% of 30,000 BV)
    a_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == sponsor_a.id,
        Commission.purchase_id == purchase.id
    ).first()
    assert a_comm is not None
    assert a_comm.amount == 3000.0
    assert a_comm.commission_type in ["DIRECT_REFERRAL", "DIRECT_COMMISSION"]

    # Root Upline receives ₹0 Direct Commission
    root_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == upline_root.id,
        Commission.purchase_id == purchase.id
    ).all()
    assert len(root_comm) == 0


# =========================================================================
# TEST 9: Pair Bonus: 30k Left + 30k Right = ₹10,000 Pair Bonus to user ONLY
# =========================================================================
def test_9_pair_bonus_30k_left_30k_right_equals_10000(db_session: Session):
    root = make_user(db_session, "pair_user@mlm.local", "Pair User")
    left_child = make_user(db_session, "left_child@mlm.local", "Left Child", sponsor_id=root.id, binary_parent_id=root.id, binary_position="LEFT")
    right_child = make_user(db_session, "right_child@mlm.local", "Right Child", sponsor_id=root.id, binary_parent_id=root.id, binary_position="RIGHT")

    pkg = db_session.query(Package).filter(Package.is_active == True).first()

    # Left child purchases package (30k BV)
    process_package_purchase(db_session, user_id=left_child.id, package_id=pkg.id, slot_id="SLOT-PAIR-01")

    # Right child purchases package (30k BV in same slot)
    process_package_purchase(db_session, user_id=right_child.id, package_id=pkg.id, slot_id="SLOT-PAIR-01")

    # Verify Pair bonus of ₹10,000 was awarded to root
    pair_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == root.id,
        Commission.commission_type == "PAIR_BONUS"
    ).first()
    assert pair_comm is not None
    assert pair_comm.amount == 10000.0


# =========================================================================
# TEST 10: Pair does NOT create Upline/Matching commission (Upline = ₹0)
# =========================================================================
def test_10_pair_does_not_create_upline_matching_commission(db_session: Session):
    grandparent = make_user(db_session, "grandparent@mlm.local", "Grandparent")
    parent_b = make_user(db_session, "parent_b@mlm.local", "Parent B", sponsor_id=grandparent.id, binary_parent_id=grandparent.id, binary_position="LEFT")
    child_left = make_user(db_session, "child_left@mlm.local", "Child Left", sponsor_id=parent_b.id, binary_parent_id=parent_b.id, binary_position="LEFT")
    child_right = make_user(db_session, "child_right@mlm.local", "Child Right", sponsor_id=parent_b.id, binary_parent_id=parent_b.id, binary_position="RIGHT")

    pkg = db_session.query(Package).filter(Package.is_active == True).first()
    process_package_purchase(db_session, user_id=child_left.id, package_id=pkg.id, slot_id="SLOT-NO-UPLINE-01")
    process_package_purchase(db_session, user_id=child_right.id, package_id=pkg.id, slot_id="SLOT-NO-UPLINE-01")

    # Parent B gets ₹10,000 Pair bonus
    b_pair = db_session.query(Commission).filter(
        Commission.beneficiary_id == parent_b.id,
        Commission.commission_type == "PAIR_BONUS"
    ).first()
    assert b_pair is not None
    assert b_pair.amount == 10000.0

    # Grandparent receives ZERO matching or upline bonus from B's pair
    gp_comms = db_session.query(Commission).filter(
        Commission.beneficiary_id == grandparent.id,
        Commission.commission_type.in_(["MATCHING_COMMISSION", "UPLINE_COMMISSION", "CARRY_COMMISSION"])
    ).all()
    assert len(gp_comms) == 0

    # Total matching commission in database is 0
    all_matching = db_session.query(Commission).filter(
        Commission.commission_type.in_(["MATCHING_COMMISSION", "UPLINE_COMMISSION"])
    ).all()
    assert len(all_matching) == 0


# =========================================================================
# TEST 11: Static QR Image asset exists and is accessible
# =========================================================================
def test_11_static_qr_image_asset_exists():
    root_dir = Path(r"D:\amol_personal\pr\MLM")
    qr_path = root_dir / "frontend" / "public" / "payment-qr.png"
    assert qr_path.exists(), f"Static payment QR not found at {qr_path}"
    assert qr_path.stat().st_size > 0, "Static payment QR file is empty"


# =========================================================================
# TEST 12: Static QR path is constant and does NOT inject dynamic query params
# =========================================================================
def test_12_qr_remains_static_across_different_users(client, db_session: Session):
    user1 = make_user(db_session, "user1_qr@mlm.local", "User 1 QR")
    user2 = make_user(db_session, "user2_qr@mlm.local", "User 2 QR")

    tok1 = create_access_token(user1.id, user1.role)
    tok2 = create_access_token(user2.id, user2.role)

    res1 = client.get("/api/package/activation-status", headers={"Authorization": f"Bearer {tok1}"})
    res2 = client.get("/api/package/activation-status", headers={"Authorization": f"Bearer {tok2}"})

    qr1 = res1.json()["data"]["upi_details"]["qr_image_url"]
    qr2 = res2.json()["data"]["upi_details"]["qr_image_url"]

    assert qr1 == "/payment-qr.png"
    assert qr2 == "/payment-qr.png"
    assert qr1 == qr2
    # Ensure no dynamic parameters like ?amount=, ?user_id=, ?ts=
    assert "?" not in qr1


# =========================================================================
# TEST 13: PIN order rejects manipulated amount
# =========================================================================
def test_13_pin_order_rejects_manipulated_amount(client, db_session: Session):
    user = make_user(db_session, "pin_buyer@mlm.local", "PIN Buyer")
    tok = create_access_token(user.id, user.role)

    # Try ordering 2 PINs (should be 2 * 35400 = 70800), but submitting 70000
    res = client.post(
        "/api/security-pins/orders",
        json={
            "quantity": 2,
            "amount": 70000.0,
            "payment_reference": "REF-BAD-AMOUNT-1"
        },
        headers={"Authorization": f"Bearer {tok}"}
    )
    assert res.status_code == 400
    assert "Invalid PIN order amount" in res.json()["detail"]
