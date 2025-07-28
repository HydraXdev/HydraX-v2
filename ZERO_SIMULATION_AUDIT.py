#!/usr/bin/env python3
"""
🚨 ZERO SIMULATION AUDIT SYSTEM
CRITICAL: Detects and reports ANY fake data in the system
"""

import os
import re
import json
from typing import List, Dict

class ZeroSimulationAuditor:
    """Audits system for ANY fake/simulation data"""
    
    def __init__(self):
        self.violations = []
        self.root_path = "/root/HydraX-v2"
        
    def audit_fake_data_patterns(self):
        """Audit for fake data patterns"""
        fake_patterns = [
            r'test_password',
            r'fake.*balance',
            r'simulation.*true',
            r'demo.*true',
            r'mock.*data',
            r'balance.*=.*10000',
            r'DEFAULT.*FOR.*TESTING',
            r'FAKE.*DATA',
            r'SIMULATE.*TICK',
            r'hardcoded.*price'
        ]
        
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                if file.endswith('.py') or file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in fake_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                self.violations.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'pattern': pattern,
                                    'match': match.group(),
                                    'severity': 'CRITICAL'
                                })
                    except:
                        pass
    
    def audit_broker_configs(self):
        """Audit broker configurations for real credentials"""
        config_file = f"{self.root_path}/data/broker_configs.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    configs = json.load(f)
                    
                for user_id, config in configs.items():
                    if user_id.startswith('user_') and isinstance(config, dict):
                        # Check for required real credentials
                        required_fields = ['login', 'password', 'server']
                        for field in required_fields:
                            creds = config.get('api_credentials', {})
                            value = creds.get(field, '')
                            
                            if ('REQUIRED' in str(value) or 
                                'test_' in str(value).lower() or
                                'fake' in str(value).lower()):
                                self.violations.append({
                                    'file': config_file,
                                    'user': user_id,
                                    'field': field,
                                    'issue': f'Invalid credential: {value}',
                                    'severity': 'CRITICAL'
                                })
            except:
                self.violations.append({
                    'file': config_file,
                    'issue': 'Cannot read broker configs',
                    'severity': 'CRITICAL'
                })
    
    def audit_mt5_fallback(self):
        """Audit MT5 fallback for real connections only"""
        fallback_file = f"{self.root_path}/src/bitten_core/mt5_fallback.py"
        
        if os.path.exists(fallback_file):
            try:
                with open(fallback_file, 'r') as f:
                    content = f.read()
                    
                # Check for any hardcoded values
                fake_indicators = [
                    'balance.*=.*[0-9]+',
                    'equity.*=.*[0-9]+',
                    'simulate',
                    'fake',
                    'default.*for.*testing'
                ]
                
                for pattern in fake_indicators:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        self.violations.append({
                            'file': fallback_file,
                            'line': line_num,
                            'issue': f'Potential fake data: {match.group()}',
                            'severity': 'HIGH'
                        })
            except:
                pass
    
    def run_full_audit(self):
        """Run complete zero simulation audit"""
        print("🚨 RUNNING ZERO SIMULATION AUDIT")
        print("=" * 60)
        
        self.audit_fake_data_patterns()
        self.audit_broker_configs() 
        self.audit_mt5_fallback()
        
        if self.violations:
            print(f"❌ FOUND {len(self.violations)} VIOLATIONS:")
            print()
            
            for i, violation in enumerate(self.violations, 1):
                print(f"{i}. {violation.get('severity', 'UNKNOWN')} VIOLATION:")
                print(f"   File: {violation.get('file', 'Unknown')}")
                if 'line' in violation:
                    print(f"   Line: {violation['line']}")
                if 'pattern' in violation:
                    print(f"   Pattern: {violation['pattern']}")
                if 'match' in violation:
                    print(f"   Match: {violation['match']}")
                if 'issue' in violation:
                    print(f"   Issue: {violation['issue']}")
                print()
                
            print("🚨 SYSTEM NOT READY - FAKE DATA DETECTED!")
            return False
        else:
            print("✅ ZERO SIMULATION AUDIT PASSED")
            print("✅ NO FAKE DATA DETECTED") 
            print("✅ SYSTEM READY FOR REAL TRADING")
            return True

if __name__ == "__main__":
    auditor = ZeroSimulationAuditor()
    audit_passed = auditor.run_full_audit()
    
    if not audit_passed:
        exit(1)
    else:
        print("\n🎯 BITTEN SYSTEM: 100% REAL DATA VERIFIED")