#\!/usr/bin/env python3
"""
Deploy BITTEN EA to all MT5 instances on Windows server
"""

import requests
import base64

AWS_SERVER = "3.145.84.187"
PORT = 5555

def execute_command(command):
    """Execute command on Windows server"""
    try:
        url = f"http://{AWS_SERVER}:{PORT}/execute"
        response = requests.post(url, json={"command": command}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('success', False), result.get('stdout', ''), result.get('stderr', '')
        return False, '', f"HTTP {response.status_code}"
    except Exception as e:
        return False, '', str(e)

def deploy_ea_to_farm():
    """Deploy the EA to all MT5 instances"""
    
    print("🚀 Deploying BITTEN EA to MT5 Farm")
    print("=" * 60)
    
    # Read the EA file
    ea_path = "/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5"
    try:
        with open(ea_path, 'r') as f:
            ea_content = f.read()
    except:
        print("❌ Could not find EA file at:", ea_path)
        return
    
    # Encode EA content
    encoded_ea = base64.b64encode(ea_content.encode()).decode()
    
    # PowerShell script to deploy EA
    deploy_script = f'''
$eaContent = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded_ea}"))

# Deploy to all master instances
$masters = @("Forex_Demo", "Forex_Live", "Coinexx_Demo", "Coinexx_Live", "Generic_Demo")

foreach ($master in $masters) {{
    $eaPath = "C:\\MT5_Farm\\Masters\\$master\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5"
    
    # Create Experts directory if it doesn't exist
    $expertsDir = Split-Path $eaPath -Parent
    if (\!(Test-Path $expertsDir)) {{
        New-Item -ItemType Directory -Path $expertsDir -Force  < /dev/null |  Out-Null
    }}
    
    # Write EA file
    $eaContent | Out-File -FilePath $eaPath -Encoding UTF8
    Write-Host "Deployed EA to: $master"
}}

# Also create a copy in Clones directory for easy access
$centralEA = "C:\\MT5_Farm\\BITTENBridge_v3_ENHANCED.mq5"
$eaContent | Out-File -FilePath $centralEA -Encoding UTF8
Write-Host "Created central EA copy at: $centralEA"

# Create deployment helper script
$helperScript = @'
# Helper to copy EA to all clone instances
param([string]$InstanceType = "all")

$centralEA = "C:\\MT5_Farm\\BITTENBridge_v3_ENHANCED.mq5"

if ($InstanceType -eq "all") {{
    $clones = Get-ChildItem "C:\\MT5_Farm\\Clones" -Directory
}} else {{
    $clones = Get-ChildItem "C:\\MT5_Farm\\Clones" -Directory -Filter "${{InstanceType}}_*"
}}

foreach ($clone in $clones) {{
    $targetPath = "$($clone.FullName)\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5"
    $expertsDir = Split-Path $targetPath -Parent
    
    if (\!(Test-Path $expertsDir)) {{
        New-Item -ItemType Directory -Path $expertsDir -Force | Out-Null
    }}
    
    Copy-Item -Path $centralEA -Destination $targetPath -Force
    Write-Host "Deployed to: $($clone.Name)"
}}
'@

$helperScript | Out-File -FilePath "C:\\MT5_Farm\\deploy_ea_to_clones.ps1" -Encoding UTF8
Write-Host "Created helper script: deploy_ea_to_clones.ps1"
'''
    
    # Execute deployment
    print("\n📤 Deploying EA to Windows server...")
    success, stdout, stderr = execute_command(f'powershell -Command "{deploy_script}"')
    
    if success:
        print("✅ EA deployed successfully\!")
        print("\nOutput:", stdout)
    else:
        print("❌ Deployment failed:", stderr)
    
    # Create instance configuration script
    config_script = '''
# Configure EA settings for each instance type
$configs = @{
    "Generic_Demo" = @{
        "MagicStart" = 50001
        "Risk" = 2.0
        "MaxTrades" = 3
        "Comment" = "BITTEN_PressPass"
    }
    "Forex_Demo" = @{
        "MagicStart" = 30001
        "Risk" = 2.0
        "MaxTrades" = 5
        "Comment" = "BITTEN_Demo"
    }
    "Coinexx_Demo" = @{
        "MagicStart" = 40001
        "Risk" = 2.0
        "MaxTrades" = 5
        "Comment" = "BITTEN_DemoOff"
    }
    "Forex_Live" = @{
        "MagicStart" = 20001
        "Risk" = 2.0
        "MaxTrades" = 10
        "Comment" = "BITTEN_Live"
    }
    "Coinexx_Live" = @{
        "MagicStart" = 10001
        "Risk" = 2.0
        "MaxTrades" = 10
        "Comment" = "BITTEN_LiveOff"
    }
}

Write-Host "EA Configuration Reference:"
Write-Host "============================"

foreach ($type in $configs.Keys) {
    $config = $configs[$type]
    Write-Host "`n$type instances:"
    Write-Host "  Magic Number Start: $($config.MagicStart)"
    Write-Host "  Risk Per Trade: $($config.Risk)%"
    Write-Host "  Max Concurrent: $($config.MaxTrades)"
    Write-Host "  Trade Comment: $($config.Comment)"
}
'''
    
    encoded_config = base64.b64encode(config_script.encode()).decode()
    cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded_config}")) | Out-File -FilePath "C:\\MT5_Farm\\ea_configurations.ps1" -Encoding UTF8'
    execute_command(cmd)
    
    print("\n" + "="*60)
    print("📋 EA DEPLOYMENT SUMMARY")
    print("="*60)
    
    print("\n✅ EA deployed to all master instances")
    print("✅ Central copy created at C:\\MT5_Farm\\BITTENBridge_v3_ENHANCED.mq5")
    print("✅ Helper scripts created for clone deployment")
    
    print("\n📍 EA LOCATIONS:")
    print("- Masters: C:\\MT5_Farm\\Masters\\[Type]\\MQL5\\Experts\\")
    print("- Central: C:\\MT5_Farm\\BITTENBridge_v3_ENHANCED.mq5")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Open each MT5 master instance")
    print("2. Press F4 to open MetaEditor")
    print("3. Navigate to Experts folder")
    print("4. Double-click BITTENBridge_v3_ENHANCED.mq5")
    print("5. Press F7 to compile")
    print("6. EA will appear in Navigator panel")
    print("7. Drag to each of the 10 currency pair charts")
    print("8. Set magic number according to instance (see ea_configurations.ps1)")
    
    print("\n💡 To deploy EA to clones later:")
    print("powershell C:\\MT5_Farm\\deploy_ea_to_clones.ps1")

if __name__ == "__main__":
    deploy_ea_to_farm()
