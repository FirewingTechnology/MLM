-- ==============================================================================
-- PRODUCTION RDS POSTGRESQL SCHEMA MIGRATION: DAILY PACKAGE REFUND SYSTEM
-- Database: PostgreSQL (AWS RDS / mystatus-postgres)
-- Execution: Run in pgAdmin 4 Query Tool, AWS RDS Query Editor, or psql
-- ==============================================================================

BEGIN;

-- 1. Create table: daily_reward_cycles
CREATE TABLE IF NOT EXISTS daily_reward_cycles (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER NOT NULL UNIQUE REFERENCES purchases(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    package_id INTEGER NOT NULL REFERENCES packages(id) ON DELETE RESTRICT,
    
    refund_target DOUBLE PRECISION NOT NULL DEFAULT 35400.0,
    refunded_amount DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    completed_pairs INTEGER NOT NULL DEFAULT 0,
    base_daily_amount DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    pair_increment DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    current_daily_reward DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    last_credit_date VARCHAR(10),
    
    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- 2. Indexes for daily_reward_cycles
CREATE INDEX IF NOT EXISTS ix_daily_reward_cycles_id ON daily_reward_cycles (id);
CREATE INDEX IF NOT EXISTS ix_daily_reward_cycles_purchase_id ON daily_reward_cycles (purchase_id);
CREATE INDEX IF NOT EXISTS ix_daily_reward_cycles_user_id ON daily_reward_cycles (user_id);
CREATE INDEX IF NOT EXISTS ix_daily_reward_cycles_status ON daily_reward_cycles (status);
CREATE INDEX IF NOT EXISTS ix_daily_reward_cycles_last_credit_date ON daily_reward_cycles (last_credit_date);
CREATE INDEX IF NOT EXISTS ix_daily_reward_cycle_user_status ON daily_reward_cycles (user_id, status);
CREATE INDEX IF NOT EXISTS ix_daily_reward_cycle_user_last_credit ON daily_reward_cycles (user_id, last_credit_date);

-- 3. Create table: daily_reward_transactions
CREATE TABLE IF NOT EXISTS daily_reward_transactions (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES daily_reward_cycles(id) ON DELETE CASCADE,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    business_date VARCHAR(10) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    completed_pairs_snapshot INTEGER NOT NULL DEFAULT 0,
    daily_reward_snapshot DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    
    wallet_transaction_id INTEGER REFERENCES wallet_transactions(id) ON DELETE SET NULL,
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- 4. Indexes for daily_reward_transactions
CREATE INDEX IF NOT EXISTS ix_daily_reward_transactions_id ON daily_reward_transactions (id);
CREATE INDEX IF NOT EXISTS ix_daily_reward_transactions_cycle_id ON daily_reward_transactions (cycle_id);
CREATE INDEX IF NOT EXISTS ix_daily_reward_transactions_purchase_id ON daily_reward_transactions (purchase_id);
CREATE INDEX IF NOT EXISTS ix_daily_reward_transactions_user_id ON daily_reward_transactions (user_id);
CREATE INDEX IF NOT EXISTS ix_daily_reward_transactions_business_date ON daily_reward_transactions (business_date);
CREATE INDEX IF NOT EXISTS ix_daily_reward_transactions_idempotency_key ON daily_reward_transactions (idempotency_key);
CREATE INDEX IF NOT EXISTS ix_daily_reward_txn_user_date ON daily_reward_transactions (user_id, business_date);

-- 5. Synchronize primary key sequences if tables already have data
SELECT setval(pg_get_serial_sequence('daily_reward_cycles', 'id'), COALESCE((SELECT MAX(id) FROM daily_reward_cycles), 1), (SELECT MAX(id) IS NOT NULL FROM daily_reward_cycles));
SELECT setval(pg_get_serial_sequence('daily_reward_transactions', 'id'), COALESCE((SELECT MAX(id) FROM daily_reward_transactions), 1), (SELECT MAX(id) IS NOT NULL FROM daily_reward_transactions));

COMMIT;

-- ==============================================================================
-- VERIFICATION QUERY
-- ==============================================================================
SELECT 
    table_name, 
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('daily_reward_cycles', 'daily_reward_transactions');
