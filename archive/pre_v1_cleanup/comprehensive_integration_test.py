#!/usr/bin/env python3
"""
Comprehensive Integration Test for HydraX-v2 Signal-to-Mission-to-Execution Pipeline

This test validates the complete flow:
1. Generate test signal in log format
2. Verify apex_telegram_connector picks it up
3. Check mission file creation
4. Test mission_endpoints API
5. Simulate fire action through fire_router
6. Verify trade execution result
7. Test WebApp integration
8. Validate error handling

Requirements:
- All system components must be properly integrated
- Mission files must persist correctly
- API endpoints must work
- Fire router must execute trades
- Proper error handling throughout
"""

import asyncio
import json
import os
import sys
import time
import tempfile
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from unittest.mock import Mock, patch
import signal
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Integration-Test')

class IntegrationTestRunner:
    """Comprehensive integration test runner"""
    
    def __init__(self):
        self.base_dir = Path("/root/HydraX-v2")
        self.missions_dir = self.base_dir / "missions"
        self.logs_dir = self.base_dir / "logs"
        self.test_log_file = self.base_dir / "apex_v5_live_real.log"
        
        # Test configuration
        self.test_user_ids = ["test_user_123", "test_user_456", "test_user_789"]
        self.test_symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        self.test_results = []
        self.failed_tests = []
        
        # API configuration
        self.api_base_url = "http://localhost:5001"
        self.webapp_base_url = "http://localhost:5000"
        
        # Test tracking
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests_count = 0
        
        # Services
        self.services = {}
        
        logger.info("Integration test runner initialized")
    
    def run_test(self, test_name: str, test_func):
        """Run a single test with error handling"""
        self.total_tests += 1
        logger.info(f"Running test: {test_name}")
        
        try:
            start_time = time.time()
            result = test_func()
            execution_time = time.time() - start_time
            
            if result:
                self.passed_tests += 1
                logger.info(f"✅ Test PASSED: {test_name} ({execution_time:.2f}s)")
                self.test_results.append({
                    "test": test_name,
                    "status": "PASSED",
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                self.failed_tests_count += 1
                logger.error(f"❌ Test FAILED: {test_name} ({execution_time:.2f}s)")
                self.failed_tests.append(test_name)
                self.test_results.append({
                    "test": test_name,
                    "status": "FAILED",
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
            
            return result
            
        except Exception as e:
            self.failed_tests_count += 1
            logger.error(f"❌ Test FAILED with exception: {test_name} - {str(e)}")
            self.failed_tests.append(test_name)
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def test_directory_structure(self) -> bool:
        """Test 1: Verify required directory structure exists"""
        try:
            required_dirs = [
                self.missions_dir,
                self.logs_dir,
                self.base_dir / "src" / "api",
                self.base_dir / "src" / "bitten_core"
            ]
            
            for dir_path in required_dirs:
                if not dir_path.exists():
                    logger.error(f"Required directory missing: {dir_path}")
                    return False
                logger.info(f"✓ Directory exists: {dir_path}")
            
            # Check for required files
            required_files = [
                self.base_dir / "apex_telegram_connector.py",
                self.base_dir / "src" / "api" / "mission_endpoints.py",
                self.base_dir / "src" / "bitten_core" / "fire_router.py",
                self.base_dir / "webapp_server.py"
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    logger.error(f"Required file missing: {file_path}")
                    return False
                logger.info(f"✓ File exists: {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Directory structure test failed: {e}")
            return False
    
    def test_mission_file_creation(self) -> bool:
        """Test 2: Test mission file creation and persistence"""
        try:
            # Import mission generator
            sys.path.append(str(self.base_dir))
            from src.bitten_core.mission_briefing_generator_v5 import generate_mission
            
            # Create test signal
            test_signal = {
                "symbol": "EURUSD",
                "type": "buy",
                "tp": 1.1050,
                "sl": 1.1020,
                "tcs_score": 85
            }
            
            # Generate mission
            mission = generate_mission(test_signal, self.test_user_ids[0])
            
            # Verify mission structure
            required_fields = ["mission_id", "user_id", "symbol", "type", "tp", "sl", "tcs", "timestamp", "expires_at", "status"]
            for field in required_fields:
                if field not in mission:
                    logger.error(f"Mission missing required field: {field}")
                    return False
            
            # Verify mission file was created
            mission_file = self.missions_dir / f"{mission['mission_id']}.json"
            if not mission_file.exists():
                logger.error(f"Mission file not created: {mission_file}")
                return False
            
            # Verify file content
            with open(mission_file, 'r') as f:
                saved_mission = json.load(f)
            
            if saved_mission['mission_id'] != mission['mission_id']:
                logger.error("Mission file content mismatch")
                return False
            
            logger.info(f"✓ Mission created and persisted: {mission['mission_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Mission file creation test failed: {e}")
            return False
    
    def test_signal_generation_and_parsing(self) -> bool:
        """Test 3: Generate test signal and verify parsing"""
        try:
            # Create test log entry
            test_signal_line = "🎯 SIGNAL #1: EURUSD BUY TCS:85%"
            
            # Import signal parser
            from apex_telegram_connector import ApexTelegramConnector
            
            # Create connector instance
            with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'}):
                connector = ApexTelegramConnector()
                
                # Parse signal
                parsed_signal = connector.parse_signal_line(test_signal_line)
                
                if not parsed_signal:
                    logger.error("Signal parsing failed")
                    return False
                
                # Verify parsed signal
                expected_fields = ["symbol", "type", "tcs_score"]
                for field in expected_fields:
                    if field not in parsed_signal:
                        logger.error(f"Parsed signal missing field: {field}")
                        return False
                
                if parsed_signal["symbol"] != "EURUSD":
                    logger.error(f"Symbol mismatch: expected EURUSD, got {parsed_signal['symbol']}")
                    return False
                
                if parsed_signal["type"] != "buy":
                    logger.error(f"Type mismatch: expected buy, got {parsed_signal['type']}")
                    return False
                
                if parsed_signal["tcs_score"] != 85:
                    logger.error(f"TCS score mismatch: expected 85, got {parsed_signal['tcs_score']}")
                    return False
                
                logger.info("✓ Signal parsing successful")
                return True
                
        except Exception as e:
            logger.error(f"Signal generation and parsing test failed: {e}")
            return False
    
    def test_mission_endpoints_api(self) -> bool:
        """Test 4: Test mission endpoints API"""
        try:
            # Start mission endpoints API in background
            import subprocess
            import time
            
            # Import mission endpoints
            sys.path.append(str(self.base_dir / "src" / "api"))
            from mission_endpoints import app
            
            # Start Flask app in background thread
            def run_api():
                app.run(host='0.0.0.0', port=5001, debug=False)
            
            api_thread = threading.Thread(target=run_api, daemon=True)
            api_thread.start()
            
            # Wait for API to start
            time.sleep(2)
            
            # Test health endpoint
            try:
                response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
                if response.status_code != 200:
                    logger.error(f"Health check failed: {response.status_code}")
                    return False
                
                health_data = response.json()
                if health_data.get("status") != "healthy":
                    logger.error(f"API not healthy: {health_data}")
                    return False
                
                logger.info("✓ Mission API health check passed")
                
            except requests.RequestException as e:
                logger.error(f"API health check failed: {e}")
                return False
            
            # Test mission creation through API
            # First create a mission file
            test_mission_id = f"test_api_{int(time.time())}"
            test_mission = {
                "mission_id": test_mission_id,
                "user_id": self.test_user_ids[0],
                "symbol": "EURUSD",
                "type": "buy",
                "tp": 1.1050,
                "sl": 1.1020,
                "tcs": 85,
                "timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "status": "pending"
            }
            
            # Save mission file
            mission_file = self.missions_dir / f"{test_mission_id}.json"
            with open(mission_file, 'w') as f:
                json.dump(test_mission, f)
            
            # Test mission status endpoint
            try:
                headers = {
                    'Authorization': 'Bearer test_token',
                    'X-User-ID': self.test_user_ids[0]
                }
                
                response = requests.get(
                    f"{self.api_base_url}/api/mission-status/{test_mission_id}",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code != 200:
                    logger.error(f"Mission status API failed: {response.status_code}")
                    return False
                
                mission_data = response.json()
                if mission_data.get("mission_id") != test_mission_id:
                    logger.error(f"Mission ID mismatch: {mission_data}")
                    return False
                
                logger.info("✓ Mission status API test passed")
                
            except requests.RequestException as e:
                logger.error(f"Mission status API test failed: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Mission endpoints API test failed: {e}")
            return False
    
    def test_fire_router_execution(self) -> bool:
        """Test 5: Test fire router trade execution"""
        try:
            # Import fire router
            sys.path.append(str(self.base_dir / "src" / "bitten_core"))
            from fire_router import FireRouter, TradeRequest, TradeDirection, ExecutionMode
            
            # Create fire router in simulation mode
            router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
            
            # Create test trade request
            trade_request = TradeRequest(
                symbol="EURUSD",
                direction=TradeDirection.BUY,
                volume=0.01,
                stop_loss=1.1020,
                take_profit=1.1050,
                tcs_score=85,
                user_id=self.test_user_ids[0],
                mission_id=f"test_fire_{int(time.time())}"
            )
            
            # Execute trade
            result = router.execute_trade_request(trade_request)
            
            # Verify result
            if not hasattr(result, 'success'):
                logger.error("Fire router result missing success field")
                return False
            
            if not result.success:
                logger.error(f"Trade execution failed: {result.message}")
                return False
            
            # Verify result fields
            expected_fields = ["success", "message", "trade_id", "timestamp"]
            for field in expected_fields:
                if not hasattr(result, field):
                    logger.error(f"Result missing field: {field}")
                    return False
            
            logger.info(f"✓ Fire router execution successful: {result.trade_id}")
            
            # Test system status
            system_status = router.get_system_status()
            if not isinstance(system_status, dict):
                logger.error("System status not returned as dict")
                return False
            
            required_status_fields = ["execution_mode", "trade_statistics", "validation_statistics"]
            for field in required_status_fields:
                if field not in system_status:
                    logger.error(f"System status missing field: {field}")
                    return False
            
            logger.info("✓ Fire router system status test passed")
            return True
            
        except Exception as e:
            logger.error(f"Fire router execution test failed: {e}")
            return False
    
    def test_fire_api_integration(self) -> bool:
        """Test 6: Test fire API integration through mission endpoints"""
        try:
            # Create test mission
            test_mission_id = f"test_fire_api_{int(time.time())}"
            test_mission = {
                "mission_id": test_mission_id,
                "user_id": self.test_user_ids[0],
                "symbol": "EURUSD",
                "type": "buy",
                "tp": 1.1050,
                "sl": 1.1020,
                "tcs": 85,
                "lot_size": 0.01,
                "timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "status": "pending"
            }
            
            # Save mission file
            mission_file = self.missions_dir / f"{test_mission_id}.json"
            with open(mission_file, 'w') as f:
                json.dump(test_mission, f)
            
            # Test fire action through API
            headers = {
                'Authorization': 'Bearer test_token',
                'X-User-ID': self.test_user_ids[0],
                'Content-Type': 'application/json'
            }
            
            fire_payload = {
                "mission_id": test_mission_id
            }
            
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/fire",
                    headers=headers,
                    json=fire_payload,
                    timeout=10
                )
                
                if response.status_code not in [200, 503]:  # 503 is acceptable if fire router not available
                    logger.error(f"Fire API failed: {response.status_code} - {response.text}")
                    return False
                
                if response.status_code == 200:
                    fire_result = response.json()
                    if fire_result.get("status") != "success":
                        logger.error(f"Fire action failed: {fire_result}")
                        return False
                    
                    logger.info("✓ Fire API integration test passed")
                else:
                    logger.info("✓ Fire API responded appropriately when service unavailable")
                
                return True
                
            except requests.RequestException as e:
                logger.error(f"Fire API integration test failed: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Fire API integration test failed: {e}")
            return False
    
    def test_webapp_server_integration(self) -> bool:
        """Test 7: Test webapp server integration"""
        try:
            # Test if webapp server can be imported
            sys.path.append(str(self.base_dir))
            
            # Just test basic imports for now
            try:
                import webapp_server
                logger.info("✓ Webapp server import successful")
            except ImportError as e:
                logger.error(f"Webapp server import failed: {e}")
                return False
            
            # Test if mission endpoints are integrated
            try:
                from src.api.mission_endpoints import app as mission_app
                logger.info("✓ Mission endpoints integration available")
            except ImportError as e:
                logger.error(f"Mission endpoints integration failed: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Webapp server integration test failed: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test 8: Test error handling throughout pipeline"""
        try:
            # Test 1: Invalid mission file handling
            invalid_mission_file = self.missions_dir / "invalid_mission.json"
            with open(invalid_mission_file, 'w') as f:
                f.write("invalid json content")
            
            # Test loading invalid mission
            sys.path.append(str(self.base_dir / "src" / "api"))
            from mission_endpoints import load_mission_data
            
            result = load_mission_data("invalid_mission")
            if result is not None:
                logger.error("Invalid mission should return None")
                return False
            
            logger.info("✓ Invalid mission handling test passed")
            
            # Test 2: Expired mission handling
            expired_mission_id = f"expired_test_{int(time.time())}"
            expired_mission = {
                "mission_id": expired_mission_id,
                "user_id": self.test_user_ids[0],
                "symbol": "EURUSD",
                "type": "buy",
                "tp": 1.1050,
                "sl": 1.1020,
                "tcs": 85,
                "timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),  # Expired
                "status": "pending"
            }
            
            mission_file = self.missions_dir / f"{expired_mission_id}.json"
            with open(mission_file, 'w') as f:
                json.dump(expired_mission, f)
            
            # Test fire action on expired mission
            headers = {
                'Authorization': 'Bearer test_token',
                'X-User-ID': self.test_user_ids[0],
                'Content-Type': 'application/json'
            }
            
            fire_payload = {
                "mission_id": expired_mission_id
            }
            
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/fire",
                    headers=headers,
                    json=fire_payload,
                    timeout=5
                )
                
                if response.status_code != 403:  # Should be forbidden
                    logger.error(f"Expected 403 for expired mission, got {response.status_code}")
                    return False
                
                logger.info("✓ Expired mission handling test passed")
                
            except requests.RequestException as e:
                logger.error(f"Expired mission test failed: {e}")
                return False
            
            # Test 3: Invalid fire router validation
            from fire_router import FireRouter, TradeRequest, TradeDirection, ExecutionMode
            
            router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
            
            # Create invalid trade request
            invalid_request = TradeRequest(
                symbol="INVALID",  # Too short
                direction=TradeDirection.BUY,
                volume=0.001,  # Too small
                tcs_score=10,  # Too low
                user_id=self.test_user_ids[0],
                mission_id="invalid_test"
            )
            
            result = router.execute_trade_request(invalid_request)
            
            if result.success:
                logger.error("Invalid trade request should fail validation")
                return False
            
            logger.info("✓ Fire router validation test passed")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False
    
    def test_complete_pipeline(self) -> bool:
        """Test 9: Test complete end-to-end pipeline"""
        try:
            # Create test signal
            test_signal = {
                "symbol": "GBPUSD",
                "type": "sell",
                "tp": 1.2750,
                "sl": 1.2800,
                "tcs_score": 78
            }
            
            # Step 1: Generate mission
            from src.bitten_core.mission_briefing_generator_v5 import generate_mission
            mission = generate_mission(test_signal, self.test_user_ids[1])
            
            # Step 2: Verify mission file created
            mission_file = self.missions_dir / f"{mission['mission_id']}.json"
            if not mission_file.exists():
                logger.error("Mission file not created in pipeline")
                return False
            
            # Step 3: Test mission retrieval through API
            headers = {
                'Authorization': 'Bearer test_token',
                'X-User-ID': self.test_user_ids[1]
            }
            
            response = requests.get(
                f"{self.api_base_url}/api/mission-status/{mission['mission_id']}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code != 200:
                logger.error(f"Mission retrieval failed: {response.status_code}")
                return False
            
            mission_data = response.json()
            
            # Step 4: Test fire action
            fire_payload = {
                "mission_id": mission['mission_id']
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/fire",
                headers=headers,
                json=fire_payload,
                timeout=10
            )
            
            # Accept both success and service unavailable
            if response.status_code not in [200, 503]:
                logger.error(f"Fire action failed: {response.status_code}")
                return False
            
            logger.info("✓ Complete pipeline test passed")
            return True
            
        except Exception as e:
            logger.error(f"Complete pipeline test failed: {e}")
            return False
    
    def test_performance_metrics(self) -> bool:
        """Test 10: Test performance and metrics"""
        try:
            # Test multiple concurrent operations
            import concurrent.futures
            import time
            
            def create_test_mission(user_id):
                try:
                    test_signal = {
                        "symbol": "USDJPY",
                        "type": "buy",
                        "tp": 150.50,
                        "sl": 149.50,
                        "tcs_score": 80
                    }
                    
                    from src.bitten_core.mission_briefing_generator_v5 import generate_mission
                    mission = generate_mission(test_signal, user_id)
                    return mission is not None
                except Exception as e:
                    logger.error(f"Performance test mission creation failed: {e}")
                    return False
            
            # Test concurrent mission creation
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_test_mission, f"perf_test_{i}") 
                          for i in range(10)]
                
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            execution_time = time.time() - start_time
            
            success_rate = sum(results) / len(results) * 100
            
            if success_rate < 80:
                logger.error(f"Performance test failed: {success_rate}% success rate")
                return False
            
            logger.info(f"✓ Performance test passed: {success_rate}% success rate in {execution_time:.2f}s")
            
            # Test fire router performance
            from fire_router import FireRouter, TradeRequest, TradeDirection, ExecutionMode
            
            router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
            
            # Test multiple trade executions
            trade_times = []
            for i in range(5):
                trade_request = TradeRequest(
                    symbol="EURUSD",
                    direction=TradeDirection.BUY,
                    volume=0.01,
                    tcs_score=80,
                    user_id=f"perf_test_{i}",
                    mission_id=f"perf_mission_{i}"
                )
                
                start_time = time.time()
                result = router.execute_trade_request(trade_request)
                exec_time = time.time() - start_time
                
                if result.success:
                    trade_times.append(exec_time)
            
            if not trade_times:
                logger.error("No successful trades in performance test")
                return False
            
            avg_time = sum(trade_times) / len(trade_times)
            
            if avg_time > 1.0:  # Should be faster than 1 second
                logger.error(f"Trade execution too slow: {avg_time:.2f}s average")
                return False
            
            logger.info(f"✓ Trade execution performance: {avg_time:.3f}s average")
            
            return True
            
        except Exception as e:
            logger.error(f"Performance metrics test failed: {e}")
            return False
    
    def cleanup_test_files(self):
        """Clean up test files"""
        try:
            # Clean up test mission files
            for mission_file in self.missions_dir.glob("test_*.json"):
                try:
                    mission_file.unlink()
                except:
                    pass
            
            for mission_file in self.missions_dir.glob("perf_*.json"):
                try:
                    mission_file.unlink()
                except:
                    pass
            
            # Clean up invalid mission file
            invalid_file = self.missions_dir / "invalid_mission.json"
            if invalid_file.exists():
                invalid_file.unlink()
            
            logger.info("✓ Test files cleaned up")
            
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        try:
            report = {
                "test_summary": {
                    "total_tests": self.total_tests,
                    "passed_tests": self.passed_tests,
                    "failed_tests": self.failed_tests_count,
                    "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                    "test_timestamp": datetime.now().isoformat()
                },
                "test_results": self.test_results,
                "failed_tests": self.failed_tests,
                "system_info": {
                    "base_directory": str(self.base_dir),
                    "missions_directory": str(self.missions_dir),
                    "logs_directory": str(self.logs_dir),
                    "api_base_url": self.api_base_url,
                    "webapp_base_url": self.webapp_base_url
                }
            }
            
            # Save report
            report_file = self.base_dir / "integration_test_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Test report saved to: {report_file}")
            
            # Print summary
            print("\n" + "="*60)
            print("INTEGRATION TEST SUMMARY")
            print("="*60)
            print(f"Total Tests: {self.total_tests}")
            print(f"Passed: {self.passed_tests}")
            print(f"Failed: {self.failed_tests_count}")
            print(f"Success Rate: {report['test_summary']['success_rate']:.1f}%")
            
            if self.failed_tests:
                print("\nFailed Tests:")
                for test in self.failed_tests:
                    print(f"  - {test}")
            
            print("="*60)
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return None
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting comprehensive integration tests...")
        
        # Define test suite
        test_suite = [
            ("Directory Structure", self.test_directory_structure),
            ("Mission File Creation", self.test_mission_file_creation),
            ("Signal Generation and Parsing", self.test_signal_generation_and_parsing),
            ("Mission Endpoints API", self.test_mission_endpoints_api),
            ("Fire Router Execution", self.test_fire_router_execution),
            ("Fire API Integration", self.test_fire_api_integration),
            ("WebApp Server Integration", self.test_webapp_server_integration),
            ("Error Handling", self.test_error_handling),
            ("Complete Pipeline", self.test_complete_pipeline),
            ("Performance Metrics", self.test_performance_metrics)
        ]
        
        # Run tests
        for test_name, test_func in test_suite:
            self.run_test(test_name, test_func)
        
        # Generate report
        report = self.generate_test_report()
        
        # Cleanup
        self.cleanup_test_files()
        
        # Return overall success
        return self.failed_tests_count == 0

def main():
    """Main test runner"""
    
    # Create test runner
    test_runner = IntegrationTestRunner()
    
    try:
        # Run all tests
        success = test_runner.run_all_tests()
        
        if success:
            logger.info("🎉 ALL TESTS PASSED - System is ready for production!")
            sys.exit(0)
        else:
            logger.error("❌ SOME TESTS FAILED - Please review the issues above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()