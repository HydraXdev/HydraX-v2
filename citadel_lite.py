#!/usr/bin/env python3
"""
CITADEL Lite - Liquidity Sweep Protection System
Protects users from broker stop hunts by detecting and avoiding pre-sweep entries
"""

import json
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LiquidityZone:
    """Represents a zone where stops are likely clustered"""
    level: float
    zone_type: str  # 'resistance' or 'support'
    strength: int   # 1-5 based on touches/rejections
    last_test: datetime
    sweep_probability: float
    pip_buffer: int  # How many pips beyond for sweep

@dataclass
class DelayedSignal:
    """Signal delayed due to sweep risk"""
    signal_id: str
    symbol: str
    direction: str
    original_confidence: float
    delay_reason: str
    delayed_at: datetime
    liquidity_zone: LiquidityZone
    expiry: datetime
    # Store critical trading parameters
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_price: Optional[float] = None
    stop_pips: Optional[float] = None
    target_pips: Optional[float] = None
    pattern_type: Optional[str] = None
    signal_type: Optional[str] = None

class CitadelProtection:
    """
    CITADEL Lite Protection System
    Detects and protects against liquidity sweeps (stop hunts)
    """
    
    def __init__(self):
        # Liquidity zone tracking
        self.liquidity_zones = defaultdict(list)  # symbol -> [LiquidityZone]
        self.recent_highs = defaultdict(lambda: deque(maxlen=50))
        self.recent_lows = defaultdict(lambda: deque(maxlen=50))
        
        # Sweep detection
        self.active_sweeps = {}  # symbol -> sweep_data
        self.completed_sweeps = defaultdict(list)  # symbol -> [sweep_events]
        
        # Signal management
        self.delayed_signals = []
        self.protected_signals = []
        
        # Configuration
        self.SWEEP_ZONE_PIPS = 5  # How close to zone = risk
        self.SWEEP_COMPLETION_PIPS = 3  # Reversal needed to confirm
        self.POST_SWEEP_BOOST = 20  # Confidence boost for post-sweep
        self.MAX_DELAY_MINUTES = 30  # Max time to delay a signal
        
        # Statistics
        self.stats = {
            'signals_delayed': 0,
            'sweeps_detected': 0,
            'sweeps_avoided': 0,
            'post_sweep_entries': 0
        }
    
    def update_market_structure(self, symbol: str, candles: List[Dict]):
        """Update liquidity zones based on market structure"""
        if len(candles) < 20:
            return
        
        # Find significant highs and lows (potential stop zones)
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        
        # Rolling 20-period high/low
        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        
        # Store for quick access
        self.recent_highs[symbol].append(recent_high)
        self.recent_lows[symbol].append(recent_low)
        
        # Identify liquidity zones (where stops cluster)
        self._identify_liquidity_zones(symbol, candles)
    
    def _identify_liquidity_zones(self, symbol: str, candles: List[Dict]):
        """Identify zones where retail stops likely cluster"""
        pip_size = 0.01 if 'JPY' in symbol else 0.0001
        
        # Clear old zones
        self.liquidity_zones[symbol] = []
        
        # Find swing points (where stops cluster)
        for i in range(10, len(candles) - 10):
            # Swing high detection
            if (candles[i]['high'] > candles[i-1]['high'] and 
                candles[i]['high'] > candles[i+1]['high']):
                
                # Check how many times this level was tested
                level = candles[i]['high']
                touches = self._count_level_touches(candles, level, pip_size * 3)
                
                if touches >= 2:  # Significant level
                    zone = LiquidityZone(
                        level=level,
                        zone_type='resistance',
                        strength=min(5, touches),
                        last_test=datetime.now(),
                        sweep_probability=self._calculate_sweep_probability(level, candles[-1]['close'], 'resistance'),
                        pip_buffer=5
                    )
                    self.liquidity_zones[symbol].append(zone)
            
            # Swing low detection
            if (candles[i]['low'] < candles[i-1]['low'] and 
                candles[i]['low'] < candles[i+1]['low']):
                
                level = candles[i]['low']
                touches = self._count_level_touches(candles, level, pip_size * 3)
                
                if touches >= 2:
                    zone = LiquidityZone(
                        level=level,
                        zone_type='support',
                        strength=min(5, touches),
                        last_test=datetime.now(),
                        sweep_probability=self._calculate_sweep_probability(level, candles[-1]['close'], 'support'),
                        pip_buffer=5
                    )
                    self.liquidity_zones[symbol].append(zone)
        
        # Sort zones by proximity to current price
        current_price = candles[-1]['close']
        self.liquidity_zones[symbol].sort(key=lambda z: abs(z.level - current_price))
        
        # Keep only nearest 3 zones each direction
        resistance_zones = [z for z in self.liquidity_zones[symbol] if z.zone_type == 'resistance'][:3]
        support_zones = [z for z in self.liquidity_zones[symbol] if z.zone_type == 'support'][:3]
        self.liquidity_zones[symbol] = resistance_zones + support_zones
    
    def _count_level_touches(self, candles: List[Dict], level: float, tolerance: float) -> int:
        """Count how many times a level was touched/tested"""
        touches = 0
        for candle in candles:
            if abs(candle['high'] - level) <= tolerance or abs(candle['low'] - level) <= tolerance:
                touches += 1
        return touches
    
    def _calculate_sweep_probability(self, zone_level: float, current_price: float, zone_type: str) -> float:
        """Calculate probability of a sweep based on proximity and market conditions"""
        pip_size = 0.0001  # Simplified, adjust per pair
        distance_pips = abs(zone_level - current_price) / pip_size
        
        # Closer = higher probability
        if distance_pips <= 5:
            base_probability = 0.8
        elif distance_pips <= 10:
            base_probability = 0.6
        elif distance_pips <= 20:
            base_probability = 0.4
        else:
            base_probability = 0.2
        
        # Adjust based on session (London/NY more likely to sweep)
        hour = datetime.now().hour
        if 8 <= hour <= 17:  # London/NY sessions
            base_probability *= 1.2
        
        return min(1.0, base_probability)
    
    def check_sweep_risk(self, signal: Dict) -> Tuple[bool, Optional[LiquidityZone]]:
        """Check if signal is at risk of being swept"""
        symbol = signal['symbol']
        direction = signal['direction']
        entry = signal['entry_price']
        
        if symbol not in self.liquidity_zones:
            return False, None
        
        pip_size = 0.01 if 'JPY' in symbol else 0.0001
        
        for zone in self.liquidity_zones[symbol]:
            distance_pips = abs(entry - zone.level) / pip_size
            
            # Check if entry is dangerously close to liquidity zone
            if distance_pips <= self.SWEEP_ZONE_PIPS:
                # Extra dangerous if we're on the wrong side
                if (direction == 'BUY' and zone.zone_type == 'resistance' and entry < zone.level):
                    return True, zone  # Likely to get swept
                elif (direction == 'SELL' and zone.zone_type == 'support' and entry > zone.level):
                    return True, zone  # Likely to get swept
        
        return False, None
    
    def detect_active_sweep(self, symbol: str, current_tick: Dict) -> bool:
        """Detect if a sweep is currently happening"""
        if symbol not in self.liquidity_zones:
            return False
        
        current_price = current_tick['bid']
        pip_size = 0.01 if 'JPY' in symbol else 0.0001
        
        for zone in self.liquidity_zones[symbol]:
            # Check if price just spiked beyond a zone
            if zone.zone_type == 'resistance':
                if current_price > zone.level + (zone.pip_buffer * pip_size):
                    # Price broke above resistance - potential sweep
                    if symbol not in self.active_sweeps:
                        self.active_sweeps[symbol] = {
                            'zone': zone,
                            'direction': 'up',
                            'start_price': current_price,
                            'start_time': datetime.now(),
                            'peak_price': current_price
                        }
                        logger.info(f"🎯 SWEEP DETECTED: {symbol} above {zone.level:.5f}")
                        self.stats['sweeps_detected'] += 1
                        return True
                    
            elif zone.zone_type == 'support':
                if current_price < zone.level - (zone.pip_buffer * pip_size):
                    # Price broke below support - potential sweep
                    if symbol not in self.active_sweeps:
                        self.active_sweeps[symbol] = {
                            'zone': zone,
                            'direction': 'down',
                            'start_price': current_price,
                            'start_time': datetime.now(),
                            'bottom_price': current_price
                        }
                        logger.info(f"🎯 SWEEP DETECTED: {symbol} below {zone.level:.5f}")
                        self.stats['sweeps_detected'] += 1
                        return True
        
        return False
    
    def check_sweep_completion(self, symbol: str, current_tick: Dict) -> bool:
        """Check if an active sweep has completed (reversed)"""
        if symbol not in self.active_sweeps:
            return False
        
        sweep = self.active_sweeps[symbol]
        current_price = current_tick['bid']
        pip_size = 0.01 if 'JPY' in symbol else 0.0001
        
        # Check for reversal
        if sweep['direction'] == 'up':
            # Swept up, now reversing down?
            if current_price < sweep['zone'].level - (self.SWEEP_COMPLETION_PIPS * pip_size):
                # Sweep complete - bearish reversal
                self.completed_sweeps[symbol].append({
                    'zone': sweep['zone'],
                    'direction': 'up_then_down',
                    'completion_time': datetime.now(),
                    'pips_swept': (sweep.get('peak_price', sweep['start_price']) - sweep['zone'].level) / pip_size
                })
                del self.active_sweeps[symbol]
                logger.info(f"✅ SWEEP COMPLETE: {symbol} reversed from resistance")
                return True
                
        elif sweep['direction'] == 'down':
            # Swept down, now reversing up?
            if current_price > sweep['zone'].level + (self.SWEEP_COMPLETION_PIPS * pip_size):
                # Sweep complete - bullish reversal
                self.completed_sweeps[symbol].append({
                    'zone': sweep['zone'],
                    'direction': 'down_then_up',
                    'completion_time': datetime.now(),
                    'pips_swept': (sweep['zone'].level - sweep.get('bottom_price', sweep['start_price'])) / pip_size
                })
                del self.active_sweeps[symbol]
                logger.info(f"✅ SWEEP COMPLETE: {symbol} reversed from support")
                return True
        
        # Update extremes
        if sweep['direction'] == 'up' and current_price > sweep.get('peak_price', 0):
            sweep['peak_price'] = current_price
        elif sweep['direction'] == 'down' and current_price < sweep.get('bottom_price', float('inf')):
            sweep['bottom_price'] = current_price
        
        return False
    
    def is_post_sweep_opportunity(self, signal: Dict) -> bool:
        """Check if this signal is a golden post-sweep entry"""
        symbol = signal['symbol']
        
        # Check recent completed sweeps
        if symbol in self.completed_sweeps:
            recent_sweeps = [s for s in self.completed_sweeps[symbol] 
                           if (datetime.now() - s['completion_time']).seconds < 300]  # Last 5 minutes
            
            for sweep in recent_sweeps:
                # Match signal direction with sweep reversal
                if (sweep['direction'] == 'up_then_down' and signal['direction'] == 'SELL'):
                    logger.info(f"🏆 POST-SWEEP OPPORTUNITY: {symbol} SELL after resistance sweep")
                    self.stats['post_sweep_entries'] += 1
                    return True
                elif (sweep['direction'] == 'down_then_up' and signal['direction'] == 'BUY'):
                    logger.info(f"🏆 POST-SWEEP OPPORTUNITY: {symbol} BUY after support sweep")
                    self.stats['post_sweep_entries'] += 1
                    return True
        
        return False
    
    def protect_signal(self, signal: Dict) -> Optional[Dict]:
        """
        Main protection function - decides if signal should be:
        1. PASSED - Safe to trade
        2. DELAYED - Sweep risk, wait
        3. BOOSTED - Post-sweep golden opportunity
        """
        symbol = signal['symbol']
        
        # Check if this is a post-sweep opportunity
        if self.is_post_sweep_opportunity(signal):
            # GOLDEN OPPORTUNITY - Boost confidence
            signal['confidence'] += self.POST_SWEEP_BOOST
            signal['citadel_protected'] = True
            signal['citadel_boost'] = 'POST_SWEEP'
            logger.info(f"🛡️ CITADEL BOOST: {symbol} confidence +{self.POST_SWEEP_BOOST}% (post-sweep)")
            return signal
        
        # Check sweep risk
        at_risk, risk_zone = self.check_sweep_risk(signal)
        
        if at_risk and risk_zone:
            # DELAY this signal - high sweep risk
            delayed = DelayedSignal(
                signal_id=signal['signal_id'],
                symbol=symbol,
                direction=signal['direction'],
                original_confidence=signal['confidence'],
                delay_reason=f"Near {risk_zone.zone_type} @ {risk_zone.level:.5f}",
                delayed_at=datetime.now(),
                liquidity_zone=risk_zone,
                expiry=datetime.now() + timedelta(minutes=self.MAX_DELAY_MINUTES),
                # Preserve critical trading parameters
                stop_loss=signal.get('stop_loss'),
                take_profit=signal.get('take_profit'),
                entry_price=signal.get('entry_price'),
                stop_pips=signal.get('stop_pips'),
                target_pips=signal.get('target_pips'),
                pattern_type=signal.get('pattern_type'),
                signal_type=signal.get('signal_type')
            )
            self.delayed_signals.append(delayed)
            self.stats['signals_delayed'] += 1
            
            logger.warning(f"⏸️ CITADEL DELAY: {symbol} {signal['direction']} - Sweep risk at {risk_zone.level:.5f}")
            return None  # Don't send signal yet
        
        # No immediate risk - pass through with protection badge
        signal['citadel_protected'] = True
        signal['citadel_status'] = 'VERIFIED'
        return signal
    
    def check_delayed_signals(self, current_tick_data: Dict) -> List[Dict]:
        """Check if any delayed signals can now be released"""
        released_signals = []
        current_time = datetime.now()
        
        for delayed in self.delayed_signals[:]:  # Copy to allow removal
            # Check if expired
            if current_time > delayed.expiry:
                self.delayed_signals.remove(delayed)
                logger.info(f"❌ Delayed signal expired: {delayed.symbol}")
                continue
            
            # Check if sweep completed for this signal
            if delayed.symbol in current_tick_data:
                if self.check_sweep_completion(delayed.symbol, current_tick_data[delayed.symbol]):
                    # Release with boost!
                    signal = {
                        'signal_id': delayed.signal_id,
                        'symbol': delayed.symbol,
                        'direction': delayed.direction,
                        'confidence': delayed.original_confidence + self.POST_SWEEP_BOOST,
                        'citadel_protected': True,
                        'citadel_boost': 'SWEEP_AVOIDED',
                        'delay_time': (current_time - delayed.delayed_at).seconds,
                        # Include all the critical trading parameters
                        'stop_loss': delayed.stop_loss,
                        'take_profit': delayed.take_profit,
                        'entry_price': delayed.entry_price,
                        'stop_pips': delayed.stop_pips,
                        'target_pips': delayed.target_pips,
                        'pattern_type': delayed.pattern_type,
                        'signal_type': delayed.signal_type
                    }
                    released_signals.append(signal)
                    self.delayed_signals.remove(delayed)
                    self.stats['sweeps_avoided'] += 1
                    
                    logger.info(f"🚀 CITADEL RELEASE: {delayed.symbol} {delayed.direction} after sweep completion (+{self.POST_SWEEP_BOOST}% confidence)")
        
        return released_signals
    
    def get_protection_stats(self) -> Dict:
        """Get CITADEL protection statistics"""
        return {
            'signals_delayed': self.stats['signals_delayed'],
            'sweeps_detected': self.stats['sweeps_detected'],
            'sweeps_avoided': self.stats['sweeps_avoided'],
            'post_sweep_entries': self.stats['post_sweep_entries'],
            'active_delays': len(self.delayed_signals),
            'active_sweeps': len(self.active_sweeps),
            'protection_rate': f"{(self.stats['sweeps_avoided'] / max(1, self.stats['sweeps_detected'])) * 100:.1f}%"
        }
    
    def get_market_status(self, symbol: str) -> Dict:
        """Get current CITADEL market analysis for a symbol"""
        status = {
            'symbol': symbol,
            'liquidity_zones': [],
            'active_sweep': None,
            'delayed_signals': 0,
            'recommendation': 'NORMAL'
        }
        
        # Add liquidity zones
        if symbol in self.liquidity_zones:
            for zone in self.liquidity_zones[symbol][:3]:  # Top 3 zones
                status['liquidity_zones'].append({
                    'level': zone.level,
                    'type': zone.zone_type,
                    'strength': zone.strength,
                    'sweep_probability': f"{zone.sweep_probability * 100:.0f}%"
                })
        
        # Check active sweep
        if symbol in self.active_sweeps:
            sweep = self.active_sweeps[symbol]
            status['active_sweep'] = {
                'direction': sweep['direction'],
                'zone': sweep['zone'].level,
                'duration': (datetime.now() - sweep['start_time']).seconds
            }
            status['recommendation'] = 'WAIT_FOR_REVERSAL'
        
        # Count delayed signals
        status['delayed_signals'] = len([d for d in self.delayed_signals if d.symbol == symbol])
        
        return status

# Example integration point
def integrate_with_elite_guard(citadel: CitadelProtection, raw_signal: Dict) -> Optional[Dict]:
    """
    Integration function to be called from Elite Guard
    """
    # Update market structure first
    # citadel.update_market_structure(signal['symbol'], recent_candles)
    
    # Protect the signal
    protected_signal = citadel.protect_signal(raw_signal)
    
    if protected_signal:
        # Add protection badge
        protected_signal['protected_by'] = 'CITADEL™'
        return protected_signal
    
    return None  # Signal delayed

if __name__ == "__main__":
    # Test CITADEL Protection
    citadel = CitadelProtection()
    
    # Simulate a signal near resistance
    test_signal = {
        'signal_id': 'TEST_001',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0845,  # Near resistance at 1.0850
        'confidence': 65
    }
    
    # Test liquidity zones
    test_candles = [
        {'high': 1.0850, 'low': 1.0840, 'close': 1.0845},
        {'high': 1.0851, 'low': 1.0841, 'close': 1.0846},
        {'high': 1.0849, 'low': 1.0839, 'close': 1.0844},
        # ... more candles
    ] * 20  # Simplified test data
    
    citadel.update_market_structure('EURUSD', test_candles)
    
    # Test protection
    result = citadel.protect_signal(test_signal)
    
    if result:
        print(f"✅ Signal passed: {result}")
    else:
        print(f"⏸️ Signal delayed for sweep protection")
    
    # Show stats
    print("\n📊 CITADEL Protection Stats:")
    for key, value in citadel.get_protection_stats().items():
        print(f"  {key}: {value}")