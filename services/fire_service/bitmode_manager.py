#!/usr/bin/env python3
"""
BITMODE v2 Manager
Hybrid position management: 25%/25%/50% strategy
"""

import logging
import sqlite3
from typing import Dict, Optional
from config import config
from models import HybridConfig

logger = logging.getLogger(__name__)


class BitmodeManager:
    """Manages BITMODE v2 hybrid position configuration"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(config.FIRE_MODE_DB)
        self._ensure_bitmode_column()

    def _ensure_bitmode_column(self):
        """Ensure bitmode_enabled column exists in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if column exists
            cursor.execute("PRAGMA table_info(user_fire_modes)")
            columns = [row[1] for row in cursor.fetchall()]

            if "bitmode_enabled" not in columns:
                cursor.execute(
                    "ALTER TABLE user_fire_modes ADD COLUMN bitmode_enabled BOOLEAN DEFAULT FALSE"
                )
                conn.commit()
                logger.info("Added bitmode_enabled column to user_fire_modes")

            conn.close()
        except Exception as e:
            logger.error(f"Error ensuring BITMODE column: {e}")

    def is_bitmode_enabled(self, user_id: str) -> bool:
        """
        Check if BITMODE is enabled for user

        Args:
            user_id: User ID

        Returns:
            True if BITMODE enabled, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT bitmode_enabled FROM user_fire_modes WHERE user_id = ?",
                (user_id,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return bool(result[0])

            return False

        except Exception as e:
            logger.error(f"Error checking BITMODE status: {e}")
            return False

    def toggle_bitmode(self, user_id: str, enabled: bool, user_tier: str = "COMMANDER") -> bool:
        """
        Toggle BITMODE for user (FANG+ tiers only)

        Args:
            user_id: User ID
            enabled: Enable or disable BITMODE
            user_tier: User subscription tier

        Returns:
            True if successful, False otherwise
        """
        # Only FANG+ tiers can use BITMODE
        allowed_tiers = ["FANG", "COMMANDER"]
        if user_tier not in allowed_tiers:
            logger.error(f"BITMODE not available for tier {user_tier} - FANG+ required")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO user_fire_modes
                (user_id, bitmode_enabled, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    bitmode_enabled = excluded.bitmode_enabled,
                    updated_at = excluded.updated_at
                """,
                (user_id, enabled)
            )

            conn.commit()
            conn.close()

            logger.info(f"User {user_id} BITMODE {'enabled' if enabled else 'disabled'}")
            return True

        except Exception as e:
            logger.error(f"Error toggling BITMODE: {e}")
            return False

    def get_bitmode_config(self, symbol: str) -> HybridConfig:
        """
        Get BITMODE hybrid configuration for symbol

        Args:
            symbol: Trading pair

        Returns:
            HybridConfig with position management rules
        """
        # Get symbol-specific pip values
        pip_size = config.get_pip_size(symbol)

        # Calculate trigger distances in price
        # For EURUSD: 8 pips = 0.0008, 12 pips = 0.0012
        # For USDJPY: 8 pips = 0.08, 12 pips = 0.12
        partial1_trigger = config.BITMODE_PARTIAL1_TRIGGER
        partial2_trigger = config.BITMODE_PARTIAL2_TRIGGER
        trail_distance = config.BITMODE_TRAIL_DISTANCE

        hybrid_config = HybridConfig(
            enabled=True,
            partial1={
                "trigger": partial1_trigger,  # Pips
                "percent": config.BITMODE_PARTIAL1_PERCENT
            },
            partial2={
                "trigger": partial2_trigger,  # Pips
                "percent": config.BITMODE_PARTIAL2_PERCENT
            },
            trail={
                "distance": trail_distance  # Pips
            }
        )

        logger.info(
            f"BITMODE config for {symbol}: "
            f"Partial1 @ +{partial1_trigger} pips (25%), "
            f"Partial2 @ +{partial2_trigger} pips (25%), "
            f"Trail @ {trail_distance} pips (50%)"
        )

        return hybrid_config

    def create_hybrid_json(self, symbol: str) -> Dict:
        """
        Create hybrid configuration JSON for fire command

        Args:
            symbol: Trading pair

        Returns:
            Hybrid configuration dictionary for EA
        """
        config_obj = self.get_bitmode_config(symbol)

        return {
            "enabled": True,
            "partial1": {
                "trigger": config_obj.partial1["trigger"],
                "percent": config_obj.partial1["percent"]
            },
            "partial2": {
                "trigger": config_obj.partial2["trigger"],
                "percent": config_obj.partial2["percent"]
            },
            "trail": {
                "distance": config_obj.trail["distance"]
            }
        }

    def validate_hybrid_position(
        self,
        entry_price: float,
        current_price: float,
        direction: str,
        symbol: str
    ) -> Dict[str, bool]:
        """
        Check which BITMODE triggers have been hit

        Args:
            entry_price: Original entry price
            current_price: Current market price
            direction: "BUY" or "SELL"
            symbol: Trading pair

        Returns:
            Dictionary with trigger states
        """
        pip_size = config.get_pip_size(symbol)

        # Calculate pips in profit
        if direction == "BUY":
            pips = (current_price - entry_price) / pip_size
        else:
            pips = (entry_price - current_price) / pip_size

        partial1_trigger = config.BITMODE_PARTIAL1_TRIGGER
        partial2_trigger = config.BITMODE_PARTIAL2_TRIGGER

        return {
            "partial1_hit": pips >= partial1_trigger,
            "partial2_hit": pips >= partial2_trigger,
            "trailing_active": pips >= partial2_trigger,
            "current_pips": round(pips, 1)
        }


# Create singleton instance
bitmode_manager = BitmodeManager()
