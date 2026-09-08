-- ==============================================================================
-- CLEAN PRODUCTION DATABASE & PRESERVE ONLY SYSTEM ADMINISTRATOR
-- Execute in pgAdmin 4 Query Tool on database 'postgres'
-- ==============================================================================

-- 1. Truncate all transactional & user tables with CASCADE
TRUNCATE TABLE 
    audit_logs,
    binary_period_volumes,
    binary_volumes,
    commissions,
    demo_time_config,
    package_activation_requests,
    packages,
    pair_events,
    purchases,
    referral_tokens,
    security_pin_ledger,
    security_pin_orders,
    security_pin_transfers,
    security_pin_upline_requests,
    security_pins,
    slot_settlements,
    volume_ledgers,
    wallet_transactions,
    withdrawals,
    wallets,
    users
RESTART IDENTITY CASCADE;

-- 2. Insert Default Franchise Package (₹35,000 / 30,000 BV)
INSERT INTO packages (id, name, description, price, product_value, gst_amount, bv, is_active, created_at)
VALUES (
    1, 
    'Premium Sub Franchise Package', 
    'Sub Franchise Business Ownership Package with 30,000 BV and active distributor rights.', 
    35000.0, 
    30000.0, 
    5000.0, 
    30000.0, 
    true, 
    NOW()
);

-- 3. Insert Time Configuration (Real Time Mode)
INSERT INTO demo_time_config (id, mode, virtual_datetime, updated_at)
VALUES (1, 'REAL', NULL, NOW());

-- 4. Insert Single System Administrator Account (Password: Admin@123)
INSERT INTO users (
    id, user_code, email, mobile, full_name, password_hash, role, referral_code, is_active, created_at, updated_at
)
VALUES (
    1, 
    'ADM-00001', 
    'admin@mynetwork.com', 
    '9876500001', 
    'System Administrator', 
    '$2b$12$/wVfiCRWigM2tkyP2EkDj.KSabPHBacB7laMinWa.0vT5LYyPOKa6', 
    'ADMIN', 
    'ADMIN001', 
    true, 
    NOW(),
    NOW()
);

-- 5. Insert Administrator Wallet
INSERT INTO wallets (user_id, balance, total_earned, total_withdrawn, updated_at)
VALUES (1, 0.0, 0.0, 0.0, NOW());

-- 6. Insert Administrator Matching Volume Structure
INSERT INTO binary_volumes (user_id, personal_bv, accumulated_left_bv, accumulated_right_bv, matched_bv, carry_left_bv, carry_right_bv, updated_at)
VALUES (1, 30000.0, 0.0, 0.0, 0.0, 0.0, 0.0, NOW());

-- 7. Reset Sequences
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));
SELECT setval('packages_id_seq', (SELECT COALESCE(MAX(id), 1) FROM packages));
SELECT setval('wallets_id_seq', (SELECT COALESCE(MAX(id), 1) FROM wallets));
SELECT setval('binary_volumes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM binary_volumes));

-- 8. Verify Only Admin Exists
SELECT id, user_code, email, mobile, full_name, role, referral_code, is_active FROM users;
