"""
Cross Timeframe Validator - Multi-timeframe alignment confirmation

Purpose: Validate signal alignment across multiple timeframes (M5, M15, H1, H4)
to ensure institutional-grade entry confirmation.
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TimeFrame(Enum):
    """Timeframe classifications"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


class TrendDirection(Enum):
    """Trend direction classifications"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class CrossTimeframeValidator:
    """
    Validates trading signals across multiple timeframes to ensure
    alignment with higher timeframe trends and structures.
    """
    
    def __init__(self):
        # Timeframe hierarchy for validation
        self.tf_hierarchy = [
            TimeFrame.M5,
            TimeFrame.M15,
            TimeFrame.H1,
            TimeFrame.H4
        ]
        
        # Minimum alignment requirements by signal type
        self.alignment_requirements = {
            'TREND_FOLLOWING': 3,  # Need 3/4 timeframes aligned
            'REVERSAL': 2,         # Need 2/4 timeframes showing exhaustion
            'SCALP': 2,           # Need 2/4 timeframes permissive
            'SWING': 3            # Need 3/4 timeframes strongly aligned
        }
        
    def validate(self, signal: Dict[str, Any], tf_data: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Validate signal across multiple timeframes.
        
        Args:
            signal: Trading signal with direction and type
            tf_data: Dict of timeframe data (e.g., {'M5': {...}, 'M15': {...}})
            
        Returns:
            Dict containing validation results for each timeframe
        """
        try:
            direction = signal.get('direction', '')
            signal_type = self._determine_signal_type(signal)
            
            # Analyze each timeframe
            tf_analysis = {}
            for tf in self.tf_hierarchy:
                tf_key = tf.value
                if tf_key in tf_data:
                    tf_analysis[tf_key] = self._analyze_timeframe(
                        tf_data[tf_key], direction, tf
                    )
                else:
                    tf_analysis[tf_key] = self._get_default_tf_analysis()
            
            # Calculate alignment scores
            alignment_results = self._calculate_alignment(tf_analysis, direction)
            
            # Determine if signal passes validation
            passes_validation = self._check_validation_rules(
                alignment_results, signal_type
            )
            
            # Identify conflicts and confluences
            conflicts = self._identify_conflicts(tf_analysis, direction)
            confluences = self._identify_confluences(tf_analysis)
            
            result = {
                'm5_confirmed': tf_analysis.get('M5', {}).get('aligned', False),
                'm15_confirmed': tf_analysis.get('M15', {}).get('aligned', False),
                'h1_confirmed': tf_analysis.get('H1', {}).get('aligned', False),
                'h4_confirmed': tf_analysis.get('H4', {}).get('aligned', False),
                'h4_conflict': tf_analysis.get('H4', {}).get('conflict', False),
                'total_aligned': alignment_results['aligned_count'],
                'alignment_score': alignment_results['score'],
                'alignment_quality': alignment_results['quality'],
                'passes_validation': passes_validation,
                'conflicts': conflicts,
                'confluences': confluences,
                'tf_details': tf_analysis,
                'recommendation': self._generate_recommendation(
                    alignment_results, conflicts, signal_type
                )
            }
            
            logger.info(f"Cross-TF validation: {alignment_results['aligned_count']}/4 aligned, "
                       f"quality={alignment_results['quality']}")
            return result
            
        except Exception as e:
            logger.error(f"Cross-timeframe validation error: {str(e)}")
            return self._get_default_validation()
    
    def _determine_signal_type(self, signal: Dict[str, Any]) -> str:
        """Determine the type of signal for validation rules."""
        # Can be enhanced with actual signal classification
        signal_type_hint = signal.get('signal_type', '')
        
        if 'REVERSAL' in signal_type_hint.upper():
            return 'REVERSAL'
        elif 'SCALP' in signal_type_hint.upper():
            return 'SCALP'
        elif 'SWING' in signal_type_hint.upper():
            return 'SWING'
        else:
            return 'TREND_FOLLOWING'
    
    def _analyze_timeframe(self, tf_data: Dict[str, Any], signal_direction: str,
                          timeframe: TimeFrame) -> Dict[str, Any]:
        """Analyze a single timeframe for alignment."""
        # Extract trend indicators
        trend = self._determine_trend(tf_data)
        momentum = self._analyze_momentum(tf_data)
        structure = self._analyze_structure(tf_data, signal_direction)
        
        # Check if timeframe aligns with signal
        aligned = self._check_alignment(trend, momentum, structure, signal_direction)
        
        # Check for conflicts
        conflict = self._check_conflict(trend, signal_direction, timeframe)
        
        # Calculate confidence for this timeframe
        confidence = self._calculate_tf_confidence(trend, momentum, structure)
        
        return {
            'timeframe': timeframe.value,
            'trend': trend.value,
            'momentum': momentum,
            'structure': structure,
            'aligned': aligned,
            'conflict': conflict,
            'confidence': confidence,
            'details': self._get_tf_details(tf_data, trend, momentum)
        }
    
    def _determine_trend(self, tf_data: Dict[str, Any]) -> TrendDirection:
        """Determine trend direction from timeframe data."""
        # MA-based trend determination
        ma_fast = tf_data.get('ma_fast', [])
        ma_slow = tf_data.get('ma_slow', [])
        price = tf_data.get('close', [])
        
        if not ma_fast or not ma_slow or not price:
            return TrendDirection.NEUTRAL
            
        current_price = price[-1] if isinstance(price, list) else price
        fast_ma = ma_fast[-1] if isinstance(ma_fast, list) else ma_fast
        slow_ma = ma_slow[-1] if isinstance(ma_slow, list) else ma_slow
        
        # Bullish: price > fast MA > slow MA
        if current_price > fast_ma > slow_ma:
            return TrendDirection.BULLISH
        # Bearish: price < fast MA < slow MA
        elif current_price < fast_ma < slow_ma:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.NEUTRAL
    
    def _analyze_momentum(self, tf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze momentum indicators."""
        momentum_data = {
            'strength': 'neutral',
            'divergence': False,
            'exhaustion': False
        }
        
        # RSI analysis
        rsi = tf_data.get('rsi', 50)
        rsi_prev = tf_data.get('rsi_prev', 50)
        
        if rsi > 70:
            momentum_data['strength'] = 'overbought'
            if rsi < rsi_prev:
                momentum_data['exhaustion'] = True
        elif rsi < 30:
            momentum_data['strength'] = 'oversold'
            if rsi > rsi_prev:
                momentum_data['exhaustion'] = True
        elif rsi > 60:
            momentum_data['strength'] = 'bullish'
        elif rsi < 40:
            momentum_data['strength'] = 'bearish'
        
        # Check for divergence
        price_highs = tf_data.get('recent_highs', [])
        price_lows = tf_data.get('recent_lows', [])
        rsi_values = tf_data.get('rsi_history', [])
        
        if len(price_highs) >= 2 and len(rsi_values) >= 2:
            # Bearish divergence: higher highs in price, lower highs in RSI
            if price_highs[-1] > price_highs[-2] and rsi_values[-1] < rsi_values[-2]:
                momentum_data['divergence'] = True
                momentum_data['divergence_type'] = 'bearish'
            # Bullish divergence: lower lows in price, higher lows in RSI
            elif price_lows[-1] < price_lows[-2] and rsi_values[-1] > rsi_values[-2]:
                momentum_data['divergence'] = True
                momentum_data['divergence_type'] = 'bullish'
        
        return momentum_data
    
    def _analyze_structure(self, tf_data: Dict[str, Any], direction: str) -> Dict[str, Any]:
        """Analyze market structure."""
        structure_data = {
            'pattern': 'none',
            'key_level': False,
            'break_of_structure': False
        }
        
        # Check for key patterns
        highs = tf_data.get('recent_highs', [])
        lows = tf_data.get('recent_lows', [])
        
        if len(highs) >= 2 and len(lows) >= 2:
            # Higher highs and higher lows (uptrend)
            if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
                structure_data['pattern'] = 'uptrend'
                if direction == 'SELL':
                    structure_data['break_of_structure'] = True
            # Lower highs and lower lows (downtrend)
            elif highs[-1] < highs[-2] and lows[-1] < lows[-2]:
                structure_data['pattern'] = 'downtrend'
                if direction == 'BUY':
                    structure_data['break_of_structure'] = True
            # Range
            else:
                structure_data['pattern'] = 'range'
        
        # Check if near key level
        current_price = tf_data.get('close', 0)
        if isinstance(current_price, list):
            current_price = current_price[-1]
            
        key_levels = tf_data.get('key_levels', [])
        for level in key_levels:
            if abs(current_price - level) < current_price * 0.002:  # Within 0.2%
                structure_data['key_level'] = True
                structure_data['key_level_price'] = level
                break
        
        return structure_data
    
    def _check_alignment(self, trend: TrendDirection, momentum: Dict,
                        structure: Dict, signal_direction: str) -> bool:
        """Check if timeframe aligns with signal direction."""
        # Trend alignment
        trend_aligned = (
            (trend == TrendDirection.BULLISH and signal_direction == 'BUY') or
            (trend == TrendDirection.BEARISH and signal_direction == 'SELL') or
            trend == TrendDirection.NEUTRAL
        )
        
        # Momentum alignment
        momentum_aligned = (
            momentum['strength'] not in ['overbought', 'oversold'] or
            (momentum['strength'] == 'oversold' and signal_direction == 'BUY') or
            (momentum['strength'] == 'overbought' and signal_direction == 'SELL')
        )
        
        # Structure alignment
        structure_aligned = not structure['break_of_structure']
        
        # Overall alignment (2 out of 3 must align)
        alignment_score = sum([trend_aligned, momentum_aligned, structure_aligned])
        return alignment_score >= 2
    
    def _check_conflict(self, trend: TrendDirection, signal_direction: str,
                       timeframe: TimeFrame) -> bool:
        """Check for direct conflicts with signal."""
        # Higher timeframes have more weight
        if timeframe in [TimeFrame.H1, TimeFrame.H4]:
            # Direct opposition is a conflict
            if (trend == TrendDirection.BULLISH and signal_direction == 'SELL' or
                trend == TrendDirection.BEARISH and signal_direction == 'BUY'):
                return True
        
        return False
    
    def _calculate_tf_confidence(self, trend: TrendDirection, momentum: Dict,
                               structure: Dict) -> float:
        """Calculate confidence score for timeframe analysis."""
        confidence = 0.5  # Base confidence
        
        # Trend contribution
        if trend != TrendDirection.NEUTRAL:
            confidence += 0.2
        
        # Momentum contribution
        if momentum['strength'] in ['bullish', 'bearish']:
            confidence += 0.15
        if momentum['divergence']:
            confidence -= 0.1
        if momentum['exhaustion']:
            confidence += 0.1
        
        # Structure contribution
        if structure['pattern'] in ['uptrend', 'downtrend']:
            confidence += 0.15
        if structure['key_level']:
            confidence += 0.1
        if structure['break_of_structure']:
            confidence -= 0.2
        
        return max(0, min(1, confidence))
    
    def _calculate_alignment(self, tf_analysis: Dict[str, Dict],
                           direction: str) -> Dict[str, Any]:
        """Calculate overall alignment metrics."""
        aligned_count = sum(1 for tf in tf_analysis.values() if tf.get('aligned', False))
        total_count = len(tf_analysis)
        
        # Calculate weighted score (higher TFs have more weight)
        weights = {'M5': 1, 'M15': 2, 'H1': 3, 'H4': 4}
        weighted_score = 0
        total_weight = 0
        
        for tf_name, analysis in tf_analysis.items():
            weight = weights.get(tf_name, 1)
            if analysis.get('aligned', False):
                weighted_score += weight * analysis.get('confidence', 0.5)
            total_weight += weight
        
        normalized_score = (weighted_score / total_weight) * 10 if total_weight > 0 else 0
        
        # Determine quality
        if aligned_count >= 4:
            quality = 'EXCELLENT'
        elif aligned_count >= 3:
            quality = 'GOOD'
        elif aligned_count >= 2:
            quality = 'MODERATE'
        else:
            quality = 'POOR'
        
        return {
            'aligned_count': aligned_count,
            'total_count': total_count,
            'score': round(normalized_score, 1),
            'quality': quality,
            'weighted_alignment': round(weighted_score / total_weight, 2) if total_weight > 0 else 0
        }
    
    def _check_validation_rules(self, alignment: Dict, signal_type: str) -> bool:
        """Check if signal passes validation based on type."""
        required_alignment = self.alignment_requirements.get(signal_type, 3)
        return alignment['aligned_count'] >= required_alignment
    
    def _identify_conflicts(self, tf_analysis: Dict[str, Dict], 
                          direction: str) -> List[str]:
        """Identify specific conflicts across timeframes."""
        conflicts = []
        
        for tf_name, analysis in tf_analysis.items():
            if analysis.get('conflict', False):
                conflicts.append(f"{tf_name}: Opposing trend")
            
            # Check for momentum conflicts
            momentum = analysis.get('momentum', {})
            if (direction == 'BUY' and momentum.get('strength') == 'overbought' or
                direction == 'SELL' and momentum.get('strength') == 'oversold'):
                conflicts.append(f"{tf_name}: Momentum exhaustion")
            
            # Check for divergence conflicts
            if momentum.get('divergence'):
                div_type = momentum.get('divergence_type', '')
                if (direction == 'BUY' and div_type == 'bearish' or
                    direction == 'SELL' and div_type == 'bullish'):
                    conflicts.append(f"{tf_name}: {div_type.title()} divergence")
        
        return conflicts
    
    def _identify_confluences(self, tf_analysis: Dict[str, Dict]) -> List[str]:
        """Identify positive confluences across timeframes."""
        confluences = []
        
        # Check for trend alignment
        aligned_trends = [tf for tf, data in tf_analysis.items() 
                         if data.get('trend') != 'neutral']
        if len(aligned_trends) >= 3:
            confluences.append(f"Strong trend alignment ({len(aligned_trends)}/4 TFs)")
        
        # Check for key level confluence
        key_level_tfs = [tf for tf, data in tf_analysis.items()
                        if data.get('structure', {}).get('key_level', False)]
        if len(key_level_tfs) >= 2:
            confluences.append(f"Key level confluence on {', '.join(key_level_tfs)}")
        
        # Check for momentum alignment
        bullish_momentum = sum(1 for data in tf_analysis.values()
                             if data.get('momentum', {}).get('strength') == 'bullish')
        bearish_momentum = sum(1 for data in tf_analysis.values()
                             if data.get('momentum', {}).get('strength') == 'bearish')
        
        if bullish_momentum >= 3:
            confluences.append("Strong bullish momentum across timeframes")
        elif bearish_momentum >= 3:
            confluences.append("Strong bearish momentum across timeframes")
        
        return confluences
    
    def _generate_recommendation(self, alignment: Dict, conflicts: List[str],
                               signal_type: str) -> str:
        """Generate recommendation based on validation results."""
        if alignment['quality'] == 'EXCELLENT':
            return "Strong multi-timeframe alignment - High confidence entry"
        elif alignment['quality'] == 'GOOD':
            if not conflicts:
                return "Good alignment with no major conflicts - Proceed with standard risk"
            else:
                return "Good alignment but monitor conflicts - Consider reduced position"
        elif alignment['quality'] == 'MODERATE':
            if len(conflicts) <= 1:
                return "Moderate alignment - Wait for better confirmation or reduce size"
            else:
                return "Moderate alignment with conflicts - Consider skipping or minimal size"
        else:
            return "Poor multi-timeframe alignment - Avoid entry or wait for improvement"
    
    def _get_tf_details(self, tf_data: Dict, trend: TrendDirection, 
                       momentum: Dict) -> str:
        """Generate human-readable timeframe details."""
        details = []
        
        # Trend
        details.append(f"Trend: {trend.value}")
        
        # Momentum
        mom_str = momentum['strength']
        if momentum.get('divergence'):
            mom_str += f" with {momentum.get('divergence_type', '')} divergence"
        details.append(f"Momentum: {mom_str}")
        
        # Key metrics
        if 'rsi' in tf_data:
            details.append(f"RSI: {tf_data['rsi']:.1f}")
        
        return " | ".join(details)
    
    def _get_default_tf_analysis(self) -> Dict[str, Any]:
        """Return default timeframe analysis."""
        return {
            'timeframe': 'unknown',
            'trend': TrendDirection.NEUTRAL.value,
            'momentum': {'strength': 'neutral'},
            'structure': {'pattern': 'none'},
            'aligned': False,
            'conflict': False,
            'confidence': 0.5,
            'details': 'No data available'
        }
    
    def _get_default_validation(self) -> Dict[str, Any]:
        """Return default validation results."""
        return {
            'm5_confirmed': False,
            'm15_confirmed': False,
            'h1_confirmed': False,
            'h4_confirmed': False,
            'h4_conflict': False,
            'total_aligned': 0,
            'alignment_score': 0,
            'alignment_quality': 'UNKNOWN',
            'passes_validation': False,
            'conflicts': [],
            'confluences': [],
            'tf_details': {},
            'recommendation': 'Unable to validate - missing data'
        }


# Example usage
if __name__ == "__main__":
    validator = CrossTimeframeValidator()
    
    # Test signal
    test_signal = {
        'pair': 'EURUSD',
        'direction': 'BUY',
        'signal_type': 'TREND_FOLLOWING'
    }
    
    # Test timeframe data
    test_tf_data = {
        'M5': {
            'close': 1.0850,
            'ma_fast': 1.0845,
            'ma_slow': 1.0840,
            'rsi': 55,
            'rsi_prev': 52,
            'recent_highs': [1.0855, 1.0860],
            'recent_lows': [1.0835, 1.0840],
            'key_levels': [1.0850, 1.0900]
        },
        'M15': {
            'close': 1.0850,
            'ma_fast': 1.0848,
            'ma_slow': 1.0843,
            'rsi': 58,
            'rsi_prev': 54,
            'recent_highs': [1.0860, 1.0865],
            'recent_lows': [1.0830, 1.0835],
            'key_levels': [1.0850, 1.0900]
        },
        'H1': {
            'close': 1.0850,
            'ma_fast': 1.0847,
            'ma_slow': 1.0842,
            'rsi': 60,
            'rsi_prev': 57,
            'recent_highs': [1.0870, 1.0875],
            'recent_lows': [1.0820, 1.0825],
            'key_levels': [1.0850, 1.0900]
        },
        'H4': {
            'close': 1.0850,
            'ma_fast': 1.0845,
            'ma_slow': 1.0840,
            'rsi': 62,
            'rsi_prev': 59,
            'recent_highs': [1.0880, 1.0890],
            'recent_lows': [1.0800, 1.0810],
            'key_levels': [1.0850, 1.0900, 1.1000]
        }
    }
    
    result = validator.validate(test_signal, test_tf_data)
    print("Cross-Timeframe Validation:")
    for key, value in result.items():
        if key != 'tf_details':
            print(f"  {key}: {value}")