-- Migration 001: Add HydraSocket sequencing support
-- Adds seq (per-account monotonic) and ingest_time fields

-- Step 1: Add new columns
ALTER TABLE events ADD COLUMN seq INTEGER;
ALTER TABLE events ADD COLUMN account_id TEXT;
ALTER TABLE events ADD COLUMN ingest_time REAL;

-- Step 2: Backfill existing data
-- Set account_id from user_id where available
UPDATE events SET account_id = user_id WHERE user_id IS NOT NULL;
UPDATE events SET account_id = 'unknown' WHERE account_id IS NULL;

-- Set ingest_time to created_at for existing records
UPDATE events SET ingest_time = created_at WHERE ingest_time IS NULL;

-- Step 3: Add seq values (monotonic per account)
-- For existing data, use id as temporary seq (will be fixed by proper sequencer)
UPDATE events SET seq = id WHERE seq IS NULL;

-- Step 4: Create required indexes
CREATE INDEX idx_events_account_seq ON events(account_id, seq);
CREATE INDEX idx_events_account_ingest_time ON events(account_id, ingest_time);
CREATE INDEX idx_events_account_id ON events(account_id);

-- Step 5: Create sequence tracking table
CREATE TABLE IF NOT EXISTS account_sequences (
    account_id TEXT PRIMARY KEY,
    last_seq INTEGER NOT NULL DEFAULT 0,
    updated_at REAL NOT NULL
);

-- Initialize sequences for existing accounts
INSERT OR REPLACE INTO account_sequences (account_id, last_seq, updated_at)
SELECT account_id, MAX(seq), strftime('%s', 'now')
FROM events
WHERE account_id IS NOT NULL
GROUP BY account_id;