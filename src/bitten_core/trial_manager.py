"""
BITTEN Trial Management System
7-day trial with payment prompt at day 6
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .database.connection import get_db_session
from .database.models import SubscriptionStatus, User, UserProfile, UserSubscription
from .stripe_payment_processor import get_stripe_processor

if TYPE_CHECKING:
    from .telegram_router import CommandResult

logger = logging.getLogger(__name__)


# Local CommandResult for avoiding circular imports at runtime
class CommandResult:
    def __init__(self, success: bool, message: str, requires_payment: bool = False):
        self.success = success
        self.message = message
        self.requires_payment = requires_payment


class TrialStatus(Enum):
    """Trial status states"""

    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"  # Day 14-15
    EXPIRED = "expired"
    CONVERTED = "converted"
    ABANDONED = "abandoned"  # 45+ days after expiry


class AccountType(Enum):
    """Account type"""

    DEMO = "demo"
    LIVE = "live"


class TrialManager:
    """Manages 7-day trial system"""

    def __init__(self, telegram_bot=None):
        self.telegram_bot = telegram_bot
        self.stripe = get_stripe_processor()

        # Trial configuration
        self.trial_duration_days = 7
        self.payment_prompt_day = 6  # Start prompting on day 6
        self.grace_period_days = 2
        self.data_retention_days = 45

        logger.info("Trial Manager initialized")

    async def start_trial(self, user_id: int, account_type: AccountType = AccountType.DEMO) -> CommandResult:
        """Start 7-day trial for new user"""

        with get_db_session() as session:
            try:
                # Check if user exists
                user = session.query(User).filter(User.user_id == user_id).first()
                if not user:
                    # Create new user
                    user = User(
                        user_id=user_id,
                        tier="NIBBLER",  # Start with basic tier during trial
                        subscription_status=SubscriptionStatus.TRIALING.value,
                        created_at=datetime.now(),
                    )
                    session.add(user)

                # Check for existing trial
                existing_trial = session.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()

                if existing_trial:
                    return CommandResult(False, "❌ Trial already used")

                # Create Stripe customer (no payment method required yet)
                stripe_result = await self.stripe.create_customer(
                    user_id, metadata={"trial_started": datetime.now().isoformat(), "account_type": account_type.value}
                )

                if not stripe_result["success"]:
                    logger.error(f"Failed to create Stripe customer: {stripe_result['error']}")

                # Create trial subscription record
                trial_end = datetime.now() + timedelta(days=self.trial_duration_days)

                subscription = UserSubscription(
                    user_id=user_id,
                    plan_name="TRIAL",
                    billing_cycle="trial",
                    price=0,
                    status=SubscriptionStatus.TRIALING.value,
                    started_at=datetime.now(),
                    current_period_start=datetime.now(),
                    current_period_end=trial_end,
                    trial_end=trial_end,
                    stripe_customer_id=stripe_result.get("customer_id"),
                    metadata=json.dumps({"account_type": account_type.value, "trial_days": self.trial_duration_days}),
                )
                session.add(subscription)

                # Update user
                user.subscription_expires_at = trial_end
                user.account_type = account_type.value

                session.commit()

                # No payment mention during trial start!
                message = f"""🎯 **WELCOME TO BITTEN, SOLDIER!**

You have **{self.trial_duration_days} days** to experience the full power of BITTEN.

🔓 **Immediate Value Unlocked:**
• All trading features available
• Complete strategy library access
• Full automation capabilities
• Squad features enabled

Get ready for a quick but powerful trial experience!
Type `/fire` to begin your first mission!"""

                return CommandResult(True, message)

            except Exception as e:
                logger.error(f"Error starting trial: {e}")
                session.rollback()
                return CommandResult(False, "❌ Failed to start trial")

    async def check_trial_status(self, user_id: int) -> Dict:
        """Check user's trial status"""

        with get_db_session() as session:
            subscription = (
                session.query(UserSubscription)
                .filter(
                    UserSubscription.user_id == user_id, UserSubscription.status == SubscriptionStatus.TRIALING.value
                )
                .first()
            )

            if not subscription:
                return {"status": "no_trial", "can_start_trial": True}

            days_remaining = (subscription.trial_end - datetime.now()).days
            days_used = self.trial_duration_days - days_remaining

            # Determine status
            if days_remaining <= 0:
                status = TrialStatus.EXPIRED
            elif days_remaining <= 1:  # Day 6-7
                status = TrialStatus.EXPIRING_SOON
            else:
                status = TrialStatus.ACTIVE

            return {
                "status": status.value,
                "days_remaining": max(0, days_remaining),
                "days_used": days_used,
                "trial_end": subscription.trial_end.isoformat(),
                "account_type": json.loads(subscription.metadata or "{}").get("account_type", "demo"),
                "show_payment_prompt": days_used >= self.payment_prompt_day,
            }

    async def send_trial_reminders(self) -> int:
        """Send payment reminders at day 6"""

        reminder_count = 0

        with get_db_session() as session:
            # Find trials that need day 6 reminder
            cutoff_date = datetime.now() - timedelta(days=self.payment_prompt_day)

            trials = (
                session.query(UserSubscription)
                .filter(
                    UserSubscription.status == SubscriptionStatus.TRIALING.value,
                    UserSubscription.started_at <= cutoff_date,
                    UserSubscription.trial_end > datetime.now(),
                )
                .all()
            )

            for trial in trials:
                days_remaining = (trial.trial_end - datetime.now()).days

                # Only send on day 6 (1 day remaining)
                if days_remaining == 1:
                    await self._send_payment_prompt(trial.user_id, days_remaining)
                    reminder_count += 1

        return reminder_count

    async def _send_payment_prompt(self, user_id: int, days_remaining: int) -> None:
        """Send payment prompt message"""

        if not self.telegram_bot:
            return

        message = f"""⏰ **YOUR TRIAL ENDS TOMORROW!**

You've been crushing it for 6 days, soldier! 🎯

Don't lose your progress:
• Your XP and achievements
• Your trading history
• Your squad connections
• Your custom settings

**Continue your journey with a subscription:**

💎 **NIBBLER** - $39/month
Perfect for focused traders

⚡ **FANG** - $89/month
Unlock advanced strategies

🔥 **COMMANDER** - $189/month
Full automation suite & elite features

Ready to lock in your gains?"""

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💳 Subscribe Now", callback_data="trial_subscribe")],
                [InlineKeyboardButton("📊 Compare Plans", callback_data="trial_compare_plans")],
                [InlineKeyboardButton("⏰ Remind Me Later", callback_data="trial_remind_later")],
            ]
        )

        try:
            await self.telegram_bot.send_message(
                chat_id=user_id, text=message, reply_markup=keyboard, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send trial reminder to {user_id}: {e}")

    async def handle_trial_expiry(self) -> int:
        """Handle expired trials"""

        handled_count = 0

        with get_db_session() as session:
            # Find expired trials
            expired_trials = (
                session.query(UserSubscription)
                .filter(
                    UserSubscription.status == SubscriptionStatus.TRIALING.value,
                    UserSubscription.trial_end <= datetime.now(),
                )
                .all()
            )

            for trial in expired_trials:
                user = session.query(User).filter(User.user_id == trial.user_id).first()
                if not user:
                    continue

                # Update subscription status
                trial.status = SubscriptionStatus.EXPIRED.value
                trial.ends_at = datetime.now()

                # Lock all features except subscribe
                user.subscription_status = SubscriptionStatus.EXPIRED.value
                user.features_locked = True

                # Send expiry notification
                await self._send_expiry_notification(trial.user_id)

                handled_count += 1

            session.commit()

        return handled_count

    async def _send_expiry_notification(self, user_id: int) -> None:
        """Send trial expiry notification"""

        if not self.telegram_bot:
            return

        message = """🔒 **TRIAL EXPIRED**

Your 7-day trial has ended. All trading features are now locked.

**Your data is safe!** You have 45 days to subscribe and pick up right where you left off.

Ready to continue your journey?"""

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🚀 Subscribe Now", callback_data="expired_subscribe")],
                [InlineKeyboardButton("💰 View Pricing", callback_data="expired_pricing")],
            ]
        )

        try:
            await self.telegram_bot.send_message(
                chat_id=user_id, text=message, reply_markup=keyboard, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send expiry notification to {user_id}: {e}")

    async def check_abandoned_accounts(self) -> int:
        """Check for accounts abandoned after 45 days"""

        abandoned_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)

        with get_db_session() as session:
            # Find expired trials older than 45 days
            abandoned = (
                session.query(UserSubscription)
                .filter(
                    UserSubscription.status == SubscriptionStatus.EXPIRED.value, UserSubscription.ends_at <= cutoff_date
                )
                .all()
            )

            for sub in abandoned:
                user = session.query(User).filter(User.user_id == sub.user_id).first()
                if not user:
                    continue

                # Reset user data
                user.xp = 0
                user.level = 1
                user.trades_count = 0
                user.win_rate = 0
                user.total_pnl = 0

                # Mark as abandoned
                sub.status = SubscriptionStatus.ABANDONED.value
                sub.metadata = json.dumps(
                    {**json.loads(sub.metadata or "{}"), "abandoned_at": datetime.now().isoformat(), "data_reset": True}
                )

                abandoned_count += 1

            session.commit()
            logger.info(f"Reset {abandoned_count} abandoned accounts")

        return abandoned_count

    async def migrate_demo_to_live(self, user_id: int, mt5_credentials: Dict) -> CommandResult:
        """Migrate user from demo to live account"""

        with get_db_session() as session:
            try:
                user = session.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return CommandResult(False, "❌ User not found")

                if user.account_type != AccountType.DEMO.value:
                    return CommandResult(False, "❌ Already on live account")

                # Store encrypted MT5 credentials
                profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()

                if not profile:
                    profile = UserProfile(user_id=user_id)
                    session.add(profile)

                # Encrypt and store credentials (implement proper encryption!)
                profile.mt5_account = mt5_credentials.get("account")
                profile.mt5_server = mt5_credentials.get("server")
                # DO NOT store password in plain text - use proper encryption

                # Update account type
                user.account_type = AccountType.LIVE.value

                # Update subscription metadata
                subscription = session.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()

                if subscription:
                    metadata = json.loads(subscription.metadata or "{}")
                    metadata["account_type"] = AccountType.LIVE.value
                    metadata["migrated_at"] = datetime.now().isoformat()
                    subscription.metadata = json.dumps(metadata)

                session.commit()

                message = """✅ **ACCOUNT UPGRADED TO LIVE!**

Your progress has been preserved:
• All XP and achievements retained
• Trading history intact
• Settings transferred

⚠️ **IMPORTANT**: You're now trading with real money. Trade responsibly!

Ready to continue with your live account?"""

                return CommandResult(True, message)

            except Exception as e:
                logger.error(f"Error migrating to live account: {e}")
                session.rollback()
                return CommandResult(False, "❌ Migration failed")

    async def handle_subscription_callback(self, user_id: int, callback_data: str) -> CommandResult:
        """Handle trial-related callbacks"""

        if callback_data == "trial_subscribe":
            # Show subscription options
            return await self._show_subscription_options(user_id)

        elif callback_data == "trial_compare_plans":
            # Show plan comparison
            return await self._show_plan_comparison(user_id)

        elif callback_data == "expired_subscribe":
            # Show subscribe page for expired users
            return await self._show_subscription_options(user_id, expired=True)

        return CommandResult(False, "Unknown callback")

    async def _show_subscription_options(self, user_id: int, expired: bool = False) -> CommandResult:
        """Show subscription options"""

        message = """💳 **CHOOSE YOUR SUBSCRIPTION**

**Monthly Recurring - Cancel Anytime**

Select your tier:"""

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🥉 NIBBLER $39/mo", callback_data="subscribe_NIBBLER")],
                [InlineKeyboardButton("🥈 FANG $89/mo", callback_data="subscribe_FANG")],
                [InlineKeyboardButton("🥇 COMMANDER $189/mo", callback_data="subscribe_COMMANDER")],
                [InlineKeyboardButton("❓ Help Me Choose", callback_data="help_choose_plan")],
                [InlineKeyboardButton("🔙 Back", callback_data="trial_back")],
            ]
        )

        return CommandResult(True, message, data={"reply_markup": keyboard})

    async def _show_plan_comparison(self, user_id: int) -> CommandResult:
        """Show detailed plan comparison"""

        message = """📊 **PLAN COMPARISON**

**🥉 NIBBLER** ($39/month)
• 6 trades per day
• Manual trading only
• Basic risk management
• Perfect for beginners

**🥈 FANG** ($89/month)
• 10 trades per day
• Sniper mode unlocked
• Chaingun progressive risk
• Advanced filters

**🥇 COMMANDER** ($189/month)
• Unlimited trades
• Full automation
• Stealth mode
• All strategies
• Priority support
• Elite features

✅ Cancel anytime
✅ No long-term commitment
✅ Instant activation

Which tier matches your trading style?"""

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💳 Subscribe Now", callback_data="trial_subscribe")],
                [InlineKeyboardButton("🔙 Back", callback_data="trial_back")],
            ]
        )

        return CommandResult(True, message, data={"reply_markup": keyboard})


# Create singleton instance
_trial_manager = None


def get_trial_manager(telegram_bot=None) -> TrialManager:
    """Get or create trial manager instance"""
    global _trial_manager
    if _trial_manager is None:
        _trial_manager = TrialManager(telegram_bot)
    return _trial_manager


# Add missing import
import json
