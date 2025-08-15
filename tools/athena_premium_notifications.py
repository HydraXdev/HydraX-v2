#!/usr/bin/env python3
"""
ATHENA Premium Notifications for AUTO-Fire Commander Tier
Sends personalized elite notifications when AUTO-fire executes
"""

import os
import sys
import requests
import json
import time
import random
from typing import Dict, Optional
import logging

# Bot token and configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7854827710:AAE9kCptkoSl8lmQwmX940UMqFWOb3TmTI0")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logger = logging.getLogger(__name__)

class AthenaAutoFireNotifier:
    """Elite notification system for AUTO-fire execution"""
    
    def __init__(self):
        self.premium_greetings = [
            "Commander, your AUTO-fire has been deployed",
            "Elite execution initiated on your behalf", 
            "Your tactical advantage is now active",
            "ATHENA has executed your standing orders",
            "Precision strike deployed to the battlefield",
            "Your autonomous strategy is in motion"
        ]
        
        self.closing_lines = [
            "Your position is now live in the market.",
            "The battlefield is yours, Commander.",
            "Trade executed with military precision.",
            "Your capital is now deployed strategically.",
            "Another calculated move in your arsenal."
        ]
        
    def send_auto_fire_notification(self, 
                                   user_id: str,
                                   signal_data: Dict,
                                   fire_data: Dict,
                                   slot_info: Optional[Dict] = None) -> bool:
        """
        Send premium AUTO-fire notification to Commander
        
        Args:
            user_id: Telegram user ID
            signal_data: Signal details (symbol, direction, confidence, etc)
            fire_data: Fire execution details (lot size, fire_id, etc)
            slot_info: Slot usage info (current/max)
        """
        try:
            # Extract signal details
            symbol = signal_data.get('symbol', 'UNKNOWN')
            direction = signal_data.get('direction', 'BUY')
            confidence = signal_data.get('confidence', 0)
            pattern = signal_data.get('pattern_type', '').replace('_', ' ').title()
            pattern_class = signal_data.get('pattern_class', 'RAPID')
            
            # Extract fire details
            lot_size = fire_data.get('lot', 0.01)
            fire_id = fire_data.get('fire_id', '')
            entry = fire_data.get('entry', 0)
            sl = fire_data.get('sl', 0)
            tp = fire_data.get('tp', 0)
            
            # Get slot status
            if slot_info:
                slots_used = slot_info.get('slots_in_use', 1)
                max_slots = slot_info.get('max_slots', 3)
                slot_status = f"[Slot {slots_used}/{max_slots}]"
            else:
                slot_status = ""
            
            # Select random premium greeting and closing
            greeting = random.choice(self.premium_greetings)
            closing = random.choice(self.closing_lines)
            
            # Determine emoji based on pattern class
            pattern_emoji = "🎯" if pattern_class == "SNIPER" else "⚡"
            
            # Calculate potential profit/loss
            pip_value = self._estimate_pip_value(symbol, lot_size)
            stop_pips = abs(entry - sl) / self._get_pip_size(symbol) if entry and sl else 0
            target_pips = abs(tp - entry) / self._get_pip_size(symbol) if entry and tp else 0
            
            potential_loss = stop_pips * pip_value
            potential_profit = target_pips * pip_value
            
            # Format premium message
            message = f"""🚀 **AUTO-FIRE EXECUTED** {slot_status}

{greeting}

{pattern_emoji} **{symbol} {direction}** • {confidence:.0f}% confidence
📊 **Position Size:** {lot_size:.2f} lots
🎯 **Pattern:** {pattern if pattern else pattern_class}

💰 **Risk/Reward Profile:**
• Risk: ${potential_loss:.2f} ({stop_pips:.0f} pips)
• Target: ${potential_profit:.2f} ({target_pips:.0f} pips)
• R:R Ratio: 1:{(potential_profit/potential_loss if potential_loss > 0 else 2):.1f}

📍 **Entry:** {entry:.5f}
🛡️ **Stop:** {sl:.5f}
🎯 **Target:** {tp:.5f}

{closing}

🔍 Track: `/status {fire_id[:8]}`"""
            
            # Send message
            payload = {
                "chat_id": user_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_notification": False  # Important notifications should ping
            }
            
            response = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=5)
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"✅ Premium AUTO-fire notification sent to {user_id}")
                return True
            else:
                logger.error(f"❌ Failed to send AUTO-fire notification: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending AUTO-fire notification: {e}")
            return False
    
    def send_slot_full_notification(self, user_id: str, slot_info: Dict) -> bool:
        """Send notification when slots are full"""
        try:
            slots_used = slot_info.get('slots_in_use', 3)
            max_slots = slot_info.get('max_slots', 3)
            
            message = f"""⚠️ **AUTO-FIRE SLOTS FULL**

All {max_slots} of your AUTO-fire slots are currently occupied.

New signals will be queued until a slot becomes available.

💡 **Tip:** Positions typically close within 30-60 minutes. Your next slot will open automatically when a position hits its target or stop.

Current slots: {slots_used}/{max_slots} 🔴"""
            
            payload = {
                "chat_id": user_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=5)
            return response.json().get('ok', False)
            
        except Exception as e:
            logger.error(f"Error sending slot full notification: {e}")
            return False
    
    def send_slot_freed_notification(self, user_id: str, slot_info: Dict) -> bool:
        """Send notification when a slot becomes available"""
        try:
            slots_used = slot_info.get('slots_in_use', 2)
            max_slots = slot_info.get('max_slots', 3)
            
            message = f"""✅ **AUTO-FIRE SLOT AVAILABLE**

A slot has been freed. You now have {max_slots - slots_used} available slot(s).

AUTO-fire is ready for the next high-confidence signal.

Current slots: {slots_used}/{max_slots} 🟢"""
            
            payload = {
                "chat_id": user_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=5)
            return response.json().get('ok', False)
            
        except Exception as e:
            logger.error(f"Error sending slot freed notification: {e}")
            return False
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        s = symbol.upper()
        if "JPY" in s:
            return 0.01
        elif s.startswith("XAU"):
            return 0.1
        else:
            return 0.0001
    
    def _estimate_pip_value(self, symbol: str, lot_size: float) -> float:
        """Estimate pip value in USD"""
        # Rough estimates for common pairs
        if "USD" in symbol and symbol.endswith("USD"):
            # USD is quote currency
            return lot_size * 100000 * 0.0001
        elif symbol.startswith("USD"):
            # USD is base currency - use rough exchange rate
            return lot_size * 100000 * 0.0001 * 0.9  # Approximate
        else:
            # Cross pairs - rough estimate
            return lot_size * 100000 * 0.0001 * 1.1
            
# Singleton instance
athena_notifier = AthenaAutoFireNotifier()