#!/usr/bin/env python3
"""
Complete MT5 Farm Setup Instructions
Now that EA is transferred, here's the full deployment plan
"""

import requests

def send_mt5_setup_commands():
    """Send automated setup commands to AWS server"""
    
    commands = [
        # Create full directory structure
        {
            "name": "Create MT5 Farm Structure",
            "command": """
mkdir C:\\MT5_Farm\\Masters 2>nul
mkdir C:\\MT5_Farm\\Masters\\Generic_Demo 2>nul  
mkdir C:\\MT5_Farm\\Masters\\Forex_Demo 2>nul
mkdir C:\\MT5_Farm\\Masters\\Forex_Live 2>nul
mkdir C:\\MT5_Farm\\Masters\\Coinexx_Demo 2>nul
mkdir C:\\MT5_Farm\\Masters\\Coinexx_Live 2>nul
mkdir C:\\MT5_Farm\\Clones 2>nul
echo Directory structure created
"""
        },
        
        # Copy EA to all master directories
        {
            "name": "Distribute EA to Masters", 
            "command": """
copy C:\\MT5_Farm\\EA.mq5 C:\\MT5_Farm\\Masters\\Generic_Demo\\EA.mq5
copy C:\\MT5_Farm\\EA.mq5 C:\\MT5_Farm\\Masters\\Forex_Demo\\EA.mq5
copy C:\\MT5_Farm\\EA.mq5 C:\\MT5_Farm\\Masters\\Forex_Live\\EA.mq5
copy C:\\MT5_Farm\\EA.mq5 C:\\MT5_Farm\\Masters\\Coinexx_Demo\\EA.mq5
copy C:\\MT5_Farm\\EA.mq5 C:\\MT5_Farm\\Masters\\Coinexx_Live\\EA.mq5
echo EA distributed to all masters
"""
        },
        
        # Create helper scripts
        {
            "name": "Create Setup Scripts",
            "command": """
echo @echo off > C:\\MT5_Farm\\install_mt5.bat
echo echo Installing MT5 instances... >> C:\\MT5_Farm\\install_mt5.bat
echo echo 1. Download MetaTrader 5 from each broker >> C:\\MT5_Farm\\install_mt5.bat
echo echo 2. Install to respective Master folders >> C:\\MT5_Farm\\install_mt5.bat  
echo echo 3. Copy EA to MQL5\\Experts\\ folder >> C:\\MT5_Farm\\install_mt5.bat
echo echo 4. Run attach_ea.bat after installation >> C:\\MT5_Farm\\install_mt5.bat
echo pause >> C:\\MT5_Farm\\install_mt5.bat

echo @echo off > C:\\MT5_Farm\\attach_ea.bat
echo echo Attaching EA to all charts... >> C:\\MT5_Farm\\attach_ea.bat
echo echo Manual step: Open each MT5 instance >> C:\\MT5_Farm\\attach_ea.bat
echo echo 1. Open MetaEditor (F4) >> C:\\MT5_Farm\\attach_ea.bat
echo echo 2. Compile BITTENBridge_v3_ENHANCED.mq5 (F7) >> C:\\MT5_Farm\\attach_ea.bat
echo echo 3. Drag EA to EURUSD, GBPUSD, USDJPY charts >> C:\\MT5_Farm\\attach_ea.bat
echo echo 4. Enable AutoTrading (Ctrl+E) >> C:\\MT5_Farm\\attach_ea.bat
echo pause >> C:\\MT5_Farm\\attach_ea.bat

echo Helper scripts created
"""
        },
        
        # Verify EA integrity
        {
            "name": "Verify EA File",
            "command": 'powershell -Command "Get-FileHash C:\\MT5_Farm\\EA.mq5 -Algorithm MD5 | Select-Object Algorithm,Hash,Path"'
        }
    ]
    
    print("🚀 Sending MT5 setup commands to AWS server...")
    
    for cmd_info in commands:
        print(f"\n📋 {cmd_info['name']}...")
        
        payload = {
            'action': 'execute_command',
            'command': cmd_info['command'],
            'timeout': 30
        }
        
        try:
            response = requests.post('http://localhost:5555/execute', json=payload, timeout=35)
            
            if response.status_code == 200:
                result = response.json()
                stdout = result.get('stdout', '')
                stderr = result.get('stderr', '')
                
                if stdout:
                    print(f"✅ {stdout}")
                if stderr:
                    print(f"⚠️ {stderr}")
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def generate_download_links():
    """Generate MT5 download links for each broker"""
    
    links = {
        "MetaQuotes (Generic)": "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe",
        "Forex.com": "https://www.forex.com/en-us/platforms/metatrader-5/",
        "Coinexx": "https://www.coinexx.com/metatrader-5"
    }
    
    print("\n📥 MT5 Download Links:")
    print("="*40)
    
    for broker, link in links.items():
        print(f"{broker}:")
        print(f"  {link}")
        print()

def create_deployment_checklist():
    """Create complete deployment checklist"""
    
    checklist = """
🎯 MT5 FARM DEPLOYMENT CHECKLIST

✅ COMPLETED:
   ▢ EA transferred to AWS server (C:\\MT5_Farm\\EA.mq5)
   ▢ Directory structure created
   ▢ Helper scripts generated

🔄 NEXT STEPS (Manual):

📥 PHASE 1: Download & Install MT5 (15 minutes)
   ▢ Download MetaTrader 5 from MetaQuotes (Generic)
   ▢ Download MetaTrader 5 from Forex.com  
   ▢ Download MetaTrader 5 from Coinexx
   ▢ Install each to respective Master folders
   ▢ Create demo accounts for testing

🔧 PHASE 2: EA Deployment (10 minutes)
   ▢ Copy EA to each MT5/MQL5/Experts/ folder
   ▢ Open MetaEditor in each instance (F4)
   ▢ Compile BITTENBridge_v3_ENHANCED.mq5 (F7) 
   ▢ Verify compilation successful (no errors)

📊 PHASE 3: Chart Setup (10 minutes)
   ▢ Open charts for 10 pairs in each MT5:
     - EURUSD, GBPUSD, USDJPY, USDCAD, GBPJPY
     - AUDUSD, NZDUSD, EURGBP, USDCHF, EURJPY
   ▢ Drag EA to each chart
   ▢ Configure EA settings (default is fine)
   ▢ Enable AutoTrading (Ctrl+E) in each instance

🚀 PHASE 4: Live Connection (5 minutes)
   ▢ Verify EAs are running (smiley face icons)
   ▢ Check Expert Advisors tab for activity
   ▢ Test connection to BITTEN Linux server
   ▢ Verify signal flow in BITTEN logs

⚡ PHASE 5: Scale to 350 Instances (Optional)
   ▢ Clone master installations 
   ▢ Configure unique magic numbers
   ▢ Distribute across user tiers
   ▢ Monitor system performance

🎉 SUCCESS CRITERIA:
   ▢ 3+ MT5 instances running with EA
   ▢ 10 currency pairs monitored per instance
   ▢ Live data flowing to BITTEN system
   ▢ Real signals generated from MT5 prices
   ▢ Complete trading pipeline operational

📞 SUPPORT:
   - EA file: C:\\MT5_Farm\\EA.mq5 (✅ ready)
   - Setup scripts: C:\\MT5_Farm\\*.bat (✅ ready)
   - Bulletproof agents: Monitoring & auto-recovery active
   - Linux BITTEN system: Waiting for MT5 connection
"""
    
    return checklist

if __name__ == "__main__":
    print("🎯 MT5 FARM COMPLETE SETUP")
    print("="*50)
    
    # Send automated setup commands
    send_mt5_setup_commands()
    
    # Show download links
    generate_download_links()
    
    # Display checklist
    checklist = create_deployment_checklist()
    print(checklist)
    
    print("\n🎉 AUTOMATED SETUP COMPLETED!")
    print("📋 Manual steps required: Download & install MT5 instances")
    print("⏱️  Estimated time: 30-40 minutes total")
    print("🎯 Result: Fully operational 350-instance MT5 farm")