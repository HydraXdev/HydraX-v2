"""
News Impact Amplifier - Enhanced news context and volatility intelligence

Purpose: Provide rich context about upcoming news events and their potential
impact on signals, helping traders make informed decisions about timing and risk.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class NewsImpact(Enum):
    """News impact classifications"""
    CRITICAL = "critical"    # Central bank decisions, NFP
    HIGH = "high"           # CPI, GDP, Rate decisions
    MEDIUM = "medium"       # PMI, Retail sales
    LOW = "low"            # Minor data releases
    NONE = "none"          # No significant news


class VolatilityExpectation(Enum):
    """Expected volatility levels"""
    EXTREME = "extreme"     # 3x+ normal volatility
    HIGH = "high"          # 2x normal volatility
    ELEVATED = "elevated"   # 1.5x normal volatility
    NORMAL = "normal"      # Standard volatility
    LOW = "low"           # Below normal volatility


class NewsAmplifier:
    """
    Amplifies signal context with comprehensive news impact analysis.
    
    Provides detailed information about upcoming events, expected volatility,
    historical precedents, and strategic recommendations.
    """
    
    def __init__(self):
        # Major economic events and their typical impacts
        self.event_profiles = {
            'NFP': {
                'name': 'Non-Farm Payrolls',
                'impact': NewsImpact.CRITICAL,
                'affected_currencies': ['USD'],
                'typical_volatility': 150,  # pips
                'duration_minutes': 120,
                'pre_event_behavior': 'consolidation',
                'post_event_behavior': 'trending',
                'best_approach': 'wait_for_direction'
            },
            'FOMC': {
                'name': 'Federal Reserve Decision',
                'impact': NewsImpact.CRITICAL,
                'affected_currencies': ['USD'],
                'typical_volatility': 200,
                'duration_minutes': 180,
                'pre_event_behavior': 'positioning',
                'post_event_behavior': 'sustained_trend',
                'best_approach': 'fade_initial_spike'
            },
            'ECB': {
                'name': 'ECB Rate Decision',
                'impact': NewsImpact.CRITICAL,
                'affected_currencies': ['EUR'],
                'typical_volatility': 180,
                'duration_minutes': 150,
                'pre_event_behavior': 'ranging',
                'post_event_behavior': 'trending',
                'best_approach': 'wait_for_confirmation'
            },
            'BOE': {
                'name': 'Bank of England Decision',
                'impact': NewsImpact.CRITICAL,
                'affected_currencies': ['GBP'],
                'typical_volatility': 200,
                'duration_minutes': 120,
                'pre_event_behavior': 'volatility_expansion',
                'post_event_behavior': 'whipsaw_then_trend',
                'best_approach': 'avoid_first_30min'
            },
            'CPI': {
                'name': 'Consumer Price Index',
                'impact': NewsImpact.HIGH,
                'affected_currencies': ['USD', 'EUR', 'GBP'],
                'typical_volatility': 80,
                'duration_minutes': 60,
                'pre_event_behavior': 'quiet',
                'post_event_behavior': 'directional',
                'best_approach': 'trade_with_trend'
            },
            'GDP': {
                'name': 'Gross Domestic Product',
                'impact': NewsImpact.HIGH,
                'affected_currencies': ['USD', 'EUR', 'GBP', 'JPY'],
                'typical_volatility': 70,
                'duration_minutes': 90,
                'pre_event_behavior': 'positioning',
                'post_event_behavior': 'gradual_trend',
                'best_approach': 'scale_in'
            }
        }
        
        # Volatility patterns by event type
        self.volatility_patterns = {
            'spike_and_reverse': {
                'description': 'Initial spike followed by reversal',
                'typical_events': ['NFP', 'CPI'],
                'strategy': 'Wait 15-30 minutes for reversal setup'
            },
            'sustained_move': {
                'description': 'One-directional move post-release',
                'typical_events': ['FOMC', 'ECB'],
                'strategy': 'Trade with the trend after confirmation'
            },
            'whipsaw': {
                'description': 'Multiple direction changes',
                'typical_events': ['BOE', 'RBA'],
                'strategy': 'Avoid trading first hour'
            },
            'fade_away': {
                'description': 'Initial move that gradually fades',
                'typical_events': ['PMI', 'Retail Sales'],
                'strategy': 'Fade the initial move after 30 minutes'
            }
        }
        
        # Historical precedents database (simplified)
        self.historical_precedents = {
            'NFP_beat': {
                'average_move': 120,
                'direction_consistency': 0.75,
                'reversal_probability': 0.30,
                'best_entry_time': 45  # minutes after release
            },
            'FOMC_hawkish': {
                'average_move': 180,
                'direction_consistency': 0.85,
                'reversal_probability': 0.15,
                'best_entry_time': 30
            },
            'CPI_miss': {
                'average_move': 90,
                'direction_consistency': 0.70,
                'reversal_probability': 0.35,
                'best_entry_time': 20
            }
        }
    
    def enhance_signal_context(self, signal: Dict[str, Any],
                             upcoming_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enhance signal with comprehensive news context.
        
        Args:
            signal: Trading signal to enhance
            upcoming_events: List of upcoming news events
            
        Returns:
            Enhanced signal context with news intelligence
        """
        if not upcoming_events:
            return self._get_no_news_context()
        
        # Analyze each upcoming event
        event_analyses = []
        overall_impact = NewsImpact.NONE
        total_volatility_expectation = 0
        
        for event in upcoming_events:
            analysis = self._analyze_event_impact(event, signal)
            event_analyses.append(analysis)
            
            # Update overall impact
            if analysis['impact'].value > overall_impact.value:
                overall_impact = analysis['impact']
            
            total_volatility_expectation += analysis['volatility_expectation']
        
        # Determine volatility classification
        volatility_class = self._classify_volatility(total_volatility_expectation)
        
        # Generate strategic recommendations
        recommendations = self._generate_news_strategy(
            signal, event_analyses, volatility_class
        )
        
        # Check for event conflicts
        conflicts = self._check_event_conflicts(event_analyses)
        
        # Historical context
        historical_context = self._get_historical_context(
            event_analyses, signal
        )
        
        return {
            'news_impact': overall_impact.value,
            'volatility_expectation': volatility_class.value,
            'events': event_analyses,
            'recommendations': recommendations,
            'conflicts': conflicts,
            'historical_context': historical_context,
            'risk_adjustments': self._calculate_risk_adjustments(
                overall_impact, volatility_class
            ),
            'timing_advice': self._get_timing_advice(event_analyses),
            'shield_modifications': self._suggest_shield_modifications(
                overall_impact, volatility_class
            )
        }
    
    def analyze_pre_news_positioning(self, signal: Dict[str, Any],
                                   event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pre-news positioning opportunities.
        
        Args:
            signal: Current signal
            event: Upcoming news event
            
        Returns:
            Pre-news positioning analysis
        """
        event_type = event.get('type', '').upper()
        time_until = self._get_time_until_event(event)
        
        if event_type not in self.event_profiles:
            return {'recommendation': 'standard_approach'}
        
        profile = self.event_profiles[event_type]
        
        # Analyze pre-event behavior
        if time_until.total_seconds() > 3600:  # More than 1 hour
            if profile['pre_event_behavior'] == 'consolidation':
                return {
                    'recommendation': 'range_trade',
                    'strategy': 'Trade the range with tight stops',
                    'exit_time': '30 minutes before news',
                    'risk_level': 'moderate'
                }
            elif profile['pre_event_behavior'] == 'positioning':
                return {
                    'recommendation': 'follow_positioning',
                    'strategy': 'Follow institutional positioning flows',
                    'exit_time': '15 minutes before news',
                    'risk_level': 'elevated'
                }
            elif profile['pre_event_behavior'] == 'volatility_expansion':
                return {
                    'recommendation': 'reduce_or_avoid',
                    'strategy': 'Volatility already expanding - avoid new positions',
                    'exit_time': 'immediately',
                    'risk_level': 'high'
                }
        else:
            return {
                'recommendation': 'avoid_new_positions',
                'strategy': 'Too close to news - wait for post-event clarity',
                'exit_time': 'n/a',
                'risk_level': 'extreme'
            }
    
    def predict_post_news_scenarios(self, event: Dict[str, Any],
                                  pair: str) -> List[Dict[str, Any]]:
        """
        Predict possible post-news scenarios.
        
        Args:
            event: News event
            pair: Currency pair
            
        Returns:
            List of scenarios with probabilities
        """
        event_type = event.get('type', '').upper()
        
        if event_type not in self.event_profiles:
            return [{'scenario': 'unknown', 'probability': 1.0}]
        
        profile = self.event_profiles[event_type]
        
        # Generate scenarios based on event type
        scenarios = []
        
        if profile['post_event_behavior'] == 'trending':
            scenarios.extend([
                {
                    'scenario': 'strong_trend_continuation',
                    'probability': 0.60,
                    'description': 'Price trends strongly in data direction',
                    'strategy': 'Trade with trend after confirmation',
                    'entry_timing': '15-30 minutes post-release'
                },
                {
                    'scenario': 'choppy_trend',
                    'probability': 0.30,
                    'description': 'Trend with multiple pullbacks',
                    'strategy': 'Buy dips in uptrend, sell rallies in downtrend',
                    'entry_timing': 'On pullbacks to key levels'
                },
                {
                    'scenario': 'reversal',
                    'probability': 0.10,
                    'description': 'Initial move reverses completely',
                    'strategy': 'Wait for clear reversal confirmation',
                    'entry_timing': '45-60 minutes post-release'
                }
            ])
        elif profile['post_event_behavior'] == 'whipsaw_then_trend':
            scenarios.extend([
                {
                    'scenario': 'whipsaw_shakeout',
                    'probability': 0.70,
                    'description': 'Multiple direction changes before trending',
                    'strategy': 'Wait for whipsaw to complete',
                    'entry_timing': '60+ minutes post-release'
                },
                {
                    'scenario': 'immediate_trend',
                    'probability': 0.20,
                    'description': 'Skips whipsaw, trends immediately',
                    'strategy': 'Quick entry with wide stops',
                    'entry_timing': '5-10 minutes post-release'
                },
                {
                    'scenario': 'extended_range',
                    'probability': 0.10,
                    'description': 'Continues ranging despite news',
                    'strategy': 'Range trade with caution',
                    'entry_timing': 'At range extremes'
                }
            ])
        
        return scenarios
    
    def _analyze_event_impact(self, event: Dict[str, Any],
                            signal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single event impact on signal."""
        event_type = event.get('type', '').upper()
        event_time = event.get('time', datetime.now())
        currencies = event.get('currencies', [])
        
        # Get event profile
        profile = self.event_profiles.get(event_type, {})
        
        # Check if signal is affected
        signal_pair = signal.get('pair', '').upper()
        is_affected = any(
            curr in signal_pair for curr in currencies
        ) or any(
            curr in signal_pair for curr in profile.get('affected_currencies', [])
        )
        
        # Calculate time until event
        time_until = self._get_time_until_event(event)
        
        # Determine impact level
        if is_affected:
            impact = profile.get('impact', NewsImpact.MEDIUM)
        else:
            impact = NewsImpact.LOW if self._is_correlated_impact(
                signal_pair, currencies
            ) else NewsImpact.NONE
        
        # Calculate volatility expectation
        base_volatility = profile.get('typical_volatility', 50)
        time_factor = self._get_time_volatility_factor(time_until)
        volatility_expectation = base_volatility * time_factor
        
        return {
            'event': event_type,
            'name': profile.get('name', event_type),
            'time_until': time_until,
            'impact': impact,
            'is_directly_affected': is_affected,
            'volatility_expectation': volatility_expectation,
            'pre_event_behavior': profile.get('pre_event_behavior', 'unknown'),
            'post_event_behavior': profile.get('post_event_behavior', 'unknown'),
            'best_approach': profile.get('best_approach', 'use_caution'),
            'duration_estimate': profile.get('duration_minutes', 60)
        }
    
    def _get_time_until_event(self, event: Dict[str, Any]) -> timedelta:
        """Calculate time until news event."""
        event_time = event.get('time', datetime.now() + timedelta(hours=1))
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time)
        return event_time - datetime.now()
    
    def _is_correlated_impact(self, pair: str, event_currencies: List[str]) -> bool:
        """Check if pair is indirectly affected through correlation."""
        # Simplified correlation check
        correlated_pairs = {
            'EUR': ['GBP', 'CHF'],
            'GBP': ['EUR', 'AUD'],
            'AUD': ['NZD', 'GBP'],
            'USD': ['CAD', 'JPY'],
            'JPY': ['USD', 'AUD']
        }
        
        for currency in event_currencies:
            if currency in correlated_pairs:
                for corr_curr in correlated_pairs[currency]:
                    if corr_curr in pair:
                        return True
        return False
    
    def _get_time_volatility_factor(self, time_until: timedelta) -> float:
        """Calculate volatility factor based on time until event."""
        minutes_until = time_until.total_seconds() / 60
        
        if minutes_until < 0:  # Event has passed
            return 0.5
        elif minutes_until < 15:  # Very close
            return 2.0
        elif minutes_until < 30:
            return 1.5
        elif minutes_until < 60:
            return 1.2
        elif minutes_until < 120:
            return 1.0
        else:
            return 0.8
    
    def _classify_volatility(self, total_expectation: float) -> VolatilityExpectation:
        """Classify expected volatility level."""
        if total_expectation > 300:
            return VolatilityExpectation.EXTREME
        elif total_expectation > 200:
            return VolatilityExpectation.HIGH
        elif total_expectation > 100:
            return VolatilityExpectation.ELEVATED
        elif total_expectation > 50:
            return VolatilityExpectation.NORMAL
        else:
            return VolatilityExpectation.LOW
    
    def _generate_news_strategy(self, signal: Dict[str, Any],
                              event_analyses: List[Dict],
                              volatility: VolatilityExpectation) -> List[str]:
        """Generate strategic recommendations based on news."""
        recommendations = []
        
        # Check for critical events
        critical_events = [e for e in event_analyses 
                          if e['impact'] == NewsImpact.CRITICAL]
        
        if critical_events:
            closest_event = min(critical_events, key=lambda e: e['time_until'])
            minutes_until = closest_event['time_until'].total_seconds() / 60
            
            if minutes_until < 30:
                recommendations.append(
                    f"🚨 CRITICAL: {closest_event['name']} in {minutes_until:.0f} min - "
                    f"Consider closing or hedging position"
                )
            elif minutes_until < 90:
                recommendations.append(
                    f"⚠️ HIGH IMPACT: {closest_event['name']} approaching - "
                    f"Tighten stops or reduce position"
                )
            else:
                recommendations.append(
                    f"📅 Plan exit before {closest_event['name']} - "
                    f"Close at least 30 min prior"
                )
        
        # Volatility-based recommendations
        if volatility == VolatilityExpectation.EXTREME:
            recommendations.append(
                "🌪️ Extreme volatility expected - Use wider stops or avoid entry"
            )
        elif volatility == VolatilityExpectation.HIGH:
            recommendations.append(
                "📊 High volatility period - Consider 50% position size"
            )
        
        # Add approach recommendations
        for event in event_analyses[:2]:  # Top 2 events
            if event['best_approach']:
                recommendations.append(
                    f"💡 {event['event']}: {event['best_approach'].replace('_', ' ').title()}"
                )
        
        return recommendations
    
    def _check_event_conflicts(self, event_analyses: List[Dict]) -> List[str]:
        """Check for conflicting news events."""
        conflicts = []
        
        # Check for multiple high-impact events
        high_impact_events = [e for e in event_analyses 
                            if e['impact'].value >= NewsImpact.HIGH.value]
        
        if len(high_impact_events) > 1:
            # Check if events are close together
            for i, event1 in enumerate(high_impact_events):
                for event2 in high_impact_events[i+1:]:
                    time_diff = abs(
                        (event1['time_until'] - event2['time_until']).total_seconds() / 60
                    )
                    if time_diff < 120:  # Within 2 hours
                        conflicts.append(
                            f"⚡ Conflicting events: {event1['name']} and "
                            f"{event2['name']} within {time_diff:.0f} minutes"
                        )
        
        # Check for opposing currency events
        currencies_affected = defaultdict(list)
        for event in event_analyses:
            if event['is_directly_affected']:
                for curr in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']:
                    if curr in event['event']:
                        currencies_affected[curr].append(event['name'])
        
        for curr, events in currencies_affected.items():
            if len(events) > 1:
                conflicts.append(
                    f"🔄 Multiple {curr} events: {', '.join(events)}"
                )
        
        return conflicts
    
    def _get_historical_context(self, event_analyses: List[Dict],
                              signal: Dict[str, Any]) -> Dict[str, Any]:
        """Get historical precedent for similar situations."""
        if not event_analyses:
            return {}
        
        # Find most impactful event
        main_event = max(event_analyses, key=lambda e: e['impact'].value)
        event_type = main_event['event']
        
        # Look up historical precedent
        precedent_key = f"{event_type}_beat"  # Simplified
        if precedent_key in self.historical_precedents:
            precedent = self.historical_precedents[precedent_key]
            return {
                'average_move': precedent['average_move'],
                'direction_consistency': f"{precedent['direction_consistency']:.0%}",
                'reversal_chance': f"{precedent['reversal_probability']:.0%}",
                'optimal_entry': f"{precedent['best_entry_time']} min after release",
                'historical_note': (
                    f"Historically, {event_type} creates {precedent['average_move']} pip "
                    f"moves with {precedent['direction_consistency']:.0%} directional consistency"
                )
            }
        
        return {
            'historical_note': 'Limited historical data for this event combination'
        }
    
    def _calculate_risk_adjustments(self, impact: NewsImpact,
                                  volatility: VolatilityExpectation) -> Dict[str, Any]:
        """Calculate recommended risk adjustments."""
        # Base adjustments
        position_size_multiplier = 1.0
        stop_loss_multiplier = 1.0
        
        # Adjust for impact
        if impact == NewsImpact.CRITICAL:
            position_size_multiplier *= 0.3
            stop_loss_multiplier *= 2.0
        elif impact == NewsImpact.HIGH:
            position_size_multiplier *= 0.5
            stop_loss_multiplier *= 1.5
        elif impact == NewsImpact.MEDIUM:
            position_size_multiplier *= 0.75
            stop_loss_multiplier *= 1.25
        
        # Adjust for volatility
        if volatility == VolatilityExpectation.EXTREME:
            position_size_multiplier *= 0.5
            stop_loss_multiplier *= 1.5
        elif volatility == VolatilityExpectation.HIGH:
            position_size_multiplier *= 0.75
            stop_loss_multiplier *= 1.25
        
        return {
            'position_size_adjustment': round(position_size_multiplier, 2),
            'stop_loss_adjustment': round(stop_loss_multiplier, 2),
            'recommendation': self._get_risk_adjustment_text(
                position_size_multiplier, stop_loss_multiplier
            )
        }
    
    def _get_risk_adjustment_text(self, size_mult: float, stop_mult: float) -> str:
        """Generate risk adjustment recommendation text."""
        if size_mult <= 0.3:
            size_text = "Minimal position (70%+ reduction)"
        elif size_mult <= 0.5:
            size_text = "Half position recommended"
        elif size_mult <= 0.75:
            size_text = "Reduced position (25% cut)"
        else:
            size_text = "Standard position acceptable"
        
        if stop_mult >= 2.0:
            stop_text = "Double your normal stop distance"
        elif stop_mult >= 1.5:
            stop_text = "Use 50% wider stops"
        elif stop_mult >= 1.25:
            stop_text = "Slightly wider stops advised"
        else:
            stop_text = "Normal stops acceptable"
        
        return f"{size_text} | {stop_text}"
    
    def _get_timing_advice(self, event_analyses: List[Dict]) -> Dict[str, Any]:
        """Provide specific timing advice."""
        if not event_analyses:
            return {'status': 'clear', 'advice': 'No news conflicts'}
        
        # Find closest event
        closest_event = min(event_analyses, key=lambda e: e['time_until'])
        minutes_until = closest_event['time_until'].total_seconds() / 60
        
        if minutes_until < 0:
            return {
                'status': 'post_news',
                'advice': f"News has passed - monitor for delayed reactions",
                'action': 'proceed_with_caution'
            }
        elif minutes_until < 15:
            return {
                'status': 'danger_zone',
                'advice': f"🚨 {closest_event['name']} in {minutes_until:.0f} min - DO NOT ENTER",
                'action': 'abort_entry'
            }
        elif minutes_until < 30:
            return {
                'status': 'high_risk',
                'advice': f"⚠️ {closest_event['name']} in {minutes_until:.0f} min - Quick scalp only",
                'action': 'scalp_or_wait'
            }
        elif minutes_until < 90:
            return {
                'status': 'caution',
                'advice': f"📊 {closest_event['name']} in {minutes_until:.0f} min - Plan your exit",
                'action': 'trade_with_exit_plan'
            }
        else:
            return {
                'status': 'safe_window',
                'advice': f"✅ Next event in {minutes_until:.0f} min - Safe to trade",
                'action': 'proceed_normally'
            }
    
    def _suggest_shield_modifications(self, impact: NewsImpact,
                                    volatility: VolatilityExpectation) -> Dict[str, Any]:
        """Suggest modifications to shield scoring based on news."""
        modifications = {
            'score_adjustment': 0,
            'reasons': []
        }
        
        # Adjust shield score based on news impact
        if impact == NewsImpact.CRITICAL:
            modifications['score_adjustment'] = -3
            modifications['reasons'].append("Critical news event approaching (-3)")
        elif impact == NewsImpact.HIGH:
            modifications['score_adjustment'] = -2
            modifications['reasons'].append("High-impact news nearby (-2)")
        elif impact == NewsImpact.MEDIUM:
            modifications['score_adjustment'] = -1
            modifications['reasons'].append("Medium news impact (-1)")
        
        # Additional volatility adjustment
        if volatility == VolatilityExpectation.EXTREME:
            modifications['score_adjustment'] -= 1
            modifications['reasons'].append("Extreme volatility expected (-1)")
        
        return modifications
    
    def _get_no_news_context(self) -> Dict[str, Any]:
        """Return context when no news events are scheduled."""
        return {
            'news_impact': NewsImpact.NONE.value,
            'volatility_expectation': VolatilityExpectation.NORMAL.value,
            'events': [],
            'recommendations': ['✅ Clear news calendar - Normal trading conditions'],
            'conflicts': [],
            'historical_context': {},
            'risk_adjustments': {
                'position_size_adjustment': 1.0,
                'stop_loss_adjustment': 1.0,
                'recommendation': 'Standard risk parameters'
            },
            'timing_advice': {
                'status': 'clear',
                'advice': 'No news conflicts',
                'action': 'proceed_normally'
            },
            'shield_modifications': {
                'score_adjustment': 0,
                'reasons': []
            }
        }


# Example usage
if __name__ == "__main__":
    amplifier = NewsAmplifier()
    
    # Test signal
    signal = {
        'pair': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0850
    }
    
    # Test upcoming events
    events = [
        {
            'type': 'ECB',
            'time': datetime.now() + timedelta(hours=2),
            'currencies': ['EUR']
        },
        {
            'type': 'CPI',
            'time': datetime.now() + timedelta(hours=4),
            'currencies': ['USD']
        }
    ]
    
    # Analyze news impact
    result = amplifier.enhance_signal_context(signal, events)
    
    print("News Impact Analysis:")
    print(f"Impact Level: {result['news_impact']}")
    print(f"Volatility Expectation: {result['volatility_expectation']}")
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  {rec}")
    
    print(f"\nRisk Adjustments: {result['risk_adjustments']['recommendation']}")