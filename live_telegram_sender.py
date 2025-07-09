#!/usr/bin/env python3
"""
LIVE TELEGRAM SENDER - Sends production signals to Telegram
"""

import sqlite3
import time
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

class LiveTelegramSender:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        
        # Telegram config
        self.bot_token = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
        self.chat_id = "-1002581996861"
        
        # Track sent signals to avoid duplicates
        self.sent_signals = set()
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/live_telegram.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def send_telegram_message(self, message: str) -> bool:
        """Send message to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Telegram send error: {e}")
            return False
            
    def format_signal_message(self, signal: Dict) -> str:
        """Format signal for Telegram"""
        
        # Get TCS tier emoji
        tcs = signal['tcs_score']
        if tcs >= 85:
            tier_emoji = "💎"
            tier_name = "SNIPER"
        elif tcs >= 80:
            tier_emoji = "⭐"
            tier_name = "PRECISION"
        elif tcs >= 75:
            tier_emoji = "🎯"
            tier_name = "STANDARD"
        else:
            tier_emoji = "⚠️"
            tier_name = "RISKY"
            
        # Direction emoji
        direction_emoji = "🟢" if signal['direction'] == "BUY" else "🔴"
        
        # Calculate expiry time
        try:
            expires_at = datetime.fromisoformat(signal['expires_at'].replace('Z', '+00:00'))
            expires_minutes = int((expires_at - datetime.now()).total_seconds() / 60)
        except:
            expires_minutes = 15  # Default
        
        # Format message
        message = f"""🚨 **LIVE SIGNAL DETECTED**

{tier_emoji} **{tier_name}** | {signal['symbol']} | {direction_emoji} {signal['direction']}
**TCS**: {tcs}% | **R:R**: {signal['risk_reward']}

📍 **Entry**: {signal['entry_price']}
🛑 **Stop**: {signal['stop_loss']}
🎯 **Target**: {signal['take_profit']}

⏰ **Expires**: {expires_minutes} minutes
📊 **Source**: Live Production Engine

*Trade at your own risk. Past performance doesn't guarantee future results.*"""

        return message
        
    def get_new_signals(self) -> List[Dict]:
        """Get new signals from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get signals from last 5 minutes that haven't been sent
            cursor.execute('''
            SELECT id, symbol, timestamp, direction, tcs_score, entry_price,
                   stop_loss, take_profit, risk_reward, expires_at, status
            FROM live_signals 
            WHERE source = 'production' 
            AND status = 'active'
            AND timestamp > datetime('now', '-5 minutes')
            ORDER BY timestamp DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            new_signals = []
            
            for row in results:
                signal_id = row[0]
                
                # Skip if already sent
                if signal_id in self.sent_signals:
                    continue
                    
                signal = {
                    'id': signal_id,
                    'symbol': row[1],
                    'timestamp': row[2],
                    'direction': row[3],
                    'tcs_score': row[4],
                    'entry_price': row[5],
                    'stop_loss': row[6],
                    'take_profit': row[7],
                    'risk_reward': row[8],
                    'expires_at': row[9],
                    'status': row[10]
                }
                
                new_signals.append(signal)
                
            return new_signals
            
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            return []
            
    def run_telegram_sender(self):
        """Run continuous Telegram signal sender"""
        self.logger.info("📱 LIVE TELEGRAM SENDER STARTED")
        
        while True:
            try:
                # Get new signals
                new_signals = self.get_new_signals()
                
                if new_signals:
                    self.logger.info(f"📨 Found {len(new_signals)} new signals")
                    
                    for signal in new_signals:
                        # Format and send message
                        message = self.format_signal_message(signal)
                        
                        if self.send_telegram_message(message):
                            self.sent_signals.add(signal['id'])
                            self.logger.info(f"✅ Sent signal {signal['id']}: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%)")
                        else:
                            self.logger.error(f"❌ Failed to send signal {signal['id']}")
                            
                    # Clean up old sent signals (keep last 100)
                    if len(self.sent_signals) > 100:
                        self.sent_signals = set(list(self.sent_signals)[-100:])
                        
                else:
                    self.logger.debug("No new signals to send")
                    
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                self.logger.info("📱 Telegram sender stopped")
                break
            except Exception as e:
                self.logger.error(f"Sender error: {e}")
                time.sleep(60)
                
    def test_telegram(self):
        """Test Telegram connection"""
        print("📱 TESTING LIVE TELEGRAM CONNECTION...")
        
        test_message = f"""🧪 **BITTEN LIVE SYSTEM TEST**

✅ Production Signal Engine: ONLINE
✅ Live Data Feed: ACTIVE  
✅ Telegram Integration: WORKING

📊 Test Time: {datetime.now().strftime('%H:%M:%S')}
🔧 Status: Ready for live signals

*This is a test message - live signals will follow this format*"""

        if self.send_telegram_message(test_message):
            print("✅ Telegram test message sent successfully")
            
            # Check for any pending signals
            signals = self.get_new_signals()
            if signals:
                print(f"📨 Found {len(signals)} pending signals")
                for signal in signals:
                    print(f"  - {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%)")
                    
                # Send the signals
                for signal in signals:
                    message = self.format_signal_message(signal)
                    if self.send_telegram_message(message):
                        self.sent_signals.add(signal['id'])
                        print(f"✅ Sent pending signal: {signal['symbol']} {signal['direction']}")
                    time.sleep(2)  # Delay between messages
                    
            else:
                print("📭 No pending signals")
                
            return True
        else:
            print("❌ Telegram test failed")
            return False

if __name__ == "__main__":
    sender = LiveTelegramSender()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            sender.test_telegram()
        elif sys.argv[1] == "run":
            sender.run_telegram_sender()
    else:
        print("Usage:")
        print("  python3 live_telegram_sender.py test  - Test and send pending signals")
        print("  python3 live_telegram_sender.py run   - Run continuous sender")