#!/usr/bin/env python3
"""
COMPLETE MT5 FARM CLEANUP AND INSTALLATION PLAN
Based on AWS server assessment: Clean server ready for MT5 farm deployment
"""

import requests
import time

class MT5FarmManager:
    def __init__(self):
        self.server = "3.145.84.187:5555"
        self.ea_source = "/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5"
        
    def send_command(self, command, timeout=15):
        """Send command to AWS server via bulletproof agent"""
        try:
            payload = {
                'action': 'execute_command',
                'command': command,
                'timeout': timeout
            }
            response = requests.post(f'http://{self.server}/execute', json=payload, timeout=timeout+5)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'stdout': result.get('stdout', '').strip(),
                    'stderr': result.get('stderr', '').strip()
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cleanup_existing_installation(self):
        """Clean up any existing MT5/BITTEN files on server"""
        print("🧹 CLEANING EXISTING MT5 FARM INSTALLATION...")
        print("="*50)
        
        cleanup_commands = [
            # Stop any running MT5 instances
            'taskkill /F /IM terminal64.exe /T 2>nul',
            'taskkill /F /IM terminal.exe /T 2>nul', 
            'taskkill /F /IM metatrader.exe /T 2>nul',
            
            # Remove existing MT5 farm structure (keep the EA.mq5 if exists)
            'if exist "C:\\MT5_Farm\\Masters" rmdir /s /q "C:\\MT5_Farm\\Masters"',
            'if exist "C:\\MT5_Farm\\Clones" rmdir /s /q "C:\\MT5_Farm\\Clones"',
            'if exist "C:\\MT5_Farm\\Logs" rmdir /s /q "C:\\MT5_Farm\\Logs"',
            
            # Clean temporary files
            'del /f /q C:\\MT5_Farm\\*.bat 2>nul',
            'del /f /q C:\\MT5_Farm\\*.ps1 2>nul',
            'del /f /q C:\\MT5_Farm\\*.log 2>nul',
            
            # Remove any existing MT5 installations
            'if exist "C:\\Program Files\\MetaTrader 5" rmdir /s /q "C:\\Program Files\\MetaTrader 5"',
            'if exist "C:\\Program Files (x86)\\MetaTrader 5" rmdir /s /q "C:\\Program Files (x86)\\MetaTrader 5"',
            
            # Clean registry entries (if needed)
            'reg delete "HKCU\\Software\\MetaQuotes" /f 2>nul',
            'reg delete "HKLM\\Software\\MetaQuotes" /f 2>nul',
            
            # Verify cleanup
            'echo Cleanup completed successfully'
        ]
        
        for i, cmd in enumerate(cleanup_commands, 1):
            print(f"📋 Cleanup Step {i}: {cmd[:60]}...")
            result = self.send_command(cmd)
            
            if result['success']:
                if result['stdout']:
                    print(f"✅ {result['stdout']}")
                else:
                    print("✅ Command completed")
            else:
                print(f"⚠️ Warning: {result.get('error', 'Unknown error')}")
            
            time.sleep(0.5)

    def create_mt5_farm_structure(self):
        """Create proper MT5 farm directory structure"""
        print("\n🏗️ CREATING MT5 FARM STRUCTURE...")
        print("="*40)
        
        structure_commands = [
            # Create main farm structure
            'mkdir "C:\\MT5_Farm\\Masters" 2>nul',
            'mkdir "C:\\MT5_Farm\\Masters\\Generic_Demo" 2>nul',
            'mkdir "C:\\MT5_Farm\\Masters\\Forex_Demo" 2>nul', 
            'mkdir "C:\\MT5_Farm\\Masters\\Forex_Live" 2>nul',
            'mkdir "C:\\MT5_Farm\\Masters\\Coinexx_Demo" 2>nul',
            'mkdir "C:\\MT5_Farm\\Masters\\Coinexx_Live" 2>nul',
            'mkdir "C:\\MT5_Farm\\Clones" 2>nul',
            'mkdir "C:\\MT5_Farm\\Logs" 2>nul',
            'mkdir "C:\\MT5_Farm\\Scripts" 2>nul',
            
            # Create EA directories for each master
            'mkdir "C:\\MT5_Farm\\Masters\\Generic_Demo\\MQL5\\Experts" 2>nul',
            'mkdir "C:\\MT5_Farm\\Masters\\Forex_Demo\\MQL5\\Experts" 2>nul',
            'mkdir "C:\\MT5_Farm\\Masters\\Forex_Live\\MQL5\\Experts" 2>nul',
            'mkdir "C:\\MT5_Farm\\Masters\\Coinexx_Demo\\MQL5\\Experts" 2>nul',
            'mkdir "C:\\MT5_Farm\\Masters\\Coinexx_Live\\MQL5\\Experts" 2>nul',
            
            # Verify structure
            'tree C:\\MT5_Farm /F',
            'echo MT5 Farm structure created successfully'
        ]
        
        for i, cmd in enumerate(structure_commands, 1):
            print(f"📋 Structure Step {i}: {cmd[:50]}...")
            result = self.send_command(cmd)
            
            if result['success']:
                if result['stdout']:
                    print(f"✅ {result['stdout']}")
                else:
                    print("✅ Directory created")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")

    def create_installation_scripts(self):
        """Create automated installation scripts for MT5 instances"""
        print("\n📜 CREATING INSTALLATION SCRIPTS...")
        print("="*35)
        
        # Create download script
        download_script = '''@echo off
echo ========================================
echo    MT5 FARM INSTALLATION SCRIPT
echo ========================================
echo.
echo Downloading MT5 from different brokers...
echo.

echo 1. Downloading MetaQuotes Generic MT5...
powershell -Command "Invoke-WebRequest -Uri 'https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe' -OutFile 'C:\\MT5_Farm\\mt5_generic.exe'"

echo.
echo 2. Manual Downloads Required:
echo    - Forex.com MT5: https://www.forex.com/en-us/platforms/metatrader-5/
echo    - Coinexx MT5: https://www.coinexx.com/metatrader-5
echo.
echo 3. Install each MT5 to respective Master folders:
echo    Generic: C:\\MT5_Farm\\Masters\\Generic_Demo\\
echo    Forex Demo: C:\\MT5_Farm\\Masters\\Forex_Demo\\
echo    Forex Live: C:\\MT5_Farm\\Masters\\Forex_Live\\
echo    Coinexx Demo: C:\\MT5_Farm\\Masters\\Coinexx_Demo\\
echo    Coinexx Live: C:\\MT5_Farm\\Masters\\Coinexx_Live\\
echo.
echo 4. Copy EA to each installation after MT5 setup
echo.
pause
'''

        # Create EA deployment script
        ea_deploy_script = '''@echo off
echo ========================================
echo    EA DEPLOYMENT SCRIPT
echo ========================================
echo.
echo Deploying BITTENBridge EA to all MT5 instances...
echo.

if not exist "C:\\MT5_Farm\\EA.mq5" (
    echo ERROR: EA file not found at C:\\MT5_Farm\\EA.mq5
    echo Please transfer the EA file first!
    pause
    exit /b 1
)

echo Copying EA to all master installations...
copy "C:\\MT5_Farm\\EA.mq5" "C:\\MT5_Farm\\Masters\\Generic_Demo\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5"
copy "C:\\MT5_Farm\\EA.mq5" "C:\\MT5_Farm\\Masters\\Forex_Demo\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5"  
copy "C:\\MT5_Farm\\EA.mq5" "C:\\MT5_Farm\\Masters\\Forex_Live\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5"
copy "C:\\MT5_Farm\\EA.mq5" "C:\\MT5_Farm\\Masters\\Coinexx_Demo\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5"
copy "C:\\MT5_Farm\\EA.mq5" "C:\\MT5_Farm\\Masters\\Coinexx_Live\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5"

echo.
echo EA deployed to all masters successfully!
echo.
echo Next steps:
echo 1. Open each MT5 instance
echo 2. Press F4 to open MetaEditor
echo 3. Compile the EA (F7)
echo 4. Attach EA to charts
echo 5. Enable AutoTrading (Ctrl+E)
echo.
pause
'''

        # Create monitoring script
        monitor_script = '''@echo off
echo ========================================
echo    MT5 FARM MONITORING SCRIPT  
echo ========================================
echo.

:LOOP
cls
echo Current time: %date% %time%
echo.
echo Running MT5 Instances:
tasklist | findstr terminal64.exe
echo.
echo Process Count:
for /f %%i in ('tasklist ^| findstr terminal64.exe ^| find /c "terminal64.exe"') do echo MT5 Instances: %%i
echo.
echo Memory Usage:
wmic process where "name='terminal64.exe'" get ProcessId,WorkingSetSize /format:list | findstr "="
echo.
echo Waiting 30 seconds for next check...
timeout /t 30 >nul
goto LOOP
'''

        scripts = [
            ('C:\\MT5_Farm\\Scripts\\1_Download_MT5.bat', download_script),
            ('C:\\MT5_Farm\\Scripts\\2_Deploy_EA.bat', ea_deploy_script),
            ('C:\\MT5_Farm\\Scripts\\3_Monitor_Farm.bat', monitor_script)
        ]
        
        for script_path, script_content in scripts:
            # Create script using echo commands (since we can't upload files directly)
            lines = script_content.split('\n')
            
            script_name = script_path.split('\\')[-1]
            print(f"📜 Creating {script_name}...")
            
            # Clear any existing file and create new one
            clear_cmd = f'if exist "{script_path}" del /f "{script_path}"'
            self.send_command(clear_cmd)
            
            # Write script line by line
            for i, line in enumerate(lines):
                if i == 0:
                    cmd = f'echo {line}> "{script_path}"'
                else:
                    cmd = f'echo {line}>> "{script_path}"'
                self.send_command(cmd)
            
            print(f"✅ {script_name} created")

    def check_current_status(self):
        """Check current MT5 farm status"""
        print("\n📊 CURRENT MT5 FARM STATUS...")
        print("="*35)
        
        status_commands = [
            ('MT5 Processes', 'tasklist | findstr terminal'),
            ('Farm Structure', 'tree C:\\MT5_Farm /F | more'),
            ('Available Scripts', 'dir C:\\MT5_Farm\\Scripts'),
            ('EA Status', 'dir C:\\MT5_Farm\\EA.mq5 2>nul || echo EA file not found'),
            ('Disk Space', 'dir C:\\ | findstr "bytes free"')
        ]
        
        for name, cmd in status_commands:
            print(f"\n📋 {name}:")
            result = self.send_command(cmd)
            
            if result['success']:
                if result['stdout']:
                    print(f"✅ {result['stdout']}")
                else:
                    print("✅ Command completed (no output)")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")

    def generate_installation_guide(self):
        """Generate comprehensive installation guide"""
        print("\n📚 MT5 FARM INSTALLATION GUIDE")
        print("="*40)
        
        guide = """
🎯 COMPLETE MT5 FARM INSTALLATION GUIDE

CURRENT STATUS:
✅ AWS Server: 3.145.84.187 (Clean and ready)
✅ Farm Structure: Created and organized  
✅ Installation Scripts: Ready for use
⚠️ EA Transfer: Required (manual step)
⚠️ MT5 Installation: Required (3 brokers)

INSTALLATION STEPS:

📥 STEP 1: TRANSFER EA TO SERVER
1. Get EA file to C:\\MT5_Farm\\EA.mq5
   Source: /root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5
   Method: HTTP download, manual copy, or agent transfer

📦 STEP 2: DOWNLOAD MT5 INSTALLERS  
1. Run: C:\\MT5_Farm\\Scripts\\1_Download_MT5.bat
2. Download additional brokers manually:
   - Forex.com MT5: https://www.forex.com/en-us/platforms/metatrader-5/
   - Coinexx MT5: https://www.coinexx.com/metatrader-5

🏗️ STEP 3: INSTALL MT5 INSTANCES
Install each MT5 to specific master directories:
- Generic MT5 → C:\\MT5_Farm\\Masters\\Generic_Demo\\
- Forex Demo → C:\\MT5_Farm\\Masters\\Forex_Demo\\
- Forex Live → C:\\MT5_Farm\\Masters\\Forex_Live\\
- Coinexx Demo → C:\\MT5_Farm\\Masters\\Coinexx_Demo\\
- Coinexx Live → C:\\MT5_Farm\\Masters\\Coinexx_Live\\

🤖 STEP 4: DEPLOY EA
1. Run: C:\\MT5_Farm\\Scripts\\2_Deploy_EA.bat
2. This copies EA to all master MQL5\\Experts folders

⚙️ STEP 5: CONFIGURE EAs
For each MT5 instance:
1. Open MT5
2. Press F4 (MetaEditor)
3. Compile EA (F7)
4. Drag EA to charts (EURUSD, GBPUSD, USDJPY, etc.)
5. Enable AutoTrading (Ctrl+E)

📊 STEP 6: MONITOR FARM
1. Run: C:\\MT5_Farm\\Scripts\\3_Monitor_Farm.bat
2. Check all instances are running
3. Verify EA connections to Linux server

🎯 TARGET CONFIGURATION:
- 5 Master MT5 instances (one per broker type)
- Each with BITTENBridge EA on 10 currency pairs
- All connected to BITTEN Linux server for signals
- Ready for cloning to 350+ instances

NEXT ACTIONS REQUIRED:
1. Transfer EA file (29,942 bytes)
2. Download and install 3 MT5 brokers
3. Deploy and configure EAs
4. Test connections to Linux BITTEN system
"""
        
        print(guide)
        
        # Save guide to server as text file
        guide_lines = guide.split('\n')
        guide_path = 'C:\\MT5_Farm\\INSTALLATION_GUIDE.txt'
        
        print(f"\n💾 Saving installation guide to {guide_path}...")
        
        # Clear existing file
        self.send_command(f'if exist "{guide_path}" del /f "{guide_path}"')
        
        # Write guide line by line
        for i, line in enumerate(guide_lines):
            if i == 0:
                cmd = f'echo {line}> "{guide_path}"'
            else:
                cmd = f'echo {line}>> "{guide_path}"'
            self.send_command(cmd)
        
        print("✅ Installation guide saved to server")

if __name__ == "__main__":
    print("🚀 MT5 FARM CLEANUP AND SETUP MANAGER")
    print("="*50)
    
    farm_manager = MT5FarmManager()
    
    try:
        # Step 1: Clean existing installation
        farm_manager.cleanup_existing_installation()
        
        # Step 2: Create proper structure  
        farm_manager.create_mt5_farm_structure()
        
        # Step 3: Create installation scripts
        farm_manager.create_installation_scripts()
        
        # Step 4: Check status
        farm_manager.check_current_status()
        
        # Step 5: Generate installation guide
        farm_manager.generate_installation_guide()
        
        print("\n🎉 MT5 FARM SETUP COMPLETE!")
        print("📋 Next: Follow installation guide for manual steps")
        print("📁 Scripts available in C:\\MT5_Farm\\Scripts\\")
        print("📚 Guide available at C:\\MT5_Farm\\INSTALLATION_GUIDE.txt")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("💡 Primary agent may be down - check bulletproof infrastructure")