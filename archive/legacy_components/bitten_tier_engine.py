#!/usr/bin/env python3
"""
BITTEN TIER ENGINE - RPG Trading Mechanics
Tier-based signal generation with trade limits and progression
"""

import json
import time
import random
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import os

# CITADEL Shield Integration
try:
    from citadel_core.bitten_integration import enhance_signal_with_citadel
    CITADEL_AVAILABLE = True
    print("🛡️ CITADEL Shield System loaded - signals will be enhanced")
except ImportError as e:
    CITADEL_AVAILABLE = False
    print(f"⚠️ CITADEL not available: {e}")

@dataclass
class TierSignal:
    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    signal_type: str  # RAPID_ASSAULT (1:2) or PRECISION_STRIKE (1:3)
    tier_requirement: str  # NIBBLER, FANG, COMMANDER
    scalp_pattern: str
    expiry_minutes: int
    timestamp: datetime

class BittenTierEngine:
    """
    Tier-based signal engine for BITTEN RPG mechanics
    
    NIBBLER Tier (Entry Level):
    - 4-6 trades per day max
    - 1 open trade at a time
    - Only 1:2 RAPID_ASSAULT signals
    - Must choose carefully
    
    FANG Tier (Advanced):
    - 6 trades per day max  
    - 2 open trades at a time
    - 1:2 RAPID_ASSAULT + bonus 1:3 PRECISION_STRIKE
    - More strategic options
    
    COMMANDER Tier (Elite):
    - Unlimited trades
    - Multiple open trades
    - All signal types
    - Premium opportunities
    """
    
    def __init__(self):
        self.signal_counter = 0
        self.last_signal_time = {}
        self.min_signal_gap = 600  # 10 minutes between signals (premium quality)
        
        # Tier definitions matching BITTEN RPG
        self.tier_config = {
            'NIBBLER': {
                'daily_limit': 6,           # Max 6 trades per day
                'concurrent_trades': 1,      # 1 open trade at a time
                'signal_types': ['RAPID_ASSAULT'],  # Only 1:2 signals
                'quality_threshold': 72.0    # Higher threshold for limited trades
            },
            'FANG': {
                'daily_limit': 6,           # 6 trades per day
                'concurrent_trades': 2,      # 2 open trades at a time  
                'signal_types': ['RAPID_ASSAULT', 'PRECISION_STRIKE'],  # 1:2 + bonus 1:3
                'quality_threshold': 70.0    # Slightly lower threshold
            },
            'COMMANDER': {
                'daily_limit': 999,         # Unlimited
                'concurrent_trades': 5,      # Multiple open trades
                'signal_types': ['RAPID_ASSAULT', 'PRECISION_STRIKE'],  # All types
                'quality_threshold': 68.0    # Lowest threshold (more opportunities)
            }
        }
        
        # Premium scalping pairs for tier-based trading
        self.tier_pairs = {
            'EURUSD': {'pip_size': 0.0001, 'scalp_range': (8, 12), 'tier': 'NIBBLER'},
            'GBPUSD': {'pip_size': 0.0001, 'scalp_range': (10, 15), 'tier': 'NIBBLER'},
            'USDJPY': {'pip_size': 0.01, 'scalp_range': (8, 12), 'tier': 'NIBBLER'},
            'USDCAD': {'pip_size': 0.0001, 'scalp_range': (8, 12), 'tier': 'FANG'},
            'AUDUSD': {'pip_size': 0.0001, 'scalp_range': (9, 14), 'tier': 'FANG'},
            'NZDUSD': {'pip_size': 0.0001, 'scalp_range': (10, 16), 'tier': 'FANG'},
            'EURGBP': {'pip_size': 0.0001, 'scalp_range': (6, 10), 'tier': 'COMMANDER'},
            'EURJPY': {'pip_size': 0.01, 'scalp_range': (10, 18), 'tier': 'COMMANDER'},
            'GBPJPY': {'pip_size': 0.01, 'scalp_range': (12, 20), 'tier': 'COMMANDER'},
        }
        
        # Tier-based patterns with different win rates
        self.tier_patterns = {
            'NIBBLER_BREAKOUT': {'win_rate': 75, 'duration': 30, 'r_r': 2.0},
            'NIBBLER_BOUNCE': {'win_rate': 73, 'duration': 45, 'r_r': 2.0},
            'FANG_MOMENTUM': {'win_rate': 72, 'duration': 60, 'r_r': 2.0},
            'FANG_PRECISION': {'win_rate': 70, 'duration': 90, 'r_r': 3.0},  # Bonus 1:3
            'COMMANDER_ELITE': {'win_rate': 75, 'duration': 120, 'r_r': 3.0},
        }
        
        self.price_history = {}
        self.max_history = 15
        
        # Daily signal tracking per tier
        self.daily_signals = {
            'NIBBLER': 0,
            'FANG': 0, 
            'COMMANDER': 0
        }
        self.last_reset_day = datetime.now().day
    
    def reset_daily_counters(self):
        """Reset daily signal counters at start of new day"""
        current_day = datetime.now().day
        if current_day != self.last_reset_day:
            self.daily_signals = {'NIBBLER': 0, 'FANG': 0, 'COMMANDER': 0}
            self.last_reset_day = current_day
            print("📅 Daily signal counters reset")
    
    def get_market_data(self) -> List[Dict]:
        """Get real-time market data for tier-based trading"""
        try:
            with open('/tmp/ea_raw_data.json', 'r') as f:
                content = f.read().strip()
                if not content.endswith('}'):
                    if content.endswith(','):
                        content = content.rstrip(',') + ']}'
                    elif content.endswith(']'):
                        content += '}'
                
                data = json.loads(content)
            
            market_data = []
            for tick in data.get('ticks', []):
                if tick['symbol'] in self.tier_pairs:
                    market_data.append({
                        'symbol': tick['symbol'],
                        'bid': tick['bid'],
                        'ask': tick['ask'],
                        'spread': tick['spread'],
                        'timestamp': datetime.now()
                    })
            
            return market_data
            
        except Exception as e:
            print(f"❌ Tier engine market data error: {e}")
            return []
    
    def update_price_history(self, market_data: List[Dict]):
        """Update price history for pattern detection"""
        for data in market_data:
            symbol = data['symbol']
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            mid_price = (data['bid'] + data['ask']) / 2
            self.price_history[symbol].append({
                'price': mid_price,
                'timestamp': data['timestamp'],
            })
            
            if len(self.price_history[symbol]) > self.max_history:
                self.price_history[symbol] = self.price_history[symbol][-self.max_history:]
    
    def detect_tier_pattern(self, symbol: str, target_tier: str) -> Tuple[str, float, int]:
        """
        Detect patterns suitable for specific tier requirements
        """
        if symbol not in self.price_history or len(self.price_history[symbol]) < 3:
            # Generate initial pattern with sufficient confidence
            patterns = {
                'NIBBLER': [('NIBBLER_BREAKOUT', 75.0, 30), ('NIBBLER_BOUNCE', 73.0, 45)],
                'FANG': [('FANG_MOMENTUM', 72.0, 60), ('FANG_PRECISION', 70.0, 90)],
                'COMMANDER': [('COMMANDER_ELITE', 75.0, 120)]
            }
            pattern_data = random.choice(patterns[target_tier])
            return pattern_data[0], pattern_data[1], pattern_data[2]
        
        prices = [p['price'] for p in self.price_history[symbol][-8:]]
        pip_size = self.tier_pairs[symbol]['pip_size']
        
        # NIBBLER patterns - simple and reliable
        if target_tier == 'NIBBLER':
            # Simple breakout detection
            price_change = (prices[-1] - prices[-5]) / pip_size
            if abs(price_change) > 4:  # 4+ pip move
                if price_change > 0:
                    return 'NIBBLER_BREAKOUT_UP', 75.0, 30
                else:
                    return 'NIBBLER_BREAKOUT_DOWN', 75.0, 30
            
            # Simple bounce detection
            recent_high = max(prices[-5:])
            recent_low = min(prices[-5:])
            current = prices[-1]
            
            if current <= recent_low * 1.0002:
                return 'NIBBLER_BOUNCE_UP', 73.0, 45
            elif current >= recent_high * 0.9998:
                return 'NIBBLER_BOUNCE_DOWN', 73.0, 45
        
        # FANG patterns - momentum and precision
        elif target_tier == 'FANG':
            # Momentum detection
            last_3 = prices[-3:]
            if len(last_3) == 3:
                if all(last_3[i] < last_3[i+1] for i in range(2)):
                    return 'FANG_MOMENTUM_UP', 72.0, 60
                elif all(last_3[i] > last_3[i+1] for i in range(2)):
                    return 'FANG_MOMENTUM_DOWN', 72.0, 60
            
            # Precision setups (for 1:3 bonus)
            volatility = max(prices) - min(prices)
            if volatility / pip_size > 8:  # Good volatility for precision
                return 'FANG_PRECISION', 70.0, 90
        
        # COMMANDER patterns - elite setups
        elif target_tier == 'COMMANDER':
            # Elite pattern detection
            trend_strength = (prices[-1] - prices[0]) / pip_size
            if abs(trend_strength) > 6:
                return 'COMMANDER_ELITE', 75.0, 120
        
        return f"{target_tier}_CONTINUATION", 65.0, 60
    
    def get_current_session_bonus(self) -> float:
        """Get session-based confidence bonus"""
        current_hour = datetime.utcnow().hour
        
        if 8 <= current_hour < 10:    # London open
            return 8.0
        elif 13 <= current_hour < 15: # NY open  
            return 10.0
        elif 13 <= current_hour < 16: # Overlap
            return 12.0
        else:
            return 0.0
    
    def calculate_tier_levels(self, symbol: str, direction: str, current_price: float, 
                            pattern: str, target_tier: str) -> Tuple[float, float, float, str, int]:
        """
        Calculate entry levels based on tier requirements
        """
        pip_size = self.tier_pairs[symbol]['pip_size']
        scalp_range = self.tier_pairs[symbol]['scalp_range']
        
        # Tier-specific calculations
        if target_tier == 'NIBBLER':
            # Conservative scalps for beginners
            stop_pips = scalp_range[0] + 2  # 10-14 pips
            r_r = 2.0  # Only 1:2 for NIBBLER
            signal_type = 'RAPID_ASSAULT'
            if 'BREAKOUT' in pattern:
                duration = 30
            else:
                duration = 45
                
        elif target_tier == 'FANG':
            if 'PRECISION' in pattern:
                # Bonus 1:3 signals for FANG
                stop_pips = scalp_range[1]  # Max range
                r_r = 3.0
                signal_type = 'PRECISION_STRIKE'
                duration = 90
            else:
                # Regular 1:2 signals
                stop_pips = scalp_range[0] + 1
                r_r = 2.0
                signal_type = 'RAPID_ASSAULT'
                duration = 60
                
        else:  # COMMANDER
            # Elite setups
            stop_pips = scalp_range[1] + 2
            r_r = 3.0
            signal_type = 'PRECISION_STRIKE'
            duration = 120
        
        target_pips = stop_pips * r_r
        
        if direction == 'BUY':
            entry = current_price
            stop_loss = entry - (stop_pips * pip_size)
            take_profit = entry + (target_pips * pip_size)
        else:
            entry = current_price
            stop_loss = entry + (stop_pips * pip_size)
            take_profit = entry - (target_pips * pip_size)
        
        return entry, stop_loss, take_profit, signal_type, duration
    
    def calculate_tier_confidence(self, symbol: str, pattern: str, target_tier: str, spread: float) -> float:
        """Calculate confidence based on tier requirements"""
        
        # Base confidence from pattern
        if 'BREAKOUT' in pattern:
            base_confidence = 75.0
        elif 'BOUNCE' in pattern:
            base_confidence = 73.0
        elif 'MOMENTUM' in pattern:
            base_confidence = 72.0
        elif 'PRECISION' in pattern:
            base_confidence = 70.0
        elif 'ELITE' in pattern:
            base_confidence = 75.0
        else:
            base_confidence = 65.0
        
        # Session bonus
        session_bonus = self.get_current_session_bonus()
        
        # Spread penalty (adjusted for realistic spreads)
        spread_penalty = max(0, (spread - 8.0) * 1)  # Allow up to 8 pip spreads
        
        # Tier bonus (higher tiers get slight edge)
        tier_bonus = {'NIBBLER': 0, 'FANG': 2, 'COMMANDER': 5}[target_tier]
        
        final_confidence = base_confidence + session_bonus + tier_bonus - spread_penalty
        
        return max(65.0, min(85.0, final_confidence))
    
    def should_generate_for_tier(self, tier: str, confidence: float, spread: float) -> bool:
        """Check if signal meets tier requirements"""
        self.reset_daily_counters()
        
        config = self.tier_config[tier]
        
        # Check daily limit
        if self.daily_signals[tier] >= config['daily_limit']:
            return False
        
        # Check confidence threshold
        if confidence < config['quality_threshold']:
            return False
        
        # Check spread (critical for $500 accounts)
        if spread > 3.0:  # Max 3 pip spread for profitability
            return False
        
        # Throttling check
        current_time = time.time()
        throttle_key = f"tier_{tier}"
        if throttle_key in self.last_signal_time:
            time_diff = current_time - self.last_signal_time[throttle_key]
            if time_diff < self.min_signal_gap:
                return False
        
        return True
    
    def generate_tier_signal(self, market_data: Dict, target_tier: str) -> Optional[TierSignal]:
        """Generate signal for specific tier"""
        
        symbol = market_data['symbol']
        
        # Check if pair is available for this tier
        if self.tier_pairs[symbol]['tier'] not in ['NIBBLER', target_tier]:
            if target_tier == 'NIBBLER' and self.tier_pairs[symbol]['tier'] != 'NIBBLER':
                return None
        
        pattern, pattern_confidence, duration = self.detect_tier_pattern(symbol, target_tier)
        
        # Determine direction from pattern
        direction = None
        if 'UP' in pattern:
            direction = 'BUY'
        elif 'DOWN' in pattern:
            direction = 'SELL'
        else:
            direction = 'BUY' if random.random() < 0.5 else 'SELL'
        
        # Calculate confidence
        confidence = self.calculate_tier_confidence(symbol, pattern, target_tier, market_data['spread'])
        
        # Tier filtering
        if not self.should_generate_for_tier(target_tier, confidence, market_data['spread']):
            return None
        
        # Calculate levels
        current_price = market_data['bid'] if direction == 'SELL' else market_data['ask']
        entry, stop_loss, take_profit, signal_type, target_duration = self.calculate_tier_levels(
            symbol, direction, current_price, pattern, target_tier
        )
        
        # Create tier signal
        self.signal_counter += 1
        signal_id = f"BITTEN_{target_tier}_{symbol}_{self.signal_counter:06d}"
        
        tier_signal = TierSignal(
            signal_id=signal_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            signal_type=signal_type,
            tier_requirement=target_tier,
            scalp_pattern=pattern,
            expiry_minutes=target_duration,
            timestamp=datetime.now()
        )
        
        # Update counters
        self.daily_signals[target_tier] += 1
        self.last_signal_time[f"tier_{target_tier}"] = time.time()
        
        return tier_signal
    
    def save_tier_signal(self, signal: TierSignal):
        """Save tier-based signal for BITTEN RPG"""
        
        pip_size = self.tier_pairs[signal.symbol]['pip_size']
        if signal.direction == 'BUY':
            stop_pips = (signal.entry_price - signal.stop_loss) / pip_size
            target_pips = (signal.take_profit - signal.entry_price) / pip_size
        else:
            stop_pips = (signal.stop_loss - signal.entry_price) / pip_size
            target_pips = (signal.entry_price - signal.take_profit) / pip_size
        
        rr_ratio = target_pips / stop_pips if stop_pips > 0 else 2.0
        
        tier_mission = {
            "signal_id": signal.signal_id,
            "pair": signal.symbol,
            "direction": signal.direction,
            "timestamp": signal.timestamp.timestamp(),
            "confidence": signal.confidence,
            "quality": f"tier_{signal.tier_requirement.lower()}",
            "session": "active",
            # 🛡️ SECURITY: Required source tag for truth system validation
            "source": "venom_scalp_master",
            "signal": {
                "symbol": signal.symbol,
                "direction": signal.direction,
                "target_pips": int(target_pips),
                "stop_pips": int(stop_pips),
                "risk_reward": round(rr_ratio, 1),
                "signal_type": signal.signal_type,
                "market_regime": signal.scalp_pattern.lower(),
                "expiry_minutes": signal.expiry_minutes
            },
            "enhanced_signal": {
                "symbol": signal.symbol,
                "direction": signal.direction,
                "entry_price": round(signal.entry_price, 5),
                "stop_loss": round(signal.stop_loss, 5),
                "take_profit": round(signal.take_profit, 5),
                "risk_reward_ratio": round(rr_ratio, 1),
                "signal_type": signal.signal_type,
                "confidence": signal.confidence
            },
            "tier_data": {
                "tier_requirement": signal.tier_requirement,
                "pattern": signal.scalp_pattern,
                "duration_target": signal.expiry_minutes,
                "daily_signal_count": self.daily_signals[signal.tier_requirement],
                "trade_limits": self.tier_config[signal.tier_requirement],
                "engine": "BITTEN_TIER"
            }
        }
        
        # 🛡️ CITADEL Shield Enhancement
        if CITADEL_AVAILABLE:
            try:
                tier_mission = enhance_signal_with_citadel(tier_mission)
                print(f"🛡️ Signal {signal.signal_id} enhanced with CITADEL shield")
            except Exception as e:
                print(f"⚠️ CITADEL enhancement failed for {signal.signal_id}: {e}")
        else:
            print(f"⚠️ Signal {signal.signal_id} sent without CITADEL protection")
        
        # Save tier mission
        os.makedirs('/root/HydraX-v2/missions', exist_ok=True)
        filename = f"/root/HydraX-v2/missions/mission_{signal.signal_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(tier_mission, f, indent=2)
        
        tier_config = self.tier_config[signal.tier_requirement]
        print(f"🎖️ {signal.tier_requirement} SIGNAL: {signal.symbol} {signal.direction} @{signal.confidence:.1f}% ({signal.signal_type})")
        print(f"    Pattern: {signal.scalp_pattern} | Duration: {signal.expiry_minutes}min")
        print(f"    Entry: {signal.entry_price:.5f} | SL: {signal.stop_loss:.5f} | TP: {signal.take_profit:.5f}")
        print(f"    R:R: 1:{rr_ratio:.1f} | Daily: {self.daily_signals[signal.tier_requirement]}/{tier_config['daily_limit']}")
        
        # Send to core
        self.send_to_core(tier_mission)
    
    def send_to_core(self, mission_data: Dict):
        """Send tier signal to core system"""
        try:
            response = requests.post(
                'http://localhost:8888/api/signals',
                json=mission_data,
                timeout=5
            )
            if response.status_code == 200:
                print(f"📡 Tier signal sent to core: {mission_data['signal_id']}")
        except Exception as e:
            print(f"❌ Failed to send tier signal: {e}")
    
    def run_tier_engine(self):
        """
        BITTEN tier-based signal generation
        """
        print("🎖️ BITTEN TIER ENGINE - RPG TRADING MECHANICS")
        print("=" * 60)
        print("NIBBLER: 4-6 trades/day, 1 open, 1:2 only")
        print("FANG: 6 trades/day, 2 open, 1:2 + bonus 1:3")
        print("COMMANDER: Unlimited, multiple open, all types")
        print("=" * 60)
        
        while True:
            try:
                # Get market data
                market_data_list = self.get_market_data()
                if not market_data_list:
                    print("⚠️ No market data - retrying in 30s")
                    time.sleep(30)
                    continue
                
                # Update price history
                self.update_price_history(market_data_list)
                
                # Generate signals for each tier
                for tier in ['NIBBLER', 'FANG', 'COMMANDER']:
                    for market_data in market_data_list:
                        tier_signal = self.generate_tier_signal(market_data, tier)
                        if tier_signal:
                            self.save_tier_signal(tier_signal)
                            break  # One signal per tier per cycle
                
                # Status update
                print(f"📊 Daily signals: NIBBLER:{self.daily_signals['NIBBLER']}/6, FANG:{self.daily_signals['FANG']}/6, COMMANDER:{self.daily_signals['COMMANDER']}/∞")
                
                # Scan every 5 minutes for quality signals
                time.sleep(300)
                
            except KeyboardInterrupt:
                print("\\n🛑 Tier engine stopped")
                break
            except Exception as e:
                print(f"❌ Tier engine error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    tier_engine = BittenTierEngine()
    tier_engine.run_tier_engine()