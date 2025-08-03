#!/usr/bin/env python3
"""
Signal Relay System - Connects VENOM signal generator to BittenCore/Telegram
"""

import json
import time
import logging
import requests
from datetime import datetime
import threading
import os
import sys

# Add HydraX paths
sys.path.insert(0, '/root/HydraX-v2')
sys.path.insert(0, '/root/HydraX-v2/src')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SignalRelay')

# Import BittenCore
from src.bitten_core.bitten_core import BittenCore

class SignalRelay:
    """Relay signals from generator to users via BittenCore"""
    
    def __init__(self):
        self.bitten_core = BittenCore()
        self.last_signal_id = None
        self.signal_count = 0
        self.start_time = datetime.now()
        
        # Load user registry to get active users
        try:
            from src.bitten_core.user_registry_manager import UserRegistryManager
            self.user_registry = UserRegistryManager()
        except:
            logger.error("Failed to load user registry")
            self.user_registry = None
    
    def process_signal_file(self):
        """Process signals from the generated_signals.json file"""
        signal_file = '/root/HydraX-v2/generated_signals.json'
        
        if not os.path.exists(signal_file):
            logger.warning(f"Signal file not found: {signal_file}")
            return
        
        try:
            # Read the last signal
            with open(signal_file, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return
                
                # Process the last few signals
                for line in lines[-5:]:  # Last 5 signals
                    try:
                        signal = json.loads(line.strip())
                        
                        # Skip if already processed
                        if signal['signal_id'] == self.last_signal_id:
                            continue
                        
                        # Process this signal
                        self.process_signal(signal)
                        self.last_signal_id = signal['signal_id']
                        
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.error(f"Error processing signal: {e}")
                        
        except Exception as e:
            logger.error(f"Error reading signal file: {e}")
    
    def process_signal(self, signal_data: Dict):
        """Process and relay a signal to users"""
        try:
            logger.info(f"📡 Processing signal: {signal_data['signal_id']}")
            
            # Process through BittenCore
            result = self.bitten_core.process_signal(signal_data)
            
            if result.get('success'):
                self.signal_count += 1
                logger.info(f"✅ Signal processed: {signal_data['pair']} {signal_data['direction']} @ {signal_data['confidence']}%")
                
                # Get active users who should receive signals
                if self.user_registry:
                    active_users = self.get_active_users()
                    logger.info(f"📤 Broadcasting to {len(active_users)} active users")
                    
                    # Send signal to each active user via Telegram webhook
                    for user_id in active_users:
                        self.send_signal_to_user(user_id, signal_data)
                else:
                    logger.warning("User registry not available - cannot broadcast signals")
            else:
                logger.error(f"❌ Failed to process signal: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    def get_active_users(self) -> List[str]:
        """Get list of users who should receive signals"""
        try:
            if not self.user_registry:
                return []
            
            active_users = []
            
            # Get all registered users
            all_users = self.user_registry.get_all_users()
            
            for user_id, user_data in all_users.items():
                # Check if user is ready for signals
                if user_data.get('ready_for_fire', False):
                    # Check if user has valid tier (not PRESS_PASS for real signals)
                    tier = user_data.get('tier', 'NIBBLER')
                    if tier != 'PRESS_PASS':
                        active_users.append(str(user_id))
            
            return active_users
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def send_signal_to_user(self, user_id: str, signal_data: Dict):
        """Send signal to specific user via Telegram webhook"""
        try:
            # Format mission briefing
            message = self.format_mission_briefing(signal_data)
            
            # Send via Telegram webhook
            webhook_url = "https://telegram1.joinbitten.com/webhook/send-message"
            
            payload = {
                "chat_id": user_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ Signal sent to user {user_id}")
            else:
                logger.error(f"Failed to send signal to user {user_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending signal to user {user_id}: {e}")
    
    def format_mission_briefing(self, signal_data: Dict) -> str:
        """Format signal as mission briefing"""
        # Extract CITADEL data
        citadel = signal_data.get('citadel_shield', {})
        shield_score = citadel.get('score', 6.0)
        shield_class = citadel.get('classification', 'SHIELD_ACTIVE')
        
        # Format message
        message = f"""🎯 **[VENOM v7 Signal]**
🧠 Symbol: {signal_data['pair']}
📈 Direction: {signal_data['direction']}
🔥 Confidence: {signal_data['confidence']}%
🛡️ CITADEL: ✅ {shield_score}/10 [{shield_class}]
⏳ Expires in: 35 min

Reply: `/fire {signal_data['signal_id']}` to execute"""
        
        return message
    
    def run(self):
        """Main relay loop"""
        logger.info("🚀 Signal Relay System started")
        logger.info("📡 Monitoring for VENOM signals...")
        
        while True:
            try:
                # Process any new signals
                self.process_signal_file()
                
                # Show status every minute
                if self.signal_count > 0 and self.signal_count % 10 == 0:
                    uptime = datetime.now() - self.start_time
                    logger.info(f"📊 Status: {self.signal_count} signals relayed | Uptime: {uptime}")
                
                # Check every 5 seconds
                time.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Signal relay stopped by user")
                break
            except Exception as e:
                logger.error(f"Relay error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    relay = SignalRelay()
    relay.run()