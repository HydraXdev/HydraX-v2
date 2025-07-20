import os
#!/usr/bin/env python3
"""Properly configured signal bot with WebApp integration"""

import asyncio
import json
import urllib.parse
from datetime import datetime
import random
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", "DISABLED_FOR_SECURITY"))
CHAT_ID = int(os.getenv("CHAT_ID", "-1002581996861"))
WEBAPP_BASE_URL = "https://joinbitten.com"  # Now using HTTPS!

# HTTPS is now configured
HTTPS_WEBAPP = "https://joinbitten.com"

class SignalBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.patterns = [
            'LONDON_RAID', 'WALL_BREACH', 'SNIPER_NEST', 
            'AMBUSH_POINT', 'SUPPLY_DROP', 'PINCER_MOVE'
        ]
    
    async def send_signal_with_webapp(self, signal_data):
        """Send signal with proper WebApp button"""
        
        # Select random pattern
        pattern = random.choice(self.patterns)
        
        # Create webapp URL
        encoded_data = urllib.parse.quote(json.dumps(signal_data))
        webapp_url = f"{HTTPS_WEBAPP}/hud?data={encoded_data}"
        
        # Get pattern name for message
        pattern_names = {
            'LONDON_RAID': '🌅 LONDON RAID',
            'WALL_BREACH': '🧱 WALL BREACH',
            'SNIPER_NEST': '🎯 SNIPER\'S NEST',
            'AMBUSH_POINT': '🪤 AMBUSH POINT',
            'SUPPLY_DROP': '📦 SUPPLY DROP',
            'PINCER_MOVE': '🦾 PINCER MOVE'
        }
        
        # Create signal message
        symbol = signal_data['signal']['symbol']
        direction = signal_data['signal']['direction']
        tcs_score = signal_data['signal']['tcs_score']
        
        # Determine signal strength emoji
        if tcs_score >= 90:
            strength = "🔥🔥"
            confidence_text = "EXTREME"
        elif tcs_score >= 85:
            strength = "🔥"
            confidence_text = "HIGH"
        elif tcs_score >= 75:
            strength = "⭐"
            confidence_text = "MODERATE"
        else:
            strength = "⚠️"
            confidence_text = "LOW"
        
        message = (
            f"{strength} **{pattern_names[pattern]}**\n"
            f"{symbol} | {direction} | {tcs_score}% confidence\n"
            f"⏰ Expires in 10 minutes"
        )
        
        # Use URL button with HTTPS (WebApp requires specific setup)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="🎯 VIEW MISSION BRIEF",
                url=webapp_url
            )]
        ])
        
        # Send the signal
        await self.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        print(f"✅ Signal sent: {pattern} - {symbol} {direction} @ {tcs_score}%")
    
    async def send_test_signals(self):
        """Send multiple test signals"""
        
        # Test signal 1 - High confidence
        signal1 = {
            'user_id': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
            'signal': {
                'id': f'sig_{datetime.now().strftime("%H%M%S")}_1',
                'signal_type': 'PRECISION',
                'symbol': 'EUR/USD',
                'direction': 'BUY',
                'tcs_score': 88,
                'entry': 1.0850,
                'sl': 1.0820,
                'tp': 1.0910,
                'sl_pips': 30,
                'tp_pips': 60,
                'rr_ratio': 2.0,
                'expiry': 600
            }
        }
        
        await self.send_signal_with_webapp(signal1)
        await asyncio.sleep(3)
        
        # Test signal 2 - Sniper shot
        signal2 = {
            'user_id': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
            'signal': {
                'id': f'sig_{datetime.now().strftime("%H%M%S")}_2',
                'signal_type': 'SNIPER',
                'symbol': 'GBP/USD',
                'direction': 'SELL',
                'tcs_score': 92,
                'entry': 1.2650,
                'sl': 1.2680,
                'tp': 1.2590,
                'sl_pips': 30,
                'tp_pips': 60,
                'rr_ratio': 2.0,
                'expiry': 480
            }
        }
        
        await self.send_signal_with_webapp(signal2)
        await asyncio.sleep(3)
        
        # Test signal 3 - Lower confidence
        signal3 = {
            'user_id': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
            'signal': {
                'id': f'sig_{datetime.now().strftime("%H%M%S")}_3',
                'signal_type': 'STANDARD',
                'symbol': 'USD/JPY',
                'direction': 'BUY',
                'tcs_score': 75,
                'entry': 148.50,
                'sl': 148.20,
                'tp': 149.10,
                'sl_pips': 30,
                'tp_pips': 60,
                'rr_ratio': 2.0,
                'expiry': 300
            }
        }
        
        await self.send_signal_with_webapp(signal3)

async def main():
    """Main function"""
    bot = SignalBot()
    
    print("🚀 Sending test signals with HTTPS WebApp integration...")
    print("\n✅ Using HTTPS for direct access without preview!")
    print("📱 Mobile & Desktop: Click button → Direct to mission brief")
    
    await bot.send_test_signals()
    
    print("\n✅ Signals sent! Check Telegram.")
    print("🎯 Click 'VIEW MISSION BRIEF' to see the enhanced HUD")

if __name__ == "__main__":
    asyncio.run(main())