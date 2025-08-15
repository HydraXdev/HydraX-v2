#!/usr/bin/env python3
"""
🚀 DEPLOY ENHANCED EA HEARTBEAT TO AWS MT5 CLONE
Deploy the enhanced EA heartbeat code to AWS MT5 clone via bridge agents
"""

import requests
import json
import time
from datetime import datetime

class EnhancedEADeployer:
    """Deploy enhanced EA heartbeat to AWS MT5 clone"""
    
    def __init__(self, user_id: str = "843859"):
        self.user_id = user_id
        self.bridge_server = "localhost"
        self.bridge_port = 5555
        self.clone_path = f"C:\\MT5_Farm\\Users\\user_{user_id}"
        
        print(f"🚀 ENHANCED EA HEARTBEAT DEPLOYER INITIALIZED")
        print(f"👤 User: {user_id}")
        print(f"🖥️ Clone: {self.clone_path}")
        print(f"☁️ Bridge: {self.bridge_server}:{self.bridge_port}")
        print("=" * 60)
    
    def execute_bridge_command(self, command: str) -> dict:
        """Execute command on AWS bridge"""
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.bridge_port}/execute",
                json={
                    "command": command,
                    "type": "powershell"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_enhanced_ea_code(self) -> str:
        """Read the enhanced EA heartbeat code from local file"""
        try:
            with open('/root/HydraX-v2/tools/enhanced_ea_heartbeat.mq5', 'r') as f:
                return f.read()
        except Exception as e:
            return f"// Error reading enhanced EA code: {e}"
    
    def deploy_enhanced_ea_code(self) -> bool:
        """Deploy enhanced EA heartbeat code to AWS MT5 clone"""
        print("📁 Reading enhanced EA heartbeat code...")
        enhanced_code = self.read_enhanced_ea_code()
        
        if "Error reading" in enhanced_code:
            print(f"❌ Failed to read enhanced EA code: {enhanced_code}")
            return False
        
        print("✅ Enhanced EA code loaded successfully")
        print(f"📊 Code size: {len(enhanced_code)} characters")
        
        # Create deployment directory
        deployment_dir = f"{self.clone_path}\\MQL5\\Experts\\BITTEN_Enhanced"
        command = f'''
# Create deployment directory for enhanced EA
$deployDir = "{deployment_dir}"
if (-not (Test-Path $deployDir)) {{
    New-Item -ItemType Directory -Path $deployDir -Force
    Write-Host "📁 Created deployment directory: $deployDir"
}} else {{
    Write-Host "📁 Deployment directory exists: $deployDir"
}}

# Backup existing BITTENBridge EA if it exists
$existingEA = "{self.clone_path}\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5"
if (Test-Path $existingEA) {{
    $backupPath = "{self.clone_path}\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').mq5"
    Copy-Item $existingEA $backupPath
    Write-Host "💾 Backed up existing EA to: $backupPath"
}}

Write-Host "🎯 Ready for EA enhancement deployment"
'''
        
        print("🚀 Creating deployment environment...")
        result = self.execute_bridge_command(command)
        
        if result.get("returncode") == 0:
            print("✅ Deployment environment ready")
            print(result.get("stdout", ""))
        else:
            print(f"❌ Environment setup failed: {result.get('stderr', 'Unknown error')}")
            return False
        
        # Deploy enhanced EA code (in chunks due to size limits)
        print("📤 Deploying enhanced EA heartbeat code...")
        
        # Split code into manageable chunks
        chunk_size = 8000  # PowerShell command length limit
        code_chunks = [enhanced_code[i:i+chunk_size] for i in range(0, len(enhanced_code), chunk_size)]
        
        enhanced_ea_path = f"{deployment_dir}\\BITTENBridge_v3_ENHANCED_with_heartbeat.mq5"
        
        # Initialize file
        init_command = f'''
$enhancedEAPath = "{enhanced_ea_path}"
if (Test-Path $enhancedEAPath) {{
    Remove-Item $enhancedEAPath -Force
}}
New-Item -ItemType File -Path $enhancedEAPath -Force
Write-Host "📄 Initialized enhanced EA file: $enhancedEAPath"
'''
        
        result = self.execute_bridge_command(init_command)
        if result.get("returncode") != 0:
            print(f"❌ Failed to initialize EA file: {result.get('stderr', 'Unknown error')}")
            return False
        
        # Deploy code chunks
        for i, chunk in enumerate(code_chunks):
            print(f"📦 Deploying chunk {i+1}/{len(code_chunks)}...")
            
            # Escape quotes and special characters for PowerShell
            escaped_chunk = chunk.replace('"', '""').replace('`', '``')
            
            chunk_command = f'''
$chunk = @"
{escaped_chunk}
"@

Add-Content -Path "{enhanced_ea_path}" -Value $chunk -NoNewline
Write-Host "✅ Deployed chunk {i+1}/{len(code_chunks)}"
'''
            
            result = self.execute_bridge_command(chunk_command)
            if result.get("returncode") != 0:
                print(f"❌ Failed to deploy chunk {i+1}: {result.get('stderr', 'Unknown error')}")
                return False
            
            time.sleep(0.5)  # Small delay between chunks
        
        # Verify deployment
        print("🔍 Verifying deployment...")
        verify_command = f'''
$enhancedEAPath = "{enhanced_ea_path}"
if (Test-Path $enhancedEAPath) {{
    $fileSize = (Get-Item $enhancedEAPath).Length
    $lineCount = (Get-Content $enhancedEAPath | Measure-Object -Line).Lines
    Write-Host "✅ Enhanced EA deployed successfully"
    Write-Host "📊 File size: $fileSize bytes"
    Write-Host "📊 Line count: $lineCount lines"
    
    # Check for key functions
    $content = Get-Content $enhancedEAPath -Raw
    if ($content -match "WriteEnhancedHeartbeat") {{
        Write-Host "✅ Enhanced heartbeat function found"
    }} else {{
        Write-Host "❌ Enhanced heartbeat function not found"
    }}
    
    if ($content -match "LogSignalActivity") {{
        Write-Host "✅ Signal logging function found"
    }} else {{
        Write-Host "❌ Signal logging function not found"
    }}
    
    if ($content -match "LogTradeExecution") {{
        Write-Host "✅ Trade execution logging function found"
    }} else {{
        Write-Host "❌ Trade execution logging function not found"
    }}
    
}} else {{
    Write-Host "❌ Enhanced EA file not found after deployment"
}}
'''
        
        result = self.execute_bridge_command(verify_command)
        
        if result.get("returncode") == 0:
            print("✅ Deployment verification successful")
            print(result.get("stdout", ""))
            return True
        else:
            print(f"❌ Deployment verification failed: {result.get('stderr', 'Unknown error')}")
            return False
    
    def create_deployment_instructions(self) -> str:
        """Create manual deployment instructions"""
        instructions = f"""
🔧 ENHANCED EA HEARTBEAT DEPLOYMENT INSTRUCTIONS
=====================================================

📁 Deployment Path: {self.clone_path}\\MQL5\\Experts\\BITTEN_Enhanced\\

🎯 Manual Steps:
1. Open MetaEditor in MT5 clone
2. Navigate to: {self.clone_path}\\MQL5\\Experts\\BITTEN_Enhanced\\
3. Open: BITTENBridge_v3_ENHANCED_with_heartbeat.mq5
4. Review the enhanced functions:
   - WriteEnhancedHeartbeat() - Enhanced heartbeat with system info
   - LogSignalActivity() - Signal detection and logging
   - LogTradeExecution() - Trade execution logging
   - Enhanced OnTick() - Integrated heartbeat and signal checking

📋 Integration Steps:
1. Copy enhanced functions to your main BITTENBridge_v3_ENHANCED.mq5
2. Update OnTick() function to include WriteEnhancedHeartbeat()
3. Update OnInit() function to include initialization code
4. Update trade execution functions to include logging
5. Compile and deploy to MT5 terminal

🔍 Verification:
- Check for bridge_heartbeat.txt file updates every 30 seconds
- Monitor signal_activity.txt for signal detection logs
- Monitor trade_execution.txt for trade execution logs
- Watch EA log for enhanced heartbeat messages

📊 Files Created:
- bridge_heartbeat.txt - Enhanced heartbeat with system info
- signal_activity.txt - Signal detection and processing logs
- trade_execution.txt - Trade execution and result logs
- ea_status_enhanced.txt - Enhanced status reporting

🎯 Expected Behavior:
- Heartbeat updates every 30 seconds with balance info
- Signal detection logs all file processing
- Trade execution logs with ticket numbers and results
- Enhanced EA log messages with emojis and tactical info
"""
        return instructions
    
    def run_deployment(self) -> bool:
        """Run complete enhanced EA deployment"""
        print("🚀 Starting enhanced EA heartbeat deployment...")
        
        # Deploy enhanced EA code
        if self.deploy_enhanced_ea_code():
            print("✅ Enhanced EA heartbeat deployment completed successfully")
            print("\n" + self.create_deployment_instructions())
            return True
        else:
            print("❌ Enhanced EA heartbeat deployment failed")
            print("\n" + self.create_deployment_instructions())
            return False

def main():
    """Main enhanced EA heartbeat deployer"""
    deployer = EnhancedEADeployer("843859")
    
    success = deployer.run_deployment()
    
    if success:
        print("\n🎉 ENHANCED EA HEARTBEAT DEPLOYMENT COMPLETED")
        print("✅ Ready for Fire Loop Validation System integration")
        print("🔗 Connect to /bridge command in Telegram bot for status monitoring")
    else:
        print("\n⚠️ ENHANCED EA HEARTBEAT DEPLOYMENT INCOMPLETE")
        print("📋 Follow manual deployment instructions above")

if __name__ == "__main__":
    main()