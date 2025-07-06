"""
BITTEN Subscription Manager
Handles subscription lifecycle, billing, renewals, and tier management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from enum import Enum
import json
import asyncio
from decimal import Decimal

from .database.connection import get_db_session
from .database.models import (
    User, UserProfile, SubscriptionPlan, UserSubscription, 
    PaymentTransaction, TierLevel, SubscriptionStatus
)
from .telegram_router import CommandResult
from .fire_modes import TIER_CONFIGS
from .risk_controller import get_risk_controller
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

class BillingCycle(Enum):
    """Billing cycle options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class PaymentStatus(Enum):
    """Payment transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class SubscriptionEvent(Enum):
    """Subscription lifecycle events"""
    CREATED = "subscription_created"
    ACTIVATED = "subscription_activated"
    RENEWED = "subscription_renewed"
    UPGRADED = "subscription_upgraded"
    DOWNGRADED = "subscription_downgraded"
    CANCELLED = "subscription_cancelled"
    EXPIRED = "subscription_expired"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_RETRY = "payment_retry"
    TRIAL_ENDING = "trial_ending"

class SubscriptionManager:
    """Manages all subscription-related operations"""
    
    def __init__(self, payment_processor=None, notification_service=None):
        self.payment_processor = payment_processor
        self.notification_service = notification_service
        
        # Pricing configuration
        self.tier_pricing = {
            BillingCycle.MONTHLY: {
                "NIBBLER": 39,
                "FANG": 89,
                "COMMANDER": 139,
                "APEX": 188
            },
            BillingCycle.QUARTERLY: {
                "NIBBLER": 105,      # ~10% discount
                "FANG": 240,         # ~10% discount
                "COMMANDER": 375,    # ~10% discount
                "APEX": 507          # ~10% discount
            },
            BillingCycle.ANNUAL: {
                "NIBBLER": 374,      # ~20% discount
                "FANG": 854,         # ~20% discount
                "COMMANDER": 1339,   # ~20% discount
                "APEX": 1805         # ~20% discount
            }
        }
        
        # Grace period settings
        self.grace_period_days = 3
        self.retry_intervals = [1, 3, 5]  # Days to retry failed payments
        
        # Trial settings
        self.trial_duration_days = 7
        self.trial_allowed_tiers = ["NIBBLER"]
        
        logger.info("Subscription Manager initialized")
    
    async def create_subscription(self, user_id: int, tier: str, 
                                billing_cycle: BillingCycle = BillingCycle.MONTHLY,
                                trial: bool = False) -> CommandResult:
        """Create new subscription for user"""
        
        with get_db_session() as session:
            try:
                # Check if user exists
                user = session.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return CommandResult(False, "❌ User not found")
                
                # Check for existing active subscription
                existing = session.query(UserSubscription).filter(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status.in_([
                        SubscriptionStatus.ACTIVE.value,
                        SubscriptionStatus.TRIALING.value
                    ])
                ).first()
                
                if existing:
                    return CommandResult(False, "❌ Active subscription already exists")
                
                # Validate tier
                if tier not in self.tier_pricing[BillingCycle.MONTHLY]:
                    return CommandResult(False, "❌ Invalid tier")
                
                # Check trial eligibility
                if trial:
                    if tier not in self.trial_allowed_tiers:
                        return CommandResult(False, f"❌ Trial not available for {tier} tier")
                    
                    # Check if user had trial before
                    had_trial = session.query(UserSubscription).filter(
                        UserSubscription.user_id == user_id,
                        UserSubscription.status == SubscriptionStatus.TRIALING.value
                    ).first()
                    
                    if had_trial:
                        return CommandResult(False, "❌ Trial already used")
                
                # Calculate dates
                start_date = datetime.now()
                if trial:
                    end_date = start_date + timedelta(days=self.trial_duration_days)
                    next_billing = end_date
                    amount = 0
                else:
                    if billing_cycle == BillingCycle.MONTHLY:
                        end_date = start_date + timedelta(days=30)
                    elif billing_cycle == BillingCycle.QUARTERLY:
                        end_date = start_date + timedelta(days=90)
                    else:  # Annual
                        end_date = start_date + timedelta(days=365)
                    
                    next_billing = end_date
                    amount = self.tier_pricing[billing_cycle][tier]
                
                # Process payment if not trial
                if not trial:
                    payment_result = await self._process_payment(
                        user_id, amount, 
                        f"New {tier} subscription - {billing_cycle.value}"
                    )
                    
                    if not payment_result['success']:
                        return CommandResult(False, f"❌ Payment failed: {payment_result['error']}")
                
                # Create subscription record
                subscription = UserSubscription(
                    user_id=user_id,
                    plan_name=tier,
                    billing_cycle=billing_cycle.value,
                    price=amount,
                    status=SubscriptionStatus.TRIALING.value if trial else SubscriptionStatus.ACTIVE.value,
                    started_at=start_date,
                    current_period_start=start_date,
                    current_period_end=end_date,
                    next_billing_date=next_billing,
                    trial_end=end_date if trial else None,
                    auto_renew=True,
                    metadata=json.dumps({
                        'original_tier': user.tier,
                        'billing_cycle': billing_cycle.value,
                        'is_trial': trial
                    })
                )
                session.add(subscription)
                
                # Update user tier and status
                user.tier = tier
                user.subscription_status = subscription.status
                user.subscription_expires_at = end_date
                
                # Update risk controller
                risk_controller = get_risk_controller()
                risk_controller.update_user_tier(user_id, tier)
                
                # Track event
                await self._track_event(
                    SubscriptionEvent.CREATED,
                    user_id,
                    {'tier': tier, 'billing_cycle': billing_cycle.value, 'trial': trial}
                )
                
                session.commit()
                
                # Send confirmation
                if trial:
                    message = f"""✅ **TRIAL ACTIVATED!**

**Tier**: {tier}
**Duration**: {self.trial_duration_days} days
**Expires**: {end_date.strftime('%Y-%m-%d')}

🎯 Your {tier} features are now active!
Use `/fire` to start trading.

⚠️ **Note**: Full subscription required after trial ends."""
                else:
                    message = f"""✅ **SUBSCRIPTION ACTIVATED!**

**Tier**: {tier}
**Billing**: {billing_cycle.value.title()}
**Amount**: ${amount}
**Next Billing**: {next_billing.strftime('%Y-%m-%d')}

🎯 Your {tier} features are now active!
Use `/fire` to start trading."""
                
                # Send notification
                if self.notification_service:
                    await self.notification_service.send_subscription_confirmation(
                        user_id, tier, billing_cycle, amount, trial
                    )
                
                return CommandResult(True, message)
                
            except Exception as e:
                logger.error(f"Error creating subscription: {e}")
                session.rollback()
                return CommandResult(False, "❌ Failed to create subscription")
    
    async def renew_subscription(self, user_id: int, auto_renew: bool = True) -> CommandResult:
        """Renew existing subscription"""
        
        with get_db_session() as session:
            try:
                # Get current subscription
                subscription = session.query(UserSubscription).filter(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status.in_([
                        SubscriptionStatus.ACTIVE.value,
                        SubscriptionStatus.PAST_DUE.value
                    ])
                ).first()
                
                if not subscription:
                    return CommandResult(False, "❌ No active subscription found")
                
                # Calculate renewal amount
                billing_cycle = BillingCycle(subscription.billing_cycle)
                amount = self.tier_pricing[billing_cycle][subscription.plan_name]
                
                # Process payment
                payment_result = await self._process_payment(
                    user_id, amount,
                    f"Renewal - {subscription.plan_name} {billing_cycle.value}"
                )
                
                if not payment_result['success']:
                    # Mark as past due
                    subscription.status = SubscriptionStatus.PAST_DUE.value
                    subscription.metadata = json.dumps({
                        **json.loads(subscription.metadata or '{}'),
                        'last_payment_attempt': datetime.now().isoformat(),
                        'payment_error': payment_result.get('error', 'Unknown error')
                    })
                    session.commit()
                    
                    await self._track_event(
                        SubscriptionEvent.PAYMENT_FAILED,
                        user_id,
                        {'error': payment_result.get('error')}
                    )
                    
                    return CommandResult(False, f"❌ Payment failed: {payment_result['error']}")
                
                # Update subscription dates
                old_end = subscription.current_period_end
                if billing_cycle == BillingCycle.MONTHLY:
                    new_end = old_end + timedelta(days=30)
                elif billing_cycle == BillingCycle.QUARTERLY:
                    new_end = old_end + timedelta(days=90)
                else:  # Annual
                    new_end = old_end + timedelta(days=365)
                
                subscription.current_period_start = old_end
                subscription.current_period_end = new_end
                subscription.next_billing_date = new_end
                subscription.status = SubscriptionStatus.ACTIVE.value
                subscription.renewed_at = datetime.now()
                subscription.auto_renew = auto_renew
                
                # Update user
                user = session.query(User).filter(User.user_id == user_id).first()
                user.subscription_expires_at = new_end
                user.subscription_status = SubscriptionStatus.ACTIVE.value
                
                # Track event
                await self._track_event(
                    SubscriptionEvent.RENEWED,
                    user_id,
                    {
                        'tier': subscription.plan_name,
                        'amount': amount,
                        'new_period_end': new_end.isoformat()
                    }
                )
                
                session.commit()
                
                message = f"""✅ **SUBSCRIPTION RENEWED!**

**Tier**: {subscription.plan_name}
**Amount**: ${amount}
**Period**: {old_end.strftime('%Y-%m-%d')} → {new_end.strftime('%Y-%m-%d')}
**Next Billing**: {new_end.strftime('%Y-%m-%d')}

Your {subscription.plan_name} features continue uninterrupted!"""
                
                return CommandResult(True, message)
                
            except Exception as e:
                logger.error(f"Error renewing subscription: {e}")
                session.rollback()
                return CommandResult(False, "❌ Failed to renew subscription")
    
    async def cancel_subscription(self, user_id: int, immediate: bool = False,
                                reason: Optional[str] = None) -> CommandResult:
        """Cancel subscription at end of period or immediately"""
        
        with get_db_session() as session:
            try:
                # Get active subscription
                subscription = session.query(UserSubscription).filter(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == SubscriptionStatus.ACTIVE.value
                ).first()
                
                if not subscription:
                    return CommandResult(False, "❌ No active subscription found")
                
                user = session.query(User).filter(User.user_id == user_id).first()
                
                if immediate:
                    # Cancel immediately and calculate refund
                    days_used = (datetime.now() - subscription.current_period_start).days
                    total_days = (subscription.current_period_end - subscription.current_period_start).days
                    days_remaining = max(0, total_days - days_used)
                    
                    # Calculate prorated refund
                    daily_rate = subscription.price / total_days
                    refund_amount = round(daily_rate * days_remaining, 2)
                    
                    # Process refund if applicable
                    if refund_amount > 0:
                        refund_result = await self._process_refund(
                            user_id, refund_amount,
                            f"Immediate cancellation refund - {days_remaining} days"
                        )
                        
                        if not refund_result['success']:
                            logger.error(f"Refund failed for user {user_id}: {refund_result['error']}")
                    
                    # Update subscription
                    subscription.status = SubscriptionStatus.CANCELLED.value
                    subscription.cancelled_at = datetime.now()
                    subscription.ends_at = datetime.now()
                    subscription.auto_renew = False
                    subscription.metadata = json.dumps({
                        **json.loads(subscription.metadata or '{}'),
                        'cancellation_reason': reason,
                        'immediate': True,
                        'refund_amount': refund_amount
                    })
                    
                    # Downgrade to free tier immediately
                    user.tier = "NIBBLER"  # Or whatever your free tier is
                    user.subscription_status = SubscriptionStatus.CANCELLED.value
                    user.subscription_expires_at = None
                    
                    # Update risk controller
                    risk_controller = get_risk_controller()
                    risk_controller.update_user_tier(user_id, "NIBBLER")
                    
                    message = f"""🚫 **SUBSCRIPTION CANCELLED**

Your {subscription.plan_name} subscription has been cancelled immediately.

**Refund**: ${refund_amount} (for {days_remaining} unused days)
**New Tier**: NIBBLER (Free)
**Effective**: Immediately

Thank you for being part of the BITTEN network."""
                    
                else:
                    # Cancel at end of period
                    subscription.auto_renew = False
                    subscription.cancelled_at = datetime.now()
                    subscription.metadata = json.dumps({
                        **json.loads(subscription.metadata or '{}'),
                        'cancellation_reason': reason,
                        'immediate': False
                    })
                    
                    # User keeps access until period ends
                    user.subscription_status = SubscriptionStatus.CANCELLED.value
                    
                    message = f"""📅 **SUBSCRIPTION SCHEDULED FOR CANCELLATION**

Your {subscription.plan_name} subscription will end on {subscription.current_period_end.strftime('%Y-%m-%d')}.

**Current Tier**: {subscription.plan_name} (until expiry)
**After Expiry**: NIBBLER (Free)
**Days Remaining**: {(subscription.current_period_end - datetime.now()).days}

You can reactivate anytime before expiry using `/upgrade`."""
                
                # Track event
                await self._track_event(
                    SubscriptionEvent.CANCELLED,
                    user_id,
                    {
                        'tier': subscription.plan_name,
                        'immediate': immediate,
                        'reason': reason
                    }
                )
                
                session.commit()
                
                # Send notification
                if self.notification_service:
                    await self.notification_service.send_cancellation_confirmation(
                        user_id, subscription.plan_name, immediate
                    )
                
                return CommandResult(True, message)
                
            except Exception as e:
                logger.error(f"Error cancelling subscription: {e}")
                session.rollback()
                return CommandResult(False, "❌ Failed to cancel subscription")
    
    async def check_expiring_subscriptions(self) -> List[Dict]:
        """Check for subscriptions expiring soon and send reminders"""
        
        expiring_soon = []
        
        with get_db_session() as session:
            try:
                # Check subscriptions expiring in next 7 days
                expiry_threshold = datetime.now() + timedelta(days=7)
                
                subscriptions = session.query(UserSubscription).filter(
                    UserSubscription.status == SubscriptionStatus.ACTIVE.value,
                    UserSubscription.auto_renew == False,
                    UserSubscription.current_period_end <= expiry_threshold,
                    UserSubscription.current_period_end > datetime.now()
                ).all()
                
                for sub in subscriptions:
                    days_until_expiry = (sub.current_period_end - datetime.now()).days
                    
                    # Send reminders at 7, 3, and 1 days
                    if days_until_expiry in [7, 3, 1]:
                        user = session.query(User).filter(User.user_id == sub.user_id).first()
                        
                        expiring_soon.append({
                            'user_id': sub.user_id,
                            'tier': sub.plan_name,
                            'expires_in_days': days_until_expiry,
                            'username': user.username if user else 'Unknown'
                        })
                        
                        # Send reminder notification
                        if self.notification_service:
                            await self.notification_service.send_expiry_reminder(
                                sub.user_id, sub.plan_name, days_until_expiry
                            )
                
                # Check for trial ending
                trial_threshold = datetime.now() + timedelta(days=2)
                trials = session.query(UserSubscription).filter(
                    UserSubscription.status == SubscriptionStatus.TRIALING.value,
                    UserSubscription.trial_end <= trial_threshold,
                    UserSubscription.trial_end > datetime.now()
                ).all()
                
                for trial in trials:
                    days_until_end = (trial.trial_end - datetime.now()).days
                    
                    if days_until_end in [2, 1, 0]:
                        await self._track_event(
                            SubscriptionEvent.TRIAL_ENDING,
                            trial.user_id,
                            {'days_remaining': days_until_end}
                        )
                        
                        # Send trial ending notification
                        if self.notification_service:
                            await self.notification_service.send_trial_ending_reminder(
                                trial.user_id, trial.plan_name, days_until_end
                            )
                
                return expiring_soon
                
            except Exception as e:
                logger.error(f"Error checking expiring subscriptions: {e}")
                return []
    
    async def process_expired_subscriptions(self) -> int:
        """Process all expired subscriptions"""
        
        processed_count = 0
        
        with get_db_session() as session:
            try:
                # Find expired active subscriptions
                expired = session.query(UserSubscription).filter(
                    UserSubscription.status.in_([
                        SubscriptionStatus.ACTIVE.value,
                        SubscriptionStatus.TRIALING.value
                    ]),
                    UserSubscription.current_period_end <= datetime.now()
                ).all()
                
                for sub in expired:
                    user = session.query(User).filter(User.user_id == sub.user_id).first()
                    if not user:
                        continue
                    
                    if sub.auto_renew and sub.status == SubscriptionStatus.ACTIVE.value:
                        # Attempt auto-renewal
                        renewal_result = await self.renew_subscription(sub.user_id, auto_renew=True)
                        if renewal_result.success:
                            processed_count += 1
                            continue
                    
                    # Mark as expired
                    sub.status = SubscriptionStatus.EXPIRED.value
                    sub.ends_at = datetime.now()
                    
                    # Downgrade user to free tier
                    user.tier = "NIBBLER"
                    user.subscription_status = SubscriptionStatus.EXPIRED.value
                    user.subscription_expires_at = None
                    
                    # Update risk controller
                    risk_controller = get_risk_controller()
                    risk_controller.update_user_tier(sub.user_id, "NIBBLER")
                    
                    # Track event
                    await self._track_event(
                        SubscriptionEvent.EXPIRED,
                        sub.user_id,
                        {'previous_tier': sub.plan_name}
                    )
                    
                    # Send expiry notification
                    if self.notification_service:
                        await self.notification_service.send_subscription_expired(
                            sub.user_id, sub.plan_name
                        )
                    
                    processed_count += 1
                
                session.commit()
                logger.info(f"Processed {processed_count} expired subscriptions")
                
                return processed_count
                
            except Exception as e:
                logger.error(f"Error processing expired subscriptions: {e}")
                session.rollback()
                return processed_count
    
    async def retry_failed_payments(self) -> int:
        """Retry failed payment attempts"""
        
        retry_count = 0
        
        with get_db_session() as session:
            try:
                # Find subscriptions in past due status
                past_due = session.query(UserSubscription).filter(
                    UserSubscription.status == SubscriptionStatus.PAST_DUE.value
                ).all()
                
                for sub in past_due:
                    metadata = json.loads(sub.metadata or '{}')
                    last_attempt = metadata.get('last_payment_attempt')
                    
                    if last_attempt:
                        last_attempt_date = datetime.fromisoformat(last_attempt)
                        days_since_attempt = (datetime.now() - last_attempt_date).days
                        
                        # Check if it's time to retry based on retry intervals
                        if days_since_attempt not in self.retry_intervals:
                            continue
                    
                    # Attempt payment retry
                    retry_result = await self.renew_subscription(sub.user_id, auto_renew=sub.auto_renew)
                    
                    if retry_result.success:
                        retry_count += 1
                        
                        # Track successful retry
                        await self._track_event(
                            SubscriptionEvent.PAYMENT_RETRY,
                            sub.user_id,
                            {'success': True, 'attempt_number': len(self.retry_intervals)}
                        )
                    else:
                        # Check if we've exhausted retries
                        if days_since_attempt >= max(self.retry_intervals) + self.grace_period_days:
                            # Cancel subscription
                            await self.cancel_subscription(sub.user_id, immediate=True, 
                                                        reason="Payment retry failed")
                
                return retry_count
                
            except Exception as e:
                logger.error(f"Error retrying failed payments: {e}")
                return retry_count
    
    async def get_subscription_status(self, user_id: int) -> Dict:
        """Get detailed subscription status for user"""
        
        with get_db_session() as session:
            try:
                user = session.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return {'error': 'User not found'}
                
                subscription = session.query(UserSubscription).filter(
                    UserSubscription.user_id == user_id
                ).order_by(UserSubscription.created_at.desc()).first()
                
                if not subscription:
                    return {
                        'status': 'never_subscribed',
                        'tier': user.tier,
                        'can_subscribe': True
                    }
                
                # Calculate days remaining
                days_remaining = 0
                if subscription.current_period_end and subscription.current_period_end > datetime.now():
                    days_remaining = (subscription.current_period_end - datetime.now()).days
                
                # Get payment history
                payments = session.query(PaymentTransaction).filter(
                    PaymentTransaction.user_id == user_id,
                    PaymentTransaction.transaction_type.in_(['subscription', 'renewal', 'upgrade'])
                ).order_by(PaymentTransaction.created_at.desc()).limit(5).all()
                
                payment_history = []
                for payment in payments:
                    payment_history.append({
                        'date': payment.created_at.isoformat(),
                        'amount': float(payment.amount),
                        'type': payment.transaction_type,
                        'status': payment.status
                    })
                
                return {
                    'status': subscription.status,
                    'tier': subscription.plan_name,
                    'billing_cycle': subscription.billing_cycle,
                    'price': float(subscription.price),
                    'started_at': subscription.started_at.isoformat() if subscription.started_at else None,
                    'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                    'days_remaining': days_remaining,
                    'auto_renew': subscription.auto_renew,
                    'is_trial': subscription.trial_end is not None,
                    'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
                    'cancelled_at': subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
                    'payment_history': payment_history
                }
                
            except Exception as e:
                logger.error(f"Error getting subscription status: {e}")
                return {'error': str(e)}
    
    async def apply_promo_code(self, user_id: int, promo_code: str) -> CommandResult:
        """Apply promotional code to subscription"""
        
        # This would integrate with a promo code system
        # For now, return a placeholder
        return CommandResult(False, "❌ Promo code system not yet implemented")
    
    async def _process_payment(self, user_id: int, amount: float, description: str) -> Dict:
        """Process payment through payment processor"""
        
        if self.payment_processor:
            return await self.payment_processor.charge(user_id, amount, description)
        
        # Mock implementation for testing
        logger.info(f"Mock payment: ${amount} for user {user_id} - {description}")
        
        # Record transaction
        with get_db_session() as session:
            transaction = PaymentTransaction(
                user_id=user_id,
                amount=amount,
                currency='USD',
                status=PaymentStatus.COMPLETED.value,
                transaction_type='subscription',
                description=description,
                gateway='mock',
                gateway_transaction_id=f"mock_{datetime.now().timestamp()}"
            )
            session.add(transaction)
            session.commit()
        
        return {'success': True, 'transaction_id': transaction.transaction_id}
    
    async def _process_refund(self, user_id: int, amount: float, reason: str) -> Dict:
        """Process refund through payment processor"""
        
        if self.payment_processor:
            return await self.payment_processor.refund(user_id, amount, reason)
        
        # Mock implementation
        logger.info(f"Mock refund: ${amount} for user {user_id} - {reason}")
        
        with get_db_session() as session:
            transaction = PaymentTransaction(
                user_id=user_id,
                amount=-amount,  # Negative for refund
                currency='USD',
                status=PaymentStatus.REFUNDED.value,
                transaction_type='refund',
                description=reason,
                gateway='mock',
                gateway_transaction_id=f"refund_{datetime.now().timestamp()}"
            )
            session.add(transaction)
            session.commit()
        
        return {'success': True, 'transaction_id': transaction.transaction_id}
    
    async def _track_event(self, event: SubscriptionEvent, user_id: int, data: Dict):
        """Track subscription lifecycle events"""
        
        try:
            logger.info(f"Subscription event: {event.value} for user {user_id} - {data}")
            
            # This would send to analytics service
            if hasattr(self, 'analytics_service'):
                await self.analytics_service.track(event.value, user_id, data)
                
        except Exception as e:
            logger.error(f"Error tracking subscription event: {e}")

# Create singleton instance
_subscription_manager = None

def get_subscription_manager(payment_processor=None, notification_service=None) -> SubscriptionManager:
    """Get or create subscription manager instance"""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager(payment_processor, notification_service)
    return _subscription_manager

# Background task runner
async def run_subscription_maintenance():
    """Run periodic subscription maintenance tasks"""
    
    manager = get_subscription_manager()
    
    while True:
        try:
            # Check expiring subscriptions every 6 hours
            await manager.check_expiring_subscriptions()
            
            # Process expired subscriptions
            await manager.process_expired_subscriptions()
            
            # Retry failed payments
            await manager.retry_failed_payments()
            
            # Sleep for 6 hours
            await asyncio.sleep(6 * 60 * 60)
            
        except Exception as e:
            logger.error(f"Error in subscription maintenance: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error