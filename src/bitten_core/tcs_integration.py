#!/usr/bin/env python3
"""
TCS Integration Layer
Connects the self-optimizing TCS engine to the main signal flow
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .self_optimizing_tcs import (
    SelfOptimizingTCS, 
    TCSOptimizationConfig, 
    MarketCondition,
    get_tcs_optimizer
)
from .signal_fusion import FusedSignal, ConfidenceTier, SignalFusionEngine
from .mt5_enhanced_adapter import MT5EnhancedAdapter

logger = logging.getLogger(__name__)

@dataclass
class TCSSignalMetrics:
    """Metrics for a signal used in TCS optimization"""
    signal_id: str
    pair: str
    direction: str
    confidence: float
    tcs_threshold_used: float
    timestamp: datetime
    market_condition: MarketCondition
    
    # Performance tracking
    executed: bool = False
    result: Optional[str] = None  # 'WIN', 'LOSS', 'PENDING'
    pips_gained: float = 0.0
    hold_time_minutes: int = 0
    closed_at: Optional[datetime] = None

class TCSPerformanceTracker:
    """
    Tracks signal performance and feeds results back to TCS optimizer
    """
    
    def __init__(self, mt5_adapter: MT5EnhancedAdapter):
        self.mt5_adapter = mt5_adapter
        self.tracked_signals: Dict[str, TCSSignalMetrics] = {}
        self.tcs_optimizer = get_tcs_optimizer()
        
    async def track_signal(self, signal: FusedSignal, tcs_threshold: float, 
                          market_condition: MarketCondition):
        """Start tracking a signal for TCS optimization"""
        
        metrics = TCSSignalMetrics(
            signal_id=signal.signal_id,
            pair=signal.pair,
            direction=signal.direction,
            confidence=signal.confidence,
            tcs_threshold_used=tcs_threshold,
            timestamp=signal.timestamp,
            market_condition=market_condition
        )
        
        self.tracked_signals[signal.signal_id] = metrics
        logger.info(f"Started tracking signal {signal.signal_id} with TCS threshold {tcs_threshold:.1f}%")
    
    async def record_signal_execution(self, signal_id: str, ticket: int, user_id: int):
        """Record that a signal was executed by a user"""
        if signal_id in self.tracked_signals:
            self.tracked_signals[signal_id].executed = True
            logger.info(f"Signal {signal_id} executed by user {user_id} (ticket: {ticket})")
    
    async def update_signal_results(self):
        """Check MT5 positions and update signal results"""
        try:
            positions_data = self.mt5_adapter.get_positions()
            closed_positions = await self._get_recent_closed_positions()
            
            # Update based on closed positions
            for position in closed_positions:
                comment = position.get('comment', '')
                if comment.startswith('BITTEN_'):
                    # Try to match with tracked signals
                    signal_id = await self._match_position_to_signal(position)
                    if signal_id and signal_id in self.tracked_signals:
                        await self._update_signal_result(signal_id, position)
            
            # Clean up old signals
            await self._cleanup_old_signals()
            
        except Exception as e:
            logger.error(f"Error updating signal results: {e}")
    
    async def _get_recent_closed_positions(self) -> List[Dict]:
        """Get recently closed positions from MT5"""
        # This would typically get closed positions from the last 24-48 hours
        # For now, we'll simulate this by checking position history
        try:
            # In a real implementation, this would query MT5 history
            # For now, return empty list to avoid errors
            return []
        except Exception as e:
            logger.error(f"Error getting closed positions: {e}")
            return []
    
    async def _match_position_to_signal(self, position: Dict) -> Optional[str]:
        """Match a closed position to a tracked signal"""
        # Extract signal information from position comment or timing
        comment = position.get('comment', '')
        symbol = position.get('symbol', '')
        direction = 'BUY' if position.get('type') == 0 else 'SELL'
        
        # Look for matching signals within reasonable timeframe
        position_time = position.get('time_close', datetime.now())
        
        for signal_id, metrics in self.tracked_signals.items():
            if (metrics.pair == symbol and 
                metrics.direction == direction and
                metrics.executed and
                metrics.result is None):
                
                # Check if timing matches (within 6 hours)
                time_diff = abs((position_time - metrics.timestamp).total_seconds())
                if time_diff < 6 * 3600:  # 6 hours
                    return signal_id
        
        return None
    
    async def _update_signal_result(self, signal_id: str, position: Dict):
        """Update the result of a tracked signal"""
        if signal_id not in self.tracked_signals:
            return
        
        metrics = self.tracked_signals[signal_id]
        
        # Determine result
        profit = position.get('profit', 0)
        metrics.result = 'WIN' if profit > 0 else 'LOSS'
        metrics.pips_gained = profit / 10  # Simplified pip calculation
        
        # Calculate hold time
        time_open = position.get('time_open', metrics.timestamp)
        time_close = position.get('time_close', datetime.now())
        metrics.hold_time_minutes = int((time_close - time_open).total_seconds() / 60)
        metrics.closed_at = time_close
        
        # Log performance to TCS optimizer
        await self.tcs_optimizer.log_signal_performance(
            pair=metrics.pair,
            tcs_score=metrics.confidence,
            direction=metrics.direction,
            result=metrics.result,
            pips_gained=metrics.pips_gained,
            hold_time_minutes=metrics.hold_time_minutes,
            market_condition=metrics.market_condition
        )
        
        logger.info(f"Signal {signal_id} result: {metrics.result} "
                   f"({metrics.pips_gained:.1f} pips, {metrics.hold_time_minutes}m)")
    
    async def _cleanup_old_signals(self):
        """Remove old signals that are no longer relevant"""
        cutoff_time = datetime.now() - timedelta(hours=48)
        
        to_remove = []
        for signal_id, metrics in self.tracked_signals.items():
            if metrics.timestamp < cutoff_time:
                to_remove.append(signal_id)
        
        for signal_id in to_remove:
            del self.tracked_signals[signal_id]
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get current tracking statistics"""
        total_signals = len(self.tracked_signals)
        executed_signals = sum(1 for m in self.tracked_signals.values() if m.executed)
        completed_signals = sum(1 for m in self.tracked_signals.values() if m.result is not None)
        
        wins = sum(1 for m in self.tracked_signals.values() if m.result == 'WIN')
        losses = sum(1 for m in self.tracked_signals.values() if m.result == 'LOSS')
        
        return {
            'total_tracked': total_signals,
            'executed': executed_signals,
            'completed': completed_signals,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / completed_signals if completed_signals > 0 else 0,
            'execution_rate': executed_signals / total_signals if total_signals > 0 else 0
        }

class MarketConditionAnalyzer:
    """
    Analyzes current market conditions for TCS optimization
    """
    
    def __init__(self, mt5_adapter: MT5EnhancedAdapter):
        self.mt5_adapter = mt5_adapter
        
    async def get_current_market_condition(self, pair: str) -> MarketCondition:
        """Analyze current market conditions for TCS optimization"""
        try:
            market_data = self.mt5_adapter.get_market_data()
            
            # Get volatility level
            volatility_level = self._analyze_volatility(market_data, pair)
            
            # Get trend strength
            trend_strength = self._analyze_trend_strength(market_data, pair)
            
            # Get session activity
            session_activity = self._get_current_session()
            
            # Get news impact (simplified)
            news_impact = self._assess_news_impact()
            
            return MarketCondition(
                volatility_level=volatility_level,
                trend_strength=trend_strength,
                session_activity=session_activity,
                news_impact=news_impact
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            # Return default conditions
            return MarketCondition(
                volatility_level="MEDIUM",
                trend_strength=0.5,
                session_activity="LONDON",
                news_impact=0.3
            )
    
    def _analyze_volatility(self, market_data: Dict, pair: str) -> str:
        """Analyze volatility level"""
        if not market_data:
            return "MEDIUM"
        
        # Get ATR or similar volatility measure
        atr = market_data.get('atr', 30)
        spread = market_data.get('spread', 2.0)
        
        # Volatility thresholds (adjust based on pair)
        if pair in ['GBPJPY', 'GBPAUD', 'AUDJPY']:
            high_threshold = 50
            low_threshold = 20
        else:
            high_threshold = 35
            low_threshold = 15
        
        if atr > high_threshold or spread > 5:
            return "HIGH"
        elif atr < low_threshold and spread < 2:
            return "LOW"
        else:
            return "MEDIUM"
    
    def _analyze_trend_strength(self, market_data: Dict, pair: str) -> float:
        """Analyze trend strength (0-1)"""
        if not market_data:
            return 0.5
        
        # Use momentum indicators or price action
        momentum = market_data.get('momentum', 0.5)
        volume_ratio = market_data.get('volume_ratio', 1.0)
        
        # Combine factors
        trend_strength = (momentum + (volume_ratio - 1.0) * 0.5) / 2
        
        # Normalize to 0-1 range
        return max(0, min(1, trend_strength))
    
    def _get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.now().hour
        
        # Session times (EST)
        if 2 <= hour <= 5:
            return "TOKYO"
        elif 3 <= hour <= 8:
            return "LONDON"
        elif 8 <= hour <= 13:
            return "OVERLAP"
        elif 13 <= hour <= 17:
            return "NY"
        else:
            return "QUIET"
    
    def _assess_news_impact(self) -> float:
        """Assess current news impact (0-1)"""
        # This would connect to an economic calendar
        # For now, return low impact
        hour = datetime.now().hour
        
        # Higher impact during typical news hours
        if 8 <= hour <= 10 or 14 <= hour <= 16:
            return 0.6
        else:
            return 0.2

class TCSIntegrationLayer:
    """
    Main integration layer that connects TCS optimizer to signal flow
    """
    
    def __init__(self, mt5_adapter: MT5EnhancedAdapter, 
                 fusion_engine: SignalFusionEngine):
        self.mt5_adapter = mt5_adapter
        self.fusion_engine = fusion_engine
        
        # Initialize components
        self.tcs_optimizer = get_tcs_optimizer()
        self.performance_tracker = TCSPerformanceTracker(mt5_adapter)
        self.market_analyzer = MarketConditionAnalyzer(mt5_adapter)
        
        # Background tasks
        self.monitoring_task = None
        
    async def start_monitoring(self):
        """Start TCS monitoring and optimization"""
        logger.info("Starting TCS integration monitoring...")
        
        # Start performance tracking
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
    async def _monitoring_loop(self):
        """Main monitoring loop for TCS optimization"""
        while True:
            try:
                # Update signal results
                await self.performance_tracker.update_signal_results()
                
                # Log current TCS stats
                stats = self.tcs_optimizer.get_optimization_stats()
                tracking_stats = self.performance_tracker.get_tracking_stats()
                
                logger.info(
                    f"TCS Stats - Threshold: {stats['current_threshold']:.1f}%, "
                    f"Signals 24h: {stats['signals_24h']}, "
                    f"Win Rate: {stats['win_rate_24h']:.1%}, "
                    f"Tracking: {tracking_stats['total_tracked']} signals"
                )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"TCS monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def process_signal_with_tcs(self, signal: FusedSignal) -> Tuple[bool, float, str]:
        """
        Process a signal through the TCS optimization system
        Returns: (should_send, tcs_threshold, reason)
        """
        try:
            # Get current market conditions
            market_condition = await self.market_analyzer.get_current_market_condition(signal.pair)
            
            # Get optimal TCS threshold
            tcs_threshold = await self.tcs_optimizer.get_optimal_tcs_threshold(market_condition)
            
            # Check if signal meets TCS threshold
            should_send = signal.confidence >= tcs_threshold
            
            # Start tracking this signal
            await self.performance_tracker.track_signal(signal, tcs_threshold, market_condition)
            
            reason = f"TCS {tcs_threshold:.1f}% (confidence: {signal.confidence:.1f}%)"
            
            return should_send, tcs_threshold, reason
            
        except Exception as e:
            logger.error(f"Error processing signal with TCS: {e}")
            # Fallback to default threshold
            return signal.confidence >= 70.0, 70.0, "TCS fallback"
    
    async def record_signal_execution(self, signal_id: str, ticket: int, user_id: int):
        """Record that a signal was executed"""
        await self.performance_tracker.record_signal_execution(signal_id, ticket, user_id)
    
    async def update_tcs_thresholds(self, pair: str) -> float:
        """Update TCS thresholds for a specific pair"""
        market_condition = await self.market_analyzer.get_current_market_condition(pair)
        return await self.tcs_optimizer.get_optimal_tcs_threshold(market_condition)
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics"""
        tcs_stats = self.tcs_optimizer.get_optimization_stats()
        tracking_stats = self.performance_tracker.get_tracking_stats()
        
        return {
            'tcs_optimization': tcs_stats,
            'performance_tracking': tracking_stats,
            'integration_status': {
                'monitoring_active': self.monitoring_task is not None and not self.monitoring_task.done(),
                'last_update': datetime.now().isoformat()
            }
        }

# Global integration instance
_integration_layer = None

def get_tcs_integration(mt5_adapter: MT5EnhancedAdapter, 
                       fusion_engine: SignalFusionEngine) -> TCSIntegrationLayer:
    """Get global TCS integration instance"""
    global _integration_layer
    if _integration_layer is None:
        _integration_layer = TCSIntegrationLayer(mt5_adapter, fusion_engine)
    return _integration_layer

def initialize_tcs_integration(mt5_adapter: MT5EnhancedAdapter, 
                              fusion_engine: SignalFusionEngine) -> TCSIntegrationLayer:
    """Initialize TCS integration system"""
    integration = get_tcs_integration(mt5_adapter, fusion_engine)
    return integration

# Example usage
async def main():
    """Test TCS integration system"""
    from .mt5_enhanced_adapter import MT5EnhancedAdapter
    from .signal_fusion import SignalFusionEngine
    
    # Initialize components
    mt5_adapter = MT5EnhancedAdapter()
    fusion_engine = SignalFusionEngine()
    
    # Initialize integration
    integration = initialize_tcs_integration(mt5_adapter, fusion_engine)
    
    # Start monitoring
    await integration.start_monitoring()
    
    print("TCS Integration system started")
    
    # Keep running
    while True:
        stats = integration.get_integration_stats()
        print(f"Current TCS threshold: {stats['tcs_optimization']['current_threshold']:.1f}%")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())