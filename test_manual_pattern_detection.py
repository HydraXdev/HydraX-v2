#!/usr/bin/env python3
"""Manually test Elite Guard pattern detection logic"""

import json
import time
import logging
from datetime import datetime
from collections import deque, defaultdict

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simple pattern detection test
def test_liquidity_sweep(candle_data):
    """Test liquidity sweep detection with candle data"""
    
    if len(candle_data) < 5:
        logger.debug("Not enough candles for pattern detection")
        return None
        
    # Extract OHLC data
    highs = [c['high'] for c in candle_data]
    lows = [c['low'] for c in candle_data]
    closes = [c['close'] for c in candle_data]
    volumes = [c.get('volume', 0) for c in candle_data]
    
    # Calculate price movement
    recent_high = max(highs)
    recent_low = min(lows)
    price_range = recent_high - recent_low
    avg_price = sum(closes) / len(closes)
    price_change_pct = (price_range / avg_price) * 100 if avg_price > 0 else 0
    
    # Volume analysis
    avg_volume = sum(volumes) / len(volumes) if volumes else 1
    recent_volume = volumes[-1] if volumes else 1
    volume_surge = recent_volume / avg_volume if avg_volume > 0 else 1
    
    logger.info(f"🔍 Liquidity sweep analysis:")
    logger.info(f"  Price range: {price_change_pct:.4f}%")
    logger.info(f"  Volume surge: {volume_surge:.2f}x")
    logger.info(f"  Recent high: {recent_high}")
    logger.info(f"  Recent low: {recent_low}")
    logger.info(f"  Price range in pips: {price_range * 10000:.1f}")
    
    # Liquidity sweep criteria
    pip_movement = price_range * 10000  # For non-JPY pairs
    
    logger.info(f"  Pip movement: {pip_movement:.1f} pips")
    logger.info(f"  Criteria: Need 3+ pips movement and 1.3x volume surge")
    
    if pip_movement > 3 and volume_surge > 1.3:
        logger.info("✅ LIQUIDITY SWEEP DETECTED!")
        return {
            'pattern': 'LIQUIDITY_SWEEP_REVERSAL',
            'confidence': 75,
            'pip_movement': pip_movement,
            'volume_surge': volume_surge
        }
    else:
        logger.info("❌ No liquidity sweep pattern found")
        return None

# Create some test candle data
test_candles = [
    {
        'time': int(time.time()) - 240,
        'open': 1.15400,
        'high': 1.15420,
        'low': 1.15395,
        'close': 1.15410,
        'volume': 100
    },
    {
        'time': int(time.time()) - 180,
        'open': 1.15410,
        'high': 1.15425,
        'low': 1.15405,
        'close': 1.15420,
        'volume': 120
    },
    {
        'time': int(time.time()) - 120,
        'open': 1.15420,
        'high': 1.15450,  # Spike high
        'low': 1.15415,
        'close': 1.15445,
        'volume': 180  # Volume surge
    },
    {
        'time': int(time.time()) - 60,
        'open': 1.15445,
        'high': 1.15448,
        'low': 1.15430,
        'close': 1.15435,
        'volume': 150
    },
    {
        'time': int(time.time()),
        'open': 1.15435,
        'high': 1.15440,
        'low': 1.15425,
        'close': 1.15430,
        'volume': 130
    }
]

print("🧪 Testing Elite Guard Pattern Detection Logic")
print("=" * 60)
print("\nTest candle data:")
for i, candle in enumerate(test_candles):
    print(f"Candle {i+1}: O={candle['open']:.5f} H={candle['high']:.5f} L={candle['low']:.5f} C={candle['close']:.5f} V={candle['volume']}")

print("\n" + "=" * 60)
result = test_liquidity_sweep(test_candles)

if result:
    print(f"\n🎯 Pattern found: {result['pattern']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Pip movement: {result['pip_movement']:.1f} pips")
    print(f"Volume surge: {result['volume_surge']:.2f}x")
else:
    print("\n⚠️ No pattern detected with test data")

print("\n✅ Test complete!")