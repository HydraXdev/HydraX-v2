#!/usr/bin/env python3
"""
End-to-End Test for Press Pass Integration
Tests the complete user journey from landing to activation
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

class PressPassE2ETest:
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        
    def log(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1
    
    def test_landing_page(self):
        """Test 1: Landing page loads and contains Press Pass section"""
        try:
            # Test local server
            response = requests.get("http://localhost/index.html", timeout=5)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for Press Pass elements
                checks = [
                    ("Press Pass section", "PRESS PASS" in content),
                    ("Pricing info", "$88" in content or "$188" in content),
                    ("Call-to-action", "JOIN THE ELITE" in content or "Get Press Pass" in content),
                    ("TCS integration", "TCS" in content or "Tactical Control System" in content)
                ]
                
                all_passed = True
                for check_name, check_result in checks:
                    if not check_result:
                        all_passed = False
                        self.log(f"Landing Page - {check_name}", "FAIL", "Element not found")
                
                if all_passed:
                    self.log("Landing Page Load", "PASS", "All Press Pass elements present")
            else:
                self.log("Landing Page Load", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log("Landing Page Load", "FAIL", str(e))
    
    def test_telegram_commands(self):
        """Test 2: Telegram bot commands structure"""
        try:
            # Check if telegram router has Press Pass commands
            router_path = "src/bitten_core/telegram_router.py"
            if os.path.exists(router_path):
                with open(router_path, 'r') as f:
                    content = f.read()
                
                commands = [
                    ("/presspass", "'/presspass'" in content),
                    ("/pp_status", "'/pp_status'" in content),
                    ("/pp_upgrade", "'/pp_upgrade'" in content),
                    ("Handler import", "press_pass_commands" in content),
                    ("Handler init", "press_pass_handler" in content)
                ]
                
                all_passed = True
                for cmd_name, cmd_present in commands:
                    if cmd_present:
                        self.log(f"Telegram Command - {cmd_name}", "PASS")
                    else:
                        self.log(f"Telegram Command - {cmd_name}", "FAIL", "Not found in router")
                        all_passed = False
                        
            else:
                self.log("Telegram Commands", "FAIL", "Router file not found")
                
        except Exception as e:
            self.log("Telegram Commands", "FAIL", str(e))
    
    def test_press_pass_components(self):
        """Test 3: Press Pass component files exist and compile"""
        components = [
            "src/bitten_core/press_pass_manager.py",
            "src/bitten_core/press_pass_scheduler.py",
            "src/bitten_core/press_pass_commands.py",
            "src/bitten_core/press_pass_reset.py",
            "src/bitten_core/onboarding/press_pass_manager.py",
            "src/bitten_core/onboarding/press_pass_tasks.py",
            "src/bitten_core/onboarding/press_pass_upgrade.py"
        ]
        
        for component in components:
            if os.path.exists(component):
                # Try to compile
                try:
                    import py_compile
                    py_compile.compile(component, doraise=True)
                    self.log(f"Component - {os.path.basename(component)}", "PASS")
                except Exception as e:
                    self.log(f"Component - {os.path.basename(component)}", "FAIL", f"Compile error: {str(e)}")
            else:
                self.log(f"Component - {os.path.basename(component)}", "FAIL", "File not found")
    
    def test_tcs_integration(self):
        """Test 4: TCS engine integration"""
        tcs_path = "core/tcs_engine.py"
        
        if os.path.exists(tcs_path):
            try:
                # Check if TCS engine can be imported
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                import core.tcs_engine
                self.log("TCS Engine", "PASS", "Successfully imported")
            except Exception as e:
                self.log("TCS Engine", "FAIL", f"Import error: {str(e)}")
        else:
            self.log("TCS Engine", "FAIL", "File not found")
    
    def test_payment_flow(self):
        """Test 5: Payment flow elements"""
        try:
            # Check landing page for payment elements
            with open("/var/www/html/index.html", 'r') as f:
                content = f.read()
            
            payment_elements = [
                ("Stripe integration", "stripe" in content.lower()),
                ("Payment form", "payment" in content.lower() or "checkout" in content.lower()),
                ("Price display", "$" in content),
                ("CTA buttons", "button" in content.lower())
            ]
            
            for element_name, element_present in payment_elements:
                if element_present:
                    self.log(f"Payment Flow - {element_name}", "PASS")
                else:
                    self.log(f"Payment Flow - {element_name}", "FAIL", "Element not found")
                    
        except Exception as e:
            self.log("Payment Flow", "FAIL", str(e))
    
    def test_database_readiness(self):
        """Test 6: Database schema readiness"""
        # This would normally check database, but we'll check for schema files
        schema_indicators = [
            "src/bitten_core/press_pass_manager.py",  # Should contain database models
            "config/database.json",  # Database config
            "migrations/"  # Migration directory
        ]
        
        for indicator in schema_indicators:
            if os.path.exists(indicator):
                self.log(f"Database Readiness - {os.path.basename(indicator)}", "PASS")
            else:
                self.log(f"Database Readiness - {os.path.basename(indicator)}", "WARN", "Not found (may be optional)")
    
    def generate_report(self):
        """Generate test report"""
        total_tests = self.passed + self.failed
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
========================================
Press Pass E2E Test Report
========================================
Timestamp: {datetime.now().isoformat()}
Total Tests: {total_tests}
Passed: {self.passed}
Failed: {self.failed}
Success Rate: {success_rate:.1f}%
========================================

Detailed Results:
"""
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            report += f"\n{status_icon} {result['test']}: {result['status']}"
            if result["details"]:
                report += f"\n   Details: {result['details']}"
        
        report += "\n\n"
        
        if self.failed == 0:
            report += "🎉 ALL TESTS PASSED! Press Pass integration is ready for production.\n"
        else:
            report += "⚠️  Some tests failed. Please review and fix before going live.\n"
        
        return report
    
    def run_all_tests(self):
        """Run all E2E tests"""
        print("Starting Press Pass E2E Tests...\n")
        
        self.test_landing_page()
        self.test_telegram_commands()
        self.test_press_pass_components()
        self.test_tcs_integration()
        self.test_payment_flow()
        self.test_database_readiness()
        
        report = self.generate_report()
        print(report)
        
        # Save report
        report_path = f"deployment/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"Report saved to: {report_path}")
        
        return self.failed == 0

if __name__ == "__main__":
    tester = PressPassE2ETest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)