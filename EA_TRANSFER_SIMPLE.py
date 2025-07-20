#!/usr/bin/env python3
"""
Ultra-Simple EA Transfer - Line by Line Text Method
This WILL work because it's the simplest possible approach
"""

import requests
import time

def transfer_ea_as_text():
    """Transfer EA as plain text file line by line"""
    
    print("📖 Reading EA file as text...")
    
    # Read EA file as text
    ea_file = "/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5"
    
    with open(ea_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    print(f"✅ File read: {len(lines)} lines")
    
    # Create directory first
    print("📁 Creating directory...")
    
    mkdir_payload = {
        'action': 'execute_command',
        'command': 'mkdir C:\\MT5_Farm 2>nul || echo Directory exists'
    }
    
    response = requests.post('http://localhost:5555/execute', json=mkdir_payload, timeout=10)
    if response.status_code == 200:
        print("✅ Directory created")
    else:
        print("❌ Directory creation failed")
        return False
    
    # Delete existing file
    print("🗑️ Removing existing file...")
    
    del_payload = {
        'action': 'execute_command',
        'command': 'del C:\\MT5_Farm\\EA.mq5 2>nul || echo No file to delete'
    }
    
    response = requests.post('http://localhost:5555/execute', json=del_payload, timeout=10)
    print("✅ Cleanup completed")
    
    # Transfer file line by line using simple echo commands
    print("📤 Transferring file line by line...")
    
    for i, line in enumerate(lines):
        if i % 50 == 0:
            print(f"📤 Line {i+1}/{len(lines)}...")
        
        # Clean the line for batch file compatibility
        clean_line = line.strip().replace('"', '""').replace('%', '%%').replace('&', '^&').replace('<', '^<').replace('>', '^>').replace('|', '^|')
        
        if i == 0:
            # First line - create file
            cmd = f'echo {clean_line}> C:\\MT5_Farm\\EA.mq5'
        else:
            # Subsequent lines - append
            cmd = f'echo {clean_line}>> C:\\MT5_Farm\\EA.mq5'
        
        payload = {
            'action': 'execute_command',
            'command': cmd
        }
        
        response = requests.post('http://localhost:5555/execute', json=payload, timeout=5)
        
        if response.status_code != 200:
            print(f"❌ Failed at line {i+1}")
            return False
        
        # Small delay every 10 lines
        if i % 10 == 0:
            time.sleep(0.1)
    
    print("✅ All lines transferred")
    
    # Verify file was created
    print("🔍 Verifying file...")
    
    verify_payload = {
        'action': 'execute_command',
        'command': 'dir C:\\MT5_Farm\\EA.mq5'
    }
    
    response = requests.post('http://localhost:5555/execute', json=verify_payload, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        output = result.get('stdout', '')
        print(f"📋 Verification: {output}")
        
        if "EA.mq5" in output:
            print("🎉 EA transfer completed successfully!")
            return True
    
    print("❌ File verification failed")
    return False

def create_simple_http_server():
    """Create a simple HTTP server to serve the EA file"""
    
    import subprocess
    import threading
    import os
    
    print("🌐 Starting HTTP server...")
    
    # Change to EA directory
    ea_dir = "/root/HydraX-v2/BITTEN_Windows_Package/EA"
    
    # Start Python HTTP server
    server_process = subprocess.Popen(
        ['python3', '-m', 'http.server', '9999'],
        cwd=ea_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)  # Let server start
    
    print("✅ HTTP server started on port 9999")
    
    # Get our external IP
    try:
        result = subprocess.run(['curl', '-s', 'ifconfig.me'], capture_output=True, text=True, timeout=5)
        external_ip = result.stdout.strip()
        print(f"📡 External IP: {external_ip}")
    except:
        external_ip = "134.199.204.67"  # Fallback
        print(f"📡 Using fallback IP: {external_ip}")
    
    # Have agent download the file
    print("⬇️ Commanding agent to download...")
    
    download_cmd = f'powershell -Command "Invoke-WebRequest -Uri http://{external_ip}:9999/BITTENBridge_v3_ENHANCED.mq5 -OutFile C:\\MT5_Farm\\EA.mq5"'
    
    download_payload = {
        'action': 'execute_command',
        'command': download_cmd,
        'timeout': 30
    }
    
    try:
        response = requests.post('http://localhost:5555/execute', json=download_payload, timeout=35)
        
        # Kill server
        server_process.terminate()
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Download result: {result}")
            
            # Verify download
            verify_payload = {
                'action': 'execute_command',
                'command': 'dir C:\\MT5_Farm\\EA.mq5'
            }
            
            verify_response = requests.post('http://localhost:5555/execute', json=verify_payload, timeout=10)
            
            if verify_response.status_code == 200:
                verify_result = verify_response.json()
                verify_output = verify_result.get('stdout', '')
                
                if "EA.mq5" in verify_output and "29," in verify_output:  # Check for ~29KB file
                    print("🎉 HTTP download successful!")
                    return True
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        server_process.terminate()
    
    return False

if __name__ == "__main__":
    print("🚀 Ultra-Simple EA Transfer")
    print("="*40)
    
    # Try HTTP download first (fastest)
    print("\\n🌐 Method 1: HTTP Download")
    if create_simple_http_server():
        print("\\n✅ HTTP DOWNLOAD SUCCESSFUL!")
    else:
        print("\\n⚠️ HTTP download failed, trying line-by-line...")
        
        # Fall back to line-by-line transfer
        print("\\n📝 Method 2: Line-by-Line Transfer")
        if transfer_ea_as_text():
            print("\\n✅ LINE-BY-LINE TRANSFER SUCCESSFUL!")
        else:
            print("\\n❌ ALL METHODS FAILED")
            exit(1)
    
    print("\\n🎉 EA SUCCESSFULLY TRANSFERRED TO AWS SERVER!")
    print("\\nFile location: C:\\\\MT5_Farm\\\\EA.mq5")
    print("\\nNext steps:")
    print("1. Install MT5 instances on AWS server")
    print("2. Copy EA to each MT5 Expert Advisors folder")
    print("3. Compile in MetaEditor")
    print("4. Attach to charts and enable AutoTrading")