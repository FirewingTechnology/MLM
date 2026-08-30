def test_admin_dashboard_and_reset(client):
    # 1. Admin login
    login_admin = client.post("/api/auth/login", json={
        "identifier": "admin@demo.com",
        "password": "Admin@123"
    })
    admin_token = login_admin.json()["data"]["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Get admin dashboard
    dash = client.get("/api/admin/dashboard", headers=admin_headers)
    assert dash.status_code == 200
    kpis = dash.json()["data"]["kpis"]
    assert kpis["total_users"] >= 2
    assert kpis["active_users"] >= 2

    # 3. Manual wallet adjustment
    users = client.get("/api/admin/users", headers=admin_headers).json()["data"]["items"]
    target_user = [u for u in users if u["email"] == "amol@demo.com"][0]
    
    adj = client.post(f"/api/admin/users/{target_user['id']}/adjust-wallet", json={
        "amount": 1500.0,
        "reason": "Test bonus from admin"
    }, headers=admin_headers)
    assert adj.status_code == 200

    # 4. Reset Demo Environment
    rst = client.post("/api/admin/demo/reset", json={}, headers=admin_headers)
    assert rst.status_code == 200
    assert "reset" in rst.json()["message"].lower()

    # 5. Verify clean seed state after reset
    login_after = client.post("/api/auth/login", json={
        "identifier": "ADMIN001",
        "password": "Admin@123"
    })
    assert login_after.status_code == 200
    token_after = login_after.json()["data"]["token"]
    headers_after = {"Authorization": f"Bearer {token_after}"}

    dash_after = client.get("/api/admin/dashboard", headers=headers_after)
    assert dash_after.status_code == 200
    assert dash_after.json()["data"]["kpis"]["total_users"] >= 1
