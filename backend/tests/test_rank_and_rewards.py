import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.package import Package
from app.models.rank_config import RankConfig
from app.models.rank_achievement import RankAchievement
from app.models.wallet import Wallet, WalletTransaction
from app.services.commission_service import process_package_purchase
from app.services.rank_service import (
    evaluate_user_rank_progress,
    get_user_rank_overview,
    update_rank_config,
    get_admin_rank_achievements,
    update_achievement_fulfillment
)
from app.security import hash_password, create_access_token

def test_star_qualification_success(db_session):
    """
    Test: User A refers 2 direct members within 7 days -> Qualifies for STAR -> ₹2,100 credited once.
    """
    # 1. Create and activate User A
    user_a = User(
        user_code="USR-A001",
        email="usera@test.com",
        mobile="9800000001",
        full_name="User Alpha",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="ALPHA01",
        is_active=True,
        created_at=datetime.utcnow() - timedelta(days=6)
    )
    db_session.add(user_a)
    db_session.flush()
    process_package_purchase(db_session, user_a.id)
    
    # 2. User A refers Direct B on Day 2
    user_b = User(
        user_code="USR-B001",
        email="userb@test.com",
        mobile="9800000002",
        full_name="User Bravo",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="BRAVO01",
        sponsor_id=user_a.id,
        is_active=True,
        created_at=datetime.utcnow() - timedelta(days=4)
    )
    db_session.add(user_b)
    db_session.flush()
    process_package_purchase(db_session, user_b.id)
    
    # Check intermediate state: 1 direct only
    overview = get_user_rank_overview(db_session, user_a.id)
    star_tier = next(t for t in overview['tiers'] if t['rank_name'] == 'STAR')
    assert star_tier['status'] == 'IN_PROGRESS'
    assert star_tier['current_count'] == 1
    
    # 3. User A refers Direct C on Day 5
    user_c = User(
        user_code="USR-C001",
        email="userc@test.com",
        mobile="9800000003",
        full_name="User Charlie",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="CHARLIE01",
        sponsor_id=user_a.id,
        is_active=True,
        created_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(user_c)
    db_session.flush()
    process_package_purchase(db_session, user_c.id)
    
    # Refresh User A
    db_session.refresh(user_a)
    assert user_a.current_rank == 'STAR'
    
    # Verify Achievement record
    star_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user_a.id,
        RankAchievement.rank_name == 'STAR'
    ).first()
    assert star_ach is not None
    assert star_ach.status == 'ACHIEVED'
    assert star_ach.reward_amount == 2100.0
    assert star_ach.reward_status == 'CREDITED'
    assert star_ach.reward_transaction_id is not None
    
    # Verify Wallet Ledger entry
    txn = db_session.get(WalletTransaction, star_ach.reward_transaction_id)
    assert txn.transaction_type == 'CREDIT'
    assert txn.amount == 2100.0
    assert txn.category == 'RANK_REWARD'
    
    # Idempotency test: repeated evaluation should NOT double-credit
    events = evaluate_user_rank_progress(db_session, user_a.id)
    assert len(events) == 0
    rank_txns = db_session.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_a.id,
        WalletTransaction.category == 'RANK_REWARD'
    ).all()
    assert len(rank_txns) == 1

def test_star_qualification_expired_after_7_days(db_session):
    """
    Test: User A refers 1 direct within 7 days and 2nd direct after 7 days -> Not qualified / Expired.
    """
    start_time = datetime.utcnow() - timedelta(days=10)
    user_a = User(
        user_code="USR-EXP1",
        email="userexp@test.com",
        mobile="9800000099",
        full_name="User Expired",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="EXP01",
        is_active=True,
        created_at=start_time
    )
    db_session.add(user_a)
    db_session.flush()
    process_package_purchase(db_session, user_a.id)
    
    # Direct 1 within 7 days
    user_b = User(
        user_code="USR-D1",
        email="d1@test.com",
        mobile="9800000091",
        full_name="Direct 1",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="D101",
        sponsor_id=user_a.id,
        is_active=True,
        created_at=start_time + timedelta(days=2)
    )
    db_session.add(user_b)
    db_session.flush()
    process_package_purchase(db_session, user_b.id)
    
    # Direct 2 after 7 days (e.g. Day 9)
    user_c = User(
        user_code="USR-D2",
        email="d2@test.com",
        mobile="9800000092",
        full_name="Direct 2",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="D201",
        sponsor_id=user_a.id,
        is_active=True,
        created_at=start_time + timedelta(days=9)
    )
    db_session.add(user_c)
    db_session.flush()
    process_package_purchase(db_session, user_c.id)
    
    evaluate_user_rank_progress(db_session, user_a.id)
    db_session.refresh(user_a)
    
    star_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user_a.id,
        RankAchievement.rank_name == 'STAR'
    ).first()
    assert star_ach.status == 'EXPIRED'
    assert user_a.current_rank == 'DISTRIBUTOR'
    
    # Zero rank reward credited
    rank_txns = db_session.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_a.id,
        WalletTransaction.category == 'RANK_REWARD'
    ).all()
    assert len(rank_txns) == 0

def test_super_star_qualification(db_session):
    """
    Test: User A (STAR) has 2 direct members (B and C) who both become STAR within qualification window ->
    User A promoted to SUPER_STAR -> ₹5,100 credited.
    """
    now = datetime.utcnow()
    # 1. User A
    user_a = User(
        user_code="USR-SS-A",
        email="ssa@test.com",
        mobile="9810000001",
        full_name="SuperStar Alpha",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="SSA01",
        is_active=True,
        created_at=now - timedelta(days=5)
    )
    db_session.add(user_a)
    db_session.flush()
    process_package_purchase(db_session, user_a.id)
    
    # 2. Directs B and C for User A
    user_b = User(
        user_code="USR-SS-B",
        email="ssb@test.com",
        mobile="9810000002",
        full_name="Direct B",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="SSB01",
        sponsor_id=user_a.id,
        is_active=True,
        created_at=now - timedelta(days=4)
    )
    user_c = User(
        user_code="USR-SS-C",
        email="ssc@test.com",
        mobile="9810000003",
        full_name="Direct C",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="SSC01",
        sponsor_id=user_a.id,
        is_active=True,
        created_at=now - timedelta(days=3)
    )
    db_session.add_all([user_b, user_c])
    db_session.flush()
    process_package_purchase(db_session, user_b.id)
    process_package_purchase(db_session, user_c.id)
    
    # User A is now STAR
    db_session.refresh(user_a)
    assert user_a.current_rank == 'STAR'
    
    # 3. User B refers B1, B2 -> B becomes STAR
    b1 = User(user_code="USR-B1", email="b1@test.com", mobile="9810000011", full_name="B1", password_hash=hash_password("Pass@123"), role="USER", referral_code="B101", sponsor_id=user_b.id, is_active=True, created_at=now - timedelta(days=2))
    b2 = User(user_code="USR-B2", email="b2@test.com", mobile="9810000012", full_name="B2", password_hash=hash_password("Pass@123"), role="USER", referral_code="B201", sponsor_id=user_b.id, is_active=True, created_at=now - timedelta(days=2))
    db_session.add_all([b1, b2])
    db_session.flush()
    process_package_purchase(db_session, b1.id)
    process_package_purchase(db_session, b2.id)
    
    db_session.refresh(user_b)
    assert user_b.current_rank == 'STAR'
    
    # 4. User C refers C1, C2 -> C becomes STAR
    c1 = User(user_code="USR-C1", email="c1@test.com", mobile="9810000021", full_name="C1", password_hash=hash_password("Pass@123"), role="USER", referral_code="C101", sponsor_id=user_c.id, is_active=True, created_at=now - timedelta(days=1))
    c2 = User(user_code="USR-C2", email="c2@test.com", mobile="9810000022", full_name="C2", password_hash=hash_password("Pass@123"), role="USER", referral_code="C201", sponsor_id=user_c.id, is_active=True, created_at=now - timedelta(days=1))
    db_session.add_all([c1, c2])
    db_session.flush()
    process_package_purchase(db_session, c1.id)
    process_package_purchase(db_session, c2.id)
    
    db_session.refresh(user_c)
    assert user_c.current_rank == 'STAR'
    
    # 5. User A should automatically promote to SUPER_STAR
    db_session.refresh(user_a)
    assert user_a.current_rank == 'SUPER_STAR'
    
    super_star_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user_a.id,
        RankAchievement.rank_name == 'SUPER_STAR'
    ).first()
    assert super_star_ach is not None
    assert super_star_ach.status == 'ACHIEVED'
    assert super_star_ach.reward_amount == 5100.0
    assert super_star_ach.reward_status == 'CREDITED'

def test_vip_cash_and_ev_scooter_rewards(db_session):
    """
    Test VIP promotion with configurable CASH (₹51,000) or EV_SCOOTER non-cash fulfillment.
    """
    now = datetime.utcnow()
    # User A as SUPER_STAR
    user_a = User(user_code="USR-VIP-A", email="vipa@test.com", mobile="9820000001", full_name="VIP Alpha", password_hash=hash_password("Pass@123"), role="USER", referral_code="VIPA01", is_active=True, current_rank="SUPER_STAR", created_at=now - timedelta(days=10))
    db_session.add(user_a)
    db_session.flush()

    user_b = User(user_code="USR-VIP-B", email="vipb@test.com", mobile="9820000002", full_name="VIP Direct B", password_hash=hash_password("Pass@123"), role="USER", referral_code="VIPB01", sponsor_id=user_a.id, is_active=True, current_rank="SUPER_STAR", created_at=now - timedelta(days=8))
    user_c = User(user_code="USR-VIP-C", email="vipc@test.com", mobile="9820000003", full_name="VIP Direct C", password_hash=hash_password("Pass@123"), role="USER", referral_code="VIPC01", sponsor_id=user_a.id, is_active=True, current_rank="SUPER_STAR", created_at=now - timedelta(days=8))
    db_session.add_all([user_b, user_c])
    db_session.flush()
    
    # Create achievements for B and C
    ach_b = RankAchievement(user_id=user_b.id, rank_name="SUPER_STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=6), qualification_deadline=now + timedelta(days=1), achieved_at=now - timedelta(days=2), reward_type="CASH", reward_amount=5100.0, reward_status="CREDITED")
    ach_c = RankAchievement(user_id=user_c.id, rank_name="SUPER_STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=6), qualification_deadline=now + timedelta(days=1), achieved_at=now - timedelta(days=2), reward_type="CASH", reward_amount=5100.0, reward_status="CREDITED")
    ach_a_ss = RankAchievement(user_id=user_a.id, rank_name="SUPER_STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=8), qualification_deadline=now - timedelta(days=1), achieved_at=now - timedelta(days=3), reward_type="CASH", reward_amount=5100.0, reward_status="CREDITED")
    
    db_session.add_all([ach_b, ach_c, ach_a_ss])
    db_session.flush()
    
    # Case 1: VIP configured as CASH
    evaluate_user_rank_progress(db_session, user_a.id)
    db_session.refresh(user_a)
    assert user_a.current_rank == 'VIP'
    
    vip_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user_a.id,
        RankAchievement.rank_name == 'VIP'
    ).first()
    assert vip_ach.status == 'ACHIEVED'
    assert vip_ach.reward_type == 'CASH'
    assert vip_ach.reward_amount == 51000.0
    assert vip_ach.reward_status == 'CREDITED'
    
    # Case 2: Test Admin EV Scooter fulfillment flow
    update_rank_config(db_session, rank_name='VIP', reward_type='EV_SCOOTER')
    vip_cfg = db_session.query(RankConfig).filter(RankConfig.rank_name == 'VIP').first()
    assert vip_cfg.reward_type == 'EV_SCOOTER'
    
    # Test Fulfillment status update
    updated_ach = update_achievement_fulfillment(
        db=db_session,
        achievement_id=vip_ach.id,
        reward_status='FULFILLED',
        admin_notes='EV Scooter dispatched via logistics partner'
    )
    assert updated_ach.reward_status == 'FULFILLED'
    assert updated_ach.admin_notes == 'EV Scooter dispatched via logistics partner'

def test_rank_reward_api_endpoints(client, db_session):
    """
    Test User and Admin Rank & Reward API Endpoints.
    """
    user = db_session.query(User).filter(User.role == "USER").first()
    admin = db_session.query(User).filter(User.role == "ADMIN").first()
    
    user_token = create_access_token(user.id, "USER")
    admin_token = create_access_token(admin.id, "ADMIN")
    
    # 1. User Overview Endpoint
    res = client.get("/api/rank-rewards/overview", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "current_rank" in data
    assert "tiers" in data
    assert len(data["tiers"]) == 3
    
    # 2. Admin Config Endpoints
    res_cfg = client.get("/api/admin/rank-rewards/config", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_cfg.status_code == 200
    assert len(res_cfg.json()["data"]) == 3
    
    # 3. Admin Update Config (Toggle VIP to EV Scooter)
    res_put = client.put(
        "/api/admin/rank-rewards/config/VIP",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"reward_type": "EV_SCOOTER", "qualification_days": 10}
    )
    assert res_put.status_code == 200
    assert res_put.json()["data"]["reward_type"] == "EV_SCOOTER"
    assert res_put.json()["data"]["qualification_days"] == 10
    
    # 4. Admin Achievements List
    res_ach = client.get("/api/admin/rank-rewards/achievements", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_ach.status_code == 200
    assert "items" in res_ach.json()["data"]

# =========================================================================
# FINAL PRODUCTION AUDIT SCENARIOS (A, B, C, D, E, F)
# =========================================================================

def test_scenario_a_two_directs_star_2100(db_session):
    """
    Scenario A:
    User has 2 direct referrals within 7 days.
    Expected: STAR + ₹2,100.
    """
    now = datetime.utcnow()
    user = User(
        user_code="USR-SC-A",
        email="sc_a@test.com",
        mobile="9900000001",
        full_name="Scenario A User",
        password_hash=hash_password("Pass@123"),
        role="USER",
        referral_code="SCA001",
        is_active=True,
        created_at=now - timedelta(days=5)
    )
    db_session.add(user)
    db_session.flush()
    process_package_purchase(db_session, user.id)

    # 2 direct referrals
    d1 = User(user_code="USR-SCA-D1", email="sca_d1@test.com", mobile="9900000011", full_name="Direct 1", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCAD1", sponsor_id=user.id, is_active=True, created_at=now - timedelta(days=3))
    d2 = User(user_code="USR-SCA-D2", email="sca_d2@test.com", mobile="9900000012", full_name="Direct 2", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCAD2", sponsor_id=user.id, is_active=True, created_at=now - timedelta(days=2))
    db_session.add_all([d1, d2])
    db_session.flush()
    process_package_purchase(db_session, d1.id)
    process_package_purchase(db_session, d2.id)

    db_session.refresh(user)
    assert user.current_rank == 'STAR'

    star_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user.id,
        RankAchievement.rank_name == 'STAR'
    ).first()
    assert star_ach is not None
    assert star_ach.status == 'ACHIEVED'
    assert star_ach.reward_amount == 2100.0
    assert star_ach.reward_status == 'CREDITED'

    # Check wallet ledger
    txn = db_session.get(WalletTransaction, star_ach.reward_transaction_id)
    assert txn.category == 'RANK_REWARD'
    assert txn.amount == 2100.0

def test_scenario_b_super_star_structure_5100(db_session):
    """
    Scenario B:
    User has 2 direct referrals. Both directs each get 2 personal directs within their required 7-day period.
    Expected: SUPER STAR + ₹5,100.
    """
    now = datetime.utcnow()
    user = User(user_code="USR-SC-B", email="sc_b@test.com", mobile="9910000001", full_name="Scenario B User", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCB001", is_active=True, created_at=now - timedelta(days=6))
    db_session.add(user)
    db_session.flush()
    process_package_purchase(db_session, user.id)

    # 2 direct referrals A and B
    a = User(user_code="USR-SCB-A", email="scb_a@test.com", mobile="9910000011", full_name="Direct A", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCBA", sponsor_id=user.id, is_active=True, created_at=now - timedelta(days=4))
    b = User(user_code="USR-SCB-B", email="scb_b@test.com", mobile="9910000012", full_name="Direct B", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCBB", sponsor_id=user.id, is_active=True, created_at=now - timedelta(days=4))
    db_session.add_all([a, b])
    db_session.flush()
    process_package_purchase(db_session, a.id)
    process_package_purchase(db_session, b.id)

    # A refers A1, A2
    a1 = User(user_code="USR-SCB-A1", email="scb_a1@test.com", mobile="9910000021", full_name="Direct A1", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCBA1", sponsor_id=a.id, is_active=True, created_at=now - timedelta(days=2))
    a2 = User(user_code="USR-SCB-A2", email="scb_a2@test.com", mobile="9910000022", full_name="Direct A2", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCBA2", sponsor_id=a.id, is_active=True, created_at=now - timedelta(days=2))
    db_session.add_all([a1, a2])
    db_session.flush()
    process_package_purchase(db_session, a1.id)
    process_package_purchase(db_session, a2.id)

    # B refers B1, B2
    b1 = User(user_code="USR-SCB-B1", email="scb_b1@test.com", mobile="9910000031", full_name="Direct B1", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCBB1", sponsor_id=b.id, is_active=True, created_at=now - timedelta(days=1))
    b2 = User(user_code="USR-SCB-B2", email="scb_b2@test.com", mobile="9910000032", full_name="Direct B2", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCBB2", sponsor_id=b.id, is_active=True, created_at=now - timedelta(days=1))
    db_session.add_all([b1, b2])
    db_session.flush()
    process_package_purchase(db_session, b1.id)
    process_package_purchase(db_session, b2.id)

    # Verify A is STAR, B is STAR, User is SUPER_STAR
    db_session.refresh(a)
    db_session.refresh(b)
    db_session.refresh(user)

    assert a.current_rank == 'STAR'
    assert b.current_rank == 'STAR'
    assert user.current_rank == 'SUPER_STAR'

    ss_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user.id,
        RankAchievement.rank_name == 'SUPER_STAR'
    ).first()
    assert ss_ach.status == 'ACHIEVED'
    assert ss_ach.reward_amount == 5100.0
    assert ss_ach.reward_status == 'CREDITED'

def test_scenario_c_vip_both_directs_super_star(db_session):
    """
    Scenario C:
    Both of user's qualifying directs become SUPER STAR.
    Expected: VIP + configured reward (₹51,000 / EV Scooter).
    """
    now = datetime.utcnow()
    user = User(user_code="USR-SC-C", email="sc_c@test.com", mobile="9920000001", full_name="Scenario C User", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCC001", is_active=True, current_rank="SUPER_STAR", created_at=now - timedelta(days=10))
    db_session.add(user)
    db_session.flush()

    a = User(user_code="USR-SCC-A", email="scc_a@test.com", mobile="9920000011", full_name="Direct A", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCCA", sponsor_id=user.id, is_active=True, current_rank="SUPER_STAR", created_at=now - timedelta(days=8))
    b = User(user_code="USR-SCC-B", email="scc_b@test.com", mobile="9920000012", full_name="Direct B", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCCB", sponsor_id=user.id, is_active=True, current_rank="SUPER_STAR", created_at=now - timedelta(days=8))
    db_session.add_all([a, b])
    db_session.flush()

    # Create Super Star achievements for A, B, and user
    ach_a = RankAchievement(user_id=a.id, rank_name="SUPER_STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=6), qualification_deadline=now + timedelta(days=1), achieved_at=now - timedelta(days=2), reward_type="CASH", reward_amount=5100.0, reward_status="CREDITED")
    ach_b = RankAchievement(user_id=b.id, rank_name="SUPER_STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=6), qualification_deadline=now + timedelta(days=1), achieved_at=now - timedelta(days=2), reward_type="CASH", reward_amount=5100.0, reward_status="CREDITED")
    ach_user_ss = RankAchievement(user_id=user.id, rank_name="SUPER_STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=8), qualification_deadline=now - timedelta(days=1), achieved_at=now - timedelta(days=3), reward_type="CASH", reward_amount=5100.0, reward_status="CREDITED")
    db_session.add_all([ach_a, ach_b, ach_user_ss])
    db_session.flush()

    evaluate_user_rank_progress(db_session, user.id)
    db_session.refresh(user)

    assert user.current_rank == 'VIP'
    vip_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user.id,
        RankAchievement.rank_name == 'VIP'
    ).first()
    assert vip_ach.status == 'ACHIEVED'
    assert vip_ach.reward_amount == 51000.0

def test_scenario_d_only_one_direct_super_star_no_vip(db_session):
    """
    Scenario D:
    Only one direct becomes SUPER STAR.
    Expected: NO VIP promotion.
    """
    now = datetime.utcnow()
    user = User(user_code="USR-SC-D", email="sc_d@test.com", mobile="9930000001", full_name="Scenario D User", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCD001", is_active=True, current_rank="SUPER_STAR", created_at=now - timedelta(days=10))
    db_session.add(user)
    db_session.flush()

    # Direct A is SUPER_STAR, Direct B is only STAR
    a = User(user_code="USR-SCD-A", email="scd_a@test.com", mobile="9930000011", full_name="Direct A", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCDA", sponsor_id=user.id, is_active=True, current_rank="SUPER_STAR", created_at=now - timedelta(days=8))
    b = User(user_code="USR-SCD-B", email="scd_b@test.com", mobile="9930000012", full_name="Direct B", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCDB", sponsor_id=user.id, is_active=True, current_rank="STAR", created_at=now - timedelta(days=8))
    db_session.add_all([a, b])
    db_session.flush()

    ach_a = RankAchievement(user_id=a.id, rank_name="SUPER_STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=6), qualification_deadline=now + timedelta(days=1), achieved_at=now - timedelta(days=2), reward_type="CASH", reward_amount=5100.0, reward_status="CREDITED")
    ach_b = RankAchievement(user_id=b.id, rank_name="STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=6), qualification_deadline=now + timedelta(days=1), achieved_at=now - timedelta(days=2), reward_type="CASH", reward_amount=2100.0, reward_status="CREDITED")
    ach_user_ss = RankAchievement(user_id=user.id, rank_name="SUPER_STAR", status="ACHIEVED", qualification_started_at=now - timedelta(days=8), qualification_deadline=now - timedelta(days=1), achieved_at=now - timedelta(days=3), reward_type="CASH", reward_amount=5100.0, reward_status="CREDITED")
    db_session.add_all([ach_a, ach_b, ach_user_ss])
    db_session.flush()

    evaluate_user_rank_progress(db_session, user.id)
    db_session.refresh(user)

    # User remains SUPER_STAR (NOT VIP)
    assert user.current_rank == 'SUPER_STAR'
    vip_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user.id,
        RankAchievement.rank_name == 'VIP'
    ).first()
    assert vip_ach is not None
    assert vip_ach.status == 'IN_PROGRESS'

def test_scenario_e_Matching_placement_downlines_do_not_count_as_directs(db_session):
    """
    Scenario E:
    A user gets 2 referrals placed under them in the Binary tree (spillover / binary_parent_id),
    but did NOT personally sponsor them (sponsor_id is someone else).
    Expected: They must NOT count towards rank qualification.
    """
    now = datetime.utcnow()
    upline_sponsor = User(user_code="USR-UPLINE", email="upline@test.com", mobile="9940000000", full_name="Upline Sponsor", password_hash=hash_password("Pass@123"), role="USER", referral_code="UPLINE01", is_active=True, created_at=now - timedelta(days=10))
    user = User(user_code="USR-SC-E", email="sc_e@test.com", mobile="9940000001", full_name="Scenario E User", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCE001", sponsor_id=upline_sponsor.id, is_active=True, created_at=now - timedelta(days=5))
    db_session.add_all([upline_sponsor, user])
    db_session.flush()
    process_package_purchase(db_session, upline_sponsor.id)
    process_package_purchase(db_session, user.id)

    # Downlines placed under `user` in Binary tree (binary_parent_id = user.id), but sponsored by `upline_sponsor`
    downline_left = User(user_code="USR-BIN-L", email="bin_l@test.com", mobile="9940000011", full_name="Matching Left Spill", password_hash=hash_password("Pass@123"), role="USER", referral_code="BINL", sponsor_id=upline_sponsor.id, binary_parent_id=user.id, binary_position="LEFT", is_active=True, created_at=now - timedelta(days=2))
    downline_right = User(user_code="USR-BIN-R", email="bin_r@test.com", mobile="9940000012", full_name="Matching Right Spill", password_hash=hash_password("Pass@123"), role="USER", referral_code="BINR", sponsor_id=upline_sponsor.id, binary_parent_id=user.id, binary_position="RIGHT", is_active=True, created_at=now - timedelta(days=2))
    db_session.add_all([downline_left, downline_right])
    db_session.flush()
    process_package_purchase(db_session, downline_left.id)
    process_package_purchase(db_session, downline_right.id)

    # Evaluate user
    evaluate_user_rank_progress(db_session, user.id)
    db_session.refresh(user)

    # Must NOT qualify for Star
    assert user.current_rank == 'DISTRIBUTOR'
    star_ach = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user.id,
        RankAchievement.rank_name == 'STAR'
    ).first()
    assert star_ach.status == 'IN_PROGRESS'
    assert star_ach.reward_status == 'PENDING'

    # Check overview: current_count must be 0
    overview = get_user_rank_overview(db_session, user.id)
    star_tier = next(t for t in overview['tiers'] if t['rank_name'] == 'STAR')
    assert star_tier['current_count'] == 0

def test_scenario_f_concurrency_and_repeated_processing_idempotency(db_session):
    """
    Scenario F:
    Same qualifying event is processed 10 times concurrently/repeatedly.
    Expected:
    - Exactly one rank promotion
    - Exactly one reward record
    - Exactly one wallet ledger transaction
    """
    now = datetime.utcnow()
    user = User(user_code="USR-SC-F", email="sc_f@test.com", mobile="9950000001", full_name="Scenario F User", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCF001", is_active=True, created_at=now - timedelta(days=5))
    db_session.add(user)
    db_session.flush()
    process_package_purchase(db_session, user.id)

    # Create 2 active direct referrals
    d1 = User(user_code="USR-SCF-D1", email="scf_d1@test.com", mobile="9950000011", full_name="Direct 1", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCFD1", sponsor_id=user.id, is_active=True, created_at=now - timedelta(days=2))
    d2 = User(user_code="USR-SCF-D2", email="scf_d2@test.com", mobile="9950000012", full_name="Direct 2", password_hash=hash_password("Pass@123"), role="USER", referral_code="SCFD2", sponsor_id=user.id, is_active=True, created_at=now - timedelta(days=2))
    db_session.add_all([d1, d2])
    db_session.flush()

    # Process evaluation 10 times consecutively
    promotion_events = []
    for _ in range(10):
        evts = evaluate_user_rank_progress(db_session, user.id)
        promotion_events.extend(evts)
        db_session.flush()

    # Exactly 1 promotion event
    assert len(promotion_events) == 1
    assert promotion_events[0]['rank'] == 'STAR'
    assert promotion_events[0]['award'] == 2100.0

    # Exactly 1 RankAchievement record
    star_achs = db_session.query(RankAchievement).filter(
        RankAchievement.user_id == user.id,
        RankAchievement.rank_name == 'STAR'
    ).all()
    assert len(star_achs) == 1
    assert star_achs[0].status == 'ACHIEVED'

    # Exactly 1 WalletTransaction ledger entry
    rank_txns = db_session.query(WalletTransaction).filter(
        WalletTransaction.user_id == user.id,
        WalletTransaction.category == 'RANK_REWARD'
    ).all()
    assert len(rank_txns) == 1
    assert rank_txns[0].amount == 2100.0

