#!/usr/bin/env python3
"""
Test script for Market Data Watchdog
Simulates various failure scenarios
"""

import time
import subprocess
import requests
import sys

def test_health_check():
    """Test health check endpoints directly"""
    print("🔍 Testing health check endpoints...")
    
    endpoints = [
        "http://localhost:8001/market-data/health",
        "http://localhost:8001/market-data/venom-feed?symbol=EURUSD"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(endpoint, timeout=5)
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:100]}...")
        except requests.exceptions.Timeout:
            print(f"  ❌ TIMEOUT - This should trigger watchdog restart!")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

def test_telegram_alert():
    """Test Telegram alert functionality"""
    print("\n📱 Testing Telegram alert...")
    
    try:
        from market_data_watchdog import MarketDataWatchdog
        watchdog = MarketDataWatchdog()
        watchdog.send_telegram_alert("🧪 TEST ALERT - Market Data Watchdog Test")
        print("  ✅ Telegram alert sent successfully")
    except Exception as e:
        print(f"  ❌ Failed to send alert: {e}")

def check_watchdog_service():
    """Check if watchdog service is running"""
    print("\n🐕 Checking watchdog service status...")
    
    try:
        result = subprocess.run(['systemctl', 'is-active', 'market-data-watchdog'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Service is {result.stdout.strip()}")
        else:
            print(f"  ❌ Service is not active")
            
        # Show recent logs
        print("\n📝 Recent watchdog logs:")
        result = subprocess.run(['journalctl', '-u', 'market-data-watchdog', 
                               '--since', '2 minutes ago', '--no-pager'], 
                              capture_output=True, text=True)
        print(result.stdout)
        
    except Exception as e:
        print(f"  ❌ Failed to check service: {e}")

def main():
    print("🧪 Market Data Watchdog Test Suite")
    print("=" * 50)
    
    test_health_check()
    test_telegram_alert()
    check_watchdog_service()
    
    print("\n✅ Test completed!")
    print("💡 Watchdog will detect timeouts and restart the service within 2 minutes.")

if __name__ == "__main__":
    main()