#!/usr/bin/env python3
"""
Test Elite Guard Signal Generation
Validates pattern detection and signal creation
"""

import sys
import time
import json
import zmq
import logging
from datetime import datetime
from elite_guard_engine import EliteGuardEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pattern_detection():
    """Test Elite Guard pattern detection directly"""
    
    print("🧪 Testing Elite Guard Pattern Detection...")
    
    # Create engine instance
    engine = EliteGuardEngine()
    
    # Simulate market data for EURUSD
    test_symbol = "EURUSD"
    
    # Add some test tick data
    from elite_guard_engine import MarketTick
    
    # Create realistic tick sequence showing a liquidity sweep
    base_price = 1.0850
    test_ticks = [
        MarketTick(test_symbol, 1.0848, 1.0849, 1.0, 1000, time.time() - 60),
        MarketTick(test_symbol, 1.0849, 1.0850, 1.0, 1200, time.time() - 55),
        MarketTick(test_symbol, 1.0851, 1.0852, 1.0, 800, time.time() - 50),
        MarketTick(test_symbol, 1.0853, 1.0854, 1.0, 1500, time.time() - 45),  # Volume surge
        MarketTick(test_symbol, 1.0855, 1.0856, 1.0, 2000, time.time() - 40),  # Price spike
        MarketTick(test_symbol, 1.0852, 1.0853, 1.0, 1800, time.time() - 35),  # Quick reversal
        MarketTick(test_symbol, 1.0850, 1.0851, 1.0, 1600, time.time() - 30),
        MarketTick(test_symbol, 1.0849, 1.0850, 1.0, 1400, time.time() - 25),
        MarketTick(test_symbol, 1.0848, 1.0849, 1.0, 1200, time.time() - 20),
        MarketTick(test_symbol, 1.0847, 1.0848, 1.0, 1000, time.time() - 15),
    ]
    
    # Add ticks to engine
    for tick in test_ticks:
        engine.tick_data[test_symbol].append(tick)
        engine.update_ohlc_data(test_symbol, tick)
    
    print(f"📊 Added {len(test_ticks)} test ticks for {test_symbol}")
    print(f"📈 Price range: {min(t.bid for t in test_ticks):.5f} - {max(t.ask for t in test_ticks):.5f}")
    
    # Test pattern detection
    print("\n🔍 Testing Pattern Detection...")
    
    # Test liquidity sweep detection
    sweep_signal = engine.detect_liquidity_sweep_reversal(test_symbol)
    if sweep_signal:
        print(f"✅ Liquidity Sweep Detected: {sweep_signal.direction} @ {sweep_signal.entry_price:.5f}")
        print(f"   Pattern: {sweep_signal.pattern}, Confidence: {sweep_signal.confidence}%")
    else:
        print("❌ No liquidity sweep detected")
    
    # Test order block detection  
    ob_signal = engine.detect_order_block_bounce(test_symbol)
    if ob_signal:
        print(f"✅ Order Block Detected: {ob_signal.direction} @ {ob_signal.entry_price:.5f}")
    else:
        print("❌ No order block detected")
        
    # Test FVG detection
    fvg_signal = engine.detect_fair_value_gap_fill(test_symbol)
    if fvg_signal:
        print(f"✅ Fair Value Gap Detected: {fvg_signal.direction} @ {fvg_signal.entry_price:.5f}")
    else:
        print("❌ No fair value gap detected")
    
    # Test complete pattern scanning
    print("\n🎯 Testing Complete Pattern Scan...")
    patterns = engine.scan_for_patterns(test_symbol)
    
    if patterns:
        print(f"✅ Found {len(patterns)} high-quality patterns:")
        for i, pattern in enumerate(patterns, 1):
            print(f"   {i}. {pattern.pattern}: {pattern.direction} @ {pattern.final_score:.1f}%")
            
        # Test signal generation
        best_pattern = patterns[0]
        rapid_signal = engine.generate_elite_signal(best_pattern, 'average')
        precision_signal = engine.generate_elite_signal(best_pattern, 'sniper')
        
        if rapid_signal:
            print(f"\n🚀 RAPID_ASSAULT Signal:")
            print(f"   Pair: {rapid_signal['pair']}, Direction: {rapid_signal['direction']}")
            print(f"   Confidence: {rapid_signal['confidence']}%, R:R: {rapid_signal['risk_reward']}")
            print(f"   Entry: {rapid_signal['entry_price']:.5f}")
            print(f"   SL: {rapid_signal['stop_loss']:.5f}, TP: {rapid_signal['take_profit']:.5f}")
            
        if precision_signal:
            print(f"\n🎯 PRECISION_STRIKE Signal:")
            print(f"   Pair: {precision_signal['pair']}, Direction: {precision_signal['direction']}")
            print(f"   Confidence: {precision_signal['confidence']}%, R:R: {precision_signal['risk_reward']}")
            print(f"   Entry: {precision_signal['entry_price']:.5f}")
            print(f"   SL: {precision_signal['stop_loss']:.5f}, TP: {precision_signal['take_profit']:.5f}")
            
    else:
        print("❌ No patterns detected above quality threshold")
    
    return len(patterns) > 0

def test_citadel_filter():
    """Test CITADEL Shield filter functionality"""
    
    print("\n🛡️ Testing CITADEL Shield Filter...")
    
    from citadel_shield_filter import CitadelShieldFilter
    
    # Create filter instance
    shield = CitadelShieldFilter()
    shield.enable_demo_mode()
    
    # Test signal for validation
    test_signal = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0851,
        'confidence': 75,
        'base_confidence': 75,
        'xp_reward': 100,
        'pattern': 'LIQUIDITY_SWEEP_REVERSAL'
    }
    
    # Test validation
    result = shield.validate_and_enhance(test_signal)
    
    if result:
        print("✅ CITADEL Shield Validation Passed:")
        print(f"   Enhanced Confidence: {result['confidence']:.1f}%")
        print(f"   Shielded: {result['citadel_shielded']}")
        print(f"   XP Reward: {result['xp_reward']}")
        return True
    else:
        print("❌ CITADEL Shield blocked the signal")
        return False

def test_zmq_connectivity():
    """Test ZMQ connectivity and message publishing"""
    
    print("\n📡 Testing ZMQ Connectivity...")
    
    try:
        context = zmq.Context()
        
        # Test subscriber connection
        subscriber = context.socket(zmq.SUB)
        subscriber.connect("tcp://127.0.0.1:5556")
        subscriber.setsockopt(zmq.SUBSCRIBE, b"")
        subscriber.setsockopt(zmq.RCVTIMEO, 2000)
        
        print("✅ ZMQ subscriber connected to port 5556")
        
        # Test publisher connection
        publisher = context.socket(zmq.PUB)
        publisher.connect("tcp://127.0.0.1:5557")
        
        print("✅ ZMQ publisher connected to port 5557")
        
        # Send test signal
        test_signal = {
            'signal_id': 'TEST_ELITE_001',
            'pair': 'EURUSD',
            'direction': 'BUY',
            'confidence': 85.5,
            'pattern': 'TEST_PATTERN'
        }
        
        message = f"ELITE_GUARD_SIGNAL {json.dumps(test_signal)}"
        publisher.send_string(message)
        
        print("✅ Test signal published successfully")
        
        context.term()
        return True
        
    except Exception as e:
        print(f"❌ ZMQ connectivity error: {e}")
        return False

def main():
    """Run all Elite Guard tests"""
    
    print("🚀 Elite Guard + CITADEL Shield Test Suite")
    print("=" * 50)
    
    # Test results
    results = {
        'pattern_detection': False,
        'citadel_filter': False,
        'zmq_connectivity': False
    }
    
    # Run tests
    try:
        results['pattern_detection'] = test_pattern_detection()
        results['citadel_filter'] = test_citadel_filter()
        results['zmq_connectivity'] = test_zmq_connectivity()
        
    except Exception as e:
        print(f"❌ Test suite error: {e}")
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    overall_success = all(results.values())
    
    if overall_success:
        print("\n🎯 All tests passed! Elite Guard system is operational.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)