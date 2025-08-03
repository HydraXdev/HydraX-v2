#!/usr/bin/env python3
"""
🚀 C.O.R.E. Crypto Fire Packet Builder
Advanced crypto signal execution system for BITTEN Trading Platform

This system seamlessly integrates with existing fire execution while handling
crypto-specific requirements like dollar-to-point conversion and position sizing.

Integration Points:
- bitten_core.py: execute_fire_command() 
- fire_router.py: execute_trade_request()
- EA ZMQ Commands: Properly formatted crypto execution

Author: Claude Code Agent
Date: August 2025
Status: Production Ready
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Signal type classification"""
    FOREX = "forex"
    CRYPTO = "crypto"
    UNKNOWN = "unknown"

class CryptoSymbol(Enum):
    """C.O.R.E. Supported Crypto Symbols - BTCUSD, ETHUSD, XRPUSD"""
    BTCUSD = {
        "symbol": "BTCUSD",
        "point_value": 0.01,  # 1 point = $0.01
        "lot_size": 1.0,      # 1 lot = 1 BTC
        "min_lot": 0.01,      # Minimum position size
        "max_lot": 5.0,       # Maximum position size (conservative)
        "pip_multiplier": 1,   # 1 pip = 1 point for crypto
        "margin_currency": "USD",
        "typical_spread": 50.0  # ~$50 spread
    }
    
    ETHUSD = {
        "symbol": "ETHUSD", 
        "point_value": 0.01,  # 1 point = $0.01
        "lot_size": 1.0,      # 1 lot = 1 ETH
        "min_lot": 0.01,      # Minimum position size
        "max_lot": 50.0,      # Maximum position size
        "pip_multiplier": 1,   # 1 pip = 1 point for crypto
        "margin_currency": "USD",
        "typical_spread": 5.0   # ~$5 spread
    }
    
    XRPUSD = {
        "symbol": "XRPUSD",
        "point_value": 0.0001, # 1 point = $0.0001 (XRP trades in smaller increments)
        "lot_size": 1.0,       # 1 lot = 1 XRP
        "min_lot": 1.0,        # Minimum 1 XRP
        "max_lot": 10000.0,    # Maximum 10,000 XRP
        "pip_multiplier": 1,    # 1 pip = 1 point for crypto
        "margin_currency": "USD",
        "typical_spread": 0.002 # ~$0.002 spread
    }

@dataclass
class CryptoSignalData:
    """Enhanced signal data structure for crypto signals"""
    signal_id: str
    symbol: str
    direction: str  # "BUY" or "SELL"
    entry_price: float
    stop_loss_dollars: float  # Dollar amount (e.g., 1000.0)
    take_profit_dollars: float  # Dollar amount (e.g., 2000.0)
    confidence: float
    pattern: str
    xp_reward: int
    timestamp: str
    engine: str = "CORE"
    signal_type: SignalType = SignalType.CRYPTO

@dataclass 
class CryptoTradePacket:
    """Formatted trade packet ready for EA execution"""
    symbol: str
    action: str  # "buy" or "sell" 
    lot: float
    sl: float  # Stop loss in points
    tp: float  # Take profit in points
    signal_id: str
    comment: str
    risk_amount: float
    account_balance: float

class CryptoSignalDetector:
    """Intelligent crypto signal detection system"""
    
    def __init__(self):
        # C.O.R.E. Official Trading Pairs
        self.crypto_symbols = {"BTCUSD", "ETHUSD", "XRPUSD"}
        self.crypto_engines = {"CORE", "C.O.R.E"}
        self.crypto_patterns = {"Sweep Reversal", "Smart Money", "Liquidity Hunt", "Breakout", "SMC Pattern"}
        
    def detect_signal_type(self, signal_data: Dict) -> SignalType:
        """Detect if signal is crypto or forex"""
        try:
            # Check symbol
            symbol = signal_data.get('symbol', '').upper()
            if symbol in self.crypto_symbols:
                return SignalType.CRYPTO
                
            # Check engine
            engine = signal_data.get('engine', '').upper()
            if engine in self.crypto_engines:
                return SignalType.CRYPTO
                
            # Check signal ID pattern
            signal_id = signal_data.get('signal_id', '').lower()
            if 'btc' in signal_id or 'crypto' in signal_id or 'core' in signal_id:
                return SignalType.CRYPTO
                
            # Check for dollar-based SL/TP (crypto characteristic)
            if 'sl' in signal_data and 'tp' in signal_data:
                sl = signal_data.get('sl', 0)
                tp = signal_data.get('tp', 0)
                # If SL/TP are large numbers, likely dollar amounts (crypto)
                if sl > 500 or tp > 500:
                    return SignalType.CRYPTO
                    
            # Default to forex
            return SignalType.FOREX
            
        except Exception as e:
            logger.error(f"Error detecting signal type: {e}")
            return SignalType.UNKNOWN

class DollarToPointConverter:
    """Advanced dollar-to-point conversion for crypto symbols"""
    
    def __init__(self):
        # C.O.R.E. Official Trading Pairs Specifications
        self.symbol_specs = {
            "BTCUSD": CryptoSymbol.BTCUSD.value,
            "ETHUSD": CryptoSymbol.ETHUSD.value,
            "XRPUSD": CryptoSymbol.XRPUSD.value
        }
        
    def convert_dollars_to_points(self, symbol: str, dollar_amount: float, current_price: float) -> float:
        """Convert dollar amount to points for specific crypto symbol"""
        try:
            if symbol not in self.symbol_specs:
                logger.warning(f"Unknown crypto symbol {symbol}, using default conversion")
                # Default conversion: assume 1 point = $0.01
                return dollar_amount / 0.01
                
            spec = self.symbol_specs[symbol]
            point_value = spec["point_value"]
            
            # For crypto: points = dollar_amount / point_value
            points = dollar_amount / point_value
            
            logger.info(f"💱 Converted ${dollar_amount} → {points} points for {symbol}")
            return points
            
        except Exception as e:
            logger.error(f"Error converting dollars to points: {e}")
            return dollar_amount / 0.01  # Safe fallback

class CryptoPositionSizer:
    """Intelligent position sizing for crypto trading with professional risk management"""
    
    def __init__(self):
        # C.O.R.E. Crypto Trading Settings (Always)
        self.default_risk_percent = 1.0  # 1% risk per trade (tighter for 55-65% win rates)
        self.max_daily_drawdown = 4.0    # 4% daily drawdown cap (4 losses max)
        self.risk_reward_ratio = 2.0     # 1:2 RR for all signals (prioritize reward)
        self.atr_multiplier = 3.0        # SL = ATR * 3 for crypto volatility
        
        # Expected performance: 55-65% win rate, ~0.65% per trade, 3 trades/day = 1.95% daily
        self.max_position_size = 1.0     # Maximum 1 BTC per trade
        
    def calculate_crypto_position_size_atr(self, 
                                         account_balance: float,
                                         symbol: str, 
                                         entry_price: float,
                                         atr_value: float = None,
                                         risk_percent: float = None,
                                         trades_today: int = 0) -> Tuple[float, float, float, Dict]:
        """
        Calculate crypto position size using ATR-based professional risk management
        
        Returns: (position_size, sl_pips, tp_pips, calculation_details)
        """
        try:
            risk_percent = risk_percent or self.default_risk_percent
            
            # Daily drawdown protection: reduce risk if approaching limit
            daily_loss_count = trades_today  # Assume worst case (all losses)
            if daily_loss_count >= 3:  # 3 losses = 3% drawn down, reduce risk for 4th trade
                risk_percent = risk_percent * 0.5  # Reduce risk for final trade
                logger.info(f"⚠️ Daily drawdown protection: Reducing risk to {risk_percent:.1f}%")
            
            # Calculate risk amount in dollars (1% of equity)
            risk_amount = account_balance * (risk_percent / 100)
            
            # Get symbol specifications for C.O.R.E. pairs
            if symbol == "BTCUSD":
                spec = CryptoSymbol.BTCUSD.value
                # BTCUSD: High volatility, wider stops needed
                default_atr = 50.0 if atr_value is None else atr_value  # 50 pips ATR example
                pip_value = 10.0  # $10 per pip for BTCUSD (assuming 1 lot = 1 BTC)
            elif symbol == "ETHUSD":
                spec = CryptoSymbol.ETHUSD.value
                # ETHUSD: Medium volatility
                default_atr = 30.0 if atr_value is None else atr_value  # 30 pips ATR example
                pip_value = 1.0   # $1 per pip for ETHUSD (assuming 1 lot = 1 ETH)
            elif symbol == "XRPUSD":
                spec = CryptoSymbol.XRPUSD.value
                # XRPUSD: Lower price, tighter stops
                default_atr = 20.0 if atr_value is None else atr_value  # 20 pips ATR example
                pip_value = 0.01  # $0.01 per pip for XRPUSD
            else:
                # Default specs for unknown crypto
                spec = {"min_lot": 0.01, "max_lot": 10.0, "point_value": 0.01}
                default_atr = 30.0
                pip_value = 1.0
            
            # Calculate stop loss: ATR * 3 (for crypto volatility)
            sl_pips = default_atr * self.atr_multiplier
            
            # Calculate take profit: SL * 2 (1:2 Risk:Reward for all signals)
            tp_pips = sl_pips * self.risk_reward_ratio
            
            # Calculate position size based on risk and stop loss
            # Position Size = Risk Amount / (Stop Loss Pips * Pip Value)
            sl_dollar_risk = sl_pips * pip_value
            
            if sl_dollar_risk <= 0:
                logger.warning("Invalid stop loss calculation")
                position_size = spec["min_lot"]
            else:
                position_size = risk_amount / sl_dollar_risk
            
            # Apply min/max constraints
            position_size = max(position_size, spec["min_lot"])
            position_size = min(position_size, spec["max_lot"])
            position_size = min(position_size, self.max_position_size)
            
            # Round to appropriate precision for each symbol
            if symbol == "BTCUSD":
                position_size = round(position_size, 2)  # 0.01 BTC precision
            elif symbol == "ETHUSD":
                position_size = round(position_size, 2)  # 0.01 ETH precision
            elif symbol == "XRPUSD":
                position_size = round(position_size, 0)  # 1 XRP precision
            else:
                position_size = round(position_size, 2)
            
            # Calculate expected values
            expected_loss = risk_amount  # 1% loss if SL hit
            expected_gain = risk_amount * self.risk_reward_ratio  # 2% gain if TP hit
            expected_value = (0.60 * expected_gain) - (0.40 * expected_loss)  # 60% win rate assumption
            
            calculation_details = {
                "account_balance": account_balance,
                "risk_percent": risk_percent,
                "risk_amount": risk_amount,
                "atr_value": default_atr,
                "sl_pips": sl_pips,
                "tp_pips": tp_pips,
                "pip_value": pip_value,
                "position_size": position_size,
                "symbol": symbol,
                "entry_price": entry_price,
                "risk_reward_ratio": self.risk_reward_ratio,
                "expected_loss": expected_loss,
                "expected_gain": expected_gain,
                "expected_value": expected_value,
                "trades_today": trades_today,
                "daily_protection_active": daily_loss_count >= 3
            }
            
            logger.info(f"💰 Professional crypto position calculated: {position_size} {symbol}")
            logger.info(f"📊 Risk: ${risk_amount:.2f} ({risk_percent:.1f}% of ${account_balance:.2f})")
            logger.info(f"🎯 SL: {sl_pips:.0f} pips | TP: {tp_pips:.0f} pips (1:{self.risk_reward_ratio:.0f} RR)")
            logger.info(f"💡 Expected Value: ${expected_value:.2f} per trade (60% win rate)")
            
            return position_size, sl_pips, tp_pips, calculation_details
            
        except Exception as e:
            logger.error(f"Error calculating professional crypto position size: {e}")
            return 0.01, 50.0, 100.0, {"error": str(e)}  # Safe fallback values
    
    def calculate_crypto_position_size(self, 
                                     account_balance: float,
                                     symbol: str, 
                                     entry_price: float,
                                     stop_loss_points: float = None,
                                     risk_percent: float = None) -> Tuple[float, Dict]:
        """Legacy method - calls new ATR-based method for compatibility"""
        position_size, sl_pips, tp_pips, details = self.calculate_crypto_position_size_atr(
            account_balance, symbol, entry_price, None, risk_percent, 0
        )
        
        # Convert pips back to points for compatibility
        if symbol == "BTCUSD":
            sl_points = sl_pips * 100  # 1 pip = 100 points for BTC
            tp_points = tp_pips * 100
        elif symbol == "ETHUSD":
            sl_points = sl_pips * 100  # 1 pip = 100 points for ETH  
        elif symbol == "XRPUSD":
            sl_points = sl_pips * 10000  # 1 pip = 10000 points for XRP
        else:
            sl_points = sl_pips * 100
            tp_points = tp_pips * 100
        
        details["stop_loss_points"] = sl_points
        details["take_profit_points"] = tp_points
        
        return position_size, details

class CryptoFirePacketBuilder:
    """Main crypto fire packet builder - integrates all components"""
    
    def __init__(self):
        self.detector = CryptoSignalDetector()
        self.converter = DollarToPointConverter()
        self.position_sizer = CryptoPositionSizer()
        self.stats = {
            "crypto_signals_processed": 0,
            "forex_signals_processed": 0,
            "conversion_errors": 0,
            "successful_packets": 0
        }
        
    def is_crypto_signal(self, signal_data: Dict) -> bool:
        """Quick check if signal is crypto"""
        signal_type = self.detector.detect_signal_type(signal_data)
        return signal_type == SignalType.CRYPTO
        
    def build_crypto_fire_packet(self, 
                                signal_data: Dict, 
                                user_profile: Dict,
                                account_balance: float = 10000.0) -> Optional[CryptoTradePacket]:
        """Build complete crypto fire packet ready for EA execution"""
        try:
            logger.info(f"🔥 Building crypto fire packet for signal: {signal_data.get('signal_id', 'unknown')}")
            
            # Extract signal data
            signal_id = signal_data.get('signal_id', signal_data.get('uuid', ''))
            symbol = signal_data.get('symbol', 'BTCUSD')
            direction = signal_data.get('direction', 'BUY').upper()
            entry_price = float(signal_data.get('entry', signal_data.get('entry_price', 67000.0)))
            
            # Handle dollar-based SL/TP from C.O.R.E. signals
            sl_dollars = float(signal_data.get('sl', 1000.0))  # Default $1000 SL
            tp_dollars = float(signal_data.get('tp', 2000.0))  # Default $2000 TP
            
            # Convert dollars to points
            sl_points = self.converter.convert_dollars_to_points(symbol, sl_dollars, entry_price)
            tp_points = self.converter.convert_dollars_to_points(symbol, tp_dollars, entry_price)
            
            # Calculate position size
            risk_percent = user_profile.get('risk_percent', 2.0)
            position_size, sizing_details = self.position_sizer.calculate_crypto_position_size(
                account_balance=account_balance,
                symbol=symbol,
                entry_price=entry_price,
                stop_loss_points=sl_points,
                risk_percent=risk_percent
            )
            
            # Build trade packet
            trade_packet = CryptoTradePacket(
                symbol=symbol,
                action=direction.lower(),  # EA expects lowercase
                lot=position_size,
                sl=sl_points,
                tp=tp_points,
                signal_id=signal_id,
                comment=f"CORE {signal_data.get('pattern', 'Unknown')} {signal_data.get('confidence', 0):.1f}%",
                risk_amount=sizing_details.get('risk_amount', 0),
                account_balance=account_balance
            )
            
            # Update stats
            self.stats["crypto_signals_processed"] += 1
            self.stats["successful_packets"] += 1
            
            logger.info(f"✅ Crypto fire packet built successfully:")
            logger.info(f"   Symbol: {trade_packet.symbol}")
            logger.info(f"   Action: {trade_packet.action}")
            logger.info(f"   Position: {trade_packet.lot} lots")
            logger.info(f"   SL: {trade_packet.sl} points (${sl_dollars})")
            logger.info(f"   TP: {trade_packet.tp} points (${tp_dollars})")
            logger.info(f"   Risk: ${trade_packet.risk_amount:.2f}")
            
            return trade_packet
            
        except Exception as e:
            logger.error(f"❌ Error building crypto fire packet: {e}")
            self.stats["conversion_errors"] += 1
            return None
            
    def convert_to_zmq_command(self, trade_packet: CryptoTradePacket) -> Dict:
        """Convert crypto trade packet to ZMQ command format for EA"""
        try:
            zmq_command = {
                "type": "signal",
                "symbol": trade_packet.symbol,
                "action": trade_packet.action,
                "lot": trade_packet.lot,
                "sl": trade_packet.sl,
                "tp": trade_packet.tp,
                "signal_id": trade_packet.signal_id,
                "comment": trade_packet.comment,
                "timestamp": datetime.now().isoformat(),
                "source": "CORE_CRYPTO"
            }
            
            logger.info(f"📡 ZMQ command formatted for EA: {zmq_command}")
            return zmq_command
            
        except Exception as e:
            logger.error(f"Error converting to ZMQ command: {e}")
            return {}
            
    def get_stats(self) -> Dict:
        """Get builder statistics"""
        return {
            **self.stats,
            "success_rate": (self.stats["successful_packets"] / max(1, self.stats["crypto_signals_processed"])) * 100
        }

# Global instance for easy integration
crypto_fire_builder = CryptoFirePacketBuilder()

def build_crypto_fire_packet(signal_data: Dict, user_profile: Dict, account_balance: float = 10000.0) -> Optional[CryptoTradePacket]:
    """Convenience function for building crypto fire packets"""
    return crypto_fire_builder.build_crypto_fire_packet(signal_data, user_profile, account_balance)

def is_crypto_signal(signal_data: Dict) -> bool:
    """Convenience function for crypto signal detection"""
    return crypto_fire_builder.is_crypto_signal(signal_data)

def convert_crypto_packet_to_zmq(trade_packet: CryptoTradePacket) -> Dict:
    """Convenience function for ZMQ conversion"""
    return crypto_fire_builder.convert_to_zmq_command(trade_packet)

if __name__ == "__main__":
    # Test crypto fire packet builder
    test_signal = {
        "signal_id": "btc-mission-test-001",
        "symbol": "BTCUSD",
        "direction": "BUY",
        "entry": 67245.50,
        "sl": 1000.0,  # $1000 stop loss
        "tp": 2000.0,  # $2000 take profit
        "confidence": 78.5,
        "pattern": "Liquidity Sweep Reversal",
        "engine": "CORE"
    }
    
    test_user = {
        "tier": "NIBBLER",
        "risk_percent": 2.0
    }
    
    # Test detection
    is_crypto = is_crypto_signal(test_signal)
    print(f"🔍 Signal detected as crypto: {is_crypto}")
    
    # Test packet building
    if is_crypto:
        packet = build_crypto_fire_packet(test_signal, test_user, 10000.0)
        if packet:
            print(f"✅ Crypto fire packet built: {packet}")
            
            # Test ZMQ conversion
            zmq_cmd = convert_crypto_packet_to_zmq(packet)
            print(f"📡 ZMQ command: {zmq_cmd}")
        else:
            print("❌ Failed to build crypto fire packet")
    
    # Show stats
    stats = crypto_fire_builder.get_stats()
    print(f"📊 Builder stats: {stats}")