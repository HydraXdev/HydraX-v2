#!/usr/bin/env python3
"""
Deploy Enhanced MT5 Bridge to AWS Server
Uploads and starts the enhanced primary agent with MT5 socket functionality
"""

import requests
import json
import time
from datetime import datetime

class MT5BridgeDeployer:
    def __init__(self):
        self.aws_server = "3.145.84.187"
        self.port = 5555
        self.base_url = f"http://{self.aws_server}:{self.port}"
        
    def test_connection(self):
        """Test connection to AWS server"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Connected to AWS server: {self.aws_server}:{self.port}")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def read_enhanced_agent_code(self):
        """Read the enhanced agent code"""
        try:
            with open('/root/HydraX-v2/bulletproof_agents/primary_agent_mt5_enhanced.py', 'r') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read enhanced agent code: {e}")
            return None
    
    def upload_enhanced_agent(self):
        """Upload enhanced agent to AWS server"""
        print("📤 Uploading enhanced MT5 bridge agent...")
        
        agent_code = self.read_enhanced_agent_code()
        if not agent_code:
            return False
        
        # Create upload command
        upload_command = f'''
        @"
{agent_code}
"@ | Out-File -FilePath "C:\\BITTEN_Agent\\primary_agent_mt5_enhanced.py" -Encoding UTF8
        echo "Enhanced agent uploaded: $(Get-Date)"
        '''
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"command": upload_command, "type": "powershell"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Enhanced agent uploaded successfully")
                    return True
                else:
                    print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Upload request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def install_mt5_dependencies(self):
        """Install MT5 dependencies if needed"""
        print("📦 Installing MT5 dependencies...")
        
        install_command = '''
        try {
            pip install MetaTrader5
            echo "MT5 dependencies installed successfully"
        } catch {
            echo "MT5 installation failed or already installed: $($_.Exception.Message)"
        }
        '''
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"command": install_command, "type": "powershell"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"📦 Dependencies result: {result.get('stdout', 'No output')}")
                return True
            else:
                print(f"❌ Dependencies install failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Dependencies error: {e}")
            return False
    
    def stop_current_agent(self):
        """Stop current primary agent"""
        print("🛑 Stopping current primary agent...")
        
        stop_command = '''
        try {
            Get-Process -Name "python" | Where-Object {$_.CommandLine -like "*primary_agent*"} | Stop-Process -Force
            echo "Primary agent stopped"
        } catch {
            echo "No primary agent running or stop failed: $($_.Exception.Message)"
        }
        '''
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"command": stop_command, "type": "powershell"},
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Current agent stopped")
                return True
            else:
                print(f"⚠️ Stop command failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ Stop error: {e}")
            return False
    
    def start_enhanced_agent(self):
        """Start the enhanced MT5 bridge agent"""
        print("🚀 Starting enhanced MT5 bridge agent...")
        
        start_command = '''
        try {
            cd C:\\BITTEN_Agent
            Start-Process python -ArgumentList "primary_agent_mt5_enhanced.py" -WindowStyle Hidden
            Start-Sleep -Seconds 3
            echo "Enhanced agent started successfully"
        } catch {
            echo "Failed to start enhanced agent: $($_.Exception.Message)"
        }
        '''
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"command": start_command, "type": "powershell"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🚀 Start result: {result.get('stdout', 'No output')}")
                return True
            else:
                print(f"❌ Start failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Start error: {e}")
            return False
    
    def test_socket_functionality(self):
        """Test the socket functionality"""
        print("🧪 Testing socket functionality...")
        
        # Wait for agent to start
        time.sleep(5)
        
        # Test ping command
        try:
            import socket
            
            # Test ping
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.aws_server, 9000))
            
            ping_command = json.dumps({"command": "ping"})
            sock.send(ping_command.encode('utf-8'))
            
            response = sock.recv(4096)
            ping_result = json.loads(response.decode('utf-8'))
            
            sock.close()
            
            print(f"✅ Ping test successful: {ping_result.get('status', 'Unknown')}")
            print(f"   Account: {ping_result.get('account', 'N/A')}")
            print(f"   Broker: {ping_result.get('broker', 'N/A')}")
            print(f"   Balance: {ping_result.get('balance', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Socket test failed: {e}")
            return False
    
    def deploy_full_system(self):
        """Deploy the complete enhanced MT5 bridge system"""
        print("🎯 DEPLOYING ENHANCED MT5 BRIDGE SYSTEM")
        print("=" * 50)
        
        # Step 1: Test connection
        if not self.test_connection():
            print("❌ Cannot connect to AWS server. Deployment aborted.")
            return False
        
        # Step 2: Install dependencies
        if not self.install_mt5_dependencies():
            print("⚠️ Dependencies installation failed, continuing anyway...")
        
        # Step 3: Upload enhanced agent
        if not self.upload_enhanced_agent():
            print("❌ Failed to upload enhanced agent. Deployment aborted.")
            return False
        
        # Step 4: Stop current agent (optional, may fail if none running)
        self.stop_current_agent()
        
        # Step 5: Start enhanced agent
        if not self.start_enhanced_agent():
            print("❌ Failed to start enhanced agent. Deployment failed.")
            return False
        
        # Step 6: Test functionality
        if not self.test_socket_functionality():
            print("⚠️ Socket functionality test failed")
            return False
        
        print("\n✅ DEPLOYMENT SUCCESSFUL!")
        print(f"🌐 HTTP API: {self.base_url}")
        print(f"🔌 Socket Bridge: {self.aws_server}:9000")
        print("📡 Ready for ping/fire commands")
        
        return True

def main():
    """Main deployment function"""
    deployer = MT5BridgeDeployer()
    
    print("🎯 Enhanced MT5 Bridge Deployment Tool")
    print("=" * 40)
    print(f"Target: {deployer.aws_server}:{deployer.port}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Deploy the system
    success = deployer.deploy_full_system()
    
    if success:
        print(f"\n🎉 DEPLOYMENT COMPLETE!")
        print(f"The enhanced MT5 bridge is now running on {deployer.aws_server}")
        print(f"Socket commands (ping/fire) available on port 9000")
        print(f"HTTP API continues on port 5555")
    else:
        print(f"\n❌ DEPLOYMENT FAILED!")
        print("Check the error messages above and try again")

if __name__ == "__main__":
    main()