# strategy_base.py
# BITTEN Master Strategy Framework - Foundation for Elite Trading Algorithms

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pytz

class SignalType(Enum):
    """Elite trading signal classifications"""
    LONDON_BREAKOUT = "london_breakout"
    SUPPORT_RESISTANCE = "support_resistance"  
    MOMENTUM_CONTINUATION = "momentum_continuation"
    MEAN_REVERSION = "mean_reversion"
    MIDNIGHT_HAMMER = "midnight_hammer"
    EMERGENCY_EXIT = "emergency_exit"

class SignalDirection(Enum):
    """Military precision direction commands"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"

class MarketSession(Enum):
    """Trading session identification"""
    LONDON = "london"
    NEW_YORK = "new_york"
    TOKYO = "tokyo"
    SYDNEY = "sydney"
    OVERLAP = "overlap"
    DEAD_ZONE = "dead_zone"

@dataclass
class MarketData:
    """Real-time market data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    spread: float
    timeframe: str

@dataclass
class TechnicalIndicators:
    """Comprehensive technical analysis suite"""
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    adx: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    ma_21: float
    ma_50: float
    ma_200: float
    volume_avg: float
    atr: float
    stoch_k: float
    stoch_d: float

@dataclass
class TradingSignal:
    """Master signal output - The Moment of Truth"""
    signal_id: str
    strategy_type: SignalType
    symbol: str
    direction: SignalDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    tcs_score: int  # Tactical Confidence Score (0-100)
    risk_reward_ratio: float
    confidence_factors: List[str]
    warning_factors: List[str]
    session: MarketSession
    timestamp: datetime
    expiry_time: datetime
    position_size_multiplier: float = 1.0
    special_conditions: Optional[Dict] = None

class StrategyBase(ABC):
    """Master Strategy Framework - Foundation of BITTEN's Trading Supremacy"""
    
    def __init__(self, symbol: str, timeframes: List[str] = None):
        self.symbol = symbol
        self.timeframes = timeframes or ['M15', 'H1', 'H4', 'D1']
        self.name = self.__class__.__name__
        
        # Market specifications for elite precision
        self.market_specs = {
            'GBPUSD': {'pip_value': 0.0001, 'spread_avg': 1.5, 'volatility_avg': 80},
            'EURUSD': {'pip_value': 0.0001, 'spread_avg': 1.2, 'volatility_avg': 70},
            'USDJPY': {'pip_value': 0.01, 'spread_avg': 1.8, 'volatility_avg': 75},
            'GBPJPY': {'pip_value': 0.01, 'spread_avg': 2.5, 'volatility_avg': 120},
            'USDCAD': {'pip_value': 0.0001, 'spread_avg': 2.0, 'volatility_avg': 65}
        }
        
        # Risk management parameters (institutional grade)
        self.max_spread_multiplier = 2.0
        self.min_atr_pips = 10
        self.max_atr_pips = 150
        self.news_blackout_minutes = 30
        
    @abstractmethod
    def analyze_setup(self, market_data: List[MarketData], indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """Core strategy logic - Where the magic happens"""
        pass
    
    def calculate_tcs_score(self, factors: Dict[str, float]) -> int:
        """Tactical Confidence Score Algorithm - Using TCS++ Engine"""
        # Import the TCS++ engine
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
        from core.tcs_engine import score_tcs, classify_trade
        
        # Convert factors to signal_data format for TCS++ engine
        signal_data = {
            # Volume and momentum
            'volume_ratio': factors.get('volume_ratio', 1.0),
            'momentum_strength': factors.get('momentum_strength', 0.5),
            
            # Structure and patterns
            'trend_clarity': factors.get('structure_integrity', 0.5),
            'sr_quality': factors.get('sr_strength', 0.5),
            'pattern_complete': factors.get('pattern_completion', False),
            'pattern_forming': factors.get('pattern_forming', False),
            
            # Timeframe alignment
            'M15_aligned': factors.get('M15_aligned', False),
            'H1_aligned': factors.get('H1_aligned', False),
            'H4_aligned': factors.get('H4_aligned', False),
            'D1_aligned': factors.get('D1_aligned', False),
            
            # Market conditions
            'atr': factors.get('atr', 20),
            'spread_ratio': factors.get('spread_ratio', 1.0),
            'volatility_stable': not factors.get('extreme_volatility', False),
            
            # Session info
            'session': self._map_session(factors.get('session', 'unknown')),
            
            # Technical indicators
            'rsi': factors.get('rsi', 50),
            'macd_aligned': factors.get('macd_aligned', False),
            'macd_divergence': factors.get('divergence_present', False),
            
            # Liquidity patterns
            'liquidity_grab': factors.get('liquidity_grab', False),
            'stop_hunt_detected': factors.get('stop_hunt', False),
            'near_institutional_level': factors.get('institutional_levels', False),
            
            # Risk/Reward
            'rr': factors.get('risk_reward', 2.0),
            
            # AI bonus
            'ai_sentiment_bonus': factors.get('ai_bonus', 0)
        }
        
        # Handle timeframe alignment if provided as single score
        if 'timeframe_alignment' in factors:
            alignment = factors['timeframe_alignment']
            if alignment > 0.8:
                signal_data.update({'M15_aligned': True, 'H1_aligned': True, 
                                   'H4_aligned': True, 'D1_aligned': True})
            elif alignment > 0.6:
                signal_data.update({'H1_aligned': True, 'H4_aligned': True})
            elif alignment > 0.4:
                signal_data.update({'H4_aligned': True})
        
        # Calculate score using TCS++ engine
        score = score_tcs(signal_data)
        
        # Store classification for reference
        if 'risk_reward' in factors:
            trade_type = classify_trade(score, factors['risk_reward'], signal_data)
            factors['trade_classification'] = trade_type
        
        # Store breakdown for transparency
        factors['tcs_breakdown'] = signal_data.get('tcs_breakdown', {})
        
        return score
    
    def _map_session(self, session_str: str) -> str:
        """Map session string to TCS++ engine format"""
        session_map = {
            'london': 'london',
            'new_york': 'new_york',
            'newyork': 'new_york',
            'ny': 'new_york',
            'tokyo': 'tokyo',
            'sydney': 'sydney',
            'overlap': 'overlap',
            'dead': 'dead_zone',
            'deadzone': 'dead_zone'
        }
        return session_map.get(session_str.lower(), 'unknown')
    
    def get_current_session(self, timestamp: datetime) -> MarketSession:
        """Identify current trading session for tactical advantage"""
        utc_time = timestamp.replace(tzinfo=pytz.UTC)
        hour = utc_time.hour
        
        # London: 08:00-17:00 UTC
        if 8 <= hour < 17:
            # NY Overlap: 13:00-17:00 UTC
            if 13 <= hour < 17:
                return MarketSession.OVERLAP
            return MarketSession.LONDON
        
        # New York: 13:00-22:00 UTC
        elif 13 <= hour < 22:
            return MarketSession.NEW_YORK
        
        # Tokyo: 00:00-09:00 UTC
        elif 0 <= hour < 9:
            return MarketSession.TOKYO
        
        # Sydney: 22:00-07:00 UTC (next day)
        elif hour >= 22 or hour < 7:
            return MarketSession.SYDNEY
        
        return MarketSession.DEAD_ZONE
    
    def calculate_position_size(self, account_balance: float, risk_percent: float, 
                              stop_loss_pips: int, tier_multiplier: float = 1.0) -> float:
        """Elite position sizing - Protect the capital, maximize the profits"""
        pip_value = self.market_specs.get(self.symbol, {}).get('pip_value', 0.0001)
        
        # Risk amount in account currency
        risk_amount = account_balance * (risk_percent / 100)
        
        # Calculate lot size based on stop loss
        if self.symbol.endswith('JPY'):
            pip_dollar_value = pip_value * 100000  # Standard lot
        else:
            pip_dollar_value = pip_value * 100000
        
        raw_lot_size = risk_amount / (stop_loss_pips * pip_dollar_value)
        
        # Apply tier multiplier (CHAINGUN, LEROY, etc.)
        adjusted_lot_size = raw_lot_size * tier_multiplier
        
        # Normalize to broker standards
        return round(adjusted_lot_size, 2)
    
    def validate_market_conditions(self, market_data: MarketData, indicators: TechnicalIndicators) -> Tuple[bool, List[str]]:
        """Market condition validation - Never trade in bad weather"""
        warnings = []
        valid = True
        
        # Spread validation (protect from broker theft)
        normal_spread = self.market_specs.get(self.symbol, {}).get('spread_avg', 2.0)
        if market_data.spread > normal_spread * self.max_spread_multiplier:
            warnings.append(f"High spread: {market_data.spread} pips")
            valid = False
        
        # Volatility validation (avoid chaos)
        if indicators.atr < self.min_atr_pips:
            warnings.append(f"Low volatility: {indicators.atr} pips ATR")
        elif indicators.atr > self.max_atr_pips:
            warnings.append(f"Extreme volatility: {indicators.atr} pips ATR")
            valid = False
        
        # Volume validation (institutional participation)
        if hasattr(indicators, 'volume_ratio'):
            if indicators.volume_avg < 0.5:
                warnings.append("Low volume environment")
        
        # News event proximity (avoid manipulation)
        if self.is_news_time(market_data.timestamp):
            warnings.append("News event proximity")
            valid = False
        
        return valid, warnings
    
    def is_news_time(self, timestamp: datetime) -> bool:
        """News event detection - Avoid the market manipulation"""
        # High-impact news times (UTC)
        news_times = [
            (8, 30),   # London open economic data
            (13, 30),  # US economic data
            (14, 0),   # FOMC announcements
            (14, 15),  # ECB announcements
        ]
        
        current_time = (timestamp.hour, timestamp.minute)
        
        for news_hour, news_minute in news_times:
            news_start = news_hour * 60 + news_minute - self.news_blackout_minutes
            news_end = news_hour * 60 + news_minute + self.news_blackout_minutes
            current_minutes = current_time[0] * 60 + current_time[1]
            
            if news_start <= current_minutes <= news_end:
                return True
        
        return False
    
    def calculate_risk_reward(self, entry: float, stop_loss: float, take_profit: float, direction: SignalDirection) -> float:
        """Risk-reward calculation - The foundation of profitable trading"""
        if direction == SignalDirection.BUY:
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
        else:
            risk = abs(stop_loss - entry)
            reward = abs(entry - take_profit)
        
        return reward / risk if risk > 0 else 0
    
    def calculate_technical_indicators(self, price_data: List[float], volume_data: List[float] = None) -> TechnicalIndicators:
        """Technical indicator calculation suite - The trader's arsenal"""
        prices = np.array(price_data)
        
        # RSI calculation (momentum)
        rsi = self._calculate_rsi(prices)
        
        # MACD calculation (trend and momentum)
        macd, macd_signal, macd_hist = self._calculate_macd(prices)
        
        # Bollinger Bands (volatility and mean reversion)
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(prices)
        
        # Moving averages (trend identification)
        ma_21 = np.mean(prices[-21:]) if len(prices) >= 21 else prices[-1]
        ma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else prices[-1]
        ma_200 = np.mean(prices[-200:]) if len(prices) >= 200 else prices[-1]
        
        # ATR (volatility measurement)
        atr = self._calculate_atr(price_data)
        
        # ADX (trend strength)
        adx = self._calculate_adx(price_data)
        
        # Stochastic (momentum oscillator)
        stoch_k, stoch_d = self._calculate_stochastic(price_data)
        
        # Volume analysis
        volume_avg = np.mean(volume_data[-20:]) if volume_data and len(volume_data) >= 20 else 1000
        
        return TechnicalIndicators(
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            macd_histogram=macd_hist,
            adx=adx,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            ma_21=ma_21,
            ma_50=ma_50,
            ma_200=ma_200,
            volume_avg=volume_avg,
            atr=atr,
            stoch_k=stoch_k,
            stoch_d=stoch_d
        )
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """RSI calculation - Momentum measurement"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """MACD calculation - Trend and momentum"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        
        # Calculate EMAs
        ema_fast = self._ema(prices, fast)
        ema_slow = self._ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        macd_history = [macd_line] * signal  # Simplified for single point
        signal_line = np.mean(macd_history)
        
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
        """Bollinger Bands calculation - Volatility and mean reversion"""
        if len(prices) < period:
            price = prices[-1]
            return price, price, price
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return upper, sma, lower
    
    def _calculate_atr(self, price_data: List[float], period: int = 14) -> float:
        """ATR calculation - Volatility measurement"""
        if len(price_data) < period + 1:
            return 20.0  # Default ATR
        
        # Simplified ATR using price ranges
        ranges = []
        for i in range(1, len(price_data)):
            high_low = abs(price_data[i] - price_data[i-1])
            ranges.append(high_low)
        
        atr = np.mean(ranges[-period:]) * 10000  # Convert to pips
        return atr
    
    def _calculate_adx(self, price_data: List[float], period: int = 14) -> float:
        """ADX calculation - Trend strength"""
        if len(price_data) < period * 2:
            return 20.0  # Default ADX
        
        # Simplified ADX calculation
        movements = np.diff(price_data)
        abs_movements = np.abs(movements)
        avg_movement = np.mean(abs_movements[-period:])
        
        # Scale to 0-100
        adx = min(100, avg_movement * 100000)
        return adx
    
    def _calculate_stochastic(self, price_data: List[float], period: int = 14) -> Tuple[float, float]:
        """Stochastic calculation - Momentum oscillator"""
        if len(price_data) < period:
            return 50.0, 50.0
        
        recent_prices = price_data[-period:]
        highest = max(recent_prices)
        lowest = min(recent_prices)
        current = price_data[-1]
        
        if highest == lowest:
            k_percent = 50
        else:
            k_percent = ((current - lowest) / (highest - lowest)) * 100
        
        # Simplified %D as 3-period SMA of %K
        d_percent = k_percent  # Simplified
        
        return k_percent, d_percent
    
    def _ema(self, prices: np.ndarray, period: int) -> float:
        """Exponential Moving Average calculation"""
        if len(prices) < period:
            return prices[-1]
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def format_signal_output(self, signal: TradingSignal) -> str:
        """Format trading signal for elite presentation"""
        confidence_emoji = "🔥" if signal.tcs_score >= 85 else "⚡" if signal.tcs_score >= 70 else "⚠️"
        
        output = f"""{confidence_emoji} **TACTICAL SIGNAL DETECTED**

🎯 **{signal.strategy_type.value.upper().replace('_', ' ')}**
📈 **{signal.symbol}** - {signal.direction.value.upper()}
🎖️ **TCS Score:** {signal.tcs_score}/100

💰 **Entry:** {signal.entry_price:.5f}
🛡️ **Stop Loss:** {signal.stop_loss:.5f}
🎯 **Take Profit:** {signal.take_profit:.5f}
⚖️ **R:R Ratio:** 1:{signal.risk_reward_ratio:.1f}

🔍 **Confidence Factors:**"""
        
        for factor in signal.confidence_factors:
            output += f"\n✅ {factor}"
        
        if signal.warning_factors:
            output += "\n\n⚠️ **Risk Factors:**"
            for warning in signal.warning_factors:
                output += f"\n🔺 {warning}"
        
        output += f"\n\n🎮 **Session:** {signal.session.value.title()}"
        output += f"\n⏰ **Valid Until:** {signal.expiry_time.strftime('%H:%M UTC')}"
        
        return output