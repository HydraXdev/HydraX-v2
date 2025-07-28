"""
Bitten Player Types Engine - 4 Distinct Trading Personalities
Each player type has unique characteristics for signal generation, risk management, and trading style
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class PlayerType(Enum):
    GRINDER = "GRINDER"
    HUNTER = "HUNTER"
    SNIPER = "SNIPER"
    WHALE = "WHALE"

@dataclass
class TradeSignal:
    """Trade signal with all necessary information"""
    timestamp: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    direction: str  # 'BUY' or 'SELL'
    pip_target: int
    risk_reward_ratio: float
    player_type: PlayerType
    confidence: float
    trade_duration_minutes: int

class PlayerProfile:
    """Base class for all player types"""
    
    def __init__(self, player_type: PlayerType):
        self.player_type = player_type
        self.signals_generated = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
    def get_win_rate(self) -> float:
        total_trades = self.winning_trades + self.losing_trades
        return (self.winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    def generate_trade_outcome(self, tcs_accuracy: float) -> bool:
        """Determine if trade is winner based on TCS accuracy"""
        return random.random() < (tcs_accuracy / 100)

class GrinderProfile(PlayerProfile):
    """
    GRINDER - High frequency, lower R:R, quick trades
    - TCS Accuracy: 75-85%
    - Pip Targets: 5-15 pips
    - R:R Ratio: 1:1 to 1:1.5
    - Trade Duration: 5-15 minutes
    - Signals/Day: 20-30
    """
    
    def __init__(self):
        super().__init__(PlayerType.GRINDER)
        self.tcs_range = (75, 85)
        self.pip_range = (5, 15)
        self.rr_range = (1.0, 1.5)
        self.duration_range = (5, 15)
        self.daily_signal_range = (20, 30)
        
    def generate_signal(self, current_price: float, timestamp: datetime) -> TradeSignal:
        # Randomize within defined ranges
        tcs_accuracy = random.uniform(*self.tcs_range)
        pip_target = random.randint(*self.pip_range)
        risk_reward = round(random.uniform(*self.rr_range), 2)
        duration = random.randint(*self.duration_range)
        
        # Determine direction with slight trend following
        direction = random.choice(['BUY', 'SELL'])
        
        # Calculate levels based on direction
        pip_value = 0.0001  # For forex pairs
        if direction == 'BUY':
            stop_loss = current_price - (pip_target * pip_value)
            take_profit = current_price + (pip_target * risk_reward * pip_value)
        else:
            stop_loss = current_price + (pip_target * pip_value)
            take_profit = current_price - (pip_target * risk_reward * pip_value)
        
        # Add slight variance to make each signal unique
        variance = random.uniform(0.9, 1.1)
        confidence = min(tcs_accuracy * variance / 100, 0.95)
        
        self.signals_generated += 1
        
        return TradeSignal(
            timestamp=timestamp,
            entry_price=current_price,
            stop_loss=round(stop_loss, 5),
            take_profit=round(take_profit, 5),
            direction=direction,
            pip_target=pip_target,
            risk_reward_ratio=risk_reward,
            player_type=self.player_type,
            confidence=confidence,
            trade_duration_minutes=duration
        )

class HunterProfile(PlayerProfile):
    """
    HUNTER - Medium frequency, balanced R:R
    - TCS Accuracy: 70-80%
    - Pip Targets: 15-30 pips
    - R:R Ratio: 1:1.5 to 1:2.5
    - Trade Duration: 15-30 minutes
    - Signals/Day: 15-20
    """
    
    def __init__(self):
        super().__init__(PlayerType.HUNTER)
        self.tcs_range = (70, 80)
        self.pip_range = (15, 30)
        self.rr_range = (1.5, 2.5)
        self.duration_range = (15, 30)
        self.daily_signal_range = (15, 20)
        
    def generate_signal(self, current_price: float, timestamp: datetime) -> TradeSignal:
        tcs_accuracy = random.uniform(*self.tcs_range)
        pip_target = random.randint(*self.pip_range)
        risk_reward = round(random.uniform(*self.rr_range), 2)
        duration = random.randint(*self.duration_range)
        
        # Hunters prefer trend continuation
        market_bias = random.random()
        direction = 'BUY' if market_bias > 0.45 else 'SELL'
        
        pip_value = 0.0001
        if direction == 'BUY':
            stop_loss = current_price - (pip_target * pip_value)
            take_profit = current_price + (pip_target * risk_reward * pip_value)
        else:
            stop_loss = current_price + (pip_target * pip_value)
            take_profit = current_price - (pip_target * risk_reward * pip_value)
        
        # Hunters have moderate confidence
        confidence = min(tcs_accuracy * random.uniform(0.85, 1.05) / 100, 0.90)
        
        self.signals_generated += 1
        
        return TradeSignal(
            timestamp=timestamp,
            entry_price=current_price,
            stop_loss=round(stop_loss, 5),
            take_profit=round(take_profit, 5),
            direction=direction,
            pip_target=pip_target,
            risk_reward_ratio=risk_reward,
            player_type=self.player_type,
            confidence=confidence,
            trade_duration_minutes=duration
        )

class SniperProfile(PlayerProfile):
    """
    SNIPER - Lower frequency, high R:R
    - TCS Accuracy: 72-82%
    - Pip Targets: 25-50 pips
    - R:R Ratio: 1:2.5 to 1:4
    - Trade Duration: 30-60 minutes
    - Signals/Day: 8-12
    """
    
    def __init__(self):
        super().__init__(PlayerType.SNIPER)
        self.tcs_range = (72, 82)
        self.pip_range = (25, 50)
        self.rr_range = (2.5, 4.0)
        self.duration_range = (30, 60)
        self.daily_signal_range = (8, 12)
        
    def generate_signal(self, current_price: float, timestamp: datetime) -> TradeSignal:
        tcs_accuracy = random.uniform(*self.tcs_range)
        pip_target = random.randint(*self.pip_range)
        risk_reward = round(random.uniform(*self.rr_range), 2)
        duration = random.randint(*self.duration_range)
        
        # Snipers wait for high-probability setups
        setup_quality = random.random()
        if setup_quality < 0.3:  # Skip low quality setups
            return None
            
        direction = 'BUY' if setup_quality > 0.5 else 'SELL'
        
        pip_value = 0.0001
        if direction == 'BUY':
            stop_loss = current_price - (pip_target * pip_value)
            take_profit = current_price + (pip_target * risk_reward * pip_value)
        else:
            stop_loss = current_price + (pip_target * pip_value)
            take_profit = current_price - (pip_target * risk_reward * pip_value)
        
        # Snipers have high confidence in their shots
        confidence = min(tcs_accuracy * random.uniform(0.95, 1.1) / 100, 0.95)
        
        self.signals_generated += 1
        
        return TradeSignal(
            timestamp=timestamp,
            entry_price=current_price,
            stop_loss=round(stop_loss, 5),
            take_profit=round(take_profit, 5),
            direction=direction,
            pip_target=pip_target,
            risk_reward_ratio=risk_reward,
            player_type=self.player_type,
            confidence=confidence,
            trade_duration_minutes=duration
        )

class WhaleProfile(PlayerProfile):
    """
    WHALE - Very selective, highest R:R
    - TCS Accuracy: 70-78%
    - Pip Targets: 40-100 pips
    - R:R Ratio: 1:3 to 1:5
    - Trade Duration: 60-120 minutes
    - Signals/Day: 3-5
    """
    
    def __init__(self):
        super().__init__(PlayerType.WHALE)
        self.tcs_range = (70, 78)
        self.pip_range = (40, 100)
        self.rr_range = (3.0, 5.0)
        self.duration_range = (60, 120)
        self.daily_signal_range = (3, 5)
        
    def generate_signal(self, current_price: float, timestamp: datetime) -> TradeSignal:
        tcs_accuracy = random.uniform(*self.tcs_range)
        pip_target = random.randint(*self.pip_range)
        risk_reward = round(random.uniform(*self.rr_range), 2)
        duration = random.randint(*self.duration_range)
        
        # Whales only trade major moves
        market_strength = random.random()
        if market_strength < 0.7:  # Skip unless strong setup
            return None
            
        # Whales follow institutional flow
        direction = 'BUY' if market_strength > 0.85 else 'SELL'
        
        pip_value = 0.0001
        if direction == 'BUY':
            stop_loss = current_price - (pip_target * pip_value)
            take_profit = current_price + (pip_target * risk_reward * pip_value)
        else:
            stop_loss = current_price + (pip_target * pip_value)
            take_profit = current_price - (pip_target * risk_reward * pip_value)
        
        # Whales have measured confidence
        confidence = min(tcs_accuracy * random.uniform(0.9, 1.05) / 100, 0.88)
        
        self.signals_generated += 1
        
        return TradeSignal(
            timestamp=timestamp,
            entry_price=current_price,
            stop_loss=round(stop_loss, 5),
            take_profit=round(take_profit, 5),
            direction=direction,
            pip_target=pip_target,
            risk_reward_ratio=risk_reward,
            player_type=self.player_type,
            confidence=confidence,
            trade_duration_minutes=duration
        )

class BittenPlayerTypesEngine:
    """Main engine managing all player types and signal generation"""
    
    def __init__(self):
        self.profiles = {
            PlayerType.GRINDER: GrinderProfile(),
            PlayerType.HUNTER: HunterProfile(),
            PlayerType.SNIPER: SniperProfile(),
            PlayerType.WHALE: WhaleProfile()
        }
        self.active_signals: List[TradeSignal] = []
        self.completed_trades: List[Dict] = []
        self.current_time = datetime.now()
        
    def get_player_profile(self, player_type: PlayerType) -> PlayerProfile:
        """Get specific player profile"""
        return self.profiles[player_type]
    
    def generate_daily_signals(self, base_price: float = 1.1000) -> Dict[PlayerType, List[TradeSignal]]:
        """Generate all signals for a trading day"""
        daily_signals = {player_type: [] for player_type in PlayerType}
        
        # Generate signals for each player type
        for player_type, profile in self.profiles.items():
            # Determine number of signals for the day
            if player_type == PlayerType.GRINDER:
                num_signals = random.randint(20, 30)
            elif player_type == PlayerType.HUNTER:
                num_signals = random.randint(15, 20)
            elif player_type == PlayerType.SNIPER:
                num_signals = random.randint(8, 12)
            else:  # WHALE
                num_signals = random.randint(3, 5)
            
            # Distribute signals throughout the day
            signal_times = self._generate_signal_times(num_signals)
            
            for signal_time in signal_times:
                # Add price movement simulation
                price_movement = random.uniform(-0.0050, 0.0050)
                current_price = base_price + price_movement
                
                signal = profile.generate_signal(current_price, signal_time)
                if signal:  # Some profiles may skip signals
                    daily_signals[player_type].append(signal)
                    
        return daily_signals
    
    def _generate_signal_times(self, num_signals: int) -> List[datetime]:
        """Generate random times throughout trading day"""
        start_hour = 8
        end_hour = 20
        trading_minutes = (end_hour - start_hour) * 60
        
        # Generate random minutes
        minutes = sorted([random.randint(0, trading_minutes) for _ in range(num_signals)])
        
        # Convert to datetime objects
        base_date = datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
        return [base_date + timedelta(minutes=m) for m in minutes]
    
    def simulate_trade_outcome(self, signal: TradeSignal) -> Dict:
        """Simulate the outcome of a trade"""
        profile = self.profiles[signal.player_type]
        
        # Get TCS accuracy for this trade
        tcs_accuracy = random.uniform(*profile.tcs_range)
        is_winner = profile.generate_trade_outcome(tcs_accuracy)
        
        # Calculate P&L
        if is_winner:
            pips_gained = signal.pip_target * signal.risk_reward_ratio
            profile.winning_trades += 1
        else:
            pips_gained = -signal.pip_target
            profile.losing_trades += 1
            
        return {
            'signal': signal,
            'outcome': 'WIN' if is_winner else 'LOSS',
            'pips': pips_gained,
            'tcs_accuracy': tcs_accuracy,
            'actual_duration': signal.trade_duration_minutes + random.randint(-5, 5)
        }
    
    def get_performance_stats(self) -> Dict[PlayerType, Dict]:
        """Get performance statistics for all player types"""
        stats = {}
        
        for player_type, profile in self.profiles.items():
            total_trades = profile.winning_trades + profile.losing_trades
            win_rate = profile.get_win_rate()
            
            stats[player_type] = {
                'total_signals': profile.signals_generated,
                'total_trades': total_trades,
                'winning_trades': profile.winning_trades,
                'losing_trades': profile.losing_trades,
                'win_rate': f"{win_rate:.1f}%",
                'characteristics': {
                    'tcs_range': profile.tcs_range,
                    'pip_range': profile.pip_range,
                    'rr_range': profile.rr_range,
                    'duration_range': profile.duration_range,
                    'daily_signals': profile.daily_signal_range
                }
            }
            
        return stats
    
    def prevent_signal_overlap(self, new_signal: TradeSignal, existing_signals: List[TradeSignal], 
                             min_price_gap: float = 0.0010) -> bool:
        """Ensure signals don't overlap in price/time"""
        for existing in existing_signals:
            # Check time overlap
            time_diff = abs((new_signal.timestamp - existing.timestamp).total_seconds() / 60)
            if time_diff < 5:  # Less than 5 minutes apart
                return False
                
            # Check price overlap
            price_diff = abs(new_signal.entry_price - existing.entry_price)
            if price_diff < min_price_gap:
                return False
                
        return True

# Example usage and testing
if __name__ == "__main__":
    # Initialize the engine
    engine = BittenPlayerTypesEngine()
    
    # Generate daily signals
    print("=== BITTEN PLAYER TYPES ENGINE ===\n")
    daily_signals = engine.generate_daily_signals()
    
    # Display signals by player type
    for player_type, signals in daily_signals.items():
        print(f"\n{player_type.value} SIGNALS ({len(signals)} total):")
        print("-" * 50)
        
        for i, signal in enumerate(signals[:3]):  # Show first 3 signals
            print(f"Signal {i+1}:")
            print(f"  Time: {signal.timestamp.strftime('%H:%M')}")
            print(f"  Direction: {signal.direction}")
            print(f"  Entry: {signal.entry_price:.5f}")
            print(f"  SL: {signal.stop_loss:.5f} | TP: {signal.take_profit:.5f}")
            print(f"  Pips: {signal.pip_target} | R:R: 1:{signal.risk_reward_ratio}")
            print(f"  Duration: {signal.trade_duration_minutes} min")
            print(f"  Confidence: {signal.confidence:.2%}\n")
    
    # Simulate some trades
    print("\n=== SIMULATING TRADES ===\n")
    for player_type in PlayerType:
        signals = daily_signals[player_type]
        if signals:
            # Simulate first few trades
            for signal in signals[:5]:
                outcome = engine.simulate_trade_outcome(signal)
                print(f"{player_type.value}: {outcome['outcome']} - {outcome['pips']:.1f} pips")
    
    # Display performance stats
    print("\n=== PERFORMANCE STATISTICS ===\n")
    stats = engine.get_performance_stats()
    
    for player_type, stat in stats.items():
        print(f"{player_type.value}:")
        print(f"  Win Rate: {stat['win_rate']}")
        print(f"  TCS Range: {stat['characteristics']['tcs_range']}")
        print(f"  Pip Targets: {stat['characteristics']['pip_range']}")
        print(f"  R:R Range: {stat['characteristics']['rr_range']}")
        print(f"  Daily Signals: {stat['characteristics']['daily_signals']}")
        print()