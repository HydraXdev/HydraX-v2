# sniper_filter.py
# BITTEN Sniper Filter - Elite Position Detection (CLASSIFIED)

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib

@dataclass
class SniperSignal:
    """Elite sniper position signal"""
    internal_strategy: str  # NEVER exposed to user
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    tcs_score: int
    expected_pips: int
    max_duration: int  # minutes
    signal_hash: str   # Unique identifier

class SniperFilter:
    """
    CLASSIFIED SNIPER ENGINE
    
    75%+ TCS threshold for elite signals only
    30-50+ pip targets, 1-2 hour positions
    3-5 signals per day maximum
    
    SECURITY: Strategy names are NEVER revealed to users
    """
    
    def __init__(self):
        self.min_tcs = 75
        self.daily_limit = 5
        self.signals_today = 0
        self.last_reset = datetime.now().date()
        
        # CLASSIFIED strategy configurations
        self._liquidity_config = {
            'hunt_hours': [9, 10, 14, 15],  # Peak liquidity times
            'min_volume_spike': 2.0,
            'stop_hunt_distance': 15,
            'reversal_confirmation': True,
            'target_multiplier': 3.0
        }
        
        self._tokyo_config = {
            'active_hours': (23, 3),  # 11PM-3AM EST
            'range_breakout': False,
            'trap_pattern': 'accumulation',
            'min_range': 20,
            'false_break_pips': 10
        }
        
        self._news_fade_config = {
            'post_news_minutes': 30,
            'fade_threshold': 40,  # pips
            'volume_exhaustion': True,
            'sentiment_reversal': True
        }
        
        self._pivot_magnet_config = {
            'pivot_types': ['weekly', 'monthly'],
            'magnet_distance': 50,  # pips
            'confluence_required': 2,
            'time_weight': 0.8
        }
    
    def scan_for_snipers(self, market_data: Dict) -> List[SniperSignal]:
        """
        Run all classified strategies
        Output is sanitized - no strategy names revealed
        """
        # Reset daily counter if needed
        if datetime.now().date() > self.last_reset:
            self.signals_today = 0
            self.last_reset = datetime.now().date()
        
        if self.signals_today >= self.daily_limit:
            return []
        
        signals = []
        
        # Run each classified strategy
        for pair in ['GBPUSD', 'EURUSD', 'USDJPY', 'GBPJPY', 'USDCAD']:
            if pair not in market_data:
                continue
            
            # Strategy 1: Liquidity Hunt (CLASSIFIED)
            signal = self._detect_liquidity_hunt(pair, market_data[pair])
            if signal and signal.tcs_score >= self.min_tcs:
                signals.append(signal)
            
            # Strategy 2: Tokyo Trap (CLASSIFIED)
            signal = self._detect_tokyo_trap(pair, market_data[pair])
            if signal and signal.tcs_score >= self.min_tcs:
                signals.append(signal)
            
            # Strategy 3: News Fade (CLASSIFIED)
            signal = self._detect_news_fade(pair, market_data[pair])
            if signal and signal.tcs_score >= self.min_tcs:
                signals.append(signal)
            
            # Strategy 4: Pivot Magnet (CLASSIFIED)
            signal = self._detect_pivot_magnet(pair, market_data[pair])
            if signal and signal.tcs_score >= self.min_tcs:
                signals.append(signal)
        
        # Sort by TCS and limit
        signals.sort(key=lambda x: x.tcs_score, reverse=True)
        available_slots = self.daily_limit - self.signals_today
        
        return signals[:available_slots]
    
    def _detect_liquidity_hunt(self, symbol: str, data: Dict) -> Optional[SniperSignal]:
        """
        CLASSIFIED STRATEGY #1
        
        Detects institutional stop hunting patterns.
        Big money clears stops before real move.
        """
        current_hour = datetime.now().hour
        if current_hour not in self._liquidity_config['hunt_hours']:
            return None
        
        # Check for stop hunt pattern
        recent_high = data.get('session_high', 0)
        recent_low = data.get('session_low', 0)
        current_price = data.get('close', 0)
        
        if not all([recent_high, recent_low, current_price]):
            return None
        
        pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
        
        # Detect stop hunt above highs
        spike_above = data.get('spike_high', 0)
        if spike_above > recent_high:
            spike_distance = (spike_above - recent_high) / pip_value
            if spike_distance >= self._liquidity_config['stop_hunt_distance']:
                if current_price < recent_high:  # Price back below
                    # Liquidity grabbed, reversal likely
                    direction = 'sell'
                    entry_price = current_price
                    stop_loss = spike_above + (10 * pip_value)
                    
                    # Target based on hunt magnitude
                    target_pips = spike_distance * self._liquidity_config['target_multiplier']
                    take_profit = entry_price - (target_pips * pip_value)
                    
                    # Calculate elite TCS
                    tcs = self._calculate_liquidity_tcs(data, spike_distance)
                    
                    if tcs >= self.min_tcs:
                        return self._create_sniper_signal(
                            'liquidity_hunt',
                            symbol, direction, entry_price,
                            stop_loss, take_profit, tcs
                        )
        
        # Check for stop hunt below lows (similar logic)
        spike_below = data.get('spike_low', 0)
        if spike_below and spike_below < recent_low:
            spike_distance = (recent_low - spike_below) / pip_value
            if spike_distance >= self._liquidity_config['stop_hunt_distance']:
                if current_price > recent_low:
                    direction = 'buy'
                    entry_price = current_price
                    stop_loss = spike_below - (10 * pip_value)
                    target_pips = spike_distance * self._liquidity_config['target_multiplier']
                    take_profit = entry_price + (target_pips * pip_value)
                    
                    tcs = self._calculate_liquidity_tcs(data, spike_distance)
                    if tcs >= self.min_tcs:
                        return self._create_sniper_signal(
                            'liquidity_hunt',
                            symbol, direction, entry_price,
                            stop_loss, take_profit, tcs
                        )
        
        return None
    
    def _detect_tokyo_trap(self, symbol: str, data: Dict) -> Optional[SniperSignal]:
        """
        CLASSIFIED STRATEGY #2
        
        Asian session accumulation before London move.
        Institutional positioning hidden in low volume.
        """
        current_hour = datetime.now().hour
        
        # Check if in Tokyo session window
        if not (23 <= current_hour or current_hour <= 3):
            return None
        
        # Only works on JPY pairs
        if 'JPY' not in symbol:
            return None
        
        # Detect accumulation pattern
        range_high = data.get('tokyo_high', 0)
        range_low = data.get('tokyo_low', 0)
        current_price = data.get('close', 0)
        volume_profile = data.get('volume_profile', {})
        
        if not all([range_high, range_low]):
            return None
        
        pip_value = 0.01  # JPY pairs
        range_size = (range_high - range_low) / pip_value
        
        if range_size < self._tokyo_config['min_range']:
            return None
        
        # Check for false breakout pattern
        if current_price > range_high:
            # Potential bull trap
            break_distance = (current_price - range_high) / pip_value
            if break_distance <= self._tokyo_config['false_break_pips']:
                # High probability of reversal
                direction = 'sell'
                entry_price = current_price
                stop_loss = current_price + (15 * pip_value)
                take_profit = range_low - (10 * pip_value)
                
                tcs = self._calculate_tokyo_tcs(data, range_size, break_distance)
                if tcs >= self.min_tcs:
                    return self._create_sniper_signal(
                        'tokyo_trap',
                        symbol, direction, entry_price,
                        stop_loss, take_profit, tcs
                    )
        
        return None
    
    def _detect_news_fade(self, symbol: str, data: Dict) -> Optional[SniperSignal]:
        """
        CLASSIFIED STRATEGY #3
        
        Fade the initial news spike.
        Emotional money rushes in, smart money fades.
        """
        last_news = data.get('last_news_time')
        if not last_news:
            return None
        
        # Check if within fade window
        time_since_news = (datetime.now() - last_news).total_seconds() / 60
        if not (15 <= time_since_news <= self._news_fade_config['post_news_minutes']):
            return None
        
        # Check for exhaustion
        news_spike_high = data.get('news_spike_high', 0)
        news_spike_low = data.get('news_spike_low', 0)
        current_price = data.get('close', 0)
        pre_news_price = data.get('pre_news_price', 0)
        
        if not all([news_spike_high, current_price, pre_news_price]):
            return None
        
        pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
        
        # Measure spike magnitude
        if current_price > pre_news_price:  # Bullish spike
            spike_pips = (news_spike_high - pre_news_price) / pip_value
            if spike_pips >= self._news_fade_config['fade_threshold']:
                # Check for exhaustion signs
                if self._check_exhaustion(data):
                    direction = 'sell'
                    entry_price = current_price
                    stop_loss = news_spike_high + (10 * pip_value)
                    take_profit = pre_news_price + (10 * pip_value)  # Back to pre-news
                    
                    tcs = self._calculate_news_fade_tcs(data, spike_pips, time_since_news)
                    if tcs >= self.min_tcs:
                        return self._create_sniper_signal(
                            'news_fade',
                            symbol, direction, entry_price,
                            stop_loss, take_profit, tcs
                        )
        
        return None
    
    def _detect_pivot_magnet(self, symbol: str, data: Dict) -> Optional[SniperSignal]:
        """
        CLASSIFIED STRATEGY #4
        
        Weekly/Monthly pivots act as magnets.
        Price gravitates to these levels like clockwork.
        """
        current_price = data.get('close', 0)
        weekly_pivot = data.get('weekly_pivot', 0)
        monthly_pivot = data.get('monthly_pivot', 0)
        
        if not any([weekly_pivot, monthly_pivot]):
            return None
        
        pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
        
        # Check distance to pivots
        pivots = []
        if weekly_pivot:
            distance = abs(current_price - weekly_pivot) / pip_value
            if distance <= self._pivot_magnet_config['magnet_distance']:
                pivots.append(('weekly', weekly_pivot, distance))
        
        if monthly_pivot:
            distance = abs(current_price - monthly_pivot) / pip_value
            if distance <= self._pivot_magnet_config['magnet_distance']:
                pivots.append(('monthly', monthly_pivot, distance))
        
        if not pivots:
            return None
        
        # Sort by distance
        pivots.sort(key=lambda x: x[2])
        pivot_type, pivot_price, distance_pips = pivots[0]
        
        # Determine direction (price gets pulled to pivot)
        if current_price > pivot_price:
            direction = 'sell'
            entry_price = current_price
            stop_loss = current_price + (20 * pip_value)
            take_profit = pivot_price
        else:
            direction = 'buy'
            entry_price = current_price
            stop_loss = current_price - (20 * pip_value)
            take_profit = pivot_price
        
        # Check for confluence
        confluence = self._check_pivot_confluence(data, pivot_price)
        if confluence < self._pivot_magnet_config['confluence_required']:
            return None
        
        tcs = self._calculate_pivot_tcs(data, distance_pips, pivot_type, confluence)
        
        if tcs >= self.min_tcs:
            return self._create_sniper_signal(
                'pivot_magnet',
                symbol, direction, entry_price,
                stop_loss, take_profit, tcs
            )
        
        return None
    
    def _create_sniper_signal(self, strategy: str, symbol: str, direction: str,
                             entry: float, stop: float, target: float, tcs: int) -> SniperSignal:
        """Create sanitized sniper signal - NEVER expose strategy name"""
        pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
        expected_pips = int(abs(target - entry) / pip_value)
        
        # Generate unique hash for tracking
        signal_hash = hashlib.md5(
            f"{strategy}{symbol}{entry}{datetime.now()}".encode()
        ).hexdigest()[:8]
        
        self.signals_today += 1
        
        return SniperSignal(
            internal_strategy=strategy,  # NEVER expose this
            symbol=symbol,
            direction=direction,
            entry_price=entry,
            stop_loss=stop,
            take_profit=target,
            tcs_score=tcs,
            expected_pips=expected_pips,
            max_duration=120,  # 2 hours max
            signal_hash=signal_hash
        )
    
    def _calculate_liquidity_tcs(self, data: Dict, spike_distance: float) -> int:
        """Calculate TCS for liquidity hunt"""
        base = 50
        
        # Spike magnitude (bigger = better)
        base += min(spike_distance / 30, 1.0) * 20
        
        # Volume spike
        volume_ratio = data.get('volume_spike', 1.0)
        base += min(volume_ratio / 3, 1.0) * 15
        
        # Time of day bonus
        if datetime.now().hour in [9, 14]:  # Peak times
            base += 10
        
        # Reversal confirmation
        if data.get('reversal_candle', False):
            base += 5
        
        return int(base)
    
    def _calculate_tokyo_tcs(self, data: Dict, range_size: float, break_distance: float) -> int:
        """Calculate TCS for Tokyo trap"""
        base = 55
        
        # Range quality
        base += min(range_size / 40, 1.0) * 20
        
        # False break quality
        base += (1 - min(break_distance / 10, 1.0)) * 15
        
        # Volume profile
        if data.get('accumulation_detected', False):
            base += 10
        
        return int(base)
    
    def _calculate_news_fade_tcs(self, data: Dict, spike_pips: float, time_since: float) -> int:
        """Calculate TCS for news fade"""
        base = 50
        
        # Spike magnitude
        base += min(spike_pips / 50, 1.0) * 20
        
        # Timing (sweet spot 20-25 mins)
        if 20 <= time_since <= 25:
            base += 15
        else:
            base += 10
        
        # Exhaustion signs
        if data.get('volume_divergence', False):
            base += 10
        if data.get('momentum_divergence', False):
            base += 5
        
        return int(base)
    
    def _calculate_pivot_tcs(self, data: Dict, distance: float, pivot_type: str, confluence: int) -> int:
        """Calculate TCS for pivot magnet"""
        base = 55
        
        # Distance (closer = stronger pull)
        base += (1 - min(distance / 50, 1.0)) * 20
        
        # Pivot type
        if pivot_type == 'monthly':
            base += 10
        else:
            base += 5
        
        # Confluence
        base += min(confluence * 5, 15)
        
        return int(base)
    
    def _check_exhaustion(self, data: Dict) -> bool:
        """Check for exhaustion patterns"""
        return (data.get('volume_declining', False) or 
                data.get('momentum_divergence', False) or
                data.get('rejection_wick', False))
    
    def _check_pivot_confluence(self, data: Dict, pivot: float) -> int:
        """Count confluence factors at pivot"""
        confluence = 0
        
        # Check if pivot aligns with other levels
        if abs(pivot - data.get('daily_pivot', 0)) < 0.0010:
            confluence += 1
        if abs(pivot - data.get('fib_level', 0)) < 0.0010:
            confluence += 1
        if abs(pivot - data.get('ma_200', 0)) < 0.0010:
            confluence += 1
            
        return confluence
    
    def format_sniper_card(self, signal: SniperSignal) -> str:
        """Format sniper signal for display - CLASSIFIED"""
        return f"""┌────────────────────────────┐
│ 🎯 SNIPER SHOT DETECTED!  │
│    [CLASSIFIED SETUP]     │
│      TCS: {signal.tcs_score}%             │
│   Expected: {signal.expected_pips} pips       │
│   Duration: <2 hours      │
│                           │
│   [🔫 FIRE] FANG+ ONLY   │
└────────────────────────────┘"""