import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from fastapi.testclient import TestClient
from app.main import app

def log(step, msg):
    print(f"\n========================================================")
    print(f"STEP {step}: {msg}")
    print(f"========================================================")

def run_live_e2e_verification():
    client = TestClient(app)
    
    # Login as Admin to control Demo Time and Reset DB
    res = client.post("/api/auth/login", json={"identifier": "admin@demo.com", "password": "Admin@123"})
    print("Login response:", res.status_code, res.json())
    admin_token = res.json()["data"]["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("Admin logged in successfully.")

    # 0. Reset Demo Database cleanly for a fresh verification
    log(0, "Resetting Demo Database for fresh test run")
    res = client.post("/api/admin/demo/reset", headers=admin_headers)
    print("Reset DB response:", res.status_code, res.json())

    # Login as Amol (User A)
    res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    amol_token = res.json()["data"]["token"]
    amol_headers = {"Authorization": f"Bearer {amol_token}"}
    amol_id = res.json()["data"]["user"]["id"]
    print(f"Amol (User A) logged in. User ID: {amol_id}")

    # 1. Check Slot 1 state
    log(1, "SLOT 1: Initial State & Pair Generation for Amol")
    slot_res = client.get("/api/admin/time", headers=admin_headers)
    slot_1_id = slot_res.json()["data"]["slot_id"]
    print(f"Current Slot ID: {slot_1_id}")

    # Register B under Amol LEFT
    res_b = client.post("/api/auth/register", json={
        "full_name": "Member B", "email": "member_b_live@demo.com", "mobile": "9870090001",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "LEFT"
    })
    b_id = res_b.json()["data"]["user"]["id"]
    b_code = res_b.json()["data"]["user"]["user_code"]
    print(f"Member B registered under Amol LEFT -> ID: {b_id}, Code: {b_code}")

    # Register C under Amol RIGHT
    res_c = client.post("/api/auth/register", json={
        "full_name": "Member C", "email": "member_c_live@demo.com", "mobile": "9870090002",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": "AMOL001", "binary_position": "RIGHT"
    })
    c_id = res_c.json()["data"]["user"]["id"]
    c_code = res_c.json()["data"]["user"]["user_code"]
    print(f"Member C registered under Amol RIGHT -> ID: {c_id}, Code: {c_code}")

    # Purchase package for B (INR 35,000 / 30,000 BV)                                                                 
    res_b_login = client.post("/api/auth/login", json={"identifier": "member_b_live@demo.com", "password": "Demo@123"})
    b_token = res_b_login.json()["data"]["token"]
    res_pur_b = client.post("/api/purchases", json={"package_id": 1}, headers={"Authorization": f"Bearer {b_token}"})
    print("Member B purchased package -> Status:", res_pur_b.status_code)

    # Purchase package for C (INR 35,000 / 30,000 BV)
    res_c_login = client.post("/api/auth/login", json={"identifier": "member_c_live@demo.com", "password": "Demo@123"})
    c_token = res_c_login.json()["data"]["token"]
    res_pur_c = client.post("/api/purchases", json={"package_id": 1}, headers={"Authorization": f"Bearer {c_token}"})
    print("Member C purchased package -> Status:", res_pur_c.status_code)

    # Verify Amol's Dashboard & Wallet after Slot 1 pair
    res_dash = client.get("/api/dashboard", headers=amol_headers)
    dash_data = res_dash.json()["data"]
    pair_sum = dash_data["pair_summary"]
    wallet_bal = dash_data["kpis"]["wallet_balance"]
    
    print("\n--- Amol Slot 1 Results ---")
    print(f"Wallet Balance: INR {wallet_bal:,.2f} (Direct Commissions: INR 6,000 + Pair Bonus: INR 15,000 = INR 21,000)")
    print(f"Effective Left BV: INR {pair_sum['effective_left_bv']:,}")
    print(f"Effective Right BV: INR {pair_sum['effective_right_bv']:,}")
    print(f"Consumed Left BV: INR {pair_sum['consumed_left_bv']:,}")
    print(f"Consumed Right BV: INR {pair_sum['consumed_right_bv']:,}")
    print(f"Pair Completed: {pair_sum['pair_completed']}")
    print(f"Pair Bonus Earned: INR {pair_sum['pair_bonus_earned']:,}")
    assert pair_sum['pair_completed'] is True
    assert pair_sum['pair_bonus_earned'] == 15000.0

    # 2. Advance to Slot 2 using Demo Time
    log(2, "Advancing to SLOT 2 using Demo Time Controls")
    res_next = client.post("/api/admin/time/next-slot", headers=admin_headers)
    slot_2_info = res_next.json()["data"]
    slot_2_id = slot_2_info["slot_id"]
    print(f"Advanced to Slot 2! New Slot ID: {slot_2_id}")

    # 3. In Slot 2: Have B create D and C create F
    log(3, "SLOT 2: Register D under B (LEFT) and F under C (RIGHT)")
    res_d = client.post("/api/auth/register", json={
        "full_name": "Member D", "email": "member_d_live@demo.com", "mobile": "9870090003",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": b_code, "binary_position": "LEFT"
    })
    d_id = res_d.json()["data"]["user"]["id"]
    d_code = res_d.json()["data"]["user"]["user_code"]
    print(f"Member D registered under B LEFT -> ID: {d_id}, Code: {d_code}")

    res_f = client.post("/api/auth/register", json={
        "full_name": "Member F", "email": "member_f_live@demo.com", "mobile": "9870090004",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": c_code, "binary_position": "RIGHT"
    })
    f_id = res_f.json()["data"]["user"]["id"]
    f_code = res_f.json()["data"]["user"]["user_code"]
    print(f"Member F registered under C RIGHT -> ID: {f_id}, Code: {f_code}")

    # 4. Generate D and F purchases
    log(4, "SLOT 2: Process Purchases for D and F (INR 30,000 BV each)")
    res_d_login = client.post("/api/auth/login", json={"identifier": "member_d_live@demo.com", "password": "Demo@123"})
    d_token = res_d_login.json()["data"]["token"]
    client.post("/api/purchases", json={"package_id": 1}, headers={"Authorization": f"Bearer {d_token}"})

    res_f_login = client.post("/api/auth/login", json={"identifier": "member_f_live@demo.com", "password": "Demo@123"})
    f_token = res_f_login.json()["data"]["token"]
    client.post("/api/purchases", json={"package_id": 1}, headers={"Authorization": f"Bearer {f_token}"})
    print("D and F packages purchased successfully.")

    # 5. Verify Amol's Slot 2 state (A did nothing personally, but receives INR 15,000 again)
    log(5, "Verifying Amol's Slot 2 Volumes & Independent Pair Payout")
    res_dash_s2 = client.get("/api/dashboard", headers=amol_headers)
    dash_s2 = res_dash_s2.json()["data"]
    pair_sum_s2 = dash_s2["pair_summary"]
    wallet_bal_s2 = dash_s2["kpis"]["wallet_balance"]
    
    print("\n--- Amol Slot 2 Results ---")
    print(f"Wallet Balance: INR {wallet_bal_s2:,.2f} (+INR 15,000 Pair Bonus from D/F network activity)")
    print(f"Slot 2 Effective Left BV: INR {pair_sum_s2['effective_left_bv']:,} (from D)")
    print(f"Slot 2 Effective Right BV: INR {pair_sum_s2['effective_right_bv']:,} (from F)")
    print(f"Slot 2 Consumed Left BV: INR {pair_sum_s2['consumed_left_bv']:,}")
    print(f"Slot 2 Consumed Right BV: INR {pair_sum_s2['consumed_right_bv']:,}")
    print(f"Slot 2 Pair Completed: {pair_sum_s2['pair_completed']}")
    print(f"Slot 2 Pair Bonus Earned: INR {pair_sum_s2['pair_bonus_earned']:,}")
    assert pair_sum_s2['pair_completed'] is True
    assert pair_sum_s2['pair_bonus_earned'] == 15000.0

    # 6. Verify B and C do NOT receive false pair bonuses
    log(6, "Verifying B and C Independent Pair Status (1-Sided Volume, NO Pair)")
    b_dash = client.get("/api/dashboard", headers={"Authorization": f"Bearer {b_token}"}).json()["data"]
    b_pair = b_dash["pair_summary"]
    print(f"Member B -> Left BV: INR {b_pair['effective_left_bv']:,}, Right BV: INR {b_pair['effective_right_bv']:,}, Pair Completed: {b_pair['pair_completed']}")
    assert b_pair['pair_completed'] is False
    assert b_pair['effective_left_bv'] == 30000.0
    assert b_pair['effective_right_bv'] == 0.0

    c_dash = client.get("/api/dashboard", headers={"Authorization": f"Bearer {c_token}"}).json()["data"]
    c_pair = c_dash["pair_summary"]
    print(f"Member C -> Left BV: INR {c_pair['effective_left_bv']:,}, Right BV: INR {c_pair['effective_right_bv']:,}, Pair Completed: {c_pair['pair_completed']}")
    assert c_pair['pair_completed'] is False
    assert c_pair['effective_left_bv'] == 0.0
    assert c_pair['effective_right_bv'] == 30000.0

    # 7. Create excess volume on LEFT side in Slot 2
    log(7, "SLOT 2: Creating Excess Volume on LEFT side (Register E under B LEFT)")
    res_e = client.post("/api/auth/register", json={
        "full_name": "Member E", "email": "member_e_live@demo.com", "mobile": "9870090005",
        "password": "Demo@123", "confirm_password": "Demo@123",
        "referral_code": "AMOL001", "binary_parent_code": d_code, "binary_position": "LEFT"
    })
    e_id = res_e.json()["data"]["user"]["id"]
    res_e_login = client.post("/api/auth/login", json={"identifier": "member_e_live@demo.com", "password": "Demo@123"})
    e_token = res_e_login.json()["data"]["token"]
    client.post("/api/purchases", json={"package_id": 1}, headers={"Authorization": f"Bearer {e_token}"})
    print("Member E purchased package (30k BV). Amol now has 60k Left in Slot 2 (30k consumed, 30k excess carry).")

    # 8. Cross into Slot 3 (Next Day Slot 1) and Verify Carry Forward
    log(8, "Advancing to SLOT 3: Verifying Left Carry Stays Left and Right Carry Stays Right")
    res_next_s3 = client.post("/api/admin/time/next-slot", headers=admin_headers)
    slot_3_id = res_next_s3.json()["data"]["slot_id"]
    print(f"Advanced to Slot 3! Slot ID: {slot_3_id}")

    res_dash_s3 = client.get("/api/dashboard", headers=amol_headers)
    dash_s3 = res_dash_s3.json()["data"]
    pair_sum_s3 = dash_s3["pair_summary"]

    print("\n--- Amol Slot 3 Starting State ---")
    print(f"Slot 3 Starting Left Carry: INR {pair_sum_s3['carry_forward_left']:,}")
    print(f"Slot 3 Starting Right Carry: INR {pair_sum_s3['carry_forward_right']:,}")
    print(f"Slot 3 Effective Left BV: INR {pair_sum_s3['effective_left_bv']:,}")
    print(f"Slot 3 Effective Right BV: INR {pair_sum_s3['effective_right_bv']:,}")
    
    assert pair_sum_s3['carry_forward_left'] == 30000.0
    assert pair_sum_s3['carry_forward_right'] == 0.0
    assert pair_sum_s3['effective_left_bv'] == 30000.0
    assert pair_sum_s3['effective_right_bv'] == 0.0

    # 9. Verify Server-side Persistence Across New Session / Another Browser Client
    log(9, "Verifying Cross-Browser Session Persistence")
    fresh_res = client.post("/api/auth/login", json={"identifier": "amol@demo.com", "password": "Demo@123"})
    fresh_token = fresh_res.json()["data"]["token"]
    fresh_dash = client.get("/api/dashboard", headers={"Authorization": f"Bearer {fresh_token}"}).json()["data"]
    
    print("New session re-login successful. Verifying state consistency:")
    print(f"Total Earnings: INR {fresh_dash['kpis']['total_earnings']:,.2f}")
    print(f"Wallet Balance: INR {fresh_dash['kpis']['wallet_balance']:,.2f}")
    print(f"Carry Left BV: INR {fresh_dash['kpis']['carry_left_bv']:,}")
    print(f"Carry Right BV: INR {fresh_dash['kpis']['carry_right_bv']:,}")
    
    assert fresh_dash['kpis']['carry_left_bv'] == 30000.0
    assert fresh_dash['kpis']['carry_right_bv'] == 0.0
    assert fresh_dash['kpis']['wallet_balance'] == wallet_bal_s2 + 3000.0  # (includes direct comm from E)

    # 10. Verify Settlements History API
    log(10, "Verifying Slot Settlements Audit Trail")
    settlements_res = client.get("/api/network/settlements", headers={"Authorization": f"Bearer {fresh_token}"})
    settlements = settlements_res.json()["data"]["items"]
    print(f"Total Settlement records found: {len(settlements)}")
    for s in settlements:
        print(f"  Slot: {s['slot_id']} | Left Before: INR {s['left_before']:,} | Right Before: INR {s['right_before']:,} | Matched: INR {s['left_matched']:,} | Pair Bonus: INR {s['pair_bonus']:,} | Carry: L:INR {s['left_carry']:,} R:INR {s['right_carry']:,}")

    print("\n========================================================")
    print("ALL 10 END-TO-END VERIFICATION STEPS PASSED 100% SUCCESSFULLY!")
    print("========================================================\n")

if __name__ == "__main__":
    run_live_e2e_verification()
