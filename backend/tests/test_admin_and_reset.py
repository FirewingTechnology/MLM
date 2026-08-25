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
    assert kpis["total_users"] >= 8
    assert kpis["active_users"] >= 7

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
    dash_after = client.get("/api/admin/dashboard", headers=admin_headers)
    assert dash_after.status_code == 200
    assert dash_after.json()["data"]["kpis"]["total_users"] == 8
