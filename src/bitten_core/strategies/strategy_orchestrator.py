# strategy_orchestrator.py
# BITTEN Strategy Orchestrator - The Master Controller

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from .strategy_base import MarketData, TechnicalIndicators, TradingSignal, SignalType
from .london_breakout import LondonBreakoutStrategy
from .support_resistance import SupportResistanceStrategy
from .momentum_continuation import MomentumContinuationStrategy
from .mean_reversion import MeanReversionStrategy
from .market_analyzer import MarketAnalyzer
from .strategy_validator import StrategyValidator
from ..tactical_strategies import TacticalStrategy, tactical_strategy_manager

logger = logging.getLogger(__name__)

class StrategyOrchestrator:
    """
    MASTER STRATEGY ORCHESTRATION ENGINE
    
    The brain that coordinates all trading strategies.
    Decides WHAT to trade, WHEN to trade, and HOW MUCH to risk.
    """
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        
        # Initialize strategies for each symbol
        self.strategies = {}
        self.market_analyzers = {}
        
        for symbol in symbols:
            self.strategies[symbol] = {
                'london_breakout': LondonBreakoutStrategy(symbol),
                'support_resistance': SupportResistanceStrategy(symbol),
                'momentum_continuation': MomentumContinuationStrategy(symbol),
                'mean_reversion': MeanReversionStrategy(symbol)}
            self.market_analyzers[symbol] = MarketAnalyzer(symbol)
        
        # Global validator
        self.validator = StrategyValidator()
        
        # Tactical manager for NIBBLER gamification
        self.tactical_manager = tactical_strategy_manager
        
        # Signal tracking
        self.recent_signals = defaultdict(list)  # Per symbol
        self.signal_history = []
        self.max_signals_per_symbol = 3
        self.signal_cooldown_minutes = 15
        
        # Performance tracking
        self.strategy_stats = defaultdict(lambda: {
            'total': 0, 'wins': 0, 'losses': 0, 'win_rate': 0.0
        })
        
    def process_market_update(self, symbol: str, market_data: MarketData,
                            indicators: TechnicalIndicators, user_id: str = None) -> Optional[TradingSignal]:
        """
        MAIN PROCESSING ENGINE
        
        Analyzes market data and generates high-probability signals.
        """
        
        if symbol not in self.symbols:
            logger.error(f"Symbol {symbol} not configured")
            return None
        
        # Update market analyzer
        self.market_analyzers[symbol].update_market_data(market_data)
        
        # Check signal cooldown
        if self._is_in_cooldown(symbol):
            return None
        
        # Get market structure
        market_structure = self.market_analyzers[symbol].analyze_market_structure()
        
        # Select optimal strategy
        optimal_strategy = self.market_analyzers[symbol].get_optimal_strategy(market_structure)
        
        logger.info(f"{symbol} - Market: {market_structure.trend} "
                   f"(strength: {market_structure.strength:.1f}), "
                   f"Selected strategy: {optimal_strategy}")
        
        # Run the selected strategy
        strategy = self.strategies[symbol][optimal_strategy]
        signal = strategy.analyze_setup([market_data], indicators)
        
        if not signal:
            # Try backup strategies if primary fails
            signal = self._try_backup_strategies(symbol, market_data, indicators, optimal_strategy)
        
        if signal:
            # Validate the signal
            market_conditions = self.market_analyzers[symbol].get_market_conditions()
            validation = self.validator.validate_signal(
                signal, 
                self.recent_signals[symbol],
                market_conditions
            )
            
            if not validation.is_valid:
                logger.warning(f"Signal killed: {validation.kill_switches}")
                return None
            
            # Apply confidence adjustment
            signal.tcs_score = max(0, min(100, signal.tcs_score + validation.confidence_boost))
            
            # Add validation feedback
            signal.confidence_factors.extend(validation.enhanced_factors)
            signal.warning_factors.extend(validation.risk_warnings)
            
            # Apply tactical strategy filtering (NIBBLER gamification)
            if user_id and hasattr(self, 'tactical_manager'):
                signal = self.tactical_manager.filter_signal_for_user(user_id, signal)
                if not signal:
                    logger.info(f"Signal filtered out by tactical strategy for user {user_id}")
                    return None
            
            # Final TCS check (NIBBLER uses tactical strategy requirements)
            min_tcs = 60 if not user_id else 60  # NIBBLER threshold
            if signal.tcs_score >= min_tcs:
                self._record_signal(symbol, signal)
                return signal
            else:
                logger.info(f"Signal rejected - TCS too low: {signal.tcs_score} (min: {min_tcs})")
                return None
        
        return None
    
    def _try_backup_strategies(self, symbol: str, market_data: MarketData,
                              indicators: TechnicalIndicators, 
                              excluded_strategy: str) -> Optional[TradingSignal]:
        """Try other strategies if primary fails"""
        
        backup_order = {
            'london_breakout': ['support_resistance', 'momentum_continuation'],
            'support_resistance': ['momentum_continuation', 'mean_reversion'],
            'momentum_continuation': ['support_resistance', 'mean_reversion'],
            'mean_reversion': ['support_resistance', 'momentum_continuation']}
        
        for backup in backup_order.get(excluded_strategy, []):
            try:
                strategy = self.strategies[symbol][backup]
                signal = strategy.analyze_setup([market_data], indicators)
                if signal and signal.tcs_score >= 75:  # Higher threshold for backup
                    logger.info(f"Backup strategy {backup} generated signal")
                    return signal
            except Exception as e:
                logger.error(f"Backup strategy {backup} failed: {e}")
        
        return None
    
    def _is_in_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in signal cooldown period"""
        
        if not self.recent_signals[symbol]:
            return False
        
        last_signal = self.recent_signals[symbol][-1]
        cooldown_end = last_signal.timestamp + timedelta(minutes=self.signal_cooldown_minutes)
        
        return datetime.now() < cooldown_end
    
    def _record_signal(self, symbol: str, signal: TradingSignal) -> None:
        """Record signal for tracking and cooldown"""
        
        # Add to recent signals
        self.recent_signals[symbol].append(signal)
        
        # Maintain window
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.recent_signals[symbol] = [
            s for s in self.recent_signals[symbol] 
            if s.timestamp > cutoff_time
        ]
        
        # Add to history
        self.signal_history.append(signal)
        
        # Update stats (would track actual results in production)
        strategy_name = signal.strategy_type.value
        self.strategy_stats[strategy_name]['total'] += 1
    
    def get_active_signals(self) -> List[TradingSignal]:
        """Get all currently active signals"""
        
        active = []
        current_time = datetime.now()
        
        for signal in self.signal_history:
            if signal.expiry_time > current_time:
                active.append(signal)
        
        return active
    
    def get_strategy_performance(self) -> Dict[str, Dict]:
        """Get performance stats for all strategies"""
        
        performance = {}
        
        for strategy, stats in self.strategy_stats.items():
            if stats['total'] > 0:
                win_rate = stats['wins'] / stats['total']
            else:
                win_rate = 0.0
            
            performance[strategy] = {
                'total_signals': stats['total'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': win_rate,
                'profit_factor': self._calculate_profit_factor(strategy)
            }
        
        return performance
    
    def _calculate_profit_factor(self, strategy: str) -> float:
        """Calculate profit factor for a strategy"""
        
        # In production, would calculate from actual P&L
        # For now, use win rate as proxy
        stats = self.strategy_stats[strategy]
        if stats['losses'] == 0:
            return 2.0 if stats['wins'] > 0 else 0.0
        
        # Assume 2:1 average R:R
        gross_profit = stats['wins'] * 2.0
        gross_loss = stats['losses'] * 1.0
        
        return gross_profit / gross_loss if gross_loss > 0 else 0.0
    
    def update_signal_result(self, signal_id: str, result: str, pips: float) -> None:
        """Update signal with actual result"""
        
        # Find signal
        signal = None
        for s in self.signal_history:
            if s.signal_id == signal_id:
                signal = s
                break
        
        if not signal:
            logger.error(f"Signal {signal_id} not found")
            return
        
        # Update stats
        strategy_name = signal.strategy_type.value
        
        if result == 'win':
            self.strategy_stats[strategy_name]['wins'] += 1
            # Update market analyzer performance
            symbol = signal.symbol
            self.market_analyzers[symbol].strategy_performance[strategy_name].append(True)
        else:
            self.strategy_stats[strategy_name]['losses'] += 1
            # Update market analyzer performance
            symbol = signal.symbol
            self.market_analyzers[symbol].strategy_performance[strategy_name].append(False)
        
        # Recalculate win rate
        stats = self.strategy_stats[strategy_name]
        stats['win_rate'] = stats['wins'] / stats['total'] if stats['total'] > 0 else 0.0