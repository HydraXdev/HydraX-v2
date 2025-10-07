"""
Auto-Fire Profile Manager
=========================
Per-user customizable auto-fire profiles with default settings.
Each user can have their own optimized trading parameters.

Created: September 16, 2025
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AutoFireProfileManager:
    """
    Manages per-user auto-fire profiles with customizable filters
    for pairs, patterns, and confidence ranges.
    """

    def __init__(self, db_path: str = "/root/HydraX-v2/data/auto_fire_profiles.db"):
        self.db_path = db_path
        self._init_database()
        self._ensure_default_profile()

    def _init_database(self):
        """Initialize the database tables for user profiles."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Main profile table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_name TEXT DEFAULT 'custom',
                    allowed_pairs TEXT,  -- JSON array
                    blocked_pairs TEXT,  -- JSON array
                    allowed_patterns TEXT,  -- JSON array
                    blocked_patterns TEXT,  -- JSON array
                    min_confidence REAL DEFAULT 80.0,
                    max_confidence REAL DEFAULT 89.0,
                    optimal_confidence_min REAL DEFAULT 80.0,
                    optimal_confidence_max REAL DEFAULT 84.0,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_performance_update TIMESTAMP,
                    total_signals INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    total_losses INTEGER DEFAULT 0,
                    notes TEXT
                )
            """
            )

            # Performance tracking table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS profile_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    signal_id TEXT,
                    symbol TEXT,
                    pattern_type TEXT,
                    confidence REAL,
                    outcome TEXT,
                    pips_result REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """
            )

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_user ON profile_performance(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON profile_performance(timestamp)")

            conn.commit()

    def _ensure_default_profile(self):
        """Ensure the DEFAULT profile exists for new users."""
        default_allowed_pairs = ["USDCNH", "XAUUSD", "USDJPY", "EURJPY", "GBPCAD", "NZDUSD", "EURAUD"]

        default_blocked_pairs = ["GBPJPY", "GBPUSD", "EURUSD"]

        default_allowed_patterns = ["KALMAN_QUICKFIRE", "BB_SCALP"]

        default_blocked_patterns = ["FAIR_VALUE_GAP_FILL", "ORDER_BLOCK_BOUNCE"]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if DEFAULT profile exists
            cursor.execute("SELECT user_id FROM user_profiles WHERE user_id = 'DEFAULT'")
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO user_profiles (
                        user_id, profile_name,
                        allowed_pairs, blocked_pairs,
                        allowed_patterns, blocked_patterns,
                        min_confidence, max_confidence,
                        optimal_confidence_min, optimal_confidence_max,
                        notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        "DEFAULT",
                        "Standard Profile",
                        json.dumps(default_allowed_pairs),
                        json.dumps(default_blocked_pairs),
                        json.dumps(default_allowed_patterns),
                        json.dumps(default_blocked_patterns),
                        80.0,
                        89.0,
                        80.0,
                        84.0,
                        "Default profile based on 12-hour performance analysis",
                    ),
                )
                conn.commit()

    def get_user_profile(self, user_id: str) -> Dict:
        """
        Get user's auto-fire profile, creating from DEFAULT if doesn't exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Try to get user's profile
            cursor.execute(
                """
                SELECT * FROM user_profiles WHERE user_id = ?
            """,
                (user_id,),
            )

            row = cursor.fetchone()

            if not row:
                # Create profile from DEFAULT
                cursor.execute(
                    """
                    SELECT * FROM user_profiles WHERE user_id = 'DEFAULT'
                """
                )
                default_row = cursor.fetchone()

                if default_row:
                    # Copy DEFAULT profile for this user
                    cursor.execute(
                        """
                        INSERT INTO user_profiles (
                            user_id, profile_name,
                            allowed_pairs, blocked_pairs,
                            allowed_patterns, blocked_patterns,
                            min_confidence, max_confidence,
                            optimal_confidence_min, optimal_confidence_max,
                            notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            user_id,
                            f"Profile for {user_id}",
                            default_row[2],
                            default_row[3],  # allowed/blocked pairs
                            default_row[4],
                            default_row[5],  # allowed/blocked patterns
                            default_row[6],
                            default_row[7],  # min/max confidence
                            default_row[8],
                            default_row[9],  # optimal confidence range
                            f"Created from DEFAULT profile on {datetime.now().isoformat()}",
                        ),
                    )
                    conn.commit()

                    # Fetch the newly created profile
                    cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
                    row = cursor.fetchone()

            if row:
                return {
                    "user_id": row[0],
                    "profile_name": row[1],
                    "allowed_pairs": json.loads(row[2]) if row[2] else [],
                    "blocked_pairs": json.loads(row[3]) if row[3] else [],
                    "allowed_patterns": json.loads(row[4]) if row[4] else [],
                    "blocked_patterns": json.loads(row[5]) if row[5] else [],
                    "min_confidence": row[6],
                    "max_confidence": row[7],
                    "optimal_confidence_min": row[8],
                    "optimal_confidence_max": row[9],
                    "enabled": bool(row[10]),
                    "total_signals": row[14],
                    "total_wins": row[15],
                    "total_losses": row[16],
                    "win_rate": (row[15] / (row[15] + row[16]) * 100) if (row[15] + row[16]) > 0 else None,
                    "notes": row[17],
                }

            return None

    def should_auto_fire(self, user_id: str, signal_data: Dict) -> Tuple[bool, str]:
        """
        Determine if a signal should auto-fire for a specific user.

        Args:
            user_id: The user to check
            signal_data: Signal information (symbol, pattern_type, confidence)

        Returns:
            Tuple of (should_fire: bool, reason: str)
        """
        profile = self.get_user_profile(user_id)

        if not profile:
            return False, "No profile found"

        if not profile["enabled"]:
            return False, "Profile disabled"

        symbol = signal_data.get("symbol", "")
        pattern = signal_data.get("pattern_type", "")
        confidence = float(signal_data.get("confidence", 0))

        # Check blocked pairs
        if symbol in profile["blocked_pairs"]:
            return False, f"Pair {symbol} blocked for user {user_id}"

        # Check blocked patterns
        if pattern in profile["blocked_patterns"]:
            return False, f"Pattern {pattern} blocked for user {user_id}"

        # Check allowed pairs (if list is not empty)
        if profile["allowed_pairs"] and symbol not in profile["allowed_pairs"]:
            return False, f"Pair {symbol} not in allowed list for user {user_id}"

        # Check allowed patterns (if list is not empty)
        if profile["allowed_patterns"] and pattern not in profile["allowed_patterns"]:
            return False, f"Pattern {pattern} not in allowed list for user {user_id}"

        # Check confidence range
        if not (profile["min_confidence"] <= confidence <= profile["max_confidence"]):
            return (
                False,
                f"Confidence {confidence}% outside range {profile['min_confidence']}-{profile['max_confidence']}%",
            )

        # Check if in optimal range (bonus info)
        if profile["optimal_confidence_min"] <= confidence <= profile["optimal_confidence_max"]:
            return True, f"Optimal confidence range for user {user_id}"

        return True, f"Within allowed parameters for user {user_id}"

    def update_profile(self, user_id: str, updates: Dict) -> bool:
        """
        Update a user's profile settings.

        Args:
            user_id: User to update (or 'DEFAULT' to update default)
            updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        allowed_fields = {
            "allowed_pairs",
            "blocked_pairs",
            "allowed_patterns",
            "blocked_patterns",
            "min_confidence",
            "max_confidence",
            "optimal_confidence_min",
            "optimal_confidence_max",
            "enabled",
            "notes",
        }

        # Filter updates to allowed fields
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            return False

        # Convert lists to JSON for storage
        for field in ["allowed_pairs", "blocked_pairs", "allowed_patterns", "blocked_patterns"]:
            if field in filtered_updates and isinstance(filtered_updates[field], list):
                filtered_updates[field] = json.dumps(filtered_updates[field])

        # Build UPDATE query
        set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
        values = list(filtered_updates.values())
        values.append(user_id)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE user_profiles
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """,
                values,
            )
            conn.commit()

            return cursor.rowcount > 0

    def add_blocked_pair(self, user_id: str, pair: str) -> bool:
        """Add a pair to user's blocked list."""
        profile = self.get_user_profile(user_id)
        if profile:
            blocked = profile["blocked_pairs"]
            if pair not in blocked:
                blocked.append(pair)
                return self.update_profile(user_id, {"blocked_pairs": blocked})
        return False

    def remove_blocked_pair(self, user_id: str, pair: str) -> bool:
        """Remove a pair from user's blocked list."""
        profile = self.get_user_profile(user_id)
        if profile:
            blocked = profile["blocked_pairs"]
            if pair in blocked:
                blocked.remove(pair)
                return self.update_profile(user_id, {"blocked_pairs": blocked})
        return False

    def record_performance(self, user_id: str, signal_data: Dict, outcome: str, pips: float = 0):
        """
        Record the performance of an auto-fired signal.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Record in performance table
            cursor.execute(
                """
                INSERT INTO profile_performance
                (user_id, signal_id, symbol, pattern_type, confidence, outcome, pips_result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    signal_data.get("signal_id"),
                    signal_data.get("symbol"),
                    signal_data.get("pattern_type"),
                    signal_data.get("confidence"),
                    outcome,
                    pips,
                ),
            )

            # Update profile statistics
            if outcome == "WIN":
                cursor.execute(
                    """
                    UPDATE user_profiles
                    SET total_wins = total_wins + 1,
                        total_signals = total_signals + 1,
                        last_performance_update = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
            elif outcome == "LOSS":
                cursor.execute(
                    """
                    UPDATE user_profiles
                    SET total_losses = total_losses + 1,
                        total_signals = total_signals + 1,
                        last_performance_update = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """,
                    (user_id,),
                )

            conn.commit()

    def get_performance_summary(self, user_id: str, hours: int = 24) -> Dict:
        """Get performance summary for a user over specified hours."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                    SUM(pips_result) as net_pips,
                    AVG(confidence) as avg_confidence
                FROM profile_performance
                WHERE user_id = ?
                AND timestamp > datetime('now', '-' || ? || ' hours')
            """,
                (user_id, hours),
            )

            row = cursor.fetchone()
            if row:
                total = row[0]
                wins = row[1] or 0
                losses = row[2] or 0

                return {
                    "total_signals": total,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": (wins / (wins + losses) * 100) if (wins + losses) > 0 else None,
                    "net_pips": row[3] or 0,
                    "avg_confidence": row[4] or 0,
                }

            return {"total_signals": 0, "wins": 0, "losses": 0, "win_rate": None}


# Create global instance
profile_manager = AutoFireProfileManager()
