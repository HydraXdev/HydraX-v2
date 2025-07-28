# market_analyzer.py
# BITTEN Market Analysis Engine - The All-Seeing Eye

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from .strategy_base import MarketData, MarketSession

@dataclass
class MarketStructure:
    """Current market structure analysis"""
    trend: str  # 'bullish', 'bearish', 'ranging'
    strength: float  # 0-100
    key_levels: List[Tuple[float, str, float]]  # (price, type, strength)
    volatility_regime: str  # 'low', 'normal', 'high', 'extreme'
    session_quality: float  # 0-1
    liquidity_score: float  # 0-1

class MarketAnalyzer:
    """
    REAL-TIME MARKET ANALYSIS ENGINE
    
    Continuously monitors market conditions to optimize strategy selection.
    This is the brain that decides WHICH strategy to use WHEN.
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        
        # Market memory (rolling windows)
        self.price_history = deque(maxlen=500)
        self.volume_history = deque(maxlen=100)
        self.spread_history = deque(maxlen=50)
        
        # Dynamic level tracking
        self.support_levels = []
        self.resistance_levels = []
        self.psychological_levels = []
        self.last_level_update = None
        
        # Market regime detection
        self.regime_lookback = 50
        self.trend_threshold_adx = 25
        self.ranging_threshold_atr = 30
        
        # Strategy performance tracking
        self.strategy_performance = {
            'london_breakout': deque(maxlen=20),
            'support_resistance': deque(maxlen=20),
            'momentum_continuation': deque(maxlen=20),
            'mean_reversion': deque(maxlen=20)}
        
    def update_market_data(self, market_data: MarketData) -> None:
        """Update market analysis with new data"""
        
        self.price_history.append({
            'timestamp': market_data.timestamp,
            'open': market_data.open,
            'high': market_data.high,
            'low': market_data.low,
            'close': market_data.close})
        
        self.volume_history.append(market_data.volume)
        self.spread_history.append(market_data.spread)
        
        # Update levels every hour
        if (self.last_level_update is None or 
            market_data.timestamp - self.last_level_update > timedelta(hours=1)):
            self._update_key_levels()
            self.last_level_update = market_data.timestamp
    
    def analyze_market_structure(self) -> MarketStructure:
        """
        COMPREHENSIVE MARKET STRUCTURE ANALYSIS
        
        Determines optimal trading approach based on current conditions.
        """
        
        if len(self.price_history) < 50:
            return self._default_structure()
        
        # 1. Trend Analysis
        trend, trend_strength = self._analyze_trend()
        
        # 2. Key Level Identification
        key_levels = self._get_nearby_key_levels()
        
        # 3. Volatility Regime
        volatility_regime = self._analyze_volatility_regime()
        
        # 4. Session Quality
        session_quality = self._calculate_session_quality()
        
        # 5. Liquidity Analysis
        liquidity_score = self._analyze_liquidity()
        
        return MarketStructure(
            trend=trend,
            strength=trend_strength,
            key_levels=key_levels,
            volatility_regime=volatility_regime,
            session_quality=session_quality,
            liquidity_score=liquidity_score
        )
    
    def get_optimal_strategy(self, market_structure: MarketStructure) -> str:
        """
        STRATEGY SELECTION ALGORITHM
        
        Chooses the best strategy for current market conditions.
        """
        
        scores = {}
        
        # London Breakout scoring
        london_score = 0
        current_hour = datetime.now().hour
        if 7 <= current_hour <= 10:  # London window
            london_score += 40
        if market_structure.volatility_regime in ['normal', 'high']:
            london_score += 20
        if market_structure.session_quality > 0.8:
            london_score += 20
        if self._get_strategy_win_rate('london_breakout') > 0.7:
            london_score += 20
        scores['london_breakout'] = london_score
        
        # Support/Resistance scoring
        sr_score = 0
        if len(market_structure.key_levels) > 0:
            nearest_level = market_structure.key_levels[0]
            if nearest_level[2] > 0.7:  # Strong level nearby
                sr_score += 40
        if market_structure.trend == 'ranging':
            sr_score += 30
        if market_structure.volatility_regime in ['low', 'normal']:
            sr_score += 15
        if self._get_strategy_win_rate('support_resistance') > 0.7:
            sr_score += 15
        scores['support_resistance'] = sr_score
        
        # Momentum Continuation scoring
        momentum_score = 0
        if market_structure.trend in ['bullish', 'bearish']:
            momentum_score += 30
        if market_structure.strength > 70:  # Strong trend
            momentum_score += 30
        if market_structure.volatility_regime == 'normal':
            momentum_score += 20
        if market_structure.liquidity_score > 0.8:
            momentum_score += 20
        scores['momentum_continuation'] = momentum_score
        
        # Mean Reversion scoring
        reversion_score = 0
        if market_structure.trend == 'ranging':
            reversion_score += 40
        if market_structure.strength < 30:  # Weak trend
            reversion_score += 20
        if market_structure.volatility_regime in ['low', 'normal']:
            reversion_score += 20
        if self._is_at_extreme():
            reversion_score += 20
        scores['mean_reversion'] = reversion_score
        
        # Return highest scoring strategy
        return max(scores, key=scores.get)
    
    def get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions for validation"""
        
        if not self.price_history:
            return self._default_conditions()
        
        current_price = self.price_history[-1]['close']
        
        # Calculate current metrics
        spread = np.mean(list(self.spread_history)) if self.spread_history else 2.0
        volume_avg = np.mean(list(self.volume_history)) if self.volume_history else 1000
        current_volume = self.volume_history[-1] if self.volume_history else 1000
        
        # ATR calculation
        atr = self._calculate_current_atr()
        
        # Trend direction
        trend_direction = self._get_simple_trend_direction()
        
        # Check proximity to key levels
        near_key_level = self._is_near_key_level(current_price)
        
        return {
            'spread': spread,
            'normal_spread': 2.0,  # Would be dynamic in production
            'atr': atr,
            'volume_ratio': current_volume / volume_avg if volume_avg > 0 else 1.0,
            'trend_direction': trend_direction,
            'near_key_level': near_key_level,
            'session': self._get_current_session()}
    
    def _analyze_trend(self) -> Tuple[str, float]:
        """Analyze current trend direction and strength"""
        
        if len(self.price_history) < self.regime_lookback:
            return 'ranging', 50.0
        
        prices = [p['close'] for p in list(self.price_history)[-self.regime_lookback:]]
        
        # Simple trend detection using linear regression
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        
        # Normalize slope to pip movement
        pip_value = 0.0001 if not self.symbol.endswith('JPY') else 0.01
        pip_slope = slope / pip_value
        
        # Determine trend
        if abs(pip_slope) < 0.5:  # Less than 0.5 pips per period
            trend = 'ranging'
            strength = 30.0
        elif pip_slope > 0:
            trend = 'bullish'
            strength = min(100, abs(pip_slope) * 20)
        else:
            trend = 'bearish'
            strength = min(100, abs(pip_slope) * 20)
        
        return trend, strength
    
    def _analyze_volatility_regime(self) -> str:
        """Determine current volatility regime"""
        
        atr = self._calculate_current_atr()
        
        if atr < 15:
            return 'low'
        elif atr < 50:
            return 'normal'
        elif atr < 100:
            return 'high'
        else:
            return 'extreme'
    
    def _calculate_current_atr(self) -> float:
        """Calculate current ATR in pips"""
        
        if len(self.price_history) < 14:
            return 30.0  # Default
        
        ranges = []
        history_list = list(self.price_history)[-14:]
        
        for i in range(1, len(history_list)):
            high = history_list[i]['high']
            low = history_list[i]['low']
            prev_close = history_list[i-1]['close']
            
            true_range = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            ranges.append(true_range)
        
        pip_value = 0.0001 if not self.symbol.endswith('JPY') else 0.01
        atr_pips = (np.mean(ranges) / pip_value) if ranges else 30.0
        
        return atr_pips
    
    def _update_key_levels(self) -> None:
        """Update support/resistance levels"""
        
        if len(self.price_history) < 100:
            return
        
        prices = [p['high'] for p in list(self.price_history)] + \
                [p['low'] for p in list(self.price_history)]
        
        # Simple level detection using price clustering
        self.support_levels = []
        self.resistance_levels = []
        
        current_price = self.price_history[-1]['close']
        
        # Find levels (simplified)
        price_levels = np.percentile(prices, [10, 25, 50, 75, 90])
        
        for level in price_levels:
            if level < current_price:
                self.support_levels.append((level, 'support', 0.7))
            else:
                self.resistance_levels.append((level, 'resistance', 0.7))
    
    def _get_nearby_key_levels(self) -> List[Tuple[float, str, float]]:
        """Get key levels near current price"""
        
        if not self.price_history:
            return []
        
        current_price = self.price_history[-1]['close']
        pip_value = 0.0001 if not self.symbol.endswith('JPY') else 0.01
        max_distance = 50 * pip_value  # 50 pips
        
        nearby_levels = []
        
        # Check all levels
        all_levels = self.support_levels + self.resistance_levels
        
        for level, level_type, strength in all_levels:
            distance = abs(current_price - level)
            if distance <= max_distance:
                nearby_levels.append((level, level_type, strength))
        
        # Sort by distance
        nearby_levels.sort(key=lambda x: abs(current_price - x[0]))
        
        return nearby_levels[:5]  # Top 5 nearest
    
    def _calculate_session_quality(self) -> float:
        """Calculate current session quality score"""
        
        session = self._get_current_session()
        
        base_scores = {
            MarketSession.LONDON: 0.9,
            MarketSession.NEW_YORK: 0.85,
            MarketSession.OVERLAP: 1.0,
            MarketSession.TOKYO: 0.7,
            MarketSession.SYDNEY: 0.6,
            MarketSession.DEAD_ZONE: 0.3}
        
        score = base_scores.get(session, 0.5)
        
        # Adjust for liquidity
        if self.volume_history:
            recent_volume = np.mean(list(self.volume_history)[-10:])
            avg_volume = np.mean(list(self.volume_history))
            if recent_volume > avg_volume * 1.2:
                score = min(1.0, score + 0.1)
        
        return score
    
    def _analyze_liquidity(self) -> float:
        """Analyze current market liquidity"""
        
        if not self.volume_history or not self.spread_history:
            return 0.5
        
        # Volume component
        recent_volume = np.mean(list(self.volume_history)[-5:])
        avg_volume = np.mean(list(self.volume_history))
        volume_score = min(1.0, recent_volume / avg_volume) if avg_volume > 0 else 0.5
        
        # Spread component
        recent_spread = np.mean(list(self.spread_history)[-5:])
        spread_score = max(0, 1.0 - (recent_spread / 5.0))  # Normalize to 5 pip max
        
        return (volume_score + spread_score) / 2
    
    def _get_strategy_win_rate(self, strategy: str) -> float:
        """Get recent win rate for a strategy"""
        
        if strategy not in self.strategy_performance:
            return 0.5
        
        results = list(self.strategy_performance[strategy])
        if not results:
            return 0.5
        
        wins = sum(1 for r in results if r)
        return wins / len(results)
    
    def _is_at_extreme(self) -> bool:
        """Check if price is at statistical extreme"""
        
        if len(self.price_history) < 20:
            return False
        
        prices = [p['close'] for p in list(self.price_history)[-20:]]
        current_price = prices[-1]
        
        mean = np.mean(prices)
        std = np.std(prices)
        
        z_score = abs(current_price - mean) / std if std > 0 else 0
        
        return z_score > 2.0  # 2 standard deviations
    
    def _get_simple_trend_direction(self) -> str:
        """Simple trend direction for conditions"""
        
        if len(self.price_history) < 20:
            return 'neutral'
        
        prices = [p['close'] for p in list(self.price_history)[-20:]]
        
        if prices[-1] > prices[0]:
            return 'up'
        elif prices[-1] < prices[0]:
            return 'down'
        else:
            return 'neutral'
    
    def _is_near_key_level(self, price: float) -> bool:
        """Check if price is near a key level"""
        
        levels = self._get_nearby_key_levels()
        if not levels:
            return False
        
        pip_value = 0.0001 if not self.symbol.endswith('JPY') else 0.01
        proximity = 10 * pip_value  # 10 pips
        
        for level, _, strength in levels:
            if abs(price - level) <= proximity and strength > 0.6:
                return True
        
        return False
    
    def _get_current_session(self) -> MarketSession:
        """Get current trading session"""
        
        utc_hour = datetime.utcnow().hour
        
        if 8 <= utc_hour < 17:
            if 13 <= utc_hour < 17:
                return MarketSession.OVERLAP
            return MarketSession.LONDON
        elif 13 <= utc_hour < 22:
            return MarketSession.NEW_YORK
        elif 0 <= utc_hour < 9:
            return MarketSession.TOKYO
        elif utc_hour >= 22 or utc_hour < 7:
            return MarketSession.SYDNEY
        else:
            return MarketSession.DEAD_ZONE
    
    def _default_structure(self) -> MarketStructure:
        """Default market structure when insufficient data"""
        
        return MarketStructure(
            trend='ranging',
            strength=50.0,
            key_levels=[],
            volatility_regime='normal',
            session_quality=0.5,
            liquidity_score=0.5
        )
    
    def _default_conditions(self) -> Dict[str, Any]:
        """Default market conditions"""
        
        return {
            'spread': 2.0,
            'normal_spread': 2.0,
            'atr': 30.0,
            'volume_ratio': 1.0,
            'trend_direction': 'neutral',
            'near_key_level': False,
            'session': MarketSession.DEAD_ZONE}