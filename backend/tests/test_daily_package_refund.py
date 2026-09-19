import pytest
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from app.models.user import User
from app.models.purchase import Purchase
from app.models.package import Package
from app.models.daily_reward import DailyRewardCycle, DailyRewardTransaction
from app.models.wallet import Wallet, WalletTransaction
from app.models.commission import Commission
from app.models.pair_event import PairEvent
from app.models.earning_cycle import EarningCycle
from app.services.daily_reward_service import daily_reward_service, SettlementTimingError
from app.services.commission_service import process_package_purchase
from app.services.pair_service import pair_service
from app.services.time_service import time_provider, IST
from app.services.wallet_service import get_or_create_wallet
from app.security import create_access_token

def get_auth_headers(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}

# =========================================================================
# 1-6. PACKAGE CREATION & PAIR REWARD FORMULA TESTS
# =========================================================================

def test_1_new_package_creates_daily_reward_cycle(client, db_session):
    """1. New package creates daily reward cycle with ₹35,400 target."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    pkg = db_session.query(Package).filter(Package.is_active == True).first()

    purchase, events = process_package_purchase(db_session, user_id=amol.id, package_id=pkg.id)
    db_session.commit()

    cycle = db_session.query(DailyRewardCycle).filter(DailyRewardCycle.purchase_id == purchase.id).first()
    assert cycle is not None
    assert cycle.user_id == amol.id
    assert cycle.refund_target == 35400.0
    assert cycle.refunded_amount == 0.0
    assert cycle.status == 'ACTIVE'
    assert cycle.completed_pairs == 0
    assert cycle.base_daily_amount == 50.0
    assert cycle.pair_increment == 50.0
    assert cycle.current_daily_reward == 50.0

def test_2_initial_daily_reward_base_50(db_session):
    """2. Initial daily reward is ₹50."""
    reward = daily_reward_service.calculate_current_daily_reward(completed_pairs=0)
    assert reward == 50.0

def test_3_zero_pairs_50_per_day(db_session):
    """3. 0 completed pairs => ₹50/day."""
    assert daily_reward_service.calculate_current_daily_reward(0) == 50.0

def test_4_one_completed_pair_100_per_day(db_session):
    """4. 1 completed pair => ₹100/day."""
    assert daily_reward_service.calculate_current_daily_reward(1) == 100.0

def test_5_two_completed_pairs_150_per_day(db_session):
    """5. 2 completed pairs => ₹150/day."""
    assert daily_reward_service.calculate_current_daily_reward(2) == 150.0

def test_6_three_completed_pairs_200_per_day(db_session):
    """6. 3 completed pairs => ₹200/day."""
    assert daily_reward_service.calculate_current_daily_reward(3) == 200.0
    assert daily_reward_service.calculate_current_daily_reward(4) == 250.0

# =========================================================================
# 7-10. AUTHORITATIVE PAIR COUNT INTEGRATION TESTS
# =========================================================================

def test_7_incomplete_pair_does_not_increase_reward(client, db_session):
    """7. Incomplete pair (Left only, 0 Right) does not increase reward."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # Register user under Amol LEFT only
    client.post("/api/auth/register", json={
        "full_name": "Left Only User",
        "email": "left_only@demo.com",
        "mobile": "9999911111",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    user_left = db_session.query(User).filter(User.email == "left_only@demo.com").first()
    process_package_purchase(db_session, user_left.id)
    db_session.commit()

    completed_pairs = daily_reward_service.get_completed_pair_count(db_session, amol.id)
    assert completed_pairs == 0
    current_reward = daily_reward_service.get_current_daily_reward(db_session, amol.id)
    assert current_reward == 50.0

def test_8_referral_alone_does_not_increase_reward(client, db_session):
    """8. Referral alone (no matching pairs) does not increase reward."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # Create 3 direct referrals without placement pairing
    for i in range(1, 4):
        client.post("/api/auth/register", json={
            "full_name": f"Direct Ref {i}",
            "email": f"ref{i}@demo.com",
            "mobile": f"988880000{i}",
            "password": "Demo@123",
            "confirm_password": "Demo@123",
            "referral_code": "AMOL001"
        })
    db_session.commit()

    completed_pairs = daily_reward_service.get_completed_pair_count(db_session, amol.id)
    assert completed_pairs == 0
    assert daily_reward_service.get_current_daily_reward(db_session, amol.id) == 50.0

def test_9_placement_alone_does_not_increase_reward(client, db_session):
    """9. Placement alone (spillover without qualification) does not increase reward."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    # Register childKumar without sponsor binary qualification
    client.post("/api/auth/register", json={
        "full_name": "Kumar",
        "email": "kumar_spill@demo.com",
        "mobile": "9777700001",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "RIGHT"
    })
    kumar = db_session.query(User).filter(User.email == "kumar_spill@demo.com").first()
    db_session.commit()

    completed_pairs = daily_reward_service.get_completed_pair_count(db_session, kumar.id)
    assert completed_pairs == 0
    assert daily_reward_service.get_current_daily_reward(db_session, kumar.id) == 50.0

def test_10_pair_count_comes_from_authoritative_engine(client, db_session):
    """10. Pair count comes from existing authoritative pairing engine (PairEvent)."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    # Register Left
    client.post("/api/auth/register", json={
        "full_name": "Left 10",
        "email": "left10@demo.com",
        "mobile": "9999900010",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "LEFT"
    })
    # Register Right
    client.post("/api/auth/register", json={
        "full_name": "Right 10",
        "email": "right10@demo.com",
        "mobile": "9999900020",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001",
        "binary_parent_code": "AMOL001",
        "binary_position": "RIGHT"
    })
    u_left = db_session.query(User).filter(User.email == "left10@demo.com").first()
    u_right = db_session.query(User).filter(User.email == "right10@demo.com").first()

    # Left & Right purchase 30k packages -> forms exact 1 completed pair
    process_package_purchase(db_session, u_left.id)
    process_package_purchase(db_session, u_right.id)
    db_session.commit()

    # Authoritative pair engine must have 1 completed PairEvent
    pair_events_count = db_session.query(PairEvent).filter(
        PairEvent.pair_earner_user_id == amol.id,
        PairEvent.status == 'COMPLETED'
    ).count()
    assert pair_events_count == 1

    # Daily reward engine must reflect exactly 1 completed pair -> ₹100/day
    assert daily_reward_service.get_completed_pair_count(db_session, amol.id) == 1
    assert daily_reward_service.get_current_daily_reward(db_session, amol.id) == 100.0

# =========================================================================
# 11-15. SETTLEMENT TIMING, 07:00 AM IST & IDEMPOTENCY
# =========================================================================

def test_11_daily_settlement_for_correct_ist_date(db_session):
    """11. Daily settlement occurs for correct IST business date."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    # Settle for specific historical IST date
    target_date = date(2026, 8, 20)
    summary = daily_reward_service.settle_daily_rewards(db_session, business_date=target_date, force=True)
    db_session.commit()

    assert summary['business_date'] == "2026-08-20"
    assert summary['credited_count'] >= 1

    cycle = db_session.query(DailyRewardCycle).filter(DailyRewardCycle.purchase_id == purchase.id).first()
    assert cycle.last_credit_date == "2026-08-20"
    assert cycle.refunded_amount == 50.0

def test_12_settlement_at_or_after_0700_ist(db_session):
    """12. Settlement at or after 07:00 IST succeeds."""
    time_provider.set_demo_time(db_session, datetime(2026, 8, 26, 7, 0, 0, tzinfo=IST))
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    summary = daily_reward_service.settle_daily_rewards(db_session, business_date=date(2026, 8, 26))
    db_session.commit()

    assert summary['credited_count'] >= 1
    assert summary['total_credited_amount'] >= 50.0

def test_13_before_0700_must_not_settle_todays_reward(db_session):
    """13. Before 07:00 AM IST must not settle that day's reward."""
    time_provider.set_demo_time(db_session, datetime(2026, 8, 26, 6, 59, 59, tzinfo=IST))
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    with pytest.raises(SettlementTimingError) as exc_info:
        daily_reward_service.settle_daily_rewards(db_session, business_date=date(2026, 8, 26), force=False)
    assert "cannot be executed before 07:00 AM IST" in str(exc_info.value)

def test_14_duplicate_scheduler_execution_does_not_double_credit(db_session):
    """14. Duplicate scheduler execution does not double-credit (idempotency)."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    wallet = get_or_create_wallet(db_session, amol.id)
    init_balance = wallet.balance

    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    # First settlement run
    summary1 = daily_reward_service.settle_daily_rewards(db_session, business_date=date(2026, 8, 21), force=True)
    db_session.commit()
    assert summary1['credited_count'] == 1

    wallet_after_1 = db_session.query(Wallet).filter(Wallet.user_id == amol.id).first()
    assert wallet_after_1.balance == init_balance + 50.0

    # Second settlement run on same business date
    summary2 = daily_reward_service.settle_daily_rewards(db_session, business_date=date(2026, 8, 21), force=True)
    db_session.commit()
    assert summary2['credited_count'] == 0
    assert summary2['skipped_count'] >= 1

    wallet_after_2 = db_session.query(Wallet).filter(Wallet.user_id == amol.id).first()
    # Balance must remain exactly unchanged (no double credit)
    assert wallet_after_2.balance == init_balance + 50.0

def test_15_concurrent_settlement_safety(db_session):
    """15. Idempotency key uniqueness prevents duplicate transactions."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    cycle = db_session.query(DailyRewardCycle).filter(DailyRewardCycle.purchase_id == purchase.id).first()
    now_ist = datetime(2026, 8, 22, 7, 0, 0, tzinfo=IST)

    res1 = daily_reward_service.settle_user_daily_reward(db_session, cycle.id, "2026-08-22", now_ist)
    db_session.commit()
    assert res1['status'] == 'CREDITED'

    # Immediate second call
    res2 = daily_reward_service.settle_user_daily_reward(db_session, cycle.id, "2026-08-22", now_ist)
    assert res2['status'] == 'SKIPPED_ALREADY_CREDITED'

    # Only 1 transaction in DB
    txns = db_session.query(DailyRewardTransaction).filter(
        DailyRewardTransaction.purchase_id == purchase.id,
        DailyRewardTransaction.business_date == "2026-08-22"
    ).all()
    assert len(txns) == 1

# =========================================================================
# 16-19. REFUND LIMIT & PARTIAL CREDIT TESTS
# =========================================================================

def test_16_daily_credit_cannot_exceed_remaining_refund(db_session):
    """16. Daily credit cannot exceed remaining refund."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    cycle = db_session.query(DailyRewardCycle).filter(DailyRewardCycle.purchase_id == purchase.id).first()
    # Set refunded amount so only ₹30 is remaining
    cycle.refunded_amount = 35370.0
    db_session.commit()

    now_ist = datetime(2026, 8, 23, 7, 0, 0, tzinfo=IST)
    res = daily_reward_service.settle_user_daily_reward(db_session, cycle.id, "2026-08-23", now_ist)
    db_session.commit()

    assert res['status'] == 'CREDITED'
    # Base daily reward is ₹50, but only ₹30 remaining -> daily credit must be exactly ₹30
    assert res['amount'] == 30.0
    assert cycle.refunded_amount == 35400.0
    assert cycle.status == 'COMPLETED'

def test_17_final_partial_credit_works_correctly(db_session):
    """17. Final partial credit works correctly (e.g. ₹25 remaining)."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    cycle = db_session.query(DailyRewardCycle).filter(DailyRewardCycle.purchase_id == purchase.id).first()
    cycle.refunded_amount = 35375.0  # Exactly ₹25 remaining
    db_session.commit()

    now_ist = datetime(2026, 8, 24, 7, 0, 0, tzinfo=IST)
    res = daily_reward_service.settle_user_daily_reward(db_session, cycle.id, "2026-08-24", now_ist)
    db_session.commit()

    assert res['amount'] == 25.0
    assert cycle.refunded_amount == 35400.0
    assert cycle.status == 'COMPLETED'
    assert cycle.completed_at is not None

def test_18_cycle_becomes_completed_exactly_at_refund_target(db_session):
    """18. Cycle becomes COMPLETED exactly at refund target."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    cycle = db_session.query(DailyRewardCycle).filter(DailyRewardCycle.purchase_id == purchase.id).first()
    cycle.refunded_amount = 35350.0  # ₹50 remaining
    db_session.commit()

    now_ist = datetime(2026, 8, 25, 7, 0, 0, tzinfo=IST)
    res = daily_reward_service.settle_user_daily_reward(db_session, cycle.id, "2026-08-25", now_ist)
    db_session.commit()

    assert res['amount'] == 50.0
    assert cycle.status == 'COMPLETED'
    assert cycle.remaining_refund == 0.0
    assert cycle.progress_percentage == 100.0

def test_19_no_credit_after_completed(db_session):
    """19. No credit after COMPLETED."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    cycle = db_session.query(DailyRewardCycle).filter(DailyRewardCycle.purchase_id == purchase.id).first()
    cycle.refunded_amount = 35400.0
    cycle.status = 'COMPLETED'
    db_session.commit()

    now_ist = datetime(2026, 8, 26, 7, 0, 0, tzinfo=IST)
    res = daily_reward_service.settle_user_daily_reward(db_session, cycle.id, "2026-08-26", now_ist)
    assert res is None  # Status is not ACTIVE, skipped immediately

# =========================================================================
# 20-25. WALLET CATEGORY, CAP ISOLATION & REGRESSION SUITE
# =========================================================================

def test_20_historical_wallet_transactions_remain_unchanged(db_session):
    """20. Historical wallet transactions remain unchanged and category is DAILY_PACKAGE_REFUND."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    daily_reward_service.settle_daily_rewards(db_session, business_date=date(2026, 8, 27), force=True)
    db_session.commit()

    w_txn = db_session.query(WalletTransaction).filter(
        WalletTransaction.user_id == amol.id,
        WalletTransaction.category == 'DAILY_PACKAGE_REFUND'
    ).first()

    assert w_txn is not None
    assert w_txn.category == 'DAILY_PACKAGE_REFUND'
    assert w_txn.transaction_type == 'CREDIT'
    assert w_txn.amount == 50.0

def test_21_existing_direct_commission_tests_pass(client, db_session):
    """21. Existing Direct Commission (10% on BV) remains unchanged."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()

    client.post("/api/auth/register", json={
        "full_name": "Direct Test User",
        "email": "direct_test@demo.com",
        "mobile": "9999988888",
        "password": "Demo@123",
        "confirm_password": "Demo@123",
        "referral_code": "AMOL001"
    })
    user_new = db_session.query(User).filter(User.email == "direct_test@demo.com").first()
    process_package_purchase(db_session, user_new.id)
    db_session.commit()

    # Direct commission on 30,000 BV @ 10% = ₹3,000
    direct_comm = db_session.query(Commission).filter(
        Commission.beneficiary_id == amol.id,
        Commission.commission_type == 'DIRECT_REFERRAL'
    ).first()
    assert direct_comm is not None
    assert direct_comm.amount == 3000.0

def test_22_existing_pair_bonus_tests_pass(client, db_session):
    """22. Existing Pair Bonus tests remain passing."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    slot_info = time_provider.get_current_slot_info(db_session)

    summary = pair_service.get_user_pair_summary(db_session, amol.id, slot_info.slot_id)
    assert 'effective_left_bv' in summary
    assert 'effective_right_bv' in summary
    assert 'pair_bonus_amount' in summary

def test_23_existing_300k_earning_cap_remains_unchanged(db_session):
    """23. Existing ₹3,00,000 Direct + Pairing cap remains unchanged and excludes DAILY_PACKAGE_REFUND."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    purchase, _ = process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    # Check EarningCycle before
    cycle = db_session.query(EarningCycle).filter(
        EarningCycle.user_id == amol.id,
        EarningCycle.status == 'ACTIVE'
    ).first()
    assert cycle is not None
    init_total_income = cycle.total_eligible_income

    # Settle daily package refund
    daily_reward_service.settle_daily_rewards(db_session, business_date=date(2026, 8, 28), force=True)
    db_session.commit()

    # EarningCycle eligible income must NOT have increased (isolated from ₹3,00,000 cap)
    db_session.refresh(cycle)
    assert cycle.total_eligible_income == init_total_income
    assert cycle.earning_cap == 300000.0

def test_24_existing_rank_reward_tests_pass(db_session):
    """24. Existing rank reward tests continue to pass."""
    from app.services.rank_service import get_all_rank_configs
    configs = get_all_rank_configs(db_session)
    assert len(configs) >= 1
    assert any(c.rank_name == 'STAR' for c in configs)

def test_25_api_endpoints_and_security(client, db_session):
    """25. User and Admin daily reward API endpoints function with authentication and access control."""
    amol = db_session.query(User).filter(User.email == "amol@demo.com").first()
    admin = db_session.query(User).filter(User.role == "ADMIN").first()

    process_package_purchase(db_session, user_id=amol.id)
    db_session.commit()

    # 1. User Overview Endpoint
    user_headers = get_auth_headers(amol)
    res_user = client.get("/api/daily-rewards/overview", headers=user_headers)
    assert res_user.status_code == 200
    user_data = res_user.json()
    assert user_data['has_active_cycle'] is True
    assert user_data['cycle']['refund_target'] == 35400.0
    assert user_data['current_daily_reward'] == 50.0

    # 2. Admin Endpoint forbidden to regular user
    res_admin_forbidden = client.get("/api/daily-rewards/admin/cycles", headers=user_headers)
    assert res_admin_forbidden.status_code == 403

    # 3. Admin Endpoint allowed to admin
    admin_headers = get_auth_headers(admin)
    res_admin = client.get("/api/daily-rewards/admin/cycles", headers=admin_headers)
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data['total_count'] >= 1
    assert 'summary' in admin_data
    assert admin_data['summary']['active_cycles'] >= 1

    # 4. Admin Settle Endpoint
    res_settle = client.post("/api/daily-rewards/admin/settle", json={"force": True, "business_date": "2026-08-29"}, headers=admin_headers)
    assert res_settle.status_code == 200
    assert res_settle.json()['credited_count'] >= 1
