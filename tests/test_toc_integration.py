#!/usr/bin/env python3
"""
TOC System Integration Test

This script tests the complete signal flow:
1. Terminal assignment
2. Signal firing
3. Trade execution
4. Result callback
"""

import os
import sys
import json
import time
import requests
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TOC_URL = os.getenv('TOC_URL', 'http://localhost:5000')
TEST_USER_ID = "test_user_123"
TEST_SIGNAL = {
    'symbol': 'EURUSD',
    'direction': 'buy',
    'volume': 0.01,
    'stop_loss': 1.0850,
    'take_profit': 1.0950,
    'comment': 'BITTEN Test Signal'
}


class TOCIntegrationTest:
    """Test the complete TOC system integration"""
    
    def __init__(self):
        self.toc_url = TOC_URL
        self.terminal_assigned = False
        self.signal_fired = False
        self.trade_result_received = False
        
    def test_health_check(self):
        """Test TOC server health"""
        logger.info("Testing TOC health check...")
        
        try:
            response = requests.get(f"{self.toc_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ TOC Server healthy: {data}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to TOC server: {e}")
            return False
    
    def test_terminal_assignment(self):
        """Test terminal assignment"""
        logger.info("Testing terminal assignment...")
        
        try:
            payload = {
                'user_id': TEST_USER_ID,
                'terminal_type': 'press_pass',
                'mt5_credentials': {
                    'login': '12345',
                    'password': 'demo_password',
                    'server': 'MetaQuotes-Demo'
                }
            }
            
            response = requests.post(
                f"{self.toc_url}/assign-terminal",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Terminal assigned: {data['assignment']['terminal_name']}")
                self.terminal_assigned = True
                return True
            else:
                logger.error(f"❌ Assignment failed: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Assignment error: {e}")
            return False
    
    def test_fire_signal(self):
        """Test firing a trade signal"""
        logger.info("Testing signal fire...")
        
        if not self.terminal_assigned:
            logger.error("❌ Cannot fire signal without terminal assignment")
            return False
        
        try:
            payload = {
                'user_id': TEST_USER_ID,
                'signal': TEST_SIGNAL
            }
            
            response = requests.post(
                f"{self.toc_url}/fire",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"✅ Signal fired successfully: {data}")
                    self.signal_fired = True
                    return True
                else:
                    logger.error(f"❌ Signal rejected: {data.get('error')}")
                    return False
            else:
                logger.error(f"❌ Fire failed: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fire error: {e}")
            return False
    
    def test_user_status(self):
        """Test user status check"""
        logger.info("Testing user status...")
        
        try:
            response = requests.get(
                f"{self.toc_url}/status/{TEST_USER_ID}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ User status retrieved:")
                logger.info(f"   - Tier: {data['user']['tier']}")
                logger.info(f"   - Fire Mode: {data['user']['fire_mode']}")
                logger.info(f"   - Assignments: {len(data['assignments'])}")
                logger.info(f"   - Daily Stats: {data['daily_stats']}")
                return True
            else:
                logger.error(f"❌ Status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Status error: {e}")
            return False
    
    def test_terminal_list(self):
        """Test terminal listing"""
        logger.info("Testing terminal list...")
        
        try:
            response = requests.get(f"{self.toc_url}/terminals", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Terminals retrieved:")
                logger.info(f"   - Available terminals: {len(data['terminals'])}")
                logger.info(f"   - Statistics: {data['statistics']}")
                return True
            else:
                logger.error(f"❌ Terminal list failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Terminal list error: {e}")
            return False
    
    def test_metrics(self):
        """Test system metrics"""
        logger.info("Testing system metrics...")
        
        try:
            response = requests.get(f"{self.toc_url}/metrics", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Metrics retrieved:")
                logger.info(f"   - Fire router stats: {data['fire_router']}")
                logger.info(f"   - Active sessions: {data['active_sessions']}")
                return True
            else:
                logger.error(f"❌ Metrics failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Metrics error: {e}")
            return False
    
    def simulate_trade_result(self):
        """Simulate a trade result callback"""
        logger.info("Simulating trade result...")
        
        if not self.signal_fired:
            logger.error("❌ Cannot simulate result without fired signal")
            return False
        
        try:
            # Simulate a winning trade
            payload = {
                'user_id': TEST_USER_ID,
                'trade_result': {
                    'ticket': 12345678,
                    'symbol': TEST_SIGNAL['symbol'],
                    'type': TEST_SIGNAL['direction'],
                    'volume': TEST_SIGNAL['volume'],
                    'open_price': 1.0900,
                    'close_price': 1.0920,
                    'profit': 20.00,
                    'commission': -0.10,
                    'swap': 0,
                    'closed_at': datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                f"{self.toc_url}/trade-result",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Trade result processed: {data}")
                self.trade_result_received = True
                return True
            else:
                logger.error(f"❌ Result processing failed: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Result error: {e}")
            return False
    
    def test_terminal_release(self):
        """Test terminal release"""
        logger.info("Testing terminal release...")
        
        try:
            response = requests.post(
                f"{self.toc_url}/release-terminal/{TEST_USER_ID}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Terminal released: {data}")
                return True
            else:
                logger.error(f"❌ Release failed: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Release error: {e}")
            return False
    
    def run_all_tests(self):
        """Run complete integration test suite"""
        logger.info("=" * 60)
        logger.info("Starting TOC Integration Tests")
        logger.info("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Terminal Assignment", self.test_terminal_assignment),
            ("Fire Signal", self.test_fire_signal),
            ("User Status", self.test_user_status),
            ("Terminal List", self.test_terminal_list),
            ("System Metrics", self.test_metrics),
            ("Trade Result", self.simulate_trade_result),
            ("Terminal Release", self.test_terminal_release)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*40}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*40}")
            
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Test crashed: {e}")
                failed += 1
            
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {len(tests)}")
        logger.info(f"Passed: {passed} ✅")
        logger.info(f"Failed: {failed} ❌")
        logger.info(f"Success Rate: {(passed/len(tests)*100):.1f}%")
        
        if failed == 0:
            logger.info("\n🎉 ALL TESTS PASSED! TOC System is fully operational.")
        else:
            logger.error(f"\n⚠️  {failed} tests failed. Check the logs above.")
        
        return failed == 0


def main():
    """Main test runner"""
    tester = TOCIntegrationTest()
    
    # Check if TOC server is running
    if not tester.test_health_check():
        logger.error("\n❌ TOC Server is not running!")
        logger.error("Please start it with: python start_toc_system.py")
        return 1
    
    # Run all tests
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())