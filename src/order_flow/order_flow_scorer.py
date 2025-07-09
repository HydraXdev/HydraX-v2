"""
Order Flow Scoring System

Real-time scoring system that combines all order flow indicators
into actionable trading signals.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import deque
from enum import Enum

from .order_book_reader import OrderBookSnapshot
from .imbalance_detector import ImbalanceSignal
from .absorption_detector import AbsorptionPattern, AbsorptionEvent
from .liquidity_void_detector import LiquidityProfile, LiquidityVoid
from .cumulative_delta import DeltaBar, DeltaDivergence
from .dark_pool_scanner import DarkPoolFlow, DarkPoolPrint

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class OrderFlowScore:
    """Comprehensive order flow score"""
    timestamp: float
    symbol: str
    exchange: str
    
    # Component scores (0-100)
    imbalance_score: float
    absorption_score: float
    liquidity_score: float
    delta_score: float
    dark_pool_score: float
    
    # Overall metrics
    composite_score: float  # -100 to 100
    signal_strength: SignalStrength
    confidence: float  # 0-1
    
    # Key insights
    insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'scores': {
                'imbalance': self.imbalance_score,
                'absorption': self.absorption_score,
                'liquidity': self.liquidity_score,
                'delta': self.delta_score,
                'dark_pool': self.dark_pool_score,
                'composite': self.composite_score
            },
            'signal_strength': self.signal_strength.value,
            'confidence': self.confidence,
            'insights': self.insights,
            'warnings': self.warnings
        }


@dataclass
class TradingOpportunity:
    """Represents a specific trading opportunity"""
    timestamp: float
    symbol: str
    exchange: str
    opportunity_type: str  # 'breakout', 'reversal', 'continuation', etc.
    direction: str  # 'long' or 'short'
    entry_price: float
    stop_loss: float
    take_profit: List[float]  # Multiple TP levels
    risk_reward_ratio: float
    confidence: float
    reasoning: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'opportunity_type': self.opportunity_type,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_reward_ratio': self.risk_reward_ratio,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }


class OrderFlowScorer:
    """Combines all order flow indicators into actionable scores"""
    
    def __init__(self,
                 weights: Optional[Dict[str, float]] = None,
                 min_confidence: float = 0.6,
                 lookback_periods: int = 20):
        """
        Initialize order flow scorer
        
        Args:
            weights: Component weights for scoring
            min_confidence: Minimum confidence for signals
            lookback_periods: Periods to analyze for scoring
        """
        self.weights = weights or {
            'imbalance': 0.25,
            'absorption': 0.20,
            'liquidity': 0.20,
            'delta': 0.20,
            'dark_pool': 0.15
        }
        self.min_confidence = min_confidence
        self.lookback_periods = lookback_periods
        
        # Score history
        self.score_history: Dict[str, deque] = {}
        self.opportunity_history: Dict[str, deque] = {}
        
        # Thresholds
        self.signal_thresholds = {
            SignalStrength.STRONG_BUY: 50,
            SignalStrength.BUY: 20,
            SignalStrength.NEUTRAL: -20,
            SignalStrength.SELL: -50,
            SignalStrength.STRONG_SELL: float('-inf')
        }
    
    def calculate_score(self,
                       symbol: str,
                       exchange: str,
                       order_book: Optional[OrderBookSnapshot] = None,
                       imbalance: Optional[ImbalanceSignal] = None,
                       absorption: Optional[AbsorptionPattern] = None,
                       liquidity: Optional[LiquidityProfile] = None,
                       delta_info: Optional[Dict] = None,
                       dark_pool: Optional[DarkPoolFlow] = None) -> OrderFlowScore:
        """Calculate comprehensive order flow score"""
        
        # Initialize history if needed
        key = f"{exchange}:{symbol}"
        if key not in self.score_history:
            self.score_history[key] = deque(maxlen=self.lookback_periods * 10)
            self.opportunity_history[key] = deque(maxlen=50)
        
        # Calculate component scores
        imbalance_score = self._score_imbalance(imbalance)
        absorption_score = self._score_absorption(absorption)
        liquidity_score = self._score_liquidity(liquidity)
        delta_score = self._score_delta(delta_info)
        dark_pool_score = self._score_dark_pool(dark_pool)
        
        # Calculate weighted composite score
        composite_score = (
            self.weights['imbalance'] * (imbalance_score - 50) * 2 +
            self.weights['absorption'] * (absorption_score - 50) * 2 +
            self.weights['liquidity'] * (liquidity_score - 50) * 2 +
            self.weights['delta'] * (delta_score - 50) * 2 +
            self.weights['dark_pool'] * (dark_pool_score - 50) * 2
        )
        
        # Determine signal strength
        signal_strength = self._determine_signal_strength(composite_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            imbalance, absorption, liquidity, delta_info, dark_pool
        )
        
        # Generate insights and warnings
        insights = self._generate_insights(
            imbalance, absorption, liquidity, delta_info, dark_pool
        )
        warnings = self._generate_warnings(
            imbalance, absorption, liquidity, delta_info, dark_pool
        )
        
        # Create score object
        score = OrderFlowScore(
            timestamp=datetime.now().timestamp(),
            symbol=symbol,
            exchange=exchange,
            imbalance_score=imbalance_score,
            absorption_score=absorption_score,
            liquidity_score=liquidity_score,
            delta_score=delta_score,
            dark_pool_score=dark_pool_score,
            composite_score=composite_score,
            signal_strength=signal_strength,
            confidence=confidence,
            insights=insights,
            warnings=warnings
        )
        
        # Store in history
        self.score_history[key].append(score)
        
        # Check for trading opportunities
        opportunity = self._check_opportunity(score, order_book)
        if opportunity:
            self.opportunity_history[key].append(opportunity)
        
        return score
    
    def _score_imbalance(self, imbalance: Optional[ImbalanceSignal]) -> float:
        """Score order book imbalance (0-100)"""
        
        if not imbalance:
            return 50  # Neutral
        
        # Base score on imbalance ratio and strength
        base_score = 50
        
        # Adjust for direction
        if imbalance.direction == 'bullish':
            # Strong bullish imbalance
            if imbalance.strength == 'extreme':
                base_score = 90
            elif imbalance.strength == 'strong':
                base_score = 75
            elif imbalance.strength == 'moderate':
                base_score = 65
            else:
                base_score = 55
        else:  # bearish
            if imbalance.strength == 'extreme':
                base_score = 10
            elif imbalance.strength == 'strong':
                base_score = 25
            elif imbalance.strength == 'moderate':
                base_score = 35
            else:
                base_score = 45
        
        # Adjust for weighted imbalance
        if imbalance.weighted_imbalance > 3:
            base_score = min(100, base_score + 10)
        elif imbalance.weighted_imbalance < 0.33:
            base_score = max(0, base_score - 10)
        
        return base_score
    
    def _score_absorption(self, absorption: Optional[AbsorptionPattern]) -> float:
        """Score absorption patterns (0-100)"""
        
        if not absorption:
            return 50  # Neutral
        
        # Base score on pattern type
        pattern_scores = {
            'accumulation': 80,
            'distribution': 20,
            'support': 70,
            'resistance': 30
        }
        
        base_score = pattern_scores.get(absorption.pattern_type, 50)
        
        # Adjust for confidence
        confidence_adjustment = (absorption.confidence - 0.5) * 20
        base_score += confidence_adjustment
        
        # Adjust for volume
        if absorption.total_volume > 1000:  # High volume absorption
            base_score = min(100, base_score + 10)
        
        return max(0, min(100, base_score))
    
    def _score_liquidity(self, liquidity: Optional[LiquidityProfile]) -> float:
        """Score liquidity profile (0-100)"""
        
        if not liquidity:
            return 50  # Neutral
        
        # Start with liquidity score
        base_score = liquidity.liquidity_score
        
        # Penalize for critical voids
        if liquidity.largest_bid_void and liquidity.largest_bid_void.severity == 'critical':
            base_score -= 15
        if liquidity.largest_ask_void and liquidity.largest_ask_void.severity == 'critical':
            base_score -= 15
        
        # Adjust for spread
        if liquidity.effective_spread > liquidity.average_spread * 2:
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    def _score_delta(self, delta_info: Optional[Dict]) -> float:
        """Score cumulative delta (0-100)"""
        
        if not delta_info:
            return 50  # Neutral
        
        base_score = 50
        
        # Adjust for delta trend
        if delta_info.get('delta_trend') == 'bullish':
            base_score = 70
        elif delta_info.get('delta_trend') == 'bearish':
            base_score = 30
        
        # Adjust for cumulative delta level
        cum_delta = delta_info.get('cumulative_delta', 0)
        if abs(cum_delta) > 1000:
            if cum_delta > 0:
                base_score = min(100, base_score + 15)
            else:
                base_score = max(0, base_score - 15)
        
        return base_score
    
    def _score_dark_pool(self, dark_pool: Optional[DarkPoolFlow]) -> float:
        """Score dark pool activity (0-100)"""
        
        if not dark_pool:
            return 50  # Neutral
        
        # Base score on flow score
        base_score = 50 + (dark_pool.flow_score / 2)  # Convert -100 to 100 -> 0 to 100
        
        # Adjust for large prints
        if dark_pool.large_print_count > 5:
            # Multiple large prints suggest institutional activity
            if dark_pool.flow_score > 0:
                base_score = min(100, base_score + 10)
            else:
                base_score = max(0, base_score - 10)
        
        return max(0, min(100, base_score))
    
    def _determine_signal_strength(self, composite_score: float) -> SignalStrength:
        """Determine signal strength from composite score"""
        
        for strength, threshold in self.signal_thresholds.items():
            if composite_score >= threshold:
                return strength
        
        return SignalStrength.STRONG_SELL
    
    def _calculate_confidence(self, *args) -> float:
        """Calculate overall confidence based on indicator agreement"""
        
        # Count how many indicators are present
        present_indicators = sum(1 for arg in args if arg is not None)
        
        if present_indicators < 2:
            return 0.3  # Low confidence with few indicators
        
        # Calculate agreement between indicators
        scores = []
        
        if args[0]:  # imbalance
            scores.append(1 if args[0].direction == 'bullish' else -1)
        if args[1]:  # absorption
            scores.append(1 if args[1].pattern_type in ['accumulation', 'support'] else -1)
        if args[3]:  # delta
            scores.append(1 if args[3].get('delta_trend') == 'bullish' else -1)
        if args[4]:  # dark pool
            scores.append(1 if args[4].flow_score > 0 else -1)
        
        if not scores:
            return 0.5
        
        # High agreement = high confidence
        agreement = abs(sum(scores)) / len(scores)
        base_confidence = 0.5 + (agreement * 0.3)
        
        # Boost confidence if more indicators present
        indicator_bonus = (present_indicators - 2) * 0.1
        
        return min(1.0, base_confidence + indicator_bonus)
    
    def _generate_insights(self, *args) -> List[str]:
        """Generate insights from indicators"""
        
        insights = []
        
        # Imbalance insights
        if args[0]:
            imbalance = args[0]
            insights.append(f"{imbalance.strength.capitalize()} {imbalance.direction} "
                          f"order book imbalance detected (ratio: {imbalance.imbalance_ratio:.2f})")
        
        # Absorption insights
        if args[1]:
            absorption = args[1]
            insights.append(f"{absorption.pattern_type.capitalize()} pattern detected "
                          f"with {absorption.total_volume:.0f} volume absorbed")
        
        # Liquidity insights
        if args[2]:
            liquidity = args[2]
            if liquidity.liquidity_score < 50:
                insights.append(f"Poor liquidity conditions (score: {liquidity.liquidity_score:.0f}/100)")
        
        # Delta insights
        if args[3]:
            delta = args[3]
            if delta.get('delta_trend') != 'neutral':
                insights.append(f"{delta['delta_trend'].capitalize()} cumulative delta trend")
        
        # Dark pool insights
        if args[4]:
            dark_pool = args[4]
            if abs(dark_pool.flow_score) > 50:
                direction = "buying" if dark_pool.flow_score > 0 else "selling"
                insights.append(f"Strong dark pool {direction} detected "
                              f"(flow score: {dark_pool.flow_score:.0f})")
        
        return insights
    
    def _generate_warnings(self, *args) -> List[str]:
        """Generate warnings from indicators"""
        
        warnings = []
        
        # Liquidity warnings
        if args[2]:  # liquidity
            liquidity = args[2]
            if liquidity.bid_void_count > 3:
                warnings.append(f"Multiple bid-side liquidity voids detected ({liquidity.bid_void_count})")
            if liquidity.ask_void_count > 3:
                warnings.append(f"Multiple ask-side liquidity voids detected ({liquidity.ask_void_count})")
            if liquidity.effective_spread > liquidity.average_spread * 3:
                warnings.append("Effective spread significantly wider than average")
        
        # Delta divergence warnings
        if args[3]:  # delta
            delta = args[3]
            if 'divergences' in delta and delta['divergences']:
                warnings.append("Price/delta divergence detected")
        
        return warnings
    
    def _check_opportunity(self, score: OrderFlowScore, order_book: Optional[OrderBookSnapshot]) -> Optional[TradingOpportunity]:
        """Check if current conditions present a trading opportunity"""
        
        # Need strong signal and high confidence
        if score.confidence < self.min_confidence:
            return None
        
        if score.signal_strength == SignalStrength.NEUTRAL:
            return None
        
        # Determine opportunity type and direction
        if score.signal_strength in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
            direction = 'long'
            opportunity_type = self._classify_opportunity_type(score, 'long')
        else:
            direction = 'short'
            opportunity_type = self._classify_opportunity_type(score, 'short')
        
        if not order_book:
            return None
        
        # Calculate entry and exit levels
        current_price = order_book.get_mid_price()
        
        if direction == 'long':
            entry_price = current_price * 1.0002  # Small buffer above mid
            stop_loss = current_price * 0.995  # 0.5% stop
            take_profit = [
                current_price * 1.005,  # TP1: 0.5%
                current_price * 1.010,  # TP2: 1.0%
                current_price * 1.015   # TP3: 1.5%
            ]
        else:
            entry_price = current_price * 0.9998  # Small buffer below mid
            stop_loss = current_price * 1.005  # 0.5% stop
            take_profit = [
                current_price * 0.995,  # TP1: 0.5%
                current_price * 0.990,  # TP2: 1.0%
                current_price * 0.985   # TP3: 1.5%
            ]
        
        # Calculate risk-reward
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit[1] - entry_price)  # Use TP2 for RR calculation
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        return TradingOpportunity(
            timestamp=score.timestamp,
            symbol=score.symbol,
            exchange=score.exchange,
            opportunity_type=opportunity_type,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward_ratio,
            confidence=score.confidence,
            reasoning=score.insights
        )
    
    def _classify_opportunity_type(self, score: OrderFlowScore, direction: str) -> str:
        """Classify the type of trading opportunity"""
        
        # Look at component scores to determine type
        if score.absorption_score > 70 and direction == 'long':
            return 'accumulation'
        elif score.absorption_score < 30 and direction == 'short':
            return 'distribution'
        elif score.imbalance_score > 80 or score.imbalance_score < 20:
            return 'imbalance_play'
        elif score.dark_pool_score > 80 or score.dark_pool_score < 20:
            return 'institutional_follow'
        else:
            return 'momentum'
    
    def get_recent_opportunities(self, symbol: str, exchange: str = None, limit: int = 10) -> List[TradingOpportunity]:
        """Get recent trading opportunities"""
        
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.opportunity_history:
            return []
        
        opportunities = list(self.opportunity_history[key])
        return opportunities[-limit:]
    
    def get_score_history(self, symbol: str, exchange: str = None, limit: int = 50) -> List[OrderFlowScore]:
        """Get historical scores"""
        
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.score_history:
            return []
        
        scores = list(self.score_history[key])
        return scores[-limit:]
    
    def get_statistics(self, symbol: str, exchange: str = None) -> Dict:
        """Get scoring statistics"""
        
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.score_history:
            return {
                'scores_calculated': 0,
                'opportunities_found': 0,
                'average_confidence': 0,
                'signal_distribution': {}
            }
        
        scores = list(self.score_history[key])
        opportunities = list(self.opportunity_history[key]) if key in self.opportunity_history else []
        
        if not scores:
            return {
                'scores_calculated': 0,
                'opportunities_found': 0,
                'average_confidence': 0,
                'signal_distribution': {}
            }
        
        # Calculate signal distribution
        signal_dist = {}
        for signal in SignalStrength:
            signal_dist[signal.value] = sum(1 for s in scores if s.signal_strength == signal)
        
        # Calculate average scores
        avg_scores = {
            'imbalance': np.mean([s.imbalance_score for s in scores]),
            'absorption': np.mean([s.absorption_score for s in scores]),
            'liquidity': np.mean([s.liquidity_score for s in scores]),
            'delta': np.mean([s.delta_score for s in scores]),
            'dark_pool': np.mean([s.dark_pool_score for s in scores]),
            'composite': np.mean([s.composite_score for s in scores])
        }
        
        return {
            'scores_calculated': len(scores),
            'opportunities_found': len(opportunities),
            'average_confidence': np.mean([s.confidence for s in scores]),
            'average_scores': avg_scores,
            'signal_distribution': signal_dist,
            'current_signal': scores[-1].signal_strength.value if scores else None,
            'hit_rate': len([o for o in opportunities if o.confidence > 0.7]) / len(opportunities) if opportunities else 0
        }


# Example usage
async def main():
    scorer = OrderFlowScorer(
        min_confidence=0.6,
        lookback_periods=20
    )
    
    # Create sample data
    from .order_book_reader import OrderBookSnapshot, OrderBookLevel
    from .imbalance_detector import ImbalanceSignal
    from .liquidity_void_detector import LiquidityProfile
    
    # Sample order book
    order_book = OrderBookSnapshot(
        symbol='BTC/USDT',
        exchange='binance',
        bids=[OrderBookLevel(50000 - i, 2.5 - i*0.1) for i in range(20)],
        asks=[OrderBookLevel(50001 + i, 0.8 + i*0.05) for i in range(20)],
        timestamp=datetime.now().timestamp()
    )
    
    # Sample imbalance (bullish)
    imbalance = ImbalanceSignal(
        timestamp=datetime.now().timestamp(),
        symbol='BTC/USDT',
        exchange='binance',
        imbalance_ratio=2.5,
        bid_volume=100,
        ask_volume=40,
        levels_analyzed=20,
        direction='bullish',
        strength='strong',
        weighted_imbalance=2.8,
        price_level=50000
    )
    
    # Sample liquidity profile
    liquidity = LiquidityProfile(
        timestamp=datetime.now().timestamp(),
        symbol='BTC/USDT',
        exchange='binance',
        total_bid_liquidity=50000,
        total_ask_liquidity=45000,
        bid_void_count=1,
        ask_void_count=2,
        largest_bid_void=None,
        largest_ask_void=None,
        liquidity_score=75,
        average_spread=1.0,
        effective_spread=1.5
    )
    
    # Sample delta info
    delta_info = {
        'cumulative_delta': 500,
        'current_bar_delta': 50,
        'delta_trend': 'bullish'
    }
    
    # Sample dark pool flow
    dark_pool = DarkPoolFlow(
        symbol='BTC/USDT',
        time_period='1h',
        total_volume=1000,
        buy_volume=700,
        sell_volume=300,
        neutral_volume=0,
        average_print_size=100000,
        large_print_count=3,
        flow_score=40
    )
    
    # Calculate score
    score = scorer.calculate_score(
        'BTC/USDT',
        'binance',
        order_book=order_book,
        imbalance=imbalance,
        liquidity=liquidity,
        delta_info=delta_info,
        dark_pool=dark_pool
    )
    
    print(f"Order Flow Score: {score.composite_score:.1f}")
    print(f"Signal: {score.signal_strength.value}")
    print(f"Confidence: {score.confidence:.2f}")
    print(f"\nInsights:")
    for insight in score.insights:
        print(f"  - {insight}")
    
    if score.warnings:
        print(f"\nWarnings:")
        for warning in score.warnings:
            print(f"  - {warning}")
    
    # Check for opportunities
    opportunities = scorer.get_recent_opportunities('BTC/USDT', 'binance')
    if opportunities:
        print(f"\nTrading Opportunities:")
        for opp in opportunities:
            print(f"  - {opp.opportunity_type} {opp.direction} @ {opp.entry_price:.2f}")
            print(f"    SL: {opp.stop_loss:.2f}, TP: {opp.take_profit}")
            print(f"    RR: {opp.risk_reward_ratio:.2f}, Confidence: {opp.confidence:.2f}")
    
    # Get statistics
    stats = scorer.get_statistics('BTC/USDT', 'binance')
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())