"""
CORS Root-Cause Verification Script
===================================
Tests and proves the FastAPI CORS configuration and live HTTP / preflight headers.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient
from app.config import Settings
from app.main import get_cors_origins

def test_cors_verification():
    print("=" * 70)
    print("RUNNING CORS CONFIGURATION & HEADER PROOF")
    print("=" * 70)

    # 1. Test environment parsing with Elastic Beanstalk ALLOWED_ORIGINS
    eb_settings = Settings(
        APP_ENV="production",
        ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173,http://web.mystatusads333.com",
        SOCKET_CORS_ORIGINS="http://localhost:3000,http://localhost:5173,http://web.mystatusads333.com",
        SECRET_KEY="super-secret-key-for-test-purposes"
    )
    computed_origins = get_cors_origins(eb_settings)
    print("\n[1] Computed Allowed Origins for Production from Elastic Beanstalk:")
    for o in computed_origins:
        print(f"    - {o}")
    
    assert "http://web.mystatusads333.com" in computed_origins
    assert "https://web.mystatusads333.com" in computed_origins
    print("    [PASS] Production frontend origins successfully parsed!")

    # 2. Build isolated test app with identical middleware configuration
    test_app = FastAPI()
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=computed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,
    )

    @test_app.get("/api/time/current")
    def get_time_dummy():
        return {"status": "success", "mode": "REAL", "time": "2026-09-01T04:20:00"}

    client = TestClient(test_app)

    # 3. Test GET request from http://web.mystatusads333.com
    print("\n[2] Testing GET /api/time/current with Origin: http://web.mystatusads333.com")
    res = client.get("/api/time/current", headers={"Origin": "http://web.mystatusads333.com"})
    print(f"    Status Code: {res.status_code}")
    print(f"    Access-Control-Allow-Origin: {res.headers.get('access-control-allow-origin')}")
    print(f"    Access-Control-Allow-Credentials: {res.headers.get('access-control-allow-credentials')}")
    
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://web.mystatusads333.com"
    assert res.headers.get("access-control-allow-credentials") == "true"
    print("    [PASS] Direct GET request returned correct CORS headers!")

    # 4. Test OPTIONS preflight request for http://web.mystatusads333.com
    print("\n[3] Testing OPTIONS Preflight /api/time/current for Origin: http://web.mystatusads333.com")
    preflight = client.options(
        "/api/time/current",
        headers={
            "Origin": "http://web.mystatusads333.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        }
    )
    print(f"    Status Code: {preflight.status_code}")
    print(f"    Access-Control-Allow-Origin: {preflight.headers.get('access-control-allow-origin')}")
    print(f"    Access-Control-Allow-Credentials: {preflight.headers.get('access-control-allow-credentials')}")
    print(f"    Access-Control-Allow-Methods: {preflight.headers.get('access-control-allow-methods')}")
    print(f"    Access-Control-Allow-Headers: {preflight.headers.get('access-control-allow-headers')}")

    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "http://web.mystatusads333.com"
    assert preflight.headers.get("access-control-allow-credentials") == "true"
    assert "GET" in preflight.headers.get("access-control-allow-methods", "")
    assert "authorization" in preflight.headers.get("access-control-allow-headers", "").lower()
    print("    [PASS] OPTIONS Preflight request successfully returned all required CORS headers!")

    # 5. Test Unauthorized Origin Rejection (e.g. evil-site.com)
    print("\n[4] Testing Unauthorized Origin: http://evil-site.com")
    bad_res = client.get("/api/time/current", headers={"Origin": "http://evil-site.com"})
    print(f"    Status Code: {bad_res.status_code}")
    print(f"    Access-Control-Allow-Origin: {bad_res.headers.get('access-control-allow-origin')}")
    assert bad_res.headers.get("access-control-allow-origin") is None
    print("    [PASS] Unauthorized origin properly rejected with NO CORS headers!")

    print("\n" + "=" * 70)
    print("ALL CORS VERIFICATIONS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    test_cors_verification()
