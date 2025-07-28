"""
Dynamic Risk Sizing Module - Shield-based intelligent position sizing

Purpose: Provide volume-preserving position size recommendations based on
shield score, allowing traders to amplify strong signals rather than filter weak ones.
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import logging
from decimal import Decimal, ROUND_DOWN

logger = logging.getLogger(__name__)


@dataclass
class RiskProfile:
    """User's risk profile configuration"""
    base_risk_percent: float = 1.0  # Default 1% risk
    max_risk_percent: float = 2.0    # Maximum 2% risk
    min_risk_percent: float = 0.25   # Minimum 0.25% risk
    shield_confidence_multiplier: bool = True
    account_balance: float = 10000.0
    risk_mode: str = "NORMAL"  # CONSERVATIVE, NORMAL, AGGRESSIVE


class DynamicRiskSizer:
    """
    Intelligent position sizing based on CITADEL shield scores.
    
    This module doesn't filter signals - it amplifies strong ones and
    suggests reduced size for weaker ones, preserving trading volume
    while improving risk-adjusted returns.
    """
    
    def __init__(self):
        # Risk sizing tiers based on shield score
        self.risk_tiers = {
            'SHIELD_APPROVED': {
                'range': (8.0, 10.0),
                'base_multiplier': 1.5,
                'description': 'Premium setup - amplified position'
            },
            'SHIELD_ACTIVE': {
                'range': (6.0, 7.9),
                'base_multiplier': 1.0,
                'description': 'Standard setup - normal position'
            },
            'VOLATILITY_ZONE': {
                'range': (4.0, 5.9),
                'base_multiplier': 0.5,
                'description': 'Caution zone - reduced position'
            },
            'UNVERIFIED': {
                'range': (0.0, 3.9),
                'base_multiplier': 0.25,
                'description': 'Low confidence - minimal position'
            }
        }
        
        # Risk mode adjustments
        self.mode_adjustments = {
            'CONSERVATIVE': 0.7,   # 30% reduction
            'NORMAL': 1.0,         # No adjustment
            'AGGRESSIVE': 1.3      # 30% increase
        }
        
        # Special conditions
        self.special_multipliers = {
            'post_sweep_entry': 1.2,      # 20% bonus for sweep entries
            'news_high_impact': 0.5,      # 50% reduction for news
            'correlation_conflict': 0.7,   # 30% reduction for conflicts
            'multi_confluence': 1.15,      # 15% bonus for confluence
            'optimal_session': 1.1         # 10% bonus for best session
        }
    
    def calculate_position_size(self, signal: Dict[str, Any],
                              shield_analysis: Dict[str, Any],
                              risk_profile: RiskProfile) -> Dict[str, Any]:
        """
        Calculate optimal position size based on shield score and risk profile.
        
        Args:
            signal: Trading signal with pair, entry, sl, tp
            shield_analysis: CITADEL shield analysis results
            risk_profile: User's risk preferences and account info
            
        Returns:
            Position sizing recommendations
        """
        try:
            # Extract key data
            shield_score = shield_analysis.get('shield_score', 5.0)
            classification = shield_analysis.get('classification', 'UNVERIFIED')
            risk_factors = shield_analysis.get('risk_factors', [])
            quality_factors = shield_analysis.get('quality_factors', [])
            
            # Calculate base risk percentage
            base_risk = self._calculate_base_risk(
                shield_score, classification, risk_profile
            )
            
            # Apply special condition multipliers
            adjusted_risk = self._apply_special_conditions(
                base_risk, risk_factors, quality_factors
            )
            
            # Apply risk mode adjustment
            final_risk = adjusted_risk * self.mode_adjustments[risk_profile.risk_mode]
            
            # Ensure within bounds
            final_risk = max(
                risk_profile.min_risk_percent,
                min(risk_profile.max_risk_percent, final_risk)
            )
            
            # Calculate actual position size
            position_details = self._calculate_position_details(
                signal, risk_profile.account_balance, final_risk
            )
            
            # Generate sizing recommendation
            recommendation = self._generate_recommendation(
                shield_score, classification, final_risk, base_risk
            )
            
            return {
                'recommended_risk_percent': round(final_risk, 2),
                'base_risk_percent': round(base_risk, 2),
                'risk_multiplier': round(final_risk / risk_profile.base_risk_percent, 2),
                'position_size': position_details['position_size'],
                'risk_amount': position_details['risk_amount'],
                'lots': position_details['lots'],
                'units': position_details['units'],
                'recommendation': recommendation,
                'sizing_factors': self._get_sizing_factors(
                    risk_factors, quality_factors
                ),
                'confidence_level': self._get_confidence_level(shield_score)
            }
            
        except Exception as e:
            logger.error(f"Risk sizing calculation error: {str(e)}")
            return self._get_default_sizing(risk_profile)
    
    def calculate_basket_allocation(self, signals: List[Dict[str, Any]],
                                  risk_profile: RiskProfile) -> Dict[str, Any]:
        """
        Calculate position sizes for multiple correlated signals.
        
        Args:
            signals: List of signals with shield analyses
            risk_profile: User's risk preferences
            
        Returns:
            Basket allocation recommendations
        """
        if not signals:
            return {'allocations': [], 'total_risk': 0}
        
        # Sort by shield score
        sorted_signals = sorted(
            signals,
            key=lambda s: s.get('citadel_shield', {}).get('score', 0),
            reverse=True
        )
        
        # Calculate total available risk
        total_risk_budget = risk_profile.max_risk_percent
        
        # Allocate based on relative shield scores
        allocations = []
        total_score = sum(s.get('citadel_shield', {}).get('score', 0) 
                         for s in sorted_signals)
        
        for signal in sorted_signals:
            shield_score = signal.get('citadel_shield', {}).get('score', 0)
            
            # Weight by shield score
            if total_score > 0:
                weight = shield_score / total_score
            else:
                weight = 1.0 / len(signals)
            
            # Allocate risk budget
            allocated_risk = total_risk_budget * weight
            
            # Apply minimum threshold
            if shield_score < 6.0:
                allocated_risk *= 0.5  # Reduce weak signals
            
            allocations.append({
                'signal_id': signal.get('signal_id'),
                'pair': signal.get('pair'),
                'shield_score': shield_score,
                'allocated_risk_percent': round(allocated_risk, 2),
                'weight': round(weight * 100, 1)
            })
        
        return {
            'allocations': allocations,
            'total_risk': round(sum(a['allocated_risk_percent'] for a in allocations), 2),
            'recommendation': self._get_basket_recommendation(allocations)
        }
    
    def suggest_scaling_strategy(self, signal: Dict[str, Any],
                               shield_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest position scaling strategy based on shield strength.
        
        Args:
            signal: Trading signal
            shield_analysis: CITADEL analysis
            
        Returns:
            Scaling strategy recommendation
        """
        shield_score = shield_analysis.get('shield_score', 5.0)
        classification = shield_analysis.get('classification', 'UNVERIFIED')
        
        if classification == 'SHIELD_APPROVED' and shield_score >= 9.0:
            return {
                'strategy': 'SCALE_IN_AGGRESSIVE',
                'entries': 3,
                'distribution': [40, 35, 25],  # Percentage per entry
                'description': 'Triple entry scaling for premium setup',
                'entry_triggers': [
                    'Immediate entry (40%)',
                    'After 10 pip momentum (35%)',
                    'On first pullback (25%)'
                ]
            }
        elif classification in ['SHIELD_APPROVED', 'SHIELD_ACTIVE']:
            return {
                'strategy': 'SCALE_IN_STANDARD',
                'entries': 2,
                'distribution': [60, 40],
                'description': 'Dual entry for solid setup',
                'entry_triggers': [
                    'Immediate entry (60%)',
                    'After confirmation (40%)'
                ]
            }
        elif classification == 'VOLATILITY_ZONE':
            return {
                'strategy': 'SINGLE_ENTRY_REDUCED',
                'entries': 1,
                'distribution': [100],
                'description': 'Single reduced position for caution zone',
                'entry_triggers': [
                    'Wait for confirmation candle'
                ]
            }
        else:
            return {
                'strategy': 'MINIMAL_PROBE',
                'entries': 1,
                'distribution': [100],
                'description': 'Minimal probe position only',
                'entry_triggers': [
                    'Only after strong confirmation'
                ]
            }
    
    def _calculate_base_risk(self, shield_score: float, classification: str,
                           risk_profile: RiskProfile) -> float:
        """Calculate base risk percentage from shield score."""
        # Find appropriate tier
        tier_multiplier = 1.0
        for tier_name, tier_data in self.risk_tiers.items():
            if tier_data['range'][0] <= shield_score <= tier_data['range'][1]:
                tier_multiplier = tier_data['base_multiplier']
                break
        
        # Apply shield confidence if enabled
        if risk_profile.shield_confidence_multiplier:
            # Linear scaling within tier
            score_factor = (shield_score / 10.0) * 0.5 + 0.5  # 0.5 to 1.0 range
            tier_multiplier *= score_factor
        
        return risk_profile.base_risk_percent * tier_multiplier
    
    def _apply_special_conditions(self, base_risk: float,
                                risk_factors: List[Dict],
                                quality_factors: List[Dict]) -> float:
        """Apply special condition multipliers to base risk."""
        adjusted_risk = base_risk
        
        # Apply negative factors
        for risk_factor in risk_factors:
            factor_name = risk_factor.get('factor', '')
            if factor_name in self.special_multipliers:
                adjusted_risk *= self.special_multipliers[factor_name]
        
        # Apply positive factors
        for quality_factor in quality_factors:
            factor_name = quality_factor.get('factor', '')
            if factor_name in self.special_multipliers:
                adjusted_risk *= self.special_multipliers[factor_name]
        
        return adjusted_risk
    
    def _calculate_position_details(self, signal: Dict[str, Any],
                                  account_balance: float,
                                  risk_percent: float) -> Dict[str, Any]:
        """Calculate detailed position information."""
        # Risk amount in account currency
        risk_amount = account_balance * (risk_percent / 100)
        
        # Extract signal data
        entry = float(signal.get('entry_price', 0))
        stop_loss = float(signal.get('sl', 0))
        
        if entry == 0 or stop_loss == 0:
            return {
                'position_size': 0,
                'risk_amount': risk_amount,
                'lots': 0,
                'units': 0
            }
        
        # Calculate stop distance
        stop_distance = abs(entry - stop_loss)
        
        # Determine pip value based on pair
        pair = signal.get('pair', '').upper()
        if 'JPY' in pair:
            pip_value = 0.01
            pip_value_per_lot = 1000  # Approximate
        else:
            pip_value = 0.0001
            pip_value_per_lot = 10  # Approximate
        
        # Calculate position size
        stop_pips = stop_distance / pip_value
        
        if stop_pips > 0:
            position_size = risk_amount / stop_pips
            lots = position_size / pip_value_per_lot
            units = position_size * 100  # Assuming standard lot = 100k units
        else:
            position_size = 0
            lots = 0
            units = 0
        
        return {
            'position_size': round(position_size, 2),
            'risk_amount': round(risk_amount, 2),
            'lots': round(lots, 2),
            'units': int(units)
        }
    
    def _generate_recommendation(self, shield_score: float, classification: str,
                               final_risk: float, base_risk: float) -> str:
        """Generate position sizing recommendation."""
        if classification == 'SHIELD_APPROVED' and shield_score >= 9.0:
            return (
                f"🔥 PREMIUM SETUP - Amplified position recommended! "
                f"Risk {final_risk:.1f}% for this high-confidence trade."
            )
        elif classification == 'SHIELD_APPROVED':
            return (
                f"🛡️ Strong setup - Full position size appropriate. "
                f"Risk {final_risk:.1f}% with confidence."
            )
        elif classification == 'SHIELD_ACTIVE':
            return (
                f"✅ Solid setup - Standard position size suggested. "
                f"Risk {final_risk:.1f}% for balanced exposure."
            )
        elif classification == 'VOLATILITY_ZONE':
            return (
                f"⚠️ Caution advised - Reduced position recommended. "
                f"Risk only {final_risk:.1f}% in volatile conditions."
            )
        else:
            return (
                f"🔍 Low confidence - Minimal position suggested. "
                f"Risk just {final_risk:.1f}% or consider paper trading."
            )
    
    def _get_sizing_factors(self, risk_factors: List[Dict],
                          quality_factors: List[Dict]) -> List[str]:
        """Get list of factors affecting position size."""
        factors = []
        
        # Negative factors
        for risk in risk_factors:
            if risk['factor'] in self.special_multipliers:
                factors.append(f"↓ {risk['description']}")
        
        # Positive factors
        for quality in quality_factors:
            if quality['factor'] in self.special_multipliers:
                factors.append(f"↑ {quality['description']}")
        
        return factors
    
    def _get_confidence_level(self, shield_score: float) -> str:
        """Get confidence level description."""
        if shield_score >= 9.0:
            return "EXTREME"
        elif shield_score >= 8.0:
            return "HIGH"
        elif shield_score >= 6.0:
            return "MODERATE"
        elif shield_score >= 4.0:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _get_basket_recommendation(self, allocations: List[Dict]) -> str:
        """Generate basket allocation recommendation."""
        high_scores = sum(1 for a in allocations if a['shield_score'] >= 8)
        
        if high_scores >= 3:
            return "🔥 CONFLUENCE ALERT - Multiple strong signals! Consider basket approach for amplified exposure."
        elif high_scores >= 1:
            return "💡 Mixed quality basket - Focus allocation on highest shield scores."
        else:
            return "⚠️ Weak basket - Consider waiting for stronger setups or minimal allocation."
    
    def _get_default_sizing(self, risk_profile: RiskProfile) -> Dict[str, Any]:
        """Return default sizing when calculation fails."""
        return {
            'recommended_risk_percent': risk_profile.base_risk_percent,
            'base_risk_percent': risk_profile.base_risk_percent,
            'risk_multiplier': 1.0,
            'position_size': 0,
            'risk_amount': 0,
            'lots': 0,
            'units': 0,
            'recommendation': 'Unable to calculate - use standard position size',
            'sizing_factors': [],
            'confidence_level': 'UNKNOWN'
        }


# Integration helper
def get_position_size_recommendation(signal: Dict[str, Any],
                                   shield_analysis: Dict[str, Any],
                                   account_balance: float = 10000,
                                   risk_mode: str = "NORMAL") -> Dict[str, Any]:
    """
    Quick helper to get position size recommendation.
    
    Args:
        signal: Trading signal
        shield_analysis: CITADEL analysis
        account_balance: Account size
        risk_mode: CONSERVATIVE, NORMAL, or AGGRESSIVE
        
    Returns:
        Position sizing recommendation
    """
    sizer = DynamicRiskSizer()
    profile = RiskProfile(
        account_balance=account_balance,
        risk_mode=risk_mode
    )
    
    return sizer.calculate_position_size(signal, shield_analysis, profile)


# Example usage
if __name__ == "__main__":
    # Test risk sizer
    test_signal = {
        'pair': 'EURUSD',
        'entry_price': 1.0850,
        'sl': 1.0820,
        'tp': 1.0910
    }
    
    test_shield = {
        'shield_score': 8.5,
        'classification': 'SHIELD_APPROVED',
        'risk_factors': [],
        'quality_factors': [
            {'factor': 'post_sweep_entry', 'description': 'Entry after sweep'}
        ]
    }
    
    result = get_position_size_recommendation(
        test_signal,
        test_shield,
        account_balance=10000,
        risk_mode="NORMAL"
    )
    
    print("Position Size Recommendation:")
    for key, value in result.items():
        print(f"  {key}: {value}")