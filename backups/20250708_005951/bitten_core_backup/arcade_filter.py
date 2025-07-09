# arcade_filter.py
# BITTEN Arcade Filter - High-Frequency Scalping Engine

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ArcadeStrategy(Enum):
    DAWN_RAID = "dawn_raid"           # London breakout
    WALL_DEFENDER = "wall_defender"   # S/R bounce
    ROCKET_RIDE = "rocket_ride"       # Momentum continuation
    RUBBER_BAND = "rubber_band"       # Mean reversion

@dataclass
class ArcadeSignal:
    """Arcade scalp signal structure"""
    strategy: ArcadeStrategy
    symbol: str
    direction: str  # 'buy' or 'sell'
    entry_price: float
    stop_loss: float
    take_profit: float
    tcs_score: int
    expected_duration: int  # minutes
    setup_description: str
    visual_emoji: str

class ArcadeFilter:
    """
    ARCADE SCALPING ENGINE
    
    65%+ TCS threshold for quality control
    10-20 pip targets, 5-45 minute holds
    20-30 signals per day across all pairs
    """
    
    def __init__(self):
        self.min_tcs = 65
        self.pairs = ['GBPUSD', 'EURUSD', 'USDJPY', 'GBPJPY', 'USDCAD']
        
        # Strategy-specific parameters
        self.dawn_raid_config = {
            'range_window': (7, 8),      # 7:00-8:00 GMT
            'breakout_window': (8, 10),  # 8:00-10:00 GMT
            'min_range_pips': 8,
            'max_range_pips': 25,
            'breakout_buffer': 3,
            'volume_spike': 1.5,
            'target_pips': 15,
            'stop_pips': 10
        }
        
        self.wall_defender_config = {
            'level_proximity': 3,         # pips from level
            'min_touches': 2,
            'rejection_size': 5,          # pip rejection candle
            'volume_confirm': 1.2,
            'target_pips': 12,
            'stop_pips': 8
        }
        
        self.rocket_ride_config = {
            'min_adx': 25,
            'ma_period': 21,
            'pullback_depth': 0.382,      # Fibonacci
            'momentum_confirm': 55,       # RSI
            'target_pips': 18,
            'stop_pips': 10
        }
        
        self.rubber_band_config = {
            'bb_deviation': 2.0,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'max_adx': 25,               # Must be ranging
            'target_pips': 15,
            'stop_pips': 12
        }
    
    def scan_all_pairs(self, market_data: Dict) -> List[ArcadeSignal]:
        """Scan all pairs for arcade opportunities"""
        signals = []
        
        for pair in self.pairs:
            if pair not in market_data:
                continue
                
            pair_data = market_data[pair]
            
            # Run all arcade strategies
            dawn_raid = self._detect_dawn_raid(pair, pair_data)
            if dawn_raid:
                signals.append(dawn_raid)
            
            wall_defender = self._detect_wall_defender(pair, pair_data)
            if wall_defender:
                signals.append(wall_defender)
            
            rocket_ride = self._detect_rocket_ride(pair, pair_data)
            if rocket_ride:
                signals.append(rocket_ride)
            
            rubber_band = self._detect_rubber_band(pair, pair_data)
            if rubber_band:
                signals.append(rubber_band)
        
        # Sort by TCS score
        signals.sort(key=lambda x: x.tcs_score, reverse=True)
        
        # Limit to top signals (avoid spam)
        return signals[:30]
    
    def _detect_dawn_raid(self, symbol: str, data: Dict) -> Optional[ArcadeSignal]:
        """
        DAWN RAID - London Breakout Strategy
        
        The classic institutional breakout play.
        Range forms pre-London, breaks with volume at open.
        """
        current_hour = datetime.utcnow().hour
        
        # Check if we're in breakout window
        if not (self.dawn_raid_config['breakout_window'][0] <= 
                current_hour < self.dawn_raid_config['breakout_window'][1]):
            return None
        
        # Check range formation
        range_high = data.get('range_high', 0)
        range_low = data.get('range_low', 0)
        current_price = data.get('close', 0)
        
        if not (range_high and range_low):
            return None
        
        # Calculate range size
        pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
        range_pips = (range_high - range_low) / pip_value
        
        # Validate range
        if not (self.dawn_raid_config['min_range_pips'] <= 
                range_pips <= self.dawn_raid_config['max_range_pips']):
            return None
        
        # Check for breakout
        breakout_high = range_high + (self.dawn_raid_config['breakout_buffer'] * pip_value)
        breakout_low = range_low - (self.dawn_raid_config['breakout_buffer'] * pip_value)
        
        direction = None
        entry_price = None
        
        if current_price > breakout_high:
            direction = 'buy'
            entry_price = breakout_high
            stop_loss = range_low - (5 * pip_value)
            take_profit = entry_price + (self.dawn_raid_config['target_pips'] * pip_value)
            
        elif current_price < breakout_low:
            direction = 'sell'
            entry_price = breakout_low
            stop_loss = range_high + (5 * pip_value)
            take_profit = entry_price - (self.dawn_raid_config['target_pips'] * pip_value)
        
        if not direction:
            return None
        
        # Volume confirmation
        volume_ratio = data.get('volume', 100) / data.get('volume_avg', 100)
        if volume_ratio < self.dawn_raid_config['volume_spike']:
            return None
        
        # Calculate TCS
        tcs_factors = {
            'range_quality': min(range_pips / 15, 1.0) * 20,      # 20 points max
            'volume_spike': min(volume_ratio / 2, 1.0) * 15,      # 15 points max
            'time_of_day': 20 if current_hour == 8 else 15,       # Early is better
            'breakout_strength': 15,                               # Clean break
            'base_score': 15                                       # Strategy base
        }
        
        tcs_score = int(sum(tcs_factors.values()))
        
        if tcs_score < self.min_tcs:
            return None
        
        return ArcadeSignal(
            strategy=ArcadeStrategy.DAWN_RAID,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            tcs_score=tcs_score,
            expected_duration=25,
            setup_description=f"London range break ({range_pips:.0f} pip range)",
            visual_emoji="🌅"
        )
    
    def _detect_wall_defender(self, symbol: str, data: Dict) -> Optional[ArcadeSignal]:
        """
        WALL DEFENDER - Support/Resistance Bounce
        
        The bread and butter of scalping.
        Price approaches key level, rejects with volume.
        """
        current_price = data.get('close', 0)
        key_levels = data.get('key_levels', [])
        
        if not key_levels:
            return None
        
        pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
        
        # Find nearest level
        nearest_level = None
        min_distance = float('inf')
        
        for level in key_levels:
            distance = abs(current_price - level['price'])
            if distance < min_distance:
                min_distance = distance
                nearest_level = level
        
        if not nearest_level:
            return None
        
        # Check proximity
        distance_pips = min_distance / pip_value
        if distance_pips > self.wall_defender_config['level_proximity']:
            return None
        
        # Check for rejection candle
        candle_range = data.get('high', 0) - data.get('low', 0)
        candle_range_pips = candle_range / pip_value
        
        if candle_range_pips < self.wall_defender_config['rejection_size']:
            return None
        
        # Determine direction based on level type
        if nearest_level['type'] == 'resistance' and current_price < data.get('high', 0):
            direction = 'sell'
            entry_price = current_price
            stop_loss = nearest_level['price'] + (self.wall_defender_config['stop_pips'] * pip_value)
            take_profit = entry_price - (self.wall_defender_config['target_pips'] * pip_value)
            
        elif nearest_level['type'] == 'support' and current_price > data.get('low', 0):
            direction = 'buy'
            entry_price = current_price
            stop_loss = nearest_level['price'] - (self.wall_defender_config['stop_pips'] * pip_value)
            take_profit = entry_price + (self.wall_defender_config['target_pips'] * pip_value)
        else:
            return None
        
        # Volume confirmation
        volume_ratio = data.get('volume', 100) / data.get('volume_avg', 100)
        
        # Calculate TCS
        tcs_factors = {
            'level_strength': nearest_level.get('strength', 0.5) * 25,  # 25 points max
            'rejection_quality': min(candle_range_pips / 10, 1.0) * 20, # 20 points max
            'volume_confirm': min(volume_ratio / 1.5, 1.0) * 15,        # 15 points max
            'level_touches': min(nearest_level.get('touches', 2) / 4, 1.0) * 10,
            'base_score': 10
        }
        
        tcs_score = int(sum(tcs_factors.values()))
        
        if tcs_score < self.min_tcs:
            return None
        
        return ArcadeSignal(
            strategy=ArcadeStrategy.WALL_DEFENDER,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            tcs_score=tcs_score,
            expected_duration=20,
            setup_description=f"{nearest_level['type'].title()} bounce at {nearest_level['price']:.5f}",
            visual_emoji="🏰"
        )
    
    def _detect_rocket_ride(self, symbol: str, data: Dict) -> Optional[ArcadeSignal]:
        """
        ROCKET RIDE - Momentum Continuation
        
        Trend is your friend until the end.
        Pullback to MA, momentum resumes.
        """
        adx = data.get('adx', 0)
        if adx < self.rocket_ride_config['min_adx']:
            return None
        
        current_price = data.get('close', 0)
        ma21 = data.get('ma_21', 0)
        rsi = data.get('rsi', 50)
        
        if not ma21:
            return None
        
        pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
        
        # Check pullback to MA
        distance_from_ma = abs(current_price - ma21)
        distance_pips = distance_from_ma / pip_value
        
        if distance_pips > 5:  # Must be near MA
            return None
        
        # Determine trend direction
        trend_direction = 'up' if current_price > ma21 else 'down'
        
        # Check momentum confirmation
        if trend_direction == 'up':
            if rsi < self.rocket_ride_config['momentum_confirm']:
                return None
            direction = 'buy'
            entry_price = current_price
            stop_loss = ma21 - (self.rocket_ride_config['stop_pips'] * pip_value)
            take_profit = entry_price + (self.rocket_ride_config['target_pips'] * pip_value)
            
        else:  # down trend
            if rsi > (100 - self.rocket_ride_config['momentum_confirm']):
                return None
            direction = 'sell'
            entry_price = current_price
            stop_loss = ma21 + (self.rocket_ride_config['stop_pips'] * pip_value)
            take_profit = entry_price - (self.rocket_ride_config['target_pips'] * pip_value)
        
        # Calculate TCS
        tcs_factors = {
            'trend_strength': min(adx / 50, 1.0) * 25,              # 25 points max
            'pullback_quality': (1 - distance_pips / 5) * 20,       # 20 points max
            'momentum_align': 15 if rsi > 50 and direction == 'buy' else 10,
            'ma_confluence': 15,                                     # At MA support
            'base_score': 10
        }
        
        tcs_score = int(sum(tcs_factors.values()))
        
        if tcs_score < self.min_tcs:
            return None
        
        return ArcadeSignal(
            strategy=ArcadeStrategy.ROCKET_RIDE,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            tcs_score=tcs_score,
            expected_duration=30,
            setup_description=f"Momentum continuation (ADX: {adx:.0f})",
            visual_emoji="🚀"
        )
    
    def _detect_rubber_band(self, symbol: str, data: Dict) -> Optional[ArcadeSignal]:
        """
        RUBBER BAND - Mean Reversion
        
        What goes up must come down.
        Extreme deviation, snap back to mean.
        """
        adx = data.get('adx', 100)
        if adx > self.rubber_band_config['max_adx']:
            return None  # Too trendy
        
        current_price = data.get('close', 0)
        bb_upper = data.get('bb_upper', 0)
        bb_lower = data.get('bb_lower', 0)
        bb_middle = data.get('bb_middle', 0)
        rsi = data.get('rsi', 50)
        
        if not all([bb_upper, bb_lower, bb_middle]):
            return None
        
        pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
        
        # Check for extreme deviation
        direction = None
        
        if current_price >= bb_upper and rsi > self.rubber_band_config['rsi_overbought']:
            direction = 'sell'
            entry_price = current_price
            stop_loss = current_price + (self.rubber_band_config['stop_pips'] * pip_value)
            # Target halfway back to middle
            target_distance = (current_price - bb_middle) * 0.618
            take_profit = current_price - target_distance
            
        elif current_price <= bb_lower and rsi < self.rubber_band_config['rsi_oversold']:
            direction = 'buy'
            entry_price = current_price
            stop_loss = current_price - (self.rubber_band_config['stop_pips'] * pip_value)
            # Target halfway back to middle
            target_distance = (bb_middle - current_price) * 0.618
            take_profit = current_price + target_distance
        
        if not direction:
            return None
        
        # Calculate deviation magnitude
        if direction == 'sell':
            deviation = (current_price - bb_upper) / (bb_upper - bb_middle)
        else:
            deviation = (bb_lower - current_price) / (bb_middle - bb_lower)
        
        # Calculate TCS
        tcs_factors = {
            'deviation_extreme': min(abs(deviation), 1.0) * 25,     # 25 points max
            'rsi_extreme': 20 if rsi < 25 or rsi > 75 else 10,     # 20 points max
            'ranging_market': (1 - adx / 40) * 20,                 # 20 points max
            'bb_confirmation': 15,                                   # At band extreme
            'base_score': 10
        }
        
        tcs_score = int(sum(tcs_factors.values()))
        
        if tcs_score < self.min_tcs:
            return None
        
        return ArcadeSignal(
            strategy=ArcadeStrategy.RUBBER_BAND,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            tcs_score=tcs_score,
            expected_duration=25,
            setup_description=f"Mean reversion (RSI: {rsi:.0f})",
            visual_emoji="🎯"
        )
    
    def format_signal_card(self, signal: ArcadeSignal) -> str:
        """Format arcade signal for display"""
        pip_value = 0.0001 if not signal.symbol.endswith('JPY') else 0.01
        target_pips = abs(signal.take_profit - signal.entry_price) / pip_value
        
        return f"""┌────────────────────────────┐
│ {signal.visual_emoji} {signal.strategy.value.upper().replace('_', ' ')}
│ {signal.symbol} | TCS: {signal.tcs_score}%
│ Entry: {signal.entry_price:.5f}
│ Target: +{target_pips:.0f} pips
│ Time: ~{signal.expected_duration} min
│ [{' 🔫 FIRE' if signal.tcs_score >= 70 else '⚡ READY'}]
└────────────────────────────┘"""