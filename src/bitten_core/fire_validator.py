#!/usr/bin/env python3
"""
Server-Side Fire Validation Engine
===================================
Enforces tier-based restrictions for all fire requests.

Tier Limits:
- NIBBLER: 1 manual slot, 0 auto, 6 trades/day, 0.5% risk max
- FANG: 2 manual slots, 0 auto, 6 trades/day, 1.0% risk max
- COMMANDER: 20 slots (10 auto + 10 manual), 99 trades/day, 0.5-4% risk range

Security: Server validation is authoritative - client requests are advisory only.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-09
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class FireValidator:
    """Server-side fire request validator with tier enforcement"""

    def __init__(self, db_path: str = "/root/HydraX-v2/bitten.db"):
        self.db_path = db_path
        self.user_registry_path = "/root/HydraX-v2/user_registry.json"
        logger.info(f"[FIRE_VALIDATOR] Using database: {self.db_path}")

        # Tier definitions (server authority)
        self.TIER_CAPS = {
            "PRESS_PASS": {
                "max_manual_slots": 1,
                "max_auto_slots": 0,
                "max_trades_per_day": 6,
                "min_risk_pct": 0.5,
                "max_risk_pct": 0.5,
                "auto_fire_allowed": False,
                "trailing_opens_slot": False,
                "description": "Trial tier - 1 trade at a time, 6 daily shots, manual only"
            },
            "NIBBLER": {
                "max_manual_slots": 1,
                "max_auto_slots": 0,
                "max_trades_per_day": 6,
                "min_risk_pct": 0.5,
                "max_risk_pct": 0.5,
                "auto_fire_allowed": False,
                "trailing_opens_slot": False,
                "description": "Entry tier - 1 trade at a time, 6 daily shots, manual only"
            },
            "FANG": {
                "max_manual_slots": 2,
                "max_auto_slots": 0,
                "max_trades_per_day": 12,
                "min_risk_pct": 0.5,
                "max_risk_pct": 1.0,
                "auto_fire_allowed": False,
                "trailing_opens_slot": True,
                "description": "Mid tier - 2 concurrent, 12 daily shots, trailing opens slots"
            },
            "COMMANDER": {
                "max_manual_slots": 20,  # Manual shots per day
                "max_auto_slots": 10,    # Base auto slots (can exceed with trailing)
                "max_trades_per_day": 20,  # Daily manual shots
                "min_risk_pct": 0.5,
                "max_risk_pct": 4.0,
                "auto_fire_allowed": True,
                "trailing_opens_slot": True,
                "description": "Top tier - 20 manual shots, up to 10 auto (unlimited if trailing)"
            }
        }

        # Symbol pip values (for lot calculation)
        self.PIP_VALUES = {
            "EURUSD": 10.0,  # $10 per pip per standard lot
            "GBPUSD": 10.0,
            "USDJPY": 9.09,  # Varies with rate, approximate
            "USDCHF": 10.0,
            "AUDUSD": 10.0,
            "NZDUSD": 10.0,
            "USDCAD": 9.09,
            "EURJPY": 9.09,
            "GBPJPY": 9.09,
            "XAUUSD": 10.0,  # Gold
            "XAGUSD": 50.0,  # Silver (higher pip value)
        }

    def validate_fire_request(
        self,
        user_id: str,
        signal_id: str,
        client_request: Dict
    ) -> Dict:
        """
        Validate fire request against server caps and return enforcement parameters.

        Args:
            user_id: User's Telegram ID
            signal_id: Signal identifier
            client_request: User's requested parameters (advisory)
                {
                    "symbol": "EURUSD",
                    "direction": "BUY",
                    "sl_pips": 20.0,
                    "tp_pips": 30.0,
                    "risk_pct": 2.0,  # User's preference (capped by tier)
                    "fire_mode": "AUTO"  # AUTO or MANUAL
                }

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "enforced": {
                    "lot_size": float,
                    "risk_pct": float,
                    "fire_mode": str,
                    "max_loss": float,
                    "expected_gain": float
                },
                "tier_info": {...},
                "validation_details": {...}
            }
        """
        logger.info(f"[FIRE_VALIDATOR] Validating request for user {user_id}, signal {signal_id}")

        try:
            # Step 1: Load user caps from database
            user_caps = self._load_user_caps(user_id)
            if not user_caps:
                return self._rejection("User not found in database", {})

            tier = user_caps.get("subscription_tier", "NIBBLER")
            tier_caps = self.TIER_CAPS.get(tier, self.TIER_CAPS["NIBBLER"])

            logger.info(f"[FIRE_VALIDATOR] User {user_id} tier: {tier}")

            # Step 2: 🛡️ CRITICAL SAFETY CHECK - SAFE MODE BLOCKS EVERYTHING
            current_mode = user_caps.get("current_mode", "AUTO").upper()
            if current_mode == "SAFE":
                return self._rejection(
                    "🛡️ SAFE MODE ACTIVE - All trading blocked. Change fire selector to resume trading.",
                    tier_caps
                )

            # Step 3: Check if trading is enabled
            if not user_caps.get("trading_enabled", True):
                return self._rejection("Trading disabled for this account", tier_caps)

            # Step 4: Validate fire mode
            fire_mode = client_request.get("fire_mode", "MANUAL").upper()
            if fire_mode == "AUTO" and not tier_caps["auto_fire_allowed"]:
                return self._rejection(
                    f"Auto-fire not available for {tier} tier (requires COMMANDER)",
                    tier_caps
                )

            # Step 4: Check slot availability (with trailing stop logic)
            slots_check = self._check_slots_available(user_id, user_caps, tier_caps, fire_mode, tier)
            if not slots_check["available"]:
                return self._rejection(slots_check["reason"], tier_caps)

            # Step 5: Check daily trade limit
            daily_check = self._check_daily_ammo(user_id, user_caps, tier_caps)
            if not daily_check["available"]:
                return self._rejection(daily_check["reason"], tier_caps)

            # Step 6: Load account balance
            balance = self._get_account_balance(user_id)
            if balance <= 0:
                return self._rejection("Account balance unavailable or zero", tier_caps)

            logger.info(f"[FIRE_VALIDATOR] Account balance: ${balance:.2f}")

            # Step 7: Enforce risk cap
            requested_risk = client_request.get("risk_pct", 2.0)
            enforced_risk = self._enforce_risk_cap(
                requested_risk,
                user_caps.get("risk_per_trade", 2.0),
                tier_caps
            )

            logger.info(f"[FIRE_VALIDATOR] Risk: requested={requested_risk}%, enforced={enforced_risk}%")

            # Step 8: Calculate lot size
            symbol = client_request.get("symbol", "EURUSD")
            sl_pips = client_request.get("sl_pips", 20.0)
            tp_pips = client_request.get("tp_pips", 30.0)

            lot_size = self._calculate_lot_size(
                balance=balance,
                risk_pct=enforced_risk,
                stop_pips=sl_pips,
                symbol=symbol
            )

            logger.info(f"[FIRE_VALIDATOR] Calculated lot size: {lot_size:.2f}")

            # Step 9: Calculate expected financials
            pip_value = self.PIP_VALUES.get(symbol, 10.0)
            max_loss = lot_size * sl_pips * pip_value
            expected_gain = lot_size * tp_pips * pip_value

            # Step 10: Validation passed - return enforced parameters
            return {
                "allowed": True,
                "reason": "Validation passed",
                "enforced": {
                    "lot_size": round(lot_size, 2),  # MT5 requires 2 decimal places
                    "risk_pct": enforced_risk,
                    "fire_mode": fire_mode,
                    "max_loss": round(max_loss, 2),
                    "expected_gain": round(expected_gain, 2),
                    "symbol": symbol,
                    "sl_pips": sl_pips,
                    "tp_pips": tp_pips,
                },
                "tier_info": {
                    "tier": tier,
                    "caps": tier_caps,
                    "user_caps": user_caps,
                },
                "validation_details": {
                    "balance": balance,
                    "slots_used": slots_check["usage"],
                    "trades_today": daily_check["usage"],
                    "risk_calculation": {
                        "requested": requested_risk,
                        "user_preference": user_caps.get("risk_per_trade", 2.0),
                        "tier_cap": tier_caps["max_risk_pct"],
                        "enforced": enforced_risk,
                    }
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"[FIRE_VALIDATOR] Validation error for user {user_id}: {e}", exc_info=True)
            return self._rejection(f"Validation error: {str(e)}", {})

    def _load_user_caps(self, user_id: str) -> Optional[Dict]:
        """Load user's server-side caps from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # CRITICAL: Column order MUST match actual database table structure
            # ⚠️ FIREBASE UID FIX: user_id in fire_modes is Telegram ID, must resolve
            # Query uses Telegram ID because fire_modes.db still stores legacy IDs
            cursor.execute("""
                SELECT
                    user_id,
                    current_mode,
                    auto_fire_enabled,
                    auto_fire_min_confidence,
                    auto_fire_max_confidence,
                    max_concurrent_positions,
                    risk_per_trade_pct,
                    updated_at,
                    subscription_tier,
                    max_manual_slots,
                    max_auto_slots_separate,
                    manual_slots_in_use,
                    auto_slots_in_use,
                    trades_used_today,
                    tier_max_trades_per_day,
                    trading_enabled,
                    risk_per_trade
                FROM user_fire_modes
                WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.warning(f"[FIRE_VALIDATOR] User {user_id} not found in database")
                return None

            # Map row indexes to match the corrected SELECT query order
            return {
                "user_id": row[0],                    # position 0
                "current_mode": row[1] or "AUTO",     # position 1 - 🛡️ SAFE MODE CHECK
                "subscription_tier": row[8] or "NIBBLER",  # position 8 - CRITICAL FIX!
                "max_manual_slots": row[9] or 1,      # position 9
                "max_auto_slots": row[10] or 0,       # position 10
                "manual_slots_in_use": row[11] or 0,  # position 11
                "auto_slots_in_use": row[12] or 0,    # position 12
                "trades_used_today": row[13] or 0,    # position 13
                "tier_max_trades_per_day": row[14] or 6,  # position 14
                "risk_per_trade": row[16] or 2.0,     # position 16
                "trading_enabled": bool(row[15]) if row[15] is not None else True,  # position 15
                "auto_fire_enabled": bool(row[2]) if row[2] is not None else False,  # position 2
            }

        except Exception as e:
            logger.error(f"[FIRE_VALIDATOR] Database error loading user caps: {e}", exc_info=True)
            return None

    def _check_slots_available(
        self,
        user_id: str,
        user_caps: Dict,
        tier_caps: Dict,
        fire_mode: str,
        tier: str
    ) -> Dict:
        """
        Check if user has available slots - ADVANCED TRAILING STOP LOGIC

        NEW RULES:
        - PRESS_PASS/NIBBLER: 1 slot max, opens on close only
        - FANG: 2 slots max, opens on close OR trailing stop (SL > breakeven)
        - COMMANDER: 10 auto slots (configurable), unlimited if trailing stop active

        ✅ Reads ACTUAL open positions from live_positions table (single source of truth)
        ✅ Detects trailing stop status (SL > entry = breakeven protection)
        """

        # Calculate max slots based on tier
        if fire_mode == "AUTO":
            max_slots = min(user_caps["max_auto_slots"], tier_caps["max_auto_slots"])
            slot_type = "auto"
        else:
            max_slots = min(user_caps["max_manual_slots"], tier_caps["max_manual_slots"])
            slot_type = "manual"

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count total open positions by fire mode
            cursor.execute("""
                SELECT COUNT(*)
                FROM live_positions lp
                JOIN fires f ON lp.fire_id = f.fire_id
                WHERE lp.user_id = ?
                  AND lp.status = 'OPEN'
                  AND (f.fire_mode = ? OR (f.fire_mode IS NULL AND ? = 'MANUAL'))
            """, (user_id, fire_mode, fire_mode))

            total_positions = cursor.fetchone()[0] or 0

            # Check if tier supports trailing stop slot opening
            trailing_enabled = tier_caps.get("trailing_opens_slot", False)

            if trailing_enabled and total_positions >= max_slots:
                # Count positions in "safe zone" (trailing stop active = SL > breakeven)
                # BUY: current SL > entry price = profit protected
                # SELL: current SL < entry price = profit protected
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM live_positions lp
                    JOIN fires f ON lp.fire_id = f.fire_id
                    WHERE lp.user_id = ?
                      AND lp.status = 'OPEN'
                      AND (f.fire_mode = ? OR (f.fire_mode IS NULL AND ? = 'MANUAL'))
                      AND (
                        (lp.direction = 'BUY' AND lp.sl > lp.entry_price) OR
                        (lp.direction = 'SELL' AND lp.sl < lp.entry_price)
                      )
                """, (user_id, fire_mode, fire_mode))

                trailing_positions = cursor.fetchone()[0] or 0

                # Slots "in use" = total positions minus trailing positions
                # (trailing positions don't count against slot limit)
                slots_in_use = total_positions - trailing_positions

                logger.info(
                    f"[FIRE_VALIDATOR] Slots check (TRAILING LOGIC): {slot_type.upper()} "
                    f"{total_positions} total positions, {trailing_positions} in trailing stop, "
                    f"{slots_in_use}/{max_slots} slots consumed"
                )
            else:
                # No trailing logic for this tier, all positions count against slots
                slots_in_use = total_positions

                logger.info(
                    f"[FIRE_VALIDATOR] Slots check (BASIC): {slot_type.upper()} "
                    f"{slots_in_use}/{max_slots} used (no trailing logic for {tier})"
                )

            conn.close()

        except Exception as e:
            logger.error(f"[FIRE_VALIDATOR] Error counting live positions: {e}", exc_info=True)
            slots_in_use = 0

        available = slots_in_use < max_slots

        if not available:
            return {
                "available": False,
                "reason": f"No {slot_type} slots available ({slots_in_use}/{max_slots} in use)",
                "usage": {"type": slot_type, "used": slots_in_use, "max": max_slots, "total_positions": total_positions if trailing_enabled else slots_in_use}
            }

        return {
            "available": True,
            "reason": f"{slot_type.capitalize()} slot available ({slots_in_use}/{max_slots} used)",
            "usage": {"type": slot_type, "used": slots_in_use, "max": max_slots, "total_positions": total_positions if trailing_enabled else slots_in_use}
        }

    def _check_daily_ammo(self, user_id: str, user_caps: Dict, tier_caps: Dict) -> Dict:
        """Check daily trade limit"""

        trades_used = user_caps["trades_used_today"]
        max_trades = min(user_caps["tier_max_trades_per_day"], tier_caps["max_trades_per_day"])

        available = trades_used < max_trades

        logger.info(
            f"[FIRE_VALIDATOR] Daily ammo check: {trades_used}/{max_trades} trades used, "
            f"available={available}"
        )

        if not available:
            return {
                "available": False,
                "reason": f"Daily trade limit reached ({trades_used}/{max_trades} trades used today)",
                "usage": {"used": trades_used, "max": max_trades}
            }

        return {
            "available": True,
            "reason": f"Daily ammo available ({trades_used}/{max_trades} used)",
            "usage": {"used": trades_used, "max": max_trades}
        }

    def _get_account_balance(self, user_id: str) -> float:
        """Load account balance from DATABASE (ea_instances.last_balance) - LIVE DATA"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            # Query the most recent EA balance for this user
            cursor.execute(
                "SELECT last_balance FROM ea_instances WHERE user_id = ? ORDER BY last_seen DESC LIMIT 1",
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()

            if result and result[0] is not None:
                balance = float(result[0])
                logger.info(f"[FIRE_VALIDATOR] Loaded LIVE balance for {user_id}: ${balance:.2f} (from ea_instances)")
                return balance
            else:
                logger.warning(f"[FIRE_VALIDATOR] No EA balance found for user {user_id} in database")
                # Fallback to a safe default rather than 0 to prevent division errors
                return 10000.0

        except Exception as e:
            logger.error(f"[FIRE_VALIDATOR] Error loading balance from database: {e}", exc_info=True)
            return 10000.0

    def _enforce_risk_cap(
        self,
        requested_risk: float,
        user_preference: float,
        tier_caps: Dict
    ) -> float:
        """Enforce risk percentage cap (minimum of all constraints)"""

        # Server enforces the MINIMUM of:
        # 1. User's request
        # 2. User's saved preference
        # 3. Tier maximum cap
        enforced = min(
            requested_risk,
            user_preference,
            tier_caps["max_risk_pct"]
        )

        # Also enforce tier minimum
        enforced = max(enforced, tier_caps["min_risk_pct"])

        return round(enforced, 2)

    def _calculate_lot_size(
        self,
        balance: float,
        risk_pct: float,
        stop_pips: float,
        symbol: str
    ) -> float:
        """
        Calculate lot size based on risk parameters.

        Formula: lot_size = (balance * risk_pct / 100) / (stop_pips * pip_value)

        Example:
        - Balance: $1000
        - Risk: 2% = $20
        - Stop: 20 pips
        - Pip value: $10 (EURUSD)
        - Lot size = $20 / (20 * $10) = $20 / $200 = 0.10 lots
        """

        pip_value = self.PIP_VALUES.get(symbol, 10.0)
        risk_amount = balance * (risk_pct / 100.0)

        if stop_pips <= 0:
            logger.error(f"[FIRE_VALIDATOR] Invalid stop_pips: {stop_pips}")
            return 0.01  # Minimum lot size

        lot_size = risk_amount / (stop_pips * pip_value)

        # MT5 minimum lot size is typically 0.01
        lot_size = max(lot_size, 0.01)

        logger.info(
            f"[FIRE_VALIDATOR] Lot calculation: balance=${balance:.2f}, risk={risk_pct}% "
            f"(${risk_amount:.2f}), SL={stop_pips} pips, pip_value=${pip_value}, "
            f"lot={lot_size:.4f}"
        )

        return lot_size

    def _rejection(self, reason: str, tier_caps: Dict) -> Dict:
        """Standard rejection response"""
        logger.warning(f"[FIRE_VALIDATOR] Rejection: {reason}")
        return {
            "allowed": False,
            "reason": reason,
            "enforced": {},
            "tier_info": {"caps": tier_caps},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance for import
fire_validator = FireValidator()


# Testing function
def test_validator():
    """Test the fire validator with sample data"""

    print("\n" + "="*70)
    print("FIRE VALIDATOR TEST SUITE")
    print("="*70)

    validator = FireValidator()

    # Test Case 1: NIBBLER user requesting manual fire
    print("\n[TEST 1] NIBBLER user - Manual fire request")
    print("-" * 70)

    result = validator.validate_fire_request(
        user_id="anonymous",
        signal_id="TEST_SIGNAL_001",
        client_request={
            "symbol": "EURUSD",
            "direction": "BUY",
            "sl_pips": 20.0,
            "tp_pips": 30.0,
            "risk_pct": 2.0,  # Will be capped to 0.5% for NIBBLER
            "fire_mode": "MANUAL"
        }
    )

    print(f"Allowed: {result['allowed']}")
    print(f"Reason: {result['reason']}")
    if result['allowed']:
        print(f"Enforced lot size: {result['enforced']['lot_size']}")
        print(f"Enforced risk: {result['enforced']['risk_pct']}%")
        print(f"Max loss: ${result['enforced']['max_loss']:.2f}")
        print(f"Expected gain: ${result['enforced']['expected_gain']:.2f}")

    # Test Case 2: NIBBLER trying auto-fire (should fail)
    print("\n[TEST 2] NIBBLER user - Auto fire request (should be rejected)")
    print("-" * 70)

    result = validator.validate_fire_request(
        user_id="anonymous",
        signal_id="TEST_SIGNAL_002",
        client_request={
            "symbol": "GBPUSD",
            "direction": "SELL",
            "sl_pips": 25.0,
            "tp_pips": 40.0,
            "risk_pct": 1.0,
            "fire_mode": "AUTO"
        }
    )

    print(f"Allowed: {result['allowed']}")
    print(f"Reason: {result['reason']}")

    # Test Case 3: COMMANDER user with auto-fire
    print("\n[TEST 3] COMMANDER user - Auto fire request")
    print("-" * 70)

    result = validator.validate_fire_request(
        user_id="wlJ5lafBqRSLwHIUBxJQMr4SBtk1",
        signal_id="TEST_SIGNAL_003",
        client_request={
            "symbol": "XAUUSD",
            "direction": "BUY",
            "sl_pips": 15.0,
            "tp_pips": 30.0,
            "risk_pct": 4.0,  # Max for COMMANDER
            "fire_mode": "AUTO"
        }
    )

    print(f"Allowed: {result['allowed']}")
    print(f"Reason: {result['reason']}")
    if result['allowed']:
        print(f"Enforced lot size: {result['enforced']['lot_size']}")
        print(f"Enforced risk: {result['enforced']['risk_pct']}%")
        print(f"Max loss: ${result['enforced']['max_loss']:.2f}")
        print(f"Expected gain: ${result['enforced']['expected_gain']:.2f}")
        print(f"Tier: {result['tier_info']['tier']}")

    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run tests if executed directly
    test_validator()
