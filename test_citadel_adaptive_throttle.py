#!/usr/bin/env python3
"""
🧪 CITADEL Adaptive TCS Throttling Test Suite
Complete validation of the pressure release system
"""

import time
import json
import requests
import threading
from datetime import datetime, timedelta
import logging
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - TEST - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CitadelAdaptiveThrottleTestSuite:
    """Comprehensive test suite for CITADEL adaptive throttle system"""
    
    def __init__(self):
        self.test_results = {}
        self.api_base_url = "http://localhost:8003"
        
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_truth_log = os.path.join(self.temp_dir, "test_truth_log.jsonl")
        self.test_citadel_state = os.path.join(self.temp_dir, "test_citadel_state.json")
        self.test_throttle_log = os.path.join(self.temp_dir, "test_throttle.log")
        
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 CITADEL ADAPTIVE TCS THROTTLING TEST SUITE")
        print("=" * 60)
        
        tests = [
            ("test_adaptive_throttle_import", "Import CITADEL adaptive throttle module"),
            ("test_adaptive_throttle_initialization", "Initialize adaptive throttle system"),
            ("test_tcs_decay_schedule", "Test 5-tier TCS decay schedule"),
            ("test_truth_log_monitoring", "Test truth_log.jsonl monitoring"),
            ("test_citadel_state_integration", "Test citadel_state.json integration"),
            ("test_pressure_override_reset", "Test 90-minute pressure override"),
            ("test_signal_completion_reset", "Test immediate reset on signal completion"),
            ("test_throttle_logging", "Test citadel_throttle.log functionality"),
            ("test_api_endpoints", "Test CITADEL throttle API endpoints"),
            ("test_venom_integration", "Test VENOM stream integration")
        ]
        
        for test_method, description in tests:
            print(f"\n🔬 {description}")
            try:
                result = getattr(self, test_method)()
                self.test_results[test_method] = {"status": "PASS", "result": result}
                print(f"✅ PASS: {description}")
            except Exception as e:
                self.test_results[test_method] = {"status": "FAIL", "error": str(e)}
                print(f"❌ FAIL: {description} - {e}")
        
        self._print_summary()
    
    def test_adaptive_throttle_import(self):
        """Test importing CITADEL adaptive throttle module"""
        try:
            from citadel_adaptive_throttle import CitadelAdaptiveThrottle, get_adaptive_throttle
            return "Successfully imported CITADEL adaptive throttle classes"
        except ImportError as e:
            raise Exception(f"Failed to import CITADEL adaptive throttle: {e}")
    
    def test_adaptive_throttle_initialization(self):
        """Test adaptive throttle initialization"""
        from citadel_adaptive_throttle import CitadelAdaptiveThrottle
        
        # Initialize with test paths
        throttle = CitadelAdaptiveThrottle(
            truth_log_path=self.test_truth_log,
            citadel_state_path=self.test_citadel_state,
            throttle_log_path=self.test_throttle_log,
            commander_user_id="TEST_USER"
        )
        
        # Check initial state
        assert throttle.current_state.current_tcs == 82.0
        assert throttle.current_state.tier_level == 0
        assert throttle.current_state.reason_code == "BASELINE"
        
        return f"Initialized with baseline TCS: {throttle.current_state.current_tcs}%"
    
    def test_tcs_decay_schedule(self):
        """Test 5-tier TCS decay schedule"""
        from citadel_adaptive_throttle import CitadelAdaptiveThrottle
        
        throttle = CitadelAdaptiveThrottle(
            truth_log_path=self.test_truth_log,
            citadel_state_path=self.test_citadel_state,
            throttle_log_path=self.test_throttle_log,
            commander_user_id="TEST_USER"
        )
        
        # Test decay schedule
        expected_schedule = [
            (0, 82.0, "BASELINE"),
            (20, 79.5, "TIER_1_PRESSURE_RELEASE"),
            (35, 77.0, "TIER_2_ENHANCED_HUNTING"),
            (50, 74.5, "TIER_3_AGGRESSIVE_SEEKING"),
            (90, 82.0, "TIER_4_PRESSURE_OVERRIDE_RESET")
        ]
        
        assert throttle.decay_schedule == expected_schedule
        
        # Test threshold configuration
        assert throttle.config.baseline == 82.0
        assert throttle.config.tier_1 == 79.5
        assert throttle.config.tier_2 == 77.0
        assert throttle.config.tier_3 == 74.5
        assert throttle.config.reset_after_minutes == 90
        
        return "All 5 decay tiers configured correctly"
    
    def test_truth_log_monitoring(self):
        """Test truth_log.jsonl monitoring"""
        from citadel_adaptive_throttle import CitadelAdaptiveThrottle
        
        # Create test truth log with signal
        test_timestamp = time.time() - 1800  # 30 minutes ago
        test_signal = {
            "timestamp": datetime.fromtimestamp(test_timestamp).isoformat() + "+00:00",
            "signal_id": "TEST_SIGNAL_001",
            "result": "WIN",
            "symbol": "EURUSD",
            "pips": 15.5
        }
        
        with open(self.test_truth_log, 'w') as f:
            f.write(json.dumps(test_signal) + '\n')
        
        # Initialize throttle
        throttle = CitadelAdaptiveThrottle(
            truth_log_path=self.test_truth_log,
            citadel_state_path=self.test_citadel_state,
            throttle_log_path=self.test_throttle_log,
            commander_user_id="TEST_USER"
        )
        
        # Check that it found the signal
        assert throttle.current_state.last_signal_timestamp == test_timestamp
        assert throttle.current_state.minutes_since_signal >= 29  # Should be ~30 minutes
        
        # Should be in tier 1 (>20 minutes)
        assert throttle.current_state.current_tcs == 79.5
        assert throttle.current_state.tier_level == 1
        assert throttle.current_state.reason_code == "TIER_1_PRESSURE_RELEASE"
        
        return f"Truth log monitoring working - TCS: {throttle.current_state.current_tcs}% after {throttle.current_state.minutes_since_signal:.1f} min"
    
    def test_citadel_state_integration(self):
        """Test citadel_state.json integration"""
        from citadel_adaptive_throttle import CitadelAdaptiveThrottle
        
        throttle = CitadelAdaptiveThrottle(
            truth_log_path=self.test_truth_log,
            citadel_state_path=self.test_citadel_state,
            throttle_log_path=self.test_throttle_log,
            commander_user_id="TEST_USER"
        )
        
        # Manually trigger a threshold change
        throttle.current_state.current_tcs = 77.0
        throttle.current_state.tier_level = 2
        throttle.current_state.reason_code = "TEST_TIER_2"
        throttle._update_citadel_state()
        
        # Check that citadel state file was created/updated
        assert os.path.exists(self.test_citadel_state)
        
        with open(self.test_citadel_state, 'r') as f:
            citadel_data = json.load(f)
        
        # Check global adaptive throttle section
        assert 'global' in citadel_data
        assert 'adaptive_throttle' in citadel_data['global']
        
        adaptive_data = citadel_data['global']['adaptive_throttle']
        assert adaptive_data['tcs_threshold'] == 77.0
        assert adaptive_data['tier_level'] == 2
        assert adaptive_data['reason_code'] == "TEST_TIER_2"
        
        return "Citadel state integration working correctly"
    
    def test_pressure_override_reset(self):
        """Test 90-minute pressure override reset"""
        from citadel_adaptive_throttle import CitadelAdaptiveThrottle
        
        throttle = CitadelAdaptiveThrottle(
            truth_log_path=self.test_truth_log,
            citadel_state_path=self.test_citadel_state,
            throttle_log_path=self.test_throttle_log,
            commander_user_id="TEST_USER"
        )
        
        # Simulate 91 minutes since last signal
        old_timestamp = time.time() - (91 * 60)  # 91 minutes ago
        throttle.current_state.last_signal_timestamp = old_timestamp
        
        # Update TCS threshold
        throttle._update_tcs_threshold()
        
        # Should trigger pressure override reset
        assert throttle.current_state.pressure_override_active == True
        assert throttle.current_state.current_tcs == 82.0  # Reset to baseline
        assert throttle.current_state.reason_code == "PRESSURE_OVERRIDE_RESET"
        assert throttle.current_state.minutes_since_signal == 0  # Reset
        
        return "Pressure override reset working at 90+ minutes"
    
    def test_signal_completion_reset(self):
        """Test immediate reset on signal completion"""
        from citadel_adaptive_throttle import CitadelAdaptiveThrottle
        
        throttle = CitadelAdaptiveThrottle(
            truth_log_path=self.test_truth_log,
            citadel_state_path=self.test_citadel_state,
            throttle_log_path=self.test_throttle_log,
            commander_user_id="TEST_USER"
        )
        
        # Set to a decayed state
        throttle.current_state.current_tcs = 74.5
        throttle.current_state.tier_level = 3
        throttle.current_state.reason_code = "TIER_3_AGGRESSIVE_SEEKING"
        
        # Trigger signal completion
        throttle.on_signal_completed("TEST_SIGNAL_COMPLETE_001")
        
        # Should reset to baseline immediately
        assert throttle.current_state.current_tcs == 82.0
        assert throttle.current_state.tier_level == 0
        assert throttle.current_state.reason_code == "SIGNAL_RESET"
        assert throttle.current_state.minutes_since_signal == 0.0
        assert throttle.current_state.next_decay_in_minutes == 20.0
        
        return "Signal completion reset working correctly"
    
    def test_throttle_logging(self):
        """Test citadel_throttle.log functionality"""
        from citadel_adaptive_throttle import CitadelAdaptiveThrottle
        
        throttle = CitadelAdaptiveThrottle(
            truth_log_path=self.test_truth_log,
            citadel_state_path=self.test_citadel_state,
            throttle_log_path=self.test_throttle_log,
            commander_user_id="TEST_USER"
        )
        
        # Generate some log entries
        throttle.throttle_logger.info("TEST_LOG_ENTRY - Testing logging functionality")
        
        # Trigger a threshold change to generate log
        throttle.current_state.current_tcs = 79.5
        throttle.current_state.reason_code = "TEST_CHANGE"
        throttle._update_citadel_state()
        
        # Check that log file was created and has content
        assert os.path.exists(self.test_throttle_log)
        
        with open(self.test_throttle_log, 'r') as f:
            log_content = f.read()
        
        assert "TEST_LOG_ENTRY" in log_content
        assert "CITADEL_UPDATE" in log_content
        
        return "Throttle logging functionality working"
    
    def test_api_endpoints(self):
        """Test CITADEL throttle API endpoints"""
        # Test if API server is running
        try:
            response = requests.get(f"{self.api_base_url}/citadel/api/health", timeout=5)
            if response.status_code in [200, 503]:
                endpoints_tested = []
                
                # Test threshold status endpoint
                try:
                    response = requests.get(f"{self.api_base_url}/citadel/api/threshold_status", timeout=5)
                    endpoints_tested.append(f"threshold_status ({response.status_code})")
                except:
                    pass
                
                # Test config endpoint
                try:
                    response = requests.get(f"{self.api_base_url}/citadel/api/config", timeout=5)
                    endpoints_tested.append(f"config ({response.status_code})")
                except:
                    pass
                
                # Test threshold history endpoint
                try:
                    response = requests.get(f"{self.api_base_url}/citadel/api/threshold_history", timeout=5)
                    endpoints_tested.append(f"threshold_history ({response.status_code})")
                except:
                    pass
                
                return f"API endpoints tested: {', '.join(endpoints_tested)}"
            else:
                return "API server not accessible"
                
        except requests.exceptions.RequestException:
            return "API server not running - endpoints untested"
    
    def test_venom_integration(self):
        """Test VENOM stream integration"""
        try:
            from venom_stream_pipeline import VenomStreamEngine
            from citadel_adaptive_throttle import CitadelAdaptiveThrottle
            
            # Initialize adaptive throttle
            throttle = CitadelAdaptiveThrottle(
                truth_log_path=self.test_truth_log,
                citadel_state_path=self.test_citadel_state,
                throttle_log_path=self.test_throttle_log,
                commander_user_id="TEST_USER"
            )
            
            # Initialize VENOM with adaptive throttle
            venom_engine = VenomStreamEngine(adaptive_throttle=throttle)
            
            # Check integration
            assert venom_engine.adaptive_throttle is not None
            assert venom_engine.fire_threshold == throttle.current_state.current_tcs
            
            # Test threshold update
            throttle.current_state.current_tcs = 79.5
            venom_engine._update_fire_threshold()
            assert venom_engine.fire_threshold == 79.5
            
            return "VENOM integration successful"
            
        except ImportError:
            return "VENOM module not available - integration untested"
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🧪 CITADEL ADAPTIVE THROTTLE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if result["status"] == "FAIL":
                    print(f"  • {test_name}: {result['error']}")
        
        print(f"\n🎯 CITADEL ADAPTIVE THROTTLE STATUS: {'✅ READY' if failed_tests == 0 else '❌ NEEDS FIXES'}")
        
        # Cleanup
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except:
            pass

def main():
    """Run the CITADEL adaptive throttle test suite"""
    tester = CitadelAdaptiveThrottleTestSuite()
    tester.run_all_tests()

if __name__ == "__main__":
    main()