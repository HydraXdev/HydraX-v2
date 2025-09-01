#!/usr/bin/env python3
"""
Multi-Timeframe Confluence Analyzer
Analyzes 1M, 5M, and 15M charts for trade confluence

Based on professional trading concepts:
- Higher timeframe bias (15M direction filter)
- Lower timeframe precision (1M entries)
- Volume-weighted analysis
- Momentum alignment
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TimeframeBias(Enum):
    STRONGLY_BULLISH = "STRONGLY_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONGLY_BEARISH = "STRONGLY_BEARISH"

@dataclass
class TimeframeAnalysis:
    timeframe: str
    bias: TimeframeBias
    strength: float  # 0-100
    key_level: float
    momentum: float  # -100 to +100
    volume_profile: str  # "INCREASING", "DECREASING", "STABLE"

@dataclass
class ConfluenceResult:
    overall_bias: TimeframeBias
    confidence: float  # 0-100
    entry_timeframe: str
    bias_timeframe: str
    confluence_factors: List[str]
    divergence_warnings: List[str]

class MTFConfluenceAnalyzer:
    """
    Multi-timeframe confluence analyzer for scalping optimization
    """
    
    def __init__(self):
        self.timeframes = {
            '1M': {'weight': 0.3, 'role': 'ENTRY'},
            '5M': {'weight': 0.4, 'role': 'CONFIRMATION'}, 
            '15M': {'weight': 0.3, 'role': 'BIAS'}
        }
        
        # Confluence scoring
        self.confluence_thresholds = {
            'PERFECT': 90,      # All timeframes aligned
            'STRONG': 75,       # 2/3 timeframes aligned strongly
            'MODERATE': 60,     # Some alignment with minor divergence
            'WEAK': 45,         # Mixed signals
            'CONFLICTED': 30    # Major divergence
        }
    
    def analyze_symbol_confluence(self, symbol: str, candle_data: Dict) -> ConfluenceResult:
        """
        Analyze confluence across multiple timeframes
        
        Args:
            symbol: Trading symbol
            candle_data: Dict with '1M', '5M', '15M' candle arrays
        """
        try:
            timeframe_analyses = {}
            
            # Analyze each timeframe
            for tf in ['1M', '5M', '15M']:
                if tf in candle_data and len(candle_data[tf]) >= 20:
                    timeframe_analyses[tf] = self.analyze_timeframe(
                        symbol, tf, candle_data[tf]
                    )
            
            # Calculate confluence
            confluence = self.calculate_confluence(timeframe_analyses)
            return confluence
            
        except Exception as e:
            logger.error(f"Error analyzing confluence for {symbol}: {e}")
            return ConfluenceResult(
                overall_bias=TimeframeBias.NEUTRAL,
                confidence=0,
                entry_timeframe='1M',
                bias_timeframe='15M',
                confluence_factors=[],
                divergence_warnings=[f"Analysis error: {e}"]
            )
    
    def analyze_timeframe(self, symbol: str, timeframe: str, candles: List) -> TimeframeAnalysis:
        """
        Analyze individual timeframe for bias and strength
        """
        if len(candles) < 20:
            return TimeframeAnalysis(
                timeframe=timeframe,
                bias=TimeframeBias.NEUTRAL,
                strength=0,
                key_level=candles[-1]['close'] if candles else 0,
                momentum=0,
                volume_profile="STABLE"
            )
        
        # Calculate momentum using EMA crossover
        momentum = self.calculate_momentum(candles)
        
        # Find key levels (support/resistance)
        key_level = self.find_key_level(candles)
        
        # Volume analysis
        volume_profile = self.analyze_volume_profile(candles)
        
        # Determine bias
        bias, strength = self.determine_bias(candles, momentum)
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            bias=bias,
            strength=strength,
            key_level=key_level,
            momentum=momentum,
            volume_profile=volume_profile
        )
    
    def calculate_momentum(self, candles: List) -> float:
        """
        Calculate momentum using multiple indicators
        Returns -100 to +100
        """
        closes = [c['close'] for c in candles]
        
        # EMA momentum (fast vs slow)
        ema_fast = self.calculate_ema(closes, 8)
        ema_slow = self.calculate_ema(closes, 21)
        
        if ema_slow == 0:
            return 0
        
        ema_momentum = ((ema_fast - ema_slow) / ema_slow) * 10000  # In pips
        
        # RSI momentum
        rsi = self.calculate_rsi(closes, 14)
        rsi_momentum = (rsi - 50) * 2  # Convert to -100 to +100
        
        # Price momentum (recent vs older)
        recent_avg = np.mean(closes[-5:])
        older_avg = np.mean(closes[-15:-10])
        
        if older_avg == 0:
            price_momentum = 0
        else:
            price_momentum = ((recent_avg - older_avg) / older_avg) * 20000
        
        # Weighted combination
        total_momentum = (ema_momentum * 0.4 + 
                         rsi_momentum * 0.3 + 
                         price_momentum * 0.3)
        
        return max(-100, min(100, total_momentum))
    
    def determine_bias(self, candles: List, momentum: float) -> Tuple[TimeframeBias, float]:
        """
        Determine timeframe bias and strength
        """
        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        
        # Structure analysis
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        current_price = closes[-1]
        
        # Position in range
        if recent_high != recent_low:
            range_position = (current_price - recent_low) / (recent_high - recent_low)
        else:
            range_position = 0.5
        
        # Trend analysis (higher highs, higher lows)
        higher_highs = sum(1 for i in range(1, min(10, len(highs))) 
                          if highs[-i] > highs[-(i+1)])
        higher_lows = sum(1 for i in range(1, min(10, len(lows))) 
                         if lows[-i] > lows[-(i+1)])
        
        lower_highs = sum(1 for i in range(1, min(10, len(highs))) 
                         if highs[-i] < highs[-(i+1)])
        lower_lows = sum(1 for i in range(1, min(10, len(lows))) 
                        if lows[-i] < lows[-(i+1)])
        
        # Bias scoring
        bullish_score = (higher_highs * 10 + 
                        higher_lows * 10 + 
                        momentum * 0.3 + 
                        range_position * 30)
        
        bearish_score = (lower_highs * 10 + 
                        lower_lows * 10 + 
                        abs(momentum) * 0.3 * (-1 if momentum < 0 else 0) + 
                        (1 - range_position) * 30)
        
        # Determine bias
        if bullish_score >= 80:
            return TimeframeBias.STRONGLY_BULLISH, min(100, bullish_score)
        elif bullish_score >= 60:
            return TimeframeBias.BULLISH, min(100, bullish_score)
        elif bearish_score >= 80:
            return TimeframeBias.STRONGLY_BEARISH, min(100, bearish_score)
        elif bearish_score >= 60:
            return TimeframeBias.BEARISH, min(100, bearish_score)
        else:
            return TimeframeBias.NEUTRAL, max(bullish_score, bearish_score)
    
    def find_key_level(self, candles: List) -> float:
        """
        Find most significant support/resistance level
        """
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        
        # Find recent swing points
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(candles) - 2):
            # Swing high: higher than 2 candles on each side
            if (candles[i]['high'] > candles[i-1]['high'] and 
                candles[i]['high'] > candles[i-2]['high'] and
                candles[i]['high'] > candles[i+1]['high'] and 
                candles[i]['high'] > candles[i+2]['high']):
                swing_highs.append(candles[i]['high'])
            
            # Swing low: lower than 2 candles on each side  
            if (candles[i]['low'] < candles[i-1]['low'] and 
                candles[i]['low'] < candles[i-2]['low'] and
                candles[i]['low'] < candles[i+1]['low'] and 
                candles[i]['low'] < candles[i+2]['low']):
                swing_lows.append(candles[i]['low'])
        
        current_price = candles[-1]['close']
        
        # Find closest significant level
        all_levels = swing_highs + swing_lows
        if not all_levels:
            return current_price
        
        closest_level = min(all_levels, key=lambda x: abs(x - current_price))
        return closest_level
    
    def analyze_volume_profile(self, candles: List) -> str:
        """
        Analyze volume trend
        """
        volumes = [c.get('volume', 0) for c in candles if 'volume' in c]
        
        if len(volumes) < 10:
            return "STABLE"
        
        recent_vol = np.mean(volumes[-5:])
        older_vol = np.mean(volumes[-15:-5])
        
        if recent_vol > older_vol * 1.2:
            return "INCREASING"
        elif recent_vol < older_vol * 0.8:
            return "DECREASING" 
        else:
            return "STABLE"
    
    def calculate_confluence(self, analyses: Dict[str, TimeframeAnalysis]) -> ConfluenceResult:
        """
        Calculate overall confluence from timeframe analyses
        """
        if not analyses:
            return ConfluenceResult(
                overall_bias=TimeframeBias.NEUTRAL,
                confidence=0,
                entry_timeframe='1M',
                bias_timeframe='15M',
                confluence_factors=[],
                divergence_warnings=["No timeframe data available"]
            )
        
        confluence_factors = []
        divergence_warnings = []
        
        # Check for alignment
        bullish_count = sum(1 for a in analyses.values() 
                           if a.bias in [TimeframeBias.BULLISH, TimeframeBias.STRONGLY_BULLISH])
        bearish_count = sum(1 for a in analyses.values() 
                           if a.bias in [TimeframeBias.BEARISH, TimeframeBias.STRONGLY_BEARISH])
        neutral_count = sum(1 for a in analyses.values() if a.bias == TimeframeBias.NEUTRAL)
        
        # Volume confluence
        increasing_volume = sum(1 for a in analyses.values() if a.volume_profile == "INCREASING")
        
        # Momentum alignment
        bullish_momentum = sum(1 for a in analyses.values() if a.momentum > 20)
        bearish_momentum = sum(1 for a in analyses.values() if a.momentum < -20)
        
        # Calculate overall bias
        if bullish_count >= 2 and bearish_count == 0:
            overall_bias = TimeframeBias.STRONGLY_BULLISH if bullish_count == 3 else TimeframeBias.BULLISH
            confluence_factors.append(f"{bullish_count}/3 timeframes bullish")
        elif bearish_count >= 2 and bullish_count == 0:
            overall_bias = TimeframeBias.STRONGLY_BEARISH if bearish_count == 3 else TimeframeBias.BEARISH
            confluence_factors.append(f"{bearish_count}/3 timeframes bearish")
        else:
            overall_bias = TimeframeBias.NEUTRAL
            if bullish_count > 0 and bearish_count > 0:
                divergence_warnings.append("Mixed timeframe signals")
        
        # Additional confluence factors
        if increasing_volume >= 2:
            confluence_factors.append("Volume increasing across timeframes")
        
        if bullish_momentum >= 2:
            confluence_factors.append("Bullish momentum alignment")
        elif bearish_momentum >= 2:
            confluence_factors.append("Bearish momentum alignment")
        
        # Check for key level confluence
        if len(analyses) >= 2:
            key_levels = [a.key_level for a in analyses.values()]
            level_range = max(key_levels) - min(key_levels)
            avg_level = np.mean(key_levels)
            
            # If key levels are close (within 10 pips), it's confluence
            pip_size = 0.0001  # Simplified for majors
            if level_range <= 10 * pip_size:
                confluence_factors.append("Key levels aligned")
        
        # Calculate confidence score
        base_confidence = 50
        
        # Perfect alignment bonus
        if bullish_count == 3 or bearish_count == 3:
            base_confidence += 30
        elif bullish_count == 2 or bearish_count == 2:
            base_confidence += 20
        
        # Volume bonus
        if increasing_volume >= 2:
            base_confidence += 10
        
        # Momentum bonus
        if bullish_momentum >= 2 or bearish_momentum >= 2:
            base_confidence += 15
        
        # Divergence penalty
        if bullish_count > 0 and bearish_count > 0:
            base_confidence -= 25
        
        # Strength bonus (average of non-neutral timeframes)
        strength_values = [a.strength for a in analyses.values() 
                          if a.bias != TimeframeBias.NEUTRAL]
        if strength_values:
            avg_strength = np.mean(strength_values)
            base_confidence += (avg_strength - 60) * 0.2  # Bonus for high strength
        
        final_confidence = max(0, min(100, base_confidence))
        
        return ConfluenceResult(
            overall_bias=overall_bias,
            confidence=final_confidence,
            entry_timeframe='1M',  # Always use 1M for entries
            bias_timeframe='15M',  # Use 15M for bias
            confluence_factors=confluence_factors,
            divergence_warnings=divergence_warnings
        )
    
    def calculate_ema(self, values: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if not values or len(values) < period:
            return 0
        
        multiplier = 2 / (period + 1)
        ema = values[0]
        
        for value in values[1:]:
            ema = (value * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def calculate_rsi(self, values: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(values) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(values)):
            change = values[i] - values[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


def format_confluence_report(confluence: ConfluenceResult) -> str:
    """Format confluence analysis for display"""
    
    bias_symbols = {
        TimeframeBias.STRONGLY_BULLISH: "🟢🟢",
        TimeframeBias.BULLISH: "🟢",
        TimeframeBias.NEUTRAL: "🟡", 
        TimeframeBias.BEARISH: "🔴",
        TimeframeBias.STRONGLY_BEARISH: "🔴🔴"
    }
    
    report = f"""
📊 Multi-Timeframe Confluence Analysis
═══════════════════════════════════════

Overall Bias: {bias_symbols.get(confluence.overall_bias, '❓')} {confluence.overall_bias.value}
Confidence: {confluence.confidence:.1f}%

✅ Confluence Factors:
{chr(10).join(f"  • {factor}" for factor in confluence.confluence_factors)}

⚠️ Divergence Warnings:
{chr(10).join(f"  • {warning}" for warning in confluence.divergence_warnings)}

Entry Timeframe: {confluence.entry_timeframe}
Bias Timeframe: {confluence.bias_timeframe}
"""
    return report


if __name__ == "__main__":
    # Test the confluence analyzer
    analyzer = MTFConfluenceAnalyzer()
    
    # Generate sample multi-timeframe data
    import random
    
    def generate_candles(count: int, base_price: float, trend: str = "neutral"):
        candles = []
        current_price = base_price
        
        for i in range(count):
            if trend == "bullish":
                change = random.uniform(-0.0005, 0.0015)
            elif trend == "bearish":
                change = random.uniform(-0.0015, 0.0005)
            else:
                change = random.uniform(-0.001, 0.001)
            
            open_price = current_price
            close_price = current_price + change
            high_price = max(open_price, close_price) + random.uniform(0, 0.0005)
            low_price = min(open_price, close_price) - random.uniform(0, 0.0005)
            
            candles.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': random.uniform(100, 1000)
            })
            
            current_price = close_price
        
        return candles
    
    # Test with different scenarios
    test_scenarios = [
        {"name": "Bullish Confluence", "1M": "bullish", "5M": "bullish", "15M": "bullish"},
        {"name": "Bearish Confluence", "1M": "bearish", "5M": "bearish", "15M": "bearish"},
        {"name": "Mixed Signals", "1M": "bullish", "5M": "neutral", "15M": "bearish"},
    ]
    
    for scenario in test_scenarios:
        print(f"\n🔍 Testing: {scenario['name']}")
        print("=" * 50)
        
        candle_data = {}
        base_price = 1.1000
        
        for tf in ['1M', '5M', '15M']:
            trend = scenario[tf]
            candle_data[tf] = generate_candles(30, base_price, trend)
        
        confluence = analyzer.analyze_symbol_confluence('EURUSD', candle_data)
        print(format_confluence_report(confluence))