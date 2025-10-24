-- ============================================================================
-- NORMAN'S NOTEBOOK - DATABASE MIGRATION
-- Migration: 001_create_notebook_tables.sql
-- Date: 2025-10-15
-- Purpose: Create all tables for Norman's Notebook system
-- ============================================================================

-- Table 1: notebook_entries
-- Stores all user journal entries with metadata
CREATE TABLE IF NOT EXISTS notebook_entries (
    entry_id TEXT PRIMARY KEY,              -- UUID for entry
    user_id TEXT NOT NULL,                  -- User identification (Firebase UID)
    title TEXT NOT NULL,                    -- Entry title
    content TEXT NOT NULL,                  -- Markdown content
    category TEXT,                          -- strategy, analysis, lesson, goal, general
    tags TEXT,                              -- JSON array of tags
    symbol TEXT,                            -- Trading pair (EURUSD, GBPUSD, etc.)
    trade_id TEXT,                          -- Mission/fire ID if linked to trade
    created_at INTEGER NOT NULL,            -- Unix timestamp
    updated_at INTEGER NOT NULL,            -- Unix timestamp
    pinned INTEGER DEFAULT 0,               -- 0=unpinned, 1=pinned
    emotional_state TEXT,                   -- excited, anxious, angry, confident, defeated, focused

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_user_entries ON notebook_entries(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_symbol_notes ON notebook_entries(symbol, user_id);
CREATE INDEX IF NOT EXISTS idx_trade_notes ON notebook_entries(trade_id);
CREATE INDEX IF NOT EXISTS idx_pinned_notes ON notebook_entries(user_id, pinned);
CREATE INDEX IF NOT EXISTS idx_category_notes ON notebook_entries(user_id, category);

-- ============================================================================

-- Table 2: story_progression
-- Tracks user's progress through Norman's story chapters
CREATE TABLE IF NOT EXISTS story_progression (
    user_id TEXT PRIMARY KEY,               -- User identification (Firebase UID)
    current_chapter TEXT NOT NULL,          -- Current chapter key (discovery, first_bite, etc.)
    total_trades INTEGER DEFAULT 0,         -- Total trades executed (for unlocking)
    chapters_unlocked TEXT,                 -- JSON array of unlocked chapter keys
    last_updated INTEGER NOT NULL,          -- Unix timestamp

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_story_user ON story_progression(user_id);

-- ============================================================================

-- Table 3: extracted_insights
-- Stores AI-extracted patterns and insights from journal entries
CREATE TABLE IF NOT EXISTS extracted_insights (
    insight_id TEXT PRIMARY KEY,            -- UUID for insight
    user_id TEXT NOT NULL,                  -- User identification (Firebase UID)
    insight_text TEXT NOT NULL,             -- Extracted pattern/lesson text
    source_entry_id TEXT,                   -- Origin journal entry
    category TEXT,                          -- pattern, mistake, success, principle
    confidence REAL,                        -- 0.0-1.0 ML confidence score
    created_at INTEGER NOT NULL,            -- Unix timestamp
    times_referenced INTEGER DEFAULT 0,     -- Usage tracking counter

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (source_entry_id) REFERENCES notebook_entries(entry_id)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_user_insights ON extracted_insights(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_category_insights ON extracted_insights(user_id, category);
CREATE INDEX IF NOT EXISTS idx_source_insights ON extracted_insights(source_entry_id);

-- ============================================================================

-- Verification: Check that tables were created
SELECT 'notebook_entries table created' as status
FROM sqlite_master
WHERE type='table' AND name='notebook_entries';

SELECT 'story_progression table created' as status
FROM sqlite_master
WHERE type='table' AND name='story_progression';

SELECT 'extracted_insights table created' as status
FROM sqlite_master
WHERE type='table' AND name='extracted_insights';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
