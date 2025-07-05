# signal_alerts.py
# BITTEN Brief Signal Alert System - Minimal alerts with HUD redirect

import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

@dataclass
class SignalAlert:
    """Brief signal alert structure"""
    signal_id: str
    symbol: str
    direction: str  # BUY/SELL
    confidence: float
    urgency: str  # CRITICAL/HIGH/MEDIUM
    timestamp: int
    expires_at: int
    
class SignalAlertSystem:
    """Delivers brief tactical alerts with HUD redirect"""
    
    def __init__(self, bot_token: str, hud_webapp_url: str):
        self.bot = telegram.Bot(token=bot_token)
        self.hud_webapp_url = hud_webapp_url
        self.active_signals: Dict[str, SignalAlert] = {}
        
    async def send_signal_alert(self, user_id: int, signal: SignalAlert, user_tier: str) -> bool:
        """Send brief signal alert with VIEW INTEL button"""
        try:
            # Urgency indicators
            urgency_icons = {
                'CRITICAL': '🚨',
                'HIGH': '⚡',
                'MEDIUM': '🎯'
            }
            
            # Brief alert message (2-3 lines max)
            alert_message = f"{urgency_icons[signal.urgency]} **SIGNAL DETECTED**\n"
            alert_message += f"{signal.symbol} | {signal.direction} | {signal.confidence:.0%} confidence\n"
            alert_message += f"⏰ Expires in {int((signal.expires_at - time.time()) / 60)} minutes"
            
            # Create inline keyboard with WebApp button
            webapp_data = {
                'signal_id': signal.signal_id,
                'user_tier': user_tier,
                'timestamp': signal.timestamp
            }
            
            keyboard = [
                [InlineKeyboardButton(
                    "🎯 VIEW INTEL", 
                    web_app=telegram.WebAppInfo(
                        url=f"{self.hud_webapp_url}?data={json.dumps(webapp_data)}"
                    )
                )]
            ]
            
            # Add tier-specific messaging
            if user_tier == 'FREE':
                keyboard.append([
                    InlineKeyboardButton("🔓 UNLOCK FULL ACCESS", callback_data="upgrade_tier")
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send alert
            await self.bot.send_message(
                chat_id=user_id,
                text=alert_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Store active signal
            self.active_signals[signal.signal_id] = signal
            
            return True
            
        except Exception as e:
            print(f"Failed to send signal alert: {e}")
            return False
    
    async def send_batch_alerts(self, signal: SignalAlert, target_users: List[Dict]) -> Dict:
        """Send alerts to multiple users based on their tiers"""
        results = {
            'sent': 0,
            'failed': 0,
            'tier_blocked': 0
        }
        
        for user in target_users:
            user_id = user['user_id']
            user_tier = user['tier']
            
            # Check tier access
            if not self._check_signal_access(signal, user_tier):
                results['tier_blocked'] += 1
                continue
            
            # Send alert
            success = await self.send_signal_alert(user_id, signal, user_tier)
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
            
            # Rate limiting
            await asyncio.sleep(0.05)  # 20 messages per second
        
        return results
    
    def _check_signal_access(self, signal: SignalAlert, user_tier: str) -> bool:
        """Check if user tier has access to signal urgency level"""
        tier_access = {
            'FREE': ['MEDIUM'],
            'AUTHORIZED': ['MEDIUM', 'HIGH'],
            'ELITE': ['MEDIUM', 'HIGH', 'CRITICAL'],
            'ADMIN': ['MEDIUM', 'HIGH', 'CRITICAL']
        }
        
        return signal.urgency in tier_access.get(user_tier, [])
    
    async def send_signal_executed(self, user_id: int, signal_id: str, result: Dict):
        """Send execution confirmation"""
        signal = self.active_signals.get(signal_id)
        if not signal:
            return
        
        # Result icons
        result_icon = '✅' if result['success'] else '❌'
        
        message = f"{result_icon} **SIGNAL EXECUTED**\n"
        message += f"{signal.symbol} {signal.direction}\n"
        
        if result['success']:
            message += f"Entry: {result['entry_price']}\n"
            message += f"Position: {result['position_id']}"
        else:
            message += f"Reason: {result['reason']}"
        
        await self.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
    
    async def cleanup_expired_signals(self):
        """Remove expired signals from active list"""
        current_time = time.time()
        expired = [
            signal_id for signal_id, signal in self.active_signals.items()
            if signal.expires_at < current_time
        ]
        
        for signal_id in expired:
            del self.active_signals[signal_id]
        
        return len(expired)
    
    def get_active_signal(self, signal_id: str) -> Optional[SignalAlert]:
        """Get active signal by ID"""
        return self.active_signals.get(signal_id)
    
    def get_user_accessible_signals(self, user_tier: str) -> List[SignalAlert]:
        """Get all signals accessible to user tier"""
        accessible = []
        for signal in self.active_signals.values():
            if self._check_signal_access(signal, user_tier):
                accessible.append(signal)
        
        return sorted(accessible, key=lambda s: s.timestamp, reverse=True)