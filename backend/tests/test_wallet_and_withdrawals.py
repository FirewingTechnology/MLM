def test_wallet_and_withdrawal_flow(client):
    # 1. Login as Amol
    login_amol = client.post("/api/auth/login", json={
        "identifier": "amol@demo.com",
        "password": "Demo@123"
    })
    amol_token = login_amol.json()["data"]["token"]
    amol_headers = {"Authorization": f"Bearer {amol_token}"}

    # 1b. Admin gives demo funds
    login_admin = client.post("/api/auth/login", json={
        "identifier": "admin@demo.com",
        "password": "Admin@123"
    })
    admin_token = login_admin.json()["data"]["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    users = client.get("/api/admin/users", headers=admin_headers).json()["data"]["items"]
    amol_id = [u for u in users if u["email"] == "amol@demo.com"][0]["id"]
    client.post(f"/api/admin/users/{amol_id}/adjust-wallet", json={"amount": 10000.0, "reason": "Test funding"}, headers=admin_headers)

    # 2. Check wallet
    wal = client.get("/api/wallet", headers=amol_headers)
    assert wal.status_code == 200
    initial_balance = wal.json()["data"]["balance"]
    assert initial_balance >= 5000.0

    # 3. Request withdrawal of ₹5,000
    wdr = client.post("/api/withdrawals", json={
        "amount": 5000.0,
        "payout_method": "VIRTUAL_UPI",
        "payout_details": {"upi_id": "amol@okhdfcbank"}
    }, headers=amol_headers)
    assert wdr.status_code == 201
    wdr_id = wdr.json()["data"]["id"]
    assert wdr.json()["data"]["status"] == "PENDING"

    # 4. Admin logs in and approves withdrawal
    login_admin = client.post("/api/auth/login", json={
        "identifier": "admin@demo.com",
        "password": "Admin@123"
    })
    admin_token = login_admin.json()["data"]["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    appr = client.post(f"/api/admin/withdrawals/{wdr_id}/approve", json={"notes": "Approved in test"}, headers=admin_headers)
    assert appr.status_code == 200
    assert appr.json()["data"]["status"] == "APPROVED"

    # 5. Check Amol's debited balance
    wal_after = client.get("/api/wallet", headers=amol_headers)
    assert wal_after.json()["data"]["balance"] == initial_balance - 5000.0
    assert wal_after.json()["data"]["total_withdrawn"] == 5000.0
