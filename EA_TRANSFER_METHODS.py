#!/usr/bin/env python3
"""
EA Transfer Methods - Multiple approaches to get EA to AWS server
30KB file should transfer easily through any of these methods
"""

import requests
import base64
import json
import time
from pathlib import Path

class EATransferManager:
    def __init__(self):
        self.ea_file = "/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5"
        self.target_server = "3.145.84.187"
        self.agent_port = 5555
        
    def method_1_direct_agent_upload(self):
        """Method 1: Direct upload via existing agent"""
        print("🔄 Method 1: Direct Agent Upload")
        
        try:
            # Read EA file
            with open(self.ea_file, 'rb') as f:
                ea_content = f.read()
            
            # Encode as base64
            ea_b64 = base64.b64encode(ea_content).decode('utf-8')
            
            # Prepare upload payload
            payload = {
                'action': 'upload_file',
                'filename': 'BITTENBridge_v3_ENHANCED.mq5',
                'destination': 'C:\\MT5_Farm\\EA.mq5',
                'content': ea_b64,
                'encoding': 'base64'
            }
            
            # Send to agent
            response = requests.post(
                f"http://{self.target_server}:{self.agent_port}/execute",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful: {result}")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Method 1 failed: {e}")
            return False
    
    def method_2_chunked_transfer(self):
        """Method 2: Split file into chunks for transfer"""
        print("🔄 Method 2: Chunked Transfer")
        
        try:
            # Read EA file
            with open(self.ea_file, 'rb') as f:
                ea_content = f.read()
            
            # Split into 10KB chunks
            chunk_size = 10240  # 10KB chunks
            chunks = [ea_content[i:i+chunk_size] for i in range(0, len(ea_content), chunk_size)]
            
            print(f"📦 Split into {len(chunks)} chunks of {chunk_size} bytes each")
            
            # Send initialization
            init_payload = {
                'action': 'init_chunked_upload',
                'filename': 'BITTENBridge_v3_ENHANCED.mq5',
                'destination': 'C:\\MT5_Farm\\EA.mq5',
                'total_chunks': len(chunks),
                'total_size': len(ea_content)
            }
            
            response = requests.post(
                f"http://{self.target_server}:{self.agent_port}/execute",
                json=init_payload,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Init failed: {response.status_code}")
                return False
            
            upload_id = response.json().get('upload_id', 'ea_upload')
            
            # Send chunks
            for i, chunk in enumerate(chunks):
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                
                chunk_payload = {
                    'action': 'upload_chunk',
                    'upload_id': upload_id,
                    'chunk_index': i,
                    'chunk_data': chunk_b64
                }
                
                response = requests.post(
                    f"http://{self.target_server}:{self.agent_port}/execute",
                    json=chunk_payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    print(f"✅ Chunk {i+1}/{len(chunks)} uploaded")
                else:
                    print(f"❌ Chunk {i+1} failed: {response.status_code}")
                    return False
                
                time.sleep(0.1)  # Small delay between chunks
            
            # Finalize upload
            finalize_payload = {
                'action': 'finalize_chunked_upload',
                'upload_id': upload_id
            }
            
            response = requests.post(
                f"http://{self.target_server}:{self.agent_port}/execute",
                json=finalize_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Chunked upload completed successfully")
                return True
            else:
                print(f"❌ Finalize failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Method 2 failed: {e}")
            return False
    
    def method_3_command_reconstruction(self):
        """Method 3: Send commands to reconstruct file"""
        print("🔄 Method 3: Command Reconstruction")
        
        try:
            # Read EA file
            with open(self.ea_file, 'r', encoding='utf-8', errors='ignore') as f:
                ea_content = f.read()
            
            # Escape special characters for batch file
            ea_escaped = ea_content.replace('"', '""').replace('%', '%%')
            
            # Split into lines (PowerShell handles long strings better)
            lines = ea_escaped.split('\n')
            
            print(f"📝 File has {len(lines)} lines")
            
            # Create PowerShell script to reconstruct file
            ps_commands = []
            ps_commands.append('# Clear any existing file')
            ps_commands.append('if (Test-Path "C:\\MT5_Farm\\EA.mq5") { Remove-Item "C:\\MT5_Farm\\EA.mq5" -Force }')
            ps_commands.append('# Create directory if needed')
            ps_commands.append('New-Item -ItemType Directory -Path "C:\\MT5_Farm" -Force | Out-Null')
            ps_commands.append('# Reconstruct file line by line')
            
            for i, line in enumerate(lines):
                if line.strip():  # Only non-empty lines
                    escaped_line = line.replace('"', '""').replace('`', '``').replace('$', '`$')
                    if i == 0:
                        ps_commands.append(f'Set-Content -Path "C:\\MT5_Farm\\EA.mq5" -Value "{escaped_line}" -Encoding UTF8')
                    else:
                        ps_commands.append(f'Add-Content -Path "C:\\MT5_Farm\\EA.mq5" -Value "{escaped_line}" -Encoding UTF8')
            
            # Send script in chunks
            script_chunks = []
            current_chunk = []
            
            for cmd in ps_commands:
                current_chunk.append(cmd)
                if len(current_chunk) >= 50:  # 50 commands per chunk
                    script_chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            
            if current_chunk:
                script_chunks.append('\n'.join(current_chunk))
            
            print(f"📦 Split script into {len(script_chunks)} chunks")
            
            # Execute script chunks
            for i, chunk in enumerate(script_chunks):
                payload = {
                    'action': 'execute_command',
                    'command': f'powershell -Command "{chunk}"',
                    'timeout': 30
                }
                
                response = requests.post(
                    f"http://{self.target_server}:{self.agent_port}/execute",
                    json=payload,
                    timeout=35
                )
                
                if response.status_code == 200:
                    print(f"✅ Script chunk {i+1}/{len(script_chunks)} executed")
                else:
                    print(f"❌ Script chunk {i+1} failed: {response.status_code}")
                    return False
                
                time.sleep(0.5)  # Delay between chunks
            
            # Verify file was created
            verify_payload = {
                'action': 'execute_command',
                'command': 'powershell -Command "if (Test-Path C:\\MT5_Farm\\EA.mq5) { Get-Item C:\\MT5_Farm\\EA.mq5 | Select-Object Name,Length } else { Write-Output FILE_NOT_FOUND }"'
            }
            
            response = requests.post(
                f"http://{self.target_server}:{self.agent_port}/execute",
                json=verify_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "FILE_NOT_FOUND" not in str(result):
                    print(f"✅ File reconstruction completed: {result}")
                    return True
                else:
                    print(f"❌ File not found after reconstruction")
                    return False
            
        except Exception as e:
            print(f"❌ Method 3 failed: {e}")
            return False
    
    def method_4_hex_transfer(self):
        """Method 4: Transfer as hex string"""
        print("🔄 Method 4: Hex Transfer")
        
        try:
            # Read EA file as binary
            with open(self.ea_file, 'rb') as f:
                ea_content = f.read()
            
            # Convert to hex
            ea_hex = ea_content.hex()
            print(f"📊 Hex string length: {len(ea_hex)} characters")
            
            # Split hex into manageable chunks
            chunk_size = 8000  # 8KB chunks in hex
            hex_chunks = [ea_hex[i:i+chunk_size] for i in range(0, len(ea_hex), chunk_size)]
            
            print(f"📦 Split into {len(hex_chunks)} hex chunks")
            
            # Create PowerShell script to reconstruct from hex
            ps_script = f"""
# Create directory
New-Item -ItemType Directory -Path "C:\\MT5_Farm" -Force | Out-Null

# Initialize empty file
Set-Content -Path "C:\\MT5_Farm\\EA_temp.hex" -Value "" -Encoding ASCII

# Append hex chunks (will be sent separately)
"""
            
            # Send initial script
            payload = {
                'action': 'execute_command',
                'command': f'powershell -Command "{ps_script}"'
            }
            
            response = requests.post(
                f"http://{self.target_server}:{self.agent_port}/execute",
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Init script failed: {response.status_code}")
                return False
            
            # Send hex chunks
            for i, chunk in enumerate(hex_chunks):
                append_payload = {
                    'action': 'execute_command',
                    'command': f'powershell -Command "Add-Content -Path C:\\MT5_Farm\\EA_temp.hex -Value \'{chunk}\' -NoNewline -Encoding ASCII"'
                }
                
                response = requests.post(
                    f"http://{self.target_server}:{self.agent_port}/execute",
                    json=append_payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    print(f"✅ Hex chunk {i+1}/{len(hex_chunks)} sent")
                else:
                    print(f"❌ Hex chunk {i+1} failed: {response.status_code}")
                    return False
                
                time.sleep(0.1)
            
            # Convert hex back to binary file
            convert_script = """
$hexContent = Get-Content -Path "C:\\MT5_Farm\\EA_temp.hex" -Raw
$bytes = for ($i = 0; $i -lt $hexContent.Length; $i += 2) {
    [Convert]::ToByte($hexContent.Substring($i, 2), 16)
}
[System.IO.File]::WriteAllBytes("C:\\MT5_Farm\\EA.mq5", $bytes)
Remove-Item "C:\\MT5_Farm\\EA_temp.hex" -Force
Get-Item "C:\\MT5_Farm\\EA.mq5" | Select-Object Name,Length
"""
            
            convert_payload = {
                'action': 'execute_command',
                'command': f'powershell -Command "{convert_script}"'
            }
            
            response = requests.post(
                f"http://{self.target_server}:{self.agent_port}/execute",
                json=convert_payload,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Hex conversion completed: {result}")
                return True
            else:
                print(f"❌ Hex conversion failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Method 4 failed: {e}")
            return False
    
    def method_5_download_bridge(self):
        """Method 5: Setup HTTP server and have agent download"""
        print("🔄 Method 5: Download Bridge")
        
        try:
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            import threading
            import os
            
            # Change to EA directory
            ea_dir = os.path.dirname(self.ea_file)
            original_cwd = os.getcwd()
            os.chdir(ea_dir)
            
            # Start HTTP server on port 9000
            server_port = 9000
            httpd = HTTPServer(('', server_port), SimpleHTTPRequestHandler)
            
            # Run server in background thread
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
            
            print(f"🌐 HTTP server started on port {server_port}")
            time.sleep(2)  # Let server start
            
            # Get this server's IP
            import subprocess
            try:
                result = subprocess.run(['curl', '-s', 'ifconfig.me'], capture_output=True, text=True, timeout=5)
                external_ip = result.stdout.strip()
            except:
                external_ip = "134.199.204.67"  # Fallback to likely IP
            
            # Have agent download the file
            download_script = f"""
New-Item -ItemType Directory -Path "C:\\MT5_Farm" -Force | Out-Null
try {{
    Invoke-WebRequest -Uri "http://{external_ip}:{server_port}/BITTENBridge_v3_ENHANCED.mq5" -OutFile "C:\\MT5_Farm\\EA.mq5" -TimeoutSec 30
    Get-Item "C:\\MT5_Farm\\EA.mq5" | Select-Object Name,Length,LastWriteTime
}} catch {{
    Write-Output "Download failed: $($_.Exception.Message)"
}}
"""
            
            download_payload = {
                'action': 'execute_command',
                'command': f'powershell -Command "{download_script}"',
                'timeout': 40
            }
            
            response = requests.post(
                f"http://{self.target_server}:{self.agent_port}/execute",
                json=download_payload,
                timeout=45
            )
            
            # Cleanup
            httpd.shutdown()
            os.chdir(original_cwd)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Download completed: {result}")
                return True
            else:
                print(f"❌ Download failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Method 5 failed: {e}")
            return False
    
    def try_all_methods(self):
        """Try all methods until one succeeds"""
        print("🚀 Attempting EA transfer using multiple methods...\n")
        
        methods = [
            ("Direct Agent Upload", self.method_1_direct_agent_upload),
            ("Chunked Transfer", self.method_2_chunked_transfer),
            ("Command Reconstruction", self.method_3_command_reconstruction),
            ("Hex Transfer", self.method_4_hex_transfer),
            ("Download Bridge", self.method_5_download_bridge)
        ]
        
        for method_name, method_func in methods:
            print(f"\n{'='*50}")
            print(f"Trying: {method_name}")
            print(f"{'='*50}")
            
            try:
                if method_func():
                    print(f"\n🎉 SUCCESS! EA transferred using: {method_name}")
                    return True
                else:
                    print(f"❌ {method_name} failed, trying next method...")
            except Exception as e:
                print(f"❌ {method_name} exception: {e}")
            
            time.sleep(2)  # Brief pause between methods
        
        print("\n💥 All methods failed. Manual intervention required.")
        return False

if __name__ == "__main__":
    manager = EATransferManager()
    success = manager.try_all_methods()
    
    if success:
        print("\n✅ EA transfer completed successfully!")
        print("Next steps:")
        print("1. Install MT5 instances on AWS server")
        print("2. Attach EA to all trading pairs")
        print("3. Enable AutoTrading")
        print("4. Start live trading system")
    else:
        print("\n❌ Transfer failed. Check network connectivity and agent status.")