#!/usr/bin/env python3
"""
Fire Mode Database Schema and Management
Handles user fire mode preferences and slot management
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FireModeDatabase:
    """Manages fire mode settings and slot tracking"""

    def __init__(self, db_path: str = "/root/HydraX-v2/data/fire_modes.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # User fire mode settings
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_fire_modes (
                user_id TEXT PRIMARY KEY,
                current_mode TEXT DEFAULT 'SELECT',
                max_auto_slots INTEGER DEFAULT 75,
                auto_slots_in_use INTEGER DEFAULT 0,
                manual_slots_in_use INTEGER DEFAULT 0,
                last_mode_change TIMESTAMP,
                trading_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Slot tracking for both AUTO and MANUAL trades
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS active_slots (
                slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                slot_type TEXT NOT NULL DEFAULT 'MANUAL',  -- MANUAL or AUTO
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                status TEXT DEFAULT 'OPEN',
                FOREIGN KEY (user_id) REFERENCES user_fire_modes(user_id)
            )
        """
        )

        # Fire mode history for analytics
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fire_mode_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                old_mode TEXT,
                new_mode TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT
            )
        """
        )

        # Chaingun inventory
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chaingun_inventory (
                user_id TEXT PRIMARY KEY,
                chaingun_count INTEGER DEFAULT 0,
                last_awarded TIMESTAMP,
                total_earned INTEGER DEFAULT 0,
                total_used INTEGER DEFAULT 0
            )
        """
        )

        # Chaingun sessions
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chaingun_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                shots_fired INTEGER DEFAULT 0,
                max_risk_reached REAL DEFAULT 0.02,
                total_profit REAL DEFAULT 0,
                parachute_deployed BOOLEAN DEFAULT FALSE,
                end_reason TEXT,
                badge_earned TEXT
            )
        """
        )

        # Migration: Add new columns if they don't exist
        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN max_auto_slots INTEGER DEFAULT 75")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN auto_slots_in_use INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN manual_slots_in_use INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE active_slots ADD COLUMN slot_type TEXT DEFAULT 'MANUAL'")
        except sqlite3.OperationalError:
            pass

        # [DISABLED BITMODE]         # BITMODE Migration: Add BITMODE column
        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN bitmode_enabled BOOLEAN DEFAULT FALSE")
        except sqlite3.OperationalError:
            pass

        # Trading enabled migration: Add trading_enabled column
        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN trading_enabled BOOLEAN DEFAULT TRUE")
        except sqlite3.OperationalError:
            pass

        # Migrate old slots_in_use to auto_slots_in_use
        cursor.execute(
            """
            UPDATE user_fire_modes
            SET auto_slots_in_use = slots_in_use
            WHERE auto_slots_in_use = 0 AND slots_in_use > 0
        """
        )

        # Add CHECK constraint to prevent slot overflow
        try:
            cursor.execute(
                """
                CREATE TRIGGER prevent_auto_slot_overflow
                BEFORE UPDATE ON user_fire_modes
                FOR EACH ROW
                WHEN NEW.auto_slots_in_use > NEW.max_auto_slots
                BEGIN
                    SELECT RAISE(ABORT, 'Auto slots cannot exceed maximum');
                END
            """
            )
        except sqlite3.OperationalError:
            pass  # Trigger already exists

        # Fix any existing overflow issues
        cursor.execute(
            """
            UPDATE user_fire_modes
            SET auto_slots_in_use = MIN(auto_slots_in_use, max_auto_slots)
            WHERE auto_slots_in_use > max_auto_slots
        """
        )

        conn.commit()
        conn.close()
        logger.info("Fire mode database initialized with overflow protection")

    def get_user_mode(self, user_id: str) -> Dict:
        """Get user's current fire mode settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT current_mode, max_auto_slots, auto_slots_in_use, manual_slots_in_use, last_mode_change, bitmode_enabled, trading_enabled
                FROM user_fire_modes
                WHERE user_id = ?
            """,
                (user_id,),
            )

            result = cursor.fetchone()

            if result:
                conn.close()
                return {
                    "current_mode": result[0],
                    "max_auto_slots": result[1],
                    "auto_slots_in_use": result[2],
                    "manual_slots_in_use": result[3],
                    "last_mode_change": result[4],
                    "bitmode_enabled": bool(result[5]) if len(result) > 5 else False,
                    "trading_enabled": bool(result[6]) if len(result) > 6 else True,
                    # For backward compatibility
                    "max_slots": result[1],
                    "slots_in_use": result[2],
                }
            else:
                # Create default entry - CRITICAL FIX: Keep connection open
                logger.info(f"Creating default fire mode entry for new user {user_id}")
                cursor.execute(
                    """
                    INSERT INTO user_fire_modes (user_id, current_mode, max_auto_slots, auto_slots_in_use, manual_slots_in_use)
                    VALUES (?, 'SELECT', 75, 0, 0)
                """,
                    (user_id,),
                )
                conn.commit()
                conn.close()
                return {
                    "current_mode": "SELECT",
                    "max_auto_slots": 75,
                    "auto_slots_in_use": 0,
                    "manual_slots_in_use": 0,
                    "last_mode_change": None,
                    "bitmode_enabled": False,
                    "trading_enabled": True,
                    # For backward compatibility
                    "max_slots": 75,
                    "slots_in_use": 0,
                }
        except Exception as e:
            logger.error(f"Critical error in get_user_mode for user {user_id}: {e}")
            conn.close()
            # Return safe defaults to prevent total failure
            return {"current_mode": "SELECT", "max_slots": 1, "slots_in_use": 0, "last_mode_change": None}

    def set_user_mode(self, user_id: str, new_mode: str, reason: str = None) -> bool:
        """Set user's fire mode"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current mode for history without recursion
            cursor.execute("SELECT current_mode FROM user_fire_modes WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            old_mode = result[0] if result else "SELECT"

            # Update or insert mode
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_fire_modes
                (user_id, current_mode, last_mode_change, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                (user_id, new_mode),
            )

            # Record history
            cursor.execute(
                """
                INSERT INTO fire_mode_history (user_id, old_mode, new_mode, reason)
                VALUES (?, ?, ?, ?)
            """,
                (user_id, old_mode, new_mode, reason),
            )

            conn.commit()
            conn.close()

            logger.info(f"User {user_id} fire mode changed from {old_mode} to {new_mode}")
            return True

        except Exception as e:
            logger.error(f"Error setting fire mode: {e}")
            conn.close()
            return False

    @staticmethod
    def get_tier_slot_limits(tier: str) -> Dict[str, int]:
        """Get maximum allowed slots based on user tier"""
        tier_limits = {
            "NIBBLER": {"manual": 1, "auto": 0, "total": 1, "trades_per_day": 6},
            "FANG": {"manual": 2, "auto": 0, "total": 2, "trades_per_day": 10},
            "COMMANDER": {"manual": 10, "auto": 10, "total": 10, "trades_per_day": 999999},
        }
        return tier_limits.get(tier.upper(), {"manual": 1, "auto": 0, "total": 1, "trades_per_day": 6})

    def set_max_auto_slots(self, user_id: str, max_slots: int, user_tier: str = "COMMANDER") -> bool:
        """Set user's maximum auto slots (only for COMMANDER tier)"""
        limits = self.get_tier_slot_limits(user_tier)
        max_allowed = limits["auto"]

        if user_tier != "COMMANDER":
            logger.error(f"Only COMMANDER tier can set auto slots")
            return False

        if max_slots < 1 or max_slots > max_allowed:
            logger.error(f"Invalid max_slots value: {max_slots} (max allowed for {user_tier}: {max_allowed})")
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE user_fire_modes
                SET max_auto_slots = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """,
                (max_slots, user_id),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error setting max slots: {e}")
            conn.close()
            return False

    def check_slot_available(self, user_id: str, slot_type: str = "AUTO", user_tier: str = "COMMANDER") -> bool:
        """Check if user has available slot for specified type"""
        mode_info = self.get_user_mode(user_id)
        limits = self.get_tier_slot_limits(user_tier)

        if slot_type == "AUTO":
            # Auto slots only for COMMANDER in AUTO mode
            if user_tier != "COMMANDER" or mode_info["current_mode"] != "AUTO":
                return False
            return mode_info["auto_slots_in_use"] < mode_info["max_auto_slots"]
        else:  # MANUAL
            # Check manual slot limit based on tier
            return mode_info["manual_slots_in_use"] < limits["manual"]

    def occupy_slot(
        self, user_id: str, mission_id: str, symbol: str, slot_type: str = "AUTO", user_tier: str = "COMMANDER"
    ) -> bool:
        """Occupy a slot for trade (AUTO or MANUAL)"""
        if not self.check_slot_available(user_id, slot_type, user_tier):
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Add active slot with type
            cursor.execute(
                """
                INSERT INTO active_slots (user_id, mission_id, symbol, slot_type)
                VALUES (?, ?, ?, ?)
            """,
                (user_id, mission_id, symbol, slot_type),
            )

            # Increment appropriate slot counter WITH BOUNDS CHECK
            if slot_type == "AUTO":
                cursor.execute(
                    """
                    UPDATE user_fire_modes
                    SET auto_slots_in_use = MIN(auto_slots_in_use + 1, max_auto_slots),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
            else:  # MANUAL
                # Get tier limit for bounds check
                limits = self.get_tier_slot_limits(user_tier)
                max_manual = limits["manual"]
                cursor.execute(
                    """
                    UPDATE user_fire_modes
                    SET manual_slots_in_use = MIN(manual_slots_in_use + 1, ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """,
                    (max_manual, user_id),
                )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error occupying slot: {e}")
            conn.close()
            return False

    def release_slot(self, user_id: str, mission_id: str) -> bool:
        """Release a slot when trade closes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # First get the slot type before closing
            cursor.execute(
                """
                SELECT slot_type FROM active_slots
                WHERE user_id = ? AND mission_id = ? AND status = 'OPEN'
            """,
                (user_id, mission_id),
            )

            result = cursor.fetchone()
            if not result:
                logger.warning(f"No open slot found for user {user_id}, mission {mission_id}")
                conn.close()
                return False

            slot_type = result[0]

            # Mark slot as closed
            cursor.execute(
                """
                UPDATE active_slots
                SET status = 'CLOSED', closed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND mission_id = ? AND status = 'OPEN'
            """,
                (user_id, mission_id),
            )

            # Decrement appropriate slot counter
            if slot_type == "AUTO":
                cursor.execute(
                    """
                    UPDATE user_fire_modes
                    SET auto_slots_in_use = MAX(0, auto_slots_in_use - 1),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
            else:  # MANUAL
                cursor.execute(
                    """
                    UPDATE user_fire_modes
                    SET manual_slots_in_use = MAX(0, manual_slots_in_use - 1),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """,
                    (user_id,),
                )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error releasing slot: {e}")
            conn.close()
            return False

    def get_active_slots(self, user_id: str) -> List[Dict]:
        """Get user's active slots"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT slot_id, mission_id, symbol, opened_at, slot_type
            FROM active_slots
            WHERE user_id = ? AND status = 'OPEN'
            ORDER BY opened_at DESC
        """,
            (user_id,),
        )

        slots = []
        for row in cursor.fetchall():
            slots.append(
                {
                    "slot_id": row[0],
                    "mission_id": row[1],
                    "symbol": row[2],
                    "opened_at": row[3],
                    "slot_type": row[4] if len(row) > 4 else "MANUAL",
                }
            )

        conn.close()
        return slots

    def get_chaingun_inventory(self, user_id: str) -> int:
        """Get user's chaingun inventory count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT chaingun_count FROM chaingun_inventory WHERE user_id = ?
        """,
            (user_id,),
        )

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0

    def award_chaingun(self, user_id: str, count: int = 1) -> bool:
        """Award chaingun(s) to user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO chaingun_inventory (user_id, chaingun_count, total_earned)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    chaingun_count = chaingun_count + ?,
                    total_earned = total_earned + ?,
                    last_awarded = CURRENT_TIMESTAMP
            """,
                (user_id, count, count, count, count),
            )

            conn.commit()
            conn.close()
            logger.info(f"Awarded {count} chaingun(s) to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error awarding chaingun: {e}")
            conn.close()
            return False

    def toggle_bitmode(self, user_id: str, enabled: bool, user_tier: str = "COMMANDER") -> bool:
        # [DISABLED BITMODE]         """Toggle BITMODE for user (FANG+ tiers only)"""
        # [DISABLED BITMODE]         # Only FANG+ tiers can use BITMODE
        allowed_tiers = ["FANG", "COMMANDER"]
        if user_tier not in allowed_tiers:
            # [DISABLED BITMODE]             logger.error(f"BITMODE not available for tier {user_tier} - FANG+ required")
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_fire_modes
                (user_id, bitmode_enabled, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    bitmode_enabled = excluded.bitmode_enabled,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (user_id, enabled),
            )

            conn.commit()
            conn.close()

            # [DISABLED BITMODE]             logger.info(f"User {user_id} BITMODE {'enabled' if enabled else 'disabled'}")
            return True

        except Exception as e:
            # [DISABLED BITMODE]             logger.error(f"Error toggling BITMODE: {e}")
            conn.close()
            return False

    def is_bitmode_enabled(self, user_id: str) -> bool:
        # [DISABLED BITMODE]         """Check if BITMODE is enabled for user"""
        user_mode = self.get_user_mode(user_id)
        return user_mode.get("bitmode_enabled", False)

    def get_all_users(self) -> List[str]:
        """Get all user_ids that have fire mode settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT user_id FROM user_fire_modes")
            results = cursor.fetchall()
            conn.close()

            return [row[0] for row in results] if results else []

        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    def set_trading_enabled(self, user_id: str, enabled: bool) -> bool:
        """Enable or disable trading for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update or insert user trading status
            cursor.execute(
                """
                INSERT INTO user_fire_modes (user_id, trading_enabled, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    trading_enabled = excluded.trading_enabled,
                    updated_at = excluded.updated_at
            """,
                (user_id, enabled),
            )

            conn.commit()
            conn.close()

            logger.info(f"User {user_id} trading {'enabled' if enabled else 'disabled'}")
            return True

        except Exception as e:
            logger.error(f"Error setting trading status for {user_id}: {e}")
            return False

    def is_trading_enabled(self, user_id: str) -> bool:
        """Check if trading is enabled for user"""
        user_mode = self.get_user_mode(user_id)
        return user_mode.get("trading_enabled", True)

    def get_real_time_slot_usage(self, user_id: str) -> Dict[str, int]:
        """Get real-time slot usage from EA event bus (positions_live table)"""
        # Connect to the main bitten.db for real EA data
        bitten_db_path = "/root/HydraX-v2/bitten.db"
        conn = sqlite3.connect(bitten_db_path)
        cursor = conn.cursor()

        try:
            # Count actual open positions from EA event bus
            cursor.execute(
                """
                SELECT COUNT(*) as total_positions
                FROM positions_live
                WHERE user_id = ?
            """,
                (user_id,),
            )

            result = cursor.fetchone()
            total_open = result[0] or 0
            conn.close()

            # For now, treat all positions as manual since we need to distinguish
            # auto vs manual in the positions_live table schema
            # TODO: Add fire_mode column to positions_live table to track auto vs manual
            return {
                "manual_slots_used": total_open,  # All counted as manual for now
                "auto_slots_used": 0,  # Need to enhance positions_live to track this
                "total_slots_used": total_open,
            }

        except Exception as e:
            logger.error(f"Error getting real-time slot usage from EA event bus for {user_id}: {e}")
            if conn:
                conn.close()
            return {"manual_slots_used": 0, "auto_slots_used": 0, "total_slots_used": 0}

    def check_daily_trade_limit(self, user_id: str, user_tier: str) -> Dict[str, any]:
        """Check if user has exceeded daily trade limit with session-based reset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current trading session start time (Sunday 5PM EST = 22:00 UTC)
            from datetime import datetime, timedelta, timezone

            now = datetime.now(timezone.utc)

            # Calculate current trading week start (Sunday 22:00 UTC)
            days_since_sunday = (now.weekday() + 1) % 7  # Monday = 0, Sunday = 6
            hours_since_sunday_start = days_since_sunday * 24 + now.hour

            if now.weekday() == 6 and now.hour >= 22:  # After Sunday 22:00 UTC
                session_start = now.replace(hour=22, minute=0, second=0, microsecond=0)
            elif hours_since_sunday_start >= (6 * 24 + 22):  # After current week Sunday 22:00
                session_start = now.replace(hour=22, minute=0, second=0, microsecond=0) - timedelta(
                    days=days_since_sunday
                )
            else:  # Before this week's Sunday 22:00, use last week
                session_start = now.replace(hour=22, minute=0, second=0, microsecond=0) - timedelta(
                    days=days_since_sunday + 7
                )

            session_start_timestamp = int(session_start.timestamp())

            # Get user's tier limits
            tier_limits = self.get_tier_slot_limits(user_tier)
            max_trades = tier_limits["trades_per_day"]

            # Count trades since session start
            cursor.execute(
                """
                SELECT COUNT(*) FROM active_slots
                WHERE user_id = ? AND opened_at >= ?
            """,
                (user_id, session_start_timestamp),
            )

            trades_used = cursor.fetchone()[0] or 0

            conn.close()

            return {
                "trades_used": trades_used,
                "max_trades": max_trades,
                "can_trade": trades_used < max_trades,
                "session_start": session_start.isoformat(),
                "unlimited": max_trades >= 999999,
            }

        except Exception as e:
            logger.error(f"Error checking daily trade limit for {user_id}: {e}")
            conn.close()
            return {"trades_used": 0, "max_trades": 6, "can_trade": True, "session_start": "", "unlimited": False}

    def can_user_fire_trade(self, user_id: str, trade_type: str = "MANUAL") -> Dict[str, any]:
        """Comprehensive check if user can fire a trade based on tier, slots, and daily limits"""
        try:
            # Get user tier
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT subscription_tier FROM user_fire_modes WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            user_tier = result[0] if result else "NIBBLER"
            conn.close()

            # Get tier limits
            tier_limits = self.get_tier_slot_limits(user_tier)

            # Check slot availability
            current_usage = self.get_real_time_slot_usage(user_id)

            # For COMMANDER tier, they have 10 slots that can be used for either manual or auto
            if user_tier == "COMMANDER":
                slots_available = current_usage["total_slots_used"] < tier_limits["total"]
                if trade_type == "AUTO" and user_tier != "COMMANDER":
                    slots_available = False  # Only COMMANDER can auto-fire
            else:
                # For NIBBLER/FANG, check specific slot types
                if trade_type == "AUTO":
                    slots_available = False  # No auto-fire for NIBBLER/FANG
                else:
                    slots_available = current_usage["manual_slots_used"] < tier_limits["manual"]

            # Check daily trade limit
            daily_limit_check = self.check_daily_trade_limit(user_id, user_tier)

            # Auto-fire availability
            auto_fire_available = user_tier == "COMMANDER" and trade_type == "AUTO"

            return {
                "can_fire": slots_available and daily_limit_check["can_trade"],
                "tier": user_tier,
                "slots_available": slots_available,
                "daily_limit_ok": daily_limit_check["can_trade"],
                "auto_fire_available": auto_fire_available,
                "current_usage": current_usage,
                "daily_stats": daily_limit_check,
                "tier_limits": tier_limits,
                "reasons": {
                    "slots_full": not slots_available,
                    "daily_limit_exceeded": not daily_limit_check["can_trade"],
                    "auto_fire_not_allowed": trade_type == "AUTO" and user_tier != "COMMANDER",
                },
            }

        except Exception as e:
            logger.error(f"Error checking if user {user_id} can fire trade: {e}")
            return {
                "can_fire": False,
                "tier": "NIBBLER",
                "slots_available": False,
                "daily_limit_ok": False,
                "auto_fire_available": False,
                "error": str(e),
            }

    def get_user_tier_summary(self, user_id: str) -> Dict[str, any]:
        """Get comprehensive tier information for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT subscription_tier, max_manual_slots, max_auto_slots_separate,
                       tier_max_trades_per_day, auto_fire_enabled, current_mode
                FROM user_fire_modes
                WHERE user_id = ?
            """,
                (user_id,),
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                tier = result[0]
                tier_limits = self.get_tier_slot_limits(tier)
                current_usage = self.get_real_time_slot_usage(user_id)
                daily_check = self.check_daily_trade_limit(user_id, tier)

                return {
                    "tier": tier,
                    "auto_fire_enabled": bool(result[4]),
                    "current_mode": result[5],
                    "limits": tier_limits,
                    "current_usage": current_usage,
                    "daily_stats": daily_check,
                    "available_slots": {
                        "manual": tier_limits["manual"] - current_usage["manual_slots_used"],
                        "auto": tier_limits["auto"] - current_usage["auto_slots_used"] if tier == "COMMANDER" else 0,
                        "total": tier_limits["total"] - current_usage["total_slots_used"],
                    },
                }
            else:
                return {
                    "tier": "NIBBLER",
                    "auto_fire_enabled": False,
                    "current_mode": "SELECT",
                    "limits": self.get_tier_slot_limits("NIBBLER"),
                    "error": "User not found",
                }

        except Exception as e:
            logger.error(f"Error getting tier summary for {user_id}: {e}")
            return {"tier": "NIBBLER", "error": str(e)}


# Create singleton instance
fire_mode_db = FireModeDatabase()
