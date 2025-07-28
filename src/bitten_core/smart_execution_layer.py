"""
Smart Execution Layer for BITTEN
Optimizes trade entry timing and execution for maximum profitability
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque
import random

logger = logging.getLogger(__name__)

class ExecutionStrategy(Enum):
    """Execution strategies based on market conditions"""
    IMMEDIATE = "immediate"          # Execute now
    SCALED = "scaled"               # Scale into position
    PATIENT = "patient"             # Wait for better price
    AGGRESSIVE = "aggressive"       # Chase the market
    ICEBERG = "iceberg"            # Hidden size execution
    TWAP = "twap"                  # Time-weighted average price
    VWAP = "vwap"                  # Volume-weighted average price

@dataclass
class ExecutionPlan:
    """Detailed execution plan for a trade"""
    signal_id: str
    strategy: ExecutionStrategy
    entry_levels: List[float]       # Multiple entry levels for scaling
    sizes: List[float]             # Size for each entry level
    time_limits: List[datetime]    # Time limit for each entry
    slippage_tolerance: float      # Max acceptable slippage
    metadata: Dict = field(default_factory=dict)
    
    @property
    def total_size(self) -> float:
        return sum(self.sizes)
    
    @property
    def average_entry(self) -> float:
        if not self.entry_levels or not self.sizes:
            return 0
        return sum(e * s for e, s in zip(self.entry_levels, self.sizes)) / self.total_size

@dataclass
class ExecutionResult:
    """Result of trade execution"""
    signal_id: str
    executed: bool
    final_entry: float
    final_size: float
    slippage: float
    execution_time: timedelta
    fills: List[Dict]  # Individual fills
    metadata: Dict = field(default_factory=dict)

class MarketMicrostructureAnalyzer:
    """Analyzes market microstructure for optimal execution"""
    
    def __init__(self):
        self.spread_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=100)
        self.volatility_history = deque(maxlen=100)
        
    def analyze_current_conditions(self, market_data: Dict) -> Dict[str, Any]:
        """Analyze current market microstructure"""
        spread = market_data.get('spread', 1.0)
        volume = market_data.get('volume', 0)
        volatility = market_data.get('atr', 20)
        
        # Update history
        self.spread_history.append(spread)
        self.volume_history.append(volume)
        self.volatility_history.append(volatility)
        
        # Calculate metrics
        avg_spread = np.mean(self.spread_history) if self.spread_history else spread
        spread_ratio = spread / avg_spread if avg_spread > 0 else 1.0
        
        avg_volume = np.mean(self.volume_history) if self.volume_history else volume
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        
        avg_volatility = np.mean(self.volatility_history) if self.volatility_history else volatility
        volatility_ratio = volatility / avg_volatility if avg_volatility > 0 else 1.0
        
        # Determine market quality
        quality_score = 100
        
        # Penalize wide spreads
        if spread_ratio > 1.5:
            quality_score -= 20
        elif spread_ratio > 1.2:
            quality_score -= 10
            
        # Reward high volume
        if volume_ratio > 1.5:
            quality_score += 10
        elif volume_ratio < 0.5:
            quality_score -= 15
            
        # Adjust for volatility
        if volatility_ratio > 2.0:
            quality_score -= 25  # Very volatile
        elif volatility_ratio > 1.5:
            quality_score -= 15
        elif volatility_ratio < 0.7:
            quality_score += 5   # Low volatility
        
        return {
            'quality_score': max(0, min(100, quality_score)),
            'spread_ratio': spread_ratio,
            'volume_ratio': volume_ratio,
            'volatility_ratio': volatility_ratio,
            'is_liquid': spread_ratio < 1.2 and volume_ratio > 0.8,
            'is_volatile': volatility_ratio > 1.5,
            'recommendation': self._get_execution_recommendation(quality_score, spread_ratio, volatility_ratio)
        }
    
    def _get_execution_recommendation(self, quality_score: float, spread_ratio: float, volatility_ratio: float) -> str:
        """Get execution recommendation based on conditions"""
        if quality_score >= 80:
            return "EXECUTE_NOW"
        elif quality_score >= 60:
            return "EXECUTE_CAREFULLY"
        elif volatility_ratio > 1.5:
            return "WAIT_FOR_CALM"
        elif spread_ratio > 1.5:
            return "WAIT_FOR_TIGHTER_SPREAD"
        else:
            return "EXECUTE_WITH_LIMITS"

class SmartExecutionEngine:
    """
    Smart execution engine that optimizes trade entries
    """
    
    def __init__(self):
        self.microstructure_analyzer = MarketMicrostructureAnalyzer()
        self.execution_history = deque(maxlen=1000)
        
        # Execution parameters
        self.max_slippage = {
            'sniper': 0.0001,      # 1 pip
            'precision': 0.0002,   # 2 pips
            'rapid': 0.0003,       # 3 pips
            'training': 0.0005     # 5 pips
        }
        
        self.execution_timeouts = {
            'immediate': timedelta(seconds=5),
            'patient': timedelta(minutes=5),
            'scaled': timedelta(minutes=10)
        }
        
    async def create_execution_plan(self, signal: Dict, market_data: Dict) -> ExecutionPlan:
        """Create optimized execution plan for a signal"""
        try:
            # Analyze market microstructure
            micro_analysis = self.microstructure_analyzer.analyze_current_conditions(market_data)
            
            # Determine execution strategy
            strategy = self._determine_strategy(signal, micro_analysis)
            
            # Create entry levels based on strategy
            entry_levels, sizes = self._calculate_entry_levels(
                signal, strategy, market_data, micro_analysis
            )
            
            # Set time limits
            time_limits = self._calculate_time_limits(strategy, len(entry_levels))
            
            # Get slippage tolerance
            tier = signal.get('tier', 'rapid')
            slippage_tolerance = self.max_slippage.get(tier, 0.0003)
            
            plan = ExecutionPlan(
                signal_id=signal['signal_id'],
                strategy=strategy,
                entry_levels=entry_levels,
                sizes=sizes,
                time_limits=time_limits,
                slippage_tolerance=slippage_tolerance,
                metadata={
                    'micro_analysis': micro_analysis,
                    'signal_confidence': signal.get('confidence', 70),
                    'market_quality': micro_analysis['quality_score']
                }
            )
            
            logger.info(
                f"Created {strategy.value} execution plan for {signal['pair']}: "
                f"{len(entry_levels)} levels, avg entry {plan.average_entry:.5f}"
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            # Return simple immediate execution as fallback
            return ExecutionPlan(
                signal_id=signal['signal_id'],
                strategy=ExecutionStrategy.IMMEDIATE,
                entry_levels=[signal['entry']],
                sizes=[1.0],
                time_limits=[datetime.now() + timedelta(seconds=30)],
                slippage_tolerance=0.0003
            )
    
    def _determine_strategy(self, signal: Dict, micro_analysis: Dict) -> ExecutionStrategy:
        """Determine optimal execution strategy"""
        quality_score = micro_analysis['quality_score']
        is_volatile = micro_analysis['is_volatile']
        confidence = signal.get('confidence', 70)
        tier = signal.get('tier', 'rapid')
        
        # High confidence + good market = immediate
        if confidence >= 85 and quality_score >= 80:
            return ExecutionStrategy.IMMEDIATE
        
        # Volatile market = scaled entry
        if is_volatile and tier in ['sniper', 'precision']:
            return ExecutionStrategy.SCALED
        
        # Poor market quality = patient
        if quality_score < 60:
            return ExecutionStrategy.PATIENT
        
        # High tier signals in normal conditions = TWAP
        if tier == 'sniper' and quality_score >= 70:
            return ExecutionStrategy.TWAP
        
        # Default to immediate for most cases
        return ExecutionStrategy.IMMEDIATE
    
    def _calculate_entry_levels(self, signal: Dict, strategy: ExecutionStrategy, 
                              market_data: Dict, micro_analysis: Dict) -> Tuple[List[float], List[float]]:
        """Calculate entry levels and sizes based on strategy"""
        base_entry = signal['entry']
        direction = signal['action']  # 'BUY' or 'SELL'
        
        if strategy == ExecutionStrategy.IMMEDIATE:
            return [base_entry], [1.0]
        
        elif strategy == ExecutionStrategy.SCALED:
            # 3 scaled entries
            spread = market_data.get('spread', 0.0001)
            if direction == 'BUY':
                levels = [
                    base_entry,
                    base_entry - spread,
                    base_entry - 2 * spread
                ]
            else:
                levels = [
                    base_entry,
                    base_entry + spread,
                    base_entry + 2 * spread
                ]
            sizes = [0.4, 0.4, 0.2]  # 40%, 40%, 20%
            return levels, sizes
        
        elif strategy == ExecutionStrategy.PATIENT:
            # Wait for better price
            improvement = 0.0002  # 2 pips better
            if direction == 'BUY':
                levels = [base_entry - improvement]
            else:
                levels = [base_entry + improvement]
            return levels, [1.0]
        
        elif strategy == ExecutionStrategy.TWAP:
            # 5 equal entries over time
            levels = [base_entry] * 5
            sizes = [0.2] * 5  # 20% each
            return levels, sizes
        
        else:  # Default
            return [base_entry], [1.0]
    
    def _calculate_time_limits(self, strategy: ExecutionStrategy, num_levels: int) -> List[datetime]:
        """Calculate time limits for each entry level"""
        now = datetime.now()
        
        if strategy == ExecutionStrategy.IMMEDIATE:
            return [now + timedelta(seconds=10)] * num_levels
        
        elif strategy == ExecutionStrategy.PATIENT:
            return [now + timedelta(minutes=5)] * num_levels
        
        elif strategy == ExecutionStrategy.TWAP:
            # Spread entries over 10 minutes
            interval = timedelta(minutes=2)
            return [now + interval * i for i in range(1, num_levels + 1)]
        
        elif strategy == ExecutionStrategy.SCALED:
            # Progressive time limits
            return [
                now + timedelta(seconds=30),
                now + timedelta(minutes=2),
                now + timedelta(minutes=5)
            ][:num_levels]
        
        else:
            return [now + timedelta(minutes=1)] * num_levels
    
    async def execute_plan(self, plan: ExecutionPlan, market_data_stream) -> ExecutionResult:
        """Execute the plan with real-time market data"""
        fills = []
        start_time = datetime.now()
        
        for i, (level, size, time_limit) in enumerate(zip(plan.entry_levels, plan.sizes, plan.time_limits)):
            if datetime.now() > time_limit:
                logger.warning(f"Execution timeout for level {i+1}/{len(plan.entry_levels)}")
                break
            
            # Execute this level
            fill = await self._execute_level(
                level, size, plan.slippage_tolerance, 
                time_limit, market_data_stream
            )
            
            if fill:
                fills.append(fill)
                
                # Add smart delays for non-immediate strategies
                if plan.strategy != ExecutionStrategy.IMMEDIATE and i < len(plan.entry_levels) - 1:
                    delay = self._calculate_smart_delay(plan.strategy, market_data_stream)
                    await asyncio.sleep(delay)
        
        # Calculate final results
        if fills:
            total_size = sum(f['size'] for f in fills)
            weighted_entry = sum(f['price'] * f['size'] for f in fills) / total_size
            
            result = ExecutionResult(
                signal_id=plan.signal_id,
                executed=True,
                final_entry=weighted_entry,
                final_size=total_size,
                slippage=weighted_entry - plan.entry_levels[0],
                execution_time=datetime.now() - start_time,
                fills=fills,
                metadata={
                    'strategy': plan.strategy.value,
                    'levels_filled': len(fills),
                    'levels_planned': len(plan.entry_levels)
                }
            )
        else:
            result = ExecutionResult(
                signal_id=plan.signal_id,
                executed=False,
                final_entry=0,
                final_size=0,
                slippage=0,
                execution_time=datetime.now() - start_time,
                fills=[],
                metadata={'failure_reason': 'No fills executed'}
            )
        
        # Record execution for learning
        self._record_execution(plan, result)
        
        return result
    
    async def _execute_level(self, target_price: float, size: float, 
                           slippage_tolerance: float, time_limit: datetime,
                           market_data_stream) -> Optional[Dict]:
        """Execute a single entry level"""
        # In production, this would interface with MT5 or broker API
        # For now, simulate execution
        
        # Simulate market movement and execution
        await asyncio.sleep(0.1)  # Simulate execution delay
        
        # Mock execution with slight slippage
        slippage = random.uniform(-0.0001, 0.0001)
        executed_price = target_price + slippage
        
        if abs(slippage) > slippage_tolerance:
            logger.warning(f"Slippage {slippage:.5f} exceeds tolerance {slippage_tolerance:.5f}")
            return None
        
        return {
            'price': executed_price,
            'size': size,
            'timestamp': datetime.now(),
            'slippage': slippage
        }
    
    def _calculate_smart_delay(self, strategy: ExecutionStrategy, market_data_stream) -> float:
        """Calculate smart delay between executions"""
        if strategy == ExecutionStrategy.TWAP:
            return 120  # 2 minutes for TWAP
        elif strategy == ExecutionStrategy.SCALED:
            # Variable delay based on market conditions
            return random.uniform(30, 120)
        else:
            return 5  # Default 5 seconds
    
    def _record_execution(self, plan: ExecutionPlan, result: ExecutionResult):
        """Record execution for performance tracking"""
        self.execution_history.append({
            'timestamp': datetime.now(),
            'strategy': plan.strategy.value,
            'success': result.executed,
            'slippage': result.slippage,
            'execution_time': result.execution_time.total_seconds(),
            'market_quality': plan.metadata.get('market_quality', 0)
        })
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution performance statistics"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0,
                'avg_slippage': 0,
                'avg_execution_time': 0,
                'strategy_breakdown': {}
            }
        
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e['success'])
        
        # Strategy breakdown
        strategy_stats = {}
        for strategy in ExecutionStrategy:
            strategy_execs = [e for e in self.execution_history if e['strategy'] == strategy.value]
            if strategy_execs:
                strategy_stats[strategy.value] = {
                    'count': len(strategy_execs),
                    'success_rate': sum(1 for e in strategy_execs if e['success']) / len(strategy_execs),
                    'avg_slippage': np.mean([e['slippage'] for e in strategy_execs]),
                    'avg_time': np.mean([e['execution_time'] for e in strategy_execs])
                }
        
        return {
            'total_executions': total,
            'success_rate': successful / total if total > 0 else 0,
            'avg_slippage': np.mean([e['slippage'] for e in self.execution_history]),
            'avg_execution_time': np.mean([e['execution_time'] for e in self.execution_history]),
            'strategy_breakdown': strategy_stats,
            'recent_quality_score': np.mean([
                e.get('market_quality', 50) 
                for e in list(self.execution_history)[-10:]
            ])
        }

# Global instance
smart_execution = SmartExecutionEngine()