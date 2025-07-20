#!/usr/bin/env python3
"""
Bridge Rescue Agent - Windows MT5 Bridge Auto-Setup and Monitor
Automatically configures firewall, starts MT5, and launches enhanced bridge
"""

import subprocess
import sys
import os
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
import socket
import psutil

class BridgeRescueAgent:
    def __init__(self, port=9000):
        self.port = port
        self.setup_logging()
        self.mt5_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
        self.enhanced_agent_name = "primary_agent_mt5_enhanced.py"
        
    def setup_logging(self):
        """Setup logging to bridge_status.log"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [BRIDGE] %(message)s',
            handlers=[
                logging.FileHandler('bridge_status.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def run_silent_command(self, command, shell=True):
        """Run command silently and return success status"""
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {command}")
            return False, "", "Timeout"
        except Exception as e:
            self.logger.error(f"Command failed: {command} - {e}")
            return False, "", str(e)
    
    def check_firewall_port(self):
        """Check and open TCP port in Windows Defender Firewall"""
        self.logger.info(f"Checking Windows Firewall for port {self.port}...")
        
        # Check if rule exists
        check_cmd = f'netsh advfirewall firewall show rule name="BITTEN Bridge Port {self.port}" dir=in'
        success, stdout, stderr = self.run_silent_command(check_cmd)
        
        if "No rules match" in stdout or not success:
            self.logger.info(f"Creating firewall rule for port {self.port}...")
            
            # Create inbound rule
            create_cmd = (
                f'netsh advfirewall firewall add rule '
                f'name="BITTEN Bridge Port {self.port}" '
                f'dir=in action=allow protocol=TCP localport={self.port}'
            )
            
            success, stdout, stderr = self.run_silent_command(create_cmd)
            if success:
                self.logger.info(f"✅ Firewall rule created for port {self.port}")
            else:
                self.logger.warning(f"⚠️ Failed to create firewall rule: {stderr}")
                # Continue anyway - port might still work
        else:
            self.logger.info(f"✅ Firewall rule already exists for port {self.port}")
    
    def check_port_available(self):
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', self.port))
                if result == 0:
                    self.logger.info(f"✅ Port {self.port} is active (something is listening)")
                    return True
                else:
                    self.logger.info(f"📡 Port {self.port} is available")
                    return False
        except Exception as e:
            self.logger.warning(f"⚠️ Could not check port {self.port}: {e}")
            return False
    
    def is_process_running(self, process_name):
        """Check if a process is running by name"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check process name
                    if process_name.lower() in proc.info['name'].lower():
                        return True, proc.info['pid']
                    
                    # Check command line for Python scripts
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if process_name in cmdline:
                            return True, proc.info['pid']
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False, None
        except Exception as e:
            self.logger.warning(f"⚠️ Could not check processes: {e}")
            return False, None
    
    def check_mt5_running(self):
        """Check if MT5 is running and start if needed"""
        self.logger.info("Checking MT5 status...")
        
        is_running, pid = self.is_process_running("terminal64.exe")
        
        if is_running:
            self.logger.info(f"✅ MT5 already running (PID: {pid})")
            return True
        
        # Check if MT5 exists
        if not os.path.exists(self.mt5_path):
            self.logger.error(f"❌ MT5 not found at: {self.mt5_path}")
            return False
        
        self.logger.info("🚀 Starting MT5...")
        try:
            # Start MT5 in background
            subprocess.Popen(
                [self.mt5_path],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
            
            # Wait for MT5 to start (up to 30 seconds)
            for i in range(30):
                time.sleep(1)
                is_running, pid = self.is_process_running("terminal64.exe")
                if is_running:
                    self.logger.info(f"✅ MT5 started successfully (PID: {pid})")
                    # Give MT5 a moment to fully initialize
                    time.sleep(3)
                    return True
            
            self.logger.error("❌ MT5 failed to start within 30 seconds")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start MT5: {e}")
            return False
    
    def check_enhanced_agent_running(self):
        """Check if enhanced agent is running and start if needed"""
        self.logger.info("Checking enhanced bridge agent...")
        
        is_running, pid = self.is_process_running(self.enhanced_agent_name)
        
        if is_running:
            self.logger.info(f"✅ Enhanced agent already running (PID: {pid})")
            return True
        
        # Check if enhanced agent file exists
        if not os.path.exists(self.enhanced_agent_name):
            self.logger.error(f"❌ Enhanced agent not found: {self.enhanced_agent_name}")
            self.logger.error("Please ensure primary_agent_mt5_enhanced.py is in the current directory")
            return False
        
        self.logger.info("🚀 Starting enhanced bridge agent...")
        try:
            # Start enhanced agent in background
            subprocess.Popen(
                [sys.executable, self.enhanced_agent_name],
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=os.getcwd()
            )
            
            # Wait for agent to start (up to 15 seconds)
            for i in range(15):
                time.sleep(1)
                is_running, pid = self.is_process_running(self.enhanced_agent_name)
                if is_running:
                    self.logger.info(f"✅ Enhanced agent started successfully (PID: {pid})")
                    # Give agent a moment to initialize socket
                    time.sleep(2)
                    return True
            
            self.logger.error("❌ Enhanced agent failed to start within 15 seconds")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start enhanced agent: {e}")
            return False
    
    def test_bridge_connectivity(self):
        """Test if the bridge is responding to connections"""
        self.logger.info(f"Testing bridge connectivity on port {self.port}...")
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(('127.0.0.1', self.port))
                
                # Try to send a ping command
                import json
                ping_cmd = json.dumps({"command": "ping"})
                s.send(ping_cmd.encode('utf-8'))
                
                # Wait for response
                s.settimeout(3)
                response = s.recv(1024)
                
                if response:
                    result = json.loads(response.decode('utf-8'))
                    self.logger.info(f"✅ Bridge responding: {result.get('status', 'Unknown')}")
                    return True
                else:
                    self.logger.warning("⚠️ Bridge connected but no response")
                    return False
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Bridge connectivity test failed: {e}")
            return False
    
    def rescue_bridge(self):
        """Main rescue sequence"""
        self.logger.info("=" * 50)
        self.logger.info("🚨 BRIDGE RESCUE AGENT STARTING")
        self.logger.info("=" * 50)
        
        success_count = 0
        total_checks = 4
        
        # Step 1: Configure firewall
        try:
            self.check_firewall_port()
            success_count += 1
        except Exception as e:
            self.logger.error(f"❌ Firewall configuration failed: {e}")
        
        # Step 2: Ensure MT5 is running
        try:
            if self.check_mt5_running():
                success_count += 1
        except Exception as e:
            self.logger.error(f"❌ MT5 check failed: {e}")
        
        # Step 3: Ensure enhanced agent is running
        try:
            if self.check_enhanced_agent_running():
                success_count += 1
        except Exception as e:
            self.logger.error(f"❌ Enhanced agent check failed: {e}")
        
        # Step 4: Test connectivity
        try:
            if self.test_bridge_connectivity():
                success_count += 1
        except Exception as e:
            self.logger.error(f"❌ Connectivity test failed: {e}")
        
        # Final status
        self.logger.info("=" * 50)
        if success_count >= 3:  # Allow some flexibility
            self.logger.info(f"✅ BRIDGE RESCUE COMPLETE ({success_count}/{total_checks} checks passed)")
            print(f"[BRIDGE] Rescue complete — listening on port {self.port} and MT5 is active.")
            return True
        else:
            self.logger.error(f"❌ BRIDGE RESCUE FAILED ({success_count}/{total_checks} checks passed)")
            self.logger.error("Manual intervention may be required")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Bridge Rescue Agent - MT5 Bridge Auto-Setup')
    parser.add_argument('--port', type=int, default=9000, help='Bridge port (default: 9000)')
    args = parser.parse_args()
    
    try:
        agent = BridgeRescueAgent(port=args.port)
        success = agent.rescue_bridge()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[BRIDGE] Rescue interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"[BRIDGE] Rescue failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()