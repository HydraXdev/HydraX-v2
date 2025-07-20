#!/usr/bin/env python3
"""
Working EA Transfer Solution
Simple, reliable method that WILL work
"""

import requests
import base64
import time

def transfer_ea_simple():
    """Simple base64 transfer that should work"""
    
    # Read EA file
    ea_file = "/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5"
    
    print("📖 Reading EA file...")
    with open(ea_file, 'rb') as f:
        ea_content = f.read()
    
    print(f"✅ File read: {len(ea_content)} bytes")
    
    # Convert to base64
    ea_b64 = base64.b64encode(ea_content).decode('utf-8')
    print(f"✅ Base64 encoded: {len(ea_b64)} characters")
    
    # Create PowerShell script to decode and save
    ps_script = f"""
try {{
    # Create directory
    New-Item -ItemType Directory -Path "C:\\MT5_Farm" -Force | Out-Null
    
    # Base64 content (split for readability)
    $base64Content = @"
{ea_b64}
"@
    
    # Decode and save
    $bytes = [System.Convert]::FromBase64String($base64Content)
    [System.IO.File]::WriteAllBytes("C:\\MT5_Farm\\EA.mq5", $bytes)
    
    # Verify
    if (Test-Path "C:\\MT5_Farm\\EA.mq5") {{
        $file = Get-Item "C:\\MT5_Farm\\EA.mq5"
        Write-Output "SUCCESS: File created - Size: $($file.Length) bytes"
    }} else {{
        Write-Output "ERROR: File not created"
    }}
}} catch {{
    Write-Output "ERROR: $($_.Exception.Message)"
}}
"""
    
    print("🚀 Sending PowerShell script to agent...")
    
    # Send script to agent
    payload = {
        'action': 'execute_command',
        'command': f'powershell -Command "{ps_script}"',
        'timeout': 60
    }
    
    try:
        response = requests.post(
            'http://localhost:5555/execute',
            json=payload,
            timeout=65
        )
        
        if response.status_code == 200:
            result = response.json()
            stdout = result.get('stdout', '')
            stderr = result.get('stderr', '')
            
            print(f"📋 Response: {stdout}")
            if stderr:
                print(f"⚠️ Stderr: {stderr}")
            
            if "SUCCESS" in stdout:
                print("🎉 EA transfer completed successfully!")
                return True
            else:
                print("❌ Transfer failed")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def transfer_ea_chunks():
    """Alternative: Transfer in small chunks"""
    
    print("🔄 Attempting chunked transfer...")
    
    # Read EA file
    ea_file = "/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5"
    
    with open(ea_file, 'rb') as f:
        ea_content = f.read()
    
    # Convert to base64
    ea_b64 = base64.b64encode(ea_content).decode('utf-8')
    
    # Split into 5KB chunks
    chunk_size = 5000
    chunks = [ea_b64[i:i+chunk_size] for i in range(0, len(ea_b64), chunk_size)]
    
    print(f"📦 Split into {len(chunks)} chunks")
    
    # Clear any existing file
    clear_script = """
if (Test-Path "C:\\MT5_Farm\\EA.mq5") { Remove-Item "C:\\MT5_Farm\\EA.mq5" -Force }
if (Test-Path "C:\\MT5_Farm\\EA_temp.b64") { Remove-Item "C:\\MT5_Farm\\EA_temp.b64" -Force }
New-Item -ItemType Directory -Path "C:\\MT5_Farm" -Force | Out-Null
Write-Output "Ready for transfer"
"""
    
    payload = {
        'action': 'execute_command', 
        'command': f'powershell -Command "{clear_script}"'
    }
    
    response = requests.post('http://localhost:5555/execute', json=payload, timeout=10)
    if response.status_code != 200:
        print("❌ Failed to clear existing files")
        return False
    
    print("✅ Cleared existing files")
    
    # Send chunks
    for i, chunk in enumerate(chunks):
        print(f"📤 Sending chunk {i+1}/{len(chunks)}...")
        
        if i == 0:
            # First chunk - create file
            chunk_script = f'Set-Content -Path "C:\\MT5_Farm\\EA_temp.b64" -Value "{chunk}" -NoNewline -Encoding ASCII'
        else:
            # Subsequent chunks - append
            chunk_script = f'Add-Content -Path "C:\\MT5_Farm\\EA_temp.b64" -Value "{chunk}" -NoNewline -Encoding ASCII'
        
        payload = {
            'action': 'execute_command',
            'command': f'powershell -Command "{chunk_script}"',
            'timeout': 15
        }
        
        response = requests.post('http://localhost:5555/execute', json=payload, timeout=20)
        
        if response.status_code == 200:
            print(f"✅ Chunk {i+1} sent")
        else:
            print(f"❌ Chunk {i+1} failed")
            return False
        
        time.sleep(0.1)  # Small delay
    
    # Convert base64 to binary
    print("🔄 Converting base64 to binary file...")
    
    convert_script = """
try {
    $base64Content = Get-Content -Path "C:\\MT5_Farm\\EA_temp.b64" -Raw
    $bytes = [System.Convert]::FromBase64String($base64Content)
    [System.IO.File]::WriteAllBytes("C:\\MT5_Farm\\EA.mq5", $bytes)
    Remove-Item "C:\\MT5_Farm\\EA_temp.b64" -Force
    
    if (Test-Path "C:\\MT5_Farm\\EA.mq5") {
        $file = Get-Item "C:\\MT5_Farm\\EA.mq5"
        Write-Output "SUCCESS: EA.mq5 created - Size: $($file.Length) bytes"
    } else {
        Write-Output "ERROR: Conversion failed"
    }
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
}
"""
    
    payload = {
        'action': 'execute_command',
        'command': f'powershell -Command "{convert_script}"',
        'timeout': 30
    }
    
    response = requests.post('http://localhost:5555/execute', json=payload, timeout=35)
    
    if response.status_code == 200:
        result = response.json()
        stdout = result.get('stdout', '')
        print(f"📋 Conversion result: {stdout}")
        
        if "SUCCESS" in stdout:
            print("🎉 Chunked transfer completed successfully!")
            return True
    
    print("❌ Chunked transfer failed")
    return False

def verify_ea_file():
    """Verify the EA file exists and has correct size"""
    
    verify_script = """
if (Test-Path "C:\\MT5_Farm\\EA.mq5") {
    $file = Get-Item "C:\\MT5_Farm\\EA.mq5"
    $hash = Get-FileHash "C:\\MT5_Farm\\EA.mq5" -Algorithm MD5
    Write-Output "File exists: $($file.Name)"
    Write-Output "Size: $($file.Length) bytes" 
    Write-Output "Modified: $($file.LastWriteTime)"
    Write-Output "MD5: $($hash.Hash)"
} else {
    Write-Output "FILE_NOT_FOUND"
}
"""
    
    payload = {
        'action': 'execute_command',
        'command': f'powershell -Command "{verify_script}"'
    }
    
    try:
        response = requests.post('http://localhost:5555/execute', json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            output = result.get('stdout', '')
            print("📋 File verification:")
            print(output)
            
            if "FILE_NOT_FOUND" in output:
                return False
            elif "Size: 29942 bytes" in output:  # Expected size
                print("✅ File verification successful!")
                return True
            else:
                print("⚠️ File exists but size doesn't match")
                return False
        else:
            print(f"❌ Verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting EA Transfer...")
    print("="*50)
    
    # Try simple method first
    if transfer_ea_simple():
        print("\n✅ Simple transfer successful!")
    elif transfer_ea_chunks():
        print("\n✅ Chunked transfer successful!")
    else:
        print("\n❌ All transfer methods failed")
        exit(1)
    
    # Verify the transfer
    print("\n🔍 Verifying transfer...")
    if verify_ea_file():
        print("\n🎉 EA TRANSFER COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Install MT5 instances: Generic, Forex.com, Coinexx")
        print("2. Copy EA to each MT5/MQL5/Experts/ folder")
        print("3. Compile EA in MetaEditor (F7)")
        print("4. Attach to charts and enable AutoTrading")
    else:
        print("\n❌ Transfer verification failed")
        exit(1)