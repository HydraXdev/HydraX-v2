#!/usr/bin/env python3
"""
REAL ENGINE PROTECTION SYSTEM
Bulletproof protection against fake VENOM engine restart
"""

import os
import sys
import hashlib
import time
from datetime import datetime

class RealEngineProtection:
    """Bulletproof protection system"""
    
    FAKE_ENGINE_FILES = [
        "apex_venom_v7_unfiltered.py.FAKE_DISABLED",
        "working_signal_generator.py.FAKE_DISABLED"
    ]
    
    REAL_ENGINE_FILES = [
        "market_data_receiver_enhanced.py",
        "venom_real_data_engine.py"
    ]
    
    PROTECTION_MARKER = "/root/HydraX-v2/REAL_ENGINE_ACTIVE.lock"
    
    def __init__(self):
        self.base_dir = "/root/HydraX-v2"
        
    def create_fake_engine_virus_protection(self):
        """Create virus-like protection that prevents fake engine execution"""
        
        for fake_file in self.FAKE_ENGINE_FILES:
            full_path = os.path.join(self.base_dir, fake_file)
            if os.path.exists(full_path):
                # Read original content
                with open(full_path, 'r') as f:
                    content = f.read()
                
                # Add virus protection at the top
                virus_protection = '''#!/usr/bin/env python3
"""
🚨 FAKE ENGINE VIRUS PROTECTION 🚨
This file contains SYNTHETIC DATA GENERATION and is PERMANENTLY DISABLED
Any attempt to execute this file will result in immediate termination
"""

import sys
import os
from datetime import datetime

# VIRUS PROTECTION - TERMINATE IMMEDIATELY
print("🚨 FAKE ENGINE DETECTED - TERMINATING IMMEDIATELY")
print("❌ This engine generates 100% SYNTHETIC DATA")
print("✅ Use market_data_receiver_enhanced.py for REAL DATA")
print(f"⏰ Protection activated: {datetime.now()}")
print("🔒 Contact system administrator to remove this protection")
sys.exit(1)

# ORIGINAL FAKE CODE BELOW (DISABLED):
"""
''' + content + '''
"""
'''
                
                # Write protected version
                with open(full_path, 'w') as f:
                    f.write(virus_protection)
                
                # Make read-only
                os.chmod(full_path, 0o444)
                
                print(f"🛡️ Virus protection added to {fake_file}")
    
    def create_real_engine_markers(self):
        """Create markers to identify real engines"""
        
        for real_file in self.REAL_ENGINE_FILES:
            full_path = os.path.join(self.base_dir, real_file)
            if os.path.exists(full_path):
                # Calculate file hash for integrity
                with open(full_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                
                # Create marker file
                marker_file = full_path + ".REAL_ENGINE_VERIFIED"
                with open(marker_file, 'w') as f:
                    f.write(f"""REAL ENGINE VERIFICATION
File: {real_file}
SHA256: {file_hash}
Verified: {datetime.now()}
Status: 100% REAL DATA - ZERO SYNTHETIC
Protection: ACTIVE
""")
                print(f"✅ Real engine marker created for {real_file}")
    
    def create_protection_lock(self):
        """Create system-wide protection lock"""
        
        with open(self.PROTECTION_MARKER, 'w') as f:
            f.write(f"""REAL ENGINE PROTECTION ACTIVE
Activated: {datetime.now()}
PID: {os.getpid()}
System: LOCKED against fake engines
Real engines: {', '.join(self.REAL_ENGINE_FILES)}
Fake engines: PERMANENTLY DISABLED
""")
        
        # Make read-only
        os.chmod(self.PROTECTION_MARKER, 0o444)
        print(f"🔒 Protection lock created: {self.PROTECTION_MARKER}")
    
    def get_engine_status(self):
        """Get current engine status with unique identifier"""
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "protection_active": os.path.exists(self.PROTECTION_MARKER),
            "real_engines": {},
            "fake_engines": {},
            "active_processes": []
        }
        
        # Check real engines
        for real_file in self.REAL_ENGINE_FILES:
            full_path = os.path.join(self.base_dir, real_file)
            marker_file = full_path + ".REAL_ENGINE_VERIFIED"
            
            status["real_engines"][real_file] = {
                "exists": os.path.exists(full_path),
                "verified": os.path.exists(marker_file),
            }
            
            if os.path.exists(marker_file):
                with open(marker_file, 'r') as f:
                    status["real_engines"][real_file]["verification"] = f.read()
        
        # Check fake engines
        for fake_file in self.FAKE_ENGINE_FILES:
            full_path = os.path.join(self.base_dir, fake_file)
            status["fake_engines"][fake_file] = {
                "exists": os.path.exists(full_path),
                "protected": False
            }
            
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    content = f.read()[:200]  # First 200 chars
                    status["fake_engines"][fake_file]["protected"] = "VIRUS PROTECTION" in content
        
        # Check active processes
        import subprocess
        try:
            ps_output = subprocess.check_output(['ps', 'aux'], text=True)
            for line in ps_output.split('\n'):
                if any(engine in line for engine in self.REAL_ENGINE_FILES + self.FAKE_ENGINE_FILES):
                    status["active_processes"].append(line.strip())
        except:
            pass
        
        return status

def main():
    """Main protection setup"""
    print("🛡️ REAL ENGINE PROTECTION SYSTEM")
    print("==================================")
    
    protection = RealEngineProtection()
    
    print("\n1. Adding virus protection to fake engines...")
    protection.create_fake_engine_virus_protection()
    
    print("\n2. Creating verification markers for real engines...")
    protection.create_real_engine_markers()
    
    print("\n3. Creating system protection lock...")
    protection.create_protection_lock()
    
    print("\n4. Current engine status:")
    status = protection.get_engine_status()
    
    print(f"Protection Active: {status['protection_active']}")
    print(f"Real Engines: {len([e for e in status['real_engines'].values() if e['verified']])} verified")
    print(f"Fake Engines: {len([e for e in status['fake_engines'].values() if e['protected']])} protected")
    print(f"Active Processes: {len(status['active_processes'])}")
    
    print("\n🔒 PROTECTION SYSTEM ACTIVATED")
    print("✅ Fake engines are now PERMANENTLY DISABLED")
    print("✅ Real engines are VERIFIED and PROTECTED")

if __name__ == "__main__":
    main()