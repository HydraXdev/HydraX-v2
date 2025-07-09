"""
Press Pass Command Handler for BITTEN
Handles all Press Pass related commands
"""

from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from .xp_integration import XPIntegrationManager


class PressPassCommandHandler:
    """Handles Press Pass commands for the Telegram bot"""
    
    def __init__(self, xp_manager: XPIntegrationManager):
        self.xp_manager = xp_manager
        
    def handle_presspass(self, user_id: str, args: List[str]) -> Dict[str, any]:
        """Handle /presspass command"""
        if not args:
            return self._show_press_pass_info(user_id)
        
        subcommand = args[0].lower()
        
        if subcommand == "activate":
            return self._activate_press_pass(user_id)
        elif subcommand == "deactivate":
            return self._deactivate_press_pass(user_id)
        elif subcommand == "status":
            return self._show_press_pass_status(user_id)
        else:
            return {
                "success": False,
                "message": "Unknown Press Pass command. Use: /presspass [activate|deactivate|status]"
            }
    
    def _show_press_pass_info(self, user_id: str) -> Dict[str, any]:
        """Show Press Pass information"""
        status = self.xp_manager.get_press_pass_status(user_id)
        
        if status["active"]:
            shadow_stats = status["shadow_stats"]
            current_xp = status["current_xp"]
            
            # Calculate time until reset
            now = datetime.now(timezone.utc)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            hours_until_reset = (midnight - now).total_seconds() / 3600
            
            message = (
                f"🎫 **PRESS PASS STATUS** 🎫\n\n"
                f"Status: ✅ ACTIVE\n"
                f"Current XP: **{current_xp:,}** 💀\n"
                f"Time until reset: **{hours_until_reset:.1f} hours**\n\n"
            )
            
            if shadow_stats:
                message += (
                    f"📊 **Shadow Stats** (hidden from public):\n"
                    f"• Real Total XP: {shadow_stats['real_total_xp']:,}\n"
                    f"• Total XP Wiped: {shadow_stats['total_xp_wiped']:,}\n"
                    f"• Reset Count: {shadow_stats['reset_count']}\n"
                    f"• Largest Wipe: {shadow_stats['largest_wipe']:,}\n\n"
                )
            
            message += (
                f"⚠️ **WARNING**: Your XP resets EVERY night at 00:00 UTC!\n"
                f"Use /xpshop to spend XP before it's wiped!\n\n"
                f"To deactivate: /presspass deactivate"
            )
        else:
            message = (
                f"🎫 **PRESS PASS** 🎫\n\n"
                f"Status: ❌ INACTIVE\n\n"
                f"**What is Press Pass?**\n"
                f"A high-stakes XP mode where your XP resets to ZERO every night!\n\n"
                f"🔥 **Features:**\n"
                f"• Nightly XP wipe at 00:00 UTC\n"
                f"• Warning notifications at 23:00 and 23:45 UTC\n"
                f"• Shadow stats track your real progress\n"
                f"• Creates urgency to spend XP daily\n\n"
                f"⚡ **For thrill-seekers only!**\n\n"
                f"To activate: /presspass activate"
            )
        
        return {
            "success": True,
            "message": message,
            "parse_mode": "Markdown"
        }
    
    def _activate_press_pass(self, user_id: str) -> Dict[str, any]:
        """Activate Press Pass for a user"""
        status = self.xp_manager.get_press_pass_status(user_id)
        
        if status["active"]:
            return {
                "success": False,
                "message": "Press Pass is already active for your account!"
            }
        
        success, message = self.xp_manager.enable_press_pass(user_id)
        
        if success:
            current_xp = self.xp_manager.xp_economy.get_user_balance(user_id).current_balance
            
            response = (
                f"🎫 **PRESS PASS ACTIVATED** 🎫\n\n"
                f"⚠️ **WARNING: HIGH-RISK MODE ENABLED** ⚠️\n\n"
                f"Your current XP: **{current_xp:,}**\n"
                f"This XP will be **WIPED** at 00:00 UTC!\n\n"
                f"🔥 Features enabled:\n"
                f"• Nightly XP reset to ZERO\n"
                f"• Warning notifications before reset\n"
                f"• Shadow stat tracking\n\n"
                f"💀 **There's no going back!**\n"
                f"(Actually there is: /presspass deactivate)"
            )
            
            return {
                "success": True,
                "message": response,
                "parse_mode": "Markdown"
            }
        else:
            return {
                "success": False,
                "message": message
            }
    
    def _deactivate_press_pass(self, user_id: str) -> Dict[str, any]:
        """Deactivate Press Pass for a user"""
        status = self.xp_manager.get_press_pass_status(user_id)
        
        if not status["active"]:
            return {
                "success": False,
                "message": "Press Pass is not active for your account."
            }
        
        success, message = self.xp_manager.disable_press_pass(user_id)
        
        if success:
            shadow_stats = status["shadow_stats"]
            
            response = (
                f"🎫 **PRESS PASS DEACTIVATED** 🎫\n\n"
                f"✅ Your XP is now safe from nightly resets.\n\n"
            )
            
            if shadow_stats:
                response += (
                    f"📊 **Final Stats:**\n"
                    f"• Total XP Wiped: {shadow_stats['total_xp_wiped']:,}\n"
                    f"• Reset Count: {shadow_stats['reset_count']}\n"
                    f"• Largest Single Wipe: {shadow_stats['largest_wipe']:,}\n\n"
                )
            
            response += f"Thanks for living dangerously! 💪"
            
            return {
                "success": True,
                "message": response,
                "parse_mode": "Markdown"
            }
        else:
            return {
                "success": False,
                "message": message
            }
    
    def _show_press_pass_status(self, user_id: str) -> Dict[str, any]:
        """Show detailed Press Pass status"""
        return self._show_press_pass_info(user_id)
    
    def handle_xpstatus(self, user_id: str) -> Dict[str, any]:
        """Handle /xpstatus command - shows XP with Press Pass info"""
        xp_status = self.xp_manager.get_user_xp_status(user_id)
        
        message = (
            f"💰 **XP STATUS** 💰\n\n"
            f"Current Balance: **{xp_status['xp_economy']['current_balance']:,} XP**\n"
            f"Lifetime Earned: {xp_status['xp_economy']['lifetime_earned']:,} XP\n"
            f"Lifetime Spent: {xp_status['xp_economy']['lifetime_spent']:,} XP\n\n"
        )
        
        # Add Press Pass warning if active
        if xp_status["press_pass"]["active"]:
            now = datetime.now(timezone.utc)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            hours_until_reset = (midnight - now).total_seconds() / 3600
            
            message += (
                f"⚠️ **PRESS PASS ACTIVE** ⚠️\n"
                f"Your XP resets in: **{hours_until_reset:.1f} hours**\n"
                f"Spend it or lose it! Visit /xpshop\n\n"
            )
            
            shadow = xp_status["press_pass"]["shadow_stats"]
            if shadow:
                message += (
                    f"📊 Shadow Stats:\n"
                    f"• Real Total XP: {shadow['real_total_xp']:,}\n"
                    f"• Total Wiped: {shadow['total_xp_wiped']:,}\n"
                )
        
        # Add prestige info
        message += (
            f"\n⭐ **Prestige Level**: {xp_status['prestige']['level']}\n"
            f"XP Multiplier: {xp_status['prestige']['multiplier']}x\n"
        )
        
        return {
            "success": True,
            "message": message,
            "parse_mode": "Markdown"
        }
    
    def handle_xpshop(self, user_id: str) -> Dict[str, any]:
        """Handle /xpshop command"""
        # Get shop display
        shop_categories = self.xp_manager.get_shop_display(user_id)
        xp_balance = self.xp_manager.xp_economy.get_user_balance(user_id).current_balance
        
        message = f"🛒 **XP SHOP** 🛒\n\nYour Balance: **{xp_balance:,} XP**\n\n"
        
        # Add Press Pass warning if active
        if self.xp_manager.press_pass_manager and self.xp_manager.press_pass_manager.is_press_pass_user(user_id):
            now = datetime.now(timezone.utc)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            hours_until_reset = (midnight - now).total_seconds() / 3600
            
            message += f"⚠️ **Press Pass Active** - XP resets in {hours_until_reset:.1f}h!\n\n"
        
        # Display shop categories
        for category in shop_categories:
            message += f"{category['icon']} **{category['category']}**\n"
            message += f"{category['description']}\n\n"
            
            for item in category['items'][:3]:  # Show top 3 items per category
                message += f"• {item['name']} - {item['cost']:,} XP\n"
            
            if len(category['items']) > 3:
                message += f"  ...and {len(category['items']) - 3} more\n"
            
            message += "\n"
        
        message += "To purchase: /buy <item_id>"
        
        return {
            "success": True,
            "message": message,
            "parse_mode": "Markdown"
        }
    
    def handle_prestige(self, user_id: str) -> Dict[str, any]:
        """Handle /prestige command"""
        xp_status = self.xp_manager.get_user_xp_status(user_id)
        current_xp = xp_status['xp_economy']['current_balance']
        prestige_info = xp_status['prestige']
        
        # Check if can prestige
        can_prestige, requirement = self.xp_manager.prestige_system.can_prestige(user_id, current_xp)
        
        if can_prestige:
            message = (
                f"⭐ **PRESTIGE AVAILABLE** ⭐\n\n"
                f"Current Level: {prestige_info['level']}\n"
                f"Current XP: {current_xp:,}\n\n"
                f"✅ You can prestige to level {prestige_info['level'] + 1}!\n\n"
                f"**Benefits:**\n"
                f"• New rank and title\n"
                f"• Increased XP multiplier\n"
                f"• Exclusive perks\n"
                f"• XP reset to 0\n\n"
                f"Type /prestige confirm to proceed"
            )
        else:
            next_level = prestige_info['level'] + 1
            xp_required = self.xp_manager.prestige_system.get_prestige_requirement(next_level)
            
            message = (
                f"⭐ **PRESTIGE STATUS** ⭐\n\n"
                f"Current Level: {prestige_info['level']}\n"
                f"Rank: {prestige_info['rank']}\n"
                f"XP Multiplier: {prestige_info['multiplier']}x\n\n"
                f"Current XP: {current_xp:,}\n"
                f"Next Level Requires: {xp_required:,} XP\n"
                f"Progress: {(current_xp/xp_required*100):.1f}%\n\n"
                f"{requirement}"
            )
        
        return {
            "success": True,
            "message": message,
            "parse_mode": "Markdown"
        }