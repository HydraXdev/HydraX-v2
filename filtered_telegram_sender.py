#!/usr/bin/env python3
"""
FILTERED TELEGRAM SENDER - Sends ONLY quality signals with proper filtering
Maximum 20-30 signals per day (1-2 per hour) for usability
"""

import sqlite3
import time
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

class FilteredTelegramSender:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        
        # Telegram config
        self.bot_token = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
        self.chat_id = "-1002581996861"
        
        # Track sent signals to avoid duplicates
        self.sent_signals = set()
        
        # CRITICAL FILTERING PARAMETERS
        self.min_tcs_threshold = 85  # Only send 85%+ TCS signals
        self.max_signals_per_hour = 2  # Maximum 2 signals per hour
        self.max_signals_per_day = 30  # Maximum 30 signals per day
        self.min_signal_gap_minutes = 20  # Minimum 20 minutes between signals
        
        # Track timing
        self.last_signal_time = None
        self.signals_sent_today = 0
        self.signals_sent_this_hour = 0
        self.current_hour = datetime.now().hour
        self.current_day = datetime.now().date()
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/filtered_telegram.log'),
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
    
    def should_send_signal(self, signal: Dict) -> tuple:
        """Check if signal meets quality and timing filters"""
        
        now = datetime.now()
        
        # Check daily reset
        if now.date() != self.current_day:
            self.signals_sent_today = 0
            self.current_day = now.date()
            self.logger.info(f"📅 New day - reset daily count")
        
        # Check hourly reset
        if now.hour != self.current_hour:
            self.signals_sent_this_hour = 0
            self.current_hour = now.hour
            self.logger.info(f"🕐 New hour - reset hourly count")
        
        # FILTER 1: TCS Quality - Only 85%+ signals
        tcs = signal['tcs_score']
        if tcs < self.min_tcs_threshold:
            return False, f"TCS {tcs}% below threshold {self.min_tcs_threshold}%"
        
        # FILTER 2: Daily limit
        if self.signals_sent_today >= self.max_signals_per_day:
            return False, f"Daily limit reached ({self.signals_sent_today}/{self.max_signals_per_day})"
        
        # FILTER 3: Hourly limit
        if self.signals_sent_this_hour >= self.max_signals_per_hour:
            return False, f"Hourly limit reached ({self.signals_sent_this_hour}/{self.max_signals_per_hour})"
        
        # FILTER 4: Minimum gap between signals
        if self.last_signal_time:
            time_diff = (now - self.last_signal_time).total_seconds() / 60
            if time_diff < self.min_signal_gap_minutes:
                return False, f"Too soon - need {self.min_signal_gap_minutes - time_diff:.1f} more minutes"
        
        return True, "APPROVED"
    
    def create_sniper_alert(self, tcs_score, signal_id, symbol):
        """SNIPER format for high quality signals"""
        text = f"⚡ SNIPER OPS ⚡ [{tcs_score}%]\n🎖️ {symbol} ELITE ACCESS"
        
        keyboard = {
            "inline_keyboard": [[{
                "text": "VIEW INTEL", 
                "url": f"https://joinbitten.com/hud?signal={signal_id}"
            }]]
        }
        
        return {"text": text, "keyboard": keyboard}
        
    def format_signal_alert(self, signal: Dict) -> Dict:
        """Format signal using SNIPER format (only high quality signals get through)"""
        
        tcs = signal['tcs_score']
        signal_id = signal['id']
        symbol = signal['symbol']
        
        # All filtered signals are SNIPER quality (85%+)
        return self.create_sniper_alert(tcs, signal_id, symbol)
        
    def get_new_signals(self) -> List[Dict]:
        """Get new high-quality signals from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get high-quality signals from last 10 minutes that haven't been sent
            cursor.execute('''
            SELECT id, symbol, timestamp, direction, tcs_score, entry_price,
                   stop_loss, take_profit, risk_reward, expires_at, status
            FROM live_signals 
            WHERE source = 'production' 
            AND status = 'active'
            AND tcs_score >= 85
            AND timestamp > datetime('now', '-10 minutes')
            ORDER BY tcs_score DESC, timestamp DESC
            LIMIT 50
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
        """Run filtered Telegram signal sender"""
        self.logger.info("🎯 FILTERED TELEGRAM SENDER STARTED")
        self.logger.info(f"🔥 FILTERS: TCS ≥{self.min_tcs_threshold}%, Max {self.max_signals_per_day}/day, {self.max_signals_per_hour}/hour")
        
        while True:
            try:
                # Get potential signals
                candidate_signals = self.get_new_signals()
                
                if candidate_signals:
                    self.logger.info(f"🔍 Found {len(candidate_signals)} candidate signals")
                    
                    sent_this_cycle = 0
                    
                    for signal in candidate_signals:
                        # Apply quality and timing filters
                        should_send, reason = self.should_send_signal(signal)
                        
                        if should_send:
                            # Format and send message
                            alert_data = self.format_signal_alert(signal)
                            
                            if self.send_telegram_message(alert_data["text"], alert_data["keyboard"]):
                                self.sent_signals.add(signal['id'])
                                self.last_signal_time = datetime.now()
                                self.signals_sent_today += 1
                                self.signals_sent_this_hour += 1
                                sent_this_cycle += 1
                                
                                self.logger.info(f"✅ SENT SNIPER signal {signal['id']}: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%)")
                                self.logger.info(f"📊 Today: {self.signals_sent_today}/{self.max_signals_per_day}, Hour: {self.signals_sent_this_hour}/{self.max_signals_per_hour}")
                                
                                # Only send one signal per cycle to avoid spam
                                break
                            else:
                                self.logger.error(f"❌ Failed to send signal {signal['id']}")
                        else:
                            self.logger.debug(f"🚫 Filtered signal {signal['id']}: {reason}")
                            
                    if sent_this_cycle == 0:
                        self.logger.debug(f"🔍 No signals passed filters from {len(candidate_signals)} candidates")
                        
                    # Clean up old sent signals (keep last 100)
                    if len(self.sent_signals) > 100:
                        self.sent_signals = set(list(self.sent_signals)[-100:])
                        
                else:
                    self.logger.debug("No candidate signals found")
                    
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.logger.info("🎯 Filtered Telegram sender stopped")
                break
            except Exception as e:
                self.logger.error(f"Sender error: {e}")
                time.sleep(60)
                
    def test_filtering(self):
        """Test filtering logic"""
        print("🎯 TESTING FILTERED TELEGRAM SENDER...")
        print(f"🔥 FILTERS:")
        print(f"  - Minimum TCS: {self.min_tcs_threshold}%")
        print(f"  - Max per day: {self.max_signals_per_day}")
        print(f"  - Max per hour: {self.max_signals_per_hour}")
        print(f"  - Min gap: {self.min_signal_gap_minutes} minutes")
        
        # Check for high-quality signals
        signals = self.get_new_signals()
        if signals:
            print(f"\n🔍 Found {len(signals)} candidate signals:")
            for signal in signals[:5]:  # Show top 5
                should_send, reason = self.should_send_signal(signal)
                status = "✅ PASS" if should_send else f"🚫 {reason}"
                print(f"  - {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%) - {status}")
                
            if any(self.should_send_signal(s)[0] for s in signals):
                print(f"\n📤 Would send highest quality signal")
            else:
                print(f"\n🚫 No signals pass filters")
        else:
            print("\n📭 No high-quality signals available")
            
        return True

if __name__ == "__main__":
    sender = FilteredTelegramSender()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            sender.test_filtering()
        elif sys.argv[1] == "run":
            sender.run_telegram_sender()
    else:
        print("Usage:")
        print("  python3 filtered_telegram_sender.py test  - Test filtering logic")
        print("  python3 filtered_telegram_sender.py run   - Run filtered sender")