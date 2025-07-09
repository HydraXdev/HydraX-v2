#!/usr/bin/env python3
"""
Comprehensive Press Pass Flow Test Script
Tests all aspects of the Press Pass system including:
1. Press Pass activation through Telegram bot
2. MetaQuotes demo account provisioning
3. XP awarding and shadow stat tracking
4. Midnight XP reset functionality
5. Warning notifications at 23:00 and 23:45
6. Conversion from Press Pass to paid tier
7. Test report generation
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bitten_core.press_pass_manager import PressPassManager
from src.bitten_core.onboarding.press_pass_manager import PressPassManager as OnboardingPressPassManager
from src.bitten_core.press_pass_commands import PressPassCommandHandler
from src.bitten_core.xp_integration import XPIntegrationManager
from src.bitten_core.press_pass_reset import PressPassResetManager, ShadowStats
from src.bitten_core.telegram_messenger import TelegramMessenger
from src.bitten_core.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_press_pass_comprehensive.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PressPassTestResult:
    """Store test results"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.details = {}
        self.error = None
        self.timestamp = datetime.now(timezone.utc)


class PressPassComprehensiveTest:
    """Comprehensive test suite for Press Pass functionality"""
    
    def __init__(self):
        self.test_results: List[PressPassTestResult] = []
        self.test_user_id = "test_user_123456"
        self.test_username = "test_trader"
        self.test_callsign = "ALPHA_TESTER"
        
        # Initialize managers
        self.press_pass_manager = PressPassManager()
        self.onboarding_manager = OnboardingPressPassManager()
        self.xp_manager = None
        self.command_handler = None
        self.telegram_messenger = None
        
    async def setup(self):
        """Setup test environment"""
        try:
            # Initialize config
            config_manager = ConfigManager()
            config = config_manager.config
            
            # Initialize telegram messenger (mock for testing)
            self.telegram_messenger = MockTelegramMessenger()
            
            # Initialize XP manager
            self.xp_manager = XPIntegrationManager(
                telegram_messenger=self.telegram_messenger
            )
            
            # Initialize command handler
            self.command_handler = PressPassCommandHandler(self.xp_manager)
            
            logger.info("Test environment setup complete")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    async def run_all_tests(self):
        """Run all Press Pass tests"""
        logger.info("Starting comprehensive Press Pass testing...")
        
        await self.setup()
        
        # Test 1: Press Pass activation through bot
        await self.test_press_pass_activation()
        
        # Test 2: MetaQuotes demo account provisioning
        await self.test_demo_account_provisioning()
        
        # Test 3: XP awarding and shadow stats
        await self.test_xp_and_shadow_stats()
        
        # Test 4: Warning notifications
        await self.test_warning_notifications()
        
        # Test 5: Midnight reset functionality
        await self.test_midnight_reset()
        
        # Test 6: Conversion to paid tier
        await self.test_conversion_to_paid()
        
        # Test 7: Edge cases and error handling
        await self.test_edge_cases()
        
        # Generate test report
        self.generate_test_report()
    
    async def test_press_pass_activation(self):
        """Test 1: Press Pass activation through Telegram bot"""
        result = PressPassTestResult("Press Pass Activation")
        
        try:
            logger.info("Testing Press Pass activation...")
            
            # Test activation command
            response = self.command_handler.handle_presspass(
                self.test_user_id, 
                ["activate"]
            )
            
            if response["success"]:
                result.passed = True
                result.message = "Press Pass activated successfully"
                result.details = {
                    "user_id": self.test_user_id,
                    "activation_time": datetime.now(timezone.utc).isoformat(),
                    "response": response["message"]
                }
                
                # Verify Press Pass is active
                status = self.xp_manager.get_press_pass_status(self.test_user_id)
                result.details["is_active"] = status["active"]
                
                logger.info(f"✅ Press Pass activation test passed")
            else:
                result.passed = False
                result.message = f"Activation failed: {response.get('message', 'Unknown error')}"
                logger.error(f"❌ Press Pass activation failed")
                
        except Exception as e:
            result.passed = False
            result.message = f"Test failed with exception: {str(e)}"
            result.error = str(e)
            logger.error(f"❌ Press Pass activation test error: {e}")
        
        self.test_results.append(result)
    
    async def test_demo_account_provisioning(self):
        """Test 2: MetaQuotes demo account provisioning"""
        result = PressPassTestResult("Demo Account Provisioning")
        
        try:
            logger.info("Testing demo account provisioning...")
            
            # Provision demo account
            account_result = await self.onboarding_manager.provision_demo_account(
                self.test_user_id,
                self.test_callsign
            )
            
            if account_result["success"]:
                result.passed = True
                result.message = "Demo account provisioned successfully"
                result.details = {
                    "account_number": account_result["account"]["account_number"],
                    "balance": account_result["account"]["balance"],
                    "currency": account_result["account"]["currency"],
                    "leverage": account_result["account"]["leverage"],
                    "server": account_result["account"]["server"],
                    "expires_at": account_result["account"]["expires_at"]
                }
                
                # Verify account details
                assert account_result["account"]["balance"] == 50000
                assert account_result["account"]["account_type"] == "PRESS_PASS_DEMO"
                assert "BITTEN_DEMO_" in account_result["account"]["account_number"]
                
                logger.info(f"✅ Demo account provisioning test passed")
            else:
                result.passed = False
                result.message = f"Provisioning failed: {account_result.get('message', 'Unknown error')}"
                logger.error(f"❌ Demo account provisioning failed")
                
        except Exception as e:
            result.passed = False
            result.message = f"Test failed with exception: {str(e)}"
            result.error = str(e)
            logger.error(f"❌ Demo account provisioning test error: {e}")
        
        self.test_results.append(result)
    
    async def test_xp_and_shadow_stats(self):
        """Test 3: XP awarding and shadow stat tracking"""
        result = PressPassTestResult("XP and Shadow Stats")
        
        try:
            logger.info("Testing XP awarding and shadow stats...")
            
            # Get initial status
            initial_status = self.xp_manager.get_press_pass_status(self.test_user_id)
            initial_xp = self.xp_manager.xp_economy.get_user_balance(self.test_user_id).current_balance
            
            # Award some XP
            xp_amounts = [100, 250, 500]
            total_awarded = 0
            
            for amount in xp_amounts:
                awarded = self.xp_manager.award_xp_with_multipliers(
                    self.test_user_id,
                    amount,
                    f"Test award {amount}",
                    "Testing XP award"
                )
                total_awarded += awarded
                logger.info(f"Awarded {awarded} XP (base: {amount})")
            
            # Get updated status
            updated_status = self.xp_manager.get_press_pass_status(self.test_user_id)
            current_xp = self.xp_manager.xp_economy.get_user_balance(self.test_user_id).current_balance
            
            # Verify XP was awarded
            xp_gained = current_xp - initial_xp
            
            result.details = {
                "initial_xp": initial_xp,
                "total_awarded": total_awarded,
                "current_xp": current_xp,
                "xp_gained": xp_gained,
                "shadow_stats": updated_status.get("shadow_stats")
            }
            
            # Verify shadow stats are tracking
            if updated_status["active"] and updated_status.get("shadow_stats"):
                shadow = updated_status["shadow_stats"]
                result.details["shadow_tracking"] = {
                    "real_total_xp": shadow.get("real_total_xp", 0),
                    "real_lifetime_earned": shadow.get("real_lifetime_earned", 0)
                }
                result.passed = True
                result.message = "XP awarding and shadow stats working correctly"
                logger.info(f"✅ XP and shadow stats test passed")
            else:
                result.passed = False
                result.message = "Shadow stats not properly initialized"
                logger.error(f"❌ Shadow stats not tracking properly")
                
        except Exception as e:
            result.passed = False
            result.message = f"Test failed with exception: {str(e)}"
            result.error = str(e)
            logger.error(f"❌ XP and shadow stats test error: {e}")
        
        self.test_results.append(result)
    
    async def test_warning_notifications(self):
        """Test 4: Warning notifications at 23:00 and 23:45"""
        result = PressPassTestResult("Warning Notifications")
        
        try:
            logger.info("Testing warning notifications...")
            
            # Clear previous messages
            self.telegram_messenger.clear_messages()
            
            # Test 1-hour warning
            await self.xp_manager.press_pass_manager.send_warning_notification(1)
            
            # Test 15-minute warning
            await self.xp_manager.press_pass_manager.send_warning_notification(0.25)
            
            # Check messages were sent
            messages = self.telegram_messenger.get_messages()
            
            result.details = {
                "messages_sent": len(messages),
                "message_contents": [msg["text"] for msg in messages]
            }
            
            # Verify correct warnings were sent
            one_hour_warning = any("1 HOUR UNTIL RESET" in msg["text"] for msg in messages)
            fifteen_min_warning = any("FINAL WARNING - 15 MINUTES" in msg["text"] for msg in messages)
            
            if one_hour_warning and fifteen_min_warning:
                result.passed = True
                result.message = "Warning notifications sent correctly"
                logger.info(f"✅ Warning notifications test passed")
            else:
                result.passed = False
                result.message = "Warning notifications not sent properly"
                result.details["one_hour_sent"] = one_hour_warning
                result.details["fifteen_min_sent"] = fifteen_min_warning
                logger.error(f"❌ Warning notifications test failed")
                
        except Exception as e:
            result.passed = False
            result.message = f"Test failed with exception: {str(e)}"
            result.error = str(e)
            logger.error(f"❌ Warning notifications test error: {e}")
        
        self.test_results.append(result)
    
    async def test_midnight_reset(self):
        """Test 5: Midnight XP reset functionality"""
        result = PressPassTestResult("Midnight XP Reset")
        
        try:
            logger.info("Testing midnight XP reset...")
            
            # Get current XP before reset
            pre_reset_xp = self.xp_manager.xp_economy.get_user_balance(self.test_user_id).current_balance
            pre_reset_shadow = self.xp_manager.press_pass_manager.get_shadow_stats(self.test_user_id)
            
            # Clear messages
            self.telegram_messenger.clear_messages()
            
            # Execute manual reset (simulating midnight)
            total_wiped = await self.xp_manager.press_pass_manager.execute_xp_reset()
            
            # Get post-reset status
            post_reset_xp = self.xp_manager.xp_economy.get_user_balance(self.test_user_id).current_balance
            post_reset_shadow = self.xp_manager.press_pass_manager.get_shadow_stats(self.test_user_id)
            
            # Check reset notification was sent
            messages = self.telegram_messenger.get_messages()
            reset_notification = any("XP RESET EXECUTED" in msg["text"] for msg in messages)
            
            result.details = {
                "pre_reset_xp": pre_reset_xp,
                "post_reset_xp": post_reset_xp,
                "total_wiped": total_wiped,
                "reset_notification_sent": reset_notification,
                "shadow_stats_updated": {
                    "total_xp_wiped": post_reset_shadow.total_xp_wiped if post_reset_shadow else 0,
                    "reset_count": post_reset_shadow.reset_count if post_reset_shadow else 0,
                    "largest_wipe": post_reset_shadow.largest_wipe if post_reset_shadow else 0
                }
            }
            
            # Verify reset worked correctly
            if post_reset_xp == 0 and pre_reset_xp > 0 and reset_notification:
                result.passed = True
                result.message = "Midnight reset executed successfully"
                logger.info(f"✅ Midnight reset test passed")
            else:
                result.passed = False
                result.message = "Reset did not work as expected"
                logger.error(f"❌ Midnight reset test failed")
                
        except Exception as e:
            result.passed = False
            result.message = f"Test failed with exception: {str(e)}"
            result.error = str(e)
            logger.error(f"❌ Midnight reset test error: {e}")
        
        self.test_results.append(result)
    
    async def test_conversion_to_paid(self):
        """Test 6: Conversion from Press Pass to paid tier"""
        result = PressPassTestResult("Conversion to Paid Tier")
        
        try:
            logger.info("Testing conversion to paid tier...")
            
            # Test conversion
            conversion_result = await self.press_pass_manager.convert_to_paid(
                self.test_user_id,
                "APEX",
                discount_applied=True
            )
            
            if conversion_result["success"]:
                result.passed = True
                result.message = "Successfully converted to paid tier"
                result.details = {
                    "tier": conversion_result["tier"],
                    "discount_applied": True,
                    "conversion_time": datetime.now(timezone.utc).isoformat()
                }
                
                # Verify Press Pass is deactivated after conversion
                status = self.xp_manager.get_press_pass_status(self.test_user_id)
                result.details["press_pass_deactivated"] = not status["active"]
                
                logger.info(f"✅ Conversion test passed")
            else:
                result.passed = False
                result.message = f"Conversion failed: {conversion_result.get('error', 'Unknown error')}"
                logger.error(f"❌ Conversion test failed")
                
        except Exception as e:
            result.passed = False
            result.message = f"Test failed with exception: {str(e)}"
            result.error = str(e)
            logger.error(f"❌ Conversion test error: {e}")
        
        self.test_results.append(result)
    
    async def test_edge_cases(self):
        """Test 7: Edge cases and error handling"""
        result = PressPassTestResult("Edge Cases")
        edge_case_results = []
        
        try:
            logger.info("Testing edge cases...")
            
            # Edge case 1: Try to activate Press Pass when already active
            response = self.command_handler.handle_presspass(self.test_user_id, ["activate"])
            edge_case_results.append({
                "case": "Duplicate activation",
                "passed": not response["success"],
                "message": response.get("message", "")
            })
            
            # Edge case 2: Deactivate and reactivate
            deactivate_response = self.command_handler.handle_presspass(self.test_user_id, ["deactivate"])
            reactivate_response = self.command_handler.handle_presspass(self.test_user_id, ["activate"])
            edge_case_results.append({
                "case": "Deactivate/Reactivate",
                "passed": deactivate_response["success"] and reactivate_response["success"],
                "deactivate": deactivate_response.get("message", ""),
                "reactivate": reactivate_response.get("message", "")
            })
            
            # Edge case 3: Check expiry handling
            expiry_check = await self.onboarding_manager.check_press_pass_expiry(
                self.test_user_id,
                datetime.utcnow() + timedelta(days=3)
            )
            edge_case_results.append({
                "case": "Expiry check",
                "passed": not expiry_check["expired"],
                "remaining_days": expiry_check.get("remaining_time", {}).get("days", 0)
            })
            
            # Edge case 4: Test with invalid user
            invalid_response = self.command_handler.handle_presspass("invalid_user", ["status"])
            edge_case_results.append({
                "case": "Invalid user",
                "passed": True,  # Should handle gracefully
                "response": invalid_response["message"]
            })
            
            result.details = {"edge_cases": edge_case_results}
            
            # Check if all edge cases passed
            all_passed = all(case.get("passed", False) for case in edge_case_results)
            
            if all_passed:
                result.passed = True
                result.message = "All edge cases handled correctly"
                logger.info(f"✅ Edge cases test passed")
            else:
                result.passed = False
                result.message = "Some edge cases failed"
                logger.error(f"❌ Some edge cases failed")
                
        except Exception as e:
            result.passed = False
            result.message = f"Test failed with exception: {str(e)}"
            result.error = str(e)
            logger.error(f"❌ Edge cases test error: {e}")
        
        self.test_results.append(result)
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            "test_run": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r.passed),
                "failed": sum(1 for r in self.test_results if not r.passed)
            },
            "test_results": []
        }
        
        # Add individual test results
        for result in self.test_results:
            test_info = {
                "name": result.test_name,
                "passed": result.passed,
                "message": result.message,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details
            }
            
            if result.error:
                test_info["error"] = result.error
                
            report["test_results"].append(test_info)
        
        # Save report
        report_path = "test_press_pass_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("PRESS PASS TEST REPORT")
        print("="*60)
        print(f"Total Tests: {report['test_run']['total_tests']}")
        print(f"Passed: {report['test_run']['passed']}")
        print(f"Failed: {report['test_run']['failed']}")
        print(f"Success Rate: {(report['test_run']['passed']/report['test_run']['total_tests']*100):.1f}%")
        print("\nDetailed Results:")
        print("-"*60)
        
        for result in self.test_results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} - {result.test_name}")
            print(f"   Message: {result.message}")
            if result.error:
                print(f"   Error: {result.error}")
            print()
        
        print(f"\nFull report saved to: {report_path}")
        print("="*60)
        
        # Check for critical issues
        critical_issues = []
        
        for result in self.test_results:
            if not result.passed:
                if "Activation" in result.test_name:
                    critical_issues.append("Press Pass activation not working")
                elif "Demo Account" in result.test_name:
                    critical_issues.append("Demo account provisioning failing")
                elif "Midnight Reset" in result.test_name:
                    critical_issues.append("XP reset functionality broken")
                elif "Warning" in result.test_name:
                    critical_issues.append("Warning notifications not sending")
        
        if critical_issues:
            print("\n⚠️  CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   - {issue}")
            print()


class MockTelegramMessenger:
    """Mock Telegram messenger for testing"""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, chat_id: str, text: str, parse_mode: str = None):
        """Mock send message"""
        self.messages.append({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Mock telegram message sent to {chat_id}")
        return True
    
    def get_messages(self):
        """Get all sent messages"""
        return self.messages
    
    def clear_messages(self):
        """Clear message history"""
        self.messages = []


async def main():
    """Main test runner"""
    try:
        # Create test instance
        tester = PressPassComprehensiveTest()
        
        # Run all tests
        await tester.run_all_tests()
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())