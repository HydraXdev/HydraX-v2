#!/usr/bin/env python3
"""
Fresh Fire Packet Builder - Real-time Trade Request Generation
Builds fresh fire packets with adjusted entries based on current market conditions
Ensures users never execute stale signals with outdated parameters
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FreshFirePacket:
    """Fresh trade request packet with adjusted parameters"""
    signal_id: str
    symbol: str
    direction: str  # BUY or SELL
    
    # Adjusted entry based on current market
    entry_price: float
    original_entry: float
    entry_adjustment_pips: float
    
    # Adjusted SL/TP maintaining R:R ratio
    stop_loss: float
    take_profit: float
    original_sl: float
    original_tp: float
    
    # Position sizing based on current balance
    lot_size: float
    risk_dollars: float
    risk_percent: float
    
    # Market conditions at execution
    current_spread: float
    expected_slippage: float
    
    # Vitality and warnings
    vitality_score: float
    execution_warnings: list
    
    # Metadata
    timestamp: datetime
    user_balance: float
    account_currency: str
    

class FreshFireBuilder:
    """
    Builds fresh fire packets with real-time adjustments
    Ensures every trade execution uses current market data
    """
    
    def __init__(self):
        self.pip_values = {
            'EURUSD': 10.0,
            'GBPUSD': 10.0,
            'USDJPY': 10.0,
            'USDCAD': 10.0,
            'AUDUSD': 10.0,
            'XAUUSD': 1.0,  # Gold has different pip value
            'BTCUSD': 0.01,  # Crypto pairs
            'ETHUSD': 0.01,
            'XRPUSD': 0.0001
        }
        
    def build_fresh_packet(
        self,
        mission_data: Dict,
        vitality_metrics: 'VitalityMetrics',
        user_profile: Dict,
        current_market: Dict
    ) -> FreshFirePacket:
        """
        Build a fresh fire packet with all adjustments applied
        
        Args:
            mission_data: Original signal/mission data
            vitality_metrics: Current vitality calculation results
            user_profile: User account information
            current_market: Current market data
            
        Returns:
            FreshFirePacket ready for execution
        """
        
        # Extract original signal data
        signal = mission_data.get('signal', mission_data)
        symbol = signal.get('symbol', 'EURUSD')
        direction = signal.get('direction', 'BUY').upper()
        
        # Get adjusted parameters from vitality metrics
        adjusted_entry = vitality_metrics.adjusted_entry
        adjusted_sl = vitality_metrics.adjusted_sl
        adjusted_tp = vitality_metrics.adjusted_tp
        
        # Calculate position size with current balance
        user_balance = user_profile.get('balance', 10000)
        risk_percent = self._get_risk_percent(user_profile)
        lot_size = self._calculate_position_size(
            symbol, 
            adjusted_entry,
            adjusted_sl,
            user_balance,
            risk_percent
        )
        
        # Calculate actual risk in dollars
        sl_pips = abs(adjusted_entry - adjusted_sl) * self._get_pip_multiplier(symbol)
        risk_dollars = sl_pips * self._get_pip_value(symbol) * lot_size
        
        # Get current market conditions
        current_spread = current_market.get('spread', 2.0)
        expected_slippage = vitality_metrics.expected_slippage_pips
        
        # Generate execution warnings
        warnings = self._generate_execution_warnings(
            vitality_metrics,
            adjusted_entry,
            signal.get('entry_price', adjusted_entry)
        )
        
        # Create fresh fire packet
        packet = FreshFirePacket(
            signal_id=mission_data.get('signal_id', f"FRESH_{symbol}_{int(datetime.now().timestamp())}"),
            symbol=symbol,
            direction=direction,
            
            # Adjusted entries
            entry_price=round(adjusted_entry, 5),
            original_entry=signal.get('entry_price', adjusted_entry),
            entry_adjustment_pips=vitality_metrics.price_drift_pips,
            
            # Adjusted SL/TP
            stop_loss=round(adjusted_sl, 5),
            take_profit=round(adjusted_tp, 5),
            original_sl=signal.get('stop_loss', adjusted_sl),
            original_tp=signal.get('take_profit', adjusted_tp),
            
            # Position sizing
            lot_size=round(lot_size, 2),
            risk_dollars=round(risk_dollars, 2),
            risk_percent=risk_percent,
            
            # Market conditions
            current_spread=current_spread,
            expected_slippage=expected_slippage,
            
            # Vitality
            vitality_score=vitality_metrics.vitality_score,
            execution_warnings=warnings,
            
            # Metadata
            timestamp=datetime.now(),
            user_balance=user_balance,
            account_currency=user_profile.get('currency', 'USD')
        )
        
        logger.info(f"Built fresh fire packet for {symbol}: Entry adjusted by {packet.entry_adjustment_pips:.1f} pips")
        
        return packet
    
    def _get_risk_percent(self, user_profile: Dict) -> float:
        """Get risk percent based on user tier and settings"""
        tier = user_profile.get('tier', 'NIBBLER')
        
        # EXPERIMENTAL: 5% risk for tonight's testing (normally 2%)
        base_risk = 5.0
        
        # Adjust based on tier or user preferences
        if tier == 'PRESS_PASS':
            return 1.0  # Demo accounts use 1%
        elif tier == 'COMMANDER':
            # EXPERIMENTAL: Commanders can use up to 5% for tonight
            return min(5.0, user_profile.get('risk_preference', 5.0))
        else:
            return base_risk
    
    def _calculate_position_size(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        balance: float,
        risk_percent: float
    ) -> float:
        """
        Calculate position size based on current balance and risk
        
        Returns:
            Lot size (standard lots)
        """
        # Calculate risk amount in account currency
        risk_amount = balance * (risk_percent / 100)
        
        # Calculate stop loss distance in pips
        pip_multiplier = self._get_pip_multiplier(symbol)
        sl_distance = abs(entry - stop_loss) * pip_multiplier
        
        if sl_distance == 0:
            logger.warning(f"Zero SL distance for {symbol}, using minimum")
            sl_distance = 10  # Minimum 10 pips
        
        # Get pip value for this symbol
        pip_value = self._get_pip_value(symbol)
        
        # Calculate lot size
        # Formula: Lot Size = Risk Amount / (SL Pips × Pip Value)
        lot_size = risk_amount / (sl_distance * pip_value)
        
        # Apply limits
        min_lot = 0.01
        max_lot = self._get_max_lot_size(symbol, balance)
        
        return max(min_lot, min(lot_size, max_lot))
    
    def _get_pip_multiplier(self, symbol: str) -> float:
        """Get pip multiplier for symbol"""
        if 'JPY' in symbol:
            return 100
        elif symbol in ['XAUUSD']:
            return 10
        elif symbol in ['BTCUSD', 'ETHUSD']:
            return 1
        elif symbol == 'XRPUSD':
            return 10000
        else:
            return 10000  # Standard forex
    
    def _get_pip_value(self, symbol: str) -> float:
        """Get pip value per standard lot for symbol"""
        return self.pip_values.get(symbol, 10.0)
    
    def _get_max_lot_size(self, symbol: str, balance: float) -> float:
        """Get maximum allowed lot size based on symbol and balance"""
        # Crypto pairs have different limits
        if symbol in ['BTCUSD', 'ETHUSD', 'XRPUSD']:
            # Max 5% of balance worth for crypto
            if symbol == 'BTCUSD':
                max_btc = (balance * 0.05) / 50000  # Assuming ~$50k per BTC
                return min(5.0, max_btc)
            elif symbol == 'ETHUSD':
                max_eth = (balance * 0.05) / 3000  # Assuming ~$3k per ETH
                return min(50.0, max_eth)
            else:  # XRPUSD
                max_xrp = (balance * 0.05) / 0.5  # Assuming ~$0.50 per XRP
                return min(10000, max_xrp)
        
        # Forex pairs - max 10% of balance / 100 (rough leverage calc)
        return min(5.0, balance / 10000)
    
    def _generate_execution_warnings(
        self,
        vitality_metrics: 'VitalityMetrics',
        adjusted_entry: float,
        original_entry: float
    ) -> list:
        """Generate warnings about the fresh packet adjustments"""
        warnings = []
        
        # Add vitality warnings
        warnings.extend(vitality_metrics.execution_warnings)
        
        # Add entry adjustment warning if significant
        entry_diff_pips = abs(adjusted_entry - original_entry) * 10000
        if entry_diff_pips > 5:
            warnings.append(f"Entry adjusted by {entry_diff_pips:.0f} pips from original")
        
        # Add spread warning if high
        if vitality_metrics.spread_ratio > 2:
            warnings.append(f"Spread increased {(vitality_metrics.spread_ratio - 1) * 100:.0f}%")
        
        # Add slippage warning if expected
        if vitality_metrics.expected_slippage_pips > 2:
            warnings.append(f"Expect {vitality_metrics.expected_slippage_pips:.0f} pips slippage")
        
        return warnings
    
    def to_trade_request(self, packet: FreshFirePacket) -> Dict:
        """
        Convert fresh fire packet to trade request format for execution
        
        Returns:
            Trade request dictionary ready for fire router
        """
        return {
            'signal_id': packet.signal_id,
            'symbol': packet.symbol,
            'direction': packet.direction,
            'entry_price': packet.entry_price,
            'stop_loss': packet.stop_loss,
            'take_profit': packet.take_profit,
            'lot_size': packet.lot_size,
            'risk_amount': packet.risk_dollars,
            'metadata': {
                'vitality_score': packet.vitality_score,
                'entry_adjusted': packet.entry_adjustment_pips > 0,
                'original_entry': packet.original_entry,
                'warnings': packet.execution_warnings,
                'timestamp': packet.timestamp.isoformat()
            }
        }
    
    def validate_packet(self, packet: FreshFirePacket) -> Tuple[bool, str]:
        """
        Validate that the fresh packet is safe to execute
        
        Returns:
            (is_valid, error_message)
        """
        # Check vitality score
        if packet.vitality_score < 20:
            return False, "Signal expired - vitality too low"
        
        # Check risk amount
        max_risk = packet.user_balance * 0.05  # Max 5% per trade
        if packet.risk_dollars > max_risk:
            return False, f"Risk too high: ${packet.risk_dollars:.2f} exceeds 5% limit"
        
        # Check lot size
        if packet.lot_size < 0.01:
            return False, "Lot size too small"
        
        # Check entry adjustment
        if packet.entry_adjustment_pips > 50:
            return False, "Entry drifted too far from original signal"
        
        # Check spread
        if packet.current_spread > 10:
            return False, "Spread too wide for safe execution"
        
        return True, ""


# Singleton instance
_fresh_builder = None

def get_fresh_fire_builder() -> FreshFireBuilder:
    """Get singleton instance of fresh fire builder"""
    global _fresh_builder
    if _fresh_builder is None:
        _fresh_builder = FreshFireBuilder()
    return _fresh_builder