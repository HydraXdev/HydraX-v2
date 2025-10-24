#!/usr/bin/env python3
"""
MULTI-TIMEFRAME ANALYZER - INSTITUTIONAL TIMEFRAME CONFLUENCE
Based on Grok research findings (Oct 21, 2025)

IMPACT: 70-80% win rate when HTF and LTF align
SOURCES: X (Twitter) @ICT_Concepts, @ForexMentorPro, prop firms FTMO/FundedNext

TECHNIQUES IMPLEMENTED:
1. HTF Bias Detection - D1/H4 for directional bias (trend identification)
2. LTF Entry Timing - M15/M1 for precise entries (pullback/breakout)
3. Multi-TF Confluence - HTF trend + LTF pattern = high-probability setup
4. Regime Detection - Trending vs Ranging (ADX, ATR-based)
5. Session Awareness - London/NY/Asian session characteristics
6. FVG Cascade Detection - Multi-timeframe Fair Value Gap alignment

EVIDENCE FROM RESEARCH:
- Multi-TF alignment: 70-80% win rate (ICT concepts)
- HTF bias + LTF entry: Industry standard for prop desks
- FVG cascade (HTF + LTF): 70% win rate when aligned

TIMEFRAME HIERARCHY:
- HTF (Higher Timeframe): D1, H4 - Directional bias, major S/R
- MTF (Mid Timeframe): H1, M15 - Intermediate structure
- LTF (Lower Timeframe): M5, M1 - Entry timing, execution

DATA SOURCE: Finnhub candles via FinnhubDataAdapter (multiple resolutions)
"""

from typing import Dict, List, Optional, Tuple
import statistics
from datetime import datetime, time as dt_time
from collections import defaultdict


class MultiTimeframeAnalyzer:
    """
    Institutional-grade multi-timeframe analysis

    Analyzes trend bias on HTF, entries on LTF, detects confluence
    """

    def __init__(self):
        """Initialize Multi-Timeframe Analyzer"""
        # Session times (UTC)
        self.sessions = {
            'ASIAN': (dt_time(0, 0), dt_time(9, 0)),      # 00:00-09:00 UTC
            'LONDON': (dt_time(8, 0), dt_time(17, 0)),    # 08:00-17:00 UTC
            'NY': (dt_time(13, 0), dt_time(22, 0)),       # 13:00-22:00 UTC
            'OVERLAP': (dt_time(13, 0), dt_time(17, 0))   # London/NY overlap
        }

    def calculate_ema(self, candles: List[Dict], period: int = 20) -> List[float]:
        """
        Calculate Exponential Moving Average

        Args:
            candles: List of candles (OHLCV)
            period: EMA period

        Returns:
            List of EMA values
        """
        if len(candles) < period:
            return []

        closes = [c['close'] for c in candles]

        # Calculate smoothing multiplier
        multiplier = 2 / (period + 1)

        # Initialize with SMA
        sma = statistics.mean(closes[:period])
        ema_values = [sma]

        # Calculate EMA for remaining periods
        for i in range(period, len(closes)):
            ema = (closes[i] - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)

        return ema_values

    def calculate_atr(self, candles: List[Dict], period: int = 14) -> float:
        """
        Calculate Average True Range

        Args:
            candles: List of candles
            period: ATR period

        Returns:
            Current ATR value
        """
        if len(candles) < period + 1:
            return 0.0

        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        # Average of last 'period' true ranges
        return statistics.mean(true_ranges[-period:]) if true_ranges else 0.0

    def calculate_adx(self, candles: List[Dict], period: int = 14) -> float:
        """
        Calculate Average Directional Index (ADX)

        ADX measures trend strength (not direction)
        - ADX > 25: Strong trend
        - ADX < 20: Weak trend / ranging

        Args:
            candles: List of candles
            period: ADX period

        Returns:
            Current ADX value (0-100)
        """
        if len(candles) < period + 1:
            return 0.0

        # Calculate +DM and -DM
        plus_dm = []
        minus_dm = []

        for i in range(1, len(candles)):
            high_diff = candles[i]['high'] - candles[i-1]['high']
            low_diff = candles[i-1]['low'] - candles[i]['low']

            if high_diff > low_diff and high_diff > 0:
                plus_dm.append(high_diff)
                minus_dm.append(0)
            elif low_diff > high_diff and low_diff > 0:
                plus_dm.append(0)
                minus_dm.append(low_diff)
            else:
                plus_dm.append(0)
                minus_dm.append(0)

        # Calculate ATR
        atr = self.calculate_atr(candles, period)
        if atr == 0:
            return 0.0

        # Calculate smoothed +DI and -DI
        plus_di = statistics.mean(plus_dm[-period:]) / atr * 100
        minus_di = statistics.mean(minus_dm[-period:]) / atr * 100

        # Calculate DX
        di_sum = plus_di + minus_di
        if di_sum == 0:
            return 0.0

        dx = abs(plus_di - minus_di) / di_sum * 100

        # ADX is smoothed DX (simplified: just return DX for now)
        return round(dx, 2)

    def detect_htf_bias(self, candles: List[Dict]) -> Dict:
        """
        Detect Higher Timeframe directional bias

        Uses EMA trend + price structure

        Args:
            candles: HTF candles (H4 or D1)

        Returns:
            Dict with:
                - bias: 'BULLISH', 'BEARISH', or 'NEUTRAL'
                - trend_strength: 'STRONG', 'MODERATE', 'WEAK'
                - ema_trend: EMA slope direction
                - price_structure: Higher highs/lows or lower highs/lows
        """
        if len(candles) < 50:
            return {
                'bias': 'NEUTRAL',
                'trend_strength': 'WEAK',
                'ema_trend': 'FLAT',
                'price_structure': 'UNDEFINED'
            }

        # 1. EMA TREND (20 and 50 period)
        ema_20 = self.calculate_ema(candles, period=20)
        ema_50 = self.calculate_ema(candles, period=50)

        if not ema_20 or not ema_50:
            return {
                'bias': 'NEUTRAL',
                'trend_strength': 'WEAK',
                'ema_trend': 'FLAT',
                'price_structure': 'UNDEFINED'
            }

        current_price = candles[-1]['close']
        current_ema_20 = ema_20[-1]
        current_ema_50 = ema_50[-1]

        # EMA alignment
        ema_trend = 'FLAT'
        if current_price > current_ema_20 > current_ema_50:
            ema_trend = 'BULLISH'
        elif current_price < current_ema_20 < current_ema_50:
            ema_trend = 'BEARISH'

        # 2. PRICE STRUCTURE (Higher highs/lows or lower highs/lows)
        recent_candles = candles[-10:]
        highs = [c['high'] for c in recent_candles]
        lows = [c['low'] for c in recent_candles]

        # Check for higher highs and higher lows (uptrend)
        higher_highs = highs[-1] > highs[-5] and highs[-5] > highs[0]
        higher_lows = lows[-1] > lows[-5] and lows[-5] > lows[0]

        # Check for lower highs and lower lows (downtrend)
        lower_highs = highs[-1] < highs[-5] and highs[-5] < highs[0]
        lower_lows = lows[-1] < lows[-5] and lows[-5] < lows[0]

        price_structure = 'UNDEFINED'
        if higher_highs and higher_lows:
            price_structure = 'BULLISH'
        elif lower_highs and lower_lows:
            price_structure = 'BEARISH'

        # 3. TREND STRENGTH (ADX-based)
        adx = self.calculate_adx(candles)
        if adx > 25:
            trend_strength = 'STRONG'
        elif adx > 15:
            trend_strength = 'MODERATE'
        else:
            trend_strength = 'WEAK'

        # 4. DETERMINE FINAL BIAS
        bias = 'NEUTRAL'
        if ema_trend == 'BULLISH' and price_structure == 'BULLISH':
            bias = 'BULLISH'
        elif ema_trend == 'BEARISH' and price_structure == 'BEARISH':
            bias = 'BEARISH'
        elif ema_trend in ['BULLISH', 'BEARISH']:
            bias = ema_trend  # EMA trend takes precedence

        return {
            'bias': bias,
            'trend_strength': trend_strength,
            'ema_trend': ema_trend,
            'price_structure': price_structure,
            'adx': adx
        }

    def detect_regime(self, candles: List[Dict]) -> Dict:
        """
        Detect market regime (Trending vs Ranging)

        Uses ADX + ATR compression

        Args:
            candles: Recent candles (any timeframe)

        Returns:
            Dict with:
                - regime: 'TRENDING', 'RANGING', 'BREAKOUT_PENDING'
                - adx: ADX value (trend strength)
                - atr_percentile: ATR relative to recent history
        """
        if len(candles) < 50:
            return {
                'regime': 'UNKNOWN',
                'adx': 0,
                'atr_percentile': 50
            }

        # Calculate ADX for trend strength
        adx = self.calculate_adx(candles)

        # Calculate ATR percentile (is volatility high or low?)
        current_atr = self.calculate_atr(candles, period=14)

        # Get ATR over last 50 candles
        atr_history = []
        for i in range(len(candles) - 50, len(candles)):
            if i >= 14:
                atr_val = self.calculate_atr(candles[:i+1], period=14)
                atr_history.append(atr_val)

        if not atr_history:
            return {
                'regime': 'UNKNOWN',
                'adx': adx,
                'atr_percentile': 50
            }

        # Calculate percentile
        atr_history_sorted = sorted(atr_history)
        atr_percentile = (atr_history_sorted.index(min(atr_history_sorted, key=lambda x: abs(x - current_atr))) / len(atr_history_sorted)) * 100

        # Determine regime
        regime = 'UNKNOWN'

        if adx > 25:
            regime = 'TRENDING'
        elif adx < 20 and atr_percentile < 30:
            regime = 'BREAKOUT_PENDING'  # Low ADX + low volatility = compression
        elif adx < 20:
            regime = 'RANGING'

        return {
            'regime': regime,
            'adx': round(adx, 2),
            'atr_percentile': round(atr_percentile, 1),
            'current_atr': round(current_atr, 5)
        }

    def detect_session(self) -> str:
        """
        Detect current trading session

        Returns:
            'ASIAN', 'LONDON', 'NY', 'OVERLAP', or 'OFF_HOURS'
        """
        now = datetime.utcnow().time()

        # Check overlap first (most important)
        if self.sessions['OVERLAP'][0] <= now <= self.sessions['OVERLAP'][1]:
            return 'OVERLAP'

        # Check individual sessions
        for session, (start, end) in self.sessions.items():
            if session != 'OVERLAP' and start <= now <= end:
                return session

        return 'OFF_HOURS'

    def detect_fvg_cascade(
        self,
        htf_candles: List[Dict],
        ltf_candles: List[Dict]
    ) -> Dict:
        """
        Detect Fair Value Gap cascade across timeframes

        Research finding: HTF + LTF FVG alignment = 70% win rate

        Args:
            htf_candles: Higher timeframe candles (H4/D1)
            ltf_candles: Lower timeframe candles (M15/M1)

        Returns:
            Dict with:
                - cascade_detected: True if HTF and LTF FVGs align
                - htf_fvg: HTF Fair Value Gap details
                - ltf_fvg: LTF Fair Value Gap details
                - alignment_quality: 'STRONG', 'MODERATE', 'WEAK'
        """
        # Detect HTF FVG
        htf_fvg = self._detect_fvg(htf_candles[-10:])

        # Detect LTF FVG
        ltf_fvg = self._detect_fvg(ltf_candles[-20:])

        cascade_detected = False
        alignment_quality = 'NONE'

        if htf_fvg and ltf_fvg:
            # Check if FVGs are in same direction
            if htf_fvg['direction'] == ltf_fvg['direction']:
                # Check if LTF FVG is within HTF FVG range
                htf_range = (htf_fvg['low'], htf_fvg['high'])
                ltf_range = (ltf_fvg['low'], ltf_fvg['high'])

                # Check overlap
                overlap = (
                    ltf_range[0] <= htf_range[1] and
                    ltf_range[1] >= htf_range[0]
                )

                if overlap:
                    cascade_detected = True

                    # Measure alignment quality
                    overlap_size = min(htf_range[1], ltf_range[1]) - max(htf_range[0], ltf_range[0])
                    htf_size = htf_range[1] - htf_range[0]

                    overlap_pct = overlap_size / htf_size if htf_size > 0 else 0

                    if overlap_pct > 0.7:
                        alignment_quality = 'STRONG'
                    elif overlap_pct > 0.4:
                        alignment_quality = 'MODERATE'
                    else:
                        alignment_quality = 'WEAK'

        return {
            'cascade_detected': cascade_detected,
            'htf_fvg': htf_fvg,
            'ltf_fvg': ltf_fvg,
            'alignment_quality': alignment_quality
        }

    def _detect_fvg(self, candles: List[Dict]) -> Optional[Dict]:
        """
        Detect Fair Value Gap (simple version)

        FVG = gap between candles where price moved too fast

        Args:
            candles: Recent candles

        Returns:
            Dict with FVG details or None
        """
        if len(candles) < 3:
            return None

        # Check last 3 candles for FVG
        for i in range(len(candles) - 3, max(0, len(candles) - 10), -1):
            c1 = candles[i]
            c2 = candles[i + 1]
            c3 = candles[i + 2]

            # Bullish FVG: c1.high < c3.low (gap up)
            if c1['high'] < c3['low']:
                return {
                    'direction': 'BULLISH',
                    'low': c1['high'],
                    'high': c3['low'],
                    'size_pips': (c3['low'] - c1['high']) * 10000,
                    'candle_index': i
                }

            # Bearish FVG: c1.low > c3.high (gap down)
            if c1['low'] > c3['high']:
                return {
                    'direction': 'BEARISH',
                    'low': c3['high'],
                    'high': c1['low'],
                    'size_pips': (c1['low'] - c3['high']) * 10000,
                    'candle_index': i
                }

        return None

    def get_mtf_signal(
        self,
        symbol: str,
        htf_candles: List[Dict],
        ltf_candles: List[Dict]
    ) -> Dict:
        """
        MAIN API: Get multi-timeframe confluence signal

        Combines HTF bias, LTF timing, regime, and session awareness

        Args:
            symbol: Trading symbol
            htf_candles: Higher timeframe candles (H4/D1, minimum 50)
            ltf_candles: Lower timeframe candles (M15/M1, minimum 50)

        Returns:
            Dict with:
                - signal: 'BUY', 'SELL', or 'NEUTRAL'
                - confidence: 0-100
                - htf_bias: HTF directional bias
                - regime: Market regime (trending/ranging)
                - session: Current session
                - fvg_cascade: Multi-TF FVG alignment
                - reasons: List of confluence factors
        """
        if len(htf_candles) < 50 or len(ltf_candles) < 50:
            return {
                'symbol': symbol,
                'signal': 'NEUTRAL',
                'confidence': 0,
                'error': 'Insufficient candle data (need 50+ on both timeframes)'
            }

        # 1. HTF BIAS
        htf_bias = self.detect_htf_bias(htf_candles)

        # 2. LTF BIAS (for entry timing)
        ltf_bias = self.detect_htf_bias(ltf_candles)  # Same method, different TF

        # 3. REGIME DETECTION
        regime = self.detect_regime(htf_candles)

        # 4. SESSION DETECTION
        session = self.detect_session()

        # 5. FVG CASCADE
        fvg_cascade = self.detect_fvg_cascade(htf_candles, ltf_candles)

        # CONFLUENCE SIGNAL GENERATION
        signal = 'NEUTRAL'
        confidence = 0
        reasons = []

        # BUY signal confluence
        buy_signals = 0

        if htf_bias['bias'] == 'BULLISH':
            buy_signals += 2  # High weight for HTF bias
            reasons.append(f"HTF bias: BULLISH ({htf_bias['trend_strength']})")

        if ltf_bias['bias'] == 'BULLISH':
            buy_signals += 1
            reasons.append("LTF bias: BULLISH (entry timing)")

        if fvg_cascade['cascade_detected'] and fvg_cascade['htf_fvg'] and fvg_cascade['htf_fvg']['direction'] == 'BULLISH':
            buy_signals += 2  # High weight for FVG cascade (research: 70% win rate)
            reasons.append(f"FVG cascade: BULLISH ({fvg_cascade['alignment_quality']})")

        if regime['regime'] == 'TRENDING' and htf_bias['bias'] == 'BULLISH':
            buy_signals += 1
            reasons.append(f"Strong trend: ADX {regime['adx']}")

        if session in ['LONDON', 'NY', 'OVERLAP']:
            buy_signals += 1
            reasons.append(f"Active session: {session}")

        # SELL signal confluence
        sell_signals = 0

        if htf_bias['bias'] == 'BEARISH':
            sell_signals += 2
            reasons.append(f"HTF bias: BEARISH ({htf_bias['trend_strength']})")

        if ltf_bias['bias'] == 'BEARISH':
            sell_signals += 1
            reasons.append("LTF bias: BEARISH (entry timing)")

        if fvg_cascade['cascade_detected'] and fvg_cascade['htf_fvg'] and fvg_cascade['htf_fvg']['direction'] == 'BEARISH':
            sell_signals += 2
            reasons.append(f"FVG cascade: BEARISH ({fvg_cascade['alignment_quality']})")

        if regime['regime'] == 'TRENDING' and htf_bias['bias'] == 'BEARISH':
            sell_signals += 1
            reasons.append(f"Strong trend: ADX {regime['adx']}")

        if session in ['LONDON', 'NY', 'OVERLAP']:
            sell_signals += 1
            reasons.append(f"Active session: {session}")

        # DETERMINE FINAL SIGNAL (minimum 3 confluence factors)
        if buy_signals >= 3:
            signal = 'BUY'
            confidence = min(buy_signals * 15, 100)  # Each factor = 15%
        elif sell_signals >= 3:
            signal = 'SELL'
            confidence = min(sell_signals * 15, 100)

        # REDUCE CONFIDENCE FOR RANGING MARKETS
        if regime['regime'] == 'RANGING':
            confidence *= 0.6  # 40% penalty for ranging (research: trends more reliable)
            if 'ranging market - reduced confidence' not in [r.lower() for r in reasons]:
                reasons.append("⚠️ Ranging market - reduced confidence")

        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': round(confidence, 1),
            'htf_bias': htf_bias,
            'ltf_bias': ltf_bias,
            'regime': regime,
            'session': session,
            'fvg_cascade': fvg_cascade,
            'reasons': reasons
        }


if __name__ == '__main__':
    """
    Test harness with sample data
    """
    import random

    # Create HTF test data (H4 uptrend)
    htf_candles = []
    base_price = 1.10000

    for i in range(100):
        # Uptrend on HTF
        open_price = base_price + (i * 0.0005) + random.uniform(-0.0003, 0.0003)
        close_price = open_price + random.uniform(0, 0.0008)  # Mostly bullish
        high_price = max(open_price, close_price) + random.uniform(0, 0.0004)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0002)

        htf_candles.append({
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5),
            'volume': random.uniform(80, 120)
        })

    # Create LTF test data (M15 with pullback then continuation)
    ltf_candles = []
    ltf_base = htf_candles[-1]['close']

    for i in range(100):
        # First 30 candles: pullback, then 70 candles: continuation up
        if i < 30:
            # Pullback
            open_price = ltf_base - (i * 0.0001) + random.uniform(-0.0001, 0.0001)
            close_price = open_price - random.uniform(0, 0.0002)
        else:
            # Continuation
            open_price = ltf_base + ((i - 30) * 0.0001) + random.uniform(-0.0001, 0.0001)
            close_price = open_price + random.uniform(0, 0.0002)

        high_price = max(open_price, close_price) + random.uniform(0, 0.0001)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0001)

        ltf_candles.append({
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5),
            'volume': random.uniform(50, 100)
        })

    # Run analysis
    analyzer = MultiTimeframeAnalyzer()
    result = analyzer.get_mtf_signal('TEST_EURUSD', htf_candles, ltf_candles)

    print("🎯 MULTI-TIMEFRAME ANALYZER TEST\n")
    print(f"Symbol: {result['symbol']}")
    print(f"Signal: {result['signal']} ({result['confidence']:.1f}% confidence)")

    print(f"\n📊 HTF Analysis (H4/D1):")
    print(f"  Bias: {result['htf_bias']['bias']}")
    print(f"  Trend Strength: {result['htf_bias']['trend_strength']} (ADX: {result['htf_bias']['adx']:.1f})")
    print(f"  EMA Trend: {result['htf_bias']['ema_trend']}")
    print(f"  Price Structure: {result['htf_bias']['price_structure']}")

    print(f"\n📈 LTF Analysis (M15/M1):")
    print(f"  Bias: {result['ltf_bias']['bias']}")
    print(f"  Trend Strength: {result['ltf_bias']['trend_strength']}")

    print(f"\n🎪 Market Regime:")
    print(f"  Regime: {result['regime']['regime']}")
    print(f"  ADX: {result['regime']['adx']}")
    print(f"  ATR Percentile: {result['regime']['atr_percentile']:.1f}%")

    print(f"\n⏰ Session:")
    print(f"  Current Session: {result['session']}")

    print(f"\n🎯 FVG Cascade:")
    print(f"  Cascade Detected: {result['fvg_cascade']['cascade_detected']}")
    if result['fvg_cascade']['cascade_detected']:
        print(f"  Alignment Quality: {result['fvg_cascade']['alignment_quality']}")
        print(f"  HTF FVG: {result['fvg_cascade']['htf_fvg']['direction']} @ {result['fvg_cascade']['htf_fvg']['size_pips']:.1f} pips")
        print(f"  LTF FVG: {result['fvg_cascade']['ltf_fvg']['direction']} @ {result['fvg_cascade']['ltf_fvg']['size_pips']:.1f} pips")

    print(f"\n✅ Confluence Factors ({len(result['reasons'])}):")
    for i, reason in enumerate(result['reasons'], 1):
        print(f"  {i}. {reason}")

    print(f"\n{'✅' if result['signal'] != 'NEUTRAL' else '⚠️'}  Final: {result['signal']} @ {result['confidence']:.1f}%")
