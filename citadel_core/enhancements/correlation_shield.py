"""
Correlation Conflict Detector - Identify and warn about correlated exposure

Purpose: Detect when multiple signals create conflicting or amplified exposure
through currency correlations, helping traders avoid hidden risks.
"""

from typing import Dict, Any, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class CorrelationShield:
    """
    Detects correlation conflicts and opportunities in signal portfolios.
    
    Prevents hidden risk from taking opposing positions in highly correlated
    pairs while identifying opportunities for amplified exposure.
    """
    
    def __init__(self):
        # Major currency correlation matrix (approximate values)
        # Positive = move together, Negative = move opposite
        self.correlation_matrix = {
            'EURUSD': {
                'GBPUSD': 0.85,   # High positive
                'AUDUSD': 0.65,   # Moderate positive
                'NZDUSD': 0.60,   # Moderate positive
                'USDCHF': -0.95,  # High negative
                'USDJPY': -0.40,  # Moderate negative
                'USDCAD': -0.75,  # High negative
                'XAUUSD': 0.45,   # Moderate positive
                'EURUSD': 1.00    # Self
            },
            'GBPUSD': {
                'EURUSD': 0.85,
                'AUDUSD': 0.55,
                'NZDUSD': 0.50,
                'USDCHF': -0.85,
                'USDJPY': -0.35,
                'USDCAD': -0.70,
                'XAUUSD': 0.40,
                'GBPUSD': 1.00
            },
            'USDJPY': {
                'EURUSD': -0.40,
                'GBPUSD': -0.35,
                'AUDUSD': -0.45,
                'NZDUSD': -0.40,
                'USDCHF': 0.45,
                'USDCAD': 0.35,
                'XAUUSD': -0.60,
                'USDJPY': 1.00
            },
            'AUDUSD': {
                'EURUSD': 0.65,
                'GBPUSD': 0.55,
                'NZDUSD': 0.85,   # AUD/NZD highly correlated
                'USDCHF': -0.70,
                'USDJPY': -0.45,
                'USDCAD': -0.60,
                'XAUUSD': 0.75,   # Gold correlates with AUD
                'AUDUSD': 1.00
            },
            'XAUUSD': {
                'EURUSD': 0.45,
                'GBPUSD': 0.40,
                'AUDUSD': 0.75,
                'NZDUSD': 0.65,
                'USDCHF': -0.55,
                'USDJPY': -0.60,
                'USDCAD': -0.50,
                'XAUUSD': 1.00
            }
        }
        
        # Correlation strength thresholds
        self.thresholds = {
            'extreme': 0.85,    # |r| >= 0.85
            'high': 0.70,       # |r| >= 0.70
            'moderate': 0.50,   # |r| >= 0.50
            'low': 0.30,        # |r| >= 0.30
            'negligible': 0.0   # |r| < 0.30
        }
        
        # Risk classifications
        self.risk_levels = {
            'CRITICAL': 'Extreme correlation conflict detected',
            'HIGH': 'High correlation risk present',
            'MODERATE': 'Moderate correlation exposure',
            'LOW': 'Minor correlation consideration',
            'SAFE': 'No significant correlation issues'
        }
    
    def analyze_signal_correlations(self, active_signals: List[Dict[str, Any]],
                                  new_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze correlation impact of adding a new signal to active positions.
        
        Args:
            active_signals: Currently active signals/positions
            new_signal: Proposed new signal
            
        Returns:
            Correlation analysis and warnings
        """
        if not active_signals:
            return self._get_safe_result()
        
        new_pair = new_signal.get('pair', '').upper()
        new_direction = new_signal.get('direction', '').upper()
        
        # Detect conflicts and synergies
        conflicts = []
        synergies = []
        net_exposure = defaultdict(float)
        
        for active in active_signals:
            active_pair = active.get('pair', '').upper()
            active_direction = active.get('direction', '').upper()
            
            # Get correlation
            correlation = self._get_correlation(new_pair, active_pair)
            
            if abs(correlation) < self.thresholds['low']:
                continue  # Skip negligible correlations
            
            # Check for conflicts
            conflict_type = self._check_conflict(
                new_pair, new_direction,
                active_pair, active_direction,
                correlation
            )
            
            if conflict_type:
                conflicts.append({
                    'pairs': f"{new_pair} vs {active_pair}",
                    'correlation': correlation,
                    'type': conflict_type,
                    'severity': self._get_severity(correlation, conflict_type),
                    'description': self._get_conflict_description(
                        new_pair, new_direction, active_pair, 
                        active_direction, correlation
                    )
                })
            else:
                # Check for synergies
                synergy_type = self._check_synergy(
                    new_pair, new_direction,
                    active_pair, active_direction,
                    correlation
                )
                
                if synergy_type:
                    synergies.append({
                        'pairs': f"{new_pair} + {active_pair}",
                        'correlation': correlation,
                        'type': synergy_type,
                        'description': self._get_synergy_description(
                            new_pair, new_direction, active_pair,
                            active_direction, correlation
                        )
                    })
            
            # Track net exposure
            self._update_net_exposure(
                net_exposure, new_pair, new_direction,
                active_pair, active_direction, correlation
            )
        
        # Calculate overall risk level
        risk_level = self._calculate_risk_level(conflicts, synergies)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            conflicts, synergies, net_exposure, new_signal
        )
        
        return {
            'risk_level': risk_level,
            'conflicts': conflicts,
            'synergies': synergies,
            'net_exposure': dict(net_exposure),
            'recommendations': recommendations,
            'correlation_map': self._get_correlation_map(active_signals, new_signal),
            'position_adjustment': self._suggest_position_adjustment(
                conflicts, synergies
            )
        }
    
    def detect_correlation_clusters(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect clusters of correlated positions for risk management.
        
        Args:
            signals: List of active or proposed signals
            
        Returns:
            Correlation clusters and exposure analysis
        """
        if len(signals) < 2:
            return {'clusters': [], 'max_correlation': 0}
        
        # Build correlation groups
        clusters = []
        processed = set()
        
        for i, signal1 in enumerate(signals):
            if i in processed:
                continue
                
            cluster = [signal1]
            processed.add(i)
            pair1 = signal1.get('pair', '').upper()
            
            for j, signal2 in enumerate(signals[i+1:], i+1):
                if j in processed:
                    continue
                    
                pair2 = signal2.get('pair', '').upper()
                correlation = self._get_correlation(pair1, pair2)
                
                if abs(correlation) >= self.thresholds['moderate']:
                    cluster.append(signal2)
                    processed.add(j)
            
            if len(cluster) > 1:
                clusters.append({
                    'signals': cluster,
                    'size': len(cluster),
                    'average_correlation': self._calculate_cluster_correlation(cluster),
                    'risk_concentration': self._assess_concentration_risk(cluster)
                })
        
        # Sort by risk
        clusters.sort(key=lambda x: x['risk_concentration'], reverse=True)
        
        return {
            'clusters': clusters,
            'largest_cluster': clusters[0] if clusters else None,
            'concentration_warning': self._get_concentration_warning(clusters)
        }
    
    def suggest_hedge_opportunities(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Suggest natural hedging opportunities using correlations.
        
        Args:
            signals: Current signals/positions
            
        Returns:
            Hedging suggestions
        """
        hedges = []
        
        for signal in signals:
            pair = signal.get('pair', '').upper()
            direction = signal.get('direction', '').upper()
            
            # Find negatively correlated pairs
            for hedge_pair, correlation in self.correlation_matrix.get(pair, {}).items():
                if correlation < -self.thresholds['high'] and hedge_pair != pair:
                    hedge_direction = direction  # Same direction creates hedge
                    
                    hedges.append({
                        'original': f"{pair} {direction}",
                        'hedge': f"{hedge_pair} {hedge_direction}",
                        'correlation': correlation,
                        'effectiveness': abs(correlation),
                        'description': (
                            f"Natural hedge: {hedge_pair} moves opposite to {pair} "
                            f"(correlation: {correlation:.2f})"
                        )
                    })
        
        # Sort by effectiveness
        hedges.sort(key=lambda x: x['effectiveness'], reverse=True)
        
        return hedges[:3]  # Top 3 hedges
    
    def _get_correlation(self, pair1: str, pair2: str) -> float:
        """Get correlation between two pairs."""
        # Check direct correlation
        if pair1 in self.correlation_matrix:
            if pair2 in self.correlation_matrix[pair1]:
                return self.correlation_matrix[pair1][pair2]
        
        # Check reverse
        if pair2 in self.correlation_matrix:
            if pair1 in self.correlation_matrix[pair2]:
                return self.correlation_matrix[pair2][pair1]
        
        # Check if same base or quote currency
        if self._share_currency(pair1, pair2):
            return 0.4  # Moderate correlation assumption
        
        return 0.0  # No known correlation
    
    def _share_currency(self, pair1: str, pair2: str) -> bool:
        """Check if pairs share a currency."""
        if len(pair1) >= 6 and len(pair2) >= 6:
            # Extract base and quote
            base1, quote1 = pair1[:3], pair1[3:6]
            base2, quote2 = pair2[:3], pair2[3:6]
            
            return (base1 == base2 or base1 == quote2 or 
                   quote1 == base2 or quote1 == quote2)
        return False
    
    def _check_conflict(self, pair1: str, dir1: str, pair2: str, 
                       dir2: str, correlation: float) -> Optional[str]:
        """Check if positions create a conflict."""
        # High positive correlation with opposite directions = conflict
        if correlation > self.thresholds['high'] and dir1 != dir2:
            return 'OPPOSING_CORRELATED'
        
        # High negative correlation with same direction = conflict
        if correlation < -self.thresholds['high'] and dir1 == dir2:
            return 'INVERSE_CONFLICT'
        
        return None
    
    def _check_synergy(self, pair1: str, dir1: str, pair2: str,
                      dir2: str, correlation: float) -> Optional[str]:
        """Check if positions create synergy."""
        # High positive correlation with same direction = synergy
        if correlation > self.thresholds['high'] and dir1 == dir2:
            return 'AMPLIFIED_EXPOSURE'
        
        # High negative correlation with opposite direction = synergy
        if correlation < -self.thresholds['high'] and dir1 != dir2:
            return 'NATURAL_HEDGE'
        
        return None
    
    def _get_severity(self, correlation: float, conflict_type: str) -> str:
        """Determine conflict severity."""
        abs_corr = abs(correlation)
        
        if abs_corr >= self.thresholds['extreme']:
            return 'CRITICAL'
        elif abs_corr >= self.thresholds['high']:
            return 'HIGH'
        else:
            return 'MODERATE'
    
    def _get_conflict_description(self, pair1: str, dir1: str, pair2: str,
                                 dir2: str, correlation: float) -> str:
        """Generate conflict description."""
        if correlation > 0:
            return (
                f"⚠️ {pair1} {dir1} conflicts with {pair2} {dir2} - "
                f"These pairs move together ({correlation:.1%}) but you're "
                f"trading them in opposite directions!"
            )
        else:
            return (
                f"⚠️ {pair1} {dir1} conflicts with {pair2} {dir2} - "
                f"These pairs move opposite ({correlation:.1%}) but you're "
                f"trading them in the same direction!"
            )
    
    def _get_synergy_description(self, pair1: str, dir1: str, pair2: str,
                               dir2: str, correlation: float) -> str:
        """Generate synergy description."""
        if correlation > 0:
            return (
                f"✅ {pair1} {dir1} amplifies {pair2} {dir2} - "
                f"Strong positive correlation ({correlation:.1%}) increases exposure"
            )
        else:
            return (
                f"🛡️ {pair1} {dir1} hedges {pair2} {dir2} - "
                f"Natural hedge from negative correlation ({correlation:.1%})"
            )
    
    def _update_net_exposure(self, exposure: Dict[str, float], 
                           new_pair: str, new_dir: str,
                           active_pair: str, active_dir: str,
                           correlation: float):
        """Update net currency exposure tracking."""
        # Simplified exposure calculation
        if correlation > 0:
            if new_dir == active_dir:
                exposure[new_pair] += abs(correlation)
            else:
                exposure[new_pair] -= abs(correlation)
    
    def _calculate_risk_level(self, conflicts: List[Dict], 
                            synergies: List[Dict]) -> str:
        """Calculate overall correlation risk level."""
        if not conflicts:
            return 'SAFE'
        
        # Check severity of conflicts
        critical_conflicts = sum(1 for c in conflicts if c['severity'] == 'CRITICAL')
        high_conflicts = sum(1 for c in conflicts if c['severity'] == 'HIGH')
        
        if critical_conflicts > 0:
            return 'CRITICAL'
        elif high_conflicts > 1:
            return 'HIGH'
        elif high_conflicts == 1 or len(conflicts) > 2:
            return 'MODERATE'
        else:
            return 'LOW'
    
    def _generate_recommendations(self, conflicts: List[Dict], synergies: List[Dict],
                                net_exposure: Dict[str, float], 
                                new_signal: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Conflict recommendations
        if conflicts:
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2}
            worst_conflict = min(conflicts, key=lambda x: severity_order.get(x['severity'], 3))
            
            if worst_conflict['severity'] == 'CRITICAL':
                recommendations.append(
                    "🚨 CRITICAL: Consider skipping this signal or closing conflicting position"
                )
            elif worst_conflict['severity'] == 'HIGH':
                recommendations.append(
                    "⚠️ Reduce position size by 50% due to correlation conflict"
                )
            else:
                recommendations.append(
                    "📊 Monitor closely - moderate correlation exposure"
                )
        
        # Synergy recommendations
        if synergies:
            amplified = [s for s in synergies if s['type'] == 'AMPLIFIED_EXPOSURE']
            hedged = [s for s in synergies if s['type'] == 'NATURAL_HEDGE']
            
            if amplified:
                recommendations.append(
                    "💡 Concentrated exposure detected - ensure total risk is managed"
                )
            if hedged:
                recommendations.append(
                    "🛡️ Natural hedge present - consider larger position"
                )
        
        # Net exposure recommendations
        high_exposure_pairs = [p for p, exp in net_exposure.items() if exp > 2]
        if high_exposure_pairs:
            recommendations.append(
                f"📈 High net exposure on: {', '.join(high_exposure_pairs)}"
            )
        
        return recommendations
    
    def _get_correlation_map(self, active_signals: List[Dict], 
                           new_signal: Dict[str, Any]) -> Dict[str, float]:
        """Create correlation map for visualization."""
        new_pair = new_signal.get('pair', '').upper()
        correlation_map = {}
        
        for signal in active_signals:
            pair = signal.get('pair', '').upper()
            correlation = self._get_correlation(new_pair, pair)
            if abs(correlation) > self.thresholds['negligible']:
                correlation_map[pair] = correlation
        
        return correlation_map
    
    def _suggest_position_adjustment(self, conflicts: List[Dict],
                                   synergies: List[Dict]) -> Dict[str, Any]:
        """Suggest position size adjustment based on correlations."""
        if not conflicts and not synergies:
            return {'multiplier': 1.0, 'reason': 'No correlation impact'}
        
        multiplier = 1.0
        reasons = []
        
        # Adjust for conflicts
        for conflict in conflicts:
            if conflict['severity'] == 'CRITICAL':
                multiplier *= 0.3
                reasons.append("Critical conflict: 70% reduction")
            elif conflict['severity'] == 'HIGH':
                multiplier *= 0.5
                reasons.append("High conflict: 50% reduction")
            else:
                multiplier *= 0.75
                reasons.append("Moderate conflict: 25% reduction")
        
        # Adjust for synergies
        natural_hedges = [s for s in synergies if s['type'] == 'NATURAL_HEDGE']
        if natural_hedges:
            multiplier *= 1.2
            reasons.append("Natural hedge: 20% increase")
        
        return {
            'multiplier': round(multiplier, 2),
            'reason': ' | '.join(reasons) if reasons else 'Standard position'
        }
    
    def _calculate_cluster_correlation(self, cluster: List[Dict]) -> float:
        """Calculate average correlation within a cluster."""
        if len(cluster) < 2:
            return 0.0
        
        total_correlation = 0
        count = 0
        
        for i, signal1 in enumerate(cluster):
            for signal2 in cluster[i+1:]:
                correlation = self._get_correlation(
                    signal1.get('pair', ''),
                    signal2.get('pair', '')
                )
                total_correlation += abs(correlation)
                count += 1
        
        return total_correlation / count if count > 0 else 0.0
    
    def _assess_concentration_risk(self, cluster: List[Dict]) -> float:
        """Assess risk from position concentration."""
        size = len(cluster)
        avg_correlation = self._calculate_cluster_correlation(cluster)
        
        # Risk increases with size and correlation
        return size * avg_correlation
    
    def _get_concentration_warning(self, clusters: List[Dict]) -> Optional[str]:
        """Generate concentration risk warning."""
        if not clusters:
            return None
        
        largest = clusters[0]
        if largest['risk_concentration'] > 3:
            return (
                f"🚨 High concentration risk: {largest['size']} correlated positions "
                f"with {largest['average_correlation']:.1%} average correlation"
            )
        elif largest['risk_concentration'] > 2:
            return (
                f"⚠️ Moderate concentration: {largest['size']} related positions"
            )
        
        return None
    
    def _get_safe_result(self) -> Dict[str, Any]:
        """Return safe result when no conflicts exist."""
        return {
            'risk_level': 'SAFE',
            'conflicts': [],
            'synergies': [],
            'net_exposure': {},
            'recommendations': ['✅ No correlation conflicts detected'],
            'correlation_map': {},
            'position_adjustment': {'multiplier': 1.0, 'reason': 'No correlation impact'}
        }


# Example usage
if __name__ == "__main__":
    shield = CorrelationShield()
    
    # Test active positions
    active_signals = [
        {'pair': 'EURUSD', 'direction': 'BUY'},
        {'pair': 'GBPUSD', 'direction': 'BUY'},
        {'pair': 'USDCHF', 'direction': 'BUY'}
    ]
    
    # New signal to analyze
    new_signal = {'pair': 'AUDUSD', 'direction': 'SELL'}
    
    # Analyze correlations
    result = shield.analyze_signal_correlations(active_signals, new_signal)
    
    print("Correlation Analysis:")
    print(f"Risk Level: {result['risk_level']}")
    print(f"\nConflicts: {len(result['conflicts'])}")
    for conflict in result['conflicts']:
        print(f"  - {conflict['description']}")
    
    print(f"\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  {rec}")