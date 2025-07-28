"""
Session Flow Analyzer - Institutional behavior patterns by trading session

Purpose: Analyze and predict market behavior based on session characteristics,
helping traders align with institutional flow patterns.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, time, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SessionType(Enum):
    """Trading session classifications"""
    ASIAN = "asian"
    ASIAN_LONDON_OVERLAP = "asian_london_overlap"
    LONDON = "london"
    LONDON_NY_OVERLAP = "london_ny_overlap"
    NEW_YORK = "new_york"
    NY_CLOSE = "ny_close"
    WEEKEND = "weekend"


class InstitutionalBehavior(Enum):
    """Institutional behavior patterns"""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    STOP_HUNTING = "stop_hunting"
    RANGE_TRADING = "range_trading"
    TREND_INITIATION = "trend_initiation"
    POSITION_SQUARING = "position_squaring"
    LIQUIDITY_PROVISION = "liquidity_provision"


class SessionFlow:
    """
    Analyzes institutional flow patterns and provides session-specific insights.
    
    Helps traders understand when to favor breakouts vs reversals, when to expect
    stop hunts, and how to align with smart money behavior.
    """
    
    def __init__(self):
        # Session time definitions (UTC)
        self.session_times = {
            SessionType.ASIAN: (time(23, 0), time(8, 0)),
            SessionType.ASIAN_LONDON_OVERLAP: (time(7, 0), time(8, 0)),
            SessionType.LONDON: (time(8, 0), time(16, 0)),
            SessionType.LONDON_NY_OVERLAP: (time(13, 0), time(16, 0)),
            SessionType.NEW_YORK: (time(13, 0), time(22, 0)),
            SessionType.NY_CLOSE: (time(21, 0), time(22, 0))
        }
        
        # Session characteristics
        self.session_profiles = {
            SessionType.ASIAN: {
                'liquidity': 'low',
                'volatility': 'low',
                'dominant_behavior': InstitutionalBehavior.RANGE_TRADING,
                'breakout_probability': 0.20,
                'reversal_probability': 0.65,
                'stop_hunt_probability': 0.30,
                'trend_continuation': 0.15,
                'best_pairs': ['USDJPY', 'AUDUSD', 'NZDUSD', 'AUDJPY'],
                'characteristics': {
                    'range_formation': 0.70,
                    'false_breakouts': 0.45,
                    'accumulation_zones': 0.60,
                    'news_sensitivity': 0.30
                },
                'trading_style': 'Mean reversion and range trading',
                'key_levels': 'Asian session highs/lows often tested in London'
            },
            SessionType.LONDON: {
                'liquidity': 'high',
                'volatility': 'high',
                'dominant_behavior': InstitutionalBehavior.TREND_INITIATION,
                'breakout_probability': 0.65,
                'reversal_probability': 0.35,
                'stop_hunt_probability': 0.70,
                'trend_continuation': 0.60,
                'best_pairs': ['EURUSD', 'GBPUSD', 'EURGBP', 'GBPJPY'],
                'characteristics': {
                    'directional_moves': 0.75,
                    'stop_raids': 0.80,
                    'breakout_confirmation': 0.65,
                    'news_sensitivity': 0.85
                },
                'trading_style': 'Breakout and momentum trading',
                'key_levels': 'Asian range extremes prime for stop raids'
            },
            SessionType.LONDON_NY_OVERLAP: {
                'liquidity': 'extreme',
                'volatility': 'extreme',
                'dominant_behavior': InstitutionalBehavior.STOP_HUNTING,
                'breakout_probability': 0.70,
                'reversal_probability': 0.50,
                'stop_hunt_probability': 0.85,
                'trend_continuation': 0.75,
                'best_pairs': ['EURUSD', 'GBPUSD', 'XAUUSD', 'USDCAD'],
                'characteristics': {
                    'whipsaw_moves': 0.60,
                    'liquidity_sweeps': 0.80,
                    'trend_acceleration': 0.70,
                    'news_sensitivity': 0.90
                },
                'trading_style': 'Post-sweep entries and trend continuation',
                'key_levels': 'Daily highs/lows prime targets for liquidity'
            },
            SessionType.NEW_YORK: {
                'liquidity': 'high',
                'volatility': 'moderate_high',
                'dominant_behavior': InstitutionalBehavior.DISTRIBUTION,
                'breakout_probability': 0.55,
                'reversal_probability': 0.45,
                'stop_hunt_probability': 0.60,
                'trend_continuation': 0.55,
                'best_pairs': ['EURUSD', 'GBPUSD', 'USDCAD', 'USDJPY'],
                'characteristics': {
                    'continuation_patterns': 0.60,
                    'profit_taking': 0.50,
                    'afternoon_reversals': 0.40,
                    'news_sensitivity': 0.80
                },
                'trading_style': 'Trend following with afternoon caution',
                'key_levels': 'London highs/lows often retested'
            },
            SessionType.NY_CLOSE: {
                'liquidity': 'declining',
                'volatility': 'low',
                'dominant_behavior': InstitutionalBehavior.POSITION_SQUARING,
                'breakout_probability': 0.15,
                'reversal_probability': 0.40,
                'stop_hunt_probability': 0.25,
                'trend_continuation': 0.20,
                'best_pairs': ['USDJPY', 'USDCAD'],
                'characteristics': {
                    'position_unwinding': 0.70,
                    'spread_widening': 0.60,
                    'gap_risk': 0.30,
                    'news_sensitivity': 0.20
                },
                'trading_style': 'Light positioning, avoid new trends',
                'key_levels': 'Day\'s range often defines next Asia'
            }
        }
        
        # Institutional flow patterns
        self.flow_patterns = {
            'stop_hunt_and_reverse': {
                'description': 'Price hunts stops then reverses sharply',
                'typical_sessions': [SessionType.LONDON, SessionType.LONDON_NY_OVERLAP],
                'identification': [
                    'Spike beyond key level',
                    'Quick rejection within 15 minutes',
                    'Volume spike on hunt',
                    'Return to pre-hunt range'
                ],
                'strategy': 'Enter on rejection confirmation'
            },
            'accumulation_distribution': {
                'description': 'Smart money accumulates in Asia, distributes in London/NY',
                'typical_sessions': [SessionType.ASIAN, SessionType.LONDON],
                'identification': [
                    'Tight Asian range',
                    'London breakout with volume',
                    'Sustained directional move',
                    'NY continuation or distribution'
                ],
                'strategy': 'Buy Asian lows, sell London/NY highs'
            },
            'overlap_whipsaw': {
                'description': 'Violent moves during session overlaps',
                'typical_sessions': [SessionType.LONDON_NY_OVERLAP],
                'identification': [
                    'Multiple direction changes',
                    'Stop losses on both sides hit',
                    'Eventually picks direction',
                    'Strong close in final direction'
                ],
                'strategy': 'Wait for whipsaw completion'
            }
        }
    
    def analyze_institutional_flow(self, pair: str, 
                                 current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Analyze current institutional flow patterns.
        
        Args:
            pair: Currency pair
            current_time: Time to analyze (default: now)
            
        Returns:
            Institutional flow analysis
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Identify current session
        session = self._identify_session(current_time)
        
        # Get session profile
        profile = self.session_profiles.get(session, {})
        
        # Check if pair is optimal for session
        is_optimal_pair = pair.upper() in profile.get('best_pairs', [])
        
        # Analyze likely institutional behavior
        behavior_analysis = self._analyze_institutional_behavior(
            session, pair, current_time
        )
        
        # Predict session flow
        flow_prediction = self._predict_session_flow(
            session, current_time, behavior_analysis
        )
        
        # Generate trading recommendations
        recommendations = self._generate_session_recommendations(
            session, pair, is_optimal_pair, behavior_analysis
        )
        
        # Identify key levels to watch
        key_levels = self._identify_key_levels(session, pair)
        
        return {
            'current_session': session.value,
            'session_characteristics': {
                'liquidity': profile.get('liquidity', 'unknown'),
                'volatility': profile.get('volatility', 'unknown'),
                'time_remaining': self._get_session_time_remaining(current_time, session)
            },
            'institutional_behavior': {
                'dominant': profile.get('dominant_behavior', InstitutionalBehavior.RANGE_TRADING).value,
                'probability': behavior_analysis
            },
            'flow_prediction': flow_prediction,
            'pair_suitability': {
                'is_optimal': is_optimal_pair,
                'score': self._calculate_pair_suitability(pair, session),
                'reason': self._get_suitability_reason(pair, session, is_optimal_pair)
            },
            'recommendations': recommendations,
            'key_levels': key_levels,
            'risk_factors': self._identify_session_risks(session, current_time)
        }
    
    def predict_session_transitions(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Predict market behavior during session transitions.
        
        Args:
            current_time: Current time
            
        Returns:
            Session transition predictions
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Identify upcoming transition
        next_session, time_until = self._get_next_session_transition(current_time)
        
        if time_until.total_seconds() > 3600:  # More than 1 hour
            return {
                'transition_imminent': False,
                'next_session': next_session.value,
                'time_until': time_until
            }
        
        # Analyze transition patterns
        current_session = self._identify_session(current_time)
        
        transition_patterns = self._get_transition_patterns(
            current_session, next_session
        )
        
        return {
            'transition_imminent': True,
            'current_session': current_session.value,
            'next_session': next_session.value,
            'time_until': time_until,
            'expected_behavior': transition_patterns['behavior'],
            'volatility_change': transition_patterns['volatility_change'],
            'flow_shift': transition_patterns['flow_shift'],
            'trading_approach': transition_patterns['approach'],
            'risks': transition_patterns['risks']
        }
    
    def get_historical_session_performance(self, pair: str, 
                                         session: SessionType) -> Dict[str, Any]:
        """
        Get historical performance data for pair in specific session.
        
        Args:
            pair: Currency pair
            session: Session type
            
        Returns:
            Historical performance metrics
        """
        # Simplified historical data (in production, query from database)
        historical_data = {
            'EURUSD': {
                SessionType.LONDON: {
                    'average_range': 75,
                    'breakout_success': 0.68,
                    'reversal_success': 0.32,
                    'best_entry_time': 'First 2 hours',
                    'typical_direction': 'Continuation of overnight'
                },
                SessionType.ASIAN: {
                    'average_range': 35,
                    'breakout_success': 0.25,
                    'reversal_success': 0.65,
                    'best_entry_time': 'Range extremes',
                    'typical_direction': 'Range-bound'
                }
            },
            'GBPJPY': {
                SessionType.LONDON: {
                    'average_range': 120,
                    'breakout_success': 0.72,
                    'reversal_success': 0.28,
                    'best_entry_time': 'After initial volatility',
                    'typical_direction': 'Strong trending'
                }
            }
        }
        
        # Get pair data or defaults
        pair_data = historical_data.get(pair.upper(), {})
        session_data = pair_data.get(session, {})
        
        if not session_data:
            # Return generic data
            profile = self.session_profiles.get(session, {})
            return {
                'average_range': 'Unknown',
                'breakout_success': profile.get('breakout_probability', 0.5),
                'reversal_success': profile.get('reversal_probability', 0.5),
                'best_entry_time': 'Use caution',
                'typical_direction': profile.get('trading_style', 'Mixed')
            }
        
        return session_data
    
    def _identify_session(self, current_time: datetime) -> SessionType:
        """Identify current trading session."""
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_time_obj = time(current_hour, current_minute)
        
        # Check weekend first
        if current_time.weekday() >= 5:
            return SessionType.WEEKEND
        
        # Check each session (handling UTC wrap-around)
        for session, (start, end) in self.session_times.items():
            if start <= end:
                # Normal case
                if start <= current_time_obj <= end:
                    return session
            else:
                # Wrap around midnight
                if current_time_obj >= start or current_time_obj <= end:
                    return session
        
        # Default to Asian if no match
        return SessionType.ASIAN
    
    def _analyze_institutional_behavior(self, session: SessionType,
                                      pair: str, current_time: datetime) -> Dict[str, float]:
        """Analyze likely institutional behavior patterns."""
        profile = self.session_profiles.get(session, {})
        behaviors = {}
        
        # Base probabilities from profile
        behaviors['stop_hunting'] = profile.get('stop_hunt_probability', 0.5)
        behaviors['trend_initiation'] = profile.get('breakout_probability', 0.5)
        behaviors['range_trading'] = profile.get('reversal_probability', 0.5)
        behaviors['position_squaring'] = 0.2  # Base probability
        
        # Adjust for time within session
        session_progress = self._get_session_progress(current_time, session)
        
        if session_progress < 0.25:  # First quarter
            behaviors['stop_hunting'] *= 1.3
            behaviors['trend_initiation'] *= 1.2
        elif session_progress > 0.75:  # Last quarter
            behaviors['position_squaring'] *= 2.5
            behaviors['trend_initiation'] *= 0.7
        
        # Normalize probabilities
        total = sum(behaviors.values())
        if total > 0:
            behaviors = {k: v/total for k, v in behaviors.items()}
        
        return behaviors
    
    def _predict_session_flow(self, session: SessionType,
                            current_time: datetime,
                            behavior_analysis: Dict[str, float]) -> Dict[str, Any]:
        """Predict how session will likely unfold."""
        profile = self.session_profiles.get(session, {})
        session_progress = self._get_session_progress(current_time, session)
        
        predictions = {
            'next_hour': '',
            'session_end': '',
            'key_times': [],
            'volatility_forecast': ''
        }
        
        # Predict based on session and progress
        if session == SessionType.ASIAN:
            if session_progress < 0.5:
                predictions['next_hour'] = 'Range formation likely'
                predictions['session_end'] = 'Range established for London'
            else:
                predictions['next_hour'] = 'Range holding or slight expansion'
                predictions['session_end'] = 'Prepare for London breakout'
            predictions['key_times'] = ['London open', 'Tokyo close']
            predictions['volatility_forecast'] = 'Low until London approaches'
            
        elif session == SessionType.LONDON:
            if session_progress < 0.25:
                predictions['next_hour'] = 'Stop hunt then directional move'
                predictions['session_end'] = 'Trend established for NY'
            else:
                predictions['next_hour'] = 'Trend continuation or consolidation'
                predictions['session_end'] = 'Watch for NY continuation'
            predictions['key_times'] = ['First hour', 'NY overlap start']
            predictions['volatility_forecast'] = 'High, especially first 2 hours'
            
        elif session == SessionType.LONDON_NY_OVERLAP:
            predictions['next_hour'] = 'Maximum volatility and liquidity'
            predictions['session_end'] = 'Direction usually set for NY session'
            predictions['key_times'] = ['News releases', 'London close']
            predictions['volatility_forecast'] = 'Extreme - widen stops'
        
        return predictions
    
    def _generate_session_recommendations(self, session: SessionType,
                                        pair: str, is_optimal: bool,
                                        behavior_analysis: Dict[str, float]) -> List[str]:
        """Generate session-specific trading recommendations."""
        recommendations = []
        profile = self.session_profiles.get(session, {})
        
        # Optimal pair recommendation
        if is_optimal:
            recommendations.append(
                f"✅ {pair} is optimal for {session.value} session"
            )
        else:
            best_pairs = profile.get('best_pairs', [])
            if best_pairs:
                recommendations.append(
                    f"💡 Consider {', '.join(best_pairs[:3])} for better {session.value} performance"
                )
        
        # Behavior-based recommendations
        dominant_behavior = max(behavior_analysis.items(), key=lambda x: x[1])
        
        if dominant_behavior[0] == 'stop_hunting':
            recommendations.append(
                "🎯 Expect stop hunts - enter after liquidity sweep"
            )
        elif dominant_behavior[0] == 'trend_initiation':
            recommendations.append(
                "📈 Favor breakouts - trade with initial momentum"
            )
        elif dominant_behavior[0] == 'range_trading':
            recommendations.append(
                "↔️ Range conditions - fade extremes with tight stops"
            )
        elif dominant_behavior[0] == 'position_squaring':
            recommendations.append(
                "🔄 Position unwinding - avoid new positions"
            )
        
        # Trading style recommendation
        style = profile.get('trading_style', '')
        if style:
            recommendations.append(f"📊 {style}")
        
        # Key level note
        key_level_note = profile.get('key_levels', '')
        if key_level_note:
            recommendations.append(f"🔑 {key_level_note}")
        
        return recommendations
    
    def _identify_key_levels(self, session: SessionType, pair: str) -> Dict[str, Any]:
        """Identify key levels to watch for current session."""
        levels = {
            'immediate': [],
            'session_targets': [],
            'notes': []
        }
        
        if session == SessionType.ASIAN:
            levels['immediate'] = ['Previous day high/low', 'Asian range boundaries']
            levels['session_targets'] = ['Form clear range for London']
            levels['notes'] = ['Range extremes become London targets']
            
        elif session == SessionType.LONDON:
            levels['immediate'] = ['Asian high/low', 'Previous day high/low']
            levels['session_targets'] = ['Break Asian range', 'Establish trend']
            levels['notes'] = ['First hour often sets session direction']
            
        elif session == SessionType.LONDON_NY_OVERLAP:
            levels['immediate'] = ['Daily high/low', 'London extremes']
            levels['session_targets'] = ['Liquidity above/below key levels']
            levels['notes'] = ['Maximum stop hunting period']
        
        return levels
    
    def _get_session_progress(self, current_time: datetime, 
                            session: SessionType) -> float:
        """Calculate progress through current session (0-1)."""
        start_time, end_time = self.session_times.get(session, (time(0), time(0)))
        
        current_minutes = current_time.hour * 60 + current_time.minute
        
        # Convert to minutes
        if start_time <= end_time:
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute
            session_duration = end_minutes - start_minutes
        else:
            # Handle wrap around
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = (24 * 60) + (end_time.hour * 60 + end_time.minute)
            session_duration = end_minutes - start_minutes
            
            if current_minutes < start_minutes:
                current_minutes += 24 * 60
        
        progress = (current_minutes - start_minutes) / session_duration
        return max(0, min(1, progress))
    
    def _get_session_time_remaining(self, current_time: datetime,
                                  session: SessionType) -> timedelta:
        """Calculate time remaining in current session."""
        _, end_time = self.session_times.get(session, (time(0), time(0)))
        
        # Create datetime for session end
        end_datetime = datetime.combine(current_time.date(), end_time)
        
        # Handle day wrap
        if end_datetime <= current_time:
            end_datetime += timedelta(days=1)
        
        return end_datetime - current_time
    
    def _calculate_pair_suitability(self, pair: str, session: SessionType) -> float:
        """Calculate suitability score for pair in session."""
        profile = self.session_profiles.get(session, {})
        best_pairs = profile.get('best_pairs', [])
        
        if pair.upper() in best_pairs:
            return 1.0
        
        # Check for partial matches (base currency)
        base_currency = pair[:3].upper() if len(pair) >= 6 else ''
        partial_match_score = 0.7 if any(base_currency in p for p in best_pairs) else 0.3
        
        return partial_match_score
    
    def _get_suitability_reason(self, pair: str, session: SessionType,
                              is_optimal: bool) -> str:
        """Get explanation for pair suitability."""
        if is_optimal:
            return f"{pair} typically performs well during {session.value}"
        
        profile = self.session_profiles.get(session, {})
        
        if profile.get('liquidity') == 'low':
            return f"{pair} may have wider spreads in low liquidity {session.value}"
        elif profile.get('volatility') == 'extreme':
            return f"{pair} subject to extreme volatility during {session.value}"
        else:
            return f"{pair} not typically active during {session.value}"
    
    def _identify_session_risks(self, session: SessionType,
                              current_time: datetime) -> List[str]:
        """Identify session-specific risks."""
        risks = []
        profile = self.session_profiles.get(session, {})
        
        # Liquidity risk
        if profile.get('liquidity') in ['low', 'declining']:
            risks.append('Low liquidity - wider spreads expected')
        
        # Volatility risk
        if profile.get('volatility') in ['extreme', 'high']:
            risks.append('High volatility - use wider stops')
        
        # Stop hunt risk
        if profile.get('stop_hunt_probability', 0) > 0.6:
            risks.append('High stop hunt probability - avoid obvious levels')
        
        # Session-specific risks
        if session == SessionType.NY_CLOSE:
            risks.append('Position squaring - avoid new trends')
        elif session == SessionType.WEEKEND:
            risks.append('Weekend gap risk - reduce exposure')
        
        return risks
    
    def _get_next_session_transition(self, current_time: datetime) -> Tuple[SessionType, timedelta]:
        """Get next session transition time."""
        current_session = self._identify_session(current_time)
        
        # Define session order
        session_order = [
            SessionType.ASIAN,
            SessionType.LONDON,
            SessionType.NEW_YORK,
            SessionType.NY_CLOSE
        ]
        
        # Find next session
        try:
            current_index = session_order.index(current_session)
            next_session = session_order[(current_index + 1) % len(session_order)]
        except ValueError:
            next_session = SessionType.ASIAN
        
        # Calculate time until next session
        next_start, _ = self.session_times.get(next_session, (time(0), time(0)))
        next_datetime = datetime.combine(current_time.date(), next_start)
        
        if next_datetime <= current_time:
            next_datetime += timedelta(days=1)
        
        return next_session, next_datetime - current_time
    
    def _get_transition_patterns(self, current: SessionType,
                               next_session: SessionType) -> Dict[str, Any]:
        """Get patterns for session transitions."""
        transition_patterns = {
            (SessionType.ASIAN, SessionType.LONDON): {
                'behavior': 'Asian range breakout',
                'volatility_change': 'Low to High',
                'flow_shift': 'Accumulation to Distribution',
                'approach': 'Prepare for breakout 30 min before London',
                'risks': ['False breakout before real move', 'Stop hunt common']
            },
            (SessionType.LONDON, SessionType.NEW_YORK): {
                'behavior': 'Trend continuation or reversal',
                'volatility_change': 'High to Higher',
                'flow_shift': 'European to American institutions',
                'approach': 'Watch for continuation or exhaustion',
                'risks': ['Overlap whipsaw', 'News event volatility']
            },
            (SessionType.NEW_YORK, SessionType.ASIAN): {
                'behavior': 'Consolidation and range formation',
                'volatility_change': 'High to Low',
                'flow_shift': 'Distribution to Accumulation',
                'approach': 'Close positions, avoid new trends',
                'risks': ['Overnight gaps', 'Thin liquidity']
            }
        }
        
        pattern = transition_patterns.get((current, next_session), {
            'behavior': 'Standard transition',
            'volatility_change': 'Variable',
            'flow_shift': 'Gradual',
            'approach': 'Monitor for changes',
            'risks': ['General transition volatility']
        })
        
        return pattern


# Example usage
if __name__ == "__main__":
    analyzer = SessionFlow()
    
    # Analyze current session
    result = analyzer.analyze_institutional_flow('EURUSD')
    
    print(f"Current Session: {result['current_session']}")
    print(f"Liquidity: {result['session_characteristics']['liquidity']}")
    print(f"Dominant Behavior: {result['institutional_behavior']['dominant']}")
    
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  {rec}")
    
    print("\nKey Levels:")
    for level_type, levels in result['key_levels'].items():
        if levels:
            print(f"  {level_type}: {levels}")
    
    # Check session transition
    transition = analyzer.predict_session_transitions()
    if transition['transition_imminent']:
        print(f"\n⚠️ Session transition in {transition['time_until']}")
        print(f"Expected: {transition['expected_behavior']}")