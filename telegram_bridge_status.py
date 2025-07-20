#!/usr/bin/env python3
"""
TELEGRAM BRIDGE STATUS COMMAND
Adds /bridge command to production bot for monitoring
"""

import json
import datetime
from pathlib import Path
from production_bridge_tunnel import get_production_tunnel

class TelegramBridgeStatus:
    """Telegram bridge status monitoring"""
    
    def __init__(self):
        self.heartbeat_file = Path("/var/run/bridge_troll_heartbeat.txt")
        self.status_file = Path("/var/run/bridge_troll_status.json")
        self.tunnel = get_production_tunnel()
    
    def get_heartbeat_status(self) -> dict:
        """Get heartbeat status from daemon"""
        try:
            if not self.heartbeat_file.exists():
                return {
                    "status": "❌ OFFLINE",
                    "last_heartbeat": "No heartbeat file found",
                    "seconds_ago": "N/A"
                }
            
            # Read heartbeat file
            with open(self.heartbeat_file, 'r') as f:
                heartbeat_line = f.read().strip()
            
            # Parse timestamp
            if "[HEARTBEAT]" in heartbeat_line:
                timestamp_str = heartbeat_line.split("[HEARTBEAT]")[1].strip()
                heartbeat_time = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                # Calculate seconds ago
                now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                seconds_ago = int((now - heartbeat_time).total_seconds())
                
                if seconds_ago < 60:
                    status = "🟢 ONLINE"
                elif seconds_ago < 300:
                    status = "🟡 DELAYED"
                else:
                    status = "🔴 STALE"
                
                return {
                    "status": status,
                    "last_heartbeat": heartbeat_time.strftime("%H:%M:%S UTC"),
                    "seconds_ago": seconds_ago
                }
            else:
                return {
                    "status": "❌ INVALID",
                    "last_heartbeat": "Invalid heartbeat format",
                    "seconds_ago": "N/A"
                }
                
        except Exception as e:
            return {
                "status": "❌ ERROR",
                "last_heartbeat": f"Error reading heartbeat: {e}",
                "seconds_ago": "N/A"
            }
    
    def get_bridge_details(self) -> dict:
        """Get detailed bridge information"""
        try:
            bridge_status = self.tunnel.get_bridge_status()
            
            return {
                "aws_server": bridge_status["connection_details"]["server"],
                "primary_port": bridge_status["connection_details"]["primary_port"],
                "backup_ports": bridge_status["connection_details"]["backup_ports"],
                "bridge_status": bridge_status["bridge_tunnel"]["status"],
                "response_time": bridge_status["bridge_health"]["response_time"],
                "signal_files": bridge_status["bridge_health"]["signal_files_count"],
                "supported_symbols": len(bridge_status["capabilities"]["supported_symbols"])
            }
        except Exception as e:
            return {
                "error": str(e),
                "aws_server": "3.145.84.187",
                "primary_port": 5555,
                "bridge_status": "ERROR"
            }
    
    def get_account_info(self, user_id: str = None) -> dict:
        """Get MT5 account information"""
        try:
            from src.bitten_core.fire_router import FireRouter
            router = FireRouter()
            
            ping_result = router.ping_bridge(user_id or "843859")
            
            if ping_result.get("success"):
                account_info = ping_result.get("account_info", {})
                return {
                    "connection": "🟢 CONNECTED",
                    "account_id": account_info.get("login", "Unknown"),
                    "balance": account_info.get("balance", "Unknown"),
                    "server": account_info.get("server", "Unknown"),
                    "currency": account_info.get("currency", "USD")
                }
            else:
                return {
                    "connection": "🔴 DISCONNECTED",
                    "account_id": user_id or "843859",
                    "balance": "Unavailable",
                    "server": "Coinexx-Demo",
                    "currency": "USD"
                }
        except Exception as e:
            return {
                "connection": "❌ ERROR",
                "error": str(e),
                "account_id": user_id or "843859"
            }
    
    def generate_bridge_status_message(self, user_id: str = None) -> str:
        """Generate comprehensive bridge status message"""
        
        heartbeat = self.get_heartbeat_status()
        bridge_details = self.get_bridge_details()
        account_info = self.get_account_info(user_id)
        
        # Build status message
        message = f"""
🏰 **BRIDGE FORTRESS STATUS**

💓 **Bridge Heartbeat**: {heartbeat["status"]}
⏱️ **Last Pulse**: {heartbeat["last_heartbeat"]} ({heartbeat["seconds_ago"]}s ago)

🌉 **AWS Bridge**: {bridge_details.get("bridge_status", "Unknown")}
🖥️ **Server**: {bridge_details.get("aws_server", "Unknown")}:{bridge_details.get("primary_port", "Unknown")}
⚡ **Response Time**: {bridge_details.get("response_time", "Unknown"):.3f}s
📁 **Signal Files**: {bridge_details.get("signal_files", "Unknown")}
💱 **Supported Pairs**: {bridge_details.get("supported_symbols", "Unknown")}

🏦 **MT5 Account**: {account_info["connection"]}
🆔 **Account ID**: {account_info["account_id"]}
💰 **Balance**: ${account_info.get("balance", "Unknown")}
🖥️ **Server**: {account_info.get("server", "Unknown")}

🎯 **System Status**: {"✅ OPERATIONAL" if heartbeat["status"] == "🟢 ONLINE" and bridge_details.get("bridge_status") == "OPERATIONAL" else "⚠️ ISSUES DETECTED"}
"""
        
        # Add warnings if needed
        if heartbeat["status"] != "🟢 ONLINE":
            message += "\n⚠️ **WARNING**: Bridge heartbeat issues detected"
        
        if bridge_details.get("bridge_status") != "OPERATIONAL":
            message += "\n⚠️ **WARNING**: AWS bridge connectivity issues"
        
        if account_info["connection"] != "🟢 CONNECTED":
            message += "\n⚠️ **WARNING**: MT5 account connection issues"
        
        return message

# Global bridge status instance
BRIDGE_STATUS = TelegramBridgeStatus()

def get_bridge_status_message(user_id: str = None) -> str:
    """Get bridge status message for Telegram"""
    return BRIDGE_STATUS.generate_bridge_status_message(user_id)

def add_bridge_command_to_bot(bot_instance):
    """Add /bridge command to existing bot"""
    
    @bot_instance.message_handler(commands=['bridge'])
    def handle_bridge_command(message):
        """Handle /bridge command"""
        try:
            user_id = str(message.from_user.id)
            status_message = get_bridge_status_message(user_id)
            bot_instance.reply_to(message, status_message, parse_mode='Markdown')
        except Exception as e:
            bot_instance.reply_to(message, f"❌ Bridge status error: {e}")

if __name__ == "__main__":
    # Test bridge status
    status = get_bridge_status_message("843859")
    print(status)