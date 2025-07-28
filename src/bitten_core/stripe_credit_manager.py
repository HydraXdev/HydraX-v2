#!/usr/bin/env python3
"""
BITTEN Stripe Credit Manager
Handles automatic credit application to Stripe invoices and subscription billing
"""

import logging
import stripe
from typing import Dict, Optional, Tuple
from decimal import Decimal

from .credit_referral_system import get_credit_referral_system

logger = logging.getLogger(__name__)

class StripeCreditManager:
    """Manages credit application for Stripe billing"""
    
    def __init__(self, stripe_api_key: Optional[str] = None):
        if stripe_api_key:
            stripe.api_key = stripe_api_key
        self.referral_system = get_credit_referral_system()
    
    def apply_credits_to_invoice(self, customer_id: str, invoice_id: str, user_id: str) -> Dict:
        """Apply available credits to a Stripe invoice before payment"""
        try:
            # Get invoice details
            invoice = stripe.Invoice.retrieve(invoice_id)
            original_amount = invoice.amount_due / 100  # Convert from cents
            
            if original_amount <= 0:
                return {
                    'success': True,
                    'credit_applied': 0.0,
                    'final_amount': 0.0,
                    'message': 'Invoice already paid or has no amount due'
                }
            
            # Get user's available credits
            balance = self.referral_system.get_user_credit_balance(user_id)
            
            if balance.total_credits <= 0:
                return {
                    'success': True,
                    'credit_applied': 0.0,
                    'final_amount': original_amount,
                    'message': 'No credits available to apply'
                }
            
            # Calculate credit to apply
            credit_to_apply, final_amount = self.referral_system.apply_credit_to_invoice(
                user_id, original_amount, invoice_id
            )
            
            if credit_to_apply > 0:
                # Apply credit as discount to invoice
                credit_amount_cents = int(credit_to_apply * 100)
                
                # Create a coupon for this specific credit amount
                coupon_id = f"credit_{user_id}_{invoice_id}_{int(credit_to_apply * 100)}"
                
                try:
                    coupon = stripe.Coupon.create(
                        id=coupon_id,
                        amount_off=credit_amount_cents,
                        currency='usd',
                        duration='once',
                        name=f'Referral Credit - ${credit_to_apply:.0f}',
                        max_redemptions=1
                    )
                    
                    # Apply coupon to customer for this invoice
                    stripe.Customer.modify(
                        customer_id,
                        coupon=coupon_id
                    )
                    
                    # Refresh invoice to apply the coupon
                    invoice = stripe.Invoice.retrieve(invoice_id)
                    
                    logger.info(f"Applied ${credit_to_apply:.2f} credit to invoice {invoice_id} for user {user_id}")
                    
                    return {
                        'success': True,
                        'credit_applied': credit_to_apply,
                        'final_amount': final_amount,
                        'original_amount': original_amount,
                        'coupon_id': coupon_id,
                        'message': f'Applied ${credit_to_apply:.0f} credit to your invoice'
                    }
                    
                except stripe.error.StripeError as e:
                    logger.error(f"Stripe error applying credit: {e}")
                    # Rollback credit application in our system
                    self.referral_system.apply_credit_to_invoice(user_id, -credit_to_apply, f"ROLLBACK_{invoice_id}")
                    
                    return {
                        'success': False,
                        'error': f'Failed to apply credit to Stripe: {str(e)}',
                        'credit_applied': 0.0,
                        'final_amount': original_amount
                    }
            
            return {
                'success': True,
                'credit_applied': 0.0,
                'final_amount': original_amount,
                'message': 'No credits to apply'
            }
            
        except Exception as e:
            logger.error(f"Error applying credits to invoice {invoice_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'credit_applied': 0.0,
                'final_amount': original_amount if 'original_amount' in locals() else 0.0
            }
    
    def handle_subscription_invoice_created(self, invoice_data: Dict) -> Dict:
        """Handle Stripe webhook for invoice.created - apply credits before payment attempt"""
        try:
            invoice_id = invoice_data['id']
            customer_id = invoice_data['customer']
            
            # Get user_id from customer metadata or lookup
            user_id = self._get_user_id_from_customer(customer_id)
            if not user_id:
                logger.warning(f"Could not find user_id for customer {customer_id}")
                return {'success': False, 'error': 'User not found'}
            
            # Apply credits to the invoice
            result = self.apply_credits_to_invoice(customer_id, invoice_id, user_id)
            
            if result['success'] and result['credit_applied'] > 0:
                logger.info(f"Auto-applied ${result['credit_applied']:.2f} credit to invoice {invoice_id}")
                
                # Send notification to user (this would integrate with your bot)
                self._send_credit_applied_notification(user_id, result['credit_applied'], result['final_amount'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error in subscription invoice created handler: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_payment_succeeded(self, payment_intent_data: Dict) -> Dict:
        """Handle successful payment - confirm referral credits for new subscribers"""
        try:
            customer_id = payment_intent_data.get('customer')
            invoice_id = payment_intent_data.get('invoice')
            
            if not customer_id:
                return {'success': False, 'error': 'No customer in payment data'}
            
            # Get user_id from customer
            user_id = self._get_user_id_from_customer(customer_id)
            if not user_id:
                logger.warning(f"Could not find user_id for customer {customer_id}")
                return {'success': False, 'error': 'User not found'}
            
            # Check if this is a first payment (new subscriber)
            if self._is_first_payment(customer_id):
                # Confirm payment and apply credit to referrer
                referrer_id = self.referral_system.confirm_payment_and_apply_credit(user_id, invoice_id)
                
                if referrer_id:
                    logger.info(f"Confirmed referral credit for {referrer_id} due to {user_id} first payment")
                    
                    # Send notification to referrer
                    self._send_referral_credit_notification(referrer_id, 10.0)
                    
                    return {
                        'success': True,
                        'referrer_credited': referrer_id,
                        'credit_amount': 10.0,
                        'message': f'Applied $10 credit to referrer {referrer_id}'
                    }
            
            return {'success': True, 'message': 'Payment processed, no referral credit applicable'}
            
        except Exception as e:
            logger.error(f"Error in payment succeeded handler: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_user_id_from_customer(self, customer_id: str) -> Optional[str]:
        """Get user_id from Stripe customer metadata"""
        try:
            customer = stripe.Customer.retrieve(customer_id)
            # Assuming user_id is stored in metadata
            return customer.metadata.get('user_id') or customer.metadata.get('telegram_id')
        except Exception as e:
            logger.error(f"Error retrieving customer {customer_id}: {e}")
            return None
    
    def _is_first_payment(self, customer_id: str) -> bool:
        """Check if this is the customer's first successful payment"""
        try:
            # Get all successful payment intents for this customer
            payments = stripe.PaymentIntent.list(
                customer=customer_id,
                limit=10
            )
            
            # Count successful payments (excluding the current one being processed)
            successful_payments = [p for p in payments.data if p.status == 'succeeded']
            
            # If this is the first or second successful payment, consider it "first" 
            # (account for potential timing issues)
            return len(successful_payments) <= 2
            
        except Exception as e:
            logger.error(f"Error checking first payment for customer {customer_id}: {e}")
            return False
    
    def _send_credit_applied_notification(self, user_id: str, credit_applied: float, final_amount: float):
        """Send notification when credit is applied to invoice"""
        # This would integrate with your Telegram bot
        # For now, just log it
        logger.info(f"NOTIFICATION: User {user_id} - ${credit_applied:.0f} credit applied, final amount: ${final_amount:.2f}")
    
    def _send_referral_credit_notification(self, referrer_id: str, credit_amount: float):
        """Send notification when referral credit is earned"""
        # This would integrate with your Telegram bot
        # For now, just log it
        logger.info(f"NOTIFICATION: User {referrer_id} earned ${credit_amount:.0f} referral credit")
    
    def get_customer_credit_summary(self, customer_id: str) -> Dict:
        """Get credit summary for a Stripe customer"""
        user_id = self._get_user_id_from_customer(customer_id)
        if not user_id:
            return {'error': 'User not found'}
        
        balance = self.referral_system.get_user_credit_balance(user_id)
        stats = self.referral_system.get_referral_stats(user_id)
        
        return {
            'user_id': user_id,
            'customer_id': customer_id,
            'available_credits': balance.total_credits,
            'pending_credits': balance.pending_credits,
            'total_referrals': balance.referral_count,
            'referral_code': stats['referral_code'],
            'free_months_earned': stats['free_months_earned']
        }
    
    def manually_apply_credit(self, user_id: str, amount: float, reason: str = "Manual adjustment") -> Dict:
        """Manually apply credit to a user (admin function)"""
        try:
            # Add credit to user's balance
            with sqlite3.connect(self.referral_system.db_path) as conn:
                self.referral_system._update_user_balance(conn, user_id, total_credit=amount)
                
                # Log the manual credit
                conn.execute("""
                    INSERT INTO referral_credits 
                    (referrer_id, referred_user_id, referral_code, credit_amount, credited, payment_confirmed)
                    VALUES (?, ?, ?, ?, 1, 1)
                """, ('ADMIN', user_id, f'MANUAL_{reason}', amount))
                
                conn.commit()
            
            logger.info(f"Manually applied ${amount:.2f} credit to user {user_id}: {reason}")
            
            return {
                'success': True,
                'amount': amount,
                'user_id': user_id,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Error manually applying credit: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
_stripe_credit_manager = None

def get_stripe_credit_manager() -> StripeCreditManager:
    """Get global Stripe credit manager instance"""
    global _stripe_credit_manager
    if _stripe_credit_manager is None:
        _stripe_credit_manager = StripeCreditManager()
    return _stripe_credit_manager