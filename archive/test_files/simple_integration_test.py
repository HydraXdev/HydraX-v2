#!/usr/bin/env python3
"""
Simple Integration Test for HydraX-v2 Pipeline

This test validates the core functionality without requiring external services:
1. Test mission file creation and retrieval
2. Test signal parsing
3. Test fire router execution
4. Test API endpoints basic functionality
5. Test error handling
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Simple-Integration-Test')

class SimpleIntegrationTest:
    """Simple integration test runner"""
    
    def __init__(self):
        self.base_dir = Path("/root/HydraX-v2")
        self.missions_dir = self.base_dir / "missions"
        self.test_results = []
        self.failed_tests = []
        
        # Ensure missions directory exists
        self.missions_dir.mkdir(exist_ok=True)
        
        logger.info("Simple integration test initialized")
    
    def test_mission_generation(self):
        """Test 1: Mission generation and file persistence"""
        try:
            logger.info("Testing mission generation...")
            
            # Add src to path
            sys.path.insert(0, str(self.base_dir / "src"))
            
            # Import mission generator
            from bitten_core.mission_briefing_generator_v5 import generate_mission
            
            # Create test signal
            test_signal = {
                "symbol": "EURUSD",
                "type": "buy",
                "tp": 1.1050,
                "sl": 1.1020,
                "tcs_score": 85
            }
            
            # Generate mission
            mission = generate_mission(test_signal, "test_user_123")
            
            # Verify mission structure
            required_fields = ["mission_id", "user_id", "symbol", "type", "tp", "sl", "tcs"]
            for field in required_fields:
                assert field in mission, f"Mission missing required field: {field}"
            
            # Verify mission file exists
            mission_file = self.missions_dir / f"{mission['mission_id']}.json"
            assert mission_file.exists(), f"Mission file not created: {mission_file}"
            
            # Verify file content
            with open(mission_file, 'r') as f:
                saved_mission = json.load(f)
            
            assert saved_mission['mission_id'] == mission['mission_id'], "Mission ID mismatch"
            assert saved_mission['symbol'] == "EURUSD", "Symbol mismatch"
            assert saved_mission['type'] == "buy", "Type mismatch"
            
            logger.info(f"✅ Mission generation test passed: {mission['mission_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Mission generation test failed: {e}")
            self.failed_tests.append(f"Mission generation: {str(e)}")
            return False
    
    def test_signal_parsing(self):
        """Test 2: Signal parsing"""
        try:
            logger.info("Testing signal parsing...")
            
            # Mock telegram bot token for testing
            original_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'
            
            try:
                # Import apex connector
                from apex_telegram_connector import ApexTelegramConnector
                
                # Create connector
                connector = ApexTelegramConnector()
                
                # Test signal parsing
                test_lines = [
                    "🎯 SIGNAL #1: EURUSD BUY TCS:85%",
                    "🎯 SIGNAL #2: GBPUSD SELL TCS:78%",
                    "🎯 SIGNAL #3: USDJPY BUY TCS:92%"
                ]
                
                for line in test_lines:
                    parsed = connector.parse_signal_line(line)
                    assert parsed is not None, f"Failed to parse: {line}"
                    assert "symbol" in parsed, "Symbol missing from parsed signal"
                    assert "type" in parsed, "Type missing from parsed signal"
                    assert "tcs_score" in parsed, "TCS score missing from parsed signal"
                    
                    logger.info(f"✓ Parsed signal: {parsed['symbol']} {parsed['type']} TCS:{parsed['tcs_score']}%")
                
                logger.info("✅ Signal parsing test passed")
                return True
                
            finally:
                # Restore original token
                if original_token:
                    os.environ['TELEGRAM_BOT_TOKEN'] = original_token
                else:
                    os.environ.pop('TELEGRAM_BOT_TOKEN', None)
            
        except Exception as e:
            logger.error(f"❌ Signal parsing test failed: {e}")
            self.failed_tests.append(f"Signal parsing: {str(e)}")
            return False
    
    def test_fire_router(self):
        """Test 3: Fire router execution"""
        try:
            logger.info("Testing fire router...")
            
            # Import fire router
            from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, ExecutionMode
            
            # Create router in simulation mode
            router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
            
            # Create test trade request
            trade_request = TradeRequest(
                symbol="EURUSD",
                direction=TradeDirection.BUY,
                volume=0.01,
                stop_loss=1.1020,
                take_profit=1.1050,
                tcs_score=85,
                user_id="test_user_123",
                mission_id=f"test_fire_{int(time.time())}"
            )
            
            # Execute trade
            result = router.execute_trade_request(trade_request)
            
            # Verify result
            assert hasattr(result, 'success'), "Result missing success field"
            assert result.success, f"Trade execution failed: {result.message}"
            assert hasattr(result, 'trade_id'), "Result missing trade_id"
            assert hasattr(result, 'message'), "Result missing message"
            
            logger.info(f"✅ Fire router test passed: {result.trade_id}")
            
            # Test system status
            status = router.get_system_status()
            assert isinstance(status, dict), "System status should be dict"
            assert "execution_mode" in status, "System status missing execution_mode"
            assert "trade_statistics" in status, "System status missing trade_statistics"
            
            logger.info("✅ Fire router system status test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fire router test failed: {e}")
            self.failed_tests.append(f"Fire router: {str(e)}")
            return False
    
    def test_mission_endpoints(self):
        """Test 4: Mission endpoints basic functionality"""
        try:
            logger.info("Testing mission endpoints...")
            
            # Import mission endpoints
            from api.mission_endpoints import load_mission_data, save_mission_data, validate_mission_access
            
            # Create test mission
            test_mission_id = f"test_endpoints_{int(time.time())}"
            test_mission = {
                "mission_id": test_mission_id,
                "user_id": "test_user_123",
                "symbol": "EURUSD",
                "type": "buy",
                "tp": 1.1050,
                "sl": 1.1020,
                "tcs": 85,
                "timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "status": "pending"
            }
            
            # Test save mission
            save_result = save_mission_data(test_mission_id, test_mission)
            assert save_result, "Failed to save mission data"
            
            # Test load mission
            loaded_mission = load_mission_data(test_mission_id)
            assert loaded_mission is not None, "Failed to load mission data"
            assert loaded_mission['mission_id'] == test_mission_id, "Mission ID mismatch"
            assert loaded_mission['symbol'] == "EURUSD", "Symbol mismatch"
            
            # Test access validation
            access_valid = validate_mission_access("test_user_123", test_mission_id)
            assert access_valid, "Mission access validation failed"
            
            logger.info("✅ Mission endpoints test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Mission endpoints test failed: {e}")
            self.failed_tests.append(f"Mission endpoints: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test 5: Error handling"""
        try:
            logger.info("Testing error handling...")
            
            # Test 1: Invalid mission loading
            from api.mission_endpoints import load_mission_data
            
            result = load_mission_data("nonexistent_mission")
            assert result is None, "Should return None for nonexistent mission"
            
            # Test 2: Invalid trade request
            from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, ExecutionMode
            
            router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
            
            # Create invalid trade request
            invalid_request = TradeRequest(
                symbol="INVALID",  # Too short
                direction=TradeDirection.BUY,
                volume=0.001,  # Too small
                tcs_score=10,  # Too low
                user_id="test_user",
                mission_id="invalid_test"
            )
            
            result = router.execute_trade_request(invalid_request)
            assert not result.success, "Invalid trade should fail validation"
            
            # Test 3: Invalid JSON handling
            invalid_json_file = self.missions_dir / "invalid_test.json"
            with open(invalid_json_file, 'w') as f:
                f.write("invalid json")
            
            result = load_mission_data("invalid_test")
            assert result is None, "Should handle invalid JSON gracefully"
            
            # Clean up
            if invalid_json_file.exists():
                invalid_json_file.unlink()
            
            logger.info("✅ Error handling test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.failed_tests.append(f"Error handling: {str(e)}")
            return False
    
    def test_complete_workflow(self):
        """Test 6: Complete workflow simulation"""
        try:
            logger.info("Testing complete workflow...")
            
            # Step 1: Generate signal
            test_signal = {
                "symbol": "GBPUSD",
                "type": "sell",
                "tp": 1.2750,
                "sl": 1.2800,
                "tcs_score": 78
            }
            
            # Step 2: Generate mission
            from bitten_core.mission_briefing_generator_v5 import generate_mission
            mission = generate_mission(test_signal, "test_user_456")
            
            # Step 3: Load mission through API
            from api.mission_endpoints import load_mission_data
            loaded_mission = load_mission_data(mission['mission_id'])
            assert loaded_mission is not None, "Failed to load generated mission"
            
            # Step 4: Execute trade
            from bitten_core.fire_router import FireRouter, ExecutionMode
            router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
            
            # Convert mission to legacy format for backward compatibility
            legacy_mission = {
                "mission_id": mission['mission_id'],
                "user_id": mission['user_id'],
                "symbol": mission['symbol'],
                "type": mission['type'],
                "tp": mission['tp'],
                "sl": mission['sl'],
                "lot_size": mission.get('lot_size', 0.01),
                "tcs": mission['tcs']
            }
            
            execution_result = router.execute_trade(legacy_mission)
            assert execution_result in ["sent_to_bridge", "failed"], f"Unexpected execution result: {execution_result}"
            
            logger.info("✅ Complete workflow test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Complete workflow test failed: {e}")
            self.failed_tests.append(f"Complete workflow: {str(e)}")
            return False
    
    def cleanup_test_files(self):
        """Clean up test files"""
        try:
            # Remove test mission files
            for mission_file in self.missions_dir.glob("test_*.json"):
                try:
                    mission_file.unlink()
                except:
                    pass
            
            logger.info("✅ Test files cleaned up")
            
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting simple integration tests...")
        
        tests = [
            ("Mission Generation", self.test_mission_generation),
            ("Signal Parsing", self.test_signal_parsing),
            ("Fire Router", self.test_fire_router),
            ("Mission Endpoints", self.test_mission_endpoints),
            ("Error Handling", self.test_error_handling),
            ("Complete Workflow", self.test_complete_workflow)
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
                self.failed_tests.append(f"{test_name}: {str(e)}")
        
        # Print summary
        success_rate = (passed / total) * 100
        
        print(f"\n{'='*60}")
        print("SIMPLE INTEGRATION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print("\nFailed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        print(f"{'='*60}")
        
        # Cleanup
        self.cleanup_test_files()
        
        return passed == total

def main():
    """Main test function"""
    test_runner = SimpleIntegrationTest()
    
    try:
        success = test_runner.run_all_tests()
        
        if success:
            print("\n🎉 ALL TESTS PASSED - Core system is working correctly!")
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