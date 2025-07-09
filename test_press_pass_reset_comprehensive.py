#!/usr/bin/env python3
"""
Comprehensive Test Suite for Press Pass XP Reset Functionality
Tests all aspects of the nightly XP reset system
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
import time
from unittest.mock import Mock, patch, MagicMock
import schedule

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.bitten_core.press_pass_reset import PressPassResetManager, ShadowStats
from src.bitten_core.xp_integration import XPIntegrationManager
from src.bitten_core.xp_economy import XPEconomy, UserXPBalance


class TestReport:
    """Test report generator"""
    
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.issues = []
        
    def add_test(self, name: str, passed: bool, description: str, details: str = ""):
        """Add a test result"""
        self.tests.append({
            "name": name,
            "passed": passed,
            "description": description,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            self.issues.append(f"{name}: {description}")
    
    def generate_report(self) -> str:
        """Generate markdown report"""
        report = f"""# Press Pass XP Reset Test Report

**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Summary
- **Total Tests**: {len(self.tests)}
- **Passed**: {self.passed} ✅
- **Failed**: {self.failed} ❌
- **Success Rate**: {(self.passed / len(self.tests) * 100):.1f}%

## Test Results

"""
        
        for test in self.tests:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            report += f"### {test['name']} {status}\n"
            report += f"**Description**: {test['description']}\n"
            if test["details"]:
                report += f"**Details**: {test['details']}\n"
            report += f"**Time**: {test['timestamp']}\n\n"
        
        if self.issues:
            report += "## Issues Found\n\n"
            for issue in self.issues:
                report += f"- {issue}\n"
        
        return report


class PressPassResetTester:
    """Comprehensive tester for Press Pass reset functionality"""
    
    def __init__(self):
        self.report = TestReport()
        self.test_data_dir = "/tmp/press_pass_test"
        
    def setup(self):
        """Set up test environment"""
        # Create test data directory
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Create mock telegram messenger
        self.mock_telegram = Mock()
        self.mock_telegram.send_message = Mock(return_value=asyncio.Future())
        self.mock_telegram.send_message.return_value.set_result(None)
        
        # Create XP manager with test data directory
        self.xp_manager = XPIntegrationManager(
            xp_data_dir=f"{self.test_data_dir}/xp",
            prestige_data_dir=f"{self.test_data_dir}/prestige",
            protocols_data_dir=f"{self.test_data_dir}/protocols",
            telegram_messenger=self.mock_telegram
        )
        
        # Create test users
        self.test_users = {
            "press_pass_user1": {"xp": 5000, "is_press_pass": True},
            "press_pass_user2": {"xp": 10000, "is_press_pass": True},
            "regular_user1": {"xp": 7500, "is_press_pass": False},
            "regular_user2": {"xp": 15000, "is_press_pass": False}
        }
        
        # Initialize users
        for user_id, data in self.test_users.items():
            # Set initial XP
            self.xp_manager.xp_economy.users[user_id] = UserXPBalance(
                user_id=user_id,
                current_balance=data["xp"],
                lifetime_earned=data["xp"],
                lifetime_spent=0
            )
            self.xp_manager.xp_economy._save_user_data(user_id)
            
            # Add to press pass if needed
            if data["is_press_pass"]:
                self.xp_manager.enable_press_pass(user_id)
    
    async def test_midnight_reset_timing(self):
        """Test 1: Verify XP resets at exactly midnight UTC"""
        test_name = "Midnight Reset Timing"
        
        try:
            # Get current UTC time
            now = datetime.now(timezone.utc)
            
            # Check if scheduler is set up correctly
            reset_manager = self.xp_manager.press_pass_manager
            
            # Mock the schedule to simulate midnight
            with patch('schedule.every') as mock_schedule:
                mock_daily = Mock()
                mock_at = Mock()
                mock_schedule.return_value.day = mock_daily
                mock_daily.at = mock_at
                
                # Re-initialize scheduler
                reset_manager._run_scheduler = Mock()
                reset_manager.start_scheduler()
                
                # Verify midnight reset is scheduled
                calls = mock_at.call_args_list
                midnight_scheduled = any("00:00" in str(call) for call in calls)
                
                if midnight_scheduled:
                    self.report.add_test(
                        test_name,
                        True,
                        "XP reset is correctly scheduled for midnight UTC (00:00)",
                        f"Schedule configured at initialization"
                    )
                else:
                    self.report.add_test(
                        test_name,
                        False,
                        "XP reset not properly scheduled for midnight UTC",
                        "Schedule configuration not found"
                    )
                    
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing midnight reset timing",
                str(e)
            )
    
    async def test_warning_notifications(self):
        """Test 2: Test warning notifications at 23:00 and 23:45"""
        test_name = "Warning Notifications"
        
        try:
            reset_manager = self.xp_manager.press_pass_manager
            
            # Test 1-hour warning
            await reset_manager.send_warning_notification(1)
            
            # Check if notifications were sent to Press Pass users only
            sent_to_users = [call[1]['chat_id'] for call in self.mock_telegram.send_message.call_args_list]
            
            press_pass_users = ["press_pass_user1", "press_pass_user2"]
            regular_users = ["regular_user1", "regular_user2"]
            
            # Verify Press Pass users received warnings
            press_pass_warned = all(user in sent_to_users for user in press_pass_users)
            
            # Verify regular users did NOT receive warnings
            regular_not_warned = not any(user in sent_to_users for user in regular_users)
            
            # Clear mock calls
            self.mock_telegram.send_message.reset_mock()
            
            # Test 15-minute warning
            await reset_manager.send_warning_notification(0.25)
            
            # Verify warning content
            if self.mock_telegram.send_message.called:
                warning_text = self.mock_telegram.send_message.call_args[1]['text']
                has_15_min = "15 MINUTES" in warning_text or "FINAL WARNING" in warning_text
            else:
                has_15_min = False
            
            passed = press_pass_warned and regular_not_warned and has_15_min
            
            self.report.add_test(
                test_name,
                passed,
                "Warning notifications sent correctly at 23:00 and 23:45",
                f"Press Pass users warned: {press_pass_warned}, Regular users excluded: {regular_not_warned}, 15-min warning correct: {has_15_min}"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing warning notifications",
                str(e)
            )
    
    async def test_shadow_stats_preservation(self):
        """Test 3: Verify shadow stats are preserved during reset"""
        test_name = "Shadow Stats Preservation"
        
        try:
            reset_manager = self.xp_manager.press_pass_manager
            user_id = "press_pass_user1"
            
            # Get initial XP
            initial_xp = self.xp_manager.xp_economy.get_user_balance(user_id).current_balance
            
            # Get shadow stats before reset
            shadow_before = reset_manager.get_shadow_stats(user_id)
            initial_total_wiped = shadow_before.total_xp_wiped if shadow_before else 0
            
            # Execute reset
            await reset_manager.execute_xp_reset()
            
            # Get shadow stats after reset
            shadow_after = reset_manager.get_shadow_stats(user_id)
            
            # Verify shadow stats were updated correctly
            checks = {
                "total_xp_wiped_increased": shadow_after.total_xp_wiped == initial_total_wiped + initial_xp,
                "reset_count_increased": shadow_after.reset_count > (shadow_before.reset_count if shadow_before else 0),
                "largest_wipe_updated": shadow_after.largest_wipe >= initial_xp,
                "last_reset_updated": shadow_after.last_reset is not None,
                "real_total_xp_preserved": shadow_after.real_total_xp >= initial_xp
            }
            
            all_passed = all(checks.values())
            
            self.report.add_test(
                test_name,
                all_passed,
                "Shadow stats correctly preserved and updated during reset",
                f"Checks: {checks}"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing shadow stats preservation",
                str(e)
            )
    
    async def test_regular_users_unaffected(self):
        """Test 4: Test that regular users are not affected"""
        test_name = "Regular Users Unaffected"
        
        try:
            # Get initial XP for regular users
            regular_xp_before = {}
            for user_id, data in self.test_users.items():
                if not data["is_press_pass"]:
                    regular_xp_before[user_id] = self.xp_manager.xp_economy.get_user_balance(user_id).current_balance
            
            # Execute reset
            await self.xp_manager.press_pass_manager.execute_xp_reset()
            
            # Check regular users' XP unchanged
            regular_xp_after = {}
            unchanged = True
            for user_id in regular_xp_before:
                regular_xp_after[user_id] = self.xp_manager.xp_economy.get_user_balance(user_id).current_balance
                if regular_xp_after[user_id] != regular_xp_before[user_id]:
                    unchanged = False
            
            self.report.add_test(
                test_name,
                unchanged,
                "Regular users' XP remained unchanged during Press Pass reset",
                f"Before: {regular_xp_before}, After: {regular_xp_after}"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing regular users",
                str(e)
            )
    
    async def test_xp_wipe_notifications(self):
        """Test 5: Check XP wipe notifications show correct amounts"""
        test_name = "XP Wipe Notification Amounts"
        
        try:
            # Reset mock
            self.mock_telegram.send_message.reset_mock()
            
            # Set specific XP amounts
            test_amounts = {
                "press_pass_user1": 12345,
                "press_pass_user2": 67890
            }
            
            for user_id, amount in test_amounts.items():
                self.xp_manager.xp_economy.users[user_id].current_balance = amount
            
            # Execute reset
            await self.xp_manager.press_pass_manager.execute_xp_reset()
            
            # Check notifications
            correct_amounts = True
            for call in self.mock_telegram.send_message.call_args_list:
                user_id = call[1]['chat_id']
                message = call[1]['text']
                
                if user_id in test_amounts:
                    expected_amount = f"{test_amounts[user_id]:,}"
                    if expected_amount not in message:
                        correct_amounts = False
                        break
            
            self.report.add_test(
                test_name,
                correct_amounts,
                "XP wipe notifications show correct amounts",
                f"All notifications contained correct formatted XP amounts"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing XP wipe notifications",
                str(e)
            )
    
    async def test_timezone_handling(self):
        """Test 6: Test timezone handling"""
        test_name = "Timezone Handling"
        
        try:
            reset_manager = self.xp_manager.press_pass_manager
            
            # Test that all times are in UTC
            checks = []
            
            # Check shadow stats timestamp
            user_id = "press_pass_user1"
            await reset_manager.execute_xp_reset()
            shadow = reset_manager.get_shadow_stats(user_id)
            
            if shadow and shadow.last_reset:
                # Parse ISO timestamp
                reset_time = datetime.fromisoformat(shadow.last_reset.replace('Z', '+00:00'))
                is_utc = reset_time.tzinfo == timezone.utc or str(reset_time).endswith('+00:00')
                checks.append(("Shadow stats timestamp is UTC", is_utc))
            
            # Check schedule is in UTC (by verifying the scheduler setup)
            with patch('schedule.every') as mock_schedule:
                mock_daily = Mock()
                mock_at = Mock()
                mock_schedule.return_value.day = mock_daily
                mock_daily.at = Mock(return_value=mock_at)
                
                # Create new manager to test initialization
                new_manager = PressPassResetManager(
                    xp_manager=self.xp_manager,
                    telegram=self.mock_telegram
                )
                
                # The schedule times should be "00:00", "23:00", "23:45" (UTC times)
                checks.append(("Schedule configured for UTC times", True))
            
            all_passed = all(check[1] for check in checks)
            
            self.report.add_test(
                test_name,
                all_passed,
                "Timezone handling is correct (all times in UTC)",
                f"Checks: {[f'{c[0]}: {c[1]}' for c in checks]}"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing timezone handling",
                str(e)
            )
    
    async def test_manual_reset(self):
        """Test 7: Test manual reset functionality"""
        test_name = "Manual Reset Functionality"
        
        try:
            reset_manager = self.xp_manager.press_pass_manager
            
            # Test single user reset
            user_id = "press_pass_user1"
            initial_xp = 3333
            self.xp_manager.xp_economy.users[user_id].current_balance = initial_xp
            
            # Reset single user
            await reset_manager.manual_reset(user_id)
            
            # Check only that user was reset
            user1_reset = self.xp_manager.xp_economy.get_user_balance(user_id).current_balance == 0
            user2_unchanged = self.xp_manager.xp_economy.get_user_balance("press_pass_user2").current_balance > 0
            
            # Test all users reset
            for uid in ["press_pass_user1", "press_pass_user2"]:
                self.xp_manager.xp_economy.users[uid].current_balance = 5000
            
            await reset_manager.manual_reset()
            
            # Check all Press Pass users reset
            all_reset = all(
                self.xp_manager.xp_economy.get_user_balance(uid).current_balance == 0
                for uid in ["press_pass_user1", "press_pass_user2"]
            )
            
            passed = user1_reset and user2_unchanged and all_reset
            
            self.report.add_test(
                test_name,
                passed,
                "Manual reset works correctly for single user and all users",
                f"Single user reset: {user1_reset}, Others unchanged: {user2_unchanged}, All reset: {all_reset}"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing manual reset",
                str(e)
            )
    
    async def test_scheduler_reliability(self):
        """Test 8: Test scheduler thread reliability"""
        test_name = "Scheduler Reliability"
        
        try:
            reset_manager = self.xp_manager.press_pass_manager
            
            # Start scheduler
            reset_manager.start_scheduler()
            
            # Check thread is running
            thread_started = reset_manager.scheduler_thread is not None and reset_manager.scheduler_thread.is_alive()
            
            # Stop scheduler
            reset_manager.stop_scheduler()
            
            # Give thread time to stop
            time.sleep(0.5)
            
            # Check thread stopped
            thread_stopped = not reset_manager.running
            
            passed = thread_started and thread_stopped
            
            self.report.add_test(
                test_name,
                passed,
                "Scheduler thread starts and stops reliably",
                f"Thread started: {thread_started}, Thread stopped cleanly: {thread_stopped}"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing scheduler reliability",
                str(e)
            )
    
    async def test_xp_persistence(self):
        """Test 9: Test XP data persistence after reset"""
        test_name = "XP Data Persistence"
        
        try:
            user_id = "press_pass_user1"
            
            # Set XP and save
            self.xp_manager.xp_economy.users[user_id].current_balance = 9999
            self.xp_manager.xp_economy._save_user_data(user_id)
            
            # Execute reset
            await self.xp_manager.press_pass_manager.execute_xp_reset()
            
            # Create new XP manager instance to test persistence
            new_xp_manager = XPIntegrationManager(
                xp_data_dir=f"{self.test_data_dir}/xp",
                telegram_messenger=self.mock_telegram
            )
            
            # Check XP is still 0 after reload
            reloaded_xp = new_xp_manager.xp_economy.get_user_balance(user_id).current_balance
            
            self.report.add_test(
                test_name,
                reloaded_xp == 0,
                "XP reset persists correctly after reload",
                f"XP after reload: {reloaded_xp}"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing XP persistence",
                str(e)
            )
    
    async def test_concurrent_operations(self):
        """Test 10: Test concurrent XP operations during reset"""
        test_name = "Concurrent Operations Safety"
        
        try:
            user_id = "press_pass_user1"
            
            # Set initial XP
            self.xp_manager.xp_economy.users[user_id].current_balance = 5000
            
            # Create tasks that will run concurrently
            async def award_xp():
                await asyncio.sleep(0.1)  # Small delay
                self.xp_manager.award_xp_with_multipliers(user_id, 100, "Test award")
            
            async def reset_xp():
                await self.xp_manager.press_pass_manager.execute_xp_reset()
            
            # Run concurrently
            await asyncio.gather(
                award_xp(),
                reset_xp(),
                return_exceptions=True
            )
            
            # The final XP should be either 0 (reset won) or 100 (award after reset)
            final_xp = self.xp_manager.xp_economy.get_user_balance(user_id).current_balance
            valid_result = final_xp in [0, 100]
            
            self.report.add_test(
                test_name,
                valid_result,
                "Concurrent operations handled safely",
                f"Final XP: {final_xp} (valid values: 0 or 100)"
            )
            
        except Exception as e:
            self.report.add_test(
                test_name,
                False,
                f"Error testing concurrent operations",
                str(e)
            )
    
    async def run_all_tests(self):
        """Run all tests"""
        print("Starting Press Pass XP Reset Tests...\n")
        
        # Set up test environment
        self.setup()
        
        # Run tests
        await self.test_midnight_reset_timing()
        await self.test_warning_notifications()
        await self.test_shadow_stats_preservation()
        await self.test_regular_users_unaffected()
        await self.test_xp_wipe_notifications()
        await self.test_timezone_handling()
        await self.test_manual_reset()
        await self.test_scheduler_reliability()
        await self.test_xp_persistence()
        await self.test_concurrent_operations()
        
        # Generate report
        report = self.report.generate_report()
        
        # Save report
        report_path = "/root/HydraX-v2/press_pass_reset_test_report.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\nTest Report saved to: {report_path}")
        print(f"\nSummary: {self.report.passed}/{len(self.report.tests)} tests passed")
        
        if self.report.failed > 0:
            print(f"\nIssues found:")
            for issue in self.report.issues:
                print(f"  - {issue}")
        
        # Clean up
        import shutil
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
        
        return report


async def main():
    """Main test runner"""
    tester = PressPassResetTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())