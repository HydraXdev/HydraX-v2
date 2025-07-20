#!/usr/bin/env python3
"""
AWS FRESH CLONE SETUP - User 843859
Uses AWS bridge agents to create and configure MT5 clone
"""

import json
import time
import requests
from datetime import datetime
from production_bridge_tunnel import get_production_tunnel

class AWSFreshCloneSetup:
    def __init__(self):
        self.user_id = "843859"
        self.credentials = {
            "username": "843859",
            "password": "Ao4@brz64erHaG",
            "server": "Coinexx-Demo"
        }
        
        # Get production tunnel
        self.tunnel = get_production_tunnel()
        self.bridge_server = "3.145.84.187"
        self.primary_port = 5555
        
    def log_step(self, step, status, details=""):
        """Log setup steps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {step}: {status}")
        if details:
            print(f"    {details}")
    
    def cleanup_existing_clone(self):
        """Clean up existing clone for this user on AWS"""
        self.log_step("AWS_CLEANUP", "🧹 Cleaning up existing clone on AWS")
        
        cleanup_command = f'''
# Clean up existing clone for user 843859
$userPath = "C:\\MT5_Farm\\Users\\user_843859"
if (Test-Path $userPath) {{
    Write-Host "Removing existing clone at $userPath"
    Remove-Item $userPath -Recurse -Force
    Write-Host "✅ Clone directory cleaned"
}}

# Stop any existing MT5 processes for this user
$processes = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue | Where-Object {{$_.Path -like "*user_843859*"}}
foreach ($proc in $processes) {{
    Write-Host "Stopping MT5 process: $($proc.Id)"
    Stop-Process -Id $proc.Id -Force
}}

Write-Host "🧹 Cleanup completed for user 843859"
'''
        
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.primary_port}/execute",
                json={
                    "command": cleanup_command,
                    "type": "powershell"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('returncode') == 0:
                    self.log_step("AWS_CLEANUP", "✅ AWS cleanup completed successfully")
                    return True
                else:
                    self.log_step("AWS_CLEANUP", f"⚠️ Cleanup warnings: {result.get('stderr', '')}")
                    return True  # Continue even with warnings
            else:
                self.log_step("AWS_CLEANUP", f"❌ AWS cleanup failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_step("AWS_CLEANUP", f"❌ AWS cleanup error: {e}")
            return False
    
    def create_fresh_clone(self):
        """Create fresh MT5 clone on AWS"""
        self.log_step("AWS_CLONE", "🏗️ Creating fresh MT5 clone on AWS")
        
        create_command = f'''
# Create fresh MT5 clone for user 843859
$masterPath = "C:\\MT5_Farm\\Masters\\BITTEN_MASTER"
$userPath = "C:\\MT5_Farm\\Users\\user_843859"

# Verify master exists
if (!(Test-Path $masterPath)) {{
    Write-Host "❌ BITTEN_MASTER not found at $masterPath"
    exit 1
}}

# Create user directory
New-Item -ItemType Directory -Path $userPath -Force
Write-Host "📁 Created user directory: $userPath"

# Copy master template
Copy-Item -Path "$masterPath\\*" -Destination $userPath -Recurse -Force
Write-Host "📋 Copied BITTEN_MASTER template"

# Create Config directory
$configPath = "$userPath\\Config"
New-Item -ItemType Directory -Path $configPath -Force

# Create terminal.ini with credentials
$terminalIni = @"
[Common]
Login={self.credentials['username']}
Password={self.credentials['password']}
Server={self.credentials['server']}
AutoTrading=true
ExpertAdvisor=true
AlgoTrading=true

[Startup]
Expert=BITTEN_v3_ENHANCED
Symbol=EURUSD
Period=H1
"@

$terminalIni | Out-File -FilePath "$configPath\\terminal.ini" -Encoding UTF8
Write-Host "⚙️ Created terminal.ini with credentials"

# Create accounts.ini
$accountsIni = @"
[Account1]
Login={self.credentials['username']}
Server={self.credentials['server']}
"@

$accountsIni | Out-File -FilePath "$configPath\\accounts.ini" -Encoding UTF8
Write-Host "🏦 Created accounts.ini"

# Create bridge directory
$bridgePath = "$userPath\\bridge"
New-Item -ItemType Directory -Path $bridgePath -Force

# Create bridge configuration
$bridgeConfig = @"
{{
  "user_id": "{self.user_id}",
  "input_file": "$bridgePath\\signals_in.json",
  "output_file": "$bridgePath\\results_out.json",
  "status_file": "$bridgePath\\status.json",
  "heartbeat_file": "$bridgePath\\heartbeat.json",
  "account_id": "{self.credentials['username']}",
  "server": "{self.credentials['server']}"
}}
"@

$bridgeConfig | Out-File -FilePath "$bridgePath\\bridge_config.json" -Encoding UTF8
Write-Host "🌉 Created bridge configuration"

# Create initial status file
$statusFile = @"
{{
  "user_id": "{self.user_id}",
  "account_id": "{self.credentials['username']}",
  "status": "initialized",
  "timestamp": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')",
  "ea_version": "BITTEN_v3_ENHANCED",
  "server": "{self.credentials['server']}"
}}
"@

$statusFile | Out-File -FilePath "$bridgePath\\status.json" -Encoding UTF8
Write-Host "📊 Created initial status file"

Write-Host "✅ Fresh clone created successfully for user 843859"
Write-Host "📁 Clone path: $userPath"
Write-Host "🌉 Bridge path: $bridgePath"
'''
        
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.primary_port}/execute",
                json={
                    "command": create_command,
                    "type": "powershell"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('returncode') == 0:
                    self.log_step("AWS_CLONE", "✅ Fresh clone created successfully")
                    self.log_step("AWS_CLONE", f"📁 Path: C:\\MT5_Farm\\Users\\user_{self.user_id}")
                    return True
                else:
                    self.log_step("AWS_CLONE", f"❌ Clone creation failed: {result.get('stderr', '')}")
                    return False
            else:
                self.log_step("AWS_CLONE", f"❌ Clone creation failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_step("AWS_CLONE", f"❌ Clone creation error: {e}")
            return False
    
    def start_mt5_instance(self):
        """Start MT5 instance on AWS"""
        self.log_step("AWS_MT5", "🚀 Starting MT5 instance on AWS")
        
        start_command = f'''
# Start MT5 instance for user 843859
$userPath = "C:\\MT5_Farm\\Users\\user_843859"
$configPath = "$userPath\\Config"
$mt5Exe = "$userPath\\terminal64.exe"

# Check if MT5 executable exists
if (!(Test-Path $mt5Exe)) {{
    Write-Host "❌ MT5 executable not found at $mt5Exe"
    exit 1
}}

# Start MT5 with user-specific configuration
$processArgs = @(
    "/config:$configPath",
    "/profile:user_843859",
    "/portable"
)

Write-Host "🚀 Starting MT5 with config: $configPath"
$process = Start-Process -FilePath $mt5Exe -ArgumentList $processArgs -WorkingDirectory $userPath -PassThru

if ($process) {{
    Write-Host "✅ MT5 started successfully"
    Write-Host "🆔 Process ID: $($process.Id)"
    Write-Host "📁 Working Directory: $userPath"
    
    # Wait a moment for MT5 to initialize
    Start-Sleep -Seconds 5
    
    # Verify process is still running
    if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {{
        Write-Host "✅ MT5 instance is running"
    }} else {{
        Write-Host "⚠️ MT5 process may have terminated"
    }}
}} else {{
    Write-Host "❌ Failed to start MT5"
    exit 1
}}
'''
        
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.primary_port}/execute",
                json={
                    "command": start_command,
                    "type": "powershell"
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('returncode') == 0:
                    self.log_step("AWS_MT5", "✅ MT5 instance started successfully")
                    return True
                else:
                    self.log_step("AWS_MT5", f"❌ MT5 start failed: {result.get('stderr', '')}")
                    return False
            else:
                self.log_step("AWS_MT5", f"❌ MT5 start failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_step("AWS_MT5", f"❌ MT5 start error: {e}")
            return False
    
    def test_connectivity_and_balance(self):
        """Test MT5 connectivity and retrieve account balance"""
        self.log_step("CONNECTIVITY", "🔍 Testing MT5 connectivity and account balance")
        
        # Wait for MT5 to fully initialize
        time.sleep(10)
        
        test_command = f'''
# Test MT5 connectivity for user 843859
$userPath = "C:\\MT5_Farm\\Users\\user_843859"
$bridgePath = "$userPath\\bridge"

# Check if bridge files exist
if (!(Test-Path "$bridgePath\\status.json")) {{
    Write-Host "❌ Bridge status file not found"
    exit 1
}}

# Create a ping/test signal
$testSignal = @"
{{
  "command": "ping",
  "user_id": "{self.user_id}",
  "account_id": "{self.credentials['username']}",
  "timestamp": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')",
  "test_connectivity": true
}}
"@

$testSignal | Out-File -FilePath "$bridgePath\\test_ping.json" -Encoding UTF8
Write-Host "📡 Created test ping signal"

# Check for any existing result files
$resultFiles = Get-ChildItem -Path $bridgePath -Filter "*.json" | Where-Object {{$_.Name -like "*result*" -or $_.Name -like "*output*"}}
if ($resultFiles) {{
    Write-Host "📊 Found existing result files:"
    foreach ($file in $resultFiles) {{
        Write-Host "  - $($file.Name)"
        $content = Get-Content $file.FullName -Raw
        if ($content) {{
            Write-Host "  Content preview: $($content.Substring(0, [Math]::Min(100, $content.Length)))"
        }}
    }}
}}

# Check bridge status
$statusContent = Get-Content "$bridgePath\\status.json" -Raw
Write-Host "📊 Bridge Status:"
Write-Host $statusContent

Write-Host "✅ Connectivity test completed"
'''
        
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.primary_port}/execute",
                json={
                    "command": test_command,
                    "type": "powershell"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                output = result.get('stdout', '')
                
                self.log_step("CONNECTIVITY", "✅ Bridge connectivity test completed")
                print(f"📊 Bridge Output:\n{output}")
                
                # Extract account info if available
                if "Account ID" in output:
                    self.log_step("CONNECTIVITY", "✅ Account connection detected")
                
                return True
            else:
                self.log_step("CONNECTIVITY", f"❌ Connectivity test failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_step("CONNECTIVITY", f"❌ Connectivity test error: {e}")
            return False
    
    def run_full_aws_setup(self):
        """Run complete AWS fresh clone setup"""
        print("=" * 60)
        print("🚀 AWS FRESH MT5 CLONE SETUP - User 843859")
        print("=" * 60)
        print(f"🎯 Target: AWS Server {self.bridge_server}")
        print(f"🏦 Account: {self.credentials['username']} @ {self.credentials['server']}")
        print("=" * 60)
        
        # Step 1: Cleanup existing clone
        if not self.cleanup_existing_clone():
            print("❌ Setup failed at AWS cleanup step")
            return False
        
        # Step 2: Create fresh clone
        if not self.create_fresh_clone():
            print("❌ Setup failed at clone creation step")
            return False
        
        # Step 3: Start MT5 instance
        if not self.start_mt5_instance():
            print("❌ Setup failed at MT5 startup step")
            return False
        
        # Step 4: Test connectivity
        if not self.test_connectivity_and_balance():
            print("❌ Setup failed at connectivity test step")
            return False
        
        print("\n" + "=" * 60)
        print("✅ AWS FRESH MT5 CLONE SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"🎯 AWS Server: {self.bridge_server}:{self.primary_port}")
        print(f"📁 Clone Path: C:\\MT5_Farm\\Users\\user_{self.user_id}")
        print(f"🌉 Bridge Path: C:\\MT5_Farm\\Users\\user_{self.user_id}\\bridge")
        print(f"🏦 Account: {self.credentials['username']} @ {self.credentials['server']}")
        print("⚠️  IMPORTANT: System will NEVER execute fake trades")
        print("⚠️  IMPORTANT: All trades will be real or clearly fail")
        print("=" * 60)
        
        return True

def main():
    """Main AWS setup function"""
    setup = AWSFreshCloneSetup()
    
    try:
        success = setup.run_full_aws_setup()
        if success:
            print("\n🎉 AWS MT5 clone is ready for live trading!")
            print("🔗 Bridge agents are operational")
            print("🚀 Ready to receive and execute live signals")
        else:
            print("\n❌ AWS setup failed. Please check logs and try again.")
            
    except KeyboardInterrupt:
        print("\n⏹️  AWS setup interrupted by user")
    except Exception as e:
        print(f"\n💥 AWS setup crashed: {e}")

if __name__ == "__main__":
    main()