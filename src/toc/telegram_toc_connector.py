"""
Telegram TOC Connector - Bridges Telegram Bot to TOC Server

This module connects the BITTEN Telegram bot to the TOC server,
handling signal execution, terminal assignment, and trade feedback.
"""

import os
import json
import logging
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Configure logging
logger = logging.getLogger(__name__)

class TelegramTOCConnector:
    """Connects Telegram bot commands to TOC server"""
    
    def __init__(self, toc_url: str = None):
        """
        Initialize the connector
        
        Args:
            toc_url: Base URL of the TOC server
        """
        self.toc_url = toc_url or os.getenv('TOC_URL', 'http://localhost:5000')
        self.timeout = 30
        
        # Cache user sessions
        self.user_sessions = {}
        
        logger.info(f"Telegram TOC Connector initialized with TOC URL: {self.toc_url}")
    
    async def assign_terminal(self, user_id: str, terminal_type: str = 'press_pass',
                            mt5_credentials: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Assign a terminal to user
        
        Args:
            user_id: Telegram user ID
            terminal_type: Type of terminal (press_pass, demo, live)
            mt5_credentials: Optional MT5 login credentials
            
        Returns:
            Tuple of (success, message)
        """
        try:
            url = f"{self.toc_url}/assign-terminal"
            payload = {
                'user_id': user_id,
                'terminal_type': terminal_type,
                'mt5_credentials': mt5_credentials or {}
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache session
                self.user_sessions[user_id] = {
                    'terminal_type': terminal_type,
                    'terminal_name': data['assignment']['terminal_name'],
                    'assigned_at': datetime.now()
                }
                
                return True, f"✅ Terminal assigned: {data['assignment']['terminal_name']}"
            else:
                error_data = response.json()
                return False, f"❌ Assignment failed: {error_data.get('error', 'Unknown error')}"
                
        except requests.exceptions.Timeout:
            return False, "❌ TOC server timeout - please try again"
        except Exception as e:
            logger.error(f"Terminal assignment error: {e}")
            return False, f"❌ Error: {str(e)}"
    
    async def fire_signal(self, user_id: str, signal_data: Dict) -> Tuple[bool, str]:
        """
        Fire a trade signal through TOC
        
        Args:
            user_id: Telegram user ID
            signal_data: Trade signal details
            
        Returns:
            Tuple of (success, message)
        """
        try:
            url = f"{self.toc_url}/fire"
            payload = {
                'user_id': user_id,
                'signal': signal_data
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                return True, f"🎯 Signal fired to {data.get('terminal', 'terminal')}"
            else:
                error_msg = data.get('error', 'Signal routing failed')
                cooldown = data.get('cooldown_remaining')
                
                if cooldown:
                    return False, f"⏱️ Cooldown active: {cooldown}s remaining"
                else:
                    return False, f"❌ {error_msg}"
                    
        except requests.exceptions.Timeout:
            return False, "❌ TOC server timeout - signal not sent"
        except Exception as e:
            logger.error(f"Fire signal error: {e}")
            return False, f"❌ Error: {str(e)}"
    
    async def get_user_status(self, user_id: str) -> Optional[Dict]:
        """
        Get user's current status from TOC
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Status dictionary or None
        """
        try:
            url = f"{self.toc_url}/status/{user_id}"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return None
    
    async def release_terminal(self, user_id: str) -> Tuple[bool, str]:
        """
        Release user's terminal assignment
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            url = f"{self.toc_url}/release-terminal/{user_id}"
            response = requests.post(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Clear cached session
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                
                return True, "✅ Terminal released successfully"
            else:
                return False, "❌ Failed to release terminal"
                
        except Exception as e:
            logger.error(f"Terminal release error: {e}")
            return False, f"❌ Error: {str(e)}"
    
    async def handle_fire_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 signal_data: Dict):
        """
        Handle /fire command from Telegram bot
        
        Args:
            update: Telegram update object
            context: Bot context
            signal_data: Parsed signal data
        """
        user_id = str(update.effective_user.id)
        
        # Check if user has terminal assigned
        status = await self.get_user_status(user_id)
        
        if not status or not status.get('assignments'):
            # Auto-assign terminal based on user tier
            user_tier = status.get('user', {}).get('tier', 'PRESS_PASS') if status else 'PRESS_PASS'
            terminal_type = 'live' if user_tier != 'PRESS_PASS' else 'press_pass'
            
            success, message = await self.assign_terminal(user_id, terminal_type)
            if not success:
                await update.message.reply_text(
                    f"{message}\n\nPlease contact support if this persists."
                )
                return
        
        # Fire the signal
        success, message = await self.fire_signal(user_id, signal_data)
        
        if success:
            # Build success message with details
            response = f"""
🎯 **SIGNAL FIRED**

**Pair**: {signal_data['symbol']}
**Direction**: {signal_data['direction'].upper()}
**Volume**: {signal_data.get('volume', 0.01)}
**SL**: {signal_data.get('stop_loss', 'None')}
**TP**: {signal_data.get('take_profit', 'None')}

{message}

_Monitor your MT5 terminal for execution..._
"""
        else:
            response = message
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = str(update.effective_user.id)
        status = await self.get_user_status(user_id)
        
        if not status:
            await update.message.reply_text("❌ Unable to fetch status")
            return
        
        user_info = status.get('user', {})
        assignments = status.get('assignments', [])
        daily_stats = status.get('daily_stats', {})
        cooldowns = status.get('cooldowns', {})
        
        # Build status message
        message_parts = [
            "📊 **YOUR STATUS**\n",
            f"**Tier**: {user_info.get('tier', 'Unknown')}",
            f"**Fire Mode**: {user_info.get('fire_mode', 'MANUAL')}",
            f"**Level**: {user_info.get('level', 1)}",
            f"**XP**: {user_info.get('xp', 0)}",
        ]
        
        if assignments:
            terminal = assignments[0]
            message_parts.extend([
                f"\n🖥️ **Terminal**: {terminal['terminal_name']}",
                f"**Type**: {terminal['terminal_type']}",
                f"**Status**: Active"
            ])
        else:
            message_parts.append("\n🖥️ **Terminal**: Not assigned")
        
        if daily_stats:
            message_parts.extend([
                f"\n📈 **Today's Stats**",
                f"**Trades**: {daily_stats.get('trade_count', 0)}",
                f"**P/L**: ${daily_stats.get('total_pnl', 0):.2f}",
                f"**Win Rate**: {daily_stats.get('win_rate', 0):.1f}%"
            ])
        
        if cooldowns and any(cooldowns.values()):
            message_parts.append("\n⏱️ **Active Cooldowns**")
            for symbol, remaining in cooldowns.items():
                if remaining > 0:
                    message_parts.append(f"{symbol}: {remaining}s")
        
        await update.message.reply_text('\n'.join(message_parts), parse_mode='Markdown')
    
    async def handle_terminal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /terminal command for terminal management"""
        user_id = str(update.effective_user.id)
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("🆓 Press Pass", callback_data="terminal_press_pass"),
                InlineKeyboardButton("🔵 Demo", callback_data="terminal_demo")
            ],
            [
                InlineKeyboardButton("🟢 Live", callback_data="terminal_live"),
                InlineKeyboardButton("🔴 Release", callback_data="terminal_release")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🖥️ **Terminal Management**\n\n"
            "Choose a terminal type to assign or release your current terminal:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_terminal_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle terminal selection callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        data = query.data
        
        if data == "terminal_release":
            success, message = await self.release_terminal(user_id)
        else:
            terminal_type = data.replace("terminal_", "")
            success, message = await self.assign_terminal(user_id, terminal_type)
        
        await query.edit_message_text(message)
    
    async def process_trade_result(self, user_id: str, trade_result: Dict):
        """
        Process trade result from MT5
        
        Args:
            user_id: Telegram user ID
            trade_result: Trade execution result
        """
        try:
            url = f"{self.toc_url}/trade-result"
            payload = {
                'user_id': user_id,
                'trade_result': trade_result
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                logger.info(f"Trade result processed for user {user_id}")
            else:
                logger.error(f"Failed to process trade result: {response.text}")
                
        except Exception as e:
            logger.error(f"Trade result processing error: {e}")
    
    def format_signal_for_fire(self, signal_text: str) -> Optional[Dict]:
        """
        Parse signal text into structured format for firing
        
        Args:
            signal_text: Raw signal text
            
        Returns:
            Structured signal data or None
        """
        try:
            # Example format: "EURUSD BUY 0.01 SL:1.0850 TP:1.0950"
            parts = signal_text.upper().split()
            
            if len(parts) < 3:
                return None
            
            signal_data = {
                'symbol': parts[0],
                'direction': parts[1].lower(),
                'volume': float(parts[2]) if len(parts) > 2 else 0.01
            }
            
            # Parse SL and TP
            for part in parts[3:]:
                if part.startswith('SL:'):
                    signal_data['stop_loss'] = float(part[3:])
                elif part.startswith('TP:'):
                    signal_data['take_profit'] = float(part[3:])
            
            return signal_data
            
        except Exception as e:
            logger.error(f"Signal parsing error: {e}")
            return None


# Create singleton instance
toc_connector = TelegramTOCConnector()

# Export commonly used methods
assign_terminal = toc_connector.assign_terminal
fire_signal = toc_connector.fire_signal
get_user_status = toc_connector.get_user_status
release_terminal = toc_connector.release_terminal