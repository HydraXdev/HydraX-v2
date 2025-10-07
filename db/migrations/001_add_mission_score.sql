-- Migration: Add mission_score column to signals table
-- Idempotent: Safe to run multiple times

-- Check if column exists and add if missing
-- SQLite doesn't support IF NOT EXISTS for columns, so we use a workaround

PRAGMA table_info(signals);

-- Add column (will fail gracefully if already exists)
ALTER TABLE signals ADD COLUMN mission_score REAL DEFAULT 0;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_signals_mission_score ON signals(mission_score);