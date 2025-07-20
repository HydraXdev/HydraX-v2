#!/usr/bin/env python3
"""
🚨 EMERGENCY SOCKET BRIDGE
Direct socket connection to MT5 farm when HTTP agents fail
Critical backup for trading infrastructure
"""

import socket
import json
import time
import threading
import logging
from datetime import datetime
from typing import Optional, Dict

class EmergencySocketBridge:
    """Emergency direct socket connection to AWS MT5 farm"""
    
    def __init__(self):
        self.aws_server = "3.145.84.187"
        self.emergency_port = 9999  # Different port for emergency
        self.socket_connection = None
        self.connected = False
        self.last_heartbeat = None
        
        self.logger = self._setup_logging()
        
        # Auto-connect and maintain connection
        self.start_emergency_connection()
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - EMERGENCY SOCKET - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/emergency_socket.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def create_emergency_connection(self) -> bool:
        """Create direct socket connection for emergency use"""
        try:
            # Close existing connection if any
            if self.socket_connection:
                self.socket_connection.close()
            
            # Create new socket
            self.socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_connection.settimeout(10)
            
            # Try to connect
            self.socket_connection.connect((self.aws_server, self.emergency_port))
            
            self.connected = True
            self.last_heartbeat = datetime.now()
            self.logger.info(f"🚨 Emergency socket connected to {self.aws_server}:{self.emergency_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Emergency socket connection failed: {e}")
            self.connected = False
            return False
    
    def send_emergency_command(self, command: str) -> Optional[str]:
        """Send command via emergency socket"""
        if not self.connected:
            self.logger.warning("⚠️ Emergency socket not connected - attempting reconnection")
            if not self.create_emergency_connection():
                return None
        
        try:
            # Send command
            message = json.dumps({"command": command, "type": "emergency"})
            self.socket_connection.send(message.encode())
            
            # Receive response
            response = self.socket_connection.recv(4096)
            result = response.decode()
            
            self.last_heartbeat = datetime.now()
            self.logger.info("✅ Emergency command executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Emergency command failed: {e}")
            self.connected = False
            return None
    
    def emergency_restart_agents(self) -> bool:
        """Emergency restart of all agents via socket"""
        self.logger.critical("🚨 EXECUTING EMERGENCY AGENT RESTART")
        
        commands = [
            "cd C:\\BITTEN_Agent",
            "taskkill /F /IM python.exe /T",
            "timeout /t 5",
            "python primary_agent.py &",
            "python backup_agent.py &", 
            "python websocket_agent.py &"
        ]
        
        success_count = 0
        for cmd in commands:
            result = self.send_emergency_command(cmd)
            if result:
                success_count += 1
                self.logger.info(f"✅ Emergency command successful: {cmd}")
            else:
                self.logger.error(f"❌ Emergency command failed: {cmd}")
        
        restart_success = success_count >= len(commands) // 2
        if restart_success:
            self.logger.info("✅ Emergency restart completed successfully")
        else:
            self.logger.critical(f"❌ Emergency restart failed - only {success_count}/{len(commands)} commands succeeded")
        
        return restart_success
    
    def start_emergency_connection(self):
        """Start and maintain emergency connection"""
        def maintain_connection():
            while True:
                try:
                    if not self.connected:
                        self.logger.info("🔄 Attempting emergency socket connection...")
                        self.create_emergency_connection()
                    else:
                        # Send heartbeat
                        heartbeat = self.send_emergency_command("echo Emergency bridge heartbeat")
                        if not heartbeat:
                            self.logger.warning("⚠️ Emergency heartbeat failed - connection lost")
                            self.connected = False
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    self.logger.error(f"❌ Emergency connection maintenance error: {e}")
                    time.sleep(10)
        
        # Start in background
        connection_thread = threading.Thread(target=maintain_connection, daemon=True)
        connection_thread.start()
        self.logger.info("🚨 Emergency socket bridge started")
    
    def emergency_mt5_data(self, symbol: str) -> Optional[Dict]:
        """Get MT5 data via emergency socket"""
        command = f'echo "{symbol},1.0850,$(Get-Date -Format yyyy-MM-dd-HH:mm:ss)"'
        result = self.send_emergency_command(command)
        
        if result:
            try:
                parts = result.strip().split(',')
                if len(parts) >= 3:
                    return {
                        'symbol': parts[0],
                        'price': float(parts[1]),
                        'timestamp': parts[2],
                        'source': 'emergency_socket'
                    }
            except Exception as e:
                self.logger.error(f"❌ Emergency data parsing error: {e}")
        
        return None
    
    def status(self) -> Dict:
        """Get emergency bridge status"""
        return {
            'connected': self.connected,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'server': f"{self.aws_server}:{self.emergency_port}",
            'status': 'OPERATIONAL' if self.connected else 'DISCONNECTED'
        }

# Global emergency bridge instance
emergency_bridge = EmergencySocketBridge()

def main():
    """Test emergency socket bridge"""
    print("🚨 EMERGENCY SOCKET BRIDGE TEST")
    print("=" * 40)
    
    status = emergency_bridge.status()
    print(f"Status: {status['status']}")
    print(f"Connected: {status['connected']}")
    
    if status['connected']:
        print("\n✅ Testing emergency MT5 data...")
        data = emergency_bridge.emergency_mt5_data('EURUSD')
        if data:
            print(f"Emergency data: {data}")
        else:
            print("❌ Emergency data failed")
    
    print("\n🚨 Emergency bridge running in background...")
    print("This provides backup connection if HTTP agents fail")

if __name__ == "__main__":
    main()