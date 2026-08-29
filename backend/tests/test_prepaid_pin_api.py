import pytest
from fastapi.testclient import TestClient
from app.main import app
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
from app.security import hash_password, create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_api_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Clean
    db.query(SecurityPinLedger).delete()
    db.query(SecurityPinTransfer).delete()
    db.query(SecurityPinUplineRequest).delete()
    db.query(SecurityPin).delete()
    db.query(SecurityPinOrder).delete()
    db.query(Commission).delete()
    db.query(Purchase).delete()
    db.query(BinaryVolume).delete()
    db.query(User).delete()
    db.query(Package).delete()
    db.commit()

    # Package
    pkg = Package(
        id=1,
        name="Premium Franchise Package",
        price=35000.0,
        product_value=30000.0,
        gst_amount=5000.0,
        bv=30000.0,
        is_active=True
    )
    db.add(pkg)

    # Admin
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

    # Amol
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

    # Member B (downline)
    user_b = User(
        id=3,
        user_code="USR-B",
        email="user_b@test.com",
        mobile="9222222222",
        full_name="Member B",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="B01",
        sponsor_id=2,
        binary_parent_id=2,
        binary_position="LEFT",
        is_active=False
    )
    db.add(user_b)

    db.commit()
    db.close()
    yield

def get_headers(user_id: int, role: str = "USER") -> dict:
    token = create_access_token(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}

def test_full_pin_inventory_api_flow():
    admin_headers = get_headers(1, "ADMIN")
    amol_headers = get_headers(2, "USER")
    b_headers = get_headers(3, "USER")

    # 1. Amol orders 10 PINs
    order_res = client.post(
        "/api/security-pins/orders",
        json={
            "package_id": 1,
            "quantity": 10,
            "payment_method": "UPI_TRANSFER",
            "payment_reference": "UTR-API-10PINS"
        },
        headers=amol_headers
    )
    assert order_res.status_code == 200
    order_data = order_res.json()["data"]
    order_id = order_data["id"]
    assert order_data["quantity"] == 10
    assert order_data["total_amount"] == 350000.0

    # 2. Admin lists orders & verifies payment
    admin_orders = client.get("/api/admin/security-pins/orders", headers=admin_headers)
    assert admin_orders.status_code == 200
    assert admin_orders.json()["data"]["total"] >= 1

    verify_res = client.post(
        f"/api/admin/security-pins/orders/{order_id}/verify",
        json={"admin_notes": "Verified 3.5 Lakhs received"},
        headers=admin_headers
    )
    assert verify_res.status_code == 200

    # 3. Admin issues batch of 10 PINs
    issue_res = client.post(
        f"/api/admin/security-pins/orders/{order_id}/issue",
        json={"expires_in_days": 30},
        headers=admin_headers
    )
    assert issue_res.status_code == 200
    assert issue_res.json()["data"]["count"] == 10

    # 4. Amol checks wallet
    inv_res = client.get("/api/security-pins/inventory", headers=amol_headers)
    assert inv_res.status_code == 200
    assert inv_res.json()["data"]["wallet"]["available"] == 10

    # 5. Amol uses 1 PIN to activate
    use_res = client.post("/api/security-pins/use", json={}, headers=amol_headers)
    assert use_res.status_code == 200
    assert use_res.json()["data"]["purchase"]["bv"] == 30000.0

    # Check remaining: 9 available, 1 used
    inv_res2 = client.get("/api/security-pins/inventory", headers=amol_headers)
    assert inv_res2.json()["data"]["wallet"]["available"] == 9
    assert inv_res2.json()["data"]["wallet"]["used"] == 1

    # 6. Amol checks eligible downlines
    downlines_res = client.get("/api/security-pins/downline-eligible", headers=amol_headers)
    assert downlines_res.status_code == 200
    downlines = downlines_res.json()["data"]
    assert any(d["id"] == 3 for d in downlines)

    # 7. Amol transfers 1 PIN to Member B
    trf_res = client.post(
        "/api/security-pins/transfer",
        json={
            "to_user_identifier": "USR-B",
            "quantity": 1,
            "reason": "Gift from sponsor"
        },
        headers=amol_headers
    )
    assert trf_res.status_code == 200

    # Member B checks wallet: 1 available, 1 received
    b_inv = client.get("/api/security-pins/inventory", headers=b_headers)
    assert b_inv.status_code == 200
    assert b_inv.json()["data"]["wallet"]["available"] == 1
    assert b_inv.json()["data"]["wallet"]["received"] == 1

    # 8. Member B activates package with their received PIN
    b_act = client.post("/api/security-pins/use", json={}, headers=b_headers)
    assert b_act.status_code == 200
    assert b_act.json()["data"]["purchase"]["bv"] == 30000.0

    # 9. Admin checks transfers audit and ledger
    trf_audit = client.get("/api/admin/security-pins/transfers", headers=admin_headers)
    assert trf_audit.status_code == 200
    assert len(trf_audit.json()["data"]["items"]) >= 1

    ledger_audit = client.get("/api/admin/security-pins/ledger", headers=admin_headers)
    assert ledger_audit.status_code == 200
    assert len(ledger_audit.json()["data"]["items"]) >= 1
