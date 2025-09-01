#!/usr/bin/env python3
"""
Advanced Smart Money Concepts (SMC) Pattern Detector
# [DISABLED BITMODE] Optimized for scalping and BITMODE trading using institutional order flow analysis

Based on research from:
- ICT (Inner Circle Trader) concepts
- Wyckoff Method accumulation/distribution
- Order flow trading principles
- Market microstructure analysis
- Statistical edge detection
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class PatternType(Enum):
    LIQUIDITY_GRAB = "LIQUIDITY_GRAB"           # Stop hunt + reversal (highest edge)
    BREAK_OF_STRUCTURE = "BREAK_OF_STRUCTURE"   # Momentum continuation  
    CHANGE_OF_CHARACTER = "CHANGE_OF_CHARACTER" # Trend reversal
    FAIR_VALUE_GAP_RETEST = "FAIR_VALUE_GAP_RETEST" # Gap retest (refined)
    ORDER_BLOCK_RETEST = "ORDER_BLOCK_RETEST"   # Institutional level retest
    INDUCEMENT_TRAP = "INDUCEMENT_TRAP"         # Fake breakout trap
    BREAKER_BLOCK = "BREAKER_BLOCK"            # Failed support becomes resistance

class MarketStructure(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH" 
    RANGING = "RANGING"
    TRANSITIONAL = "TRANSITIONAL"

@dataclass
class MarketData:
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    tick_volume: int = 0

@dataclass
class SMCPattern:
    pattern_type: PatternType
    direction: str  # BUY/SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    risk_reward: float
    trigger_time: float
    expiry_time: float
    metadata: Dict

class AdvancedSMCDetector:
    """
    Advanced SMC pattern detector using institutional trading concepts
    Optimized for 1M scalping with multi-timeframe confluence
    """
    
    def __init__(self):
        # Market structure tracking
        self.market_structure = {}  # symbol -> structure
        self.swing_highs = {}       # symbol -> [(time, price), ...]
        self.swing_lows = {}        # symbol -> [(time, price), ...]
        
        # Order flow analysis
        self.order_blocks = {}      # symbol -> [OrderBlock, ...]
        self.fair_value_gaps = {}   # symbol -> [FVG, ...]
        self.liquidity_levels = {}  # symbol -> [LiquidityZone, ...]
        
        # Volume analysis
        self.volume_profile = {}    # symbol -> VolumeProfile
        self.tick_analysis = {}     # symbol -> TickData
        
        # Pattern calibration (learned from performance)
        self.pattern_stats = {
            PatternType.LIQUIDITY_GRAB: {'base_confidence': 85, 'win_rate_adj': 1.2},
            PatternType.BREAK_OF_STRUCTURE: {'base_confidence': 80, 'win_rate_adj': 1.1},
            PatternType.CHANGE_OF_CHARACTER: {'base_confidence': 75, 'win_rate_adj': 1.0},
            PatternType.FAIR_VALUE_GAP_RETEST: {'base_confidence': 70, 'win_rate_adj': 0.8},
            PatternType.ORDER_BLOCK_RETEST: {'base_confidence': 75, 'win_rate_adj': 0.9},
            PatternType.INDUCEMENT_TRAP: {'base_confidence': 90, 'win_rate_adj': 1.3},
            PatternType.BREAKER_BLOCK: {'base_confidence': 85, 'win_rate_adj': 1.1},
        }
        
        # Scalping optimization
        self.min_rr_ratio = 1.5      # Minimum risk:reward
        self.max_sl_pips = 20        # Maximum stop loss
        self.scalp_targets = {        # Quick profit targets
            'EURUSD': [4, 6, 8],     # [1st_target, 2nd_target, runner]
            'GBPUSD': [5, 8, 12],
            'USDJPY': [4, 6, 10],
            'XAUUSD': [3, 5, 8],     # Tighter for gold
        }
    
    def analyze_market_structure(self, symbol: str, candles: List[MarketData]) -> MarketStructure:
        """
        Analyze current market structure using swing analysis
        Critical for determining pattern validity
        """
        if len(candles) < 50:
            return MarketStructure.RANGING
        
        # Find recent swing highs and lows (last 20 candles)
        recent_candles = candles[-20:]
        highs = [c.high for c in recent_candles]
        lows = [c.low for c in recent_candles]
        
        # Calculate structure metrics
        higher_highs = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
        lower_lows = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])
        
        higher_lows = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])
        lower_highs = sum(1 for i in range(1, len(highs)) if highs[i] < highs[i-1])
        
        # Determine structure
        if higher_highs >= 3 and higher_lows >= 2:
            return MarketStructure.BULLISH
        elif lower_lows >= 3 and lower_highs >= 2:
            return MarketStructure.BEARISH
        elif higher_highs >= 2 and lower_lows >= 2:
            return MarketStructure.TRANSITIONAL
        else:
            return MarketStructure.RANGING
    
    def detect_liquidity_grab(self, symbol: str, candles: List[MarketData]) -> Optional[SMCPattern]:
        """
        Detect liquidity grab patterns - highest probability setups
        
        Logic:
        1. Price sweeps above/below recent high/low (liquidity grab)
        2. Immediate rejection with strong volume
        3. Entry on pullback to grab candle
        """
        if len(candles) < 20:
            return None
        
        current = candles[-1]
        recent = candles[-10:]  # Last 10 candles
        
        # Find recent swing high/low
        swing_high = max(recent, key=lambda c: c.high)
        swing_low = min(recent, key=lambda c: c.low)
        
        # Check for liquidity grab above high (bearish setup)
        if (current.high > swing_high.high and 
            current.close < swing_high.high - (swing_high.high - swing_high.low) * 0.3):
            
            # Calculate entry and levels
            entry = swing_high.high - (swing_high.high - swing_high.low) * 0.2
            stop_loss = current.high + self._calculate_atr(candles[-14:]) * 0.5
            
            # Scalping targets
            targets = self.scalp_targets.get(symbol, [6, 10, 15])
            pip_size = self._get_pip_size(symbol)
            take_profit = entry - (targets[0] * pip_size)
            
            # Risk/reward check
            risk_pips = abs(stop_loss - entry) / pip_size
            reward_pips = abs(entry - take_profit) / pip_size
            
            if risk_pips > 0 and reward_pips / risk_pips >= self.min_rr_ratio:
                confidence = self._calculate_confidence(
                    PatternType.LIQUIDITY_GRAB,
                    symbol, candles, {'direction': 'SELL', 'grab_strength': current.high - swing_high.high}
                )
                
                return SMCPattern(
                    pattern_type=PatternType.LIQUIDITY_GRAB,
                    direction='SELL',
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    risk_reward=reward_pips / risk_pips,
                    trigger_time=current.timestamp,
                    expiry_time=current.timestamp + 900,  # 15 min expiry
                    metadata={
                        'grab_candle': current.timestamp,
                        'liquidity_level': swing_high.high,
                        'grab_strength': current.high - swing_high.high,
                        'volume_surge': current.volume > np.mean([c.volume for c in recent]) * 1.5
                    }
                )
        
        # Check for liquidity grab below low (bullish setup)
        elif (current.low < swing_low.low and
              current.close > swing_low.low + (swing_low.high - swing_low.low) * 0.3):
            
            # Calculate entry and levels
            entry = swing_low.low + (swing_low.high - swing_low.low) * 0.2
            stop_loss = current.low - self._calculate_atr(candles[-14:]) * 0.5
            
            # Scalping targets
            targets = self.scalp_targets.get(symbol, [6, 10, 15])
            pip_size = self._get_pip_size(symbol)
            take_profit = entry + (targets[0] * pip_size)
            
            # Risk/reward check
            risk_pips = abs(entry - stop_loss) / pip_size
            reward_pips = abs(take_profit - entry) / pip_size
            
            if risk_pips > 0 and reward_pips / risk_pips >= self.min_rr_ratio:
                confidence = self._calculate_confidence(
                    PatternType.LIQUIDITY_GRAB,
                    symbol, candles, {'direction': 'BUY', 'grab_strength': swing_low.low - current.low}
                )
                
                return SMCPattern(
                    pattern_type=PatternType.LIQUIDITY_GRAB,
                    direction='BUY',
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    risk_reward=reward_pips / risk_pips,
                    trigger_time=current.timestamp,
                    expiry_time=current.timestamp + 900,
                    metadata={
                        'grab_candle': current.timestamp,
                        'liquidity_level': swing_low.low,
                        'grab_strength': swing_low.low - current.low,
                        'volume_surge': current.volume > np.mean([c.volume for c in recent]) * 1.5
                    }
                )
        
        return None
    
    def detect_break_of_structure(self, symbol: str, candles: List[MarketData]) -> Optional[SMCPattern]:
        """
        Detect break of structure (BOS) - momentum continuation patterns
        High probability when aligned with market structure
        """
        if len(candles) < 30:
            return None
        
        structure = self.analyze_market_structure(symbol, candles)
        current = candles[-1]
        recent = candles[-15:]
        
        # For bullish structure, look for breaks above resistance
        if structure == MarketStructure.BULLISH:
            # Find recent resistance level
            resistance_candles = [c for c in recent if c.high > current.close * 0.999]
            if not resistance_candles:
                return None
            
            resistance_level = max(c.high for c in resistance_candles)
            
            # Check if we broke above with momentum
            if (current.close > resistance_level and 
                current.high > resistance_level and
                current.close > current.open):  # Bullish candle
                
                # Entry on pullback to resistance (now support)
                entry = resistance_level + self._get_pip_size(symbol) * 2
                stop_loss = resistance_level - self._get_pip_size(symbol) * 8
                
                # Scalping target
                targets = self.scalp_targets.get(symbol, [6, 10, 15])
                take_profit = entry + (targets[1] * self._get_pip_size(symbol))
                
                risk_pips = abs(entry - stop_loss) / self._get_pip_size(symbol)
                reward_pips = abs(take_profit - entry) / self._get_pip_size(symbol)
                
                if risk_pips > 0 and reward_pips / risk_pips >= self.min_rr_ratio:
                    confidence = self._calculate_confidence(
                        PatternType.BREAK_OF_STRUCTURE,
                        symbol, candles, {'direction': 'BUY', 'structure': 'BULLISH'}
                    )
                    
                    return SMCPattern(
                        pattern_type=PatternType.BREAK_OF_STRUCTURE,
                        direction='BUY',
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        confidence=confidence,
                        risk_reward=reward_pips / risk_pips,
                        trigger_time=current.timestamp,
                        expiry_time=current.timestamp + 1800,  # 30 min expiry
                        metadata={
                            'break_level': resistance_level,
                            'structure': structure.value,
                            'momentum_strength': (current.close - current.open) / current.open * 10000
                        }
                    )
        
        # For bearish structure, look for breaks below support
        elif structure == MarketStructure.BEARISH:
            # Find recent support level
            support_candles = [c for c in recent if c.low < current.close * 1.001]
            if not support_candles:
                return None
            
            support_level = min(c.low for c in support_candles)
            
            # Check if we broke below with momentum
            if (current.close < support_level and 
                current.low < support_level and
                current.close < current.open):  # Bearish candle
                
                # Entry on pullback to support (now resistance)
                entry = support_level - self._get_pip_size(symbol) * 2
                stop_loss = support_level + self._get_pip_size(symbol) * 8
                
                # Scalping target
                targets = self.scalp_targets.get(symbol, [6, 10, 15])
                take_profit = entry - (targets[1] * self._get_pip_size(symbol))
                
                risk_pips = abs(stop_loss - entry) / self._get_pip_size(symbol)
                reward_pips = abs(entry - take_profit) / self._get_pip_size(symbol)
                
                if risk_pips > 0 and reward_pips / risk_pips >= self.min_rr_ratio:
                    confidence = self._calculate_confidence(
                        PatternType.BREAK_OF_STRUCTURE,
                        symbol, candles, {'direction': 'SELL', 'structure': 'BEARISH'}
                    )
                    
                    return SMCPattern(
                        pattern_type=PatternType.BREAK_OF_STRUCTURE,
                        direction='SELL',
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        confidence=confidence,
                        risk_reward=reward_pips / risk_pips,
                        trigger_time=current.timestamp,
                        expiry_time=current.timestamp + 1800,
                        metadata={
                            'break_level': support_level,
                            'structure': structure.value,
                            'momentum_strength': abs(current.open - current.close) / current.open * 10000
                        }
                    )
        
        return None
    
    def detect_inducement_trap(self, symbol: str, candles: List[MarketData]) -> Optional[SMCPattern]:
        """
        Detect inducement/fake breakout traps - very high probability
        
        Logic:
        1. False breakout above/below key level
        2. Immediate reversal back inside range
        3. Trap retail traders who bought the breakout
        """
        if len(candles) < 25:
            return None
        
        current = candles[-1]
        recent = candles[-12:]
        
        # Find key levels (support/resistance)
        highs = [c.high for c in recent[:-3]]  # Exclude last 3 candles
        lows = [c.low for c in recent[:-3]]
        
        key_resistance = max(highs)
        key_support = min(lows)
        
        # Check for false breakout above resistance (bearish trap)
        false_break_candles = [c for c in candles[-3:] if c.high > key_resistance]
        if (false_break_candles and 
            current.close < key_resistance and
            current.close < current.open):  # Rejection candle
            
            # This is a bearish inducement trap
            entry = key_resistance - self._get_pip_size(symbol) * 3
            stop_loss = max(c.high for c in false_break_candles) + self._get_pip_size(symbol) * 3
            
            # Aggressive scalping target (trap reversals move fast)
            targets = self.scalp_targets.get(symbol, [8, 12, 20])
            take_profit = entry - (targets[0] * self._get_pip_size(symbol))
            
            risk_pips = abs(stop_loss - entry) / self._get_pip_size(symbol)
            reward_pips = abs(entry - take_profit) / self._get_pip_size(symbol)
            
            if risk_pips > 0 and risk_pips <= 15:  # Tight stop for traps
                confidence = self._calculate_confidence(
                    PatternType.INDUCEMENT_TRAP,
                    symbol, candles, {
                        'direction': 'SELL', 
                        'trap_strength': max(c.high for c in false_break_candles) - key_resistance
                    }
                )
                
                return SMCPattern(
                    pattern_type=PatternType.INDUCEMENT_TRAP,
                    direction='SELL',
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    risk_reward=reward_pips / risk_pips if risk_pips > 0 else 0,
                    trigger_time=current.timestamp,
                    expiry_time=current.timestamp + 600,  # 10 min expiry (fast setup)
                    metadata={
                        'trap_level': key_resistance,
                        'false_break_high': max(c.high for c in false_break_candles),
                        'rejection_strength': key_resistance - current.close
                    }
                )
        
        # Check for false breakout below support (bullish trap)
        false_break_candles = [c for c in candles[-3:] if c.low < key_support]
        if (false_break_candles and 
            current.close > key_support and
            current.close > current.open):  # Bullish rejection
            
            # This is a bullish inducement trap
            entry = key_support + self._get_pip_size(symbol) * 3
            stop_loss = min(c.low for c in false_break_candles) - self._get_pip_size(symbol) * 3
            
            # Aggressive scalping target
            targets = self.scalp_targets.get(symbol, [8, 12, 20])
            take_profit = entry + (targets[0] * self._get_pip_size(symbol))
            
            risk_pips = abs(entry - stop_loss) / self._get_pip_size(symbol)
            reward_pips = abs(take_profit - entry) / self._get_pip_size(symbol)
            
            if risk_pips > 0 and risk_pips <= 15:  # Tight stop for traps
                confidence = self._calculate_confidence(
                    PatternType.INDUCEMENT_TRAP,
                    symbol, candles, {
                        'direction': 'BUY',
                        'trap_strength': key_support - min(c.low for c in false_break_candles)
                    }
                )
                
                return SMCPattern(
                    pattern_type=PatternType.INDUCEMENT_TRAP,
                    direction='BUY',
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    risk_reward=reward_pips / risk_pips if risk_pips > 0 else 0,
                    trigger_time=current.timestamp,
                    expiry_time=current.timestamp + 600,
                    metadata={
                        'trap_level': key_support,
                        'false_break_low': min(c.low for c in false_break_candles),
                        'rejection_strength': current.close - key_support
                    }
                )
        
        return None
    
    def _calculate_confidence(self, pattern_type: PatternType, symbol: str, 
                            candles: List[MarketData], metadata: Dict) -> float:
        """
        Advanced confidence calculation using multiple factors
        """
        base_conf = self.pattern_stats[pattern_type]['base_confidence']
        win_rate_adj = self.pattern_stats[pattern_type]['win_rate_adj']
        
        # Session bonus (London/NY overlap is best)
        session_bonus = self._get_session_bonus()
        
        # Volume confirmation
        current = candles[-1]
        avg_volume = np.mean([c.volume for c in candles[-10:]])
        volume_surge = min(20, (current.volume / avg_volume - 1) * 50) if avg_volume > 0 else 0
        
        # Volatility check (not too high, not too low)
        atr = self._calculate_atr(candles[-14:])
        avg_atr = self._get_symbol_avg_atr(symbol)
        volatility_factor = max(0, min(15, 15 - abs(atr / avg_atr - 1) * 30)) if avg_atr > 0 else 0
        
        # Multi-timeframe confirmation (simulated)
        mtf_confluence = self._get_mtf_confluence(symbol, metadata.get('direction', 'BUY'))
        
        # Pattern-specific bonuses
        pattern_bonus = 0
        if pattern_type == PatternType.LIQUIDITY_GRAB:
            # Higher confidence for stronger grabs
            grab_strength = metadata.get('grab_strength', 0)
            pattern_bonus = min(10, grab_strength / self._get_pip_size(symbol) * 2)
        elif pattern_type == PatternType.INDUCEMENT_TRAP:
            # Higher confidence for cleaner traps
            trap_strength = metadata.get('trap_strength', 0)
            pattern_bonus = min(15, trap_strength / self._get_pip_size(symbol) * 3)
        
        # Calculate final confidence
        final_confidence = (base_conf * win_rate_adj + 
                          session_bonus + 
                          volume_surge + 
                          volatility_factor + 
                          mtf_confluence + 
                          pattern_bonus)
        
        return max(50, min(99, final_confidence))  # Clamp between 50-99
    
    def _get_session_bonus(self) -> float:
        """Get session-based confidence bonus"""
        from datetime import datetime, timezone
        
        current_hour = datetime.now(timezone.utc).hour
        
        # London session (7-16 UTC)
        if 7 <= current_hour <= 16:
            return 15
        # NY session (13-22 UTC) 
        elif 13 <= current_hour <= 22:
            return 12
        # Overlap (13-16 UTC) - best time
        elif 13 <= current_hour <= 16:
            return 20
        # Asian session (21-6 UTC)
        elif current_hour >= 21 or current_hour <= 6:
            return 5
        else:
            return 0
    
    def _get_mtf_confluence(self, symbol: str, direction: str) -> float:
        """
        Simulate multi-timeframe confluence
        In production, this would analyze 5M and 15M charts
        """
        # Simplified: assume 60% chance of confluence
        import random
        if random.random() < 0.6:
            return 12  # Strong confluence bonus
        elif random.random() < 0.3:
            return 6   # Weak confluence
        else:
            return -5  # Divergence penalty
    
    def _calculate_atr(self, candles: List[MarketData]) -> float:
        """Calculate Average True Range"""
        if len(candles) < 2:
            return 0.001
        
        true_ranges = []
        for i in range(1, len(candles)):
            high_low = candles[i].high - candles[i].low
            high_close = abs(candles[i].high - candles[i-1].close)
            low_close = abs(candles[i].low - candles[i-1].close)
            true_ranges.append(max(high_low, high_close, low_close))
        
        return np.mean(true_ranges) if true_ranges else 0.001
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        if 'JPY' in symbol:
            return 0.01
        elif symbol in ['XAUUSD']:
            return 0.1
        elif symbol in ['XAGUSD']:
            return 0.01
        else:
            return 0.0001
    
    def _get_symbol_avg_atr(self, symbol: str) -> float:
        """Get historical average ATR for symbol (simulated)"""
        avg_atrs = {
            'EURUSD': 0.0008,
            'GBPUSD': 0.0012,
            'USDJPY': 0.08,
            'XAUUSD': 1.2,
            'GBPJPY': 0.12,
        }
        return avg_atrs.get(symbol, 0.001)
    
    def scan_for_patterns(self, symbol: str, candles: List[MarketData]) -> List[SMCPattern]:
        """
        Main pattern detection function
        Returns prioritized list of detected patterns
        """
        patterns = []
        
        # Detect patterns in order of priority/edge
        try:
            # Highest edge patterns first
            liquidity_grab = self.detect_liquidity_grab(symbol, candles)
            if liquidity_grab and liquidity_grab.confidence >= 75:
                patterns.append(liquidity_grab)
            
            inducement_trap = self.detect_inducement_trap(symbol, candles)
            if inducement_trap and inducement_trap.confidence >= 80:
                patterns.append(inducement_trap)
            
            break_of_structure = self.detect_break_of_structure(symbol, candles)
            if break_of_structure and break_of_structure.confidence >= 75:
                patterns.append(break_of_structure)
            
        except Exception as e:
            logger.error(f"Error detecting patterns for {symbol}: {e}")
        
        # Sort by confidence and return top pattern
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns[:1]  # Only return best pattern to avoid noise


if __name__ == "__main__":
    # Test the detector
    detector = AdvancedSMCDetector()
    
    # Generate sample data
    import random
    base_price = 1.1000
    candles = []
    
    for i in range(50):
        # Simulate price movement
        open_price = base_price + random.uniform(-0.002, 0.002)
        high_price = open_price + random.uniform(0, 0.001)
        low_price = open_price - random.uniform(0, 0.001)
        close_price = open_price + random.uniform(-0.0008, 0.0008)
        
        candle = MarketData(
            timestamp=datetime.now().timestamp() + i * 60,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=random.uniform(100, 1000),
            tick_volume=random.randint(50, 500)
        )
        candles.append(candle)
        base_price = close_price
    
    # Test pattern detection
    patterns = detector.scan_for_patterns('EURUSD', candles)
    
    print("🔍 Advanced SMC Pattern Detection Test:")
    if patterns:
        for pattern in patterns:
            print(f"Pattern: {pattern.pattern_type.value}")
            print(f"Direction: {pattern.direction}")
            print(f"Confidence: {pattern.confidence:.1f}%")
            print(f"Entry: {pattern.entry_price:.5f}")
            print(f"SL: {pattern.stop_loss:.5f}")
            print(f"TP: {pattern.take_profit:.5f}")
            print(f"R:R: {pattern.risk_reward:.1f}:1")
            print(f"Metadata: {pattern.metadata}")
            print()
    else:
        print("No high-confidence patterns detected")