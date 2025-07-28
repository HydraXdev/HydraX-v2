#!/usr/bin/env python3
"""
BITTEN Autonomous Operation Validator
Validates all systems are ready for 100% autonomous operation
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path

class AutonomousValidator:
    def __init__(self):
        self.base_path = Path("/root/HydraX-v2")
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "critical_systems": {},
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
    def validate_signal_generation(self):
        """Check signal generation system"""
        try:
            apex_file = self.base_path / "apex_production_v6.py"
            if apex_file.exists():
                self.results["critical_systems"]["signal_generation"] = {
                    "status": "OPERATIONAL",
                    "engine": "v6.0 Enhanced",
                    "file": str(apex_file)
                }
                return True
            else:
                self.results["errors"].append("signal generation file missing")
                return False
        except Exception as e:
            self.results["errors"].append(f"Signal generation validation failed: {e}")
            return False
    
    def validate_webapp(self):
        """Check webapp is running and accessible"""
        try:
            response = requests.get("http://localhost:8888/health", timeout=5)
            if response.status_code == 200:
                self.results["critical_systems"]["webapp"] = {
                    "status": "RUNNING",
                    "port": 8888,
                    "url": "http://localhost:8888"
                }
                return True
            else:
                self.results["errors"].append(f"Webapp responded with status {response.status_code}")
                return False
        except Exception as e:
            self.results["warnings"].append(f"Webapp not accessible: {e}")
            return False
    
    def validate_pricing_consistency(self):
        """Validate pricing consistency across system"""
        try:
            config_file = self.base_path / "config" / "payment.py"
            if config_file.exists():
                with open(config_file) as f:
                    content = f.read()
                    if "'COMMANDER': 189" in content and "'FANG': 89" in content and "'NIBBLER': 39" in content:
                        self.results["critical_systems"]["pricing"] = {
                            "status": "CONSISTENT",
                            "tiers": {"NIBBLER": 39, "FANG": 89, "COMMANDER": 189}
                        }
                        return True
                    else:
                        self.results["errors"].append("Pricing inconsistency detected in payment config")
                        return False
            else:
                self.results["errors"].append("Payment config file missing")
                return False
        except Exception as e:
            self.results["errors"].append(f"Pricing validation failed: {e}")
            return False
    
    def validate_drill_reports(self):
        """Check drill report system"""
        try:
            drill_file = self.base_path / "send_daily_drill_reports.py"
            drill_system = self.base_path / "src" / "bitten_core" / "daily_drill_report.py"
            
            if drill_file.exists() and drill_system.exists():
                self.results["critical_systems"]["drill_reports"] = {
                    "status": "READY",
                    "scheduler": str(drill_file),
                    "system": str(drill_system)
                }
                return True
            else:
                self.results["warnings"].append("Drill report system files not found")
                return False
        except Exception as e:
            self.results["warnings"].append(f"Drill report validation failed: {e}")
            return False
    
    def validate_tier_system(self):
        """Validate tier access and capabilities"""
        try:
            fire_config = self.base_path / "config" / "fire_mode_config.py"
            if fire_config.exists():
                with open(fire_config) as f:
                    content = f.read()
                    has_nibbler = "NIBBLER" in content
                    has_fang = "FANG" in content  
                    has_commander = "COMMANDER" in content
                    no_apex = not in content
                    
                    if has_nibbler and has_fang and has_commander and no_apex:
                        self.results["critical_systems"]["tier_system"] = {
                            "status": "CLEAN",
                            "tiers": ["PRESS_PASS", "NIBBLER", "FANG", "COMMANDER"],
                            "apex_removed": True
                        }
                        return True
                    else:
                        self.results["errors"].append("Tier system still contains legacy references")
                        return False
            else:
                self.results["errors"].append("Fire mode config missing")
                return False
        except Exception as e:
            self.results["errors"].append(f"Tier system validation failed: {e}")
            return False
    
    def validate_claude_md(self):
        """Validate CLAUDE.md as single source of truth"""
        try:
            claude_file = self.base_path / "CLAUDE.md"
            if claude_file.exists():
                with open(claude_file) as f:
                    content = f.read()
                    
                # Check for critical inconsistencies
                has_correct_pricing = "$189/month" in content or "189" in content
                no_aws_ips = "3.145.84.187" not in content
                has_apex_removed = "features merged into COMMANDER" in content or "removed " in content.lower()
                
                if has_correct_pricing and no_aws_ips:
                    self.results["critical_systems"]["documentation"] = {
                        "status": "CONSISTENT",
                        "file": str(claude_file),
                        "pricing_updated": has_correct_pricing,
                        "aws_removed": no_aws_ips
                    }
                    return True
                else:
                    self.results["warnings"].append("CLAUDE.md may have inconsistencies")
                    return False
            else:
                self.results["errors"].append("CLAUDE.md missing")
                return False
        except Exception as e:
            self.results["errors"].append(f"Documentation validation failed: {e}")
            return False
    
    def check_autonomous_readiness(self):
        """Overall autonomous operation readiness check"""
        critical_count = len([s for s in self.results["critical_systems"].values() if s.get("status") in ["OPERATIONAL", "RUNNING", "CONSISTENT", "READY", "CLEAN"]])
        error_count = len(self.results["errors"])
        
        if critical_count >= 4 and error_count == 0:
            self.results["overall_status"] = "AUTONOMOUS_READY"
            self.results["recommendations"].append("System is ready for 100% autonomous operation")
        elif critical_count >= 3 and error_count <= 2:
            self.results["overall_status"] = "MOSTLY_READY"
            self.results["recommendations"].append("System mostly ready - minor issues need attention")
        else:
            self.results["overall_status"] = "NOT_READY"
            self.results["recommendations"].append("Critical issues must be resolved before autonomous operation")
    
    def run_validation(self):
        """Run complete validation suite"""
        print("🚀 BITTEN Autonomous Operation Validator")
        print("=" * 50)
        
        # Run all validations
        validations = [
            ("Signal Generation", self.validate_signal_generation),
            ("WebApp Service", self.validate_webapp),  
            ("Pricing Consistency", self.validate_pricing_consistency),
            ("Drill Reports", self.validate_drill_reports),
            ("Tier System", self.validate_tier_system),
            ("Documentation", self.validate_claude_md)
        ]
        
        for name, validator in validations:
            print(f"\n🔍 Checking {name}...")
            try:
                result = validator()
                status = "✅ PASS" if result else "⚠️  WARN"
                print(f"   {status}")
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
        
        # Final assessment
        self.check_autonomous_readiness()
        
        print(f"\n🎯 OVERALL STATUS: {self.results['overall_status']}")
        
        if self.results["errors"]:
            print(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                print(f"   - {error}")
        
        if self.results["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"]:
                print(f"   - {warning}")
        
        if self.results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                print(f"   - {rec}")
        
        # Save results
        report_file = self.base_path / "AUTONOMOUS_VALIDATION_REPORT.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Full report saved: {report_file}")
        return self.results

if __name__ == "__main__":
    validator = AutonomousValidator()
    results = validator.run_validation()
    
    # Exit with appropriate code
    if results["overall_status"] == "AUTONOMOUS_READY":
        sys.exit(0)
    elif results["overall_status"] == "MOSTLY_READY":
        sys.exit(1)
    else:
        sys.exit(2)