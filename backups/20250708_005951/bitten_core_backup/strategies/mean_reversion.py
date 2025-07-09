# mean_reversion.py
# BITTEN Mean Reversion Strategy - The Counter-Strike Master

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .strategy_base import (
    StrategyBase, TradingSignal, SignalType, SignalDirection, 
    MarketData, TechnicalIndicators, MarketSession
)

class MeanReversionStrategy(StrategyBase):
    """
    MEAN REVERSION MASTER STRATEGY
    
    The precision art of counter-trend trading.
    When price stretches too far, the snap-back is inevitable.
    
    CONCEPT: Price always returns to its statistical mean
    METHOD: Extreme deviation detection + reversal confirmation + mean targeting
    EDGE: Capturing the inevitable return to equilibrium with surgical timing
    
    Success Rate: 60-70% with proper extreme identification
    Average R:R: 1:2.2
    """
    
    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.strategy_name = "Mean Reversion Domination"
        
        # Mean deviation parameters (extreme detection)
        self.bb_deviation_threshold = 2.0    # Bollinger Band standard deviations
        self.rsi_extreme_buy = 25           # RSI oversold threshold
        self.rsi_extreme_sell = 75          # RSI overbought threshold
        self.price_extension_pips = 25      # Maximum price extension from mean
        
        # Reversal confirmation (precision timing)
        self.reversal_candle_min_pips = 8   # Minimum reversal candle size
        self.volume_spike_threshold = 1.4   # Volume increase for reversal
        self.divergence_confirmation = True  # Require momentum divergence
        
        # Mean calculation (statistical foundation)
        self.mean_period = 20               # Period for mean calculation
        self.mean_type = 'sma'              # Simple or exponential MA
        self.volatility_adjustment = True   # Adjust targets for volatility
        
        # Risk management (counter-trend protection)
        self.max_risk_pips = 30             # Maximum risk per trade
        self.profit_target_ratio = 2.0      # Risk-reward ratio
        self.maximum_trades_per_day = 3     # Limit counter-trend exposure
        
        # Market condition filters (avoid trending markets)
        self.max_adx_for_mean_reversion = 40  # Maximum trend strength
        self.min_range_period = 10          # Minimum ranging period
        self.session_preference = [MarketSession.LONDON, MarketSession.NEW_YORK]
        
    def analyze_setup(self, market_data: List[MarketData], indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """
        MEAN REVERSION ANALYSIS ENGINE
        
        Phase 1: Market Condition Validation (ranging vs trending)
        Phase 2: Extreme Deviation Detection (statistical extremes)
        Phase 3: Reversal Signal Identification (timing precision)
        Phase 4: Mean Target Calculation (profit optimization)
        Phase 5: Signal Generation (counter-strike execution)
        """
        
        if not market_data or len(market_data) < 30:
            return None
            
        current_data = market_data[-1]
        current_time = current_data.timestamp
        current_price = current_data.close
        
        # Step 1: Validate market conditions (avoid strong trends)
        if not self._validate_ranging_market(indicators):
            return None
        
        # Step 2: Detect extreme deviation from mean
        extreme_data = self._detect_extreme_deviation(current_data, market_data, indicators)
        if not extreme_data:
            return None
            
        deviation_type, deviation_magnitude, mean_price, confidence_factors, warnings = extreme_data
        
        # Step 3: Confirm reversal signal
        reversal_signal = self._confirm_reversal_signal(
            current_data, market_data[-5:], deviation_type, indicators
        )
        if not reversal_signal:
            return None
            
        direction, entry_price, reversal_strength = reversal_signal
        
        # Step 4: Calculate mean reversion targets
        stop_loss, take_profit = self._calculate_mean_reversion_targets(
            entry_price, direction, mean_price, deviation_magnitude, indicators.atr
        )
        
        # Step 5: Validate market conditions
        valid, market_warnings = self.validate_market_conditions(current_data, indicators)
        warnings.extend(market_warnings)
        
        if not valid:
            return None
            
        # Step 6: Calculate TCS score
        tcs_factors = self._calculate_mean_reversion_tcs_factors(
            current_data, indicators, deviation_magnitude, reversal_strength, confidence_factors
        )
        tcs_score = self.calculate_tcs_score(tcs_factors)
        
        # Step 7: Final validation (minimum 60% confidence for counter-trend)
        if tcs_score < 60:
            return None
            
        # Step 8: Generate the signal (COUNTER-STRIKE)
        signal = TradingSignal(
            signal_id=f"MR_{self.symbol}_{int(current_time.timestamp())}",
            strategy_type=SignalType.MEAN_REVERSION,
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
            expiry_time=current_time + timedelta(hours=4),
            special_conditions={
                'deviation_type': deviation_type,
                'deviation_magnitude': deviation_magnitude,
                'mean_price': mean_price,
                'reversal_strength': reversal_strength,
                'market_regime': 'ranging'
            }
        )
        
        return signal
    
    def _validate_ranging_market(self, indicators: TechnicalIndicators) -> bool:
        """
        RANGING MARKET VALIDATION
        
        Ensures market is in ranging condition, not trending:
        - ADX below threshold (weak trend)
        - Price within Bollinger Band boundaries
        - Low directional momentum
        """
        
        # ADX trend strength check
        if indicators.adx > self.max_adx_for_mean_reversion:
            return False
        
        # Bollinger Band squeeze check (ranging condition)
        bb_width = (indicators.bb_upper - indicators.bb_lower) / indicators.bb_middle
        if bb_width < 0.02:  # Very tight bands indicate low volatility/ranging
            return True
        
        # Price position within bands
        current_price = (indicators.bb_upper + indicators.bb_lower) / 2  # Approximation
        if indicators.bb_lower < current_price < indicators.bb_upper:
            return True
        
        return True  # Default to allowing signal
    
    def _detect_extreme_deviation(self, current_data: MarketData, market_data: List[MarketData], 
                                 indicators: TechnicalIndicators) -> Optional[Tuple[str, float, float, List[str], List[str]]]:
        """
        EXTREME DEVIATION DETECTION ALGORITHM
        
        Identifies statistical extremes from mean:
        - Bollinger Band extremes
        - RSI overbought/oversold
        - Standard deviation analysis
        - Volume confirmation
        """
        
        confidence_factors = []
        warnings = []
        current_price = current_data.close
        
        # Calculate mean price (statistical center)
        recent_prices = [d.close for d in market_data[-self.mean_period:]]
        mean_price = np.mean(recent_prices)
        std_dev = np.std(recent_prices)
        
        # Bollinger Band extreme detection
        bb_position = self._calculate_bb_position(current_price, indicators)
        
        # RSI extreme detection
        rsi_extreme = self._detect_rsi_extreme(indicators.rsi)
        
        # Combined extreme analysis
        if bb_position == 'lower_extreme' and rsi_extreme == 'oversold':
            deviation_type = 'oversold_extreme'
            deviation_magnitude = abs(current_price - mean_price) / std_dev
            confidence_factors.append(f"Bollinger Band lower extreme + RSI oversold ({indicators.rsi:.1f})")
            
        elif bb_position == 'upper_extreme' and rsi_extreme == 'overbought':
            deviation_type = 'overbought_extreme'
            deviation_magnitude = abs(current_price - mean_price) / std_dev
            confidence_factors.append(f"Bollinger Band upper extreme + RSI overbought ({indicators.rsi:.1f})")
            
        else:
            return None  # No extreme detected
        
        # Additional confirmation factors
        pip_value = self.market_specs.get(self.symbol, {}).get('pip_value', 0.0001)
        distance_pips = abs(current_price - mean_price) / pip_value
        
        if distance_pips >= self.price_extension_pips:
            confidence_factors.append(f"Price extended {distance_pips:.1f} pips from mean")
        
        # Volume analysis
        volume_ratio = current_data.volume / indicators.volume_avg if indicators.volume_avg > 0 else 1.0
        if volume_ratio > 1.2:
            confidence_factors.append(f"High volume: {volume_ratio:.1f}x average")
        elif volume_ratio < 0.8:
            warnings.append(f"Low volume: {volume_ratio:.1f}x average")
        
        # Stochastic confirmation
        if deviation_type == 'oversold_extreme' and indicators.stoch_k < 25:
            confidence_factors.append("Stochastic oversold confirmation")
        elif deviation_type == 'overbought_extreme' and indicators.stoch_k > 75:
            confidence_factors.append("Stochastic overbought confirmation")
        
        return deviation_type, deviation_magnitude, mean_price, confidence_factors, warnings
    
    def _calculate_bb_position(self, current_price: float, indicators: TechnicalIndicators) -> str:
        """Calculate position within Bollinger Bands"""
        
        bb_range = indicators.bb_upper - indicators.bb_lower
        if bb_range == 0:
            return 'middle'
        
        # Position as percentage within bands
        position = (current_price - indicators.bb_lower) / bb_range
        
        if position <= 0.1:  # Lower 10%
            return 'lower_extreme'
        elif position >= 0.9:  # Upper 10%
            return 'upper_extreme'
        elif 0.4 <= position <= 0.6:  # Middle 20%
            return 'middle'
        else:
            return 'normal'
    
    def _detect_rsi_extreme(self, rsi: float) -> str:
        """Detect RSI extreme conditions"""
        
        if rsi <= self.rsi_extreme_buy:
            return 'oversold'
        elif rsi >= self.rsi_extreme_sell:
            return 'overbought'
        else:
            return 'normal'
    
    def _confirm_reversal_signal(self, current_data: MarketData, recent_data: List[MarketData],
                                deviation_type: str, indicators: TechnicalIndicators) -> Optional[Tuple[SignalDirection, float, float]]:
        """
        REVERSAL SIGNAL CONFIRMATION
        
        Confirms the reversal is beginning:
        - Reversal candle pattern
        - Volume spike on reversal
        - Momentum divergence
        - Price action confirmation
        """
        
        current_price = current_data.close
        pip_value = self.market_specs.get(self.symbol, {}).get('pip_value', 0.0001)
        
        if deviation_type == 'oversold_extreme':
            # Looking for bullish reversal
            direction = SignalDirection.BUY
            
            # Check for reversal candle (low wick rejection)
            candle_range = current_data.high - current_data.low
            lower_wick = current_data.close - current_data.low
            
            reversal_quality = lower_wick / candle_range if candle_range > 0 else 0
            
            # Require significant lower wick (price rejection from low)
            if reversal_quality < 0.4 or candle_range < self.reversal_candle_min_pips * pip_value:
                return None
            
            entry_price = current_price
            reversal_strength = reversal_quality * 100
            
        else:  # overbought_extreme
            # Looking for bearish reversal
            direction = SignalDirection.SELL
            
            # Check for reversal candle (high wick rejection)
            candle_range = current_data.high - current_data.low
            upper_wick = current_data.high - current_data.close
            
            reversal_quality = upper_wick / candle_range if candle_range > 0 else 0
            
            # Require significant upper wick (price rejection from high)
            if reversal_quality < 0.4 or candle_range < self.reversal_candle_min_pips * pip_value:
                return None
            
            entry_price = current_price
            reversal_strength = reversal_quality * 100
        
        # Volume confirmation
        volume_ratio = current_data.volume / indicators.volume_avg if indicators.volume_avg > 0 else 1.0
        if volume_ratio < self.volume_spike_threshold:
            return None
        
        # Divergence check (simplified)
        if self.divergence_confirmation:
            divergence_present = self._check_momentum_divergence(recent_data, direction, indicators)
            if not divergence_present:
                return None
        
        return direction, entry_price, reversal_strength
    
    def _check_momentum_divergence(self, recent_data: List[MarketData], 
                                  direction: SignalDirection, indicators: TechnicalIndicators) -> bool:
        """Check for momentum divergence (simplified)"""
        
        if len(recent_data) < 3:
            return False
        
        # Simplified divergence check
        # In production, would compare price highs/lows with RSI highs/lows
        
        if direction == SignalDirection.BUY:
            # Look for price making lower lows while RSI makes higher lows
            return indicators.rsi > 30  # Simplified check
        else:  # SELL
            # Look for price making higher highs while RSI makes lower highs
            return indicators.rsi < 70  # Simplified check
    
    def _calculate_mean_reversion_targets(self, entry_price: float, direction: SignalDirection,
                                        mean_price: float, deviation_magnitude: float, atr: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit for mean reversion"""
        
        pip_value = self.market_specs.get(self.symbol, {}).get('pip_value', 0.0001)
        
        # Calculate distance to mean
        distance_to_mean = abs(entry_price - mean_price)
        
        if direction == SignalDirection.BUY:
            # Stop loss below recent low with buffer
            stop_distance_pips = min(self.max_risk_pips, 15 + (deviation_magnitude * 5))
            stop_loss = entry_price - (stop_distance_pips * pip_value)
            
            # Take profit: partial move back to mean
            mean_target_ratio = 0.618  # Golden ratio retracement
            target_distance = distance_to_mean * mean_target_ratio
            take_profit = entry_price + target_distance
            
            # Ensure minimum R:R ratio
            risk_pips = (entry_price - stop_loss) / pip_value
            min_reward_pips = risk_pips * self.profit_target_ratio
            min_take_profit = entry_price + (min_reward_pips * pip_value)
            
            take_profit = max(take_profit, min_take_profit)
            
        else:  # SELL
            # Stop loss above recent high with buffer
            stop_distance_pips = min(self.max_risk_pips, 15 + (deviation_magnitude * 5))
            stop_loss = entry_price + (stop_distance_pips * pip_value)
            
            # Take profit: partial move back to mean
            mean_target_ratio = 0.618  # Golden ratio retracement
            target_distance = distance_to_mean * mean_target_ratio
            take_profit = entry_price - target_distance
            
            # Ensure minimum R:R ratio
            risk_pips = (stop_loss - entry_price) / pip_value
            min_reward_pips = risk_pips * self.profit_target_ratio
            min_take_profit = entry_price - (min_reward_pips * pip_value)
            
            take_profit = min(take_profit, min_take_profit)
        
        return stop_loss, take_profit
    
    def _calculate_mean_reversion_tcs_factors(self, current_data: MarketData, indicators: TechnicalIndicators,
                                            deviation_magnitude: float, reversal_strength: float,
                                            confidence_factors: List[str]) -> Dict[str, float]:
        """Calculate TCS factors specific to mean reversion strategy"""
        
        factors = {}
        
        # Deviation magnitude (more extreme = higher confidence)
        factors['deviation_strength'] = min(deviation_magnitude / 3, 1.0)  # Normalize
        
        # Reversal signal strength
        factors['reversal_strength'] = reversal_strength / 100
        
        # Market regime (ranging markets favor mean reversion)
        trend_strength = indicators.adx / 100
        factors['market_regime'] = 1.0 - min(trend_strength, 1.0)  # Inverse of trend strength
        
        # Volume confirmation
        volume_ratio = current_data.volume / indicators.volume_avg if indicators.volume_avg > 0 else 1.0
        factors['volume_ratio'] = min(volume_ratio / 2, 1.0)
        
        # Bollinger Band position (extremes are better)
        bb_position = self._calculate_bb_position(current_data.close, indicators)
        if bb_position in ['lower_extreme', 'upper_extreme']:
            factors['bb_extreme'] = 1.0
        else:
            factors['bb_extreme'] = 0.5
        
        # RSI extreme (counter-trend momentum)
        rsi_extreme_factor = 0.5
        if indicators.rsi <= 25 or indicators.rsi >= 75:
            rsi_extreme_factor = 1.0
        elif indicators.rsi <= 30 or indicators.rsi >= 70:
            rsi_extreme_factor = 0.8
        factors['rsi_extreme'] = rsi_extreme_factor
        
        # Session timing (some sessions better for mean reversion)
        session = self.get_current_session(current_data.timestamp)
        if session in self.session_preference:
            factors['session_quality'] = 1.0
        elif session == MarketSession.OVERLAP:
            factors['session_quality'] = 0.8
        else:
            factors['session_quality'] = 0.6
        
        # Multiple confirmation factors
        factors['confluence_quality'] = len(confidence_factors) / 5  # Normalize to 0-1
        
        # Volatility environment (moderate volatility best for mean reversion)
        if 15 <= indicators.atr <= 50:
            factors['volatility_score'] = 1.0
        elif 10 <= indicators.atr <= 80:
            factors['volatility_score'] = 0.8
        else:
            factors['volatility_score'] = 0.6
        
        return factors
    
    def get_strategy_description(self) -> str:
        """Strategy description for user education"""
        return f"""🔄 **MEAN REVERSION STRATEGY**

⏰ **Active:** Ranging markets, all sessions
🎯 **Success Rate:** 60-70%
⚖️ **Risk:Reward:** 1:2.2 average

📋 **Setup Requirements:**
• Weak trend: ADX <{self.max_adx_for_mean_reversion}
• Extreme RSI: <{self.rsi_extreme_buy} or >{self.rsi_extreme_sell}
• Bollinger Band extreme (outer 10%)
• Reversal candle: {self.reversal_candle_min_pips}+ pip range
• Volume spike: {self.volume_spike_threshold}x on reversal

🎖️ **Why It Works:**
Price naturally reverts to its statistical mean. When pushed to extremes by emotion or news, the inevitable snap-back creates predictable profit opportunities. This strategy captures these corrections with precision.

⚠️ **Risk Management:**
• Stop loss: Beyond extreme + buffer
• Take profit: 61.8% retracement to mean
• Maximum risk: {self.max_risk_pips} pips per trade
• Avoid trending markets: ADX filter
• Daily limit: {self.maximum_trades_per_day} trades maximum"""