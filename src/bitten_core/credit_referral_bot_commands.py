#!/usr/bin/env python3
"""
BITTEN Credit Referral Bot Commands
Telegram bot handlers for /recruit and /credits commands
"""

import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .credit_referral_system import get_credit_referral_system

logger = logging.getLogger(__name__)


class CreditReferralBotCommands:
    """Bot command handlers for credit referral system"""

    def __init__(self):
        self.referral_system = get_credit_referral_system()
        self.base_url = "https://t.me/Bitten_Commander_bot?start="

    def _get_current_badge_display(self, referral_count: int) -> str:
        """Get current recruitment badge display"""
        if referral_count >= 50:
            return "👑 LEGENDARY_RECRUITER"
        elif referral_count >= 25:
            return "⭐ RECRUITMENT_MASTER"
        elif referral_count >= 10:
            return "🥇 ELITE_RECRUITER"
        elif referral_count >= 5:
            return "🥈 SQUAD_BUILDER"
        elif referral_count >= 1:
            return "🥉 RECRUITER"
        else:
            return "🎖️ NEW_RECRUIT"

    async def handle_recruit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /recruit command - generate and display referral link"""
        user_id = str(update.effective_user.id)

        try:
            # Generate referral code
            referral_code = self.referral_system.generate_referral_code(user_id)
            referral_link = f"{self.base_url}{referral_code}"

            # Get current stats
            stats = self.referral_system.get_referral_stats(user_id)
            balance = stats["balance"]

            # Build response message
            message = f"""🎖️ **YOUR RECRUITMENT COMMAND CENTER**

**🔗 Your Referral Link:**
`{referral_link}`

**📊 Current Stats:**
💰 Available Credits: **${balance.total_credits:.0f}**
⏳ Pending Credits: **${balance.pending_credits:.0f}**
👥 Total Recruits: **{balance.referral_count}**

**🎯 Earnings Breakdown:**
• Each successful recruit = **$10 credit**
• Credits automatically apply to your next bill
• Stack credits for free months!

**💡 Progress to Free Month:**
You need {stats['progress_to_free_month']} more to earn a free month!
({stats['free_months_earned']} free months earned so far)

**🚀 How It Works:**
1. Share your link with friends
2. They sign up and subscribe ($39+ tier)
3. You get $10 credit after their first payment
4. Credits automatically reduce your next bill

**📱 Share Your Link:**
Copy the link above and share it anywhere! When someone joins BITTEN through your link and subscribes, you both win!"""

            # Create inline keyboard with share options
            keyboard = [
                [
                    InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_link_{referral_code}"),
                    InlineKeyboardButton("📊 Detailed Stats", callback_data=f"recruit_stats_{user_id}"),
                ],
                [
                    InlineKeyboardButton(
                        "💬 Share to Telegram",
                        url=f"https://t.me/share/url?url={referral_link}&text=Join me on BITTEN - Elite Tactical Trading Academy! 🎯",
                    )
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True
            )

        except Exception as e:
            logger.error(f"Error in recruit command for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Error generating your referral link. Please try again later.", parse_mode="Markdown"
            )

    async def handle_credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /credits command - show credit balance and history"""
        user_id = str(update.effective_user.id)

        try:
            stats = self.referral_system.get_referral_stats(user_id)
            balance = stats["balance"]

            # Build detailed credits message
            message = f"""💰 **YOUR CREDIT BALANCE**

**Current Balance:**
💳 Available Credits: **${balance.total_credits:.0f}**
⏳ Pending Credits: **${balance.pending_credits:.0f}**
✅ Applied Credits: **${balance.applied_credits:.0f}**

**📈 Recruitment Success:**
👥 Total Recruits: **{balance.referral_count}**
🆓 Free Months Earned: **{stats['free_months_earned']}**

**🎯 Progress to Next Free Month:**
You're **{stats['progress_to_free_month']}** away from earning another free month!
(NIBBLER tier = $39/month)

**💡 How Credits Work:**
• Earn $10 for each successful referral
• Credits automatically apply to your next invoice
• No expiration - stack as many as you want!
• Credits apply before charging your payment method"""

            # Add recent referrals if any
            if stats["recent_referrals"]:
                message += "\n\n**📋 Recent Referrals:**\n"
                for i, referral in enumerate(stats["recent_referrals"][:5]):
                    status = (
                        "✅ Paid"
                        if referral["credited"]
                        else ("💰 Payment Pending" if referral["payment_confirmed"] else "⏳ Waiting for Payment")
                    )
                    message += f"{i+1}. User ID: `{referral['referred_user'][-8:]}...` - {status}\n"

            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🎖️ Get Referral Link", callback_data=f"get_recruit_link_{user_id}"),
                    InlineKeyboardButton("📊 Full History", callback_data=f"credit_history_{user_id}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error in credits command for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Error retrieving your credit balance. Please try again later.", parse_mode="Markdown"
            )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        user_id = str(update.effective_user.id)

        try:
            if callback_data.startswith("copy_link_"):
                referral_code = callback_data.split("_")[-1]
                referral_link = f"{self.base_url}{referral_code}"

                await query.edit_message_text(
                    f"📋 **Referral Link Copied!**\n\n`{referral_link}`\n\nShare this link to start earning $10 credits for each successful referral!",
                    parse_mode="Markdown",
                )

            elif callback_data.startswith("recruit_stats_"):
                stats = self.referral_system.get_referral_stats(user_id)
                balance = stats["balance"]

                detailed_message = f"""📊 **DETAILED RECRUITMENT STATS**

**💰 Financial Overview:**
• Total Credits Earned: **${balance.applied_credits + balance.total_credits:.0f}**
• Currently Available: **${balance.total_credits:.0f}**
• Applied to Invoices: **${balance.applied_credits:.0f}**
• Pending Payment: **${balance.pending_credits:.0f}**

**👥 Recruitment Performance:**
• Total Successful Recruits: **{balance.referral_count}**
• Conversion Rate: **{(balance.referral_count / max(1, len(stats['recent_referrals']))) * 100:.1f}%**
• Average per Recruit: **$10.00**

**🎯 Milestones:**
• Next Free Month: {stats['progress_to_free_month']} away
• Free Months Earned: **{stats['free_months_earned']}**
• Total Value Generated: **${(balance.referral_count * 10):.0f}**"""

                if stats["recent_referrals"]:
                    detailed_message += "\n\n**📋 All Referrals:**\n"
                    for i, referral in enumerate(stats["recent_referrals"]):
                        status_emoji = (
                            "✅" if referral["credited"] else ("💰" if referral["payment_confirmed"] else "⏳")
                        )
                        detailed_message += f"{i+1}. {status_emoji} `{referral['referred_user'][-8:]}...` - ${referral['credit_amount']:.0f}\n"

                await query.edit_message_text(detailed_message, parse_mode="Markdown")

            elif callback_data.startswith("get_recruit_link_"):
                # Redirect to recruit command functionality
                referral_code = self.referral_system.generate_referral_code(user_id)
                referral_link = f"{self.base_url}{referral_code}"

                await query.edit_message_text(
                    f"🎖️ **Your Referral Link:**\n\n`{referral_link}`\n\nShare this to earn $10 for each successful recruit!",
                    parse_mode="Markdown",
                )

            elif callback_data.startswith("credit_history_"):
                stats = self.referral_system.get_referral_stats(user_id)

                history_message = f"""📋 **COMPLETE CREDIT HISTORY**

**Summary:**
• Total Credits Earned: **${stats['balance'].applied_credits + stats['balance'].total_credits:.0f}**
• Total Recruits: **{stats['balance'].referral_count}**"""

                if stats["recent_referrals"]:
                    history_message += "\n\n**Transaction History:**\n"
                    for i, referral in enumerate(stats["recent_referrals"]):
                        date = referral["created_at"][:10] if referral["created_at"] else "Unknown"
                        status = (
                            "✅ Credited"
                            if referral["credited"]
                            else ("💰 Payment Confirmed" if referral["payment_confirmed"] else "⏳ Pending Payment")
                        )
                        history_message += f"`{date}` - User `{referral['referred_user'][-8:]}...` - ${referral['credit_amount']:.0f} - {status}\n"
                else:
                    history_message += "\n\n*No referrals yet. Use /recruit to get your referral link!*"

                await query.edit_message_text(history_message, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error handling callback {callback_data} for user {user_id}: {e}")
            await query.edit_message_text("❌ Error processing request. Please try again.", parse_mode="Markdown")

    def send_credit_notification(self, referrer_id: str, credit_amount: float = 10.0):
        """Send notification when credit is applied (to be called by webhook)"""
        # This would be called by the Stripe webhook handler
        # For now, we'll store it as a method that can be triggered

        remaining_for_free = 39 - (credit_amount % 39)
        message = f"""🎉 **CREDIT EARNED!**

You just earned **${credit_amount:.0f} credit**!

You're now **${remaining_for_free:.0f}** away from a free month!

This credit will automatically apply to your next invoice. Keep recruiting to stack more credits and earn free months!

Use /credits to see your balance or /recruit to get your referral link."""

        # Note: This requires bot instance access - will be integrated in main bot
        return message


# Global instance
_credit_bot_commands = None


def get_credit_referral_bot_commands() -> CreditReferralBotCommands:
    """Get global credit referral bot commands instance"""
    global _credit_bot_commands
    if _credit_bot_commands is None:
        _credit_bot_commands = CreditReferralBotCommands()
    return _credit_bot_commands
