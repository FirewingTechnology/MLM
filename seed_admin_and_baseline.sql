-- ==============================================================================
-- PRODUCTION RDS POSTGRESQL INITIAL ADMIN & ROOT PARTNER SEED SCRIPT
-- Execute in pgAdmin 4 Query Tool on database 'postgres'
-- ==============================================================================

-- 1. Insert Default Franchise Package (₹35,000 / 30,000 BV)
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
)
ON CONFLICT (id) DO NOTHING;

-- 2. Insert Time Engine Configuration (Real Time Mode)
INSERT INTO demo_time_config (id, mode, virtual_datetime)
VALUES (1, 'REAL', NULL)
ON CONFLICT (id) DO NOTHING;

-- 3. Insert Initial Administrator Account
-- Login: admin@mynetwork.com / Admin@123
INSERT INTO users (
    id, user_code, email, mobile, full_name, password_hash, role, referral_code, is_active, created_at
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
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- 4. Create Admin Wallet & Matching Volume Structures
INSERT INTO wallets (user_id, balance, total_earned, total_withdrawn, created_at)
VALUES (1, 0.0, 0.0, 0.0, NOW())
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO binary_volumes (user_id, personal_bv, accumulated_left_bv, accumulated_right_bv, matched_bv, carry_left_bv, carry_right_bv, created_at)
VALUES (1, 30000.0, 0.0, 0.0, 0.0, 0.0, 0.0, NOW())
ON CONFLICT (user_id) DO NOTHING;

-- 5. Insert Root Member Account (for testing partner registrations & network tree)
-- Login: amol@mynetwork.com / Admin@123
-- Referral Code: AMOL001
INSERT INTO users (
    id, user_code, email, mobile, full_name, password_hash, role, referral_code, sponsor_id, is_active, created_at
)
VALUES (
    2, 
    'USR-AMOL', 
    'amol@mynetwork.com', 
    '9876500002', 
    'Amol Partner', 
    '$2b$12$/wVfiCRWigM2tkyP2EkDj.KSabPHBacB7laMinWa.0vT5LYyPOKa6', 
    'USER', 
    'AMOL001', 
    1, 
    true, 
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- 6. Create Root Member Wallet & Matching Volume Structures
INSERT INTO wallets (user_id, balance, total_earned, total_withdrawn, created_at)
VALUES (2, 0.0, 0.0, 0.0, NOW())
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO binary_volumes (user_id, personal_bv, accumulated_left_bv, accumulated_right_bv, matched_bv, carry_left_bv, carry_right_bv, created_at)
VALUES (2, 30000.0, 0.0, 0.0, 0.0, 0.0, 0.0, NOW())
ON CONFLICT (user_id) DO NOTHING;

-- 7. Reset PostgreSQL Primary Key Sequences
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));
SELECT setval('packages_id_seq', (SELECT COALESCE(MAX(id), 1) FROM packages));
SELECT setval('wallets_id_seq', (SELECT COALESCE(MAX(id), 1) FROM wallets));
SELECT setval('binary_volumes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM binary_volumes));

-- 8. Verify Seeded Data
SELECT id, user_code, email, mobile, full_name, role, referral_code, is_active FROM users;
