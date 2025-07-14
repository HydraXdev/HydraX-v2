"""
BITTEN Tier Upgrade Router
Handles user tier transitions, upgrades, downgrades, and subscription management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from enum import Enum
import json

from .database.connection import get_db_session
from .database.models import User, UserProfile, SubscriptionPlan, UserSubscription, PaymentTransaction, TierLevel, SubscriptionStatus
from .telegram_router import CommandResult
from .fire_modes import TIER_CONFIGS
from .risk_controller import get_risk_controller
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

class UpgradeAction(Enum):
    """Types of tier transitions"""
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    RENEW = "renew"
    CANCEL = "cancel"
    REACTIVATE = "reactivate"

class TierUpgradeRouter:
    """Manages tier upgrades, downgrades, and subscription transitions"""
    
    def __init__(self, payment_processor=None):
        self.payment_processor = payment_processor  # Payment integration (Stripe, etc.)
        self.tier_order = ["NIBBLER", "FANG", "COMMANDER", "APEX"]
        self.tier_pricing = {
            "NIBBLER": 39,
            "FANG": 89,
            "COMMANDER": 139,
            "APEX": 188
        }
        
    def get_upgrade_options(self, user_id: int) -> CommandResult:
        """Show available upgrade options for user"""
        
        with get_db_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return CommandResult(False, "❌ User not found")
            
            current_tier = user.tier
            current_index = self.tier_order.index(current_tier)
            
            # Build upgrade message
            message = f"""🎖️ **TIER UPGRADE CENTER**

**Current Tier**: {current_tier} (${self.tier_pricing[current_tier]}/month)
**Status**: {user.subscription_status}"""
            
            if user.subscription_expires_at:
                days_left = (user.subscription_expires_at - datetime.now()).days
                message += f"\n**Expires**: {days_left} days"
            
            # Show tier comparison
            message += "\n\n📊 **TIER COMPARISON:**\n"
            
            tier_features = {
                "NIBBLER": "• 6 trades/day\n• 75% TCS minimum\n• Manual trading only\n• Basic features",
                "FANG": "• 10 trades/day\n• 80% TCS for sniper\n• Chaingun unlocked\n• Sniper mode access",
                "COMMANDER": "• 20 trades/day\n• 90% TCS auto / 75% semi\n• Auto-fire unlocked\n• Stealth mode\n• All features",
                "APEX": "• Unlimited trades\n• 91% TCS minimum\n• Midnight Hammer\n• Priority support\n• Elite network access"
            }
            
            for tier in self.tier_order:
                if tier == current_tier:
                    message += f"\n✅ **{tier}** - ${self.tier_pricing[tier]}/mo (Current)\n{tier_features[tier]}\n"
                else:
                    message += f"\n🔐 **{tier}** - ${self.tier_pricing[tier]}/mo\n{tier_features[tier]}\n"
            
            # Create upgrade buttons
            keyboard = []
            
            # Upgrade options
            if current_index < len(self.tier_order) - 1:
                for i in range(current_index + 1, len(self.tier_order)):
                    next_tier = self.tier_order[i]
                    price_diff = self.tier_pricing[next_tier] - self.tier_pricing[current_tier]
                    keyboard.append([
                        InlineKeyboardButton(
                            f"⬆️ Upgrade to {next_tier} (+${price_diff}/mo)",
                            callback_data=f"upgrade_{next_tier}"
                        )
                    ])
            
            # Downgrade options
            if current_index > 0:
                for i in range(current_index):
                    lower_tier = self.tier_order[i]
                    price_diff = self.tier_pricing[current_tier] - self.tier_pricing[lower_tier]
                    keyboard.append([
                        InlineKeyboardButton(
                            f"⬇️ Downgrade to {lower_tier} (-${price_diff}/mo)",
                            callback_data=f"downgrade_{lower_tier}"
                        )
                    ])
            
            # Other options
            if user.subscription_status == SubscriptionStatus.ACTIVE.value:
                keyboard.append([
                    InlineKeyboardButton("🔄 Renew Subscription", callback_data="renew_current"),
                    InlineKeyboardButton("❌ Cancel Subscription", callback_data="cancel_subscription")
                ])
            elif user.subscription_status == SubscriptionStatus.CANCELLED.value:
                keyboard.append([
                    InlineKeyboardButton("♻️ Reactivate Subscription", callback_data="reactivate_subscription")
                ])
            
            keyboard.append([
                InlineKeyboardButton("📊 View Benefits", callback_data="view_tier_benefits"),
                InlineKeyboardButton("💳 Payment Methods", callback_data="manage_payment")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            return CommandResult(True, message, data={'reply_markup': reply_markup})
    
    def process_tier_change(self, user_id: int, new_tier: str, action: UpgradeAction) -> CommandResult:
        """Process tier upgrade or downgrade"""
        
        with get_db_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return CommandResult(False, "❌ User not found")
            
            old_tier = user.tier
            old_price = self.tier_pricing[old_tier]
            new_price = self.tier_pricing[new_tier]
            
            # Validate tier change
            if new_tier not in self.tier_order:
                return CommandResult(False, "❌ Invalid tier")
            
            if action == UpgradeAction.UPGRADE:
                # Process upgrade
                if self.tier_order.index(new_tier) <= self.tier_order.index(old_tier):
                    return CommandResult(False, "❌ Cannot upgrade to lower or same tier")
                
                # Calculate prorated amount if mid-cycle
                proration = self._calculate_proration(user, old_price, new_price)
                
                # Create payment intent
                payment_result = self._process_payment(user_id, proration['amount'], f"Upgrade to {new_tier}")
                
                if not payment_result['success']:
                    return CommandResult(False, f"❌ Payment failed: {payment_result['error']}")
                
                # Update user tier
                user.tier = new_tier
                user.subscription_status = SubscriptionStatus.ACTIVE.value
                
                # Log subscription change
                sub_change = UserSubscription(
                    user_id=user_id,
                    plan_name=new_tier,
                    price=new_price,
                    status=SubscriptionStatus.ACTIVE.value,
                    started_at=datetime.now(),
                    next_billing_date=datetime.now() + timedelta(days=30)
                )
                session.add(sub_change)
                
                # Update risk controller
                risk_controller = get_risk_controller()
                risk_controller.update_user_tier(user_id, new_tier)
                
                session.commit()
                
                success_msg = f"""✅ **UPGRADE SUCCESSFUL!**

**New Tier**: {new_tier}
**Monthly Price**: ${new_price}
**Activation**: Immediate

🎯 **New Capabilities Unlocked:**
{self._get_tier_unlock_message(old_tier, new_tier)}

Your new powers are active immediately. Use them wisely, soldier!

Type `/fire` to experience your upgraded firepower!"""
                
                return CommandResult(True, success_msg)
                
            elif action == UpgradeAction.DOWNGRADE:
                # Process downgrade (usually at end of billing cycle)
                if self.tier_order.index(new_tier) >= self.tier_order.index(old_tier):
                    return CommandResult(False, "❌ Cannot downgrade to higher or same tier")
                
                # Schedule downgrade for end of billing period
                user.pending_tier = new_tier
                session.commit()
                
                downgrade_date = user.subscription_expires_at or (datetime.now() + timedelta(days=30))
                
                return CommandResult(
                    True,
                    f"📅 **Downgrade Scheduled**\n\n"
                    f"Your downgrade to **{new_tier}** will take effect on {downgrade_date.strftime('%Y-%m-%d')}.\n"
                    f"Until then, enjoy your {old_tier} benefits!\n\n"
                    f"You can cancel this downgrade anytime before the effective date."
                )
    
    def _calculate_proration(self, user: User, old_price: float, new_price: float) -> Dict:
        """Calculate prorated amount for mid-cycle changes"""
        
        if not user.subscription_expires_at:
            # No active subscription, charge full amount
            return {'amount': new_price, 'credit': 0, 'charge': new_price}
        
        # Calculate days remaining in current cycle
        days_remaining = (user.subscription_expires_at - datetime.now()).days
        if days_remaining <= 0:
            return {'amount': new_price, 'credit': 0, 'charge': new_price}
        
        # Calculate credit for unused time
        daily_rate_old = old_price / 30
        credit = daily_rate_old * days_remaining
        
        # Calculate charge for new tier
        daily_rate_new = new_price / 30
        charge = daily_rate_new * days_remaining
        
        # Net amount to charge
        amount = max(0, charge - credit)
        
        return {
            'amount': round(amount, 2),
            'credit': round(credit, 2),
            'charge': round(charge, 2),
            'days_remaining': days_remaining
        }
    
    def _process_payment(self, user_id: int, amount: float, description: str) -> Dict:
        """Process payment through payment processor"""
        
        # This is where you'd integrate with Stripe, PayPal, etc.
        # For now, return mock success
        
        if self.payment_processor:
            return self.payment_processor.charge(user_id, amount, description)
        
        # Mock implementation
        logger.info(f"Processing payment: ${amount} for user {user_id} - {description}")
        
        # Record transaction
        with get_db_session() as session:
            transaction = PaymentTransaction(
                user_id=user_id,
                amount=amount,
                currency='USD',
                status='completed',
                transaction_type='upgrade',
                description=description,
                gateway='mock',
                gateway_transaction_id=f"mock_{datetime.now().timestamp()}"
            )
            session.add(transaction)
            session.commit()
        
        return {'success': True, 'transaction_id': transaction.transaction_id}
    
    def _get_tier_unlock_message(self, old_tier: str, new_tier: str) -> str:
        """Generate message about newly unlocked features"""
        
        unlocks = {
            "NIBBLER": [],
            "FANG": ["🎯 Sniper Mode", "⚡ Chaingun", "📊 Advanced Filters"],
            "COMMANDER": ["🤖 Auto-Fire Mode", "👻 Stealth Mode", "🔧 Semi-Auto Toggle", "📈 Elite Strategies"],
            "APEX": ["🔨 Midnight Hammer", "♾️ Unlimited Trades", "🌟 Priority Support", "🏆 Elite Network"]
        }
        
        old_features = set()
        for tier in self.tier_order:
            if tier == old_tier:
                break
            old_features.update(unlocks[tier])
        
        new_features = []
        for tier in self.tier_order:
            if tier == new_tier:
                new_features.extend([f for f in unlocks[tier] if f not in old_features])
                break
            if self.tier_order.index(tier) > self.tier_order.index(old_tier):
                new_features.extend([f for f in unlocks[tier] if f not in old_features])
        
        return "\n".join(new_features) if new_features else "All features retained"
    
    def handle_subscription_callback(self, user_id: int, callback_data: str) -> CommandResult:
        """Handle subscription-related callbacks"""
        
        parts = callback_data.split('_')
        action = parts[0]
        
        if action == "upgrade" and len(parts) > 1:
            new_tier = parts[1]
            return self.process_tier_change(user_id, new_tier, UpgradeAction.UPGRADE)
            
        elif action == "downgrade" and len(parts) > 1:
            new_tier = parts[1]
            return self.process_tier_change(user_id, new_tier, UpgradeAction.DOWNGRADE)
            
        elif callback_data == "cancel_subscription":
            return self.cancel_subscription(user_id)
            
        elif callback_data == "reactivate_subscription":
            return self.reactivate_subscription(user_id)
            
        elif callback_data == "view_tier_benefits":
            return self.show_detailed_benefits(user_id)
            
        else:
            return CommandResult(False, "❌ Unknown action")
    
    def cancel_subscription(self, user_id: int) -> CommandResult:
        """Cancel user's subscription"""
        
        with get_db_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return CommandResult(False, "❌ User not found")
            
            if user.subscription_status != SubscriptionStatus.ACTIVE.value:
                return CommandResult(False, "❌ No active subscription to cancel")
            
            # Set to cancel at end of period
            user.subscription_status = SubscriptionStatus.CANCELLED.value
            session.commit()
            
            cancel_date = user.subscription_expires_at or datetime.now()
            
            return CommandResult(
                True,
                f"🚫 **Subscription Cancelled**\n\n"
                f"Your {user.tier} subscription will end on {cancel_date.strftime('%Y-%m-%d')}.\n"
                f"You'll retain access until then.\n\n"
                f"We're sorry to see you go, soldier. You can reactivate anytime."
            )
    
    def reactivate_subscription(self, user_id: int) -> CommandResult:
        """Reactivate cancelled subscription"""
        
        with get_db_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return CommandResult(False, "❌ User not found")
            
            if user.subscription_status != SubscriptionStatus.CANCELLED.value:
                return CommandResult(False, "❌ Subscription is not cancelled")
            
            # Process payment for current tier
            payment_result = self._process_payment(
                user_id, 
                self.tier_pricing[user.tier], 
                f"Reactivate {user.tier}"
            )
            
            if not payment_result['success']:
                return CommandResult(False, f"❌ Payment failed: {payment_result.get('error', 'Unknown error')}")
            
            # Reactivate subscription
            user.subscription_status = SubscriptionStatus.ACTIVE.value
            user.subscription_expires_at = datetime.now() + timedelta(days=30)
            session.commit()
            
            return CommandResult(
                True,
                f"✅ **Subscription Reactivated!**\n\n"
                f"Welcome back, soldier! Your {user.tier} powers are restored.\n"
                f"Next billing: {user.subscription_expires_at.strftime('%Y-%m-%d')}"
            )
    
    def show_detailed_benefits(self, user_id: int) -> CommandResult:
        """Show detailed tier benefits comparison"""
        
        message = """🎖️ **DETAILED TIER BENEFITS**

**🥉 NIBBLER ($39/mo)**
```
Daily Trades: 6
TCS Required: 75%
Risk Control: 2% fixed
Position Limit: 1
Cooldown: Trade completion
Features: Manual trading only
Perfect for: Beginners learning discipline
```

**🥈 FANG ($89/mo)**
```
Daily Trades: 10
TCS Required: 80% (sniper)
Risk Control: 2-2.5% boost
Position Limit: 2
Cooldown: Trade completion
Features: + Sniper mode
         + Chaingun (progressive risk)
         + Advanced filters
Perfect for: Developing traders
```

**🥇 COMMANDER ($139/mo)**
```
Daily Trades: 20
TCS Required: 90% auto / 75% semi
Risk Control: 2-3% boost
Position Limit: 5
Cooldown: 2 hours
Features: + Auto-fire mode
         + Semi-auto toggle
         + Stealth mode
         + All strategies
Perfect for: Serious traders
```

**💎 APEX ($188/mo)**
```
Daily Trades: Unlimited
TCS Required: 91%
Risk Control: 2-3% boost
Position Limit: 10
Cooldown: None
Features: + Midnight Hammer
         + Priority support
         + Elite network
         + Beta features
Perfect for: Professional traders
```

Use `/upgrade` to change your tier!"""
        
        return CommandResult(True, message)

# Create singleton instance
_upgrade_router = None

def get_upgrade_router(payment_processor=None) -> TierUpgradeRouter:
    """Get or create upgrade router instance"""
    global _upgrade_router
    if _upgrade_router is None:
        _upgrade_router = TierUpgradeRouter(payment_processor)
    return _upgrade_router