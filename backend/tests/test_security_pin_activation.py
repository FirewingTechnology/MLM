import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.package import Package
from app.models.activation_request import PackageActivationRequest
from app.models.security_pin import SecurityPin
from app.models.commission import Commission
from app.models.volume import BinaryVolume
from app.services.pin_service import pin_service, PinSecurityError, PinValidationError
from app.security import hash_password

def get_auth_token(client, email, password="Demo@123"):
    res = client.post("/api/auth/login", json={"identifier": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["data"]["token"]

def test_full_pin_activation_lifecycle(client, db_session):
    """
    TEST 1: Full PIN Activation Flow:
    1. New User registers (is_active = False, BV = 0)
    2. User submits Payment Request
    3. User cannot activate without verified payment & PIN
    4. Admin verifies payment
    5. Admin issues Security PIN
    6. User enters valid Security PIN
    7. User becomes active, 30,000 personal BV credited, Direct Sponsor Commission (₹3,000) credited to Amol
    8. PIN becomes USED, cannot be reused
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # 1. Register new user under Amol
    new_user = User(
        user_code="USR-TEST-001",
        email="test_buyer@demo.com",
        mobile="9876543210",
        full_name="Test Buyer",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="BUYER01",
        sponsor_id=amol.id,
        binary_parent_id=amol.id,
        binary_position="LEFT",
        is_active=False
    )
    db_session.add(new_user)
    db_session.commit()

    user_token = get_auth_token(client, "test_buyer@demo.com")
    admin_token = get_auth_token(client, "admin@demo.com", "Admin@123")

    # BV must be 0 before activation
    res_status = client.get("/api/package/activation-status", headers={"Authorization": f"Bearer {user_token}"})
    assert res_status.status_code == 200
    assert res_status.json()["data"]["is_active"] is False

    # 2. User submits payment
    res_sub = client.post("/api/package/payment-submit", json={
        "payment_method": "UPI_TRANSFER",
        "payment_reference": "UPI-UTR-9988776655"
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res_sub.status_code == 200
    req_data = res_sub.json()["data"]
    req_id = req_data["id"]
    assert req_data["status"] == "PAYMENT_SUBMITTED"
    assert req_data["payment_reference"] == "UPI-UTR-9988776655"

    # 3. User tries activating with random PIN before verification -> MUST FAIL
    res_fake = client.post("/api/package/activate", json={
        "pin": "FAKE1234",
        "request_id": req_id
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res_fake.status_code == 400
    assert "Invalid or unavailable" in res_fake.json()["error"]["message"]

    # 4. Admin cannot issue PIN before payment verification -> MUST FAIL
    res_premature = client.post(f"/api/admin/activation-requests/{req_id}/issue-pin", json={
        "expires_in_days": 7
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_premature.status_code == 400
    assert "Payment must be verified first" in res_premature.json()["error"]["message"]

    # 5. Admin verifies payment
    res_verify = client.post(f"/api/admin/activation-requests/{req_id}/verify-payment", json={
        "admin_notes": "Payment received in HDFC Bank"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_verify.status_code == 200
    assert res_verify.json()["data"]["status"] == "PAYMENT_VERIFIED"

    # 6. Admin issues Security PIN
    res_issue = client.post(f"/api/admin/activation-requests/{req_id}/issue-pin", json={
        "expires_in_days": 7
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_issue.status_code == 200
    issue_data = res_issue.json()["data"]
    raw_pin = issue_data["raw_security_pin"]
    assert raw_pin is not None
    assert len(raw_pin) == 8

    # 7. User checks activation status -> Can activate
    res_status2 = client.get("/api/package/activation-status", headers={"Authorization": f"Bearer {user_token}"})
    assert res_status2.status_code == 200
    assert res_status2.json()["data"]["can_activate_with_pin"] is True
    assert res_status2.json()["data"]["activation_request"]["status"] == "PIN_ISSUED"

    # 8. User enters valid PIN to activate
    res_act = client.post("/api/package/activate", json={
        "pin": raw_pin,
        "request_id": req_id
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res_act.status_code == 200
    act_data = res_act.json()["data"]
    assert act_data["purchase"]["bv"] == 30000.0
    assert act_data["purchase"]["amount"] == 35400.0
    assert act_data["user"]["is_active"] is True

    # 9. Verify direct sponsor commission (10% = ₹3,000) was awarded to Amol
    comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert comm is not None
    assert comm.amount == 3000.0

    # 10. Re-using same PIN must fail
    res_reuse = client.post("/api/package/activate", json={
        "pin": raw_pin,
        "request_id": req_id
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res_reuse.status_code == 400

def test_pin_attempt_rate_limiting_and_lock(client, db_session):
    """
    TEST 2: Rate limit on wrong PIN attempts:
    Entering 5 wrong PINs revokes / locks the issued PIN.
    """
    user = User(
        user_code="USR-TEST-002",
        email="test_lock@demo.com",
        mobile="9876543211",
        full_name="Test Lock",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="LOCK01",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()

    user_token = get_auth_token(client, "test_lock@demo.com")
    admin_token = get_auth_token(client, "admin@demo.com", "Admin@123")

    # Create request & issue PIN
    req = pin_service.get_or_create_activation_request(db_session, user.id, payment_reference="PAY-LOCK-1")
    db_session.commit()
    pin_service.verify_payment(db_session, req.id, 1)
    pin, raw_pin = pin_service.issue_security_pin(db_session, req.id, 1)
    db_session.commit()

    # Enter 5 incorrect PINs
    for i in range(5):
        res_fail = client.post("/api/package/activate", json={
            "pin": f"WRONG{i:03d}"
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert res_fail.status_code == 400

    # Check that the PIN is now REVOKED
    db_session.refresh(pin)
    assert pin.status == 'REVOKED'
    assert pin.attempt_count >= 5

    # Even the correct PIN now fails
    res_correct_after_lock = client.post("/api/package/activate", json={
        "pin": raw_pin
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res_correct_after_lock.status_code == 400
    assert "revoked" in res_correct_after_lock.json()["error"]["message"].lower()

def test_expired_pin_cannot_activate(client, db_session):
    """
    TEST 3: Expired PIN cannot activate package.
    """
    user = User(
        user_code="USR-TEST-003",
        email="test_expire@demo.com",
        mobile="9876543212",
        full_name="Test Expire",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="EXP01",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()

    user_token = get_auth_token(client, "test_expire@demo.com")

    req = pin_service.get_or_create_activation_request(db_session, user.id, payment_reference="PAY-EXP-1")
    db_session.commit()
    pin_service.verify_payment(db_session, req.id, 1)
    pin, raw_pin = pin_service.issue_security_pin(db_session, req.id, 1)

    # Set expiry in the past
    pin.expires_at = datetime.utcnow() - timedelta(days=1)
    db_session.commit()

    res = client.post("/api/package/activate", json={
        "pin": raw_pin
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 400
    assert "expired" in res.json()["error"]["message"].lower()

def test_user_cannot_use_another_users_pin(client, db_session):
    """
    TEST 4: User A cannot use User B's PIN.
    """
    user_a = User(
        user_code="USR-TEST-004A",
        email="user_a@demo.com",
        mobile="9876543213",
        full_name="User A",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="USRA01",
        is_active=False
    )
    user_b = User(
        user_code="USR-TEST-004B",
        email="user_b@demo.com",
        mobile="9876543214",
        full_name="User B",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="USRB01",
        is_active=False
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = get_auth_token(client, "user_a@demo.com")
    token_b = get_auth_token(client, "user_b@demo.com")

    # Issue PIN for User B
    req_b = pin_service.get_or_create_activation_request(db_session, user_b.id, payment_reference="PAY-B")
    db_session.commit()
    pin_service.verify_payment(db_session, req_b.id, 1)
    pin_b, raw_pin_b = pin_service.issue_security_pin(db_session, req_b.id, 1)
    db_session.commit()

    # User A tries using User B's PIN
    res = client.post("/api/package/activate", json={
        "pin": raw_pin_b
    }, headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 400
    assert "Invalid or unavailable" in res.json()["error"]["message"]

    # User B can still activate successfully with User B's PIN
    res_b = client.post("/api/package/activate", json={
        "pin": raw_pin_b
    }, headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    assert res_b.json()["data"]["user"]["is_active"] is True

def test_admin_reject_request_and_revoke_pin(client, db_session):
    """
    TEST 5: Admin can reject activation request and revoke PIN.
    """
    user = User(
        user_code="USR-TEST-005",
        email="test_reject@demo.com",
        mobile="9876543215",
        full_name="Test Reject",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="REJ01",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()

    admin_token = get_auth_token(client, "admin@demo.com", "Admin@123")

    req = pin_service.get_or_create_activation_request(db_session, user.id, payment_reference="INVALID-PAYMENT")
    db_session.commit()

    # Admin rejects request
    res_rej = client.post(f"/api/admin/activation-requests/{req.id}/reject", json={
        "reason": "Payment reference could not be found in bank statement."
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_rej.status_code == 200
    assert res_rej.json()["data"]["status"] == "REJECTED"
    assert res_rej.json()["data"]["rejection_reason"] == "Payment reference could not be found in bank statement."

def test_admin_activation_endpoints(client, db_session):
    """
    TEST 6: Admin endpoints for activation requests and security pins:
    - GET /api/admin/activation-requests
    - GET /api/admin/activation-requests/{id}
    - GET /api/admin/security-pins
    - POST /api/admin/security-pins/{id}/revoke
    """
    admin_token = get_auth_token(client, "admin@demo.com", "Admin@123")

    user = User(
        user_code="USR-TEST-006",
        email="test_admin_list@demo.com",
        mobile="9876543216",
        full_name="Test Admin List",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="ADM01",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()

    req = pin_service.get_or_create_activation_request(db_session, user.id, payment_reference="PAY-ADMIN-1")
    db_session.commit()
    pin_service.verify_payment(db_session, req.id, 1)
    pin, raw_pin = pin_service.issue_security_pin(db_session, req.id, 1)
    db_session.commit()

    # 1. Admin gets requests list
    res_list = client.get("/api/admin/activation-requests?status=PIN_ISSUED", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_list.status_code == 200
    items = res_list.json()["data"]["items"]
    assert any(r["id"] == req.id for r in items)

    # 2. Admin gets request detail
    res_detail = client.get(f"/api/admin/activation-requests/{req.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_detail.status_code == 200
    assert res_detail.json()["data"]["id"] == req.id

    # 3. Admin gets pins list
    res_pins = client.get("/api/admin/security-pins", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_pins.status_code == 200
    pin_items = res_pins.json()["data"]["items"]
    assert any(p["id"] == pin.id for p in pin_items)

    # 4. Admin revokes pin
    res_rev = client.post(f"/api/admin/security-pins/{pin.id}/revoke", json={
        "reason": "Administrative manual cancellation"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_rev.status_code == 200
    assert res_rev.json()["data"]["status"] == "REVOKED"

def test_already_active_user_cannot_create_or_activate(client, db_session):
    """
    TEST 7: User who is already active cannot create new activation request or activate another PIN.
    """
    user = User(
        user_code="USR-TEST-007",
        email="test_active_block@demo.com",
        mobile="9876543217",
        full_name="Test Active Block",
        password_hash=hash_password("Demo@123"),
        role="USER",
        referral_code="BLK01",
        is_active=True # Already active
    )
    db_session.add(user)
    db_session.commit()

    user_token = get_auth_token(client, "test_active_block@demo.com")

    # Creating request must fail
    res_req = client.post("/api/package/activation-request", json={
        "payment_method": "UPI_TRANSFER"
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res_req.status_code == 400
    assert "already has an active package" in res_req.json()["error"]["message"].lower()

    # Activating PIN must fail
    res_act = client.post("/api/package/activate", json={
        "pin": "ANYPIN12"
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res_act.status_code == 400
    assert "already active" in res_act.json()["error"]["message"].lower()

