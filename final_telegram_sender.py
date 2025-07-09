#!/usr/bin/env python3
"""
FINAL TELEGRAM SENDER - Uses the tactical format from this morning
Based on bitten_live_signals.py from 10:56 AM work session
"""

import sqlite3
import time
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

class FinalTelegramSender:
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
                logging.FileHandler('/root/HydraX-v2/logs/final_telegram.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def send_telegram_message(self, text: str, keyboard=None) -> bool:
        """Send message to Telegram with optional keyboard"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            if keyboard:
                data['reply_markup'] = json.dumps(keyboard)
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Telegram send error: {e}")
            return False
    
    def create_arcade_alert(self, tcs_score, signal_id, symbol=None):
        """ARCADE format with MISSION BRIEF button (from morning session)"""
        text = f"🔫 RAPID ASSAULT [{tcs_score}%]\n🔥 STRIKE 💥"
        
        keyboard = {
            "inline_keyboard": [[{
                "text": "MISSION BRIEF",
                "url": f"https://joinbitten.com/hud?signal={signal_id}"
            }]]
        }
        
        return {"text": text, "keyboard": keyboard}

    def create_sniper_alert(self, tcs_score, signal_id, symbol=None):
        """SNIPER format with VIEW INTEL button (from morning session)"""
        text = f"⚡ SNIPER OPS ⚡ [{tcs_score}%]\n🎖️ ELITE ACCESS"
        
        keyboard = {
            "inline_keyboard": [[{
                "text": "VIEW INTEL", 
                "url": f"https://joinbitten.com/hud?signal={signal_id}"
            }]]
        }
        
        return {"text": text, "keyboard": keyboard}
        
    def format_signal_alert(self, signal: Dict) -> Dict:
        """Format signal using tactical format from morning session"""
        
        tcs = signal['tcs_score']
        signal_id = signal['id']
        
        # Determine signal type based on TCS
        if tcs >= 85:
            # SNIPER signal
            return self.create_sniper_alert(tcs, signal_id, signal['symbol'])
        else:
            # ARCADE signal
            return self.create_arcade_alert(tcs, signal_id, signal['symbol'])
        
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
        self.logger.info("🔫 FINAL TELEGRAM SENDER STARTED (TACTICAL FORMAT)")
        
        while True:
            try:
                # Get new signals
                new_signals = self.get_new_signals()
                
                if new_signals:
                    self.logger.info(f"🔥 Found {len(new_signals)} new signals")
                    
                    for signal in new_signals:
                        # Format alert using tactical format
                        alert_data = self.format_signal_alert(signal)
                        
                        if self.send_telegram_message(alert_data["text"], alert_data["keyboard"]):
                            self.sent_signals.add(signal['id'])
                            signal_type = "SNIPER" if signal['tcs_score'] >= 85 else "ARCADE"
                            self.logger.info(f"✅ Sent {signal_type} signal {signal['id']}: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%)")
                        else:
                            self.logger.error(f"❌ Failed to send signal {signal['id']}")
                            
                        # Add delay between messages to avoid rate limiting
                        time.sleep(2)
                            
                    # Clean up old sent signals (keep last 100)
                    if len(self.sent_signals) > 100:
                        self.sent_signals = set(list(self.sent_signals)[-100:])
                        
                else:
                    self.logger.debug("No new signals to send")
                    
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                self.logger.info("🔫 Final Telegram sender stopped")
                break
            except Exception as e:
                self.logger.error(f"Sender error: {e}")
                time.sleep(60)
                
    def test_telegram(self):
        """Test Telegram connection with tactical format"""
        print("🔫 TESTING FINAL TACTICAL FORMAT...")
        
        # Test both signal types
        arcade_test = self.create_arcade_alert(78, "TEST_001")
        sniper_test = self.create_sniper_alert(92, "TEST_002")
        
        print("\n🎮 Testing ARCADE format...")
        if self.send_telegram_message(arcade_test["text"], arcade_test["keyboard"]):
            print("✅ ARCADE alert sent successfully")
        else:
            print("❌ ARCADE alert failed")
            
        time.sleep(2)
        
        print("\n🎯 Testing SNIPER format...")
        if self.send_telegram_message(sniper_test["text"], sniper_test["keyboard"]):
            print("✅ SNIPER alert sent successfully")
        else:
            print("❌ SNIPER alert failed")
            
        # Check for any pending live signals
        signals = self.get_new_signals()
        if signals:
            print(f"\n🔥 Found {len(signals)} pending signals")
            for signal in signals:
                print(f"  - {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%)")
                
        return True

if __name__ == "__main__":
    sender = FinalTelegramSender()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            sender.test_telegram()
        elif sys.argv[1] == "run":
            sender.run_telegram_sender()
    else:
        print("Usage:")
        print("  python3 final_telegram_sender.py test  - Test tactical format")
        print("  python3 final_telegram_sender.py run   - Run final sender")