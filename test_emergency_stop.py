#!/usr/bin/env python3
"""
BITTEN Emergency Stop System Test
Comprehensive testing of emergency stop functionality
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bitten_core.emergency_stop_controller import (
    EmergencyStopController, 
    EmergencyStopTrigger, 
    EmergencyStopLevel
)
from bitten_core.emergency_notification_system import EmergencyNotificationSystem

class EmergencyStopTester:
    """Test suite for emergency stop functionality"""
    
    def __init__(self):
        self.controller = EmergencyStopController(data_dir="test_data")
        self.test_results = []
        self.test_count = 0
        self.passed_count = 0
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.test_count += 1
        if passed:
            self.passed_count += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            'test_name': test_name,
            'status': status,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
    
    def test_emergency_stop_activation(self):
        """Test emergency stop activation"""
        try:
            # Test manual emergency stop
            result = self.controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.MANUAL,
                level=EmergencyStopLevel.SOFT,
                user_id=12345,
                reason="Test manual emergency stop"
            )
            
            success = result.get('success', False)
            is_active = self.controller.is_active()
            
            self.log_test(
                "Emergency Stop Activation", 
                success and is_active,
                f"Success: {success}, Active: {is_active}"
            )
            
            # Test status retrieval
            status = self.controller.get_emergency_status()
            has_current_event = status.get('current_event') is not None
            
            self.log_test(
                "Emergency Status Retrieval",
                has_current_event,
                f"Has current event: {has_current_event}"
            )
            
        except Exception as e:
            self.log_test(
                "Emergency Stop Activation", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def test_emergency_stop_types(self):
        """Test different emergency stop types"""
        try:
            # Clear any existing emergency
            if self.controller.is_active():
                self.controller.recover_from_emergency(force=True)
            
            # Test PANIC emergency
            result = self.controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.PANIC,
                level=EmergencyStopLevel.PANIC,
                user_id=12345,
                reason="Test panic mode"
            )
            
            panic_success = result.get('success', False)
            
            # Clear for next test
            self.controller.recover_from_emergency(force=True)
            
            # Test drawdown emergency
            result = self.controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.DRAWDOWN,
                level=EmergencyStopLevel.HARD,
                user_id=12345,
                reason="Test drawdown emergency",
                metadata={'drawdown_percent': -12.5}
            )
            
            drawdown_success = result.get('success', False)
            
            self.log_test(
                "Emergency Stop Types",
                panic_success and drawdown_success,
                f"Panic: {panic_success}, Drawdown: {drawdown_success}"
            )
            
        except Exception as e:
            self.log_test(
                "Emergency Stop Types",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_emergency_recovery(self):
        """Test emergency recovery"""
        try:
            # Ensure emergency is active
            if not self.controller.is_active():
                self.controller.trigger_emergency_stop(
                    trigger=EmergencyStopTrigger.MANUAL,
                    level=EmergencyStopLevel.SOFT,
                    user_id=12345,
                    reason="Setup for recovery test"
                )
            
            # Test recovery
            result = self.controller.recover_from_emergency(
                user_id=12345,
                force=True
            )
            
            recovery_success = result.get('success', False)
            is_still_active = self.controller.is_active()
            
            self.log_test(
                "Emergency Recovery",
                recovery_success and not is_still_active,
                f"Recovery success: {recovery_success}, Still active: {is_still_active}"
            )
            
        except Exception as e:
            self.log_test(
                "Emergency Recovery",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_state_persistence(self):
        """Test state persistence across controller instances"""
        try:
            # Create emergency with first controller
            self.controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.MANUAL,
                level=EmergencyStopLevel.SOFT,
                user_id=12345,
                reason="Test persistence"
            )
            
            first_active = self.controller.is_active()
            
            # Create new controller instance
            new_controller = EmergencyStopController(data_dir="test_data")
            second_active = new_controller.is_active()
            
            # Clean up
            new_controller.recover_from_emergency(force=True)
            
            self.log_test(
                "State Persistence",
                first_active and second_active,
                f"First active: {first_active}, Second active: {second_active}"
            )
            
        except Exception as e:
            self.log_test(
                "State Persistence",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_notification_system(self):
        """Test notification system"""
        try:
            # Test notification system initialization
            notification_system = EmergencyNotificationSystem()
            templates_loaded = len(notification_system.notification_templates) > 0
            
            # Test template retrieval
            manual_template = notification_system.notification_templates.get('manual_emergency_stop')
            has_manual_template = manual_template is not None
            
            # Test stats
            stats = notification_system.get_notification_stats()
            has_stats = 'active_notifications' in stats
            
            self.log_test(
                "Notification System",
                templates_loaded and has_manual_template and has_stats,
                f"Templates: {templates_loaded}, Manual template: {has_manual_template}, Stats: {has_stats}"
            )
            
        except Exception as e:
            self.log_test(
                "Notification System",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_fire_validator_integration(self):
        """Test fire validator integration"""
        try:
            from bitten_core.fire_mode_validator import FireModeValidator
            
            # Create validator
            validator = FireModeValidator()
            
            # Test with no emergency
            if self.controller.is_active():
                self.controller.recover_from_emergency(force=True)
            
            normal_result = validator._check_kill_switch()
            normal_valid = normal_result.valid
            
            # Test with emergency active
            self.controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.MANUAL,
                level=EmergencyStopLevel.SOFT,
                user_id=12345,
                reason="Test fire validator integration"
            )
            
            emergency_result = validator._check_kill_switch()
            emergency_blocked = not emergency_result.valid
            
            # Clean up
            self.controller.recover_from_emergency(force=True)
            
            self.log_test(
                "Fire Validator Integration",
                normal_valid and emergency_blocked,
                f"Normal valid: {normal_valid}, Emergency blocked: {emergency_blocked}"
            )
            
        except Exception as e:
            self.log_test(
                "Fire Validator Integration",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        try:
            # Test multiple emergency stops
            self.controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.MANUAL,
                level=EmergencyStopLevel.SOFT,
                user_id=12345,
                reason="First emergency"
            )
            
            # Try to trigger another emergency (should handle gracefully)
            result2 = self.controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.PANIC,
                level=EmergencyStopLevel.PANIC,
                user_id=12345,
                reason="Second emergency"
            )
            
            multiple_emergency_handled = result2.get('success', False)
            
            # Test recovery when not active
            self.controller.recover_from_emergency(force=True)
            
            result3 = self.controller.recover_from_emergency(user_id=12345)
            recovery_when_inactive = not result3.get('success', True)  # Should fail
            
            self.log_test(
                "Edge Cases",
                multiple_emergency_handled and recovery_when_inactive,
                f"Multiple emergency: {multiple_emergency_handled}, Recovery when inactive: {recovery_when_inactive}"
            )
            
        except Exception as e:
            self.log_test(
                "Edge Cases",
                False,
                f"Exception: {str(e)}"
            )
    
    def run_all_tests(self):
        """Run all emergency stop tests"""
        print("🚨 BITTEN Emergency Stop System Test Suite")
        print("=" * 50)
        
        # Ensure test data directory exists
        os.makedirs("test_data", exist_ok=True)
        
        # Run tests
        self.test_emergency_stop_activation()
        self.test_emergency_stop_types()
        self.test_emergency_recovery()
        self.test_state_persistence()
        self.test_notification_system()
        self.test_fire_validator_integration()
        self.test_edge_cases()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.passed_count}/{self.test_count} passed")
        
        if self.passed_count == self.test_count:
            print("✅ All tests passed! Emergency stop system is operational.")
        else:
            failed_count = self.test_count - self.passed_count
            print(f"❌ {failed_count} tests failed. Review emergency stop implementation.")
        
        # Save detailed results
        with open("test_data/emergency_stop_test_results.json", "w") as f:
            json.dump({
                'summary': {
                    'total_tests': self.test_count,
                    'passed_tests': self.passed_count,
                    'failed_tests': self.test_count - self.passed_count,
                    'success_rate': (self.passed_count / self.test_count) * 100 if self.test_count > 0 else 0,
                    'test_date': datetime.now().isoformat()
                },
                'detailed_results': self.test_results
            }, indent=2)
        
        print(f"\n📁 Detailed results saved to: test_data/emergency_stop_test_results.json")
        
        # Clean up test data
        try:
            if self.controller.is_active():
                self.controller.recover_from_emergency(force=True)
        except:
            pass
        
        return self.passed_count == self.test_count

if __name__ == "__main__":
    try:
        tester = EmergencyStopTester()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test suite failed with exception: {e}")
        traceback.print_exc()
        sys.exit(1)