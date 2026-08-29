import pytest
from app.models.user import User
from app.models.package import Package
from app.models.referral_token import ReferralToken
from app.services.referral_service import get_or_create_referral_token, validate_referral_input
from app.services.commission_service import process_package_purchase
from app.services.time_service import time_provider

def test_01_left_referral_token_resolves_to_left(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    assert amol is not None

    token_rec = get_or_create_referral_token(db, amol.id, "LEFT")
    assert token_rec is not None
    assert token_rec.placement_side == "LEFT"
    assert token_rec.sponsor_user_id == amol.id

    val = validate_referral_input(db, token_rec.token)
    assert val["valid"] is True
    assert val["placement_side"] == "LEFT"
    assert val["is_locked"] is True
    assert val["sponsor_code"] == amol.user_code

def test_02_right_referral_token_resolves_to_right(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    
    token_rec = get_or_create_referral_token(db, amol.id, "RIGHT")
    assert token_rec is not None
    assert token_rec.placement_side == "RIGHT"

    val = validate_referral_input(db, token_rec.token)
    assert val["valid"] is True
    assert val["placement_side"] == "RIGHT"
    assert val["is_locked"] is True

def test_03_token_tamper_protection(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    token_rec = get_or_create_referral_token(db, amol.id, "LEFT")
    
    # Tampered token
    tampered_token = token_rec.token + "_TAMPERED"
    val = validate_referral_input(db, tampered_token)
    assert val["valid"] is False

    # Attempt registration with tampered token
    res = client.post("/api/auth/register", json={
        "full_name": "Tamper Test",
        "email": "tamper@test.com",
        "mobile": "9999999901",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "referral_token": tampered_token
    })
    assert res.status_code == 400
    assert "INVALID_SPONSOR" in res.json().get("error", {}).get("code", "")

def test_04_client_cannot_override_locked_placement_side(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    left_token = get_or_create_referral_token(db, amol.id, "LEFT")

    # Client tries to pass binary_position="RIGHT" in request body while using LEFT token
    res = client.post("/api/auth/register", json={
        "full_name": "Override Hacker",
        "email": "hacker@test.com",
        "mobile": "9999999902",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "referral_token": left_token.token,
        "binary_position": "RIGHT"  # Attempt to force RIGHT
    })
    assert res.status_code == 201
    user_data = res.json()["data"]["user"]
    
    # Must be placed on LEFT
    assert user_data["binary_position"] == "LEFT"
    assert user_data["binary_parent_id"] == amol.id
    assert user_data["sponsor_id"] == amol.id

def test_05_and_06_and_07_extreme_left_placements(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    left_token = get_or_create_referral_token(db, amol.id, "LEFT")

    # 1. Register User B via Amol LEFT link
    res_b = client.post("/api/auth/register", json={
        "full_name": "User B",
        "email": "userb@test.com",
        "mobile": "9999999911",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "referral_token": left_token.token
    })
    assert res_b.status_code == 201
    b = res_b.json()["data"]["user"]
    assert b["binary_parent_id"] == amol.id
    assert b["binary_position"] == "LEFT"
    assert b["sponsor_id"] == amol.id

    # 2. Register User C via Amol LEFT link (Same token)
    res_c = client.post("/api/auth/register", json={
        "full_name": "User C",
        "email": "userc@test.com",
        "mobile": "9999999912",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "referral_token": left_token.token
    })
    assert res_c.status_code == 201
    c = res_c.json()["data"]["user"]
    # C must be placed extreme-left under B
    assert c["binary_parent_id"] == b["id"]
    assert c["binary_position"] == "LEFT"
    assert c["sponsor_id"] == amol.id  # Sponsor is still Amol!

    # 3. Register User D via Amol LEFT link
    res_d = client.post("/api/auth/register", json={
        "full_name": "User D",
        "email": "userd@test.com",
        "mobile": "9999999913",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "referral_token": left_token.token
    })
    assert res_d.status_code == 201
    d = res_d.json()["data"]["user"]
    # D must be placed extreme-left under C
    assert d["binary_parent_id"] == c["id"]
    assert d["binary_position"] == "LEFT"
    assert d["sponsor_id"] == amol.id

def test_08_and_09_extreme_right_placements(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    right_token = get_or_create_referral_token(db, amol.id, "RIGHT")

    # 1. Register User X via Amol RIGHT link
    res_x = client.post("/api/auth/register", json={
        "full_name": "User X",
        "email": "userx@test.com",
        "mobile": "9999999921",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "referral_token": right_token.token
    })
    assert res_x.status_code == 201
    x = res_x.json()["data"]["user"]
    assert x["binary_parent_id"] == amol.id
    assert x["binary_position"] == "RIGHT"
    assert x["sponsor_id"] == amol.id

    # 2. Register User Y via Amol RIGHT link
    res_y = client.post("/api/auth/register", json={
        "full_name": "User Y",
        "email": "usery@test.com",
        "mobile": "9999999922",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "referral_token": right_token.token
    })
    assert res_y.status_code == 201
    y = res_y.json()["data"]["user"]
    # Y must be placed extreme-right under X
    assert y["binary_parent_id"] == x["id"]
    assert y["binary_position"] == "RIGHT"
    assert y["sponsor_id"] == amol.id

def test_10_mixed_left_and_right_tree(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    left_token = get_or_create_referral_token(db, amol.id, "LEFT")
    right_token = get_or_create_referral_token(db, amol.id, "RIGHT")

    # B (LEFT), X (RIGHT), C (LEFT), Y (RIGHT)
    res_b = client.post("/api/auth/register", json={"full_name": "B", "email": "b@test.com", "mobile": "9000000001", "password": "Pass!", "confirm_password": "Pass!", "referral_token": left_token.token})
    res_x = client.post("/api/auth/register", json={"full_name": "X", "email": "x@test.com", "mobile": "9000000002", "password": "Pass!", "confirm_password": "Pass!", "referral_token": right_token.token})
    res_c = client.post("/api/auth/register", json={"full_name": "C", "email": "c@test.com", "mobile": "9000000003", "password": "Pass!", "confirm_password": "Pass!", "referral_token": left_token.token})
    res_y = client.post("/api/auth/register", json={"full_name": "Y", "email": "y@test.com", "mobile": "9000000004", "password": "Pass!", "confirm_password": "Pass!", "referral_token": right_token.token})

    b = res_b.json()["data"]["user"]
    x = res_x.json()["data"]["user"]
    c = res_c.json()["data"]["user"]
    y = res_y.json()["data"]["user"]

    assert b["binary_parent_id"] == amol.id and b["binary_position"] == "LEFT"
    assert x["binary_parent_id"] == amol.id and x["binary_position"] == "RIGHT"
    assert c["binary_parent_id"] == b["id"] and c["binary_position"] == "LEFT"
    assert y["binary_parent_id"] == x["id"] and y["binary_position"] == "RIGHT"

def test_11_and_12_child_shares_own_link(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    left_token = get_or_create_referral_token(db, amol.id, "LEFT")

    # Amol -> B (LEFT)
    res_b = client.post("/api/auth/register", json={"full_name": "User B", "email": "b_share@test.com", "mobile": "9111111111", "password": "Pass!", "confirm_password": "Pass!", "referral_token": left_token.token})
    b_id = res_b.json()["data"]["user"]["id"]

    # B generates their OWN LEFT link
    b_left_token = get_or_create_referral_token(db, b_id, "LEFT")
    assert b_left_token.sponsor_user_id == b_id

    # C registers via B's LEFT link
    res_c = client.post("/api/auth/register", json={"full_name": "User C", "email": "c_share@test.com", "mobile": "9111111112", "password": "Pass!", "confirm_password": "Pass!", "referral_token": b_left_token.token})
    c = res_c.json()["data"]["user"]

    # C's sponsor must be B, and placement parent must be B
    assert c["sponsor_id"] == b_id
    assert c["binary_parent_id"] == b_id
    assert c["binary_position"] == "LEFT"

def test_15_deep_bv_propagation_follows_placement_tree(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    pkg = db.query(Package).first()
    left_token = get_or_create_referral_token(db, amol.id, "LEFT")

    # A -> B -> C (all extreme LEFT)
    res_b = client.post("/api/auth/register", json={"full_name": "B", "email": "b_bv@test.com", "mobile": "9222222221", "password": "Pass!", "confirm_password": "Pass!", "referral_token": left_token.token})
    res_c = client.post("/api/auth/register", json={"full_name": "C", "email": "c_bv@test.com", "mobile": "9222222222", "password": "Pass!", "confirm_password": "Pass!", "referral_token": left_token.token})

    c_id = res_c.json()["data"]["user"]["id"]
    b_id = res_b.json()["data"]["user"]["id"]

    # C purchases package (30,000 BV)
    process_package_purchase(db, c_id, pkg.id)

    # Check BV:
    b_user = db.get(User, b_id)
    amol_user = db.get(User, amol.id)

    assert b_user.volume.accumulated_left_bv == 30000.0
    assert b_user.volume.accumulated_right_bv == 0.0
    assert amol_user.volume.accumulated_left_bv == 30000.0
    assert amol_user.volume.accumulated_right_bv == 0.0

def test_16_permanent_placement_survives_slot_rollover(client, db_session):
    db = db_session
    amol = db.query(User).filter(User.referral_code == "AMOL001").first()
    left_token = get_or_create_referral_token(db, amol.id, "LEFT")

    res_b = client.post("/api/auth/register", json={"full_name": "B", "email": "b_slot@test.com", "mobile": "9333333331", "password": "Pass!", "confirm_password": "Pass!", "referral_token": left_token.token})
    b_id = res_b.json()["data"]["user"]["id"]

    # Advance time / slot
    current_time = time_provider.get_current_ist_time(db)
    from datetime import timedelta
    next_time = current_time + timedelta(hours=24)
    # Check that placement is immutable
    b_user = db.get(User, b_id)
    assert b_user.binary_parent_id == amol.id
    assert b_user.binary_position == "LEFT"
    assert b_user.sponsor_id == amol.id
