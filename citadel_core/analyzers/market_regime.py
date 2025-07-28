"""
Market Regime Analyzer - Detect current market conditions

Purpose: Identify market state (trending, ranging, volatile) to properly scale
CITADEL's protective sensitivity and provide context for shield scoring.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING_CALM = "ranging_calm"
    RANGING_VOLATILE = "ranging_volatile"
    BREAKOUT = "breakout"
    NEWS_DRIVEN = "news_driven"
    UNDEFINED = "undefined"


class TradingSession(Enum):
    """Trading session classifications"""
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"
    OVERLAP_LONDON_NY = "overlap_london_ny"
    WEEKEND = "weekend"


class MarketRegimeAnalyzer:
    """
    Analyzes current market conditions to provide context for shield scoring.
    Detects trends, volatility, session characteristics, and news impacts.
    """
    
    def __init__(self):
        # Session time ranges (UTC)
        self.session_ranges = {
            'ASIAN': (23, 8),      # 23:00 - 08:00 UTC
            'LONDON': (7, 16),     # 07:00 - 16:00 UTC  
            'NEW_YORK': (12, 21),  # 12:00 - 21:00 UTC
        }
        
        # Known high-impact news times (can be updated dynamically)
        self.high_impact_events = {
            'NFP': 'first_friday_1330',
            'FOMC': 'wednesday_1800',
            'ECB': 'thursday_1145',
            'BOE': 'thursday_1100'
        }
        
    def analyze(self, pair: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze current market regime and conditions.
        
        Args:
            pair: Currency pair (e.g., 'EURUSD')
            market_data: Market data including price history, indicators
            
        Returns:
            Dict containing regime analysis
        """
        try:
            # Get current time context or use enhanced session data
            current_time = datetime.utcnow()
            
            # Check if we have enhanced session data from broker stream
            if 'session' in market_data:
                session_str = market_data['session']
                session_map = {
                    'asian': TradingSession.ASIAN,
                    'london': TradingSession.LONDON, 
                    'new_york': TradingSession.NEW_YORK,
                    'overlap_london_ny': TradingSession.OVERLAP_LONDON_NY
                }
                session = session_map.get(session_str, self._identify_session(current_time))
            else:
                session = self._identify_session(current_time)
            
            # Analyze trend state - enhanced with real data
            trend_analysis = self._analyze_trend(market_data)
            
            # Measure volatility - use real ATR and percentile if available
            volatility_analysis = self._analyze_volatility(market_data)
            
            # Detect regime
            regime = self._classify_regime(trend_analysis, volatility_analysis)
            
            # Check for news events
            news_analysis = self._analyze_news_impact(current_time, pair)
            
            # Get session-specific characteristics
            session_chars = self._get_session_characteristics(session, pair)
            
            result = {
                'regime': regime.value,
                'trend': trend_analysis['direction'],
                'trend_strength': trend_analysis['strength'],
                'volatility': volatility_analysis['level'],
                'volatility_percentile': volatility_analysis['percentile'],
                'session': session.value,
                'session_characteristics': session_chars,
                'news_risk': news_analysis['risk_level'],
                'news_events': news_analysis['upcoming_events'],
                'regime_stability': self._assess_regime_stability(market_data),
                'recommended_sensitivity': self._recommend_sensitivity(regime, volatility_analysis)
            }
            
            logger.info(f"Market regime for {pair}: {regime.value} in {session.value} session")
            return result
            
        except Exception as e:
            logger.error(f"Market regime analysis error: {str(e)}")
            return self._get_default_analysis()
    
    def _identify_session(self, current_time: datetime) -> TradingSession:
        """Identify current trading session."""
        hour = current_time.hour
        weekday = current_time.weekday()
        
        # Weekend check
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return TradingSession.WEEKEND
            
        # Check for overlaps first
        london_start, london_end = self.session_ranges['LONDON']
        ny_start, ny_end = self.session_ranges['NEW_YORK']
        
        if london_start <= hour < ny_end and ny_start <= hour < london_end:
            return TradingSession.OVERLAP_LONDON_NY
            
        # Check individual sessions
        for session_name, (start, end) in self.session_ranges.items():
            if start <= hour < end:
                return TradingSession[session_name]
                
        # Default to Asian if no match
        return TradingSession.ASIAN
    
    def _analyze_trend(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trend direction and strength."""
        # Extract moving averages
        ma_fast = market_data.get('ma_20', [])
        ma_slow = market_data.get('ma_50', [])
        ma_long = market_data.get('ma_200', [])
        
        # Extract price data
        closes = market_data.get('closes', [])
        
        if not closes or len(closes) < 20:
            return {'direction': 'neutral', 'strength': 0}
            
        # Current price position
        current_price = closes[-1]
        
        # Trend direction based on MA alignment
        direction = 'neutral'
        strength = 0
        
        if ma_fast and ma_slow and len(ma_fast) > 0 and len(ma_slow) > 0:
            # Bullish: price > fast MA > slow MA
            if current_price > ma_fast[-1] > ma_slow[-1]:
                direction = 'bullish'
                strength = 3
                if ma_long and len(ma_long) > 0 and ma_slow[-1] > ma_long[-1]:
                    strength = 5  # Strong bull trend
                    
            # Bearish: price < fast MA < slow MA
            elif current_price < ma_fast[-1] < ma_slow[-1]:
                direction = 'bearish'
                strength = 3
                if ma_long and len(ma_long) > 0 and ma_slow[-1] < ma_long[-1]:
                    strength = 5  # Strong bear trend
                    
        # Additional trend strength from price action
        if len(closes) >= 20:
            recent_trend = (closes[-1] - closes[-20]) / closes[-20] * 100
            
            if abs(recent_trend) > 2:  # Strong directional move
                strength = min(strength + 1, 5)
            elif abs(recent_trend) < 0.5:  # Ranging
                strength = max(strength - 1, 0)
                direction = 'neutral' if strength < 2 else direction
                
        return {
            'direction': direction,
            'strength': strength,
            'ma_alignment': self._check_ma_alignment(ma_fast, ma_slow, ma_long)
        }
    
    def _analyze_volatility(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current volatility levels."""
        # Use enhanced volatility data if available
        if 'volatility_percentile' in market_data:
            percentile = market_data['volatility_percentile']
            current_atr = market_data.get('atr', 0)
            
            # Determine volatility level based on real percentile
            if percentile >= 80:
                level = 'high'
            elif percentile >= 60:
                level = 'elevated'  
            elif percentile <= 20:
                level = 'low'
            else:
                level = 'normal'
                
            # Calculate ratio if we have history
            atr_history = market_data.get('atr_history', [])
            if atr_history and len(atr_history) >= 10:
                avg_atr = sum(atr_history) / len(atr_history)
                volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
            else:
                volatility_ratio = 1.0
                
            return {
                'level': level,
                'percentile': percentile,
                'ratio': round(volatility_ratio, 2),
                'atr_value': current_atr,
                'real_data': True
            }
        
        # Fallback to original logic
        atr = market_data.get('atr', 0)
        atr_history = market_data.get('atr_history', [])
        
        if not atr_history or len(atr_history) < 20:
            return {'level': 'normal', 'percentile': 50, 'ratio': 1.0}
            
        # Calculate volatility percentile
        sorted_atr = sorted(atr_history)
        percentile = (sorted_atr.index(atr) / len(sorted_atr)) * 100 if atr in sorted_atr else 50
        
        # Average ATR
        avg_atr = sum(atr_history) / len(atr_history)
        volatility_ratio = atr / avg_atr if avg_atr > 0 else 1.0
        
        # Classify volatility level
        if percentile >= 80 or volatility_ratio > 1.5:
            level = 'high'
        elif percentile >= 60 or volatility_ratio > 1.2:
            level = 'elevated'
        elif percentile <= 20 or volatility_ratio < 0.7:
            level = 'low'
        else:
            level = 'normal'
            
        return {
            'level': level,
            'percentile': round(percentile, 1),
            'ratio': round(volatility_ratio, 2),
            'atr_value': atr
        }
    
    def _classify_regime(self, trend: Dict[str, Any], volatility: Dict[str, Any]) -> MarketRegime:
        """Classify the market regime based on trend and volatility."""
        trend_dir = trend['direction']
        trend_strength = trend['strength']
        vol_level = volatility['level']
        
        # Strong trending markets
        if trend_strength >= 4:
            if trend_dir == 'bullish':
                return MarketRegime.TRENDING_BULL
            elif trend_dir == 'bearish':
                return MarketRegime.TRENDING_BEAR
                
        # Breakout conditions
        if vol_level == 'high' and trend_strength >= 3:
            return MarketRegime.BREAKOUT
            
        # Ranging markets
        if trend_dir == 'neutral' or trend_strength <= 2:
            if vol_level in ['high', 'elevated']:
                return MarketRegime.RANGING_VOLATILE
            else:
                return MarketRegime.RANGING_CALM
                
        # Moderate trends
        if trend_strength == 3:
            if trend_dir == 'bullish':
                return MarketRegime.TRENDING_BULL
            elif trend_dir == 'bearish':
                return MarketRegime.TRENDING_BEAR
                
        return MarketRegime.UNDEFINED
    
    def _analyze_news_impact(self, current_time: datetime, pair: str) -> Dict[str, Any]:
        """Analyze upcoming news events and their potential impact."""
        upcoming_events = []
        risk_level = "🟢"  # Green = low risk
        
        # Check for major events in next 2 hours
        for event_name, schedule in self.high_impact_events.items():
            # Simplified news checking - in production, integrate with economic calendar API
            if self._is_event_upcoming(current_time, schedule):
                # Check if event affects this pair
                if self._event_affects_pair(event_name, pair):
                    upcoming_events.append({
                        'name': event_name,
                        'time_until': 'Within 2 hours',
                        'impact': 'HIGH'
                    })
                    risk_level = "🔴"  # Red = high risk
                    
        # Medium impact events (placeholder for real calendar integration)
        if not upcoming_events and current_time.hour in [8, 13, 14]:
            risk_level = "🟡"  # Yellow = medium risk
            
        return {
            'risk_level': risk_level,
            'upcoming_events': upcoming_events,
            'news_trading_window': len(upcoming_events) > 0
        }
    
    def _is_event_upcoming(self, current_time: datetime, schedule: str) -> bool:
        """Check if scheduled event is upcoming (simplified)."""
        # This is a placeholder - integrate with real economic calendar
        return False
    
    def _event_affects_pair(self, event: str, pair: str) -> bool:
        """Check if news event affects the currency pair."""
        event_currencies = {
            'NFP': ['USD'],
            'FOMC': ['USD'],
            'ECB': ['EUR'],
            'BOE': ['GBP']
        }
        
        affected_currencies = event_currencies.get(event, [])
        return any(curr in pair.upper() for curr in affected_currencies)
    
    def _get_session_characteristics(self, session: TradingSession, pair: str) -> Dict[str, Any]:
        """Get characteristics specific to current session and pair."""
        characteristics = {
            TradingSession.ASIAN: {
                'typical_range': 'low',
                'breakout_probability': 0.2,
                'reversal_probability': 0.3,
                'best_pairs': ['USDJPY', 'AUDUSD', 'NZDUSD']
            },
            TradingSession.LONDON: {
                'typical_range': 'high',
                'breakout_probability': 0.6,
                'reversal_probability': 0.4,
                'best_pairs': ['EURUSD', 'GBPUSD', 'EURGBP']
            },
            TradingSession.NEW_YORK: {
                'typical_range': 'high',
                'breakout_probability': 0.5,
                'reversal_probability': 0.5,
                'best_pairs': ['EURUSD', 'GBPUSD', 'USDCAD']
            },
            TradingSession.OVERLAP_LONDON_NY: {
                'typical_range': 'very_high',
                'breakout_probability': 0.7,
                'reversal_probability': 0.6,
                'best_pairs': ['EURUSD', 'GBPUSD', 'XAUUSD']
            },
            TradingSession.WEEKEND: {
                'typical_range': 'none',
                'breakout_probability': 0,
                'reversal_probability': 0,
                'best_pairs': []
            }
        }
        
        session_data = characteristics.get(session, {})
        session_data['is_optimal_pair'] = pair.upper() in session_data.get('best_pairs', [])
        
        return session_data
    
    def _assess_regime_stability(self, market_data: Dict[str, Any]) -> str:
        """Assess how stable the current regime is."""
        # Check for regime changes in recent history
        regime_changes = market_data.get('regime_change_count', 0)
        
        if regime_changes == 0:
            return 'stable'
        elif regime_changes <= 2:
            return 'transitioning'
        else:
            return 'unstable'
    
    def _recommend_sensitivity(self, regime: MarketRegime, volatility: Dict[str, Any]) -> str:
        """Recommend CITADEL sensitivity level based on conditions."""
        # High sensitivity = more protective, lower scores
        # Low sensitivity = less protective, higher scores
        
        if regime == MarketRegime.NEWS_DRIVEN:
            return 'maximum'
        elif regime in [MarketRegime.BREAKOUT, MarketRegime.RANGING_VOLATILE]:
            return 'high'
        elif regime in [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR]:
            if volatility['level'] == 'high':
                return 'medium'
            else:
                return 'low'
        elif regime == MarketRegime.RANGING_CALM:
            return 'medium'
        else:
            return 'medium'
    
    def _check_ma_alignment(self, ma_fast: List[float], ma_slow: List[float], 
                           ma_long: List[float]) -> str:
        """Check moving average alignment."""
        if not ma_fast or not ma_slow:
            return 'undefined'
            
        if ma_long and len(ma_long) > 0:
            if ma_fast[-1] > ma_slow[-1] > ma_long[-1]:
                return 'bullish_aligned'
            elif ma_fast[-1] < ma_slow[-1] < ma_long[-1]:
                return 'bearish_aligned'
                
        return 'mixed'
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when error occurs."""
        return {
            'regime': MarketRegime.UNDEFINED.value,
            'trend': 'neutral',
            'trend_strength': 0,
            'volatility': 'normal',
            'volatility_percentile': 50,
            'session': TradingSession.LONDON.value,
            'session_characteristics': {},
            'news_risk': "🟡",
            'news_events': [],
            'regime_stability': 'unknown',
            'recommended_sensitivity': 'medium'
        }


# Example usage
if __name__ == "__main__":
    analyzer = MarketRegimeAnalyzer()
    
    # Test market data
    test_market_data = {
        'closes': [1.0850, 1.0855, 1.0860, 1.0858, 1.0865, 1.0870, 1.0868, 
                   1.0872, 1.0875, 1.0878, 1.0880, 1.0882, 1.0885, 1.0883,
                   1.0887, 1.0890, 1.0892, 1.0895, 1.0893, 1.0898],
        'ma_20': [1.0860, 1.0862, 1.0865, 1.0868, 1.0870],
        'ma_50': [1.0840, 1.0842, 1.0845, 1.0848, 1.0850],
        'ma_200': [1.0800, 1.0802, 1.0805, 1.0808, 1.0810],
        'atr': 0.0045,
        'atr_history': [0.0035, 0.0038, 0.0040, 0.0042, 0.0045, 0.0043, 
                        0.0041, 0.0039, 0.0037, 0.0036, 0.0038, 0.0040,
                        0.0042, 0.0044, 0.0046, 0.0045, 0.0043, 0.0041,
                        0.0039, 0.0038]
    }
    
    result = analyzer.analyze('EURUSD', test_market_data)
    print("Market Regime Analysis:")
    for key, value in result.items():
        print(f"  {key}: {value}")