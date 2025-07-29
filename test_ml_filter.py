#!/usr/bin/env python3
"""
Test script for CITADEL ML Filter
Demonstrates signal filtering based on predicted win probability
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.append('/root/HydraX-v2')

try:
    from citadel_ml_filter import CitadelMLFilter
    ML_FILTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing ML filter: {e}")
    ML_FILTER_AVAILABLE = False
    sys.exit(1)

def create_sample_signals():
    """Create sample signals for testing"""
    return [
        {
            'signal_id': 'TEST_EURUSD_001',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 85.5,
            'entry_price': 1.16527,
            'stop_loss': 1.16417,
            'take_profit': 1.16747,
            'tcs_score': 85.5
        },
        {
            'signal_id': 'TEST_GBPUSD_002',
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'confidence': 72.3,
            'entry_price': 1.27820,
            'stop_loss': 1.27920,
            'take_profit': 1.27620,
            'tcs_score': 72.3
        },
        {
            'signal_id': 'TEST_USDJPY_003',
            'symbol': 'USDJPY',
            'direction': 'BUY',
            'confidence': 91.2,
            'entry_price': 149.85,
            'stop_loss': 149.65,
            'take_profit': 150.25,
            'tcs_score': 91.2
        },
        {
            'signal_id': 'TEST_AUDUSD_004',
            'symbol': 'AUDUSD',
            'direction': 'SELL',
            'confidence': 68.7,
            'entry_price': 0.67450,
            'stop_loss': 0.67550,
            'take_profit': 0.67250,
            'tcs_score': 68.7
        }
    ]

def setup_test_config():
    """Setup test configuration for ML filter"""
    config = {
        "global": {
            "auto_close_seconds": 7200,
            "ml_filter": {
                "enabled": True,
                "min_acceptable_probability": 0.65,
                "log_suppressed": True,
                "model_override": False
            }
        },
        "_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "test_run": True
        }
    }
    
    # Save test config
    config_path = Path("/root/HydraX-v2/citadel_state.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"📝 Test configuration saved to {config_path}")
    return config

def test_ml_filter():
    """Test the ML filter with sample signals"""
    print("🧪 Testing CITADEL ML Filter")
    print("=" * 50)
    
    # Setup test configuration
    config = setup_test_config()
    min_prob = config['global']['ml_filter']['min_acceptable_probability']
    print(f"🎯 Minimum acceptable probability: {min_prob:.3f}")
    
    # Initialize ML filter
    try:
        ml_filter = CitadelMLFilter()
        print("✅ ML Filter initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ML filter: {e}")
        return
    
    # Get filter statistics
    stats = ml_filter.get_filter_stats()
    print(f"📊 Model loaded: {stats.get('model_loaded', False)}")
    print(f"📊 Model type: {stats.get('model_type', 'unknown')}")
    print(f"📊 Model accuracy: {stats.get('model_accuracy', 0):.3f}")
    
    # Test signals
    sample_signals = create_sample_signals()
    
    print(f"\n🔍 Testing {len(sample_signals)} sample signals:")
    print("=" * 50)
    
    allowed_count = 0
    blocked_count = 0
    
    for i, signal in enumerate(sample_signals, 1):
        print(f"\n📡 Signal {i}: {signal['symbol']} {signal['direction']}")
        print(f"   TCS Score: {signal['confidence']}")
        
        # Test the filter
        should_allow, filter_info = ml_filter.filter_signal(signal)
        
        if should_allow:
            allowed_count += 1
            status = "✅ ALLOWED"
            color = "🟢"
        else:
            blocked_count += 1
            status = "🚫 BLOCKED"
            color = "🔴"
        
        print(f"   {color} {status}")
        
        # Show prediction details
        if filter_info.get('predicted_win_probability') is not None:
            prob = filter_info['predicted_win_probability']
            threshold = filter_info.get('min_threshold', min_prob)
            print(f"   🤖 Predicted probability: {prob:.3f}")
            print(f"   📏 Threshold: {threshold:.3f}")
            
            if prob >= threshold:
                print(f"   ✅ Probability above threshold (+{(prob - threshold):.3f})")
            else:
                print(f"   ❌ Probability below threshold (-{(threshold - prob):.3f})")
        
        # Show filter result
        result = filter_info.get('filter_result', 'unknown')
        print(f"   📋 Filter result: {result}")
        
        if result == 'prediction_failed':
            print(f"   ⚠️ Prediction failed - signal allowed by default")
        elif result == 'disabled':
            print(f"   ⚠️ ML filter disabled - signal allowed")
    
    # Summary
    print(f"\n📊 Test Summary:")
    print("=" * 30)
    print(f"Total signals tested: {len(sample_signals)}")
    print(f"✅ Allowed: {allowed_count}")
    print(f"🚫 Blocked: {blocked_count}")
    print(f"📈 Pass rate: {(allowed_count / len(sample_signals)) * 100:.1f}%")
    
    # Check suppressed log
    suppressed_log_path = Path("/root/HydraX-v2/logs/suppressed_signals.log")
    if suppressed_log_path.exists():
        with open(suppressed_log_path, 'r') as f:
            suppressed_lines = [line for line in f if line.strip()]
        print(f"📝 Suppressed signals logged: {len(suppressed_lines)}")
    else:
        print(f"📝 No suppressed signals log found")

def test_configuration_changes():
    """Test different configuration scenarios"""
    print(f"\n🔧 Testing Configuration Changes:")
    print("=" * 40)
    
    ml_filter = CitadelMLFilter()
    test_signal = {
        'signal_id': 'CONFIG_TEST_001',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'confidence': 75.0,
        'entry_price': 1.16500,
        'stop_loss': 1.16400,
        'take_profit': 1.16700
    }
    
    # Test 1: Normal operation
    print(f"\n1️⃣ Normal operation (threshold: 0.65):")
    should_allow, filter_info = ml_filter.filter_signal(test_signal)
    print(f"   Result: {'✅ ALLOWED' if should_allow else '🚫 BLOCKED'}")
    if filter_info.get('predicted_win_probability'):
        print(f"   Probability: {filter_info['predicted_win_probability']:.3f}")
    
    # Test 2: Disabled filter
    print(f"\n2️⃣ Testing disabled filter:")
    # Update config to disable
    config_path = Path("/root/HydraX-v2/citadel_state.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    config['global']['ml_filter']['enabled'] = False
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    should_allow, filter_info = ml_filter.filter_signal(test_signal)
    print(f"   Result: {'✅ ALLOWED' if should_allow else '🚫 BLOCKED'}")
    print(f"   Reason: {filter_info.get('filter_result', 'unknown')}")
    
    # Test 3: Very high threshold
    print(f"\n3️⃣ Testing very high threshold (0.95):")
    config['global']['ml_filter']['enabled'] = True
    config['global']['ml_filter']['min_acceptable_probability'] = 0.95
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    should_allow, filter_info = ml_filter.filter_signal(test_signal)
    print(f"   Result: {'✅ ALLOWED' if should_allow else '🚫 BLOCKED'}")
    if filter_info.get('predicted_win_probability'):
        prob = filter_info['predicted_win_probability']
        threshold = filter_info['min_threshold']
        print(f"   Probability: {prob:.3f} vs Threshold: {threshold:.3f}")
    
    # Reset to normal
    config['global']['ml_filter']['min_acceptable_probability'] = 0.65
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\n🔄 Configuration reset to normal")

def main():
    """Main test function"""
    if not ML_FILTER_AVAILABLE:
        print("❌ ML Filter not available - cannot run tests")
        return
    
    try:
        print("🤖 CITADEL ML Filter Test Suite")
        print("=" * 50)
        
        # Run main tests
        test_ml_filter()
        
        # Test configuration changes
        test_configuration_changes()
        
        print(f"\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()