import pytest
from app.models.user import User
from app.services.pair_service import pair_service
from app.services.commission_service import process_package_purchase
from app.services.time_service import time_provider

def test_carry_count_case_1_exact_pair(client, db_session):
    """
    TEST 1: LEFT = 30k, RIGHT = 30k
    After pair: LEFT CARRY = 0, RIGHT CARRY = 0
    PAID: 1, UNPAID: 0
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    login_res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    token = login_res.json()["data"]["token"]

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]

    assert "carry" in data
    carry = data["carry"]

    # Left
    assert carry["left"]["count"] == 0
    assert carry["left"]["unpaid_count"] == 0
    assert carry["left"]["paid_count"] == 1

    # Right
    assert carry["right"]["count"] == 0
    assert carry["right"]["unpaid_count"] == 0
    assert carry["right"]["paid_count"] == 1

def test_carry_count_case_2_unequal_pair_left_60k(client, db_session):
    """
    TEST 2: LEFT = 60k, RIGHT = 30k
    After one pair: LEFT CARRY = 1, RIGHT CARRY = 0
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    login_res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    token = login_res.json()["data"]["token"]

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    carry = res.json()["data"]["carry"]

    assert carry["left"]["count"] == 1
    assert carry["left"]["unpaid_count"] == 1
    assert carry["left"]["paid_count"] == 1

    assert carry["right"]["count"] == 0
    assert carry["right"]["unpaid_count"] == 0
    assert carry["right"]["paid_count"] == 1

def test_carry_count_case_3_unequal_pair_left_90k(client, db_session):
    """
    TEST 3: LEFT = 90k, RIGHT = 30k
    After one pair: LEFT CARRY = 2, RIGHT CARRY = 0
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 90000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_info.slot_id)
    db_session.commit()

    login_res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    token = login_res.json()["data"]["token"]

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    carry = res.json()["data"]["carry"]

    assert carry["left"]["count"] == 2
    assert carry["left"]["unpaid_count"] == 2
    assert carry["left"]["paid_count"] == 1

    assert carry["right"]["count"] == 0
    assert carry["right"]["unpaid_count"] == 0
    assert carry["right"]["paid_count"] == 1

def test_carry_count_case_4_unequal_pair_right_90k(client, db_session):
    """
    TEST 4: LEFT = 30k, RIGHT = 90k
    After one pair: LEFT CARRY = 0, RIGHT CARRY = 2
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 30000.0, slot_info.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 90000.0, slot_info.slot_id)
    db_session.commit()

    login_res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    token = login_res.json()["data"]["token"]

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    carry = res.json()["data"]["carry"]

    assert carry["left"]["count"] == 0
    assert carry["left"]["unpaid_count"] == 0
    assert carry["left"]["paid_count"] == 1

    assert carry["right"]["count"] == 2
    assert carry["right"]["unpaid_count"] == 2
    assert carry["right"]["paid_count"] == 1

def test_carry_count_case_5_and_6_slot_rollover_and_cross_slot_consumption(client, db_session):
    """
    TEST 5 & 6:
    Previous slot: LEFT = 60k, RIGHT = 30k -> 1 pair paid, LEFT CARRY = 1.
    Slot rollover: LEFT carry preserved as 1 CARRY (unpaid = 1).
    Next slot: RIGHT new volume = 30k -> consumes 1 pair -> remaining LEFT CARRY = 0.
    """
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_1.slot_id)
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_1.slot_id)
    db_session.commit()

    # Advance slot
    slot_2 = time_provider.next_slot(db_session, admin.id)

    login_res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    token = login_res.json()["data"]["token"]

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    carry_s2 = res.json()["data"]["carry"]

    # Slot 2 starts with 1 carry unit on Left, 0 on Right
    assert carry_s2["left"]["count"] == 1
    assert carry_s2["left"]["unpaid_count"] == 1
    assert carry_s2["left"]["paid_count"] == 1
    assert carry_s2["right"]["count"] == 0
    assert carry_s2["right"]["unpaid_count"] == 0
    assert carry_s2["right"]["paid_count"] == 1

    # In Slot 2, generate 30,000 volume on RIGHT
    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'RIGHT', 30000.0, slot_2.slot_id)
    db_session.commit()

    res2 = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    carry_s2_after = res2.json()["data"]["carry"]

    # Second pair completed: Left carry = 0, Right carry = 0; Paid count = 2
    assert carry_s2_after["left"]["count"] == 0
    assert carry_s2_after["left"]["unpaid_count"] == 0
    assert carry_s2_after["left"]["paid_count"] == 2

    assert carry_s2_after["right"]["count"] == 0
    assert carry_s2_after["right"]["unpaid_count"] == 0
    assert carry_s2_after["right"]["paid_count"] == 2

def test_carry_count_case_7_no_pair_preserves_unmatched_carry(client, db_session):
    """
    TEST 7: If no pair occurs during a slot (e.g. only Left gets 60k, Right gets 0),
    all unmatched carry remains on the same leg.
    """
    admin = db_session.query(User).filter(User.email == "admin@demo.com").first()
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_1 = time_provider.get_current_slot_info(db_session)

    pair_service.record_bv_and_evaluate_pairs(db_session, amol.id, 'LEFT', 60000.0, slot_1.slot_id)
    db_session.commit()

    time_provider.next_slot(db_session, admin.id)

    login_res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    token = login_res.json()["data"]["token"]

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    carry = res.json()["data"]["carry"]

    assert carry["left"]["count"] == 2
    assert carry["left"]["unpaid_count"] == 2
    assert carry["left"]["paid_count"] == 0

    assert carry["right"]["count"] == 0
    assert carry["right"]["unpaid_count"] == 0
    assert carry["right"]["paid_count"] == 0

def test_paid_and_unpaid_member_counts_in_dashboard(client, db_session):
    """
    TEST 8: Verify that when members register under Left/Right without purchase,
    unpaid_count is incremented properly.
    When a member activates (purchases package), paid_count is incremented and unpaid_count is decremented.
    """
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # Register an unpaid user on Left leg
    left_user = User(
        user_code="USR-TEST-L1",
        email="unpaid_left@test.com",
        mobile="9999900001",
        full_name="Unpaid Left User",
        password_hash="fakehash",
        role="USER",
        referral_code="UNPL01",
        sponsor_id=amol.id,
        binary_parent_id=amol.id,
        binary_position="LEFT",
        is_active=False
    )
    db_session.add(left_user)
    db_session.commit()

    login_res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    token = login_res.json()["data"]["token"]

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    carry = res.json()["data"]["carry"]

    # Left leg should show 1 unpaid member, 0 paid members, 0 carry
    assert carry["left"]["unpaid_count"] == 1
    assert carry["left"]["paid_count"] == 0
    assert carry["left"]["count"] == 0

    # Right leg should show 0 unpaid, 0 paid
    assert carry["right"]["unpaid_count"] == 0
    assert carry["right"]["paid_count"] == 0

    # Register an unpaid user on Right leg
    right_user = User(
        user_code="USR-TEST-R1",
        email="unpaid_right@test.com",
        mobile="9999900002",
        full_name="Unpaid Right User",
        password_hash="fakehash",
        role="USER",
        referral_code="UNPR01",
        sponsor_id=amol.id,
        binary_parent_id=amol.id,
        binary_position="RIGHT",
        is_active=False
    )
    db_session.add(right_user)
    db_session.commit()

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    carry = res.json()["data"]["carry"]

    assert carry["left"]["unpaid_count"] == 1
    assert carry["left"]["paid_count"] == 0
    assert carry["right"]["unpaid_count"] == 1
    assert carry["right"]["paid_count"] == 0

    # Now activate the Left user (they purchased a package)
    left_user.is_active = True
    db_session.commit()

    res = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    carry = res.json()["data"]["carry"]

    # Left: 1 paid, 0 unpaid
    assert carry["left"]["paid_count"] == 1
    assert carry["left"]["unpaid_count"] == 0
    # Right: 0 paid, 1 unpaid
    assert carry["right"]["paid_count"] == 0
    assert carry["right"]["unpaid_count"] == 1
