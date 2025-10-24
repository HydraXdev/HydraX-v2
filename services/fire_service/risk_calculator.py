#!/usr/bin/env python3
"""
Risk Calculator Module
Position sizing based on 2% (manual) or 5% (auto) risk
"""

import logging
from typing import Dict, Tuple
from config import config

logger = logging.getLogger(__name__)


class RiskCalculator:
    """Calculates position sizes based on risk parameters"""

    def __init__(self):
        self.config = config

    def calculate_position_size(
        self,
        symbol: str,
        account_balance: float,
        entry_price: float,
        sl_price: float,
        direction: str,
        fire_mode: str = "MANUAL"
    ) -> Tuple[float, Dict]:
        """
        Calculate position size based on risk percentage

        Args:
            symbol: Trading pair (e.g., "EURUSD")
            account_balance: Current account balance
            entry_price: Entry price for trade
            sl_price: Stop loss price
            direction: "BUY" or "SELL"
            fire_mode: "MANUAL" or "AUTO"

        Returns:
            Tuple of (lot_size, calculation_details)
        """
        try:
            # Determine risk percentage based on fire mode
            if fire_mode == "AUTO":
                risk_pct = self.config.AUTO_RISK_PCT
            else:
                risk_pct = self.config.MANUAL_RISK_PCT

            # Calculate risk amount in account currency
            risk_amount = account_balance * (risk_pct / 100.0)

            # Get symbol specifications
            pip_size = self.config.get_pip_size(symbol)
            pip_value = self.config.get_pip_value(symbol)

            # Calculate SL distance in pips
            sl_pips = abs(entry_price - sl_price) / pip_size

            # Validate SL distance
            if sl_pips < 5:
                logger.warning(f"SL too tight ({sl_pips:.1f} pips), using minimum 5 pips")
                sl_pips = 5.0

            # Calculate lot size
            # Formula: lot_size = risk_amount / (sl_pips * pip_value)
            lot_size = risk_amount / (sl_pips * pip_value)

            # Round to 2 decimal places for MT5 compatibility
            lot_size = round(lot_size, 2)

            # Apply lot size limits
            min_lot = 0.01
            max_lot = 100.0

            if lot_size < min_lot:
                logger.warning(f"Lot size {lot_size} below minimum, using {min_lot}")
                lot_size = min_lot
            elif lot_size > max_lot:
                logger.warning(f"Lot size {lot_size} above maximum, using {max_lot}")
                lot_size = max_lot

            # Calculate actual risk amount with final lot size
            actual_risk = lot_size * sl_pips * pip_value
            actual_risk_pct = (actual_risk / account_balance) * 100.0

            calculation_details = {
                "account_balance": account_balance,
                "risk_pct": risk_pct,
                "risk_amount": risk_amount,
                "sl_pips": round(sl_pips, 1),
                "pip_value": pip_value,
                "lot_size": lot_size,
                "actual_risk": round(actual_risk, 2),
                "actual_risk_pct": round(actual_risk_pct, 2),
                "fire_mode": fire_mode
            }

            logger.info(
                f"Position sizing: {symbol} {direction} | "
                f"Balance: ${account_balance:.2f} | "
                f"Risk: {risk_pct}% (${risk_amount:.2f}) | "
                f"SL: {sl_pips:.1f} pips | "
                f"Lot: {lot_size:.2f}"
            )

            return lot_size, calculation_details

        except Exception as e:
            logger.error(f"Position sizing error: {e}")
            # Return minimum lot size as fallback
            return 0.01, {"error": str(e)}

    def validate_risk_limits(
        self,
        account_balance: float,
        lot_size: float,
        sl_pips: float,
        pip_value: float
    ) -> Tuple[bool, str]:
        """
        Validate if risk is within acceptable limits

        Args:
            account_balance: Current account balance
            lot_size: Calculated lot size
            sl_pips: Stop loss distance in pips
            pip_value: Pip value for symbol

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Calculate actual risk
            risk_amount = lot_size * sl_pips * pip_value
            risk_pct = (risk_amount / account_balance) * 100.0

            # Check against maximum risk
            if risk_pct > self.config.MAX_RISK_PCT:
                return False, f"Risk {risk_pct:.1f}% exceeds maximum {self.config.MAX_RISK_PCT}%"

            # Check minimum account balance
            if account_balance < 100:
                return False, f"Account balance ${account_balance:.2f} too low (minimum $100)"

            return True, ""

        except Exception as e:
            logger.error(f"Risk validation error: {e}")
            return False, str(e)

    def get_optimal_sl_distance(
        self,
        symbol: str,
        entry_price: float,
        direction: str,
        atr: float = None
    ) -> float:
        """
        Calculate optimal SL distance based on symbol and volatility

        Args:
            symbol: Trading pair
            entry_price: Entry price
            direction: "BUY" or "SELL"
            atr: Average True Range (optional)

        Returns:
            Optimal SL price
        """
        pip_size = self.config.get_pip_size(symbol)

        # Use ATR-based SL if available
        if atr:
            sl_distance = atr * 1.5  # 1.5x ATR
        else:
            # Default SL distances by symbol
            defaults = {
                "EURUSD": 20,
                "GBPUSD": 25,
                "USDJPY": 20,
                "EURJPY": 25,
                "GBPJPY": 30,
                "XAUUSD": 150,
                "XAGUSD": 30,
            }
            sl_pips = defaults.get(symbol, 20)
            sl_distance = sl_pips * pip_size

        # Calculate SL price
        if direction == "BUY":
            sl_price = entry_price - sl_distance
        else:
            sl_price = entry_price + sl_distance

        return sl_price


# Create singleton instance
risk_calculator = RiskCalculator()
