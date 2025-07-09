#!/usr/bin/env python3
"""
Unified Signal Flow for BITTEN
Streamlined routing from signal generation to user delivery
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import urllib.parse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/signal_flow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UnifiedSignalFlow:
    """Manages the complete signal flow from generation to delivery"""
    
    def __init__(self):
        self.bot_token = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
        self.chat_id = '-1002581996861'
        self.webapp_url = 'http://134.199.204.67:8888'
        self.bot = telegram.Bot(token=self.bot_token)
        
    def format_signal_message(self, signal: Dict[str, Any]) -> str:
        """Format signal for Telegram display"""
        tcs = signal.get('tcs_score', 0)
        symbol = signal.get('symbol', '')
        direction = signal.get('direction', '')
        
        # Determine signal type and formatting
        if tcs >= 90:
            header = "🔥🔥 **SNIPER SHOT** 🔥🔥"
            confidence = f"{tcs}%"
        elif tcs >= 80:
            header = "⭐ **Precision Strike** ⭐"
            confidence = f"{tcs}%"
        else:
            header = "✅ Signal Alert"
            confidence = f"{tcs}%"
        
        # Build message
        message = f"{header}\n"
        message += f"**{symbol} {direction}** | {confidence}"
        
        # Add tier-specific info
        if signal.get('rr_ratio'):
            message += f" | R:R {signal['rr_ratio']}"
        
        return message
    
    def create_webapp_button(self, signal: Dict[str, Any]) -> InlineKeyboardMarkup:
        """Create WebApp button for signal"""
        # Prepare data for webapp
        webapp_data = {
            'mission_id': signal.get('id', f"SIG-{int(time.time()*1000)}"),
            'signal': signal,
            'timestamp': int(time.time())
        }
        
        # Encode data
        encoded_data = urllib.parse.quote(json.dumps(webapp_data))
        url = f"{self.webapp_url}/hud?data={encoded_data}"
        
        # Determine button text based on signal type
        tcs = signal.get('tcs_score', 0)
        if tcs >= 90:
            button_text = "🎯 SNIPER MISSION BRIEF"
        elif tcs >= 80:
            button_text = "⭐ PRECISION INTEL"
        else:
            button_text = "📊 VIEW DETAILS"
        
        # Create button
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(text=button_text, url=url)
        ]])
        
        return keyboard
    
    async def send_signal(self, signal: Dict[str, Any]) -> bool:
        """Send signal to Telegram with webapp integration"""
        try:
            # Format message
            message = self.format_signal_message(signal)
            
            # Create webapp button
            keyboard = self.create_webapp_button(signal)
            
            # Send to Telegram
            result = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            logger.info(f"Signal sent successfully: {signal.get('symbol')} {signal.get('direction')}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending signal: {e}")
            return False
    
    async def process_signal_batch(self, signals: list) -> Dict[str, int]:
        """Process multiple signals with tier-based filtering"""
        results = {'sent': 0, 'filtered': 0, 'failed': 0}
        
        for signal in signals:
            # Add any tier-based filtering here
            tcs = signal.get('tcs_score', 0)
            
            # For now, send all signals above 70 TCS
            if tcs >= 70:
                success = await self.send_signal(signal)
                if success:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                
                # Rate limiting
                await asyncio.sleep(2)
            else:
                results['filtered'] += 1
                logger.info(f"Signal filtered (TCS {tcs}): {signal.get('symbol')}")
        
        return results
    
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate signal has required fields"""
        required_fields = ['symbol', 'direction', 'tcs_score', 'entry', 'sl', 'tp']
        
        for field in required_fields:
            if field not in signal:
                logger.error(f"Signal missing required field: {field}")
                return False
        
        return True
    
    async def handle_webapp_callback(self, user_id: int, action: str, signal_id: str) -> Dict[str, Any]:
        """Handle callbacks from webapp (fire button clicks, etc)"""
        # This would connect to your TOC system
        logger.info(f"Webapp callback: user={user_id}, action={action}, signal={signal_id}")
        
        # Placeholder for TOC integration
        response = {
            'status': 'success',
            'message': 'Trade queued for execution',
            'signal_id': signal_id
        }
        
        return response

# Test function
async def test_unified_flow():
    """Test the unified signal flow"""
    flow = UnifiedSignalFlow()
    
    # Test signal
    test_signal = {
        'id': f"TEST-{int(time.time()*1000)}",
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 92,
        'signal_type': 'SNIPER',
        'entry': 1.09235,
        'sl': 1.09035,
        'tp': 1.09635,
        'sl_pips': 20,
        'tp_pips': 40,
        'rr_ratio': 2.0,
        'spread': 1.2,
        'session': 'LONDON',
        'timestamp': datetime.now().isoformat(),
        'expiry': 600
    }
    
    # Validate and send
    if flow.validate_signal(test_signal):
        success = await flow.send_signal(test_signal)
        if success:
            print("✅ Test signal sent successfully!")
        else:
            print("❌ Failed to send test signal")
    else:
        print("❌ Invalid signal format")

if __name__ == '__main__':
    print("🧪 Testing Unified Signal Flow...")
    asyncio.run(test_unified_flow())