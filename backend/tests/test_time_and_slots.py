from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from app.services.time_service import SlotService, TimeProvider, IST
from app.models.demo_time import DemoTimeConfig
from app.models.user import User
from app.models.purchase import Purchase
from app.models.commission import Commission
from app.services.commission_service import process_package_purchase

def test_slot_service_pure_logic():
    # 1. 11:59:59 AM -> Slot 1
    dt_1159_am = datetime(2026, 8, 26, 11, 59, 59, tzinfo=IST)
    assert SlotService.get_slot_number(dt_1159_am) == 1
    assert SlotService.get_slot_id(dt_1159_am) == "2026-08-26-S1"

    # 2. 12:00:00 PM -> Slot 2
    dt_1200_pm = datetime(2026, 8, 26, 12, 0, 0, tzinfo=IST)
    assert SlotService.get_slot_number(dt_1200_pm) == 2
    assert SlotService.get_slot_id(dt_1200_pm) == "2026-08-26-S2"

    # 3. 11:59:59 PM -> Slot 2
    dt_1159_pm = datetime(2026, 8, 26, 23, 59, 59, tzinfo=IST)
    assert SlotService.get_slot_number(dt_1159_pm) == 2
    assert SlotService.get_slot_id(dt_1159_pm) == "2026-08-26-S2"

    # 4. 12:00:00 AM next day -> Slot 1 Next Day
    dt_1200_am_next = datetime(2026, 8, 27, 0, 0, 0, tzinfo=IST)
    assert SlotService.get_slot_number(dt_1200_am_next) == 1
    assert SlotService.get_slot_id(dt_1200_am_next) == "2026-08-27-S1"

    # Boundaries
    start_s1, end_s1 = SlotService.get_slot_boundaries(dt_1159_am)
    assert start_s1 == datetime(2026, 8, 26, 0, 0, 0, tzinfo=IST)
    assert end_s1 == datetime(2026, 8, 26, 12, 0, 0, tzinfo=IST)

    start_s2, end_s2 = SlotService.get_slot_boundaries(dt_1200_pm)
    assert start_s2 == datetime(2026, 8, 26, 12, 0, 0, tzinfo=IST)
    assert end_s2 == datetime(2026, 8, 27, 0, 0, 0, tzinfo=IST)

    # Next Slot start
    next_from_s1 = SlotService.get_next_slot_start(dt_1159_am)
    assert next_from_s1 == datetime(2026, 8, 26, 12, 0, 0, tzinfo=IST)

    next_from_s2 = SlotService.get_next_slot_start(dt_1200_pm)
    assert next_from_s2 == datetime(2026, 8, 27, 0, 0, 0, tzinfo=IST)

    # Previous Slot start
    prev_from_s1 = SlotService.get_previous_slot_start(dt_1159_am)
    assert prev_from_s1 == datetime(2026, 8, 25, 12, 0, 0, tzinfo=IST)

    prev_from_s2 = SlotService.get_previous_slot_start(dt_1200_pm)
    assert prev_from_s2 == datetime(2026, 8, 26, 0, 0, 0, tzinfo=IST)

    # Remaining Seconds
    rem = SlotService.get_remaining_seconds(dt_1159_am, end_s1)
    assert rem == 1
    assert SlotService.format_duration(rem) == "00:00:01"

def test_public_time_endpoint_real_mode(client):
    res = client.get("/api/time/current")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["mode"] == "REAL"
    assert data["timezone"] == "Asia/Kolkata"
    assert "slot_id" in data
    assert data["slot_number"] in (1, 2)
    assert "remaining_seconds" in data
    assert "remaining_formatted" in data

def test_admin_demo_time_workflow(client):
    # 1. Login as Admin
    login_res = client.post("/api/auth/login", json={
        "identifier": "admin@demo.com",
        "password": "Admin@123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}


    # 2. Switch to DEMO mode and set to 11:59 AM
    set_res = client.post("/api/admin/time/set", json={
        "datetime": "2026-08-26 11:59:00"
    }, headers=headers)
    assert set_res.status_code == 200
    set_data = set_res.json()["data"]
    assert set_data["mode"] == "DEMO"
    assert set_data["slot_id"] == "2026-08-26-S1"
    assert set_data["slot_number"] == 1
    assert set_data["remaining_seconds"] == 60

    # 3. Advance by +1 minute -> should automatically roll into SLOT 2
    adv_res = client.post("/api/admin/time/advance", json={
        "minutes": 1
    }, headers=headers)
    assert adv_res.status_code == 200
    adv_data = adv_res.json()["data"]
    assert adv_data["slot_id"] == "2026-08-26-S2"
    assert adv_data["slot_number"] == 2
    assert adv_data["time_formatted"].startswith("12:00:00 PM")

    # 4. Jump to Next Slot -> should jump to 12:00 AM next day (Slot 1)
    next_res = client.post("/api/admin/time/next-slot", headers=headers)
    assert next_res.status_code == 200
    next_data = next_res.json()["data"]
    assert next_data["slot_id"] == "2026-08-27-S1"
    assert next_data["slot_number"] == 1
    assert next_data["date"] == "2026-08-27"
    assert next_data["time_formatted"].startswith("12:00:00 AM")

    # 5. Jump to Previous Slot -> should jump to 12:00 PM previous day (Slot 2)
    prev_res = client.post("/api/admin/time/previous-slot", headers=headers)
    assert prev_res.status_code == 200
    prev_data = prev_res.json()["data"]
    assert prev_data["slot_id"] == "2026-08-26-S2"
    assert prev_data["slot_number"] == 2

    # 6. Reset to REAL TIME
    reset_res = client.post("/api/admin/time/reset", headers=headers)
    assert reset_res.status_code == 200
    reset_data = reset_res.json()["data"]
    assert reset_data["mode"] == "REAL"

def test_slot_aware_purchases_and_commissions(db_session):
    # Set demo time to Slot 1: 2026-08-26 10:00 AM
    TimeProvider.set_demo_time(db_session, datetime(2026, 8, 26, 10, 0, 0, tzinfo=IST))

    # Amol is root (USR-00002)
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    
    # Process a purchase for Amol
    purchase, events = process_package_purchase(db_session, amol.id)
    assert purchase.slot_id == "2026-08-26-S1"

    # Create a downline under Amol and purchase
    downline = User(
        user_code="USR-TEST01",
        email="test01@demo.com",
        mobile="9876599991",
        full_name="Downline User",
        password_hash="hash",
        role="USER",
        referral_code="REFTEST01",
        sponsor_id=amol.id,
        binary_parent_id=amol.id,
        binary_position="LEFT",
        is_active=False
    )
    db_session.add(downline)
    db_session.flush()

    dl_purchase, dl_events = process_package_purchase(db_session, downline.id)
    assert dl_purchase.slot_id == "2026-08-26-S1"

    # Check direct commission
    comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.purchase_id == dl_purchase.id
    ).first()
    assert comm is not None
    assert comm.slot_id == "2026-08-26-S1"
