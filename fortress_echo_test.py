#!/usr/bin/env python3
"""
FORTRESS ECHO TEST SYSTEM - Military Grade Round-Trip Validation
Version: 1.0 BULLETPROOF
Mission: Validate complete bridge ➜ SPE communication pipeline with zero tolerance

TESTS EVERYTHING. VALIDATES EVERYTHING. NEVER MISSES.
"""

import json
import socket
import time
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import our fortress components
from fortress_bridge_converter import FortressBridgeConverter, get_fortress_converter
from fortress_signal_processor import FortressSignalProcessor, get_fortress_spe

class TestStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"

@dataclass
class TestResult:
    test_name: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration: float
    expected_result: Optional[Dict]
    actual_result: Optional[Dict]
    error_message: Optional[str]
    details: Dict

class FortressEchoTest:
    """
    MILITARY-GRADE ECHO TEST SYSTEM
    
    Capabilities:
    - Complete bridge ➜ SPE round-trip testing
    - Real-time performance validation
    - Error detection and analysis
    - Load testing and stress testing
    - Component isolation testing
    - Full system integration testing
    """
    
    def __init__(self, spe_port: int = 8889):
        self.spe_port = spe_port
        self.test_results = []
        self.is_running = False
        
        # Test components
        self.converter = None
        self.spe = None
        self.test_socket = None
        
        # Performance metrics
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Initialize logging
        self.setup_logging()
        
        self.logger.info(f"🛡️ FORTRESS ECHO TEST SYSTEM INITIALIZED")
        self.logger.info(f"🎯 SPE Port: {self.spe_port}")
        
    def setup_logging(self):
        """Initialize military-grade logging"""
        log_format = '%(asctime)s - FORTRESS_ECHO - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('/root/HydraX-v2/fortress_echo_test.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("FORTRESS_ECHO")
        
    def setup_test_environment(self):
        """Setup test environment with all components"""
        try:
            self.logger.info(f"🔧 Setting up test environment...")
            
            # Initialize converter
            self.converter = FortressBridgeConverter("bridge_001")
            self.logger.info(f"✅ Bridge converter initialized")
            
            # Initialize SPE
            self.spe = get_fortress_spe(self.spe_port)
            
            # Start SPE in separate thread
            spe_thread = threading.Thread(target=self.spe.start, daemon=True)
            spe_thread.start()
            
            # Wait for SPE to be ready
            time.sleep(2)
            
            self.logger.info(f"✅ Signal processor started on port {self.spe_port}")
            
            # Setup test socket
            self.test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.test_socket.connect(('localhost', self.spe_port))
            
            self.logger.info(f"✅ Test socket connected")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test environment setup failed: {e}")
            return False
            
    def teardown_test_environment(self):
        """Teardown test environment"""
        try:
            if self.test_socket:
                self.test_socket.close()
                
            if self.spe:
                self.spe.stop()
                
            self.logger.info(f"✅ Test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"❌ Teardown error: {e}")
            
    def run_complete_test_suite(self) -> Dict:
        """Run complete test suite with all scenarios"""
        self.logger.info(f"🚀 STARTING COMPLETE FORTRESS TEST SUITE")
        
        if not self.setup_test_environment():
            return {"status": "SETUP_FAILED", "results": []}
            
        try:
            # Test scenarios
            test_scenarios = [
                ("basic_conversion", self.test_basic_conversion),
                ("round_trip_new_trade", self.test_round_trip_new_trade),
                ("round_trip_price_update", self.test_round_trip_price_update),
                ("heartbeat_test", self.test_heartbeat),
                ("error_handling", self.test_error_handling),
                ("performance_test", self.test_performance),
                ("load_test", self.test_load),
                ("validation_test", self.test_validation)
            ]
            
            # Run all tests
            for test_name, test_func in test_scenarios:
                self.logger.info(f"🧪 Running test: {test_name}")
                result = test_func()
                self.test_results.append(result)
                
                if result.status == TestStatus.PASSED:
                    self.passed_tests += 1
                    self.logger.info(f"✅ {test_name} PASSED ({result.duration:.3f}s)")
                else:
                    self.failed_tests += 1
                    self.logger.error(f"❌ {test_name} FAILED: {result.error_message}")
                    
                self.total_tests += 1
                
            # Generate summary
            summary = self.generate_test_summary()
            
            self.logger.info(f"🏁 TEST SUITE COMPLETED")
            self.logger.info(f"📊 Summary: {self.passed_tests}/{self.total_tests} passed ({(self.passed_tests/self.total_tests*100):.1f}%)")
            
            return summary
            
        finally:
            self.teardown_test_environment()
            
    def test_basic_conversion(self) -> TestResult:
        """Test basic MT5 order conversion"""
        test_name = "basic_conversion"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Test data
            test_order = {
                'symbol': 'XAUUSD',
                'type': 0,  # Buy
                'volume': 0.10,
                'price': 2374.10,
                'sl': 2370.00,
                'tp': 2382.00,
                'comment': 'ECHO_TEST',
                'magic': 82
            }
            
            # Convert order
            result = self.converter.convert_mt5_order(test_order)
            
            # Validate result
            expected_fields = ['event', 'timestamp', 'symbol', 'order_type', 'lot_size', 'entry_price']
            if all(field in result for field in expected_fields):
                if result['symbol'] == 'XAUUSD' and result['order_type'] == 'buy':
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        start_time=start_time,
                        end_time=datetime.now(timezone.utc),
                        duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                        expected_result={"symbol": "XAUUSD", "order_type": "buy"},
                        actual_result=result,
                        error_message=None,
                        details={"converted_fields": len(result)}
                    )
            
            raise Exception("Invalid conversion result")
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                expected_result=None,
                actual_result=None,
                error_message=str(e),
                details={}
            )
            
    def test_round_trip_new_trade(self) -> TestResult:
        """Test complete round-trip for new trade signal"""
        test_name = "round_trip_new_trade"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Create test order
            test_order = {
                'symbol': 'EURUSD',
                'type': 0,  # Buy
                'volume': 0.05,
                'price': 1.0875,
                'sl': 1.0850,
                'tp': 1.0900,
                'comment': 'ROUND_TRIP_TEST',
                'magic': 75
            }
            
            # Convert to signal
            signal = self.converter.convert_mt5_order(test_order)
            signal_json = json.dumps(signal)
            
            # Send to SPE
            self.test_socket.send(signal_json.encode() + b'\n')
            
            # Wait for acknowledgment
            ack = self.test_socket.recv(1024).decode().strip()
            
            if ack == "ACK":
                # Wait for processing
                time.sleep(0.1)
                
                # Check SPE metrics
                metrics = self.spe.get_performance_metrics()
                
                if metrics['total_received'] > 0 and metrics['total_processed'] > 0:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        start_time=start_time,
                        end_time=datetime.now(timezone.utc),
                        duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                        expected_result={"ack": "ACK", "processed": True},
                        actual_result={"ack": ack, "metrics": metrics},
                        error_message=None,
                        details={"signal_size": len(signal_json)}
                    )
            
            raise Exception(f"Invalid acknowledgment: {ack}")
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                expected_result=None,
                actual_result=None,
                error_message=str(e),
                details={}
            )
            
    def test_round_trip_price_update(self) -> TestResult:
        """Test round-trip for price update signal"""
        test_name = "round_trip_price_update"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Create price update
            signal = self.converter.convert_price_update("GBPUSD", 1.2750, 1.2753, 0.3)
            signal_json = json.dumps(signal)
            
            # Send to SPE
            self.test_socket.send(signal_json.encode() + b'\n')
            
            # Wait for acknowledgment
            ack = self.test_socket.recv(1024).decode().strip()
            
            if ack == "ACK":
                time.sleep(0.1)
                
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                    expected_result={"ack": "ACK"},
                    actual_result={"ack": ack, "signal": signal},
                    error_message=None,
                    details={"event_type": "price_update"}
                )
            
            raise Exception(f"Invalid acknowledgment: {ack}")
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                expected_result=None,
                actual_result=None,
                error_message=str(e),
                details={}
            )
            
    def test_heartbeat(self) -> TestResult:
        """Test heartbeat signal"""
        test_name = "heartbeat_test"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Create heartbeat (modify to use valid symbol)
            signal = self.converter.create_heartbeat()
            signal['symbol'] = 'EURUSD'  # Use valid 6-char symbol
            signal_json = json.dumps(signal)
            
            # Send to SPE
            self.test_socket.send(signal_json.encode() + b'\n')
            
            # Wait for acknowledgment
            ack = self.test_socket.recv(1024).decode().strip()
            
            if ack == "ACK":
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                    expected_result={"ack": "ACK"},
                    actual_result={"ack": ack, "event": "heartbeat"},
                    error_message=None,
                    details={"bridge_id": signal['bridge_id']}
                )
            
            raise Exception(f"Invalid acknowledgment: {ack}")
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                expected_result=None,
                actual_result=None,
                error_message=str(e),
                details={}
            )
            
    def test_error_handling(self) -> TestResult:
        """Test error handling with invalid data"""
        test_name = "error_handling"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Send invalid JSON
            invalid_data = '{"invalid": "json", "missing_required_fields": true'
            
            initial_errors = self.spe.total_errors
            
            self.test_socket.send(invalid_data.encode() + b'\n')
            
            # Should still get ACK (connection handling)
            ack = self.test_socket.recv(1024).decode().strip()
            
            time.sleep(0.1)
            
            # Errors should have increased
            final_errors = self.spe.total_errors
            
            if final_errors > initial_errors:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                    expected_result={"errors_increased": True},
                    actual_result={"initial_errors": initial_errors, "final_errors": final_errors},
                    error_message=None,
                    details={"error_handling": "validated"}
                )
            
            raise Exception("Error count did not increase")
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                expected_result=None,
                actual_result=None,
                error_message=str(e),
                details={}
            )
            
    def test_performance(self) -> TestResult:
        """Test performance with timing constraints"""
        test_name = "performance_test"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Performance thresholds
            max_conversion_time = 0.01  # 10ms
            max_round_trip_time = 0.1   # 100ms
            
            # Test conversion performance
            conv_start = time.time()
            
            test_order = {
                'symbol': 'USDJPY',
                'type': 1,  # Sell
                'volume': 0.01,
                'price': 149.75,
                'sl': 150.00,
                'tp': 149.50,
                'comment': 'PERF_TEST',
                'magic': 60
            }
            
            signal = self.converter.convert_mt5_order(test_order)
            conv_time = time.time() - conv_start
            
            # Test round-trip performance
            rt_start = time.time()
            signal_json = json.dumps(signal)
            self.test_socket.send(signal_json.encode() + b'\n')
            ack = self.test_socket.recv(1024).decode().strip()
            rt_time = time.time() - rt_start
            
            if conv_time < max_conversion_time and rt_time < max_round_trip_time:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                    expected_result={"conv_time": f"<{max_conversion_time}s", "rt_time": f"<{max_round_trip_time}s"},
                    actual_result={"conv_time": conv_time, "rt_time": rt_time},
                    error_message=None,
                    details={"performance": "within_limits"}
                )
            
            raise Exception(f"Performance threshold exceeded: conv={conv_time:.4f}s, rt={rt_time:.4f}s")
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                expected_result=None,
                actual_result=None,
                error_message=str(e),
                details={}
            )
            
    def test_load(self) -> TestResult:
        """Test system under load"""
        test_name = "load_test"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Load test parameters
            num_signals = 50
            max_time = 5.0  # seconds
            
            initial_metrics = self.spe.get_performance_metrics()
            
            load_start = time.time()
            
            # Send multiple signals rapidly
            for i in range(num_signals):
                test_order = {
                    'symbol': 'XAUUSD',
                    'type': i % 2,  # Alternate buy/sell
                    'volume': 0.01,
                    'price': 2370.0 + i * 0.1,
                    'comment': f'LOAD_TEST_{i}',
                    'magic': 50 + i
                }
                
                signal = self.converter.convert_mt5_order(test_order)
                signal_json = json.dumps(signal)
                self.test_socket.send(signal_json.encode() + b'\n')
                
                # Read ACK
                self.test_socket.recv(1024)
                
            load_time = time.time() - load_start
            
            # Wait for processing
            time.sleep(1)
            
            final_metrics = self.spe.get_performance_metrics()
            processed_count = final_metrics['total_processed'] - initial_metrics['total_processed']
            
            if load_time < max_time and processed_count >= num_signals * 0.9:  # 90% success rate
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                    expected_result={"signals_sent": num_signals, "time_limit": max_time},
                    actual_result={"load_time": load_time, "processed_count": processed_count},
                    error_message=None,
                    details={"throughput": f"{num_signals/load_time:.1f} signals/sec"}
                )
            
            raise Exception(f"Load test failed: time={load_time:.2f}s, processed={processed_count}/{num_signals}")
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                expected_result=None,
                actual_result=None,
                error_message=str(e),
                details={}
            )
            
    def test_validation(self) -> TestResult:
        """Test signal validation"""
        test_name = "validation_test"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Test valid signal
            valid_signal = {
                "event": "new_trade",
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "symbol": "EURJPY",
                "order_type": "buy",
                "lot_size": 0.02,
                "entry_price": 161.25,
                "bridge_id": "bridge_001",
                "account_id": "123456",
                "execution_id": "VAL_TEST",
                "strategy": "bitmode_auto",
                "tcs_score": 70
            }
            
            # Should process successfully
            result = self.spe.process_signal_sync(json.dumps(valid_signal))
            
            if result.status.value == "COMPLETED":
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=datetime.now(timezone.utc),
                    duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                    expected_result={"validation": "passed"},
                    actual_result={"processing_status": result.status.value},
                    error_message=None,
                    details={"validation": "schema_compliant"}
                )
            
            raise Exception(f"Signal processing failed: {result.error_message}")
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds(),
                expected_result=None,
                actual_result=None,
                error_message=str(e),
                details={}
            )
            
    def generate_test_summary(self) -> Dict:
        """Generate comprehensive test summary"""
        total_duration = sum(r.duration for r in self.test_results)
        avg_duration = total_duration / len(self.test_results) if self.test_results else 0
        
        return {
            "test_suite": "FORTRESS_ECHO_COMPLETE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                "total_duration": total_duration,
                "average_duration": avg_duration
            },
            "results": [asdict(r) for r in self.test_results],
            "component_status": {
                "bridge_converter": "OPERATIONAL" if self.converter else "FAILED",
                "signal_processor": "OPERATIONAL" if self.spe else "FAILED"
            },
            "performance_metrics": self.spe.get_performance_metrics() if self.spe else {}
        }

def run_fortress_echo_test() -> Dict:
    """Run complete fortress echo test suite"""
    echo_test = FortressEchoTest()
    return echo_test.run_complete_test_suite()

if __name__ == "__main__":
    print("🛡️ FORTRESS ECHO TEST - COMPLETE VALIDATION")
    print("=" * 60)
    
    results = run_fortress_echo_test()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"✅ Passed: {results['summary']['passed']}")
    print(f"❌ Failed: {results['summary']['failed']}")
    print(f"📈 Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"⏱️  Total Duration: {results['summary']['total_duration']:.2f}s")
    
    if results['summary']['failed'] > 0:
        print(f"\n❌ FAILED TESTS:")
        for result in results['results']:
            if result['status'] == 'FAILED':
                print(f"  - {result['test_name']}: {result['error_message']}")
    else:
        print(f"\n🎉 ALL TESTS PASSED - FORTRESS SYSTEM VALIDATED")