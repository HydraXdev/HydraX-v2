#!/usr/bin/env python3
"""
BITTEN Dynamic Position Sizing System
Calculates position size based on 2% max account risk for ALL tiers
"""

import math
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DynamicPositionSizing:
    """
    Dynamic position sizing with 2% max risk for all user tiers
    """
    
    def __init__(self):
        self.max_risk_percent = 0.02  # 2% maximum risk per trade
        self.min_lot_size = 0.01      # Minimum broker lot size
        self.max_lot_size = 100.0     # Maximum reasonable lot size
        
    def calculate_position_size(self, 
                              account_balance: float,
                              entry_price: float,
                              stop_loss: float,
                              symbol: str = "EURUSD",
                              user_tier: str = "NIBBLER") -> Dict:
        """
        Calculate optimal position size based on 2% risk rule
        
        Args:
            account_balance: User's current account balance
            entry_price: Trade entry price
            stop_loss: Stop loss price
            symbol: Trading symbol
            user_tier: User tier (for logging only - 2% applies to ALL)
            
        Returns:
            Dict with position size and risk metrics
        """
        try:
            # Calculate risk amount (2% of account)
            risk_amount = account_balance * self.max_risk_percent
            
            # Calculate pip value based on symbol
            pip_value = self._get_pip_value(symbol, entry_price)
            
            # Calculate stop loss distance in pips
            sl_distance_pips = abs(entry_price - stop_loss) / pip_value
            
            # Calculate position size
            # For standard lot: 1 pip = $10 for EURUSD
            # Risk Amount = Pip Distance × $10 per pip × Lot Size
            # Lot Size = Risk Amount / (Pip Distance × $10 per pip)
            
            if sl_distance_pips > 0:
                # Standard calculation: $10 per pip per standard lot for major pairs
                dollars_per_pip_per_lot = 10.0 if "JPY" not in symbol else 1.0
                calculated_lot_size = risk_amount / (sl_distance_pips * dollars_per_pip_per_lot)
            else:
                calculated_lot_size = self.min_lot_size
                
            # Apply lot size constraints
            lot_size = max(self.min_lot_size, min(calculated_lot_size, self.max_lot_size))
            
            # Round to broker lot step (usually 0.01)
            lot_size = round(lot_size, 2)
            
            # Calculate actual risk with final lot size
            dollars_per_pip_per_lot = 10.0 if "JPY" not in symbol else 1.0
            actual_risk = sl_distance_pips * dollars_per_pip_per_lot * lot_size
            actual_risk_percent = (actual_risk / account_balance) * 100
            
            result = {
                "lot_size": lot_size,
                "volume": lot_size,  # Alias for compatibility
                "risk_amount": actual_risk,
                "risk_percent": actual_risk_percent,
                "sl_distance_pips": sl_distance_pips,
                "pip_value": pip_value,
                "account_balance": account_balance,
                "user_tier": user_tier,
                "max_risk_percent": self.max_risk_percent * 100,
                "calculation_method": "2% Dynamic Risk for All Tiers"
            }
            
            logger.info(f"Position sizing for {user_tier}: {lot_size} lots, "
                       f"{actual_risk_percent:.2f}% risk, ${actual_risk:.2f} at risk")
            
            return result
            
        except Exception as e:
            logger.error(f"Position sizing calculation failed: {e}")
            # Fallback to minimum safe size
            return {
                "lot_size": self.min_lot_size,
                "volume": self.min_lot_size,
                "risk_amount": 0,
                "risk_percent": 0,
                "error": str(e),
                "calculation_method": "Fallback - Minimum Size"
            }
    
    def _get_pip_value(self, symbol: str, price: float) -> float:
        """
        Get pip value for different symbols
        """
        symbol = symbol.upper()
        
        # Major USD pairs (pip = 0.0001)
        if symbol in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"]:
            return 0.0001
            
        # JPY pairs (pip = 0.01)
        elif "JPY" in symbol:
            return 0.01
            
        # Gold/XAU (pip = 0.01)
        elif "XAU" in symbol or "GOLD" in symbol:
            return 0.01
            
        # Default to standard pip
        else:
            return 0.0001
    
    def get_tier_info(self, user_tier: str) -> Dict:
        """
        Get tier information (all tiers now use same 2% risk)
        """
        return {
            "tier": user_tier,
            "max_risk_percent": self.max_risk_percent * 100,
            "risk_rule": "2% maximum account risk per trade",
            "position_sizing": "Dynamic based on account balance and stop loss",
            "note": "All tiers use same risk management rules"
        }

def calculate_dynamic_position_size(account_balance: float,
                                  entry_price: float, 
                                  stop_loss: float,
                                  symbol: str = "EURUSD",
                                  user_tier: str = "NIBBLER") -> Dict:
    """
    Convenience function for dynamic position sizing
    """
    sizer = DynamicPositionSizing()
    return sizer.calculate_position_size(
        account_balance=account_balance,
        entry_price=entry_price,
        stop_loss=stop_loss,
        symbol=symbol,
        user_tier=user_tier
    )

# Quick test function
def test_position_sizing():
    """Test the position sizing system"""
    sizer = DynamicPositionSizing()
    
    test_cases = [
        # (balance, entry, sl, symbol, tier)
        (10000, 1.0900, 1.0850, "EURUSD", "NIBBLER"),
        (10000, 1.0900, 1.0850, "EURUSD", "FANG"), 
        (10000, 1.0900, 1.0850, "EURUSD", "COMMANDER"),
        (5000, 150.50, 149.50, "USDJPY", "NIBBLER"),
        (25000, 1.2600, 1.2550, "GBPUSD", "COMMANDER"),
    ]
    
    print("🎯 DYNAMIC POSITION SIZING TEST")
    print("=" * 50)
    
    for balance, entry, sl, symbol, tier in test_cases:
        result = sizer.calculate_position_size(balance, entry, sl, symbol, tier)
        print(f"\n{tier} - {symbol}:")
        print(f"  Balance: ${balance:,.2f}")
        print(f"  Entry: {entry}, SL: {sl}")
        print(f"  Position: {result['lot_size']} lots")
        print(f"  Risk: {result['risk_percent']:.2f}% (${result['risk_amount']:.2f})")

if __name__ == "__main__":
    test_position_sizing()