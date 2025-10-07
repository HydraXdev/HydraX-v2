#!/usr/bin/env python3
"""
HUD Bridge - Event Bus Integration for Mission Brief HUD
Provides clean, real-time data access for the mission briefing interface
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class HUDBridge:
    """Bridge between Mission Brief HUD and Event Bus system"""

    def __init__(self):
        self.event_db_path = Path("/root/HydraX-v2/event_bus/bitten_events.db")
        self.bitten_db_path = Path("/root/HydraX-v2/bitten.db")

    def get_mission_state(self, mission_id: str) -> Dict[str, Any]:
        """
        Reconstruct complete mission state from event bus
        Single source of truth for all mission data
        """
        try:
            conn = sqlite3.connect(self.event_db_path)
            cursor = conn.cursor()

            # Get all events for this mission
            cursor.execute(
                """
                SELECT event_type, data_json, created_at
                FROM events
                WHERE data_json LIKE ?
                ORDER BY created_at DESC
                LIMIT 100
            """,
                (f"%{mission_id}%",),
            )

            events = cursor.fetchall()

            # Build state from events
            state = {
                "mission_id": mission_id,
                "status": "active",
                "created_at": None,
                "last_updated": None,
                "signal": {},
                "execution": {},
                "outcomes": [],
            }

            for event_type, data_json, created_at in events:
                try:
                    data = json.loads(data_json)

                    # Process different event types
                    if event_type == "signal_generated":
                        state["signal"] = {
                            "symbol": data.get("symbol"),
                            "direction": data.get("direction"),
                            "entry_price": data.get("entry_price"),
                            "stop_loss": data.get("stop_loss"),
                            "take_profit": data.get("take_profit"),
                            "pattern_type": data.get("pattern"),
                            "confidence": data.get("confidence"),
                            "session": data.get("session", "UNKNOWN"),
                            "created_at": created_at,
                        }
                        if not state["created_at"]:
                            state["created_at"] = created_at

                    elif event_type == "trade_executed":
                        state["execution"] = {
                            "fire_id": data.get("fire_id"),
                            "user_id": data.get("user_id"),
                            "lot_size": data.get("lot_size"),
                            "executed_at": created_at,
                            "ticket": data.get("ticket"),
                        }

                    elif event_type == "trade_outcome":
                        state["outcomes"].append(
                            {"outcome": data.get("outcome"), "pips": data.get("pips_result"), "timestamp": created_at}
                        )

                    state["last_updated"] = created_at

                except json.JSONDecodeError:
                    continue

            conn.close()

            # Calculate derived fields
            state["freshness"] = self._calculate_freshness(state)
            state["time_remaining"] = self._calculate_time_remaining(state)

            return state

        except Exception as e:
            print(f"Error getting mission state: {e}")
            return {"error": str(e), "mission_id": mission_id}

    def get_user_live_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get real-time user data from event bus and EA instances
        Includes balance, win rate, active positions, etc.
        """
        try:
            # Get latest balance from EA instances
            conn = sqlite3.connect(self.bitten_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT last_balance, last_equity, leverage, broker, currency,
                       (strftime('%s', 'now') - last_seen) as seconds_ago
                FROM ea_instances
                WHERE user_id = ?
                ORDER BY last_seen DESC
                LIMIT 1
            """,
                (user_id,),
            )

            ea_data = cursor.fetchone()

            # Get win rate from event bus
            event_conn = sqlite3.connect(self.event_db_path)
            event_cursor = event_conn.cursor()

            event_cursor.execute(
                """
                SELECT
                    COUNT(CASE WHEN json_extract(data_json, '$.outcome') = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN json_extract(data_json, '$.outcome') = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN json_extract(data_json, '$.outcome') IN ('WIN', 'LOSS') THEN 1 END) as total
                FROM events
                WHERE event_type = 'trade_outcome'
                AND data_json LIKE ?
                AND created_at > (julianday('now') - 7) * 86400
            """,
                (f'%"user_id":"{user_id}"%',),
            )

            win_stats = event_cursor.fetchone()
            wins, losses, total = win_stats if win_stats else (0, 0, 0)
            win_rate = (wins / total * 100) if total > 0 else 0

            # Get active positions count
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM fires
                WHERE user_id = ?
                AND status IN ('PENDING', 'FILLED')
            """,
                (user_id,),
            )

            active_positions = cursor.fetchone()[0]

            # Get user tier (simplified)
            tier = "COMMANDER" if user_id == "7176191872" else "NIBBLER"

            user_data = {
                "user_id": user_id,
                "tier": tier,
                "balance": float(ea_data[0]) if ea_data and ea_data[0] else 0.0,
                "equity": float(ea_data[1]) if ea_data and ea_data[1] else 0.0,
                "leverage": ea_data[2] if ea_data else 500,
                "broker": ea_data[3] if ea_data else "Not Connected",
                "currency": ea_data[4] if ea_data else "USD",
                "connection_fresh": ea_data[5] < 120 if ea_data else False,
                "win_rate": round(win_rate, 1),
                "total_trades": total,
                "wins": wins,
                "losses": losses,
                "active_positions": active_positions,
                "slots": self._get_slot_availability(user_id, tier),
                "risk_percentage": 2.0,  # Default 2% risk
                "timestamp": datetime.now().isoformat(),
            }

            conn.close()
            event_conn.close()

            return user_data

        except Exception as e:
            print(f"Error getting user live data: {e}")
            return {"user_id": user_id, "error": str(e), "balance": 0, "equity": 0, "win_rate": 0}

    def get_signal_freshness(self, signal_id: str) -> Dict[str, Any]:
        """
        Calculate real-time signal freshness/quality
        Based on age, market conditions, and pattern validity
        """
        try:
            conn = sqlite3.connect(self.event_db_path)
            cursor = conn.cursor()

            # Get signal creation time
            cursor.execute(
                """
                SELECT created_at, data_json
                FROM events
                WHERE event_type = 'signal_generated'
                AND data_json LIKE ?
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (f"%{signal_id}%",),
            )

            result = cursor.fetchone()
            if not result:
                return {"freshness": 0, "status": "NOT_FOUND", "signal_id": signal_id}

            created_at, data_json = result
            signal_data = json.loads(data_json)

            # Calculate age in seconds
            age_seconds = time.time() - created_at
            age_minutes = age_seconds / 60

            # Freshness calculation (100% fresh to 0% stale)
            if age_minutes < 5:
                freshness = 100
                status = "FRESH"
                color = "#10b981"
            elif age_minutes < 15:
                freshness = 100 - ((age_minutes - 5) * 5)  # Decay 5% per minute
                status = "ACTIVE"
                color = "#f59e0b"
            elif age_minutes < 30:
                freshness = 50 - ((age_minutes - 15) * 2)  # Faster decay
                status = "STALE"
                color = "#ef4444"
            else:
                freshness = 0
                status = "EXPIRED"
                color = "#6b7280"

            # Check for pattern invalidation events
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM events
                WHERE event_type = 'pattern_invalidated'
                AND data_json LIKE ?
                AND created_at > ?
            """,
                (f"%{signal_id}%", created_at),
            )

            invalidated = cursor.fetchone()[0] > 0

            if invalidated:
                freshness = 0
                status = "INVALIDATED"
                color = "#ef4444"

            conn.close()

            return {
                "signal_id": signal_id,
                "freshness": max(0, min(100, freshness)),
                "status": status,
                "color": color,
                "age_minutes": round(age_minutes, 1),
                "pattern_type": signal_data.get("pattern"),
                "invalidated": invalidated,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"Error calculating freshness: {e}")
            return {"signal_id": signal_id, "freshness": 0, "status": "ERROR", "error": str(e)}

    def get_pattern_stats(self, pattern_type: str) -> Dict[str, Any]:
        """Get performance statistics for a specific pattern"""
        try:
            conn = sqlite3.connect(self.event_db_path)
            cursor = conn.cursor()

            # Get pattern performance from events
            cursor.execute(
                """
                SELECT
                    COUNT(CASE WHEN json_extract(data_json, '$.outcome') = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN json_extract(data_json, '$.outcome') = 'LOSS' THEN 1 END) as losses,
                    AVG(CAST(json_extract(data_json, '$.pips_result') AS REAL)) as avg_pips,
                    MAX(CAST(json_extract(data_json, '$.pips_result') AS REAL)) as best_trade,
                    MIN(CAST(json_extract(data_json, '$.pips_result') AS REAL)) as worst_trade
                FROM events
                WHERE event_type = 'trade_outcome'
                AND json_extract(data_json, '$.pattern') = ?
                AND created_at > (julianday('now') - 7) * 86400
            """,
                (pattern_type,),
            )

            stats = cursor.fetchone()
            wins, losses, avg_pips, best, worst = stats if stats else (0, 0, 0, 0, 0)

            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0

            conn.close()

            return {
                "pattern_type": pattern_type,
                "total_trades": total,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 1),
                "avg_pips": round(avg_pips, 1) if avg_pips else 0,
                "best_trade": round(best, 1) if best else 0,
                "worst_trade": round(worst, 1) if worst else 0,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"Error getting pattern stats: {e}")
            return {"pattern_type": pattern_type, "error": str(e), "total_trades": 0, "win_rate": 0}

    def _calculate_freshness(self, state: Dict) -> int:
        """Calculate freshness percentage based on signal age"""
        if not state.get("created_at"):
            return 0

        age_seconds = time.time() - state["created_at"]
        age_minutes = age_seconds / 60

        if age_minutes < 5:
            return 100
        elif age_minutes < 15:
            return int(100 - ((age_minutes - 5) * 5))
        elif age_minutes < 30:
            return int(50 - ((age_minutes - 15) * 2))
        else:
            return 0

    def _calculate_time_remaining(self, state: Dict) -> int:
        """Calculate seconds remaining until signal expires"""
        if not state.get("created_at"):
            return 0

        # Signals expire after 30 minutes
        expiry_time = state["created_at"] + (30 * 60)
        remaining = expiry_time - time.time()

        return max(0, int(remaining))

    def _get_slot_availability(self, user_id: str, tier: str) -> Dict[str, Any]:
        """Get slot availability for user"""
        # Simplified slot calculation
        tier_limits = {
            "COMMANDER": {"manual": 5, "auto": 3},
            "NIBBLER": {"manual": 1, "auto": 0},
            "DEFAULT": {"manual": 3, "auto": 1},
        }

        limits = tier_limits.get(tier, tier_limits["DEFAULT"])

        try:
            # Get active positions count
            conn = sqlite3.connect(self.bitten_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(CASE WHEN fire_id LIKE 'MANUAL%' THEN 1 END) as manual_used,
                    COUNT(CASE WHEN fire_id LIKE 'AUTO%' THEN 1 END) as auto_used
                FROM fires
                WHERE user_id = ?
                AND status IN ('PENDING', 'FILLED')
            """,
                (user_id,),
            )

            result = cursor.fetchone()
            manual_used, auto_used = result if result else (0, 0)

            conn.close()

            return {
                "manual_available": max(0, limits["manual"] - manual_used),
                "manual_total": limits["manual"],
                "manual_used": manual_used,
                "auto_available": max(0, limits["auto"] - auto_used),
                "auto_total": limits["auto"],
                "auto_used": auto_used,
            }

        except Exception as e:
            print(f"Error getting slots: {e}")
            return {
                "manual_available": limits["manual"],
                "manual_total": limits["manual"],
                "auto_available": limits["auto"],
                "auto_total": limits["auto"],
            }


# Singleton instance
hud_bridge = HUDBridge()
