#!/usr/bin/env python3
"""
BITTEN Live Signal System - Production
Uses MT5 live data with new alert format
"""

import json
import time
import sqlite3
import requests
import asyncio
from datetime import datetime
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BITTEN_LIVE')

# Telegram configuration
BOT_TOKEN = "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ"
CHAT_ID = "-1002581996861"

# Production alert formats
def create_arcade_alert(tcs_score, signal_id):
    """ARCADE format with MISSION BRIEF button"""
    text = f"🔫 RAPID ASSAULT [{tcs_score}%]\n🔥 STRIKE 💥"
    
    keyboard = {
        "inline_keyboard": [[{
            "text": "MISSION BRIEF",
            "web_app": {
                "url": f"https://joinbitten.com/mission?id={signal_id}"
            }
        }]]
    }
    
    return {"text": text, "keyboard": keyboard}

def create_sniper_alert(tcs_score, signal_id):
    """SNIPER format with VIEW INTEL button"""
    text = f"⚡ SNIPER OPS ⚡ [{tcs_score}%]\n🎖️ ELITE ACCESS"
    
    keyboard = {
        "inline_keyboard": [[{
            "text": "VIEW INTEL",
            "web_app": {
                "url": f"https://joinbitten.com/mission?id={signal_id}"
            }
        }]]
    }
    
    return {"text": text, "keyboard": keyboard}

def send_telegram_alert(alert_data):
    """Send alert to Telegram with inline button"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": alert_data["text"],
        "reply_markup": json.dumps(alert_data["keyboard"]),
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info(f"Alert sent successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
    
    return False

class MT5LiveSignalProcessor:
    """Process live MT5 data and generate signals"""
    
    def __init__(self):
        self.windows_agent_url = "http://3.145.84.187:5555"
        self.db_path = "/root/HydraX-v2/data/bitten_live.db"
        self.init_database()
        self.signal_count = 0
        
    def init_database(self):
        """Initialize live signal database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                tcs_score INTEGER NOT NULL,
                signal_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def check_mt5_data(self):
        """Check Windows agent for MT5 data"""
        try:
            # Check for response files from MT5
            check_cmd = 'Get-ChildItem -Path "C:\\MT5_Farm\\Responses" -Filter "*.json" -Recurse | Select-Object -First 10'
            
            resp = requests.post(
                f"{self.windows_agent_url}/execute",
                json={"command": check_cmd, "powershell": True},
                timeout=10
            )
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get('stdout'):
                    # Process MT5 data files
                    await self.process_mt5_files()
                    
        except Exception as e:
            logger.error(f"Error checking MT5 data: {e}")
            
    async def process_mt5_files(self):
        """Process MT5 response files"""
        # This would read actual MT5 tick data
        # For now, we'll use a placeholder
        logger.info("Processing MT5 data files...")
        
    async def generate_signal(self, market_data):
        """Generate signal from market data"""
        # Calculate TCS based on real indicators
        tcs_score = self.calculate_tcs(market_data)
        
        if tcs_score >= 70:  # Minimum threshold
            self.signal_count += 1
            signal_id = f"LIVE_{self.signal_count:06d}"
            
            # Determine signal type
            if tcs_score >= 85 and market_data.get('strong_trend'):
                # SNIPER signal
                alert = create_sniper_alert(tcs_score, signal_id)
                signal_type = "SNIPER"
            else:
                # ARCADE signal
                alert = create_arcade_alert(tcs_score, signal_id)
                signal_type = "ARCADE"
            
            # Store signal
            self.store_signal(signal_id, market_data, tcs_score, signal_type)
            
            # Send alert
            send_telegram_alert(alert)
            
            logger.info(f"Generated {signal_type} signal: {tcs_score}%")
            
    def calculate_tcs(self, market_data):
        """Calculate Trade Confidence Score from real data"""
        # This would use real technical indicators
        # Placeholder for now
        return 75
        
    def store_signal(self, signal_id, market_data, tcs_score, signal_type):
        """Store signal in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO live_signals 
            (signal_id, symbol, direction, entry_price, tcs_score, signal_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            signal_id,
            market_data.get('symbol', 'EURUSD'),
            market_data.get('direction', 'BUY'),
            market_data.get('price', 1.0850),
            tcs_score,
            signal_type
        ))
        
        conn.commit()
        conn.close()

async def main():
    """Main loop for live signal processing"""
    processor = MT5LiveSignalProcessor()
    
    logger.info("=== BITTEN LIVE SIGNAL SYSTEM STARTED ===")
    logger.info("Alert format: ARCADE (MISSION BRIEF) / SNIPER (VIEW INTEL)")
    logger.info("Waiting for MT5 live data...")
    
    # For testing, send one of each type
    test_arcade = create_arcade_alert(78, "TEST_001")
    test_sniper = create_sniper_alert(92, "TEST_002")
    
    logger.info("Sending test alerts...")
    send_telegram_alert(test_arcade)
    time.sleep(2)
    send_telegram_alert(test_sniper)
    
    # Main processing loop
    while True:
        try:
            # Check for MT5 data
            await processor.check_mt5_data()
            
            # Wait before next check
            await asyncio.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())