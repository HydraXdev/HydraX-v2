#!/usr/bin/env python3
"""
TACTICAL FILTERED SENDER - 83% ARCADE / 90% SNIPER thresholds
Your exact specifications for quality signal filtering
"""

import sqlite3
import time
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

class TacticalFilteredSender:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        
        # Telegram config
        self.bot_token = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
        self.chat_id = "-1002581996861"
        
        # Track sent signals to avoid duplicates
        self.sent_signals = set()
        
        # YOUR EXACT THRESHOLDS
        self.arcade_min_tcs = 83  # ARCADE: 83-89% TCS
        self.sniper_min_tcs = 90  # SNIPER: 90%+ TCS
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/tactical_filtered.log'),
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
    
    def create_arcade_alert(self, tcs_score, signal_id, symbol):
        """ARCADE format for 83-89% TCS signals"""
        text = f"🔫 RAPID ASSAULT [{tcs_score}%]\n🔥 {symbol} STRIKE 💥"
        
        keyboard = {
            "inline_keyboard": [[{
                "text": "MISSION BRIEF",
                "url": f"https://joinbitten.com/hud?signal={signal_id}"
            }]]
        }
        
        return {"text": text, "keyboard": keyboard}

    def create_sniper_alert(self, tcs_score, signal_id, symbol):
        """SNIPER format for 90%+ TCS signals"""
        text = f"⚡ SNIPER OPS ⚡ [{tcs_score}%]\n🎖️ {symbol} ELITE ACCESS"
        
        keyboard = {
            "inline_keyboard": [[{
                "text": "VIEW INTEL", 
                "url": f"https://joinbitten.com/hud?signal={signal_id}"
            }]]
        }
        
        return {"text": text, "keyboard": keyboard}
        
    def format_signal_alert(self, signal: Dict) -> Dict:
        """Format signal based on TCS thresholds"""
        
        tcs = signal['tcs_score']
        signal_id = signal['id']
        symbol = signal['symbol']
        
        # Determine signal type based on YOUR thresholds
        if tcs >= self.sniper_min_tcs:
            # SNIPER: 90%+ TCS
            return self.create_sniper_alert(tcs, signal_id, symbol)
        elif tcs >= self.arcade_min_tcs:
            # ARCADE: 83-89% TCS
            return self.create_arcade_alert(tcs, signal_id, symbol)
        else:
            # Below threshold - shouldn't happen due to database filter
            return None
        
    def get_quality_signals(self) -> List[Dict]:
        """Get signals meeting your TCS thresholds"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get signals meeting your 83%+ threshold from last 10 minutes
            cursor.execute('''
            SELECT id, symbol, timestamp, direction, tcs_score, entry_price,
                   stop_loss, take_profit, risk_reward, expires_at, status
            FROM live_signals 
            WHERE source = 'production' 
            AND status = 'active'
            AND tcs_score >= ?
            AND timestamp > datetime('now', '-10 minutes')
            ORDER BY tcs_score DESC, timestamp DESC
            ''', (self.arcade_min_tcs,))
            
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
        """Run tactical filtered Telegram sender"""
        self.logger.info("🎯 TACTICAL FILTERED SENDER STARTED")
        self.logger.info(f"🔫 ARCADE: {self.arcade_min_tcs}-{self.sniper_min_tcs-1}% TCS")
        self.logger.info(f"⚡ SNIPER: {self.sniper_min_tcs}%+ TCS")
        
        while True:
            try:
                # Get quality signals
                quality_signals = self.get_quality_signals()
                
                if quality_signals:
                    self.logger.info(f"🔍 Found {len(quality_signals)} quality signals")
                    
                    for signal in quality_signals:
                        # Format alert based on TCS
                        alert_data = self.format_signal_alert(signal)
                        
                        if alert_data:
                            if self.send_telegram_message(alert_data["text"], alert_data["keyboard"]):
                                self.sent_signals.add(signal['id'])
                                
                                # Determine signal type for logging
                                signal_type = "SNIPER" if signal['tcs_score'] >= self.sniper_min_tcs else "ARCADE"
                                
                                self.logger.info(f"✅ Sent {signal_type} signal {signal['id']}: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%)")
                            else:
                                self.logger.error(f"❌ Failed to send signal {signal['id']}")
                                
                        # Small delay to avoid rapid-fire
                        time.sleep(1)
                            
                    # Clean up old sent signals (keep last 200)
                    if len(self.sent_signals) > 200:
                        self.sent_signals = set(list(self.sent_signals)[-200:])
                        
                else:
                    self.logger.debug("No quality signals found")
                    
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.logger.info("🎯 Tactical filtered sender stopped")
                break
            except Exception as e:
                self.logger.error(f"Sender error: {e}")
                time.sleep(60)
                
    def test_filtering(self):
        """Test your filtering thresholds"""
        print("🎯 TESTING TACTICAL FILTERED SENDER")
        print("=" * 50)
        print(f"🔫 ARCADE: {self.arcade_min_tcs}-{self.sniper_min_tcs-1}% TCS")
        print(f"⚡ SNIPER: {self.sniper_min_tcs}%+ TCS")
        
        # Check for quality signals
        signals = self.get_quality_signals()
        if signals:
            print(f"\n🔍 Found {len(signals)} quality signals:")
            
            arcade_count = 0
            sniper_count = 0
            
            for signal in signals[:10]:  # Show top 10
                tcs = signal['tcs_score']
                if tcs >= self.sniper_min_tcs:
                    signal_type = "⚡ SNIPER"
                    sniper_count += 1
                else:
                    signal_type = "🔫 ARCADE"
                    arcade_count += 1
                    
                print(f"  - {signal_type} {signal['symbol']} {signal['direction']} (TCS: {tcs}%)")
                
            print(f"\n📊 BREAKDOWN:")
            print(f"🔫 ARCADE signals: {arcade_count}")
            print(f"⚡ SNIPER signals: {sniper_count}")
            print(f"📤 Total to send: {len(signals)}")
            
        else:
            print("\n📭 No quality signals available")
            
        return True

if __name__ == "__main__":
    sender = TacticalFilteredSender()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            sender.test_filtering()
        elif sys.argv[1] == "run":
            sender.run_telegram_sender()
    else:
        print("Usage:")
        print("  python3 tactical_filtered_sender.py test  - Test your thresholds")
        print("  python3 tactical_filtered_sender.py run   - Run tactical sender")