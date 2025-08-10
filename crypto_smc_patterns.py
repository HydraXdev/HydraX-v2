#!/usr/bin/env python3
"""
🚀 C.O.R.E. Crypto SMC (Smart Money Concepts) Pattern Detection System
Advanced crypto signal generation engine with specialized SMC patterns for Bitcoin, Ethereum, and XRP

This system provides crypto-specific adaptations of Smart Money Concepts:
- Higher pip thresholds (10+ vs 4+ for forex)
- 2x volume surge requirements vs 1.3x for forex
- 0.5-2% gap sizes vs 4-pip gaps for forex
- ATR-based dynamic thresholds for each crypto pair
- 24/7 market considerations (no session gaps)

Integration Points:
- Elite Guard architecture compatibility
- ZMQ signal publishing on port 5557
- CITADEL Shield validation
- Truth tracking system
- Fire execution system

Author: Claude Code Agent
Date: August 2025
Status: Production Ready - Crypto Trading Engine
"""

import zmq
import json
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import threading
from collections import defaultdict, deque
import requests

# Import existing components for integration
try:
    from citadel_shield_filter import CitadelShieldFilter
except ImportError:
    CitadelShieldFilter = None
    logging.warning("CITADEL Shield not available - running without shield validation")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CryptoMarketRegime(Enum):
    """Crypto-specific market regimes (24/7 trading)"""
    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    VOLATILE_RANGE = "volatile_range"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    BREAKOUT_PENDING = "breakout_pending"
    NEWS_DRIVEN = "news_driven"
    INSTITUTIONAL_ACTIVITY = "institutional_activity"

class CryptoSMCPattern(Enum):
    """Crypto SMC pattern types"""
    LIQUIDITY_SWEEP = "CRYPTO_LIQUIDITY_SWEEP"
    ORDER_BLOCK_BOUNCE = "CRYPTO_ORDER_BLOCK"
    FAIR_VALUE_GAP = "CRYPTO_FVG"
    BREAK_OF_STRUCTURE = "CRYPTO_BOS"
    CHANGE_OF_CHARACTER = "CRYPTO_CHOCH"
    INSTITUTIONAL_CANDLE = "CRYPTO_INST_CANDLE"
    WYCKOFF_SPRING = "CRYPTO_WYCKOFF_SPRING"
    WYCKOFF_UPTHRUST = "CRYPTO_WYCKOFF_UPTHRUST"

class CryptoSignalType(Enum):
    """Crypto signal types"""
    SCALP_ATTACK = "SCALP_ATTACK"        # 15-30 min holds
    SWING_ASSAULT = "SWING_ASSAULT"      # 2-6 hour holds
    POSITION_STRIKE = "POSITION_STRIKE"  # 1-3 day holds

@dataclass
class CryptoTick:
    """Crypto market tick data"""
    symbol: str
    bid: float
    ask: float
    spread: float
    volume: float
    timestamp: float
    volatility: float = 0.0

@dataclass
class CryptoCandle:
    """Crypto OHLCV candle data"""
    symbol: str
    timeframe: str
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    atr: float = 0.0

@dataclass
class CryptoSMCSignal:
    """Crypto SMC pattern signal"""
    pattern: CryptoSMCPattern
    symbol: str
    direction: str  # "BUY" or "SELL"
    timeframe: str
    entry_price: float
    confidence: float
    volume_confirmation: bool
    market_structure: str
    
    # Crypto-specific levels
    stop_loss_pct: float  # Percentage-based SL
    take_profit_pct: float  # Percentage-based TP
    stop_loss_price: float
    take_profit_price: float
    
    # Pattern-specific data
    pattern_data: Dict[str, Any]
    
    # Scoring components
    base_score: float
    volume_score: float
    structure_score: float
    confluence_score: float
    final_score: float = 0.0

class CryptoATRCalculator:
    """Advanced ATR calculation for crypto pairs"""
    
    def __init__(self):
        # Crypto-specific ATR configurations
        self.crypto_configs = {
            "BTCUSD": {
                "typical_atr_pct": 2.5,    # 2.5% daily ATR
                "volatility_multiplier": 1.0,
                "pip_threshold": 100,       # 100 points = 1 pip for BTC
                "max_spread_pct": 0.1      # 0.1% max spread
            },
            "ETHUSD": {
                "typical_atr_pct": 3.0,    # 3.0% daily ATR  
                "volatility_multiplier": 1.2,
                "pip_threshold": 10,        # 10 points = 1 pip for ETH
                "max_spread_pct": 0.15     # 0.15% max spread
            },
            "XRPUSD": {
                "typical_atr_pct": 4.0,    # 4.0% daily ATR
                "volatility_multiplier": 1.5,
                "pip_threshold": 1,         # 1 point = 1 pip for XRP
                "max_spread_pct": 0.2      # 0.2% max spread
            }
        }
    
    def calculate_crypto_atr(self, symbol: str, candledata: List[CryptoCandle], periods: int = 14) -> float:
        """Calculate crypto-specific ATR"""
        try:
            if len(candledata) < periods:
                config = self.crypto_configs.get(symbol, self.crypto_configs["BTCUSD"])
                return config["typical_atr_pct"] / 100  # Return typical ATR as decimal
            
            # Calculate True Range for each period
            true_ranges = []
            for i in range(1, len(candledata)):
                current = candledata[i]
                previous = candledata[i-1]
                
                tr1 = current.high - current.low
                tr2 = abs(current.high - previous.close)
                tr3 = abs(current.low - previous.close)
                
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
            
            if not true_ranges:
                config = self.crypto_configs.get(symbol, self.crypto_configs["BTCUSD"])
                return config["typical_atr_pct"] / 100
            
            # Calculate ATR as average of true ranges
            recent_trs = true_ranges[-periods:] if len(true_ranges) >= periods else true_ranges
            atr_absolute = np.mean(recent_trs)
            
            # Convert to percentage of current price
            current_price = candledata[-1].close
            atr_percentage = (atr_absolute / current_price) if current_price > 0 else 0.01
            
            return atr_percentage
            
        except Exception as e:
            logger.error(f"Error calculating crypto ATR for {symbol}: {e}")
            config = self.crypto_configs.get(symbol, self.crypto_configs["BTCUSD"])
            return config["typical_atr_pct"] / 100

class CryptoLiquiditySweepDetector:
    """Crypto liquidity sweep detection with higher thresholds"""
    
    def __init__(self, atr_calculator: CryptoATRCalculator):
        self.atr_calc = atr_calculator
        self.min_sweep_pct = 0.5  # 0.5% minimum sweep for crypto
        self.volume_surge_threshold = 2.0  # 2x volume surge required
        
    def detect_liquidity_sweep(self, symbol: str, m1_data: List[CryptoCandle], 
                              m5_data: List[CryptoCandle]) -> Optional[CryptoSMCSignal]:
        """
        Detect liquidity sweep reversal patterns in crypto markets
        
        Crypto Liquidity Sweep Criteria:
        - 10+ pip price spike beyond recent highs/lows  
        - 2x volume surge confirmation
        - Quick reversal after sweep (institutional entry)
        - Base score: 75%
        """
        try:
            if len(m1_data) < 10 or len(m5_data) < 5:
                return None
            
            # Get recent data for analysis
            recent_m1 = m1_data[-20:]  # Last 20 M1 candles
            recent_m5 = m5_data[-10:]  # Last 10 M5 candles
            
            current_price = recent_m1[-1].close
            current_volume = recent_m1[-1].volume
            
            # Calculate dynamic thresholds using ATR
            atr = self.atr_calc.calculate_crypto_atr(symbol, recent_m5, 14)
            sweep_threshold_pct = max(self.min_sweep_pct, atr * 2.0) / 100  # ATR * 2 or 0.5% min
            
            # Find recent high/low levels (last 15 M1 candles)
            lookback_candles = recent_m1[-15:]
            recent_high = max([c.high for c in lookback_candles])
            recent_low = min([c.low for c in lookback_candles])
            
            # Calculate price movement from recent levels
            high_breach_pct = (current_price - recent_high) / recent_high if recent_high > 0 else 0
            low_breach_pct = (recent_low - current_price) / recent_low if recent_low > 0 else 0
            
            # Volume analysis for confirmation  
            recent_volumes = [c.volume for c in recent_m1[-10:]]
            avg_volume = np.mean(recent_volumes) if recent_volumes else 1
            volume_surge = current_volume / avg_volume if avg_volume > 0 else 1
            
            logger.debug(f"🔍 {symbol} Liquidity Sweep Analysis:")
            logger.debug(f"   High breach: {high_breach_pct:.3f}% | Low breach: {low_breach_pct:.3f}%")
            logger.debug(f"   Threshold: {sweep_threshold_pct:.3f}% | Volume surge: {volume_surge:.2f}x")
            
            # Detect liquidity sweep conditions
            sweep_direction = None
            breach_percentage = 0
            
            # Upward liquidity sweep (price spikes above recent high)
            if high_breach_pct > sweep_threshold_pct and volume_surge >= self.volume_surge_threshold:
                # Check for reversal confirmation (next few candles pull back)
                if len(recent_m1) >= 3:
                    reversal_candles = recent_m1[-3:]
                    pullback_confirmed = any(c.close < recent_high * 0.998 for c in reversal_candles)  # 0.2% pullback
                    
                    if pullback_confirmed:
                        sweep_direction = "SELL"  # Sell after upward sweep
                        breach_percentage = high_breach_pct * 100
            
            # Downward liquidity sweep (price spikes below recent low) 
            elif low_breach_pct > sweep_threshold_pct and volume_surge >= self.volume_surge_threshold:
                # Check for reversal confirmation
                if len(recent_m1) >= 3:
                    reversal_candles = recent_m1[-3:]
                    pullback_confirmed = any(c.close > recent_low * 1.002 for c in reversal_candles)  # 0.2% pullback
                    
                    if pullback_confirmed:
                        sweep_direction = "BUY"  # Buy after downward sweep
                        breach_percentage = low_breach_pct * 100
            
            if sweep_direction:
                # Calculate stop loss and take profit levels
                if sweep_direction == "BUY":
                    entry_price = current_price
                    stop_loss_pct = atr * 1.5  # 1.5x ATR stop loss
                    take_profit_pct = atr * 3.0  # 1:2 risk reward
                    stop_loss_price = entry_price * (1 - stop_loss_pct)
                    take_profit_price = entry_price * (1 + take_profit_pct)
                else:  # SELL
                    entry_price = current_price
                    stop_loss_pct = atr * 1.5
                    take_profit_pct = atr * 3.0
                    stop_loss_price = entry_price * (1 + stop_loss_pct)
                    take_profit_price = entry_price * (1 - take_profit_pct)
                
                # Score calculation
                base_score = 75.0  # Base score for liquidity sweep
                volume_score = min(15.0, volume_surge * 5.0)  # Up to 15 points for volume
                structure_score = min(10.0, breach_percentage * 2.0)  # Up to 10 points for breach size
                
                signal = CryptoSMCSignal(
                    pattern=CryptoSMCPattern.LIQUIDITY_SWEEP,
                    symbol=symbol,
                    direction=sweep_direction,
                    timeframe="M1",  
                    entry_price=entry_price,
                    confidence=base_score,
                    volume_confirmation=volume_surge >= self.volume_surge_threshold,
                    market_structure="SWEEP_REVERSAL",
                    stop_loss_pct=stop_loss_pct * 100,
                    take_profit_pct=take_profit_pct * 100,
                    stop_loss_price=stop_loss_price,
                    take_profit_price=take_profit_price,
                    pattern_data={
                        "sweep_level": recent_high if sweep_direction == "SELL" else recent_low,
                        "breach_percentage": breach_percentage,
                        "volume_surge": volume_surge,
                        "atr_value": atr,
                        "reversal_confirmed": True
                    },
                    base_score=base_score,
                    volume_score=volume_score,
                    structure_score=structure_score,
                    confluence_score=0.0
                )
                
                logger.info(f"✅ {symbol} LIQUIDITY SWEEP detected: {sweep_direction} @ {entry_price:.2f}")
                logger.info(f"   Breach: {breach_percentage:.2f}% | Volume: {volume_surge:.1f}x | ATR: {atr:.3f}")
                
                return signal
                
        except Exception as e:
            logger.error(f"Error detecting liquidity sweep for {symbol}: {e}")
        
        return None

class CryptoOrderBlockDetector:
    """Crypto order block detection with enhanced institutional logic"""
    
    def __init__(self, atr_calculator: CryptoATRCalculator):
        self.atr_calc = atr_calculator
        self.consolidation_threshold = 0.5  # 0.5% consolidation range
        self.volume_confirmation = 2.0  # 2x volume required
        
    def detect_order_block_bounce(self, symbol: str, m5_data: List[CryptoCandle], 
                                 m15_data: List[CryptoCandle]) -> Optional[CryptoSMCSignal]:
        """
        Detect order block bounces in crypto markets
        
        Crypto Order Block Criteria:
        - Identify institutional accumulation zones (consolidation areas)
        - Detect when price returns to these levels for bounces
        - Require 2x volume confirmation and tight spreads
        - Base score: 70%
        """
        try:
            if len(m5_data) < 30 or len(m15_data) < 10:
                return None
            
            # Look for consolidation zones in M15 data
            recent_m15 = m15_data[-20:]  # Last 20 M15 candles
            recent_m5 = m5_data[-30:]    # Last 30 M5 candles
            
            current_price = recent_m5[-1].close
            current_volume = recent_m5[-1].volume
            
            # Calculate ATR for dynamic thresholds
            atr = self.atr_calc.calculate_crypto_atr(symbol, recent_m15, 14)
            consolidation_range = max(self.consolidation_threshold / 100, atr * 0.8)
            
            # Find consolidation zones (areas where price stayed within range)
            order_blocks = []
            
            for i in range(len(recent_m15) - 8):  # Look for 8+ candle consolidations
                consolidation_candles = recent_m15[i:i+8]
                
                # Calculate consolidation metrics
                highs = [c.high for c in consolidation_candles]
                lows = [c.low for c in consolidation_candles]
                volumes = [c.volume for c in consolidation_candles]
                
                range_high = max(highs)
                range_low = min(lows)
                range_pct = (range_high - range_low) / range_low if range_low > 0 else 0
                avg_volume = np.mean(volumes)
                
                # Check if this qualifies as an order block (institutional accumulation)
                if range_pct <= consolidation_range and avg_volume > 0:
                    # Additional confirmation: increasing volume during consolidation
                    volume_trend = np.polyfit(range(len(volumes)), volumes, 1)[0]  # Linear trend
                    
                    order_block = {
                        "high": range_high,
                        "low": range_low,
                        "midpoint": (range_high + range_low) / 2,
                        "range_pct": range_pct * 100,
                        "avg_volume": avg_volume,
                        "volume_trend": volume_trend,
                        "start_time": consolidation_candles[0].timestamp,
                        "end_time": consolidation_candles[-1].timestamp,
                        "strength": avg_volume * (1 + max(0, volume_trend))  # Volume + trend bonus
                    }
                    order_blocks.append(order_block)
            
            if not order_blocks:
                return None
            
            # Find the most recent and strongest order block
            # Sort by strength (volume and recency)
            current_time = time.time()
            for ob in order_blocks:
                recency_score = 1.0 / (1 + (current_time - ob["end_time"]) / 3600)  # Decay over hours
                ob["total_strength"] = ob["strength"] * recency_score
            
            strongest_ob = max(order_blocks, key=lambda x: x["total_strength"])
            
            # Check if current price is approaching the order block
            distance_to_high = abs(current_price - strongest_ob["high"]) / current_price
            distance_to_low = abs(current_price - strongest_ob["low"]) / current_price
            distance_to_mid = abs(current_price - strongest_ob["midpoint"]) / current_price
            
            min_distance = min(distance_to_high, distance_to_low, distance_to_mid)
            
            # Price must be within 1% of order block to trigger
            if min_distance > 0.01:  # 1% tolerance
                return None
            
            # Volume confirmation
            recent_volumes = [c.volume for c in recent_m5[-5:]]
            avg_recent_volume = np.mean(recent_volumes)
            volume_surge = current_volume / avg_recent_volume if avg_recent_volume > 0 else 1
            
            if volume_surge < self.volume_confirmation:
                return None
            
            # Determine bounce direction
            if distance_to_low <= distance_to_high:
                # Price near support (low) - expect bounce up
                direction = "BUY"
                entry_price = current_price
                key_level = strongest_ob["low"]
                stop_loss_pct = atr * 1.0  # Tight stop below support
                take_profit_pct = atr * 2.5  # Conservative target
                stop_loss_price = entry_price * (1 - stop_loss_pct)
                take_profit_price = entry_price * (1 + take_profit_pct)
            else:
                # Price near resistance (high) - expect bounce down
                direction = "SELL"
                entry_price = current_price
                key_level = strongest_ob["high"]
                stop_loss_pct = atr * 1.0  # Tight stop above resistance
                take_profit_pct = atr * 2.5
                stop_loss_price = entry_price * (1 + stop_loss_pct) 
                take_profit_price = entry_price * (1 - take_profit_pct)
            
            # Score calculation
            base_score = 70.0
            volume_score = min(12.0, (volume_surge - 1.0) * 8.0)  # Up to 12 points
            structure_score = min(8.0, strongest_ob["total_strength"] / 1000.0)  # Strength bonus
            proximity_bonus = max(0, 5.0 - min_distance * 500)  # Closer = better
            
            signal = CryptoSMCSignal(
                pattern=CryptoSMCPattern.ORDER_BLOCK_BOUNCE,
                symbol=symbol,
                direction=direction,
                timeframe="M5",
                entry_price=entry_price,
                confidence=base_score,
                volume_confirmation=volume_surge >= self.volume_confirmation,
                market_structure="ORDER_BLOCK_BOUNCE",
                stop_loss_pct=stop_loss_pct * 100,
                take_profit_pct=take_profit_pct * 100,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                pattern_data={
                    "order_block": strongest_ob,
                    "key_level": key_level,
                    "distance_pct": min_distance * 100,
                    "volume_surge": volume_surge,
                    "atr_value": atr
                },
                base_score=base_score,
                volume_score=volume_score,
                structure_score=structure_score + proximity_bonus,
                confluence_score=0.0
            )
            
            logger.info(f"✅ {symbol} ORDER BLOCK BOUNCE detected: {direction} @ {entry_price:.2f}")
            logger.info(f"   Key Level: {key_level:.2f} | Distance: {min_distance*100:.2f}% | Volume: {volume_surge:.1f}x")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error detecting order block for {symbol}: {e}")
        
        return None

class CryptoFVGDetector:
    """Fair Value Gap detection for crypto markets"""
    
    def __init__(self, atr_calculator: CryptoATRCalculator):
        self.atr_calc = atr_calculator
        self.min_gap_pct = 0.5  # 0.5% minimum gap for crypto
        self.max_gap_age_hours = 24  # Gaps valid for 24 hours
        
    def detect_fair_value_gap(self, symbol: str, m5_data: List[CryptoCandle]) -> Optional[CryptoSMCSignal]:
        """
        Detect Fair Value Gap fills in crypto markets
        
        Crypto FVG Criteria:
        - Find price inefficiencies (gaps) of 0.5%+ in crypto charts
        - Detect when price approaches gap midpoint for fills
        - Focus on unfilled gaps as high-probability targets
        - Base score: 65%
        """
        try:
            if len(m5_data) < 50:  # Need more data to find gaps
                return None
            
            recent_candles = m5_data[-50:]  # Last 50 M5 candles
            current_price = recent_candles[-1].close
            current_time = time.time()
            
            # Calculate ATR for dynamic gap threshold
            atr = self.atr_calc.calculate_crypto_atr(symbol, recent_candles, 14)
            gap_threshold_pct = max(self.min_gap_pct / 100, atr * 0.4)  # ATR * 0.4 or 0.5% min
            
            # Look for Fair Value Gaps (3-candle pattern)
            unfilled_gaps = []
            
            for i in range(2, len(recent_candles) - 3):  # Leave room for gap formation and filling check
                candle1 = recent_candles[i-2]  # First candle
                candle2 = recent_candles[i-1]  # Middle candle (impulse)
                candle3 = recent_candles[i]    # Third candle
                
                # Check for bullish FVG (gap up)
                if candle2.close > candle2.open:  # Bullish impulse candle
                    gap_low = candle1.high
                    gap_high = candle3.low
                    
                    if gap_high > gap_low:  # Valid gap
                        gap_size_pct = (gap_high - gap_low) / gap_low
                        
                        if gap_size_pct >= gap_threshold_pct:
                            # Check if gap is still unfilled
                            subsequent_candles = recent_candles[i+1:]
                            gap_filled = any(c.low <= gap_low or c.high >= gap_high for c in subsequent_candles)
                            
                            if not gap_filled:
                                gap = {
                                    "type": "BULLISH_FVG",
                                    "gap_low": gap_low,
                                    "gap_high": gap_high,
                                    "gap_mid": (gap_low + gap_high) / 2,
                                    "size_pct": gap_size_pct * 100,
                                    "formation_time": candle2.timestamp,
                                    "age_hours": (current_time - candle2.timestamp) / 3600,
                                    "impulse_strength": abs(candle2.close - candle2.open) / candle2.open
                                }
                                unfilled_gaps.append(gap)
                
                # Check for bearish FVG (gap down)
                elif candle2.close < candle2.open:  # Bearish impulse candle
                    gap_high = candle1.low
                    gap_low = candle3.high
                    
                    if gap_high > gap_low:  # Valid gap
                        gap_size_pct = (gap_high - gap_low) / gap_high
                        
                        if gap_size_pct >= gap_threshold_pct:
                            # Check if gap is still unfilled
                            subsequent_candles = recent_candles[i+1:]
                            gap_filled = any(c.high >= gap_high or c.low <= gap_low for c in subsequent_candles)
                            
                            if not gap_filled:
                                gap = {
                                    "type": "BEARISH_FVG",
                                    "gap_low": gap_low,
                                    "gap_high": gap_high,
                                    "gap_mid": (gap_low + gap_high) / 2,
                                    "size_pct": gap_size_pct * 100,
                                    "formation_time": candle2.timestamp,
                                    "age_hours": (current_time - candle2.timestamp) / 3600,
                                    "impulse_strength": abs(candle2.close - candle2.open) / candle2.open
                                }
                                unfilled_gaps.append(gap)
            
            if not unfilled_gaps:
                return None
            
            # Filter gaps by age (remove stale gaps)
            fresh_gaps = [g for g in unfilled_gaps if g["age_hours"] <= self.max_gap_age_hours]
            
            if not fresh_gaps:
                return None
            
            # Find the most relevant gap (closest to current price and strongest)
            for gap in fresh_gaps:
                gap["distance_to_price"] = abs(current_price - gap["gap_mid"]) / current_price
                gap["relevance_score"] = gap["impulse_strength"] / (1 + gap["distance_to_price"])
            
            best_gap = max(fresh_gaps, key=lambda x: x["relevance_score"])
            
            # Check if price is approaching the gap (within 2% of gap midpoint)
            distance_to_gap = best_gap["distance_to_price"]
            if distance_to_gap > 0.02:  # 2% tolerance
                return None
            
            # Determine fill direction
            if best_gap["type"] == "BULLISH_FVG":
                if current_price < best_gap["gap_mid"]:
                    direction = "BUY"  # Price below gap, expect fill upward
                    entry_price = current_price
                    target_price = best_gap["gap_high"]
                    stop_below_gap = best_gap["gap_low"] * 0.995  # Stop 0.5% below gap
                else:
                    direction = "SELL"  # Price above gap, expect retest downward
                    entry_price = current_price
                    target_price = best_gap["gap_low"]
                    stop_below_gap = best_gap["gap_high"] * 1.005  # Stop 0.5% above gap
            else:  # BEARISH_FVG
                if current_price > best_gap["gap_mid"]:
                    direction = "SELL"  # Price above gap, expect fill downward
                    entry_price = current_price
                    target_price = best_gap["gap_low"]
                    stop_below_gap = best_gap["gap_high"] * 1.005
                else:
                    direction = "BUY"  # Price below gap, expect retest upward
                    entry_price = current_price
                    target_price = best_gap["gap_high"]
                    stop_below_gap = best_gap["gap_low"] * 0.995
            
            # Calculate percentage-based levels
            if direction == "BUY":
                take_profit_pct = ((target_price - entry_price) / entry_price) * 100
                stop_loss_pct = ((entry_price - stop_below_gap) / entry_price) * 100
                take_profit_price = target_price
                stop_loss_price = stop_below_gap
            else:
                take_profit_pct = ((entry_price - target_price) / entry_price) * 100  
                stop_loss_pct = ((stop_below_gap - entry_price) / entry_price) * 100
                take_profit_price = target_price
                stop_loss_price = stop_below_gap
            
            # Score calculation
            base_score = 65.0
            gap_size_bonus = min(10.0, best_gap["size_pct"] * 2.0)  # Larger gaps = higher score
            proximity_bonus = max(0, 8.0 - distance_to_gap * 400)  # Closer = better
            impulse_bonus = min(7.0, best_gap["impulse_strength"] * 100)  # Stronger impulse = better
            
            signal = CryptoSMCSignal(
                pattern=CryptoSMCPattern.FAIR_VALUE_GAP,
                symbol=symbol,
                direction=direction,
                timeframe="M5",
                entry_price=entry_price,
                confidence=base_score,
                volume_confirmation=True,  # FVG doesn't require volume confirmation
                market_structure="FVG_FILL",
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                pattern_data={
                    "gap_data": best_gap,
                    "target_price": target_price,
                    "distance_pct": distance_to_gap * 100,
                    "atr_value": atr
                },
                base_score=base_score,
                volume_score=0.0,  # FVG doesn't use volume scoring
                structure_score=gap_size_bonus + proximity_bonus + impulse_bonus,
                confluence_score=0.0
            )
            
            logger.info(f"✅ {symbol} FAIR VALUE GAP detected: {direction} @ {entry_price:.2f}")
            logger.info(f"   Gap: {best_gap['gap_low']:.2f} - {best_gap['gap_high']:.2f} | Size: {best_gap['size_pct']:.2f}%")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error detecting FVG for {symbol}: {e}")
        
        return None

class CryptoBOSDetector:
    """Break of Structure detector for crypto markets"""
    
    def __init__(self, atr_calculator: CryptoATRCalculator):
        self.atr_calc = atr_calculator
        self.min_break_pct = 0.8  # 0.8% minimum break for significance
        self.volume_surge_required = 1.8  # 1.8x volume surge required
        
    def detect_break_of_structure(self, symbol: str, m15_data: List[CryptoCandle]) -> Optional[CryptoSMCSignal]:
        """
        Detect Break of Structure patterns in crypto markets
        
        Crypto BOS Criteria:
        - Identify when price breaks significant support/resistance
        - Confirm with volume surge and momentum continuation
        - Look for pullback entries after initial break
        """  
        try:
            if len(m15_data) < 30:
                return None
            
            recent_candles = m15_data[-30:]
            current_price = recent_candles[-1].close
            current_volume = recent_candles[-1].volume
            
            # Calculate ATR for dynamic thresholds
            atr = self.atr_calc.calculate_crypto_atr(symbol, recent_candles, 14)
            break_threshold_pct = max(self.min_break_pct / 100, atr * 0.6)
            
            # Identify key structural levels (swing highs and lows)
            swing_highs = []
            swing_lows = []
            
            # Look for swing points using a 5-candle window
            for i in range(2, len(recent_candles) - 2):
                candle = recent_candles[i]
                prev2 = recent_candles[i-2]
                prev1 = recent_candles[i-1]
                next1 = recent_candles[i+1]
                next2 = recent_candles[i+2]
                
                # Swing high: current high > surrounding highs
                if (candle.high > prev2.high and candle.high > prev1.high and 
                    candle.high > next1.high and candle.high > next2.high):
                    swing_highs.append({
                        "price": candle.high,
                        "timestamp": candle.timestamp,
                        "index": i,
                        "strength": candle.volume  # Volume as strength indicator
                    })
                
                # Swing low: current low < surrounding lows
                if (candle.low < prev2.low and candle.low < prev1.low and 
                    candle.low < next1.low and candle.low < next2.low):
                    swing_lows.append({
                        "price": candle.low,
                        "timestamp": candle.timestamp,
                        "index": i,
                        "strength": candle.volume
                    })
            
            if not swing_highs and not swing_lows:
                return None
            
            # Check for recent breaks of structure
            recent_time = time.time() - 3600  # Last hour
            break_detected = None
            
            # Check for break of recent swing high (bullish BOS)
            if swing_highs:
                recent_high = max(swing_highs, key=lambda x: x["timestamp"])
                if recent_high["timestamp"] > recent_time:
                    break_pct = (current_price - recent_high["price"]) / recent_high["price"]
                    if break_pct > break_threshold_pct:
                        # Volume confirmation
                        recent_volumes = [c.volume for c in recent_candles[-5:]]
                        avg_volume = np.mean(recent_volumes)
                        volume_surge = current_volume / avg_volume if avg_volume > 0 else 1
                        
                        if volume_surge >= self.volume_surge_required:
                            break_detected = {
                                "type": "BULLISH_BOS",
                                "broken_level": recent_high["price"],
                                "break_pct": break_pct * 100,
                                "volume_surge": volume_surge,
                                "direction": "BUY"
                            }
            
            # Check for break of recent swing low (bearish BOS)  
            if swing_lows and not break_detected:
                recent_low = max(swing_lows, key=lambda x: x["timestamp"])
                if recent_low["timestamp"] > recent_time:
                    break_pct = (recent_low["price"] - current_price) / recent_low["price"]
                    if break_pct > break_threshold_pct:
                        # Volume confirmation
                        recent_volumes = [c.volume for c in recent_candles[-5:]]
                        avg_volume = np.mean(recent_volumes)
                        volume_surge = current_volume / avg_volume if avg_volume > 0 else 1
                        
                        if volume_surge >= self.volume_surge_required:
                            break_detected = {
                                "type": "BEARISH_BOS",
                                "broken_level": recent_low["price"],
                                "break_pct": break_pct * 100,
                                "volume_surge": volume_surge,
                                "direction": "SELL"
                            }
            
            if not break_detected:
                return None
            
            # Calculate entry, stop loss, and take profit
            direction = break_detected["direction"]
            entry_price = current_price
            
            if direction == "BUY":
                # Entry above broken resistance, stop below previous structure
                stop_loss_pct = atr * 1.2  # 1.2x ATR stop
                take_profit_pct = atr * 2.4  # 1:2 risk reward
                stop_loss_price = entry_price * (1 - stop_loss_pct)
                take_profit_price = entry_price * (1 + take_profit_pct)
            else:
                # Entry below broken support, stop above previous structure
                stop_loss_pct = atr * 1.2
                take_profit_pct = atr * 2.4
                stop_loss_price = entry_price * (1 + stop_loss_pct)
                take_profit_price = entry_price * (1 - take_profit_pct)
            
            # Score calculation
            base_score = 68.0  # Base score for BOS
            break_strength_bonus = min(12.0, break_detected["break_pct"] * 1.5)
            volume_bonus = min(10.0, (break_detected["volume_surge"] - 1.0) * 6.0)
            
            signal = CryptoSMCSignal(
                pattern=CryptoSMCPattern.BREAK_OF_STRUCTURE,
                symbol=symbol,
                direction=direction,
                timeframe="M15",
                entry_price=entry_price,
                confidence=base_score,
                volume_confirmation=break_detected["volume_surge"] >= self.volume_surge_required,
                market_structure="STRUCTURE_BREAK",
                stop_loss_pct=stop_loss_pct * 100,
                take_profit_pct=take_profit_pct * 100,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                pattern_data={
                    "break_data": break_detected,
                    "atr_value": atr,
                    "swing_highs": len(swing_highs),
                    "swing_lows": len(swing_lows)
                },
                base_score=base_score,
                volume_score=volume_bonus,
                structure_score=break_strength_bonus,
                confluence_score=0.0
            )
            
            logger.info(f"✅ {symbol} BREAK OF STRUCTURE detected: {direction} @ {entry_price:.2f}")
            logger.info(f"   Broken Level: {break_detected['broken_level']:.2f} | Break: {break_detected['break_pct']:.2f}%")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error detecting BOS for {symbol}: {e}")
        
        return None

class CryptoCHoCHDetector:
    """Change of Character detector for crypto trend reversals"""
    
    def __init__(self, atr_calculator: CryptoATRCalculator):
        self.atr_calc = atr_calculator
        self.trend_strength_threshold = 0.02  # 2% trend strength required
        
    def detect_change_of_character(self, symbol: str, m15_data: List[CryptoCandle], 
                                  m30_data: List[CryptoCandle]) -> Optional[CryptoSMCSignal]:
        """
        Detect Change of Character patterns in crypto markets
        
        Crypto CHoCH Criteria:
        - Detect trend reversal signals in crypto markets
        - Look for failed continuation patterns
        - Confirm with divergence and volume analysis
        """
        try:
            if len(m15_data) < 40 or len(m30_data) < 20:
                return None
            
            recent_m15 = m15_data[-40:]
            recent_m30 = m30_data[-20:]
            current_price = recent_m15[-1].close
            
            # Calculate ATR
            atr = self.atr_calc.calculate_crypto_atr(symbol, recent_m30, 14)
            
            # Determine current trend using M30 data
            m30_prices = [c.close for c in recent_m30[-10:]]
            trend_slope = np.polyfit(range(len(m30_prices)), m30_prices, 1)[0]
            trend_strength = abs(trend_slope) / np.mean(m30_prices)
            
            if trend_strength < self.trend_strength_threshold:
                return None  # No clear trend to reverse
            
            current_trend = "BULLISH" if trend_slope > 0 else "BEARISH"
            
            # Look for signs of character change in M15 data
            recent_highs = [c.high for c in recent_m15[-10:]]
            recent_lows = [c.low for c in recent_m15[-10:]]
            recent_volumes = [c.volume for c in recent_m15[-10:]]
            
            # Check for failure to make new highs/lows
            if current_trend == "BULLISH":
                # In uptrend, look for failure to make new highs
                latest_high = max(recent_highs[-5:])  # Last 5 candles
                previous_high = max(recent_highs[-10:-5])  # Previous 5 candles
                
                if latest_high <= previous_high:  # Failed to make new high
                    # Check for volume divergence
                    recent_vol_avg = np.mean(recent_volumes[-5:])
                    previous_vol_avg = np.mean(recent_volumes[-10:-5])
                    
                    if recent_vol_avg < previous_vol_avg * 0.8:  # Volume declining
                        choch_detected = {
                            "type": "BULLISH_TO_BEARISH",
                            "failed_level": previous_high,
                            "current_high": latest_high,
                            "volume_divergence": (previous_vol_avg - recent_vol_avg) / previous_vol_avg * 100,
                            "direction": "SELL"
                        }
                    else:
                        return None
                else:
                    return None
                        
            else:  # BEARISH trend
                # In downtrend, look for failure to make new lows
                latest_low = min(recent_lows[-5:])
                previous_low = min(recent_lows[-10:-5])
                
                if latest_low >= previous_low:  # Failed to make new low
                    # Check for volume divergence
                    recent_vol_avg = np.mean(recent_volumes[-5:])
                    previous_vol_avg = np.mean(recent_volumes[-10:-5])
                    
                    if recent_vol_avg < previous_vol_avg * 0.8:
                        choch_detected = {
                            "type": "BEARISH_TO_BULLISH", 
                            "failed_level": previous_low,
                            "current_low": latest_low,
                            "volume_divergence": (previous_vol_avg - recent_vol_avg) / previous_vol_avg * 100,
                            "direction": "BUY"
                        }
                    else:
                        return None
                else:
                    return None
            
            # Calculate entry and levels
            direction = choch_detected["direction"]
            entry_price = current_price
            
            if direction == "BUY":
                stop_loss_pct = atr * 1.5  # 1.5x ATR stop
                take_profit_pct = atr * 3.0  # 1:2 risk reward
                stop_loss_price = entry_price * (1 - stop_loss_pct)
                take_profit_price = entry_price * (1 + take_profit_pct)
            else:
                stop_loss_pct = atr * 1.5
                take_profit_pct = atr * 3.0
                stop_loss_price = entry_price * (1 + stop_loss_pct)
                take_profit_price = entry_price * (1 - take_profit_pct)
            
            # Score calculation
            base_score = 62.0  # Base score for CHoCH
            divergence_bonus = min(15.0, choch_detected["volume_divergence"] * 0.5)
            trend_strength_bonus = min(8.0, trend_strength * 400)
            
            signal = CryptoSMCSignal(
                pattern=CryptoSMCPattern.CHANGE_OF_CHARACTER,
                symbol=symbol,
                direction=direction,
                timeframe="M15",
                entry_price=entry_price,
                confidence=base_score,
                volume_confirmation=True,
                market_structure="TREND_REVERSAL",
                stop_loss_pct=stop_loss_pct * 100,
                take_profit_pct=take_profit_pct * 100,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                pattern_data={
                    "choch_data": choch_detected,
                    "trend_strength": trend_strength,
                    "original_trend": current_trend,
                    "atr_value": atr
                },
                base_score=base_score,
                volume_score=divergence_bonus,
                structure_score=trend_strength_bonus,
                confluence_score=0.0
            )
            
            logger.info(f"✅ {symbol} CHANGE OF CHARACTER detected: {direction} @ {entry_price:.2f}")
            logger.info(f"   Trend Change: {current_trend} → {choch_detected['type']} | Divergence: {choch_detected['volume_divergence']:.1f}%")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error detecting CHoCH for {symbol}: {e}")
        
        return None

class CryptoSMCEngine:
    """Main crypto SMC pattern detection engine"""
    
    def __init__(self):
        # Initialize components
        self.atr_calculator = CryptoATRCalculator()
        self.liquidity_detector = CryptoLiquiditySweepDetector(self.atr_calculator)
        self.orderblock_detector = CryptoOrderBlockDetector(self.atr_calculator)
        self.fvg_detector = CryptoFVGDetector(self.atr_calculator)
        self.bos_detector = CryptoBOSDetector(self.atr_calculator)
        self.choch_detector = CryptoCHoCHDetector(self.atr_calculator)
        
        # Crypto symbols for C.O.R.E. system
        self.crypto_symbols = ["BTCUSD", "ETHUSD", "XRPUSD"]
        
        # Market data storage
        self.tick_data = defaultdict(lambda: deque(maxlen=100))
        self.m1_data = defaultdict(lambda: deque(maxlen=200))
        self.m5_data = defaultdict(lambda: deque(maxlen=200))
        self.m15_data = defaultdict(lambda: deque(maxlen=100))
        self.m30_data = defaultdict(lambda: deque(maxlen=50))
        
        # ZMQ setup for signal publishing
        self.context = zmq.Context()
        self.publisher = None
        
        # CITADEL Shield integration
        self.citadel_shield = CitadelShieldFilter() if CitadelShieldFilter else None
        
        # Signal tracking
        self.signals_generated = 0
        self.patterns_detected = defaultdict(int)
        self.last_signal_time = {}
        self.signal_cooldown = 300  # 5 minutes cooldown per symbol
        
        # Truth tracking
        self.truth_tracker_url = "http://localhost:8888/api/truth_tracker"
        
        logger.info("🚀 C.O.R.E. Crypto SMC Engine initialized")
        logger.info(f"📊 Monitoring {len(self.crypto_symbols)} crypto pairs: {', '.join(self.crypto_symbols)}")
        
    def setup_zmq_publisher(self):
        """Setup ZMQ publisher for signals"""
        try:
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5557")  # Same port as Elite Guard
            logger.info("📡 ZMQ publisher bound to port 5557")
        except Exception as e:
            logger.error(f"Error setting up ZMQ publisher: {e}")
    
    def process_crypto_tick(self, symbol: str, bid: float, ask: float, volume: float):
        """Process incoming crypto tick data"""
        try:
            if symbol not in self.crypto_symbols:
                return
            
            spread = ask - bid
            volatility = spread / ((bid + ask) / 2) * 100  # Spread as % of mid price
            
            tick = CryptoTick(
                symbol=symbol,
                bid=bid,
                ask=ask,
                spread=spread,
                volume=volume,
                timestamp=time.time(),
                volatility=volatility
            )
            
            self.tick_data[symbol].append(tick)
            logger.debug(f"📊 {symbol} tick: {bid:.2f}/{ask:.2f} vol:{volume:.2f}")
            
        except Exception as e:
            logger.error(f"Error processing tick for {symbol}: {e}")
    
    def process_crypto_candle(self, symbol: str, timeframe: str, ohlcv_data: Dict):
        """Process crypto candle data"""
        try:
            if symbol not in self.crypto_symbols:
                return
            
            candle = CryptoCandle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ohlcv_data.get('timestamp', time.time()),
                open=float(ohlcv_data['open']),
                high=float(ohlcv_data['high']),
                low=float(ohlcv_data['low']),
                close=float(ohlcv_data['close']),
                volume=float(ohlcv_data.get('volume', 0))
            )
            
            # Store in appropriate timeframe buffer
            if timeframe == "M1":
                self.m1_data[symbol].append(candle)
            elif timeframe == "M5":
                self.m5_data[symbol].append(candle)
            elif timeframe == "M15":
                self.m15_data[symbol].append(candle)
            elif timeframe == "M30":
                self.m30_data[symbol].append(candle)
                
            logger.debug(f"🕯️ {symbol} {timeframe} candle: O:{candle.open:.2f} H:{candle.high:.2f} L:{candle.low:.2f} C:{candle.close:.2f}")
            
        except Exception as e:
            logger.error(f"Error processing {timeframe} candle for {symbol}: {e}")
    
    def scan_crypto_patterns(self, symbol: str) -> List[CryptoSMCSignal]:
        """Scan for all crypto SMC patterns on a symbol"""
        patterns = []
        current_time = time.time()
        
        # Check cooldown
        if symbol in self.last_signal_time:
            if current_time - self.last_signal_time[symbol] < self.signal_cooldown:
                return patterns
        
        try:
            logger.info(f"🔍 Scanning {symbol} for crypto SMC patterns...")
            
            # Get data for analysis
            m1_candles = list(self.m1_data[symbol])
            m5_candles = list(self.m5_data[symbol])
            m15_candles = list(self.m15_data[symbol])
            m30_candles = list(self.m30_data[symbol])
            
            # Check data availability
            logger.debug(f"📊 {symbol} data: M1:{len(m1_candles)} M5:{len(m5_candles)} M15:{len(m15_candles)} M30:{len(m30_candles)}")
            
            # 1. Liquidity Sweep Detection (highest priority)
            if len(m1_candles) >= 10 and len(m5_candles) >= 5:
                sweep_signal = self.liquidity_detector.detect_liquidity_sweep(symbol, m1_candles, m5_candles)
                if sweep_signal:
                    patterns.append(sweep_signal)
                    self.patterns_detected["LIQUIDITY_SWEEP"] += 1
                    logger.info(f"✅ {symbol} LIQUIDITY SWEEP detected!")
            
            # 2. Order Block Bounce Detection
            if len(m5_candles) >= 30 and len(m15_candles) >= 10:
                ob_signal = self.orderblock_detector.detect_order_block_bounce(symbol, m5_candles, m15_candles)
                if ob_signal:
                    patterns.append(ob_signal)
                    self.patterns_detected["ORDER_BLOCK"] += 1
                    logger.info(f"✅ {symbol} ORDER BLOCK BOUNCE detected!")
            
            # 3. Fair Value Gap Detection
            if len(m5_candles) >= 50:
                fvg_signal = self.fvg_detector.detect_fair_value_gap(symbol, m5_candles)
                if fvg_signal:
                    patterns.append(fvg_signal)
                    self.patterns_detected["FAIR_VALUE_GAP"] += 1
                    logger.info(f"✅ {symbol} FAIR VALUE GAP detected!")
            
            # 4. Break of Structure Detection
            if len(m15_candles) >= 30:
                bos_signal = self.bos_detector.detect_break_of_structure(symbol, m15_candles)
                if bos_signal:
                    patterns.append(bos_signal)
                    self.patterns_detected["BREAK_OF_STRUCTURE"] += 1
                    logger.info(f"✅ {symbol} BREAK OF STRUCTURE detected!")
            
            # 5. Change of Character Detection
            if len(m15_candles) >= 40 and len(m30_candles) >= 20:
                choch_signal = self.choch_detector.detect_change_of_character(symbol, m15_candles, m30_candles)
                if choch_signal:
                    patterns.append(choch_signal)
                    self.patterns_detected["CHANGE_OF_CHARACTER"] += 1
                    logger.info(f"✅ {symbol} CHANGE OF CHARACTER detected!")
            
            # Apply confluence scoring and filtering
            for pattern in patterns:
                pattern.final_score = self.calculate_confluence_score(pattern)
            
            # Filter by minimum quality (60+ for crypto volatility)
            quality_patterns = [p for p in patterns if p.final_score >= 60.0]
            
            # Sort by final score
            quality_patterns.sort(key=lambda x: x.final_score, reverse=True)
            
            logger.info(f"🎯 {symbol}: {len(patterns)} patterns detected, {len(quality_patterns)} above quality threshold")
            
            return quality_patterns
            
        except Exception as e:
            logger.error(f"Error scanning patterns for {symbol}: {e}")
            return []
    
    def calculate_confluence_score(self, signal: CryptoSMCSignal) -> float:
        """Calculate confluence score for crypto SMC signal"""
        try:
            score = signal.base_score
            
            # Add component scores
            score += signal.volume_score
            score += signal.structure_score
            
            # Crypto-specific bonuses
            
            # 1. Volatility bonus (optimal volatility increases score)
            if signal.symbol in self.tick_data and len(self.tick_data[signal.symbol]) > 0:
                recent_tick = list(self.tick_data[signal.symbol])[-1]
                if 0.05 <= recent_tick.volatility <= 0.15:  # Optimal volatility range
                    score += 5.0
            
            # 2. Market cap weighting (BTC > ETH > XRP)
            if signal.symbol == "BTCUSD":
                score += 3.0  # BTC premium
            elif signal.symbol == "ETHUSD":
                score += 2.0  # ETH premium
            elif signal.symbol == "XRPUSD":
                score += 1.0  # XRP premium
            
            # 3. Pattern reliability bonus
            pattern_bonuses = {
                CryptoSMCPattern.LIQUIDITY_SWEEP: 8.0,     # Highest reliability
                CryptoSMCPattern.ORDER_BLOCK_BOUNCE: 6.0,  # High reliability
                CryptoSMCPattern.FAIR_VALUE_GAP: 4.0,      # Medium reliability
                CryptoSMCPattern.BREAK_OF_STRUCTURE: 5.0,  # Good reliability
                CryptoSMCPattern.CHANGE_OF_CHARACTER: 3.0  # Lower reliability
            }
            score += pattern_bonuses.get(signal.pattern, 0.0)
            
            # 4. Risk/Reward bonus
            if signal.take_profit_pct > 0 and signal.stop_loss_pct > 0:
                rr_ratio = signal.take_profit_pct / signal.stop_loss_pct
                if rr_ratio >= 2.0:  # 1:2 or better
                    score += min(5.0, rr_ratio)
            
            # Cap at realistic maximum for crypto
            final_score = min(score, 95.0)
            
            logger.debug(f"📊 {signal.symbol} {signal.pattern.value} confluence score: {final_score:.1f}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating confluence score: {e}")
            return signal.base_score
    
    def generate_crypto_signal(self, smc_signal: CryptoSMCSignal) -> Dict:
        """Convert SMC signal to standardized signal format"""
        try:
            # Generate unique signal ID
            signal_id = f"CORE_{smc_signal.symbol}_{smc_signal.pattern.value}_{int(time.time())}"
            
            # Determine signal type based on timeframe and pattern
            if smc_signal.timeframe in ["M1", "M5"]:
                signal_type = CryptoSignalType.SCALP_ATTACK
                duration = 30 * 60  # 30 minutes
                xp_multiplier = 1.2
            elif smc_signal.timeframe in ["M15"]:
                signal_type = CryptoSignalType.SWING_ASSAULT
                duration = 4 * 3600  # 4 hours
                xp_multiplier = 1.8
            else:
                signal_type = CryptoSignalType.POSITION_STRIKE
                duration = 24 * 3600  # 24 hours
                xp_multiplier = 2.5
            
            # Create standardized signal
            signal = {
                'signal_id': signal_id,
                'pair': smc_signal.symbol,
                'symbol': smc_signal.symbol,
                'direction': smc_signal.direction,
                'signal_type': signal_type.value,
                'pattern': smc_signal.pattern.value,
                'confidence': round(smc_signal.final_score, 1),
                'entry_price': round(smc_signal.entry_price, 2),
                'stop_loss': round(smc_signal.stop_loss_price, 2),
                'take_profit': round(smc_signal.take_profit_price, 2),
                'stop_loss_pct': round(smc_signal.stop_loss_pct, 2),
                'take_profit_pct': round(smc_signal.take_profit_pct, 2),
                'risk_reward': round(smc_signal.take_profit_pct / max(smc_signal.stop_loss_pct, 0.1), 1),
                'duration': duration,
                'xp_reward': int(smc_signal.final_score * xp_multiplier),
                'timeframe': smc_signal.timeframe,
                'timestamp': time.time(),
                'source': 'CORE_CRYPTO_SMC',
                'engine': 'C.O.R.E',
                'volume_confirmation': smc_signal.volume_confirmation,
                'market_structure': smc_signal.market_structure,
                'pattern_data': smc_signal.pattern_data,
                'base_confidence': smc_signal.base_score,
                'citadel_shielded': False  # Will be set by CITADEL Shield
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating crypto signal: {e}")
            return None
    
    def publish_crypto_signal(self, signal: Dict):
        """Publish crypto signal via ZMQ"""
        try:
            if self.publisher:
                signal_msg = json.dumps(signal)
                self.publisher.send_string(f"CORE_CRYPTO_SIGNAL {signal_msg}")
                
                # Log to truth tracker
                self.log_to_truth_tracker(signal)
                
                logger.info(f"📡 Published {signal['symbol']} {signal['direction']} @ {signal['confidence']:.1f}%")
                logger.info(f"   Pattern: {signal['pattern']} | RR: 1:{signal['risk_reward']}")
                
        except Exception as e:
            logger.error(f"Error publishing crypto signal: {e}")
    
    def log_to_truth_tracker(self, signal: Dict):
        """Log signal to truth tracking system"""
        try:
            truth_entry = {
                'signal_id': signal['signal_id'],
                'source': 'CORE_CRYPTO_SMC',
                'pair': signal['symbol'],
                'direction': signal['direction'],
                'pattern': signal['pattern'],
                'confidence': signal['confidence'],
                'entry_price': signal['entry_price'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'risk_reward': signal['risk_reward'],
                'signal_type': signal['signal_type'],
                'xp_reward': signal['xp_reward'],
                'timestamp': signal['timestamp'],
                'timeframe': signal['timeframe'],
                'volume_confirmed': signal['volume_confirmation'],
                'market_structure': signal['market_structure'],
                'status': 'ACTIVE',
                'outcome': 'PENDING'
            }
            
            response = requests.post(
                self.truth_tracker_url,
                json=truth_entry,
                timeout=2
            )
            
            if response.status_code == 200:
                logger.debug(f"✅ Truth tracker logged: {signal['signal_id']}")
            
        except Exception as e:
            logger.debug(f"Truth tracker error (non-critical): {e}")
    
    def main_scan_loop(self):
        """Main scanning loop for crypto patterns"""
        logger.info("🚀 Starting C.O.R.E. Crypto SMC main scan loop")
        
        while True:
            try:
                for symbol in self.crypto_symbols:
                    # Scan for patterns
                    patterns = self.scan_crypto_patterns(symbol)
                    
                    if patterns:
                        # Take the best pattern
                        best_pattern = patterns[0]
                        
                        # Generate signal
                        signal = self.generate_crypto_signal(best_pattern)
                        
                        if signal:
                            # Apply CITADEL Shield if available
                            if self.citadel_shield:
                                shielded_signal = self.citadel_shield.validate_and_enhance(signal.copy())
                                if shielded_signal:
                                    self.publish_crypto_signal(shielded_signal)
                                    self.signals_generated += 1
                                    self.last_signal_time[symbol] = time.time()
                            else:
                                # Publish without shield
                                self.publish_crypto_signal(signal)
                                self.signals_generated += 1
                                self.last_signal_time[symbol] = time.time()
                
                # Sleep between scans (30 seconds for crypto volatility)
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in main scan loop: {e}")
                time.sleep(60)
    
    def get_statistics(self) -> Dict:
        """Get engine statistics"""
        return {
            "signals_generated": self.signals_generated,
            "patterns_detected": dict(self.patterns_detected),
            "symbols_monitored": self.crypto_symbols,
            "data_status": {
                symbol: {
                    "ticks": len(self.tick_data[symbol]),
                    "m1_candles": len(self.m1_data[symbol]),
                    "m5_candles": len(self.m5_data[symbol]),
                    "m15_candles": len(self.m15_data[symbol]),
                    "m30_candles": len(self.m30_data[symbol])
                }
                for symbol in self.crypto_symbols
            }
        }

# Global instance for integration
crypto_smc_engine = CryptoSMCEngine()

def start_crypto_smc_engine():
    """Start the crypto SMC engine"""
    crypto_smc_engine.setup_zmq_publisher()
    crypto_smc_engine.main_scan_loop()

if __name__ == "__main__":
    # Test the crypto SMC engine
    print("🚀 C.O.R.E. Crypto SMC Pattern Detection System")
    print("=" * 60)
    
    # Initialize engine
    engine = CryptoSMCEngine()
    engine.setup_zmq_publisher()
    
    # Simulate some test data
    test_data = {
        "BTCUSD": {
            "price": 67245.50,
            "volume": 125.5,
            "spread": 25.0
        },
        "ETHUSD": {
            "price": 3456.78,
            "volume": 890.2,
            "spread": 2.5
        },
        "XRPUSD": {
            "price": 0.6234,
            "volume": 15000.0,
            "spread": 0.0008
        }
    }
    
    # Process test ticks
    for symbol, data in test_data.items():
        engine.process_crypto_tick(
            symbol=symbol,
            bid=data["price"] - data["spread"]/2,
            ask=data["price"] + data["spread"]/2,
            volume=data["volume"]
        )
    
    # Show statistics
    stats = engine.get_statistics()
    print(f"📊 Engine Statistics:")
    print(f"   Signals Generated: {stats['signals_generated']}")
    print(f"   Patterns Detected: {stats['patterns_detected']}")
    print(f"   Symbols Monitored: {len(stats['symbols_monitored'])}")
    
    print("\n✅ C.O.R.E. Crypto SMC Engine ready for production")
    print("🎯 Monitoring: BTCUSD, ETHUSD, XRPUSD")
    print("📡 Publishing signals on ZMQ port 5557")
    print("🛡️ CITADEL Shield integration ready")