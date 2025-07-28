"""
Shield Scoring Engine - Core CITADEL scoring algorithm

Purpose: Calculate comprehensive shield scores (0-10) based on all analysis modules,
providing transparent and explainable protection ratings for each signal.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScoreComponent:
    """Individual scoring component with explanation"""
    name: str
    value: float
    max_value: float
    reason: str
    category: str  # 'positive', 'negative', 'neutral'


class ShieldScoringEngine:
    """
    Central scoring engine that combines all CITADEL analysis modules
    to produce a final shield score with full transparency.
    """
    
    def __init__(self):
        # Scoring weights for different components
        self.weights = {
            'liquidity': 3.0,      # Liquidity analysis is critical
            'timeframe': 2.5,      # Multi-TF alignment very important
            'regime': 2.0,         # Market conditions matter
            'signal': 1.5,         # Signal quality baseline
            'timing': 1.0          # Entry timing factors
        }
        
        # Shield classification thresholds
        self.thresholds = {
            'approved': 8.0,       # 🛡️ Shield Approved
            'active': 6.0,         # ✅ Shield Active
            'caution': 4.0,        # ⚠️ Volatility Zone
            'unverified': 0.0      # 🔍 Unverified
        }
        
        # Risk factor penalties
        self.risk_penalties = {
            'news_high_impact': -2.0,
            'trap_high_probability': -2.5,
            'volatility_extreme': -1.5,
            'timeframe_conflicts': -1.0,
            'low_liquidity_session': -0.5
        }
        
        # Positive factors bonuses
        self.quality_bonuses = {
            'post_sweep_entry': 2.0,
            'strong_tf_alignment': 1.5,
            'trend_continuation': 1.0,
            'key_level_confluence': 1.0,
            'optimal_session': 0.5
        }
    
    def calculate_score(self, signal_analysis: Dict[str, Any], 
                       market_regime: Dict[str, Any],
                       liquidity_analysis: Dict[str, Any],
                       tf_validation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive shield score based on all analyses.
        
        Args:
            signal_analysis: Results from SignalInspector
            market_regime: Results from MarketRegimeAnalyzer
            liquidity_analysis: Results from LiquidityMapper
            tf_validation: Results from CrossTimeframeValidator
            
        Returns:
            Dict containing score, classification, and detailed breakdown
        """
        try:
            # Initialize score components
            components = []
            
            # 1. Signal Quality Component
            signal_components = self._score_signal_quality(signal_analysis)
            components.extend(signal_components)
            
            # 2. Liquidity Component
            liquidity_components = self._score_liquidity(liquidity_analysis)
            components.extend(liquidity_components)
            
            # 3. Market Regime Component
            regime_components = self._score_market_regime(market_regime)
            components.extend(regime_components)
            
            # 4. Timeframe Alignment Component
            tf_components = self._score_timeframe_alignment(tf_validation)
            components.extend(tf_components)
            
            # 5. Timing Component
            timing_components = self._score_timing_factors(market_regime, signal_analysis)
            components.extend(timing_components)
            
            # Calculate base score
            base_score = self._calculate_base_score(components)
            
            # Apply risk penalties
            risk_factors = self._identify_risk_factors(
                signal_analysis, market_regime, liquidity_analysis, tf_validation
            )
            
            # Apply quality bonuses
            quality_factors = self._identify_quality_factors(
                signal_analysis, market_regime, liquidity_analysis, tf_validation
            )
            
            # Calculate final score
            final_score = self._calculate_final_score(
                base_score, risk_factors, quality_factors
            )
            
            # Determine classification
            classification = self._classify_shield_status(final_score)
            
            # Generate explanation
            explanation = self._generate_explanation(
                components, risk_factors, quality_factors, final_score
            )
            
            result = {
                'shield_score': round(final_score, 1),
                'base_score': round(base_score, 1),
                'classification': classification,
                'label': self._get_shield_label(classification),
                'emoji': self._get_shield_emoji(classification),
                'components': self._format_components(components),
                'risk_factors': risk_factors,
                'quality_factors': quality_factors,
                'explanation': explanation,
                'confidence': self._calculate_confidence(components, final_score),
                'recommendation': self._generate_recommendation(
                    classification, final_score, risk_factors
                )
            }
            
            logger.info(f"Shield score calculated: {final_score:.1f} ({classification})")
            return result
            
        except Exception as e:
            logger.error(f"Shield scoring error: {str(e)}")
            return self._get_default_score()
    
    def _score_signal_quality(self, analysis: Dict[str, Any]) -> List[ScoreComponent]:
        """Score signal quality components."""
        components = []
        
        # Signal strength
        strength_map = {'STRONG': 1.5, 'MODERATE': 1.0, 'WEAK': 0.5, 'VERY_WEAK': 0}
        strength = analysis.get('signal_strength', 'MODERATE')
        components.append(ScoreComponent(
            name='Signal Strength',
            value=strength_map.get(strength, 0.5),
            max_value=1.5,
            reason=f"{strength.replace('_', ' ').lower()} signal pattern",
            category='positive' if strength in ['STRONG', 'MODERATE'] else 'negative'
        ))
        
        # Risk/Reward ratio
        rr_ratio = analysis.get('risk_reward_ratio', 0)
        rr_score = min(rr_ratio / 3.0, 1.0)  # Max score at 1:3 or better
        components.append(ScoreComponent(
            name='Risk/Reward',
            value=rr_score,
            max_value=1.0,
            reason=f"1:{rr_ratio:.1f} risk/reward ratio",
            category='positive' if rr_ratio >= 2 else 'negative'
        ))
        
        # Entry structure quality
        if analysis.get('entry_structure', '').lower().count('confluence') > 0:
            components.append(ScoreComponent(
                name='Entry Structure',
                value=0.5,
                max_value=0.5,
                reason="Multi-timeframe confluence detected",
                category='positive'
            ))
        
        return components
    
    def _score_liquidity(self, analysis: Dict[str, Any]) -> List[ScoreComponent]:
        """Score liquidity-related components."""
        components = []
        
        # Liquidity sweep bonus
        if analysis.get('sweep_detected'):
            sweep_quality = analysis.get('sweep_quality', 'low')
            quality_scores = {'high': 2.0, 'medium': 1.5, 'low': 1.0}
            components.append(ScoreComponent(
                name='Liquidity Sweep',
                value=quality_scores.get(sweep_quality, 1.0),
                max_value=2.0,
                reason=f"{sweep_quality.title()} quality sweep detected",
                category='positive'
            ))
        
        # Trap probability penalty
        trap_prob = analysis.get('trap_probability', 'UNKNOWN')
        if trap_prob in ['HIGH', 'MEDIUM']:
            penalty = -1.5 if trap_prob == 'HIGH' else -0.75
            components.append(ScoreComponent(
                name='Trap Risk',
                value=penalty,
                max_value=0,
                reason=f"{trap_prob.lower()} probability of retail trap",
                category='negative'
            ))
        
        # Order block proximity
        if analysis.get('order_block_nearby'):
            components.append(ScoreComponent(
                name='Order Block',
                value=0.5,
                max_value=0.5,
                reason="Near institutional order block",
                category='positive'
            ))
        
        # Psychological level
        psych_level = analysis.get('psychological_level', {})
        if psych_level.get('at_level') and psych_level.get('strength') in ['major', 'strong']:
            components.append(ScoreComponent(
                name='Psychological Level',
                value=0.5,
                max_value=0.5,
                reason=f"At {psych_level['strength']} psychological level",
                category='neutral'
            ))
        
        return components
    
    def _score_market_regime(self, analysis: Dict[str, Any]) -> List[ScoreComponent]:
        """Score market regime components."""
        components = []
        
        # Regime favorability
        regime = analysis.get('regime', 'undefined')
        favorable_regimes = ['trending_bull', 'trending_bear', 'breakout']
        if regime in favorable_regimes:
            components.append(ScoreComponent(
                name='Market Regime',
                value=1.0,
                max_value=1.0,
                reason=f"Favorable {regime.replace('_', ' ')} regime",
                category='positive'
            ))
        elif regime == 'ranging_volatile':
            components.append(ScoreComponent(
                name='Market Regime',
                value=-0.5,
                max_value=0,
                reason="Volatile ranging conditions",
                category='negative'
            ))
        
        # Volatility assessment
        vol_level = analysis.get('volatility', 'normal')
        if vol_level == 'high':
            components.append(ScoreComponent(
                name='Volatility',
                value=-0.5,
                max_value=0,
                reason="High volatility environment",
                category='negative'
            ))
        elif vol_level == 'low':
            components.append(ScoreComponent(
                name='Volatility',
                value=0.25,
                max_value=0.25,
                reason="Low volatility (stable conditions)",
                category='positive'
            ))
        
        # Session quality
        session = analysis.get('session', 'unknown')
        session_chars = analysis.get('session_characteristics', {})
        if session_chars.get('is_optimal_pair'):
            components.append(ScoreComponent(
                name='Session Timing',
                value=0.5,
                max_value=0.5,
                reason=f"Optimal pair for {session} session",
                category='positive'
            ))
        
        return components
    
    def _score_timeframe_alignment(self, analysis: Dict[str, Any]) -> List[ScoreComponent]:
        """Score timeframe alignment components."""
        components = []
        
        # Overall alignment score
        alignment_score = analysis.get('alignment_score', 0)
        normalized_score = alignment_score / 10.0 * 2.0  # Normalize to max 2.0
        components.append(ScoreComponent(
            name='TF Alignment',
            value=normalized_score,
            max_value=2.0,
            reason=f"{analysis.get('total_aligned', 0)}/4 timeframes aligned",
            category='positive' if alignment_score >= 6 else 'negative'
        ))
        
        # Conflicts penalty
        conflicts = analysis.get('conflicts', [])
        if conflicts:
            penalty = -0.5 * min(len(conflicts), 2)  # Max -1.0 penalty
            components.append(ScoreComponent(
                name='TF Conflicts',
                value=penalty,
                max_value=0,
                reason=f"{len(conflicts)} timeframe conflict(s)",
                category='negative'
            ))
        
        # Confluences bonus
        confluences = analysis.get('confluences', [])
        if confluences:
            bonus = 0.25 * min(len(confluences), 2)  # Max 0.5 bonus
            components.append(ScoreComponent(
                name='TF Confluences',
                value=bonus,
                max_value=0.5,
                reason=f"{len(confluences)} positive confluence(s)",
                category='positive'
            ))
        
        return components
    
    def _score_timing_factors(self, regime: Dict[str, Any], 
                            signal: Dict[str, Any]) -> List[ScoreComponent]:
        """Score timing-related factors."""
        components = []
        
        # News risk
        news_risk = regime.get('news_risk', '🟢')
        if news_risk == '🔴':
            components.append(ScoreComponent(
                name='News Risk',
                value=-1.0,
                max_value=0,
                reason="High-impact news event approaching",
                category='negative'
            ))
        elif news_risk == '🟡':
            components.append(ScoreComponent(
                name='News Risk',
                value=-0.5,
                max_value=0,
                reason="Medium-impact news consideration",
                category='negative'
            ))
        
        # Volatility zone timing
        if signal.get('volatility_zone'):
            components.append(ScoreComponent(
                name='Volatility Timing',
                value=-0.5,
                max_value=0,
                reason="Entry in high volatility zone",
                category='negative'
            ))
        
        return components
    
    def _calculate_base_score(self, components: List[ScoreComponent]) -> float:
        """Calculate base score from all components."""
        # Start with neutral score
        base_score = 5.0
        
        # Add all component values
        for component in components:
            base_score += component.value
        
        # Ensure score stays within bounds
        return max(0, min(10, base_score))
    
    def _identify_risk_factors(self, signal_analysis: Dict, regime: Dict,
                             liquidity: Dict, tf: Dict) -> List[Dict[str, Any]]:
        """Identify all risk factors present."""
        risk_factors = []
        
        # Check each risk condition
        if regime.get('news_risk') == '🔴':
            risk_factors.append({
                'factor': 'news_high_impact',
                'penalty': self.risk_penalties['news_high_impact'],
                'description': 'High-impact news event within 90 minutes'
            })
        
        if liquidity.get('trap_probability') == 'HIGH':
            risk_factors.append({
                'factor': 'trap_high_probability',
                'penalty': self.risk_penalties['trap_high_probability'],
                'description': 'High probability of liquidity trap'
            })
        
        if regime.get('volatility') == 'high' and regime.get('volatility_percentile', 0) > 85:
            risk_factors.append({
                'factor': 'volatility_extreme',
                'penalty': self.risk_penalties['volatility_extreme'],
                'description': 'Extreme volatility conditions'
            })
        
        if len(tf.get('conflicts', [])) >= 2:
            risk_factors.append({
                'factor': 'timeframe_conflicts',
                'penalty': self.risk_penalties['timeframe_conflicts'],
                'description': 'Multiple timeframe conflicts'
            })
        
        session = regime.get('session', '')
        if session in ['asian', 'weekend']:
            risk_factors.append({
                'factor': 'low_liquidity_session',
                'penalty': self.risk_penalties['low_liquidity_session'],
                'description': f'Low liquidity {session} session'
            })
        
        return risk_factors
    
    def _identify_quality_factors(self, signal_analysis: Dict, regime: Dict,
                                liquidity: Dict, tf: Dict) -> List[Dict[str, Any]]:
        """Identify all quality bonus factors."""
        quality_factors = []
        
        # Post-sweep entry
        if liquidity.get('sweep_detected') and liquidity.get('time_since_sweep', 99) <= 3:
            quality_factors.append({
                'factor': 'post_sweep_entry',
                'bonus': self.quality_bonuses['post_sweep_entry'],
                'description': 'Entry after liquidity sweep'
            })
        
        # Strong timeframe alignment
        if tf.get('alignment_quality') in ['EXCELLENT', 'GOOD']:
            quality_factors.append({
                'factor': 'strong_tf_alignment',
                'bonus': self.quality_bonuses['strong_tf_alignment'],
                'description': f"{tf['alignment_quality'].title()} multi-TF alignment"
            })
        
        # Trend continuation
        if (signal_analysis.get('signal_type') == 'CONTINUATION' and 
            regime.get('trend_strength', 0) >= 3):
            quality_factors.append({
                'factor': 'trend_continuation',
                'bonus': self.quality_bonuses['trend_continuation'],
                'description': 'Strong trend continuation setup'
            })
        
        # Key level confluence
        if (liquidity.get('psychological_level', {}).get('at_level') and
            liquidity.get('order_block_nearby')):
            quality_factors.append({
                'factor': 'key_level_confluence',
                'bonus': self.quality_bonuses['key_level_confluence'],
                'description': 'Multiple key level confluence'
            })
        
        # Optimal session
        session_chars = regime.get('session_characteristics', {})
        if session_chars.get('is_optimal_pair') and session_chars.get('typical_range') == 'high':
            quality_factors.append({
                'factor': 'optimal_session',
                'bonus': self.quality_bonuses['optimal_session'],
                'description': 'Optimal session for this pair'
            })
        
        return quality_factors
    
    def _calculate_final_score(self, base_score: float, risk_factors: List[Dict],
                             quality_factors: List[Dict]) -> float:
        """Calculate final score with all adjustments."""
        final_score = base_score
        
        # Apply risk penalties
        for risk in risk_factors:
            final_score += risk['penalty']
        
        # Apply quality bonuses
        for quality in quality_factors:
            final_score += quality['bonus']
        
        # Ensure bounds
        return max(0, min(10, final_score))
    
    def _classify_shield_status(self, score: float) -> str:
        """Classify shield status based on score."""
        if score >= self.thresholds['approved']:
            return 'SHIELD_APPROVED'
        elif score >= self.thresholds['active']:
            return 'SHIELD_ACTIVE'
        elif score >= self.thresholds['caution']:
            return 'VOLATILITY_ZONE'
        else:
            return 'UNVERIFIED'
    
    def _get_shield_label(self, classification: str) -> str:
        """Get human-readable shield label."""
        labels = {
            'SHIELD_APPROVED': 'SHIELD APPROVED',
            'SHIELD_ACTIVE': 'SHIELD ACTIVE',
            'VOLATILITY_ZONE': 'VOLATILITY ZONE',
            'UNVERIFIED': 'UNVERIFIED'
        }
        return labels.get(classification, 'UNKNOWN')
    
    def _get_shield_emoji(self, classification: str) -> str:
        """Get shield emoji for classification."""
        emojis = {
            'SHIELD_APPROVED': '🛡️',
            'SHIELD_ACTIVE': '✅',
            'VOLATILITY_ZONE': '⚠️',
            'UNVERIFIED': '🔍'
        }
        return emojis.get(classification, '❓')
    
    def _format_components(self, components: List[ScoreComponent]) -> List[Dict]:
        """Format components for output."""
        return [
            {
                'name': comp.name,
                'score': round(comp.value, 2),
                'max_score': comp.max_value,
                'reason': comp.reason,
                'impact': comp.category
            }
            for comp in components
        ]
    
    def _generate_explanation(self, components: List[ScoreComponent],
                            risk_factors: List[Dict], quality_factors: List[Dict],
                            final_score: float) -> str:
        """Generate human-readable explanation of score."""
        explanations = []
        
        # Top positive factors
        positive_comps = sorted(
            [c for c in components if c.category == 'positive' and c.value > 0.5],
            key=lambda x: x.value, reverse=True
        )[:2]
        
        if positive_comps:
            explanations.append(
                "Strengths: " + ", ".join([c.reason for c in positive_comps])
            )
        
        # Top negative factors
        negative_comps = sorted(
            [c for c in components if c.category == 'negative'],
            key=lambda x: x.value
        )[:2]
        
        if negative_comps:
            explanations.append(
                "Cautions: " + ", ".join([c.reason for c in negative_comps])
            )
        
        # Major bonuses/penalties
        if quality_factors:
            explanations.append(
                "Bonuses: " + quality_factors[0]['description']
            )
        
        if risk_factors:
            explanations.append(
                "Risks: " + risk_factors[0]['description']
            )
        
        return " | ".join(explanations)
    
    def _calculate_confidence(self, components: List[ScoreComponent], 
                            score: float) -> float:
        """Calculate confidence in the score."""
        # Base confidence on score stability
        if score >= 8 or score <= 2:
            confidence = 0.9  # Very clear signal
        elif 6 <= score < 8 or 2 < score <= 4:
            confidence = 0.7  # Moderate clarity
        else:
            confidence = 0.5  # Borderline signal
        
        # Adjust for component agreement
        positive_count = sum(1 for c in components if c.category == 'positive')
        negative_count = sum(1 for c in components if c.category == 'negative')
        
        if positive_count > negative_count * 2 or negative_count > positive_count * 2:
            confidence += 0.1  # Strong consensus
        
        return min(1.0, confidence)
    
    def _generate_recommendation(self, classification: str, score: float,
                               risk_factors: List[Dict]) -> str:
        """Generate trading recommendation."""
        if classification == 'SHIELD_APPROVED':
            if score >= 9:
                return "Exceptional setup - Full position size recommended"
            else:
                return "High-quality setup - Standard position size"
        elif classification == 'SHIELD_ACTIVE':
            if len(risk_factors) == 0:
                return "Good setup with minor cautions - Consider 75% position"
            else:
                return "Decent setup but monitor risks - Consider 50% position"
        elif classification == 'VOLATILITY_ZONE':
            return "Trade with caution - Reduce position size or wait for improvement"
        else:
            return "Low confidence setup - Consider skipping or paper trade only"
    
    def _get_default_score(self) -> Dict[str, Any]:
        """Return default score when error occurs."""
        return {
            'shield_score': 5.0,
            'base_score': 5.0,
            'classification': 'UNVERIFIED',
            'label': 'UNVERIFIED',
            'emoji': '🔍',
            'components': [],
            'risk_factors': [],
            'quality_factors': [],
            'explanation': 'Unable to calculate shield score',
            'confidence': 0.0,
            'recommendation': 'Cannot assess - missing data'
        }


# Example usage
if __name__ == "__main__":
    engine = ShieldScoringEngine()
    
    # Test with sample analysis results
    test_signal = {
        'signal_strength': 'STRONG',
        'risk_reward_ratio': 2.5,
        'entry_structure': 'Retest of M15 resistance with H1 confluence',
        'volatility_zone': False,
        'trap_risk': 'LOW'
    }
    
    test_regime = {
        'regime': 'trending_bear',
        'trend_strength': 4,
        'volatility': 'normal',
        'volatility_percentile': 45,
        'session': 'london',
        'session_characteristics': {'is_optimal_pair': True, 'typical_range': 'high'},
        'news_risk': '🟢'
    }
    
    test_liquidity = {
        'sweep_detected': True,
        'sweep_quality': 'high',
        'time_since_sweep': 2,
        'trap_probability': 'LOW',
        'order_block_nearby': True,
        'psychological_level': {'at_level': True, 'strength': 'strong'}
    }
    
    test_tf = {
        'total_aligned': 3,
        'alignment_score': 7.5,
        'alignment_quality': 'GOOD',
        'conflicts': [],
        'confluences': ['Strong trend alignment (3/4 TFs)']
    }
    
    result = engine.calculate_score(test_signal, test_regime, test_liquidity, test_tf)
    print(f"\nShield Score: {result['shield_score']}/10")
    print(f"Classification: {result['emoji']} {result['label']}")
    print(f"Explanation: {result['explanation']}")
    print(f"Recommendation: {result['recommendation']}")