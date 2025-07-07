#!/usr/bin/env python3
"""Demo BITTEN Live Trading System - Shows the complete flow"""

import asyncio
import json
import time
import random
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import urllib.parse

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
WEBAPP_URL = 'https://joinbitten.com/mission'

class SimulatedMarketData:
    """Simulated market data for demo"""
    
    def __init__(self):
        self.base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2750,
            'USDJPY': 150.50,
            'AUDUSD': 0.6550
        }
        
    def get_price(self, symbol):
        """Get simulated price with realistic movement"""
        base = self.base_prices[symbol]
        movement = random.gauss(0, 0.0002)
        price = base * (1 + movement)
        
        spread = 0.0002 if 'JPY' not in symbol else 0.02
        
        return {
            'bid': round(price - spread/2, 5),
            'ask': round(price + spread/2, 5),
            'mid': round(price, 5)
        }
    
    def should_signal(self):
        """Randomly decide if we should generate a signal"""
        return random.random() < 0.1  # 10% chance per check

async def demo_live_system():
    """Demo the complete BITTEN flow"""
    
    print("🚀 BITTEN Live Trading System Demo")
    print("=" * 50)
    print("📊 Market Data: Simulated")
    print("📱 Telegram: Connected")
    print("🌐 WebApp: joinbitten.com/mission")
    print("=" * 50)
    
    # Initialize components
    market = SimulatedMarketData()
    bot = Bot(token=BOT_TOKEN)
    
    # Send startup notification
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🟢 **BITTEN System Online**\n\nLive signal detection active.\nMonitoring: EUR/USD, GBP/USD, USD/JPY, AUD/USD",
            parse_mode=ParseMode.MARKDOWN
        )
        print("✅ Startup notification sent")
    except Exception as e:
        print(f"❌ Could not send startup notification: {e}")
    
    print("\n📡 Monitoring markets for signals...")
    print("(Signals will appear randomly for demo)\n")
    
    # Monitor loop
    checks = 0
    signals_sent = 0
    
    try:
        while True:
            checks += 1
            
            # Get current prices
            prices = {}
            for symbol in market.base_prices.keys():
                prices[symbol] = market.get_price(symbol)
            
            # Display current prices
            price_line = " | ".join([f"{sym}: {p['bid']}/{p['ask']}" for sym, p in prices.items()])
            print(f"[{checks:03d}] {price_line}", end='\r')
            
            # Check if we should generate a signal
            if market.should_signal() and signals_sent < 3:  # Limit to 3 signals for demo
                # Pick random symbol
                symbol = random.choice(list(prices.keys()))
                direction = random.choice(['BUY', 'SELL'])
                confidence = random.randint(70, 95)
                
                print(f"\n\n🎯 SIGNAL DETECTED!")
                print(f"Symbol: {symbol}")
                print(f"Direction: {direction}")
                print(f"Confidence: {confidence}%")
                
                # Send signal alert
                await send_signal_alert(symbol, direction, confidence, prices[symbol])
                signals_sent += 1
                
                print(f"\n✅ Signal {signals_sent}/3 sent!")
                print("\n📡 Continuing to monitor...\n")
            
            # Wait before next check
            await asyncio.sleep(2)
            
            # Stop after 60 checks or 3 signals
            if checks >= 60 or signals_sent >= 3:
                break
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring stopped by user")
    
    # Send shutdown notification
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🔴 **BITTEN System Offline**\n\nDemo complete.\nSignals sent: {signals_sent}\nChecks performed: {checks}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    print(f"\n\n📊 Demo Summary:")
    print(f"- Checks performed: {checks}")
    print(f"- Signals sent: {signals_sent}")
    print(f"- System status: Demo complete")

async def send_signal_alert(symbol, direction, confidence, price_data):
    """Send signal alert to Telegram"""
    bot = Bot(token=BOT_TOKEN)
    
    # Generate operation name
    operation_names = ['DAWN RAID', 'VORTEX AMBUSH', 'LIGHTNING STRIKE', 'SHADOW PIERCE']
    operation = random.choice(operation_names)
    
    # Brief alert message (2-3 lines as per spec)
    alert_message = f"""⚡ **SIGNAL DETECTED**
{symbol} | {direction} | {confidence}% confidence
⏰ Expires in 10 minutes"""
    
    # Calculate SL/TP
    pip_multiplier = 0.0001 if 'JPY' not in symbol else 0.01
    
    if direction == 'BUY':
        entry = price_data['ask']
        sl = round(entry - (20 * pip_multiplier), 5)
        tp = round(entry + (30 * pip_multiplier), 5)
    else:
        entry = price_data['bid']
        sl = round(entry + (20 * pip_multiplier), 5)
        tp = round(entry - (30 * pip_multiplier), 5)
    
    # Signal data for WebApp
    signal_data = {
        'signal_id': f'demo_{int(time.time())}',
        'symbol': symbol,
        'direction': direction,
        'entry_price': entry,
        'stop_loss': sl,
        'take_profit': tp,
        'confidence': confidence,
        'risk_pips': 20,
        'reward_pips': 30,
        'operation_name': operation,
        'expires_at': int(time.time()) + 600
    }
    
    # Encode data for URL
    encoded_data = urllib.parse.quote(json.dumps(signal_data))
    
    # Create keyboard with VIEW INTEL button
    keyboard = [[
        InlineKeyboardButton(
            "🎯 VIEW INTEL",
            url=f"{WEBAPP_URL}?data={encoded_data}"
        )
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=alert_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"\n❌ Error sending alert: {e}")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║         BITTEN DEMO SYSTEM           ║
    ║                                      ║
    ║  Demonstrates the complete flow:     ║
    ║  • Live market monitoring            ║
    ║  • Signal detection                  ║
    ║  • Telegram alerts                   ║
    ║  • WebApp mission briefings          ║
    ║                                      ║
    ║  Signals will appear randomly        ║
    ║  for demonstration purposes          ║
    ╚══════════════════════════════════════╝
    
    Starting in 3 seconds...
    """)
    
    asyncio.sleep(3)
    asyncio.run(demo_live_system())