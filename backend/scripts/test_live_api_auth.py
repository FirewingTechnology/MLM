"""
Live Backend API Verification Script
====================================
Tests authentication and core endpoints against the live AWS Elastic Beanstalk backend:
http://api.mystatusads333.com/api
"""

import urllib.request
import json

BASE_URL = "http://api.mystatusads333.com/api"

def make_request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}

def test_live_api():
    print("=" * 70)
    print(f"TESTING LIVE AWS BACKEND API: {BASE_URL}")
    print("=" * 70)

    # 1. Health Check
    status, res = make_request("/health")
    print(f"[1] GET /health -> Status {status}: {res}")

    # 2. Packages
    status, res = make_request("/packages")
    print(f"[2] GET /packages -> Status {status}: {res.get('message', '')} ({len(res.get('data', []))} packages)")

    # 3. Admin Login
    status, res = make_request("/auth/login", method="POST", data={
        "identifier": "admin@mynetwork.com",
        "password": "Admin@123"
    })
    print(f"[3] POST /auth/login (Admin) -> Status {status}")
    admin_token = None
    if status == 200 and res.get("success"):
        admin_token = res["data"]["token"]
        user_info = res["data"]["user"]
        print(f"    [SUCCESS] Logged in as Admin: {user_info['user_code']} ({user_info['role']})")
    else:
        print(f"    [NOTE] Admin login response: {res}")

    # 4. User Login
    status, res = make_request("/auth/login", method="POST", data={
        "identifier": "amol@mynetwork.com",
        "password": "Admin@123"
    })
    print(f"[4] POST /auth/login (User) -> Status {status}")
    user_token = None
    if status == 200 and res.get("success"):
        user_token = res["data"]["token"]
        user_info = res["data"]["user"]
        print(f"    [SUCCESS] Logged in as User: {user_info['user_code']} ({user_info['role']})")
    else:
        print(f"    [NOTE] User login response: {res}")

    # 5. User Dashboard
    if user_token:
        status, res = make_request("/dashboard", token=user_token)
        print(f"[5] GET /dashboard -> Status {status}: Balance=₹{res.get('data', {}).get('wallet', {}).get('balance', 0):,.2f}")

    # 6. Admin Dashboard
    if admin_token:
        status, res = make_request("/admin/dashboard", token=admin_token)
        print(f"[6] GET /admin/dashboard -> Status {status}: Total Users={res.get('data', {}).get('total_users', 0)}")

    print("=" * 70)

if __name__ == "__main__":
    test_live_api()
