#!/usr/bin/env python3
"""
Database bootstrap for clean BITTEN signal loop
Creates SQLite tables for users, missions, and fires
"""
import sqlite3
import os

DB = os.environ.get("BITTEN_DB", "bitten.db")

def bootstrap():
    conn = sqlite3.connect(DB)
    conn.executescript("""
    PRAGMA journal_mode=WAL;

    CREATE TABLE IF NOT EXISTS users(
      user_id TEXT PRIMARY KEY,
      tier TEXT,                 -- NIBBLER/FANG/COMMANDER
      risk_pct_default REAL,
      max_concurrent INTEGER,
      daily_dd_limit REAL,
      cooldown_s INTEGER,
      balance_cache REAL,
      xp INTEGER DEFAULT 0,
      streak INTEGER DEFAULT 0,
      last_fire_at INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS missions(
      mission_id TEXT PRIMARY KEY,
      signal_id TEXT,
      payload_json TEXT NOT NULL,
      tg_message_id INTEGER,
      status TEXT,               -- PENDING/FILLED/FAILED/TIMEOUT
      expires_at INTEGER,
      created_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS fires(
      fire_id TEXT PRIMARY KEY,
      mission_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      status TEXT,               -- SENT/FILLED/FAILED/TIMEOUT
      ticket INTEGER,
      price REAL,
      idem TEXT UNIQUE,
      created_at INTEGER,
      updated_at INTEGER
    );

    CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);
    CREATE INDEX IF NOT EXISTS idx_missions_expires ON missions(expires_at);
    CREATE INDEX IF NOT EXISTS idx_fires_user ON fires(user_id);
    CREATE INDEX IF NOT EXISTS idx_fires_mission ON fires(mission_id);
    CREATE INDEX IF NOT EXISTS idx_fires_idem ON fires(idem);
    """)
    conn.commit()
    conn.close()
    print(f"✅ Database ready: {DB}")

if __name__ == "__main__":
    bootstrap()