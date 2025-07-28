#!/usr/bin/env python3
"""
Basic System Test - Tests core functionality without complex dependencies

This test validates:
1. Signal parsing from apex_telegram_connector
2. Fire router execution
3. Mission endpoints API basic functionality
4. Directory structure
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Basic-System-Test')

class BasicSystemTest:
    """Basic system functionality test"""
    
    def __init__(self):
        self.base_dir = Path("/root/HydraX-v2")
        self.missions_dir = self.base_dir / "missions"
        self.test_results = []
        
        # Ensure directories exist
        self.missions_dir.mkdir(exist_ok=True)
        
        logger.info("Basic system test initialized")
    
    def test_signal_parsing(self):
        """Test signal parsing functionality"""
        try:
            logger.info("Testing signal parsing...")
            
            # Mock telegram bot token
            original_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'
            
            try:
                # Import and test apex connector
                from apex_telegram_connector import ApexTelegramConnector
                
                connector = ApexTelegramConnector()
                
                # Test signals
                test_signals = [
                    "🎯 SIGNAL #1: EURUSD BUY TCS:85%",
                    "🎯 SIGNAL #2: GBPUSD SELL TCS:78%",
                    "🎯 SIGNAL #3: USDJPY BUY TCS:92%"
                ]
                
                parsed_signals = []
                for signal_line in test_signals:
                    parsed = connector.parse_signal_line(signal_line)
                    if parsed:
                        parsed_signals.append(parsed)
                        logger.info(f"✓ Parsed: {parsed['symbol']} {parsed['type']} TCS:{parsed['tcs_score']}%")
                    else:
                        logger.error(f"Failed to parse: {signal_line}")
                        return False
                
                if len(parsed_signals) == 3:
                    logger.info("✅ Signal parsing test passed")
                    return True
                else:
                    logger.error(f"Expected 3 parsed signals, got {len(parsed_signals)}")
                    return False
                    
            finally:
                # Restore original token
                if original_token:
                    os.environ['TELEGRAM_BOT_TOKEN'] = original_token
                else:
                    os.environ.pop('TELEGRAM_BOT_TOKEN', None)
                    
        except Exception as e:
            logger.error(f"❌ Signal parsing test failed: {e}")
            return False
    
    def test_fire_router(self):
        """Test fire router functionality"""
        try:
            logger.info("Testing fire router...")
            
            # Add src to path
            sys.path.insert(0, str(self.base_dir / "src"))
            
            from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, ExecutionMode
            
            # Create router in simulation mode
            router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
            
            # Test multiple trade requests
            success_count = 0
            total_tests = 5
            
            for i in range(total_tests):
                trade_request = TradeRequest(
                    symbol="EURUSD",
                    direction=TradeDirection.BUY,
                    volume=0.01,
                    stop_loss=1.1020,
                    take_profit=1.1050,
                    tcs_score=85,
                    user_id=f"test_user_{i}",
                    mission_id=f"test_mission_{i}_{int(time.time())}"
                )
                
                result = router.execute_trade_request(trade_request)
                
                if result.success:
                    success_count += 1
                    logger.info(f"✓ Trade {i+1} executed successfully")
                else:
                    logger.warning(f"Trade {i+1} failed: {result.message}")
            
            # We expect at least 80% success rate (allowing for simulated failures)
            success_rate = success_count / total_tests
            if success_rate >= 0.8:
                logger.info(f"✅ Fire router test passed: {success_rate:.1%} success rate")
                return True
            else:
                logger.error(f"❌ Fire router test failed: {success_rate:.1%} success rate")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fire router test failed: {e}")
            return False
    
    def test_mission_endpoints(self):
        """Test mission endpoints basic functionality"""
        try:
            logger.info("Testing mission endpoints...")
            
            # Add src to path
            sys.path.insert(0, str(self.base_dir / "src"))
            
            from api.mission_endpoints import load_mission_data, save_mission_data
            
            # Create test mission
            test_mission_id = f"basic_test_{int(time.time())}"
            test_mission = {
                "mission_id": test_mission_id,
                "user_id": "test_user",
                "symbol": "EURUSD",
                "type": "buy",
                "tp": 1.1050,
                "sl": 1.1020,
                "tcs": 85,
                "timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "status": "pending"
            }
            
            # Test save
            save_result = save_mission_data(test_mission_id, test_mission)
            if not save_result:
                logger.error("Failed to save mission data")
                return False
            
            # Test load
            loaded_mission = load_mission_data(test_mission_id)
            if not loaded_mission:
                logger.error("Failed to load mission data")
                return False
            
            # Verify data integrity
            if loaded_mission['mission_id'] != test_mission_id:
                logger.error("Mission ID mismatch")
                return False
            
            if loaded_mission['symbol'] != "EURUSD":
                logger.error("Symbol mismatch")
                return False
            
            logger.info("✅ Mission endpoints test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Mission endpoints test failed: {e}")
            return False
    
    def test_directory_structure(self):
        """Test directory structure"""
        try:
            logger.info("Testing directory structure...")
            
            required_dirs = [
                self.missions_dir,
                self.base_dir / "src",
                self.base_dir / "src" / "api",
                self.base_dir / "src" / "bitten_core"
            ]
            
            for dir_path in required_dirs:
                if not dir_path.exists():
                    logger.error(f"Required directory missing: {dir_path}")
                    return False
                logger.info(f"✓ Directory exists: {dir_path}")
            
            required_files = [
                self.base_dir / "apex_telegram_connector.py",
                self.base_dir / "src" / "api" / "mission_endpoints.py",
                self.base_dir / "src" / "bitten_core" / "fire_router.py"
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    logger.error(f"Required file missing: {file_path}")
                    return False
                logger.info(f"✓ File exists: {file_path}")
            
            logger.info("✅ Directory structure test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Directory structure test failed: {e}")
            return False
    
    def test_integration(self):
        """Test basic integration"""
        try:
            logger.info("Testing basic integration...")
            
            # Test signal parsing
            os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'
            
            try:
                from apex_telegram_connector import ApexTelegramConnector
                connector = ApexTelegramConnector()
                
                # Parse a signal
                parsed = connector.parse_signal_line("🎯 SIGNAL #1: EURUSD BUY TCS:85%")
                if not parsed:
                    logger.error("Failed to parse signal in integration test")
                    return False
                
                # Create mission using parsed signal
                test_mission = {
                    "mission_id": f"integration_test_{int(time.time())}",
                    "user_id": "test_user",
                    "symbol": parsed["symbol"],
                    "type": parsed["type"],
                    "tp": parsed["tp"],
                    "sl": parsed["sl"],
                    "tcs": parsed["tcs_score"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                    "status": "pending"
                }
                
                # Save mission
                from api.mission_endpoints import save_mission_data
                save_result = save_mission_data(test_mission["mission_id"], test_mission)
                if not save_result:
                    logger.error("Failed to save mission in integration test")
                    return False
                
                # Execute trade using fire router
                from bitten_core.fire_router import FireRouter, ExecutionMode
                router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
                
                # Convert to legacy format
                legacy_mission = {
                    "mission_id": test_mission["mission_id"],
                    "user_id": test_mission["user_id"],
                    "symbol": test_mission["symbol"],
                    "type": test_mission["type"],
                    "tp": test_mission["tp"],
                    "sl": test_mission["sl"],
                    "lot_size": 0.01,
                    "tcs": test_mission["tcs"]
                }
                
                execution_result = router.execute_trade(legacy_mission)
                
                if execution_result not in ["sent_to_bridge", "failed"]:
                    logger.error(f"Unexpected execution result: {execution_result}")
                    return False
                
                logger.info("✅ Basic integration test passed")
                return True
                
            finally:
                os.environ.pop('TELEGRAM_BOT_TOKEN', None)
                
        except Exception as e:
            logger.error(f"❌ Basic integration test failed: {e}")
            return False
    
    def cleanup_test_files(self):
        """Clean up test files"""
        try:
            for mission_file in self.missions_dir.glob("basic_test_*.json"):
                try:
                    mission_file.unlink()
                except:
                    pass
            
            for mission_file in self.missions_dir.glob("integration_test_*.json"):
                try:
                    mission_file.unlink()
                except:
                    pass
            
            logger.info("✅ Test files cleaned up")
            
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def run_all_tests(self):
        """Run all basic tests"""
        logger.info("Starting basic system tests...")
        
        tests = [
            ("Directory Structure", self.test_directory_structure),
            ("Signal Parsing", self.test_signal_parsing),
            ("Fire Router", self.test_fire_router),
            ("Mission Endpoints", self.test_mission_endpoints),
            ("Basic Integration", self.test_integration)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                if test_func():
                    passed += 1
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    logger.error(f"❌ {test_name} FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} FAILED with exception: {e}")
        
        # Print summary
        success_rate = (passed / total) * 100
        
        print(f"\n{'='*60}")
        print("BASIC SYSTEM TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"{'='*60}")
        
        # Cleanup
        self.cleanup_test_files()
        
        return passed == total

def main():
    """Main test function"""
    test_runner = BasicSystemTest()
    
    try:
        success = test_runner.run_all_tests()
        
        if success:
            print("\n🎉 ALL BASIC TESTS PASSED - Core system is working!")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED - Please check the issues above")
            return 1
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"Test runner failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())