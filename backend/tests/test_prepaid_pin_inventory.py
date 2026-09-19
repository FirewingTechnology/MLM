import pytest
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.package import Package
from app.models.purchase import Purchase
from app.models.volume import BinaryVolume
from app.models.commission import Commission
from app.models.pin_order import SecurityPinOrder
from app.models.pin_transfer import SecurityPinTransfer
from app.models.pin_upline_request import SecurityPinUplineRequest
from app.models.pin_ledger import SecurityPinLedger
from app.models.security_pin import SecurityPin
from app.services.pin_service import pin_service, PinValidationError, PinSecurityError
from app.security import hash_password

from app.models.activation_request import PackageActivationRequest

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Clean tables
    db.query(SecurityPinLedger).delete()
    db.query(SecurityPinTransfer).delete()
    db.query(SecurityPinUplineRequest).delete()
    db.query(SecurityPin).delete()
    db.query(SecurityPinOrder).delete()
    db.query(PackageActivationRequest).delete()
    db.query(Commission).delete()
    db.query(Purchase).delete()
    db.query(BinaryVolume).delete()
    db.query(User).delete()
    db.query(Package).delete()
    db.commit()

    # Create Package
    pkg = Package(
        id=1,
        name="Premium Franchise Package",
        price=35400.0,
        product_value=30000.0,
        gst_amount=5400.0,
        bv=30000.0,
        is_active=True
    )
    db.add(pkg)

    # Create Admin (id=1)
    admin = User(
        id=1,
        user_code="ADM-001",
        email="admin@test.com",
        mobile="9000000000",
        full_name="System Admin",
        password_hash=hash_password("Admin@123"),
        role="ADMIN",
        referral_code="ADM01",
        is_active=True
    )
    db.add(admin)

    # Create Root / Leader Amol (id=2)
    amol = User(
        id=2,
        user_code="USR-AMOL",
        email="amol@test.com",
        mobile="9111111111",
        full_name="Amol Sharma",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="AMOL01",
        sponsor_id=None,
        binary_parent_id=None,
        is_active=False
    )
    db.add(amol)
    db.flush()

    # Create Downline User B (id=3, under Amol on LEFT)
    user_b = User(
        id=3,
        user_code="USR-B",
        email="user_b@test.com",
        mobile="9222222222",
        full_name="Member B",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="B01",
        sponsor_id=2, # Sponsored by Amol
        binary_parent_id=2, # Under Amol
        binary_position="LEFT",
        is_active=False
    )
    db.add(user_b)

    # Create Downline User C (id=4, under Member B on LEFT)
    user_c = User(
        id=4,
        user_code="USR-C",
        email="user_c@test.com",
        mobile="9333333333",
        full_name="Member C",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="C01",
        sponsor_id=3, # Sponsored by B
        binary_parent_id=3, # Under B
        binary_position="LEFT",
        is_active=False
    )
    db.add(user_c)

    # Create Stranger / Unrelated User X (id=5, no connection to Amol)
    user_x = User(
        id=5,
        user_code="USR-X",
        email="stranger@test.com",
        mobile="9444444444",
        full_name="Stranger X",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="X01",
        sponsor_id=None,
        binary_parent_id=None,
        is_active=False
    )
    db.add(user_x)

    db.commit()
    db.close()
    yield

def test_bulk_pin_order_and_admin_issuance():
    db = SessionLocal()
    # 1. Amol requests 10 PINs
    order = pin_service.create_pin_order(
        db=db,
        user_id=2,
        package_id=1,
        quantity=10,
        payment_method="UPI_TRANSFER",
        payment_reference="UPI-AMOL-10PINS-999"
    )
    db.commit()

    assert order.quantity == 10
    assert order.total_amount == 354000.0
    assert order.status == 'PAYMENT_SUBMITTED'

    # Cannot issue before payment verification
    with pytest.raises(PinValidationError):
        pin_service.admin_issue_pin_batch(db, order.id, admin_id=1)

    # 2. Admin verifies payment
    order = pin_service.admin_verify_order_payment(db, order.id, admin_id=1, admin_notes="Received 3.5L via NEFT")
    db.commit()
    assert order.status == 'PAYMENT_VERIFIED'

    # 3. Admin issues PINs
    order, generated_pins = pin_service.admin_issue_pin_batch(db, order.id, admin_id=1, expires_in_days=30)
    db.commit()

    assert order.status == 'COMPLETED'
    assert len(generated_pins) == 10

    # 4. Check Amol's PIN Wallet
    inv = pin_service.get_user_pin_inventory(db, user_id=2)
    assert inv['wallet']['available'] == 10
    assert inv['wallet']['used'] == 0
    assert inv['wallet']['transferred'] == 0
    assert len(inv['available_pins']) == 10
    db.close()

def test_amol_use_own_pin_to_activate():
    db = SessionLocal()
    # Issue 10 PINs to Amol
    order = pin_service.create_pin_order(db=db, user_id=2, package_id=1, quantity=10, payment_reference="REF-AMOL-1")
    order = pin_service.admin_verify_order_payment(db, order.id, admin_id=1)
    order, pins = pin_service.admin_issue_pin_batch(db, order.id, admin_id=1)
    db.commit()

    # Amol uses 1 PIN to activate his own account
    res = pin_service.user_use_own_pin_to_activate(db, user_id=2)
    db.commit()

    # Verify Amol is now active and 30k BV credited
    amol = db.get(User, 2)
    assert amol.is_active is True
    assert res['purchase']['amount'] == 35400.0
    assert res['purchase']['bv'] == 30000.0

    # Amol's inventory should now have 9 available, 1 used
    inv = pin_service.get_user_pin_inventory(db, user_id=2)
    assert inv['wallet']['available'] == 9
    assert inv['wallet']['used'] == 1

    # Amol cannot activate again (already active)
    with pytest.raises(PinValidationError):
        pin_service.user_use_own_pin_to_activate(db, user_id=2)

    db.close()

def test_pin_transfer_to_downline_and_activation():
    db = SessionLocal()
    # Issue 5 PINs to Amol
    order = pin_service.create_pin_order(db=db, user_id=2, package_id=1, quantity=5, payment_reference="REF-AMOL-5")
    order = pin_service.admin_verify_order_payment(db, order.id, admin_id=1)
    order, pins = pin_service.admin_issue_pin_batch(db, order.id, admin_id=1)
    db.commit()

    # 1. Amol transfers 1 PIN to Member B (User 3)
    transferred = pin_service.user_transfer_pin_to_downline(
        db=db,
        from_user_id=2,
        to_user_identifier=3,
        quantity=1,
        reason="Activation gift"
    )
    db.commit()

    assert len(transferred) == 1
    transferred_pin_id = transferred[0]['id']

    # Amol wallet check: 4 available, 1 transferred
    amol_inv = pin_service.get_user_pin_inventory(db, user_id=2)
    assert amol_inv['wallet']['available'] == 4
    assert amol_inv['wallet']['transferred'] == 1

    # Member B wallet check: 1 available, 1 received
    b_inv = pin_service.get_user_pin_inventory(db, user_id=3)
    assert b_inv['wallet']['available'] == 1
    assert b_inv['wallet']['received'] == 1

    # 2. Amol CANNOT use the transferred PIN
    with pytest.raises(PinValidationError):
        pin_service.user_use_own_pin_to_activate(db, user_id=2, pin_id=transferred_pin_id)

    # 3. Member B activates package with their received PIN
    res_b = pin_service.user_use_own_pin_to_activate(db, user_id=3, pin_id=transferred_pin_id)
    db.commit()

    user_b = db.get(User, 3)
    assert user_b.is_active is True
    assert res_b['purchase']['bv'] == 30000.0

    # Member B wallet: 0 available, 1 used
    b_inv = pin_service.get_user_pin_inventory(db, user_id=3)
    assert b_inv['wallet']['available'] == 0
    assert b_inv['wallet']['used'] == 1

    # 4. PIN is now USED and cannot be transferred or reused
    with pytest.raises(PinValidationError):
        pin_service.user_transfer_pin_to_downline(db, from_user_id=3, to_user_identifier=4, pin_id=transferred_pin_id)

    db.close()

def test_transfer_to_stranger_rejected():
    db = SessionLocal()
    # Issue PIN to Amol
    order = pin_service.create_pin_order(db=db, user_id=2, package_id=1, quantity=2, payment_reference="REF-AMOL-2")
    order = pin_service.admin_verify_order_payment(db, order.id, admin_id=1)
    order, pins = pin_service.admin_issue_pin_batch(db, order.id, admin_id=1)
    db.commit()

    # Amol attempts to transfer to Stranger X (id=5) -> Must fail
    with pytest.raises(PinValidationError) as exc:
        pin_service.user_transfer_pin_to_downline(db, from_user_id=2, to_user_identifier=5, quantity=1)
    assert "not in your eligible downline network" in str(exc.value)

    db.close()

def test_upline_pin_request_approval_and_rejection():
    db = SessionLocal()
    # Issue PINs to Amol
    order = pin_service.create_pin_order(db=db, user_id=2, package_id=1, quantity=5, payment_reference="REF-AMOL-5")
    order = pin_service.admin_verify_order_payment(db, order.id, admin_id=1)
    order, pins = pin_service.admin_issue_pin_batch(db, order.id, admin_id=1)
    db.commit()

    # 1. Member B requests 1 PIN from Amol (upline)
    req1 = pin_service.request_pin_from_upline(
        db=db,
        requester_user_id=3,
        upline_id=2,
        quantity=1,
        notes="Please provide 1 activation PIN"
    )
    db.commit()
    assert req1.status == 'PENDING'

    # Amol approves request
    approval_res = pin_service.upline_approve_pin_request(db, request_id=req1.id, upline_user_id=2)
    db.commit()

    assert approval_res['request']['status'] == 'APPROVED'
    assert len(approval_res['transferred_pins']) == 1

    # B now has 1 available PIN
    b_inv = pin_service.get_user_pin_inventory(db, user_id=3)
    assert b_inv['wallet']['available'] == 1

    # 2. Member C requests 1 PIN from Member B, but Member B rejects
    req2 = pin_service.request_pin_from_upline(
        db=db,
        requester_user_id=4,
        upline_id=3,
        quantity=1,
        notes="PIN for activation"
    )
    db.commit()

    rej_req = pin_service.upline_reject_pin_request(db, request_id=req2.id, upline_user_id=3, reason="Out of stock")
    db.commit()

    assert rej_req.status == 'REJECTED'
    assert rej_req.rejection_reason == "Out of stock"

    # Member C still has 0 PINs
    c_inv = pin_service.get_user_pin_inventory(db, user_id=4)
    assert c_inv['wallet']['available'] == 0

    db.close()

def test_independent_downline_purchase_from_admin():
    db = SessionLocal()
    # Member B purchases 3 PINs directly from Admin
    order = pin_service.create_pin_order(db=db, user_id=3, package_id=1, quantity=3, payment_reference="REF-B-3PINS")
    order = pin_service.admin_verify_order_payment(db, order.id, admin_id=1)
    order, pins = pin_service.admin_issue_pin_batch(db, order.id, admin_id=1)
    db.commit()

    # Member B has exactly 3 PINs
    b_inv = pin_service.get_user_pin_inventory(db, user_id=3)
    assert b_inv['wallet']['available'] == 3

    # Member B transfers 1 PIN to their downline Member C (User 4)
    transferred = pin_service.user_transfer_pin_to_downline(db, from_user_id=3, to_user_identifier=4, quantity=1)
    db.commit()

    assert len(transferred) == 1
    assert pin_service.get_user_pin_inventory(db, user_id=3)['wallet']['available'] == 2
    assert pin_service.get_user_pin_inventory(db, user_id=4)['wallet']['available'] == 1

    db.close()

def test_pin_ledger_and_audit_trail():
    db = SessionLocal()
    # Complete lifecycle: Order -> Verify -> Issue -> Transfer -> Use
    order = pin_service.create_pin_order(db=db, user_id=2, package_id=1, quantity=1, payment_reference="REF-AUDIT-1")
    order = pin_service.admin_verify_order_payment(db, order.id, admin_id=1)
    order, pins = pin_service.admin_issue_pin_batch(db, order.id, admin_id=1)
    db.commit()

    pin_id = pins[0]['id']

    # Transfer to B
    pin_service.user_transfer_pin_to_downline(db, from_user_id=2, to_user_identifier=3, pin_id=pin_id)
    db.commit()

    # B activates
    pin_service.user_use_own_pin_to_activate(db, user_id=3, pin_id=pin_id)
    db.commit()

    # Verify ledger entries for this PIN
    ledgers = db.query(SecurityPinLedger).filter(SecurityPinLedger.pin_id == pin_id).order_by(SecurityPinLedger.id.asc()).all()
    actions = [l.action for l in ledgers]
    assert 'PIN_PURCHASED' in actions
    assert 'PIN_TRANSFERRED' in actions
    assert 'PIN_TRANSFER_RECEIVED' in actions
    assert 'PIN_USED' in actions

    db.close()
