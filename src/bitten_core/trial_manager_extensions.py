"""
Extensions for trial manager - subscription processing
Add these methods to TrialManager class
"""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .trial_manager import CommandResult
from .database.connection import get_db_session
from .database.models import UserSubscription

async def _process_subscription(self, user_id: int, tier: str) -> CommandResult:
    """Process subscription selection"""
    
    # Get or create Stripe customer
    from .stripe_payment_simple import get_stripe_processor
    stripe = get_stripe_processor()
    
    with get_db_session() as session:
        # Get user subscription record
        subscription = session.query(UserSubscription).filter(
            UserSubscription.user_id == user_id
        ).first()
        
        if not subscription:
            return CommandResult(False, "❌ No trial found")
        
        # Create customer if needed
        if not subscription.stripe_customer_id:
            customer_result = await stripe.create_customer(user_id)
            if customer_result['success']:
                subscription.stripe_customer_id = customer_result['customer_id']
                session.commit()
            else:
                return CommandResult(False, "❌ Error creating customer")
        
        # Create payment link
        link_result = await stripe.create_payment_link(
            subscription.stripe_customer_id,
            tier
        )
        
        if not link_result['success']:
            # Fallback to checkout session
            checkout_result = await stripe.create_checkout_session(
                subscription.stripe_customer_id,
                tier,
                success_url='https://t.me/your_bot?start=payment_success',
                cancel_url='https://t.me/your_bot?start=payment_cancelled'
            )
            
            if checkout_result['success']:
                payment_url = checkout_result['checkout_url']
            else:
                return CommandResult(False, "❌ Error creating payment link")
        else:
            payment_url = link_result['payment_url']
    
    # Get price for tier
    price = 39  # Default
    if tier == 'FANG':
        price = 89
    elif tier == 'COMMANDER':
        price = 139
    elif tier == '':
        price = 188
    
    message = f"""💳 **COMPLETE YOUR SUBSCRIPTION**

**Selected Tier**: {tier}
**Price**: ${price}/month

🔗 Click the button below to enter your payment details securely through Stripe.

✅ **What happens next:**
• Instant activation upon payment
• Full access to {tier} features
• Cancel anytime from /me menu
• 2-day grace period if payment fails

🔒 **Secure payment** via Stripe"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Complete Payment", url=payment_url)],
        [InlineKeyboardButton("🔙 Back to Plans", callback_data="trial_subscribe")]
    ])
    
    return CommandResult(True, message, data={'reply_markup': keyboard})

async def _show_plan_help(self, user_id: int) -> CommandResult:
    """Show detailed plan selection help"""
    
    message = """🤔 **WHICH PLAN IS RIGHT FOR YOU?**

**Start with NIBBLER if:**
• You're new to automated trading
• You want to test the waters
• You trade part-time
• Budget conscious

**Choose FANG if:**
• You're ready for advanced features
• You want sniper mode precision
• You trade daily
• You need more firepower

**Go COMMANDER if:**
• You want full automation
• You're a serious trader
• You need all strategies
• Time is money

**is for you if:**
• You're a professional
• You need unlimited trades
• You want priority support
• You demand the best

💡 **Pro tip**: You can upgrade anytime!"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Choose Plan", callback_data="trial_subscribe")],
        [InlineKeyboardButton("🔙 Back", callback_data="trial_back")]
    ])
    
    return CommandResult(True, message, data={'reply_markup': keyboard})

# Update handle_subscription_callback to handle these new callbacks:
def handle_subscription_callback_updated(self, user_id: int, callback_data: str):
    """Updated callback handler"""
    
    if callback_data == "trial_subscribe":
        return self._show_subscription_options(user_id)
    
    elif callback_data == "trial_compare_plans":
        return self._show_plan_comparison(user_id)
    
    elif callback_data == "expired_subscribe":
        return self._show_subscription_options(user_id, expired=True)
        
    elif callback_data.startswith("subscribe_"):
        # Handle tier selection
        tier = callback_data.replace("subscribe_", "").upper()
        return self._process_subscription(user_id, tier)
    
    elif callback_data == "help_choose_plan":
        return self._show_plan_help(user_id)
    
    elif callback_data == "trial_remind_later":
        return CommandResult(True, "✅ We'll remind you tomorrow!", 
                           data={'callback_answer': True})
    
    elif callback_data == "trial_back":
        return CommandResult(True, "Going back...", 
                           data={'delete_message': True})
    
    return CommandResult(False, "Unknown callback")