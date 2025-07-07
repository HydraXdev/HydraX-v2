#!/usr/bin/env python3
"""Test the live trading system with simulated data"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bitten_core.tradermade_client import TraderMadeClient
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
import json
import time

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
WEBAPP_URL = 'https://joinbitten.com/mission'

async def test_live_flow():
    """Test complete flow with simulated data"""
    
    print("🚀 Starting BITTEN Live Test")
    print("=" * 50)
    
    # 1. Initialize market data client (will use simulated data)
    market_client = TraderMadeClient()
    await market_client.connect()
    
    # 2. Monitor for signals
    print("\n📊 Monitoring for signals...")
    print("(Using simulated market data)")
    
    signal_sent = False
    iterations = 0
    
    while not signal_sent and iterations < 60:  # Try for 60 iterations
        # Get current rates
        rates = await market_client.get_live_rates(['EURUSD', 'GBPUSD'])
        
        # Simulate signal detection on iteration 10
        if iterations == 10:
            print(f"\n🎯 SIGNAL DETECTED!")
            print(f"EUR/USD BUY @ {rates['EURUSD']['ask']}")
            print(f"Confidence: 87%")
            
            # Send Telegram alert
            await send_signal_alert(rates['EURUSD'])
            signal_sent = True
        else:
            # Show we're monitoring
            if iterations % 5 == 0:
                print(f"Monitoring... EUR/USD: {rates['EURUSD']['bid']}/{rates['EURUSD']['ask']}", end='\r')
        
        iterations += 1
        await asyncio.sleep(1)
    
    # Keep running for a bit to show live updates
    print("\n\n📈 Continuing to monitor... (Press Ctrl+C to stop)")
    
    try:
        while True:
            rates = await market_client.get_live_rates(['EURUSD'])
            print(f"EUR/USD: {rates['EURUSD']['bid']}/{rates['EURUSD']['ask']}", end='\r')
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Stopping...")
    
    await market_client.close()

async def send_signal_alert(price_data):
    """Send test signal alert to Telegram"""
    bot = Bot(token=BOT_TOKEN)
    
    # Brief alert message
    alert_message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""
    
    # Signal data for WebApp
    signal_data = {
        'signal_id': f'test_{int(time.time())}',
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry_price': price_data['ask'],
        'stop_loss': round(price_data['ask'] - 0.0020, 5),
        'take_profit': round(price_data['ask'] + 0.0030, 5),
        'confidence': 87,
        'risk_pips': 20,
        'reward_pips': 30,
        'tier_required': 'NIBBLER',
        'expires_at': int(time.time()) + 600,
        'fire_mode': 'ARCADE',
        'operation_name': 'DAWN RAID'
    }
    
    # URL encode the data
    import urllib.parse
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
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text=alert_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        print(f"\n✅ Signal alert sent to Telegram!")
        print(f"Message ID: {message.message_id}")
        print("\n📱 User Flow:")
        print("1. User sees brief alert in Telegram")
        print("2. Clicks 'VIEW INTEL' to open mission briefing")
        print("3. Reviews full intel at joinbitten.com/mission")
        print("4. Clicks FIRE to execute trade")
        print("5. Confirmation updates on same page")
        
    except Exception as e:
        print(f"\n❌ Error sending alert: {e}")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║      BITTEN LIVE SYSTEM TEST         ║
    ║                                      ║
    ║  This will:                          ║
    ║  1. Connect to market data           ║
    ║  2. Monitor for signals              ║
    ║  3. Send test alert to Telegram      ║
    ║  4. Continue monitoring              ║
    ╚══════════════════════════════════════╝
    """)
    
    asyncio.run(test_live_flow())