def test_package_purchase_and_commissions(client):
    # 1. Register a new user under Sneha RIGHT sponsored by Amol
    reg = client.post("/api/auth/register", json={
        "full_name": "Karan Singhal",
        "email": "karan@demo.com",
        "mobile": "9999900022",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    assert reg.status_code == 201
    karan_token = reg.json()["data"]["token"]
    karan_headers = {"Authorization": f"Bearer {karan_token}"}

    # 2. Karan purchases the virtual package
    pur = client.post("/api/purchases", json={}, headers=karan_headers)
    assert pur.status_code == 201
    p_data = pur.json()
    assert p_data["success"] is True
    assert p_data["data"]["purchase"]["bv"] == 30000.0

    # 3. Check Amol's commissions (Amol gets direct 10% bonus = ₹3,000)
    login_amol = client.post("/api/auth/login", json={
        "identifier": "amol@demo.com",
        "password": "Demo@123"
    })
    amol_token = login_amol.json()["data"]["token"]
    amol_headers = {"Authorization": f"Bearer {amol_token}"}

    dash = client.get("/api/dashboard", headers=amol_headers)
    assert dash.status_code == 200
    kpis = dash.json()["data"]["kpis"]
    assert kpis["wallet_balance"] > 0
    assert kpis["total_earnings"] > 0

def test_purchase_idempotency(client):
    login = client.post("/api/auth/login", json={
        "identifier": "amol@demo.com",
        "password": "Demo@123"
    })
    token = login.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    idemp_key = "IDEMP-TEST-KEY-12345"
    p1 = client.post("/api/purchases", json={"idempotency_key": idemp_key}, headers=headers)
    assert p1.status_code == 201

    # Second identical call should not duplicate
    p2 = client.post("/api/purchases", json={"idempotency_key": idemp_key}, headers=headers)
    assert p2.status_code == 201
    assert p2.json()["data"]["events"][0]["type"] == "IDEMPOTENT_REPLAY"
