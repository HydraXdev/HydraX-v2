#!/usr/bin/env python3
"""
Fixed Telegram Alert System with:
1. WebApp buttons (no confirmation)
2. Two different alert templates 
3. Tier-based HUD routing
"""

import asyncio
import json
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from datetime import datetime

class FixedTelegramAlerts:
    def __init__(self, bot_token, webapp_url="https://joinbitten.com"):
        self.bot = Bot(token=bot_token)
        self.webapp_url = webapp_url
    
    def create_mission_data(self, signal, user_tier="NIBBLER"):
        """Create mission data with tier-specific routing"""
        mission_data = {
            'mission_id': f"{signal['symbol']}_{int(datetime.now().timestamp())}",
            'signal': signal,
            'user_tier': user_tier,
            'timestamp': int(datetime.now().timestamp()),
            'template': f"{user_tier.lower()}_hud"  # nibbler_hud, fang_hud, commander_hud
        }
        return mission_data
    
    def format_sniper_alert(self, signal):
        """High-priority military-style alert for 80%+ TCS"""
        return (
            f"🔥🔥 **SNIPER SHOT** 🔥🔥\n"
            f"**{signal['symbol']} {signal['direction']}** | {signal['tcs_score']}% | R:R 2.0\n"
            f"⚡ HIGH PROBABILITY TARGET"
        )
    
    def format_rapid_alert(self, signal):
        """Standard alert for 65-79% TCS"""
        return (
            f"🎯 **RAPID ASSAULT**\n"
            f"{signal['symbol']} {signal['direction']} | {signal['tcs_score']}%\n"
            f"📊 {signal.get('session', 'LONDON')} Session"
        )
    
    def create_webapp_button(self, mission_data, alert_type):
        """Create WebApp button based on alert type"""
        encoded_data = urllib.parse.quote(json.dumps(mission_data))
        webapp_url = f"{self.webapp_url}/hud?data={encoded_data}"
        
        if alert_type == "sniper":
            button_text = "🎯 SNIPER MISSION"
        else:
            button_text = "📊 VIEW INTEL"
        
        return InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text=button_text,
                web_app=WebAppInfo(url=webapp_url)
            )
        ]])
    
    async def send_signal_alert(self, signal, chat_id, user_tier="NIBBLER"):
        """Send the appropriate alert based on TCS score"""
        try:
            # Create mission data with tier routing
            mission_data = self.create_mission_data(signal, user_tier)
            
            # Determine alert type and format
            if signal['tcs_score'] >= 80:
                # SNIPER SHOT for high confidence
                message = self.format_sniper_alert(signal)
                keyboard = self.create_webapp_button(mission_data, "sniper")
            else:
                # RAPID ASSAULT for medium confidence
                message = self.format_rapid_alert(signal)
                keyboard = self.create_webapp_button(mission_data, "rapid")
            
            # Send with WebApp button
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending alert: {e}")
            return False

# Example usage
async def demo_fixed_alerts():
    """Demo the fixed alert system"""
    alerts = FixedTelegramAlerts("8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k")
    
    # High confidence signal (SNIPER)
    sniper_signal = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 87,
        'entry': 1.09235,
        'sl': 1.09035,
        'tp': 1.09635,
        'session': 'LONDON'
    }
    
    # Medium confidence signal (RAPID)
    rapid_signal = {
        'symbol': 'GBPUSD',
        'direction': 'SELL',
        'tcs_score': 72,
        'entry': 1.26545,
        'sl': 1.26745,
        'tp': 1.26145,
        'session': 'NEW_YORK'
    }
    
    chat_id = "-1002581996861"
    
    print("🚀 Sending SNIPER alert...")
    await alerts.send_signal_alert(sniper_signal, chat_id, "COMMANDER")
    
    await asyncio.sleep(3)
    
    print("🚀 Sending RAPID alert...")
    await alerts.send_signal_alert(rapid_signal, chat_id, "FANG")
    
    print("✅ Fixed alerts sent!")

if __name__ == "__main__":
    asyncio.run(demo_fixed_alerts())