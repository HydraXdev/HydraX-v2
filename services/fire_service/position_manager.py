#!/usr/bin/env python3
"""
Position Manager Module
Tracks live positions and provides position data
"""

import logging
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)


class PositionManager:
    """Manages live position tracking"""

    def __init__(self):
        self.config = config

    def get_user_positions(self, user_id: str) -> List[Dict]:
        """
        Get user's current open positions

        Args:
            user_id: User ID

        Returns:
            List of position dictionaries
        """
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            # Query positions_live table (created by EA event bus)
            cursor.execute(
                """
                SELECT ticket, fire_id, symbol, direction, open_price,
                       current_price, sl, tp, volume, profit, pips, opened_at
                FROM positions_live
                WHERE user_id = ?
                ORDER BY opened_at DESC
                """,
                (user_id,)
            )

            results = cursor.fetchall()
            conn.close()

            positions = []
            for row in results:
                positions.append({
                    "ticket": row[0],
                    "fire_id": row[1],
                    "symbol": row[2],
                    "direction": row[3],
                    "open_price": row[4],
                    "current_price": row[5],
                    "sl": row[6],
                    "tp": row[7],
                    "volume": row[8],
                    "profit": row[9],
                    "pips": row[10],
                    "opened_at": row[11]
                })

            return positions

        except Exception as e:
            logger.error(f"Error getting user positions: {e}")
            return []

    def get_position_by_ticket(self, ticket: int) -> Optional[Dict]:
        """
        Get position details by ticket number

        Args:
            ticket: MT5 ticket number

        Returns:
            Position dictionary or None
        """
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT ticket, fire_id, symbol, direction, open_price,
                       current_price, sl, tp, volume, profit, pips, opened_at, user_id
                FROM positions_live
                WHERE ticket = ?
                """,
                (ticket,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    "ticket": result[0],
                    "fire_id": result[1],
                    "symbol": result[2],
                    "direction": result[3],
                    "open_price": result[4],
                    "current_price": result[5],
                    "sl": result[6],
                    "tp": result[7],
                    "volume": result[8],
                    "profit": result[9],
                    "pips": result[10],
                    "opened_at": result[11],
                    "user_id": result[12]
                }

            return None

        except Exception as e:
            logger.error(f"Error getting position by ticket: {e}")
            return None

    def get_position_count(self, user_id: str) -> int:
        """
        Get count of user's open positions

        Args:
            user_id: User ID

        Returns:
            Number of open positions
        """
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM positions_live WHERE user_id = ?",
                (user_id,)
            )

            result = cursor.fetchone()
            conn.close()

            return result[0] if result else 0

        except Exception as e:
            logger.error(f"Error getting position count: {e}")
            return 0

    def get_total_exposure(self, user_id: str) -> Dict:
        """
        Calculate total exposure for user

        Args:
            user_id: User ID

        Returns:
            Dictionary with exposure metrics
        """
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT SUM(volume), SUM(profit), COUNT(*)
                FROM positions_live
                WHERE user_id = ?
                """,
                (user_id,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    "total_volume": result[0] or 0.0,
                    "total_profit": result[1] or 0.0,
                    "position_count": result[2] or 0
                }

            return {"total_volume": 0.0, "total_profit": 0.0, "position_count": 0}

        except Exception as e:
            logger.error(f"Error getting total exposure: {e}")
            return {"total_volume": 0.0, "total_profit": 0.0, "position_count": 0}

    def get_positions_by_symbol(self, user_id: str, symbol: str) -> List[Dict]:
        """
        Get positions for specific symbol

        Args:
            user_id: User ID
            symbol: Trading pair (e.g., "EURUSD")

        Returns:
            List of positions for symbol
        """
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT ticket, fire_id, direction, open_price,
                       current_price, sl, tp, volume, profit, pips
                FROM positions_live
                WHERE user_id = ? AND symbol = ?
                ORDER BY opened_at DESC
                """,
                (user_id, symbol)
            )

            results = cursor.fetchall()
            conn.close()

            positions = []
            for row in results:
                positions.append({
                    "ticket": row[0],
                    "fire_id": row[1],
                    "direction": row[2],
                    "open_price": row[3],
                    "current_price": row[4],
                    "sl": row[5],
                    "tp": row[6],
                    "volume": row[7],
                    "profit": row[8],
                    "pips": row[9]
                })

            return positions

        except Exception as e:
            logger.error(f"Error getting positions by symbol: {e}")
            return []

    def has_opposing_position(self, user_id: str, symbol: str, direction: str) -> bool:
        """
        Check if user has opposing position on symbol (hedge protection)

        Args:
            user_id: User ID
            symbol: Trading pair
            direction: "BUY" or "SELL"

        Returns:
            True if opposing position exists
        """
        try:
            opposing_direction = "SELL" if direction == "BUY" else "BUY"

            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) FROM positions_live
                WHERE user_id = ? AND symbol = ? AND direction = ?
                """,
                (user_id, symbol, opposing_direction)
            )

            result = cursor.fetchone()
            conn.close()

            return (result[0] if result else 0) > 0

        except Exception as e:
            logger.error(f"Error checking opposing position: {e}")
            return False

    def get_position_metrics(self, user_id: str) -> Dict:
        """
        Get comprehensive position metrics for user

        Args:
            user_id: User ID

        Returns:
            Dictionary with position metrics
        """
        positions = self.get_user_positions(user_id)
        exposure = self.get_total_exposure(user_id)

        # Calculate metrics
        winning_positions = sum(1 for p in positions if p["profit"] > 0)
        losing_positions = sum(1 for p in positions if p["profit"] < 0)

        return {
            "total_positions": len(positions),
            "winning_positions": winning_positions,
            "losing_positions": losing_positions,
            "total_volume": exposure["total_volume"],
            "total_profit": exposure["total_profit"],
            "positions": positions[:5]  # Latest 5 positions
        }


# Create singleton instance
position_manager = PositionManager()
