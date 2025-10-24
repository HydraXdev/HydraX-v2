-- BITTEN v2.0 Users Table
-- Core user account management with tier system and fire mode configuration

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    balance REAL DEFAULT 0,
    equity REAL DEFAULT 0,
    tier TEXT DEFAULT 'RECRUIT' CHECK (tier IN ('RECRUIT', 'FANG', 'COMMANDER', 'COMMANDER+')),
    fire_mode TEXT DEFAULT 'MANUAL' CHECK (fire_mode IN ('MANUAL', 'SEMI_AUTO', 'FULL_AUTO')),
    bitmode_enabled BOOLEAN DEFAULT FALSE,
    target_uuid TEXT,
    account_login TEXT,
    broker TEXT,
    currency TEXT DEFAULT 'USD',
    leverage INTEGER DEFAULT 500,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier);
CREATE INDEX IF NOT EXISTS idx_users_fire_mode ON users(fire_mode);
CREATE INDEX IF NOT EXISTS idx_users_target_uuid ON users(target_uuid);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE users IS 'Core user accounts with tier system and trading configuration';
COMMENT ON COLUMN users.tier IS 'RECRUIT (free), FANG ($97), COMMANDER ($497), COMMANDER+ ($997)';
COMMENT ON COLUMN users.fire_mode IS 'Trading execution mode: MANUAL, SEMI_AUTO, FULL_AUTO';
COMMENT ON COLUMN users.bitmode_enabled IS 'Hybrid position management (25%/25%/50% strategy)';
