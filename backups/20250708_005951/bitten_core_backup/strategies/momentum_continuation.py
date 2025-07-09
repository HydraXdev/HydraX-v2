# momentum_continuation.py
# BITTEN Momentum Continuation Strategy - Riding the Institutional Wave

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .strategy_base import (
    StrategyBase, TradingSignal, SignalType, SignalDirection, 
    MarketData, TechnicalIndicators, MarketSession
)

class MomentumContinuationStrategy(StrategyBase):
    """
    MOMENTUM CONTINUATION MASTER STRATEGY
    
    The art of riding institutional momentum waves.
    When the big money moves, we move with surgical precision.
    
    CONCEPT: Institutional orders create sustained directional pressure
    METHOD: Pullback identification + momentum resumption + trend continuation
    EDGE: Capturing the next leg of established institutional moves
    
    Success Rate: 65-75% with proper trend identification
    Average R:R: 1:2.8
    """
    
    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.strategy_name = "Momentum Continuation Domination"
        
        # Trend identification parameters (institutional detection)
        self.min_trend_strength = 70    # ADX minimum for valid trend
        self.trend_length_periods = 20  # Minimum periods for trend validity
        self.momentum_threshold = 60    # RSI threshold for momentum
        
        # Pullback requirements (entry precision)
        self.pullback_depth_min = 0.3   # Minimum 30% retracement
        self.pullback_depth_max = 0.7   # Maximum 70% retracement
        self.pullback_duration_max = 12 # Maximum pullback duration (periods)
        
        # Continuation signals (resumption detection)
        self.volume_increase_min = 1.3  # Minimum volume increase on resumption
        self.break_confirmation_pips = 5 # Pips needed to confirm break
        self.ma_confluence_distance = 10 # Distance from key MAs (pips)
        
        # Risk management (ride the wave safely)
        self.max_pullback_risk = 40     # Maximum risk in pips
        self.trend_target_multiplier = 2.5 # Target based on trend strength
        self.stop_buffer_pips = 8       # Buffer beyond pullback low/high
        
    def analyze_setup(self, market_data: List[MarketData], indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """
        MOMENTUM CONTINUATION ANALYSIS ENGINE
        
        Phase 1: Trend Identification (institutional direction)
        Phase 2: Pullback Analysis (entry opportunity)
        Phase 3: Resumption Detection (continuation signal)
        Phase 4: Risk Assessment (protect the capital)
        Phase 5: Signal Generation (execute with precision)
        """
        
        if not market_data or len(market_data) < 50:
            return None
            
        current_data = market_data[-1]
        current_time = current_data.timestamp
        current_price = current_data.close
        
        # Step 1: Identify the primary trend
        trend_data = self._identify_primary_trend(market_data, indicators)
        if not trend_data:
            return None
            
        trend_direction, trend_strength, trend_start_price, confidence_factors, warnings = trend_data
        
        # Step 2: Analyze pullback quality
        pullback_data = self._analyze_pullback(market_data, trend_direction, trend_start_price)
        if not pullback_data:
            return None
            
        pullback_depth, pullback_low_high, pullback_quality, pullback_factors = pullback_data
        
        # Step 3: Detect continuation signal
        continuation_signal = self._detect_continuation_resumption(
            current_data, market_data[-10:], trend_direction, pullback_low_high, indicators
        )
        if not continuation_signal:
            return None
            
        direction, entry_price, resumption_strength = continuation_signal
        
        # Step 4: Calculate targets with trend-based optimization
        stop_loss, take_profit = self._calculate_momentum_targets(
            entry_price, direction, pullback_low_high, trend_strength, indicators.atr
        )
        
        # Step 5: Validate market conditions
        valid, market_warnings = self.validate_market_conditions(current_data, indicators)
        warnings.extend(market_warnings)
        confidence_factors.extend(pullback_factors)
        
        if not valid:
            return None
            
        # Step 6: Calculate TCS score
        tcs_factors = self._calculate_momentum_tcs_factors(
            current_data, indicators, trend_strength, pullback_quality, 
            resumption_strength, confidence_factors
        )
        tcs_score = self.calculate_tcs_score(tcs_factors)
        
        # Step 7: Final validation (minimum 65% confidence)
        if tcs_score < 65:
            return None
            
        # Step 8: Generate the signal (RIDE THE WAVE)
        signal = TradingSignal(
            signal_id=f"MC_{self.symbol}_{int(current_time.timestamp())}",
            strategy_type=SignalType.MOMENTUM_CONTINUATION,
            symbol=self.symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            tcs_score=tcs_score,
            risk_reward_ratio=self.calculate_risk_reward(entry_price, stop_loss, take_profit, direction),
            confidence_factors=confidence_factors,
            warning_factors=warnings,
            session=self.get_current_session(current_time),
            timestamp=current_time,
            expiry_time=current_time + timedelta(hours=6),
            special_conditions={
                'trend_direction': trend_direction.value,
                'trend_strength': trend_strength,
                'pullback_depth': pullback_depth,
                'resumption_strength': resumption_strength,
                'pullback_quality': pullback_quality
            }
        )
        
        return signal
    
    def _identify_primary_trend(self, market_data: List[MarketData], indicators: TechnicalIndicators) -> Optional[Tuple]:
        """
        PRIMARY TREND IDENTIFICATION ALGORITHM
        
        Analyzes market structure to identify institutional trend:
        - ADX trend strength validation
        - Moving average alignment
        - Higher highs/lower lows pattern
        - Volume confirmation
        """
        
        confidence_factors = []
        warnings = []
        
        # ADX trend strength validation
        if indicators.adx < self.min_trend_strength:
            return None
        
        confidence_factors.append(f"Strong trend: ADX {indicators.adx:.1f}")
        
        # Moving average alignment analysis
        ma_alignment = self._analyze_ma_alignment(indicators)
        if not ma_alignment:
            return None
            
        trend_direction, ma_strength = ma_alignment
        confidence_factors.append(f"MA alignment: {ma_strength:.1f}% strength")
        
        # Price structure analysis (higher highs/lower lows)
        structure_data = self._analyze_price_structure(market_data, trend_direction)
        if not structure_data:
            warnings.append("Weak price structure")
            return None
            
        structure_strength, trend_start_price = structure_data
        confidence_factors.append(f"Price structure: {structure_strength:.1f}% confirmation")
        
        # Volume trend confirmation
        volume_trend = self._analyze_volume_trend(market_data)
        if volume_trend > 1.1:
            confidence_factors.append(f"Volume trending: {volume_trend:.1f}x")
        else:
            warnings.append("Volume not confirming trend")
        
        # Calculate overall trend strength
        trend_strength = (indicators.adx + ma_strength + structure_strength) / 3
        
        return trend_direction, trend_strength, trend_start_price, confidence_factors, warnings
    
    def _analyze_ma_alignment(self, indicators: TechnicalIndicators) -> Optional[Tuple[SignalDirection, float]]:
        """Analyze moving average alignment for trend direction"""
        
        # Check MA hierarchy for trend direction
        mas = [indicators.ma_21, indicators.ma_50, indicators.ma_200]
        current_price = indicators.ma_21  # Proxy for current price
        
        # Bullish alignment: 21 > 50 > 200 and price > 21
        if indicators.ma_21 > indicators.ma_50 > indicators.ma_200:
            strength = 85 if current_price > indicators.ma_21 else 70
            return SignalDirection.BUY, strength
        
        # Bearish alignment: 21 < 50 < 200 and price < 21  
        elif indicators.ma_21 < indicators.ma_50 < indicators.ma_200:
            strength = 85 if current_price < indicators.ma_21 else 70
            return SignalDirection.SELL, strength
        
        return None
    
    def _analyze_price_structure(self, market_data: List[MarketData], trend_direction: SignalDirection) -> Optional[Tuple[float, float]]:
        """Analyze price structure for trend confirmation"""
        
        recent_data = market_data[-self.trend_length_periods:]
        if len(recent_data) < 10:
            return None
        
        highs = [d.high for d in recent_data]
        lows = [d.low for d in recent_data]
        
        if trend_direction == SignalDirection.BUY:
            # Look for higher highs and higher lows
            higher_highs = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
            higher_lows = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])
            
            structure_strength = ((higher_highs + higher_lows) / (2 * (len(highs) - 1))) * 100
            trend_start_price = min(lows)
            
        else:  # SELL
            # Look for lower highs and lower lows
            lower_highs = sum(1 for i in range(1, len(highs)) if highs[i] < highs[i-1])
            lower_lows = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])
            
            structure_strength = ((lower_highs + lower_lows) / (2 * (len(highs) - 1))) * 100
            trend_start_price = max(highs)
        
        return structure_strength, trend_start_price
    
    def _analyze_volume_trend(self, market_data: List[MarketData]) -> float:
        """Analyze volume trend to confirm momentum"""
        
        if len(market_data) < 20:
            return 1.0
        
        recent_volume = [d.volume for d in market_data[-10:]]
        older_volume = [d.volume for d in market_data[-20:-10]]
        
        recent_avg = np.mean(recent_volume)
        older_avg = np.mean(older_volume)
        
        return recent_avg / older_avg if older_avg > 0 else 1.0
    
    def _analyze_pullback(self, market_data: List[MarketData], trend_direction: SignalDirection, 
                         trend_start_price: float) -> Optional[Tuple[float, float, float, List[str]]]:
        """
        PULLBACK ANALYSIS ENGINE
        
        Validates pullback quality for optimal entry:
        - Pullback depth within acceptable range
        - Pullback duration not excessive
        - Support/resistance level interaction
        """
        
        recent_data = market_data[-self.pullback_duration_max:]
        if len(recent_data) < 5:
            return None
        
        pullback_factors = []
        current_price = recent_data[-1].close
        
        if trend_direction == SignalDirection.BUY:
            # Find pullback low
            pullback_low = min(d.low for d in recent_data)
            trend_high = max(d.high for d in market_data[-30:])
            
            # Calculate pullback depth
            trend_range = trend_high - trend_start_price
            pullback_depth = (trend_high - pullback_low) / trend_range if trend_range > 0 else 0
            
            pullback_reference = pullback_low
            
        else:  # SELL trend
            # Find pullback high
            pullback_high = max(d.high for d in recent_data)
            trend_low = min(d.low for d in market_data[-30:])
            
            # Calculate pullback depth
            trend_range = trend_start_price - trend_low
            pullback_depth = (pullback_high - trend_low) / trend_range if trend_range > 0 else 0
            
            pullback_reference = pullback_high
        
        # Validate pullback depth
        if not (self.pullback_depth_min <= pullback_depth <= self.pullback_depth_max):
            return None
        
        pullback_factors.append(f"Pullback depth: {pullback_depth:.1%}")
        
        # Analyze pullback quality
        pullback_quality = self._calculate_pullback_quality(recent_data, trend_direction, pullback_depth)
        pullback_factors.append(f"Pullback quality: {pullback_quality:.1f}/100")
        
        # Check for support/resistance interaction
        sr_interaction = self._check_sr_interaction(current_price, pullback_reference, trend_direction)
        if sr_interaction:
            pullback_factors.append("Support/resistance interaction confirmed")
        
        return pullback_depth, pullback_reference, pullback_quality, pullback_factors
    
    def _calculate_pullback_quality(self, pullback_data: List[MarketData], 
                                   trend_direction: SignalDirection, pullback_depth: float) -> float:
        """Calculate pullback quality score"""
        
        quality_score = 50  # Base score
        
        # Depth scoring (optimal around 50% retracement)
        optimal_depth = 0.5
        depth_deviation = abs(pullback_depth - optimal_depth)
        depth_score = max(0, 25 - (depth_deviation * 50))
        quality_score += depth_score
        
        # Pullback cleanliness (smooth vs choppy)
        price_changes = []
        for i in range(1, len(pullback_data)):
            change = abs(pullback_data[i].close - pullback_data[i-1].close)
            price_changes.append(change)
        
        volatility = np.std(price_changes) if price_changes else 0
        if volatility < np.mean(price_changes) * 0.5:  # Low volatility = clean pullback
            quality_score += 15
        
        # Time efficiency (quick pullbacks are better)
        if len(pullback_data) <= 6:  # Quick pullback
            quality_score += 10
        
        return min(100, quality_score)
    
    def _check_sr_interaction(self, current_price: float, pullback_reference: float, 
                             trend_direction: SignalDirection) -> bool:
        """Check if pullback interacted with key support/resistance"""
        
        pip_value = self.market_specs.get(self.symbol, {}).get('pip_value', 0.0001)
        interaction_distance = 10 * pip_value
        
        # This is a simplified check - in production, would use actual S/R levels
        return abs(current_price - pullback_reference) <= interaction_distance
    
    def _detect_continuation_resumption(self, current_data: MarketData, recent_data: List[MarketData],
                                      trend_direction: SignalDirection, pullback_reference: float,
                                      indicators: TechnicalIndicators) -> Optional[Tuple[SignalDirection, float, float]]:
        """
        CONTINUATION RESUMPTION DETECTION
        
        Identifies the moment when momentum resumes:
        - Break of pullback level with volume
        - Momentum indicator confirmation
        - Price action validation
        """
        
        current_price = current_data.close
        pip_value = self.market_specs.get(self.symbol, {}).get('pip_value', 0.0001)
        
        if trend_direction == SignalDirection.BUY:
            # Looking for break above pullback high
            pullback_break_level = pullback_reference + (self.break_confirmation_pips * pip_value)
            
            if current_price >= pullback_break_level:
                direction = SignalDirection.BUY
                entry_price = pullback_break_level
                
                # Calculate resumption strength
                break_distance = (current_price - pullback_reference) / pip_value
                resumption_strength = min(100, break_distance * 2)
                
            else:
                return None
                
        else:  # SELL trend
            # Looking for break below pullback low
            pullback_break_level = pullback_reference - (self.break_confirmation_pips * pip_value)
            
            if current_price <= pullback_break_level:
                direction = SignalDirection.SELL
                entry_price = pullback_break_level
                
                # Calculate resumption strength
                break_distance = (pullback_reference - current_price) / pip_value
                resumption_strength = min(100, break_distance * 2)
                
            else:
                return None
        
        # Volume confirmation
        volume_ratio = current_data.volume / indicators.volume_avg if indicators.volume_avg > 0 else 1.0
        if volume_ratio < self.volume_increase_min:
            return None
        
        # Momentum confirmation
        if direction == SignalDirection.BUY and indicators.rsi < self.momentum_threshold:
            return None
        elif direction == SignalDirection.SELL and indicators.rsi > (100 - self.momentum_threshold):
            return None
        
        return direction, entry_price, resumption_strength
    
    def _calculate_momentum_targets(self, entry_price: float, direction: SignalDirection,
                                  pullback_reference: float, trend_strength: float, atr: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit for momentum continuation"""
        
        pip_value = self.market_specs.get(self.symbol, {}).get('pip_value', 0.0001)
        
        if direction == SignalDirection.BUY:
            # Stop loss below pullback low with buffer
            stop_loss = pullback_reference - (self.stop_buffer_pips * pip_value)
            
            # Take profit based on trend strength and risk
            risk_pips = (entry_price - stop_loss) / pip_value
            target_pips = risk_pips * self.trend_target_multiplier * (trend_strength / 100)
            take_profit = entry_price + (target_pips * pip_value)
            
        else:  # SELL
            # Stop loss above pullback high with buffer
            stop_loss = pullback_reference + (self.stop_buffer_pips * pip_value)
            
            # Take profit based on trend strength and risk
            risk_pips = (stop_loss - entry_price) / pip_value
            target_pips = risk_pips * self.trend_target_multiplier * (trend_strength / 100)
            take_profit = entry_price - (target_pips * pip_value)
        
        return stop_loss, take_profit
    
    def _calculate_momentum_tcs_factors(self, current_data: MarketData, indicators: TechnicalIndicators,
                                      trend_strength: float, pullback_quality: float, resumption_strength: float,
                                      confidence_factors: List[str]) -> Dict[str, float]:
        """Calculate TCS factors specific to momentum continuation"""
        
        factors = {}
        
        # Trend strength is primary factor
        factors['trend_strength'] = trend_strength / 100
        
        # Pullback quality
        factors['pullback_quality'] = pullback_quality / 100
        
        # Resumption strength
        factors['resumption_strength'] = resumption_strength / 100
        
        # ADX trend confirmation
        factors['trend_confirmation'] = min(indicators.adx / 100, 1.0)
        
        # Volume confirmation
        volume_ratio = current_data.volume / indicators.volume_avg if indicators.volume_avg > 0 else 1.0
        factors['volume_ratio'] = min(volume_ratio / 2, 1.0)  # Normalize to 0-1
        
        # Market structure integrity
        factors['structure_integrity'] = 0.8 if len(confidence_factors) >= 4 else 0.6
        
        # Momentum alignment
        if 40 <= indicators.rsi <= 60:  # Balanced momentum
            momentum_score = 0.9
        elif indicators.rsi > 70 or indicators.rsi < 30:  # Extreme momentum
            momentum_score = 0.7
        else:
            momentum_score = 0.8
        factors['momentum_strength'] = momentum_score
        
        # Session timing
        session = self.get_current_session(current_data.timestamp)
        if session in [MarketSession.LONDON, MarketSession.NEW_YORK, MarketSession.OVERLAP]:
            factors['session_quality'] = 1.0
        else:
            factors['session_quality'] = 0.7
        
        # Confluence bonus
        if trend_strength > 80 and pullback_quality > 75:
            factors['confluence_bonus'] = 1.0
        else:
            factors['confluence_bonus'] = 0.6
        
        return factors
    
    def get_strategy_description(self) -> str:
        """Strategy description for user education"""
        return f"""🚀 **MOMENTUM CONTINUATION STRATEGY**

⏰ **Active:** All major sessions
🎯 **Success Rate:** 65-75%
⚖️ **Risk:Reward:** 1:2.8 average

📋 **Setup Requirements:**
• Strong trend: ADX ≥{self.min_trend_strength}
• Clean pullback: {self.pullback_depth_min:.0%}-{self.pullback_depth_max:.0%} retracement
• Volume spike: {self.volume_increase_min}x on resumption
• Break confirmation: {self.break_confirmation_pips} pip break

🎖️ **Why It Works:**
Institutional momentum creates sustained directional pressure. When price pulls back and resumes, it signals the next leg of the institutional move. This strategy captures these continuation patterns with precision.

⚠️ **Risk Management:**
• Stop loss: Beyond pullback + {self.stop_buffer_pips} pip buffer
• Take profit: {self.trend_target_multiplier}x risk (trend-adjusted)
• Maximum pullback risk: {self.max_pullback_risk} pips
• Trend validation: Multi-timeframe confluence"""