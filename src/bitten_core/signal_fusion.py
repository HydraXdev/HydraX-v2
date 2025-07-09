"""
BITTEN Signal Fusion System
Combines all intelligence sources with confidence-based tiers
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ConfidenceTier(Enum):
    """Signal confidence tiers with quality thresholds"""
    SNIPER = "sniper"        # 90%+ confidence - Elite precision signals
    PRECISION = "precision"  # 80-89% confidence - High quality signals  
    RAPID = "rapid"          # 70-79% confidence - Standard signals
    TRAINING = "training"    # 60-69% confidence - Learning signals


@dataclass
class IntelSource:
    """Individual intelligence source data"""
    source_id: str
    source_type: str  # 'technical', 'sentiment', 'fundamental', 'ai_bot'
    signal: str       # 'BUY', 'SELL', 'NEUTRAL'
    confidence: float # 0-100
    weight: float     # Source weight in fusion
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FusedSignal:
    """Combined signal with multi-source fusion"""
    signal_id: str
    pair: str
    direction: str     # 'BUY', 'SELL'
    confidence: float  # 0-100 overall confidence
    tier: ConfidenceTier
    entry: float
    sl: float
    tp: float
    sources: List[IntelSource]
    fusion_scores: Dict[str, float]
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def agreement_score(self) -> float:
        """Calculate source agreement percentage"""
        if not self.sources:
            return 0.0
        
        direction_counts = defaultdict(int)
        for source in self.sources:
            direction_counts[source.signal] += 1
        
        max_agreement = max(direction_counts.values())
        return (max_agreement / len(self.sources)) * 100
    
    @property
    def source_diversity(self) -> float:
        """Calculate diversity of source types (0-1)"""
        if not self.sources:
            return 0.0
        
        source_types = set(s.source_type for s in self.sources)
        return len(source_types) / 4  # Assuming 4 main source types


class SignalQualityOptimizer:
    """Optimizes signal quality based on historical performance"""
    
    def __init__(self):
        self.performance_history = defaultdict(lambda: deque(maxlen=100))
        self.tier_stats = defaultdict(lambda: {'wins': 0, 'total': 0})
        self.source_reliability = defaultdict(lambda: deque(maxlen=50))
        
    def update_performance(self, signal: FusedSignal, result: bool):
        """Update performance metrics for signal and its sources"""
        # Update tier performance
        tier_key = signal.tier.value
        self.tier_stats[tier_key]['total'] += 1
        if result:
            self.tier_stats[tier_key]['wins'] += 1
        
        # Update source reliability
        for source in signal.sources:
            self.source_reliability[source.source_id].append(
                (source.confidence, result)
            )
        
        # Store performance data
        self.performance_history[signal.pair].append({
            'confidence': signal.confidence,
            'tier': signal.tier,
            'result': result,
            'agreement': signal.agreement_score,
            'diversity': signal.source_diversity
        })
    
    def get_tier_win_rate(self, tier: ConfidenceTier) -> float:
        """Get win rate for a specific tier"""
        stats = self.tier_stats[tier.value]
        if stats['total'] == 0:
            return 0.5  # Default 50%
        return stats['wins'] / stats['total']
    
    def get_source_reliability_score(self, source_id: str) -> float:
        """Calculate reliability score for a source"""
        history = list(self.source_reliability[source_id])
        if not history:
            return 0.7  # Default 70%
        
        # Weight recent performance more heavily
        weights = np.linspace(0.5, 1.0, len(history))
        weighted_sum = sum(w * (1 if result else 0) 
                          for w, (_, result) in zip(weights, history))
        return weighted_sum / weights.sum()
    
    def optimize_weights(self, sources: List[IntelSource]) -> Dict[str, float]:
        """Optimize source weights based on reliability"""
        optimized_weights = {}
        
        for source in sources:
            base_weight = source.weight
            reliability = self.get_source_reliability_score(source.source_id)
            
            # Adjust weight based on reliability
            optimized_weight = base_weight * (0.5 + reliability * 0.5)
            optimized_weights[source.source_id] = optimized_weight
        
        # Normalize weights
        total_weight = sum(optimized_weights.values())
        if total_weight > 0:
            for source_id in optimized_weights:
                optimized_weights[source_id] /= total_weight
        
        return optimized_weights


class SignalFusionEngine:
    """
    Main signal fusion engine that combines all intelligence sources
    Enhanced with TCS optimization integration
    """
    
    def __init__(self):
        self.quality_optimizer = SignalQualityOptimizer()
        self.active_signals = {}
        
        # Fusion parameters
        self.min_sources_required = 3
        self.tier_thresholds = {
            ConfidenceTier.SNIPER: 90,
            ConfidenceTier.PRECISION: 80,
            ConfidenceTier.RAPID: 70,
            ConfidenceTier.TRAINING: 60
        }
        
        # Dynamic TCS thresholds (updated by optimizer)
        self.dynamic_tcs_thresholds = {
            'EURUSD': 75.0,
            'GBPUSD': 75.0,
            'USDJPY': 75.0,
            'XAUUSD': 75.0,
            'AUDUSD': 75.0
        }
        
        # Source type weights (can be adjusted)
        self.source_type_weights = {
            'technical': 0.4,
            'sentiment': 0.2,
            'fundamental': 0.2,
            'ai_bot': 0.2
        }
        
        # TCS integration
        self.tcs_integration = None
    
    def set_tcs_integration(self, tcs_integration):
        """Set TCS integration layer"""
        self.tcs_integration = tcs_integration
        logger.info("TCS integration enabled for signal fusion")
    
    def update_tcs_threshold(self, pair: str, threshold: float):
        """Update dynamic TCS threshold for a pair"""
        self.dynamic_tcs_thresholds[pair] = threshold
        logger.info(f"Updated TCS threshold for {pair}: {threshold:.1f}%")
    
    def get_tcs_threshold(self, pair: str) -> float:
        """Get current TCS threshold for a pair"""
        return self.dynamic_tcs_thresholds.get(pair, 75.0)
        
    def fuse_signals(self, sources: List[IntelSource], pair: str) -> Optional[FusedSignal]:
        """
        Fuse multiple intelligence sources into a single high-confidence signal
        """
        if len(sources) < self.min_sources_required:
            logger.warning(f"Insufficient sources for fusion: {len(sources)}")
            return None
        
        # Get optimized weights
        optimized_weights = self.quality_optimizer.optimize_weights(sources)
        
        # Calculate fusion scores
        fusion_scores = self._calculate_fusion_scores(sources, optimized_weights)
        
        # Determine primary direction
        direction = self._determine_direction(sources, optimized_weights)
        if not direction:
            return None
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(sources, fusion_scores, optimized_weights)
        
        # Apply TCS filtering if integration is available
        if self.tcs_integration:
            tcs_threshold = self.get_tcs_threshold(pair)
            if confidence < tcs_threshold:
                logger.debug(f"Signal filtered by TCS: {confidence:.1f}% < {tcs_threshold:.1f}%")
                return None
        
        # Determine tier
        tier = self._determine_tier(confidence)
        if not tier:
            return None  # Below minimum threshold
        
        # Calculate entry, SL, TP
        entry, sl, tp = self._calculate_levels(sources, direction)
        
        # Create fused signal
        signal_id = f"FUSED_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pair}"
        
        fused_signal = FusedSignal(
            signal_id=signal_id,
            pair=pair,
            direction=direction,
            confidence=confidence,
            tier=tier,
            entry=entry,
            sl=sl,
            tp=tp,
            sources=sources,
            fusion_scores=fusion_scores,
            metadata={
                'agreement_score': 0,  # Will be calculated by property
                'source_diversity': 0,  # Will be calculated by property
                'optimization_applied': True,
                'tcs_threshold': self.get_tcs_threshold(pair) if self.tcs_integration else None,
                'tcs_filtered': self.tcs_integration is not None
            }
        )
        
        # Store active signal
        self.active_signals[signal_id] = fused_signal
        
        return fused_signal
    
    def _calculate_fusion_scores(self, sources: List[IntelSource], 
                                weights: Dict[str, float]) -> Dict[str, float]:
        """Calculate various fusion metrics"""
        scores = {}
        
        # Weighted confidence
        weighted_confidence = sum(
            source.confidence * weights.get(source.source_id, source.weight)
            for source in sources
        )
        scores['weighted_confidence'] = weighted_confidence
        
        # Source type coverage
        type_coverage = len(set(s.source_type for s in sources)) / len(self.source_type_weights)
        scores['type_coverage'] = type_coverage * 100
        
        # Confidence variance (lower is better)
        confidences = [s.confidence for s in sources]
        confidence_std = np.std(confidences) if len(confidences) > 1 else 0
        scores['confidence_consistency'] = max(0, 100 - confidence_std)
        
        # Time synchronization (how recent are the sources)
        now = datetime.now()
        time_deltas = [(now - s.timestamp).total_seconds() for s in sources]
        avg_age = np.mean(time_deltas)
        scores['time_sync'] = max(0, 100 - (avg_age / 60))  # Penalize per minute
        
        return scores
    
    def _determine_direction(self, sources: List[IntelSource], 
                           weights: Dict[str, float]) -> Optional[str]:
        """Determine consensus direction from sources"""
        direction_scores = defaultdict(float)
        
        for source in sources:
            weight = weights.get(source.source_id, source.weight)
            score = source.confidence * weight
            
            if source.signal in ['BUY', 'SELL']:
                direction_scores[source.signal] += score
        
        if not direction_scores:
            return None
        
        # Get highest scoring direction
        best_direction = max(direction_scores.items(), key=lambda x: x[1])
        
        # Require at least 60% weighted agreement
        total_score = sum(direction_scores.values())
        if best_direction[1] / total_score < 0.6:
            return None
        
        return best_direction[0]
    
    def _calculate_confidence(self, sources: List[IntelSource], 
                            fusion_scores: Dict[str, float],
                            weights: Dict[str, float]) -> float:
        """Calculate overall confidence score"""
        # Base confidence from weighted average
        base_confidence = fusion_scores['weighted_confidence']
        
        # Apply modifiers
        modifiers = []
        
        # Type coverage bonus (up to +5%)
        type_bonus = fusion_scores['type_coverage'] * 0.05
        modifiers.append(type_bonus)
        
        # Consistency bonus (up to +5%)
        consistency_bonus = fusion_scores['confidence_consistency'] * 0.05
        modifiers.append(consistency_bonus)
        
        # Time sync penalty (up to -10%)
        time_penalty = (100 - fusion_scores['time_sync']) * -0.1
        modifiers.append(time_penalty)
        
        # Agreement bonus
        direction_agreement = self._calculate_direction_agreement(sources)
        agreement_bonus = (direction_agreement - 60) * 0.2  # +0.2% per % above 60%
        modifiers.append(agreement_bonus)
        
        # Apply modifiers
        final_confidence = base_confidence + sum(modifiers)
        
        # Clamp to 0-100
        return max(0, min(100, final_confidence))
    
    def _calculate_direction_agreement(self, sources: List[IntelSource]) -> float:
        """Calculate percentage of sources agreeing on direction"""
        if not sources:
            return 0
        
        direction_counts = defaultdict(int)
        for source in sources:
            if source.signal in ['BUY', 'SELL']:
                direction_counts[source.signal] += 1
        
        if not direction_counts:
            return 0
        
        max_agreement = max(direction_counts.values())
        total_directional = sum(direction_counts.values())
        
        return (max_agreement / total_directional) * 100
    
    def _determine_tier(self, confidence: float) -> Optional[ConfidenceTier]:
        """Determine confidence tier based on score"""
        for tier in [ConfidenceTier.SNIPER, ConfidenceTier.PRECISION, 
                     ConfidenceTier.RAPID, ConfidenceTier.TRAINING]:
            if confidence >= self.tier_thresholds[tier]:
                return tier
        
        return None  # Below minimum threshold
    
    def _calculate_levels(self, sources: List[IntelSource], 
                         direction: str) -> Tuple[float, float, float]:
        """Calculate entry, stop loss, and take profit levels"""
        # Extract levels from sources that provide them
        entries = []
        sls = []
        tps = []
        
        for source in sources:
            meta = source.metadata
            if 'entry' in meta and meta['entry'] > 0:
                entries.append(meta['entry'])
            if 'sl' in meta and meta['sl'] > 0:
                sls.append(meta['sl'])
            if 'tp' in meta and meta['tp'] > 0:
                tps.append(meta['tp'])
        
        # Use median for robustness
        entry = np.median(entries) if entries else 0
        
        if direction == 'BUY':
            sl = min(sls) if sls else entry * 0.998  # 0.2% default SL
            tp = max(tps) if tps else entry * 1.004  # 0.4% default TP
        else:  # SELL
            sl = max(sls) if sls else entry * 1.002
            tp = min(tps) if tps else entry * 0.996
        
        return entry, sl, tp
    
    def get_tier_stats(self) -> Dict[str, Any]:
        """Get performance statistics for each tier"""
        stats = {}
        
        for tier in ConfidenceTier:
            tier_data = self.quality_optimizer.tier_stats[tier.value]
            win_rate = self.quality_optimizer.get_tier_win_rate(tier)
            
            stats[tier.value] = {
                'name': tier.name,
                'threshold': self.tier_thresholds[tier],
                'total_signals': tier_data['total'],
                'wins': tier_data['wins'],
                'win_rate': win_rate,
                'active_signals': sum(1 for s in self.active_signals.values() 
                                    if s.tier == tier)
            }
        
        return stats
    
    def get_tcs_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced statistics with TCS integration data"""
        base_stats = self.get_tier_stats()
        
        # Add TCS-specific statistics
        tcs_stats = {
            'tcs_thresholds': self.dynamic_tcs_thresholds.copy(),
            'tcs_integration_active': self.tcs_integration is not None,
            'signals_filtered_by_tcs': 0,  # Would be tracked in practice
            'avg_tcs_threshold': sum(self.dynamic_tcs_thresholds.values()) / len(self.dynamic_tcs_thresholds),
            'threshold_adjustments_today': 0  # Would be tracked in practice
        }
        
        # Add pair-specific TCS performance
        pair_tcs_stats = {}
        for pair, threshold in self.dynamic_tcs_thresholds.items():
            pair_signals = [s for s in self.active_signals.values() if s.pair == pair]
            pair_tcs_stats[pair] = {
                'current_threshold': threshold,
                'active_signals': len(pair_signals),
                'avg_confidence': np.mean([s.confidence for s in pair_signals]) if pair_signals else 0,
                'signals_above_threshold': len([s for s in pair_signals if s.confidence >= threshold])
            }
        
        return {
            'tier_stats': base_stats,
            'tcs_stats': tcs_stats,
            'pair_tcs_stats': pair_tcs_stats
        }


class TierBasedRouter:
    """
    Routes signals to users based on their tier limits
    Ensures Nibbler gets best 6, Fang gets best 10, etc.
    """
    
    def __init__(self):
        self.tier_limits = {
            'nibbler': 6,
            'fang': 10,
            'commander': 15,
            'apex': 20  # Unlimited in practice
        }
        
        self.user_signal_counts = defaultdict(lambda: defaultdict(int))
        self.daily_reset_time = None
        
    def route_signal(self, signal: FusedSignal, user_tier: str) -> bool:
        """
        Determine if signal should be routed to user based on tier
        Returns True if signal should be sent
        """
        self._check_daily_reset()
        
        # Get user's current signal count for today
        today = datetime.now().date()
        current_count = self.user_signal_counts[user_tier][today]
        
        # Check if user has reached limit
        limit = self.tier_limits.get(user_tier, 0)
        if current_count >= limit:
            return False
        
        # For lower tiers, only send higher confidence signals
        if user_tier == 'nibbler':
            # Nibbler gets SNIPER, PRECISION, and RAPID signals with 70%+ confidence
            if signal.tier not in [ConfidenceTier.SNIPER, ConfidenceTier.PRECISION, ConfidenceTier.RAPID]:
                return False
            if signal.tier == ConfidenceTier.PRECISION and signal.confidence < 80:
                return False
            if signal.tier == ConfidenceTier.RAPID and signal.confidence < 70:
                return False
        
        elif user_tier == 'fang':
            # Fang gets SNIPER, PRECISION, and top RAPID
            if signal.tier == ConfidenceTier.TRAINING:
                return False
            if signal.tier == ConfidenceTier.RAPID and signal.confidence < 75:
                return False
        
        # Increment count and allow signal
        self.user_signal_counts[user_tier][today] += 1
        return True
    
    def _check_daily_reset(self):
        """Reset daily counters at midnight"""
        now = datetime.now()
        if self.daily_reset_time is None or now.date() > self.daily_reset_time.date():
            self.user_signal_counts.clear()
            self.daily_reset_time = now
    
    def get_user_stats(self, user_tier: str) -> Dict[str, Any]:
        """Get routing statistics for a user tier"""
        today = datetime.now().date()
        current_count = self.user_signal_counts[user_tier][today]
        limit = self.tier_limits.get(user_tier, 0)
        
        return {
            'tier': user_tier,
            'daily_limit': limit,
            'signals_today': current_count,
            'remaining': max(0, limit - current_count),
            'limit_reached': current_count >= limit
        }


class EngagementBalancer:
    """
    Balances signal distribution to maintain user engagement
    """
    
    def __init__(self):
        self.user_last_signal = {}
        self.user_signal_history = defaultdict(lambda: deque(maxlen=50))
        
        # Engagement parameters
        self.min_time_between_signals = {
            'nibbler': timedelta(hours=2),
            'fang': timedelta(hours=1.5),
            'commander': timedelta(hours=1),
            'apex': timedelta(minutes=30)
        }
        
        self.quality_distribution_targets = {
            'nibbler': {'sniper': 0.5, 'precision': 0.5},
            'fang': {'sniper': 0.3, 'precision': 0.5, 'rapid': 0.2},
            'commander': {'sniper': 0.2, 'precision': 0.4, 'rapid': 0.3, 'training': 0.1},
            'apex': {'sniper': 0.15, 'precision': 0.35, 'rapid': 0.35, 'training': 0.15}
        }
    
    def should_send_signal(self, signal: FusedSignal, user_id: str, 
                          user_tier: str) -> Tuple[bool, str]:
        """
        Check if signal should be sent based on engagement rules
        Returns (should_send, reason)
        """
        # Check minimum time between signals
        if user_id in self.user_last_signal:
            time_since_last = datetime.now() - self.user_last_signal[user_id]
            min_time = self.min_time_between_signals.get(user_tier, timedelta(hours=1))
            
            if time_since_last < min_time:
                return False, f"Too soon since last signal ({time_since_last.total_seconds()/60:.0f} min ago)"
        
        # Check quality distribution
        history = list(self.user_signal_history[user_id])
        if len(history) >= 10:  # Need enough history
            tier_counts = defaultdict(int)
            for hist_signal in history[-10:]:
                tier_counts[hist_signal['tier']] += 1
            
            # Calculate current distribution
            total = sum(tier_counts.values())
            current_dist = {tier: count/total for tier, count in tier_counts.items()}
            
            # Check if adding this signal would skew distribution too much
            targets = self.quality_distribution_targets.get(user_tier, {})
            signal_tier = signal.tier.value
            
            if signal_tier in targets:
                current_ratio = current_dist.get(signal_tier, 0)
                target_ratio = targets[signal_tier]
                
                # Allow 20% deviation from target
                if current_ratio > target_ratio * 1.2:
                    return False, f"Too many {signal_tier} signals recently"
        
        return True, "OK"
    
    def record_signal_sent(self, signal: FusedSignal, user_id: str):
        """Record that a signal was sent to user"""
        self.user_last_signal[user_id] = datetime.now()
        self.user_signal_history[user_id].append({
            'signal_id': signal.signal_id,
            'tier': signal.tier.value,
            'confidence': signal.confidence,
            'timestamp': datetime.now()
        })
    
    def get_user_engagement_stats(self, user_id: str) -> Dict[str, Any]:
        """Get engagement statistics for a user"""
        history = list(self.user_signal_history[user_id])
        
        if not history:
            return {
                'total_signals': 0,
                'tier_distribution': {},
                'avg_confidence': 0,
                'last_signal': None
            }
        
        # Calculate tier distribution
        tier_counts = defaultdict(int)
        confidence_sum = 0
        
        for signal in history:
            tier_counts[signal['tier']] += 1
            confidence_sum += signal['confidence']
        
        total = len(history)
        
        return {
            'total_signals': total,
            'tier_distribution': {
                tier: count/total for tier, count in tier_counts.items()
            },
            'avg_confidence': confidence_sum / total,
            'last_signal': self.user_last_signal.get(user_id),
            'signals_last_24h': sum(
                1 for s in history 
                if datetime.now() - s['timestamp'] < timedelta(hours=24)
            )
        }


# Global instances
signal_fusion_engine = SignalFusionEngine()
tier_router = TierBasedRouter()
engagement_balancer = EngagementBalancer()