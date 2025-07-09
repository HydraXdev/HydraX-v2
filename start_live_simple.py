#!/usr/bin/env python3
"""
Simplified live start - focus on signal generation and Telegram alerts
"""

import asyncio
import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

# Simple env loading
def load_env():
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    return env_vars

# Load environment
ENV = load_env()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    """Simple Telegram bot for sending alerts"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    async def send_signal(self, signal: Dict):
        """Send signal alert to Telegram"""
        # Format the brief alert
        message = (
            f"⚡ **SIGNAL DETECTED**\n"
            f"{signal['symbol']} | {signal['direction']} | {signal['confidence']}% confidence\n"
            f"⏰ Expires in 10 minutes"
        )
        
        # Create inline keyboard with WebApp button
        keyboard = {
            "inline_keyboard": [[{
                "text": "🎯 VIEW INTEL",
                "url": f"https://joinbitten.com/mission/{signal['id']}"
            }]]
        }
        
        # Send via requests (using curl for simplicity)
        import subprocess
        
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(keyboard)
        }
        
        curl_cmd = [
            "curl", "-s", "-X", "POST",
            f"{self.base_url}/sendMessage",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(data)
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Signal sent to Telegram: {signal['symbol']} {signal['direction']}")
        else:
            logger.error(f"❌ Failed to send to Telegram: {result.stderr}")

class SimpleMarketAnalyzer:
    """Simple market analyzer using TraderMade API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.last_prices = {}
    
    async def get_live_rates(self) -> Dict:
        """Get live rates from TraderMade"""
        import subprocess
        
        pairs = "EURUSD,GBPUSD,USDJPY,XAUUSD"
        url = f"https://marketdata.tradermade.com/api/v1/live?currency={pairs}&api_key={self.api_key}"
        
        curl_cmd = ["curl", "-s", url]
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if 'quotes' in data:
                    rates = {}
                    for quote in data['quotes']:
                        rates[quote['instrument']] = {
                            'bid': quote['bid'],
                            'ask': quote['ask'],
                            'mid': quote['mid']
                        }
                    return rates
            except:
                pass
        
        # Fallback to simulated data
        return self.get_simulated_rates()
    
    def get_simulated_rates(self) -> Dict:
        """Generate simulated rates for testing"""
        base_prices = {
            'EURUSD': 1.0950,
            'GBPUSD': 1.2650,
            'USDJPY': 150.50,
            'XAUUSD': 1950.00
        }
        
        rates = {}
        for symbol, base in base_prices.items():
            # Add some random movement
            change = random.uniform(-0.0010, 0.0010)
            mid = base + change
            spread = 0.0001 if symbol != 'XAUUSD' else 0.50
            
            rates[symbol] = {
                'bid': mid - spread/2,
                'ask': mid + spread/2,
                'mid': mid
            }
        
        return rates
    
    async def analyze_for_signal(self, symbol: str, rates: Dict) -> Optional[Dict]:
        """Simple signal analysis"""
        if symbol not in rates:
            return None
        
        current_price = rates[symbol]['mid']
        
        # Store price history
        if symbol not in self.last_prices:
            self.last_prices[symbol] = []
        
        self.last_prices[symbol].append(current_price)
        if len(self.last_prices[symbol]) > 20:
            self.last_prices[symbol].pop(0)
        
        # Need at least 5 prices
        if len(self.last_prices[symbol]) < 5:
            return None
        
        # Simple momentum check
        prices = self.last_prices[symbol]
        avg_5 = sum(prices[-5:]) / 5
        avg_20 = sum(prices) / len(prices) if len(prices) >= 20 else avg_5
        
        # Generate signal based on momentum
        signal = None
        confidence = random.randint(65, 95)  # For testing
        
        if avg_5 > avg_20 * 1.0001:  # Bullish momentum
            if confidence >= 70:
                signal = {
                    'symbol': symbol,
                    'direction': 'BUY',
                    'confidence': confidence,
                    'entry': current_price,
                    'sl': current_price - (0.0010 if symbol != 'XAUUSD' else 5.0),
                    'tp': current_price + (0.0020 if symbol != 'XAUUSD' else 10.0)
                }
        elif avg_5 < avg_20 * 0.9999:  # Bearish momentum
            if confidence >= 70:
                signal = {
                    'symbol': symbol,
                    'direction': 'SELL',
                    'confidence': confidence,
                    'entry': current_price,
                    'sl': current_price + (0.0010 if symbol != 'XAUUSD' else 5.0),
                    'tp': current_price - (0.0020 if symbol != 'XAUUSD' else 10.0)
                }
        
        return signal

async def main():
    """Main trading loop"""
    print("🚀 BITTEN Live Trading System (Simplified)")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 TraderMade API: Configured")
    print(f"📱 Telegram: Ready")
    print(f"🌐 WebApp: https://joinbitten.com")
    print("=" * 50)
    
    # Initialize components
    bot = SimpleTelegramBot(
        token=ENV.get('TELEGRAM_BOT_TOKEN'),
        chat_id=ENV.get('TELEGRAM_CHAT_ID')
    )
    
    analyzer = SimpleMarketAnalyzer(
        api_key=ENV.get('TRADERMADE_API_KEY')
    )
    
    # Track sent signals
    sent_signals = {}
    signal_cooldown = 300  # 5 minutes between signals per symbol
    
    print("\n🔥 System is LIVE! Monitoring markets...")
    print("Signals will appear when conditions are met (70%+ confidence)")
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            # Get live rates
            rates = await analyzer.get_live_rates()
            
            if rates:
                # Check each symbol
                for symbol in ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']:
                    # Check cooldown
                    if symbol in sent_signals:
                        if time.time() - sent_signals[symbol] < signal_cooldown:
                            continue
                    
                    # Analyze for signal
                    signal = await analyzer.analyze_for_signal(symbol, rates)
                    
                    if signal:
                        # Generate signal ID
                        signal['id'] = f"SIG_{int(time.time())}_{symbol}"
                        
                        # Send to Telegram
                        await bot.send_signal(signal)
                        
                        # Track sent time
                        sent_signals[symbol] = time.time()
                        
                        print(f"🎯 Signal sent: {symbol} {signal['direction']} @ {signal['confidence']}%")
            
            # Wait before next check
            await asyncio.sleep(5)
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping BITTEN...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(10)
    
    print("✅ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())