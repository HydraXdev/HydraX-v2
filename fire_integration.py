#!/usr/bin/env python3
"""
Fire Integration System - Wire existing Mission HUD with Rule/Slot engines
Integrates with existing webapp_server_optimized.py endpoints
"""

import hashlib
import hmac
import json
import logging
import sqlite3
import time
import uuid
from contextlib import contextmanager
from typing import Dict, Optional, Tuple

import zmq

logger = logging.getLogger(__name__)


class FirePacketBuilder:
    """Builds fire packets with proper lot sizing and validation"""

    def __init__(self):
        self.context = zmq.Context()

    def build_fire_packet(self, signal_data: Dict, user_data: Dict) -> Dict:
        """Build fire packet from signal and user data"""

        # Get user risk profile
        risk_percent = user_data.get("risk_percent", 2.0)  # Default 2%
        balance = user_data.get("balance", 10000.0)  # Default $10k

        # Calculate position size based on SL distance
        sl_pips = signal_data.get("stop_pips", 20)
        symbol = signal_data["symbol"]

        # Symbol-specific pip values (per standard lot)
        pip_values = {
            "EURUSD": 10.0,
            "GBPUSD": 10.0,
            "USDJPY": 10.0,
            "USDCHF": 10.0,
            "AUDUSD": 10.0,
            "USDCAD": 10.0,
            "NZDUSD": 10.0,
            "EURJPY": 10.0,
            "GBPJPY": 10.0,
            "EURGBP": 10.0,
            "XAUUSD": 10.0,  # Gold: $10 per pip per standard lot (100 oz)
            "XAGUSD": 50.0,  # Silver: $50 per pip per standard lot (5000 oz)
        }

        pip_value = pip_values.get(symbol, 10.0)
        risk_amount = balance * (risk_percent / 100)
        lot_size = risk_amount / (sl_pips * pip_value)

        # Round to standard lot sizes
        lot_size = round(max(0.01, min(lot_size, 10.0)), 2)

        # Calculate SL/TP prices
        entry = signal_data.get("entry_price", 0)
        direction = signal_data["direction"]

        # Determine pip size based on symbol
        if "JPY" in symbol:
            pip_size = 0.01
        elif symbol in ["XAUUSD", "XAGUSD", "BTCUSD"]:
            pip_size = 0.001  # Metals and crypto use 0.001 pip size
        else:
            pip_size = 0.0001  # Standard forex pairs

        if direction.upper() == "BUY":
            sl_price = entry - (sl_pips * pip_size)
            tp_price = entry + (signal_data.get("target_pips", 30) * pip_size)
        else:  # SELL
            sl_price = entry + (sl_pips * pip_size)
            tp_price = entry - (signal_data.get("target_pips", 30) * pip_size)

        # Build fire packet
        fire_packet = {
            "type": "fire",
            "target_uuid": "COMMANDER_DEV_001",  # Production EA
            "fire_id": f"HUD_FIRE_{signal_data['signal_id']}_{int(time.time())}",
            "symbol": symbol,
            "direction": direction.upper(),
            "entry": 0,  # Market order
            "sl": round(sl_price, 5),
            "tp": round(tp_price, 5),
            "lot": lot_size,
            "snapshot_tf": "M1",
        }

        return fire_packet


class RuleSlotEngine:
    """Mock Rule/Slot engine that integrates with existing fire_mode_database"""

    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/fire_modes.db"

    @contextmanager
    def get_db_connection(self):
        """Get database connection with context management"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def validate_fire_request(self, uid: str, sid: str, mode: str, base_symbol: str, direction: str) -> Dict:
        """
        Validate fire request and return rule/slot decision

        Returns dict matching contract:
        {
            allow: true|false,
            reason?: "…",
            policy_echo: {...},
            symbol_exact: "…",
            lot: <number>,
            sl: <number>,
            tp: <number>,
            digits: <int>,
            slots: {
                concurrent_used_after, concurrent_limit,
                daily_used_after, daily_limit,
                auto_daily_used_after, auto_daily_limit,
                action: "reserve" | "noop"
            }
        }
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                # Get user limits from fire mode database
                user_limits = self._get_user_limits(uid)

                # Count current slots
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM active_slots
                    WHERE user_id = ? AND status = 'OPEN' AND slot_type = 'MANUAL'
                """,
                    (uid,),
                )
                concurrent_used = cursor.fetchone()[0]

                # Count daily fires
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM fires
                    WHERE user_id = ? AND DATE(created_at) = DATE('now') AND status NOT IN ('FAILED', 'CANCELLED')
                """,
                    (uid,),
                )
                daily_used = cursor.fetchone()[0]

                # Validation checks using user's actual limits
                concurrent_limit = user_limits["concurrent_limit"]
                daily_limit = user_limits["daily_limit"]

                if concurrent_used >= concurrent_limit:
                    return {
                        "allow": False,
                        "reason": f"Concurrent slot limit reached ({concurrent_used}/{concurrent_limit})",
                        "slots": self._build_slot_info(concurrent_used, daily_used, 0, user_limits, "noop"),
                    }

                if daily_used >= daily_limit:
                    return {
                        "allow": False,
                        "reason": f"Daily fire limit reached ({daily_used}/{daily_limit})",
                        "slots": self._build_slot_info(concurrent_used, daily_used, 0, user_limits, "noop"),
                    }

                # Get signal data for packet building
                with sqlite3.connect("/root/HydraX-v2/bitten.db") as signal_conn:
                    signal_cursor = signal_conn.cursor()
                    signal_cursor.execute(
                        """
                        SELECT symbol, direction, entry_price, stop_pips, target_pips
                        FROM signals WHERE signal_id = ?
                    """,
                        (sid,),
                    )
                    signal_data = signal_cursor.fetchone()

                if not signal_data:
                    return {
                        "allow": False,
                        "reason": "Signal not found",
                        "slots": self._build_slot_info(concurrent_used, daily_used, 0, tier_limits, "noop"),
                    }

                # Build fire packet with REAL user data from database
                # Get user's actual balance from EA instance
                signal_cursor.execute(
                    """
                    SELECT last_balance FROM ea_instances
                    WHERE user_id = ?
                    ORDER BY last_seen DESC LIMIT 1
                """,
                    (uid,),
                )
                balance_row = signal_cursor.fetchone()
                user_balance = balance_row[0] if balance_row and balance_row[0] else 1000.0

                # Get user's risk preference from users table
                signal_cursor.execute(
                    """
                    SELECT risk_pct_default FROM users
                    WHERE user_id = ?
                """,
                    (uid,),
                )
                risk_row = signal_cursor.fetchone()
                user_risk_pct = risk_row[0] if risk_row and risk_row[0] else 2.0  # Default 2% if NULL

                user_data = {"balance": user_balance, "risk_percent": user_risk_pct}
                builder = FirePacketBuilder()
                signal_dict = {
                    "signal_id": sid,
                    "symbol": signal_data[0],
                    "direction": signal_data[1],
                    "entry_price": signal_data[2] or 0,
                    "stop_pips": signal_data[3] or 20,
                    "target_pips": signal_data[4] or 30,
                }
                fire_packet = builder.build_fire_packet(signal_dict, user_data)

                # Success response
                return {
                    "allow": True,
                    "policy_echo": {
                        "subscription_tier": user_limits["subscription_tier"],
                        "current_mode": user_limits["current_mode"],
                        "risk_percent": user_data["risk_percent"],
                        "calculated_lot": fire_packet["lot"],
                    },
                    "symbol_exact": fire_packet["symbol"],
                    "lot": fire_packet["lot"],
                    "sl": fire_packet["sl"],
                    "tp": fire_packet["tp"],
                    "digits": 5,
                    "slots": self._build_slot_info(concurrent_used + 1, daily_used + 1, 0, user_limits, "reserve"),
                }

        except Exception as e:
            logger.error(f"Rule/Slot engine error: {e}")
            return {
                "allow": False,
                "reason": f"Validation error: {str(e)}",
                "slots": self._build_slot_info(0, 0, 0, {"concurrent_limit": 1, "daily_limit": 10}, "noop"),
            }

    def _get_user_limits(self, uid: str) -> Dict:
        """Get user limits from actual fire mode database"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                # Get user's actual settings from database
                cursor.execute(
                    """
                    SELECT current_mode, max_auto_slots, auto_slots_in_use, manual_slots_in_use,
                           max_trades_per_day, subscription_tier, max_manual_slots
                    FROM user_fire_modes WHERE user_id = ?
                """,
                    (uid,),
                )

                user_data = cursor.fetchone()
                if not user_data:
                    # User not found, return conservative defaults
                    return {
                        "concurrent_limit": 1,
                        "daily_limit": 10,
                        "current_mode": "MANUAL",
                        "subscription_tier": "NIBBLER",
                    }

                (
                    current_mode,
                    max_auto_slots,
                    auto_slots_in_use,
                    manual_slots_in_use,
                    max_trades_per_day,
                    subscription_tier,
                    max_manual_slots,
                ) = user_data

                # The concurrent limit depends on the mode
                if current_mode == "AUTO":
                    concurrent_limit = max_auto_slots
                else:
                    concurrent_limit = max_manual_slots

                return {
                    "concurrent_limit": concurrent_limit,
                    "daily_limit": max_trades_per_day,
                    "current_mode": current_mode,
                    "subscription_tier": subscription_tier,
                    "max_auto_slots": max_auto_slots,
                    "max_manual_slots": max_manual_slots,
                    "auto_slots_in_use": auto_slots_in_use,
                    "manual_slots_in_use": manual_slots_in_use,
                }

        except Exception as e:
            logger.error(f"Error getting user limits: {e}")
            # Fallback to conservative limits
            return {"concurrent_limit": 1, "daily_limit": 10, "current_mode": "MANUAL", "subscription_tier": "NIBBLER"}

    def _get_user_tier(self, uid: str) -> str:
        """Get user tier from user registry"""
        try:
            with open("/root/HydraX-v2/user_registry.json", "r") as f:
                users = json.load(f)
                return users.get(uid, {}).get("tier", "GLADIATOR")
        except:
            return "GLADIATOR"

    def _build_slot_info(
        self, concurrent_used: int, daily_used: int, auto_daily_used: int, limits: Dict, action: str
    ) -> Dict:
        """Build slot information response"""
        return {
            "concurrent_used_after": concurrent_used,
            "concurrent_limit": limits.get("concurrent_limit", 1),
            "daily_used_after": daily_used,
            "daily_limit": limits.get("daily_limit", 10),
            "auto_daily_used_after": auto_daily_used,
            "max_auto_slots": limits.get("max_auto_slots", 0),
            "max_manual_slots": limits.get("max_manual_slots", 1),
            "auto_slots_in_use": limits.get("auto_slots_in_use", 0),
            "manual_slots_in_use": limits.get("manual_slots_in_use", 0),
            "subscription_tier": limits.get("subscription_tier", "NIBBLER"),
            "current_mode": limits.get("current_mode", "MANUAL"),
            "action": action,
        }


class ConfirmationEnricher:
    """Enriches confirmation events with slot and account information"""

    def __init__(self):
        self.rule_engine = RuleSlotEngine()

    def enrich_confirmation(self, confirmation_data: Dict) -> Dict:
        """
        Enrich confirmation with slots and account information

        Input: { type:"confirmation", fire_id, status, ticket, price, message, user_uuid, account:{...} }
        Output: Enhanced with slots:{...} information
        """
        try:
            fire_id = confirmation_data.get("fire_id")
            user_uuid = confirmation_data.get("user_uuid")

            if not fire_id or not user_uuid:
                return confirmation_data

            # Get current slot counts
            with sqlite3.connect("/root/HydraX-v2/data/fire_modes.db") as conn:
                cursor = conn.cursor()

                # Get concurrent slots
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM active_slots
                    WHERE user_id = ? AND status = 'OPEN'
                """,
                    (user_uuid,),
                )
                concurrent_used = cursor.fetchone()[0]

                # Get daily fires
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM fires
                    WHERE user_id = ? AND DATE(created_at) = DATE('now')
                """,
                    (user_uuid,),
                )
                daily_used = cursor.fetchone()[0]

            # Get user limits from fire mode database
            user_limits = self.rule_engine._get_user_limits(user_uuid)

            # Add slot information to confirmation
            enriched = confirmation_data.copy()
            enriched["slots"] = {
                "concurrent_used": concurrent_used,
                "concurrent_limit": user_limits.get("concurrent_limit", 1),
                "daily_used": daily_used,
                "daily_limit": user_limits.get("daily_limit", 10),
                "auto_daily_used": 0,  # TODO: Track auto fires separately
                "max_auto_slots": user_limits.get("max_auto_slots", 0),
                "max_manual_slots": user_limits.get("max_manual_slots", 1),
                "auto_slots_in_use": user_limits.get("auto_slots_in_use", 0),
                "manual_slots_in_use": user_limits.get("manual_slots_in_use", 0),
                "subscription_tier": user_limits.get("subscription_tier", "NIBBLER"),
                "current_mode": user_limits.get("current_mode", "MANUAL"),
                "action": "hold" if confirmation_data.get("status") == "success" else "release",
            }

            return enriched

        except Exception as e:
            logger.error(f"Confirmation enrichment error: {e}")
            return confirmation_data


class FireIntegrationAPI:
    """Main API class for fire integration"""

    def __init__(self):
        self.rule_engine = RuleSlotEngine()
        self.enricher = ConfirmationEnricher()
        self.zmq_context = zmq.Context()

    def verify_signal_access(self, sid: str, uid: str, t: str, sig: str) -> Tuple[bool, Dict]:
        """Verify HMAC signature for signal access"""
        try:
            # HMAC verification
            secret_key = "bitten_dev_key_2025".encode("utf-8")  # Same as webapp
            message = f"{sid}|{uid}|{t}".encode("utf-8")
            expected_sig = hmac.new(secret_key, message, hashlib.sha256).hexdigest()

            if not hmac.compare_digest(sig, expected_sig):
                return False, {"error": "Invalid signature"}

            # Check timestamp (within 5 minutes)
            current_time = int(time.time())
            if abs(current_time - int(t)) > 300:
                return False, {"error": "Request expired"}

            # Get signal and health data
            with sqlite3.connect("/root/HydraX-v2/bitten.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT signal_id, symbol, pattern_type, direction, confidence
                    FROM signals WHERE signal_id = ?
                """,
                    (sid,),
                )
                signal_data = cursor.fetchone()

            if not signal_data:
                return False, {"error": "Signal not found"}

            # Mock health data (in real system, get from EA metrics)
            health_data = {"pong_ms": 45, "balance": 10000.0, "equity": 9875.5, "open_positions": 2}

            response = {
                "signal": {
                    "sid": signal_data[0],
                    "symbol": signal_data[1],
                    "pattern": signal_data[2],
                    "direction": signal_data[3],
                    "confidence": signal_data[4],
                },
                "health": health_data,
            }

            return True, response

        except Exception as e:
            logger.error(f"Signal verification error: {e}")
            return False, {"error": str(e)}

    def execute_fire(self, sid: str, uid: str, idempotency_key: str) -> Tuple[int, Dict]:
        """Execute fire command with idempotency"""
        try:
            # Check idempotency
            with sqlite3.connect("/root/HydraX-v2/bitten.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT fire_id, status FROM fires
                    WHERE user_id = ? AND idempotency_key = ?
                """,
                    (uid, idempotency_key),
                )
                existing = cursor.fetchone()

                if existing:
                    return 200, {
                        "queued": True,
                        "fire_id": existing[0],
                        "status": existing[1],
                        "message": "Already processed (idempotent)",
                    }

                # Get signal data
                cursor.execute(
                    """
                    SELECT symbol, direction FROM signals WHERE signal_id = ?
                """,
                    (sid,),
                )
                signal_data = cursor.fetchone()

                if not signal_data:
                    return 404, {"error": "Signal not found"}

                base_symbol = signal_data[0][:3]  # Simple base symbol extraction

                # Call Rule/Slot engine
                validation = self.rule_engine.validate_fire_request(
                    uid=uid, sid=sid, mode="manual", base_symbol=base_symbol, direction=signal_data[1]
                )

                if not validation["allow"]:
                    return 409, {"success": False, "error": validation["reason"], "slots": validation["slots"]}

                # Create fire record
                fire_id = f"HUD_FIRE_{sid}_{uid}_{int(time.time())}"
                cursor.execute(
                    """
                    INSERT INTO fires (fire_id, mission_id, user_id, status,
                                     idempotency_key, policy_echo, created_at)
                    VALUES (?, ?, ?, 'queued', ?, ?, ?)
                """,
                    (fire_id, sid, uid, idempotency_key, json.dumps(validation["policy_echo"]), datetime.now()),
                )

                # Reserve slot
                cursor.execute(
                    """
                    INSERT INTO active_slots (user_id, mission_id, symbol, slot_type, status, created_at)
                    VALUES (?, ?, ?, 'MANUAL', 'OPEN', ?)
                """,
                    (uid, sid, validation["symbol_exact"], datetime.now()),
                )

                conn.commit()

                # Build and send fire packet to IPC
                fire_packet = {
                    "type": "fire",
                    "target_uuid": "COMMANDER_DEV_001",
                    "fire_id": fire_id,
                    "symbol": validation["symbol_exact"],
                    "direction": signal_data[1].upper(),
                    "entry": 0,
                    "sl": validation["sl"],
                    "tp": validation["tp"],
                    "lot": validation["lot"],
                    "snapshot_tf": "M1",
                }

                # Send via IPC
                push_socket = self.zmq_context.socket(zmq.PUSH)
                push_socket.connect("ipc:///tmp/bitten_cmdqueue")
                push_socket.send_json(fire_packet)
                push_socket.close()

                logger.info(f"Fire command sent: {fire_id}")

                return 202, {"queued": True, "fire_id": fire_id, "slots": validation["slots"]}

        except Exception as e:
            logger.error(f"Fire execution error: {e}")
            return 500, {"error": str(e)}


# Global instance for webapp integration
fire_integration = FireIntegrationAPI()
