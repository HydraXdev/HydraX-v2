# microstructure_scorer.py
# Microstructure Scoring System - Comprehensive Market Quality Assessment

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass
import logging

# Import our microstructure components
from .iceberg_detector import IcebergDetector, IcebergSignal
from .spoofing_detector import SpoofingDetector, SpoofingEvent
from .hft_activity_detector import HFTActivityDetector, HFTSignature
from .quote_stuffing_identifier import QuoteStuffingIdentifier, QuoteStuffingEvent
from .hidden_liquidity_scanner import HiddenLiquidityScanner, HiddenLiquiditySignal
from .market_maker_analyzer import MarketMakerAnalyzer, MarketMakerAction

logger = logging.getLogger(__name__)

@dataclass
class MicrostructureScore:
    """Comprehensive microstructure quality score"""
    timestamp: datetime
    overall_score: float  # 0-100
    liquidity_score: float
    stability_score: float
    fairness_score: float
    efficiency_score: float
    manipulation_risk: float  # 0-100 (higher = more risk)
    institutional_presence: float  # 0-100
    market_quality: str  # 'excellent', 'good', 'fair', 'poor'
    key_insights: List[str]
    component_scores: Dict[str, float]

@dataclass
class MarketMicrostructureState:
    """Current market microstructure state"""
    timestamp: datetime
    spread: float
    depth: float
    volatility: float
    hft_intensity: float
    maker_count: int
    recent_manipulation_events: int
    hidden_liquidity_estimate: float
    institutional_flow_probability: float

class MicrostructureScorer:
    """
    MICROSTRUCTURE SCORING SYSTEM
    
    Integrates all microstructure components to provide:
    - Real-time market quality assessment
    - Manipulation risk scoring
    - Institutional activity detection
    - Trading environment evaluation
    """
    
    def __init__(self, symbol: str, tick_size: float = 0.0001):
        self.symbol = symbol
        self.tick_size = tick_size
        
        # Initialize all components
        self.iceberg_detector = IcebergDetector(symbol, tick_size)
        self.spoofing_detector = SpoofingDetector(symbol, tick_size)
        self.hft_detector = HFTActivityDetector(symbol, tick_size)
        self.stuffing_identifier = QuoteStuffingIdentifier(symbol, tick_size)
        self.liquidity_scanner = HiddenLiquidityScanner(symbol, tick_size)
        self.maker_analyzer = MarketMakerAnalyzer(symbol, tick_size)
        
        # Scoring weights
        self.weights = {
            'liquidity': 0.25,
            'stability': 0.20,
            'fairness': 0.30,
            'efficiency': 0.25
        }
        
        # Historical tracking
        self.score_history = deque(maxlen=1000)
        self.state_history = deque(maxlen=1000)
        self.alerts = deque(maxlen=100)
        
        # Thresholds
        self.manipulation_thresholds = {
            'low': 20,
            'moderate': 40,
            'high': 60,
            'extreme': 80
        }
        
    def update_market_data(self, timestamp: datetime, 
                         bid_book: Dict[float, float],
                         ask_book: Dict[float, float],
                         trades: List[Dict[str, Any]],
                         quotes: List[Dict[str, Any]]) -> MicrostructureScore:
        """
        Update all components with market data and calculate scores
        
        Args:
            timestamp: Current timestamp
            bid_book: Bid price -> size mapping
            ask_book: Ask price -> size mapping
            trades: List of recent trades
            quotes: List of recent quotes
            
        Returns:
            MicrostructureScore with comprehensive assessment
        """
        
        # Update market maker analyzer
        if bid_book and ask_book:
            best_bid = max(bid_book.keys())
            best_ask = min(ask_book.keys())
            self.maker_analyzer.analyze_quote_update(
                timestamp,
                best_bid, bid_book[best_bid],
                best_ask, ask_book[best_ask]
            )
        
        # Process trades for various detectors
        for trade in trades:
            # Iceberg detection
            self.iceberg_detector.update_order_flow(
                trade['timestamp'],
                trade['price'],
                trade['volume'],
                trade['side'],
                trade.get('spread', 2.0)
            )
            
            # Hidden liquidity analysis
            displayed_liquidity = bid_book if trade['side'] == 'buy' else ask_book
            self.liquidity_scanner.analyze_execution(
                trade['timestamp'],
                trade['price'],
                trade['volume'],
                displayed_liquidity,
                trade['side']
            )
        
        # Process quotes for manipulation detection
        for quote in quotes:
            # HFT activity
            self.hft_detector.process_event(
                quote['timestamp'],
                quote['event_type'],
                quote['price'],
                quote['size'],
                quote['side'],
                quote.get('aggressive', False)
            )
            
            # Quote stuffing
            self.stuffing_identifier.process_quote_message(
                quote['timestamp'],
                quote.get('message_id', ''),
                quote['action'],
                quote['price'],
                quote['size'],
                quote['side']
            )
        
        # Update order book for detectors
        bid_levels = [(p, s) for p, s in sorted(bid_book.items(), reverse=True)][:10]
        ask_levels = [(p, s) for p, s in sorted(ask_book.items())][:10]
        
        self.spoofing_detector.update_order_book(timestamp, bid_levels, ask_levels)
        self.liquidity_scanner.update_order_book(timestamp, bid_book, ask_book)
        
        # Calculate comprehensive score
        score = self._calculate_microstructure_score(timestamp)
        
        # Update history
        self.score_history.append(score)
        
        # Check for alerts
        self._check_alerts(score)
        
        return score
    
    def _calculate_microstructure_score(self, timestamp: datetime) -> MicrostructureScore:
        """Calculate comprehensive microstructure score"""
        
        # Component scores
        liquidity_score = self._calculate_liquidity_score()
        stability_score = self._calculate_stability_score()
        fairness_score = self._calculate_fairness_score()
        efficiency_score = self._calculate_efficiency_score()
        
        # Manipulation risk
        manipulation_risk = self._calculate_manipulation_risk()
        
        # Institutional presence
        institutional_presence = self._calculate_institutional_presence()
        
        # Overall score (weighted average minus manipulation penalty)
        overall_score = (
            liquidity_score * self.weights['liquidity'] +
            stability_score * self.weights['stability'] +
            fairness_score * self.weights['fairness'] +
            efficiency_score * self.weights['efficiency']
        )
        
        # Apply manipulation penalty
        overall_score = overall_score * (1 - manipulation_risk / 200)
        
        # Determine market quality category
        if overall_score >= 80:
            market_quality = 'excellent'
        elif overall_score >= 60:
            market_quality = 'good'
        elif overall_score >= 40:
            market_quality = 'fair'
        else:
            market_quality = 'poor'
        
        # Generate key insights
        insights = self._generate_insights(
            liquidity_score, stability_score, fairness_score, 
            efficiency_score, manipulation_risk, institutional_presence
        )
        
        return MicrostructureScore(
            timestamp=timestamp,
            overall_score=overall_score,
            liquidity_score=liquidity_score,
            stability_score=stability_score,
            fairness_score=fairness_score,
            efficiency_score=efficiency_score,
            manipulation_risk=manipulation_risk,
            institutional_presence=institutional_presence,
            market_quality=market_quality,
            key_insights=insights,
            component_scores={
                'liquidity': liquidity_score,
                'stability': stability_score,
                'fairness': fairness_score,
                'efficiency': efficiency_score,
                'iceberg_activity': self._get_iceberg_activity_score(),
                'hft_impact': self._get_hft_impact_score(),
                'maker_quality': self._get_maker_quality_score()
            }
        )
    
    def _calculate_liquidity_score(self) -> float:
        """Calculate liquidity quality score"""
        
        score = 50.0  # Base score
        
        # Market maker contribution
        maker_metrics = self.maker_analyzer.get_market_quality_metrics()
        if maker_metrics['maker_count'] >= 3:
            score += 20
        elif maker_metrics['maker_count'] >= 1:
            score += 10
        
        # Spread tightness
        if maker_metrics.get('avg_spread', 5) < 2:
            score += 15
        elif maker_metrics.get('avg_spread', 5) < 3:
            score += 10
        elif maker_metrics.get('avg_spread', 5) > 5:
            score -= 10
        
        # Hidden liquidity presence
        hidden_liquidity = self.liquidity_scanner.get_hidden_liquidity_summary()
        if hidden_liquidity['total_detections'] > 0:
            score += min(15, hidden_liquidity['total_detections'] * 3)
        
        return min(100, max(0, score))
    
    def _calculate_stability_score(self) -> float:
        """Calculate market stability score"""
        
        score = 70.0  # Base score
        
        # HFT impact on stability
        hft_impact = self.hft_detector.get_hft_impact_analysis()
        if 'volatility_increase' in hft_impact:
            if hft_impact['volatility_increase'] > 50:
                score -= 20
            elif hft_impact['volatility_increase'] > 20:
                score -= 10
        
        # Quote stuffing impact
        stuffing_stats = self.stuffing_identifier.get_stuffing_statistics()
        if stuffing_stats['event_count'] > 5:
            score -= 15
        elif stuffing_stats['event_count'] > 2:
            score -= 10
        
        # Spread volatility
        maker_metrics = self.maker_analyzer.get_market_quality_metrics()
        if maker_metrics.get('spread_volatility', 0) > 2:
            score -= 10
        
        return min(100, max(0, score))
    
    def _calculate_fairness_score(self) -> float:
        """Calculate market fairness score"""
        
        score = 80.0  # Base score
        
        # Spoofing detection
        spoofing_stats = self.spoofing_detector.get_spoofing_statistics()
        if spoofing_stats['total_events'] > 10:
            score -= 30
        elif spoofing_stats['total_events'] > 5:
            score -= 20
        elif spoofing_stats['total_events'] > 0:
            score -= 10
        
        # Quote stuffing (unfair latency creation)
        is_stuffing, stuffing_type = self.stuffing_identifier.is_currently_stuffing()
        if is_stuffing:
            score -= 20
        
        # Two-sided market making
        maker_metrics = self.maker_analyzer.get_market_quality_metrics()
        if maker_metrics.get('improvement_rate', 0) > 0.2:
            score += 10
        
        return min(100, max(0, score))
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate market efficiency score"""
        
        score = 60.0  # Base score
        
        # Price discovery efficiency
        hft_activity = self.hft_detector.get_current_hft_activity()
        if hft_activity['active'] and hft_activity['dominant_type'] == 'arbitrage':
            score += 15  # Arbitrage improves efficiency
        
        # Hidden liquidity utilization
        hidden_summary = self.liquidity_scanner.get_hidden_liquidity_summary()
        if hidden_summary.get('price_improvement_events', 0) > 5:
            score += 10
        
        # Market maker competition
        maker_metrics = self.maker_analyzer.get_market_quality_metrics()
        if maker_metrics['competition_level'] == 'high':
            score += 15
        elif maker_metrics['competition_level'] == 'moderate':
            score += 10
        
        # Iceberg efficiency (smooth execution)
        active_icebergs = self.iceberg_detector.get_active_icebergs()
        if active_icebergs:
            score += 5
        
        return min(100, max(0, score))
    
    def _calculate_manipulation_risk(self) -> float:
        """Calculate overall manipulation risk score"""
        
        risk_score = 0.0
        
        # Spoofing risk
        spoofing_stats = self.spoofing_detector.get_spoofing_statistics()
        if spoofing_stats['total_events'] > 0:
            risk_score += min(40, spoofing_stats['total_events'] * 4)
        
        # Quote stuffing risk
        stuffing_stats = self.stuffing_identifier.get_stuffing_statistics()
        if stuffing_stats['event_count'] > 0:
            severity_weight = {
                'low': 5,
                'medium': 10,
                'high': 20,
                'extreme': 30
            }
            avg_severity = stuffing_stats.get('avg_severity', 'low')
            risk_score += severity_weight.get(avg_severity, 5)
        
        # Predatory HFT risk
        hft_activity = self.hft_detector.get_current_hft_activity()
        if hft_activity['active'] and hft_activity['dominant_type'] == 'predatory':
            risk_score += 25
        
        return min(100, risk_score)
    
    def _calculate_institutional_presence(self) -> float:
        """Calculate institutional activity presence"""
        
        presence_score = 0.0
        
        # Iceberg orders
        active_icebergs = self.iceberg_detector.get_active_icebergs()
        for iceberg in active_icebergs:
            presence_score += iceberg.institutional_probability * 20
        
        # Dark pool activity
        dark_pool_prob = self.liquidity_scanner.get_dark_pool_probability(
            (0, float('inf'))  # Full price range
        )
        presence_score += dark_pool_prob * 30
        
        # Large hidden orders
        hidden_liquidity = self.liquidity_scanner.get_hidden_liquidity_map()
        total_hidden = sum(hidden_liquidity['bid'].values()) + sum(hidden_liquidity['ask'].values())
        if total_hidden > 100000:
            presence_score += 20
        elif total_hidden > 50000:
            presence_score += 10
        
        return min(100, presence_score)
    
    def _generate_insights(self, liquidity: float, stability: float, 
                         fairness: float, efficiency: float,
                         manipulation_risk: float, institutional: float) -> List[str]:
        """Generate key insights from scores"""
        
        insights = []
        
        # Liquidity insights
        if liquidity < 40:
            insights.append("⚠️ Low liquidity - wider spreads expected")
        elif liquidity > 80:
            insights.append("✅ Excellent liquidity conditions")
        
        # Stability insights
        if stability < 50:
            insights.append("⚠️ High volatility detected in microstructure")
        
        # Fairness insights
        if fairness < 50:
            insights.append("🚨 Potential market manipulation detected")
        
        # Efficiency insights
        if efficiency > 70:
            insights.append("✅ Efficient price discovery in progress")
        
        # Manipulation risk
        if manipulation_risk > 60:
            insights.append("🚨 HIGH manipulation risk - trade with caution")
        elif manipulation_risk > 40:
            insights.append("⚠️ Moderate manipulation risk present")
        
        # Institutional activity
        if institutional > 70:
            insights.append("🏦 Strong institutional presence detected")
        elif institutional > 40:
            insights.append("🏦 Moderate institutional activity")
        
        # Market maker insights
        maker_metrics = self.maker_analyzer.get_market_quality_metrics()
        if maker_metrics['maker_count'] == 0:
            insights.append("⚠️ No active market makers detected")
        elif maker_metrics['competition_level'] == 'high':
            insights.append("✅ Healthy market maker competition")
        
        # HFT insights
        hft_activity = self.hft_detector.get_current_hft_activity()
        if hft_activity['active']:
            insights.append(f"🤖 HFT activity: {hft_activity['dominant_type']}")
        
        return insights
    
    def _get_iceberg_activity_score(self) -> float:
        """Get iceberg order activity score"""
        
        active_icebergs = self.iceberg_detector.get_active_icebergs()
        if not active_icebergs:
            return 0.0
        
        # Weight by confidence and recency
        total_score = sum(i.confidence * 100 for i in active_icebergs[:5])
        return min(100, total_score / 3)
    
    def _get_hft_impact_score(self) -> float:
        """Get HFT impact score (negative = bad impact)"""
        
        hft_impact = self.hft_detector.get_hft_impact_analysis()
        
        if 'volatility_increase' not in hft_impact:
            return 50.0  # Neutral
        
        # Negative impact from volatility increase
        volatility_impact = hft_impact['volatility_increase']
        
        if volatility_impact > 50:
            return 20.0
        elif volatility_impact > 20:
            return 35.0
        elif volatility_impact > 0:
            return 45.0
        else:
            return 60.0  # HFT reducing volatility
    
    def _get_maker_quality_score(self) -> float:
        """Get overall market maker quality score"""
        
        rankings = self.maker_analyzer.get_maker_rankings()
        
        if not rankings:
            return 0.0
        
        # Average quality score of top makers
        top_makers = rankings[:3]
        if top_makers:
            avg_quality = np.mean([m[1]['quality_score'] for m in top_makers])
            return avg_quality
        
        return 50.0
    
    def _check_alerts(self, score: MicrostructureScore):
        """Check for alert conditions"""
        
        alerts = []
        
        # Manipulation alert
        if score.manipulation_risk > 60:
            alerts.append({
                'timestamp': score.timestamp,
                'type': 'manipulation',
                'severity': 'high',
                'message': f"High manipulation risk detected: {score.manipulation_risk:.1f}%"
            })
        
        # Quality degradation alert
        if score.overall_score < 40:
            alerts.append({
                'timestamp': score.timestamp,
                'type': 'quality',
                'severity': 'high',
                'message': f"Poor market quality: {score.market_quality}"
            })
        
        # Institutional activity alert
        if score.institutional_presence > 80:
            alerts.append({
                'timestamp': score.timestamp,
                'type': 'institutional',
                'severity': 'info',
                'message': "Heavy institutional activity detected"
            })
        
        # Store alerts
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"Microstructure Alert: {alert['message']}")
    
    def get_current_state(self) -> MarketMicrostructureState:
        """Get current market microstructure state"""
        
        maker_metrics = self.maker_analyzer.get_market_quality_metrics()
        hft_activity = self.hft_detector.get_current_hft_activity()
        hidden_liquidity = self.liquidity_scanner.get_hidden_liquidity_summary()
        
        # Recent manipulation events
        spoofing_events = self.spoofing_detector.get_recent_spoofing_events(minutes=5)
        stuffing_stats = self.stuffing_identifier.get_stuffing_statistics(minutes=5)
        manipulation_count = len(spoofing_events) + stuffing_stats['event_count']
        
        return MarketMicrostructureState(
            timestamp=datetime.now(),
            spread=maker_metrics.get('avg_spread', 2.0),
            depth=maker_metrics.get('maker_count', 0) * 10000,  # Simplified
            volatility=maker_metrics.get('spread_volatility', 1.0),
            hft_intensity=hft_activity.get('intensity', 0.0),
            maker_count=maker_metrics.get('maker_count', 0),
            recent_manipulation_events=manipulation_count,
            hidden_liquidity_estimate=hidden_liquidity.get('estimated_hidden_volume', 0),
            institutional_flow_probability=self._calculate_institutional_presence() / 100
        )
    
    def get_trading_recommendations(self) -> Dict[str, Any]:
        """Get trading recommendations based on microstructure analysis"""
        
        if not self.score_history:
            return {'status': 'insufficient_data'}
        
        current_score = self.score_history[-1]
        current_state = self.get_current_state()
        
        recommendations = {
            'timestamp': datetime.now(),
            'market_quality': current_score.market_quality,
            'overall_score': current_score.overall_score,
            'can_trade': current_score.overall_score >= 40 and current_score.manipulation_risk < 60,
            'preferred_style': 'unknown',
            'size_recommendation': 'normal',
            'timing_recommendation': 'normal',
            'warnings': []
        }
        
        # Determine preferred trading style
        if current_score.efficiency_score > 70 and current_score.fairness_score > 70:
            recommendations['preferred_style'] = 'aggressive'
        elif current_score.manipulation_risk > 40:
            recommendations['preferred_style'] = 'defensive'
        else:
            recommendations['preferred_style'] = 'normal'
        
        # Size recommendations
        if current_state.hidden_liquidity_estimate > 100000:
            recommendations['size_recommendation'] = 'can_increase'
        elif current_score.liquidity_score < 40:
            recommendations['size_recommendation'] = 'reduce'
        
        # Timing recommendations
        if current_state.hft_intensity > 0.7:
            recommendations['timing_recommendation'] = 'avoid_micro_timing'
            recommendations['warnings'].append("High HFT activity - avoid competing on speed")
        
        if current_state.recent_manipulation_events > 5:
            recommendations['warnings'].append("Recent manipulation detected - exercise caution")
        
        if current_score.institutional_presence > 70:
            recommendations['warnings'].append("Heavy institutional flow - expect larger moves")
        
        return recommendations