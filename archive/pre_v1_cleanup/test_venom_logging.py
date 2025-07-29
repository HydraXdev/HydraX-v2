#!/usr/bin/env python3
"""
Test VENOM Activity Logging System
"""

import sys
sys.path.insert(0, '/root/HydraX-v2/src')

from venom_activity_logger import (
    log_feed_monitor_start, 
    log_feed_monitor_heartbeat,
    log_venom_signal_generated,
    log_signal_to_core,
    log_engine_status,
    log_error
)

def test_logging_system():
    """Test all logging functions"""
    print("🧠 Testing VENOM Activity Logging System...")
    
    # Test feed monitor logging
    print("1. Testing VenomFeedMonitor logging...")
    log_feed_monitor_start("hydrax_engine_node_v7", "test_initialization")
    log_feed_monitor_heartbeat("hydrax_engine_node_v7", {
        "container_healthy": True,
        "mt5_active": True,
        "tick_data_flowing": True,
        "overall_status": "healthy"
    })
    
    # Test VENOM signal generation logging
    print("2. Testing VENOM signal generation logging...")
    test_signal = {
        "signal_id": "VENOM_TEST_EURUSD_001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "confidence": 87.5,
        "signal_type": "RAPID_ASSAULT",
        "quality": "platinum"
    }
    log_venom_signal_generated(test_signal)
    
    # Test Core signal processing logging
    print("3. Testing Core signal processing logging...")
    log_signal_to_core("VENOM_TEST_EURUSD_001", "processed", {
        "symbol": "EURUSD",
        "direction": "BUY",
        "confidence": 87.5
    })
    
    # Test engine status logging
    print("4. Testing engine status logging...")
    log_engine_status("VenomV7SmartTimer", "operational", {
        "signals_generated": 25,
        "success_rate": 84.3
    })
    
    # Test error logging
    print("5. Testing error logging...")
    log_error("TestComponent", "This is a test error", {
        "test_data": "sample_value"
    })
    
    print("✅ All logging tests completed!")
    print("📄 Check /root/HydraX-v2/logs/venom_activity.log for JSONL output")

if __name__ == "__main__":
    test_logging_system()