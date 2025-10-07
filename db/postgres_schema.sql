-- BITTEN v2.1 - Postgres Schema for Single Source of Truth
-- Date: 2025-09-16
-- Purpose: Complete user management with event bus integration

-- USERS & ACCOUNTS
CREATE TABLE users (
  user_id        BIGSERIAL PRIMARY KEY,
  telegram_id    BIGINT UNIQUE,
  username       TEXT,
  email          TEXT,
  status         TEXT DEFAULT 'active',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE accounts (
  account_id     BIGSERIAL PRIMARY KEY,
  user_id        BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  broker         TEXT,
  account_number TEXT,
  base_ccy       TEXT DEFAULT 'USD',
  leverage       INT,
  is_primary     BOOLEAN DEFAULT TRUE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, account_number)
);

-- ADMIN-EDITABLE KNOBS (the settings you can tweak)
CREATE TABLE user_settings (
  user_id           BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  tier              TEXT,                 -- COMMANDER, FANG, APEX, etc.
  risk_mode         TEXT,                 -- fixed, percent, conservative
  risk_per_trade_bp INT,                  -- basis points (e.g., 500 = 5.0%)
  max_concurrent    INT,                  -- max concurrent positions
  daily_dd_cap_bp   INT,                  -- daily drawdown cap in bp
  slots             INT,                  -- number of mission slots
  auto_fire_enabled BOOLEAN DEFAULT TRUE, -- auto-fire toggle
  confidence_min    NUMERIC(5,2) DEFAULT 80.0,  -- min confidence for auto-fire
  confidence_max    NUMERIC(5,2) DEFAULT 89.0,  -- max confidence for auto-fire
  flags             JSONB DEFAULT '{}'    -- feature toggles, e.g. {"bitmode": true}
);

-- IMMUTABLE FACTS PER TRADE (fed by event bus)
CREATE TABLE trade_facts (
  trade_id       TEXT PRIMARY KEY,        -- signal_id from comprehensive_tracking.jsonl
  user_id        BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  account_id     BIGINT REFERENCES accounts(account_id),
  signal_id      TEXT,                    -- same as trade_id for our events
  fire_id        TEXT,                    -- if executed via fire command
  symbol         TEXT,                    -- USDCNH, XAUUSD, etc.
  pattern        TEXT,                    -- KALMAN_QUICKFIRE, BB_SCALP, etc.
  session        TEXT,                    -- LONDON, NY, ASIAN, OVERLAP
  confidence     NUMERIC(5,2),            -- 73.4, 84.0, etc.
  direction      TEXT,                    -- BUY/SELL
  entry          NUMERIC(18,6),           -- entry price
  exit           NUMERIC(18,6),           -- exit price
  sl             NUMERIC(18,6),           -- stop loss
  tp             NUMERIC(18,6),           -- take profit
  rr             NUMERIC(10,4),           -- risk/reward ratio
  pips_net       NUMERIC(12,4),           -- pips result (19.0, -30.0, etc.)
  pnl_ccy        NUMERIC(18,2),           -- P&L in account currency
  fees_ccy       NUMERIC(18,2) DEFAULT 0, -- trading fees
  result         TEXT,                    -- win|loss|be|manual_close|timeout
  closed_reason  TEXT,                    -- tp|sl|trail|manual|timeout
  ts_open        TIMESTAMPTZ,             -- signal creation time
  ts_close       TIMESTAMPTZ,             -- outcome resolution time
  duration_min   NUMERIC(10,2),           -- trade duration in minutes
  source         TEXT DEFAULT 'event_bus', -- event_bus|manual|backfill
  raw_event      JSONB,                   -- store full original event
  schema_version INT NOT NULL DEFAULT 1
);

-- Performance indexes for trade_facts
CREATE INDEX trade_facts_user_close_idx   ON trade_facts (user_id, ts_close DESC);
CREATE INDEX trade_facts_user_symbol_idx  ON trade_facts (user_id, symbol);
CREATE INDEX trade_facts_user_pattern_idx ON trade_facts (user_id, pattern);
CREATE INDEX trade_facts_result_idx       ON trade_facts (result);
CREATE INDEX trade_facts_ts_close_idx     ON trade_facts (ts_close DESC);

-- LEDGER (deposits/withdrawals/sweeps/bonuses separate from PnL)
CREATE TABLE user_ledger (
  ledger_id      BIGSERIAL PRIMARY KEY,
  user_id        BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
  type           TEXT,                    -- deposit|withdrawal|sweep|fee|bonus|adjustment
  amount_ccy     NUMERIC(18,2),
  ccy            TEXT DEFAULT 'USD',
  meta           JSONB DEFAULT '{}'
);
CREATE INDEX user_ledger_user_ts_idx ON user_ledger (user_id, ts DESC);

-- XP EVENTS (gamification system)
CREATE TABLE xp_events (
  xp_id          BIGSERIAL PRIMARY KEY,
  user_id        BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
  points         INT NOT NULL,
  reason         TEXT,                    -- trade_win, trade_be, streak_3, pattern_variety
  related_trade_id TEXT,
  meta           JSONB DEFAULT '{}'
);
CREATE INDEX xp_events_user_ts_idx ON xp_events (user_id, ts DESC);

-- TEMP OVERRIDES (manual numbers or feature toggles with expiry)
CREATE TABLE user_overrides (
  user_id     BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
  key         TEXT,                      -- xp_total, risk_lock, feature_flag
  value       JSONB,
  expires_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, key)
);

-- ADMIN AUDIT LOG (tracks all manual changes)
CREATE TABLE admin_audit (
  audit_id  BIGSERIAL PRIMARY KEY,
  ts        TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor     TEXT,                        -- admin username/id
  user_id   BIGINT,
  action    TEXT,                        -- update_settings, add_override, etc.
  table_name TEXT,                       -- which table was modified
  before    JSONB,                       -- snapshot before change
  after     JSONB                        -- snapshot after change
);
CREATE INDEX admin_audit_user_ts_idx ON admin_audit (user_id, ts DESC);
CREATE INDEX admin_audit_actor_idx ON admin_audit (actor, ts DESC);

-- MATERIALIZED VIEWS FOR FAST READS
CREATE MATERIALIZED VIEW user_perf_mv AS
SELECT
  u.user_id,
  count(t.trade_id)                                          AS trades,
  sum((t.result='win')::int)                                 AS wins,
  sum((t.result='loss')::int)                                AS losses,
  sum((t.result='be')::int)                                  AS breakevens,
  avg(t.rr)                                                  AS avg_rr,
  avg(t.pips_net)                                            AS avg_pips,
  sum(t.pips_net)                                            AS pips_total,
  sum(t.pnl_ccy - coalesce(t.fees_ccy,0))                    AS pnl_total_ccy,
  100.0 * sum((t.result='win')::int) / nullif(count(t.*),0)  AS win_rate_pct,
  avg(t.duration_min)                                        AS avg_duration_min,
  max(t.ts_close)                                            AS last_trade_ts
FROM users u
LEFT JOIN trade_facts t ON t.user_id=u.user_id 
WHERE t.ts_close >= now() - interval '90 days' OR t.ts_close IS NULL
GROUP BY u.user_id;

CREATE UNIQUE INDEX user_perf_mv_uid_idx ON user_perf_mv (user_id);

-- Pattern and symbol performance breakdown
CREATE MATERIALIZED VIEW user_pattern_perf_mv AS
SELECT
  u.user_id,
  t.pattern,
  count(*) AS trades,
  sum((t.result='win')::int) AS wins,
  sum(t.pips_net) AS pips_total,
  sum(t.pnl_ccy) AS pnl_total,
  100.0 * sum((t.result='win')::int) / nullif(count(*),0) AS win_rate_pct
FROM users u
LEFT JOIN trade_facts t ON t.user_id=u.user_id
WHERE t.ts_close >= now() - interval '90 days'
GROUP BY u.user_id, t.pattern;

CREATE UNIQUE INDEX user_pattern_perf_mv_idx ON user_pattern_perf_mv (user_id, pattern);

CREATE MATERIALIZED VIEW user_symbol_perf_mv AS
SELECT
  u.user_id,
  t.symbol,
  count(*) AS trades,
  sum((t.result='win')::int) AS wins,
  sum(t.pips_net) AS pips_total,
  sum(t.pnl_ccy) AS pnl_total,
  100.0 * sum((t.result='win')::int) / nullif(count(*),0) AS win_rate_pct
FROM users u
LEFT JOIN trade_facts t ON t.user_id=u.user_id
WHERE t.ts_close >= now() - interval '90 days'
GROUP BY u.user_id, t.symbol;

CREATE UNIQUE INDEX user_symbol_perf_mv_idx ON user_symbol_perf_mv (user_id, symbol);

-- Best/worst performers view
CREATE MATERIALIZED VIEW user_best_worst_mv AS
WITH per_pair AS (
  SELECT user_id, symbol, sum(pnl_ccy) pnl, sum(pips_net) pips, count(*) n
  FROM trade_facts 
  WHERE ts_close >= now() - interval '90 days'
  GROUP BY user_id, symbol
),
per_pattern AS (
  SELECT user_id, pattern, sum(pnl_ccy) pnl, sum(pips_net) pips, count(*) n
  FROM trade_facts 
  WHERE ts_close >= now() - interval '90 days'
  GROUP BY user_id, pattern
)
SELECT
  u.user_id,
  (SELECT symbol  FROM per_pair    p WHERE p.user_id=u.user_id ORDER BY pnl DESC  NULLS LAST LIMIT 1) AS best_pair_by_pnl,
  (SELECT symbol  FROM per_pair    p WHERE p.user_id=u.user_id ORDER BY pnl ASC   NULLS LAST LIMIT 1) AS worst_pair_by_pnl,
  (SELECT pattern FROM per_pattern p WHERE p.user_id=u.user_id ORDER BY pnl DESC  NULLS LAST LIMIT 1) AS best_pattern_by_pnl,
  (SELECT pattern FROM per_pattern p WHERE p.user_id=u.user_id ORDER BY pnl ASC   NULLS LAST LIMIT 1) AS worst_pattern_by_pnl
FROM users u;

CREATE UNIQUE INDEX user_bw_mv_uid_idx ON user_best_worst_mv (user_id);

-- SINGLE READ VIEW FOR APP/ADMIN (the money shot)
CREATE VIEW user_profile_v AS
SELECT
  u.user_id, u.username, u.telegram_id, u.status, u.created_at,
  -- Settings (editable)
  s.tier, s.risk_mode, s.risk_per_trade_bp, s.max_concurrent, s.daily_dd_cap_bp, 
  s.slots, s.auto_fire_enabled, s.confidence_min, s.confidence_max, s.flags,
  -- Performance metrics (computed)
  p.trades, p.wins, p.losses, p.breakevens, p.avg_rr, p.avg_pips, 
  p.pips_total, p.pnl_total_ccy, p.win_rate_pct, p.avg_duration_min, p.last_trade_ts,
  -- Best/worst performers
  bw.best_pair_by_pnl, bw.worst_pair_by_pnl, bw.best_pattern_by_pnl, bw.worst_pattern_by_pnl,
  -- XP total (with override support)
  COALESCE(
    (SELECT (value->>'xp_total')::INT
       FROM user_overrides o
      WHERE o.user_id=u.user_id AND o.key='xp_total'
        AND (o.expires_at IS NULL OR o.expires_at>now())),
    (SELECT COALESCE(sum(points),0) FROM xp_events x WHERE x.user_id=u.user_id)
  ) AS xp_total,
  -- Account info
  a.broker, a.account_number, a.base_ccy, a.leverage
FROM users u
LEFT JOIN user_settings      s  ON s.user_id=u.user_id
LEFT JOIN user_perf_mv       p  ON p.user_id=u.user_id
LEFT JOIN user_best_worst_mv bw ON bw.user_id=u.user_id
LEFT JOIN accounts           a  ON a.user_id=u.user_id AND a.is_primary=true;

-- Initial data: Current BITTEN user
INSERT INTO users (telegram_id, username, status) 
VALUES (7176191872, 'COMMANDER_DEV', 'active');

INSERT INTO user_settings (user_id, tier, risk_mode, risk_per_trade_bp, max_concurrent, slots, auto_fire_enabled, confidence_min, confidence_max, flags)
SELECT user_id, 'COMMANDER', 'percent', 500, 10, 10, true, 80.0, 89.0, '{"bitmode": false}'
FROM users WHERE telegram_id = 7176191872;

-- Comments for documentation
COMMENT ON TABLE users IS 'Core user accounts and profile information';
COMMENT ON TABLE user_settings IS 'Admin-editable trading parameters and risk settings';
COMMENT ON TABLE trade_facts IS 'Immutable trade records fed by event bus from comprehensive_tracking.jsonl';
COMMENT ON TABLE user_ledger IS 'Financial transactions separate from trading P&L';
COMMENT ON TABLE xp_events IS 'Gamification points awarded for trading activities';
COMMENT ON TABLE user_overrides IS 'Temporary manual adjustments with expiry dates';
COMMENT ON TABLE admin_audit IS 'Complete audit trail of all administrative changes';
COMMENT ON VIEW user_profile_v IS 'Single source of truth view combining all user data for app/admin reads';