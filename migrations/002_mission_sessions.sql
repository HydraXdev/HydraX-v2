-- Migration 002: Mission Session Architecture
-- Date: October 5, 2025
-- Purpose: Secure mission-based trading flow with JWT tokens and replay protection

-- 1. Mission Sessions Table
CREATE TABLE IF NOT EXISTS mission_sessions (
    mission_session_id TEXT PRIMARY KEY,          -- Format: ms_<ulid>
    user_id TEXT NOT NULL,
    alert_id INTEGER NOT NULL,                    -- References signals.id
    signal_id TEXT NOT NULL,                      -- References signals.signal_id
    status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING/EXECUTED/EXPIRED
    pair TEXT,
    timeframe TEXT,
    risk_max_usd REAL,
    token_nonce TEXT UNIQUE,                      -- One-time use nonce
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,                  -- 5-10 min TTL
    executed_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (signal_id) REFERENCES signals(signal_id)
);

CREATE INDEX IF NOT EXISTS idx_mission_sessions_user ON mission_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_mission_sessions_status ON mission_sessions(status);
CREATE INDEX IF NOT EXISTS idx_mission_sessions_expires ON mission_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_mission_sessions_nonce ON mission_sessions(token_nonce);
CREATE INDEX IF NOT EXISTS idx_mission_sessions_signal ON mission_sessions(signal_id);

-- 2. Idempotency Cache Table
CREATE TABLE IF NOT EXISTS idempotency_cache (
    cache_key TEXT PRIMARY KEY,                   -- {user_id}:{ms_id}:{client_request_id}
    user_id TEXT NOT NULL,
    mission_session_id TEXT NOT NULL,
    client_request_id TEXT NOT NULL,
    op_id TEXT NOT NULL,
    response_json TEXT NOT NULL,                  -- Cached response
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,                  -- 10 min TTL
    UNIQUE(user_id, mission_session_id, client_request_id)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_idempotency_user_ms ON idempotency_cache(user_id, mission_session_id);

-- 3. API Tokens Table (for JWT key management)
CREATE TABLE IF NOT EXISTS api_tokens (
    token_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    key_id TEXT NOT NULL,                         -- kid for JWT rotation
    public_key TEXT NOT NULL,                     -- For RS256 verification
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    revoked_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_api_tokens_user ON api_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_key_id ON api_tokens(key_id);

-- 4. Migration tracking
INSERT OR IGNORE INTO schema_versions (version, applied_at)
VALUES ('002_mission_sessions', strftime('%s', 'now'));
