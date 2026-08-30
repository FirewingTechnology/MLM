def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["framework"] == "FastAPI"
    assert data["status"] == "healthy"

def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "identifier": "amol@demo.com",
        "password": "Demo@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert data["data"]["user"]["email"] == "amol@demo.com"

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "identifier": "amol@demo.com",
        "password": "WrongPassword"
    })
    assert res.status_code == 401
    assert res.json()["success"] is False

def test_referral_lookup(client):
    res = client.get("/api/referral/AMOL001")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["sponsor_name"] == "Amol Sharma"

def test_register_new_member(client):
    res = client.post("/api/auth/register", json={
        "full_name": "Test Member",
        "email": "testmember@demo.com",
        "mobile": "9999900011",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["user"]["full_name"] == "Test Member"
    assert data["data"]["user"]["sponsor_name"] == "Amol Sharma"
    assert data["data"]["user"]["binary_position"] == "LEFT"
