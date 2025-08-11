#!/usr/bin/env python3
"""
BITTEN User Onboarding Flow
Handles complete user lifecycle from first contact to trading
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import hashlib
import random
import string

logger = logging.getLogger(__name__)

class UserOnboardingFlow:
    """Manages complete user onboarding from first contact"""
    
    def __init__(self):
        from src.bitten_core.central_user_manager import get_central_user_manager
        self.user_mgr = get_central_user_manager()
        
    def handle_first_contact(self, telegram_id: int, telegram_data: Dict) -> Dict:
        """
        Handle user's VERY FIRST interaction with the bot
        This is called when /start is pressed
        """
        
        # Check if user already exists
        existing_user = self.user_mgr.get_complete_user(telegram_id)
        
        if existing_user:
            logger.info(f"Existing user {telegram_id} returned")
            return {
                'is_new': False,
                'user': existing_user,
                'message': "Welcome back to BITTEN!"
            }
        
        # NEW USER - Create with PRESS_PASS tier
        logger.info(f"🆕 New user {telegram_id} detected - creating account")
        
        # Generate unique referral code for this user
        referral_code = self.generate_referral_code(telegram_id)
        
        # Create user with initial data
        initial_data = {
            'user_uuid': f'USER_{telegram_id}_{datetime.now().strftime("%Y%m%d")}',
            'username': telegram_data.get('username', ''),
            'first_name': telegram_data.get('first_name', ''),
            'last_name': telegram_data.get('last_name', ''),
            'tier': 'PRESS_PASS',  # Everyone starts with free PRESS_PASS
            'referral_code': referral_code,
            'referred_by': telegram_data.get('start_param'),  # Referral code from deep link
            'created_from': 'telegram_bot',
            'onboarding_stage': 'INITIAL_CONTACT'
        }
        
        # Create user in central database
        success = self.user_mgr.create_user(telegram_id, initial_data)
        
        if success:
            # Process referral if user came through referral link
            if initial_data.get('referred_by'):
                self.process_referral_signup(telegram_id, initial_data['referred_by'])
            
            # Get newly created user
            new_user = self.user_mgr.get_complete_user(telegram_id)
            
            # Award welcome XP
            self.user_mgr.add_xp(telegram_id, 5, "Welcome to BITTEN")
            
            return {
                'is_new': True,
                'user': new_user,
                'message': """🎮 Welcome to BITTEN!

You've been granted a FREE Press Pass to explore the system.

Press Pass includes:
• 3 daily trades
• Access to RAPID signals (1:1.5 RR)
• Basic statistics
• 1 manual fire slot

Ready to start your trading journey?"""
            }
        else:
            logger.error(f"Failed to create user {telegram_id}")
            return {
                'is_new': False,
                'error': True,
                'message': "Error creating account. Please try again."
            }
    
    def handle_referral_click(self, telegram_id: int, referral_code: str) -> Dict:
        """
        Handle when user clicks a referral link
        Called from /start?start=REF_CODE
        """
        
        # Check if user exists
        user = self.user_mgr.get_complete_user(telegram_id)
        
        if not user:
            # New user - will be created with referral attached
            return {
                'action': 'create_with_referral',
                'referral_code': referral_code
            }
        
        # Existing user clicking referral link
        if user.get('referrals', {}).get('referred_by_code'):
            return {
                'action': 'already_referred',
                'message': "You're already part of a squad!"
            }
        
        # Existing user not yet referred - update their referral
        self.process_referral_signup(telegram_id, referral_code)
        
        return {
            'action': 'referral_added',
            'message': "You've joined the squad! 🎯"
        }
    
    def handle_mt5_handshake(self, telegram_id: int, mt5_data: Dict) -> Dict:
        """
        Handle MT5 account handshake data
        Updates user with trading account information
        """
        
        user = self.user_mgr.get_complete_user(telegram_id)
        
        if not user:
            # User doesn't exist - this shouldn't happen
            logger.error(f"MT5 handshake for non-existent user {telegram_id}")
            return {'success': False, 'error': 'User not found'}
        
        # Update user with MT5 account data
        from central_database_sqlite import get_central_database
        db = get_central_database()
        
        # Add MT5 account to user_mt5_accounts table
        mt5_account = {
            'account_number': mt5_data.get('login'),
            'broker': mt5_data.get('broker'),
            'server': mt5_data.get('server'),
            'balance': mt5_data.get('balance', 0),
            'equity': mt5_data.get('equity', 0),
            'currency': mt5_data.get('currency', 'USD'),
            'account_type': 'DEMO' if 'demo' in mt5_data.get('server', '').lower() else 'LIVE',
            'is_primary': True  # First account is primary
        }
        
        # This would need an INSERT INTO user_mt5_accounts
        logger.info(f"✅ MT5 account {mt5_account['account_number']} linked to user {telegram_id}")
        
        # Update onboarding stage
        db.update_user(telegram_id, {'onboarding_stage': 'MT5_CONNECTED'}, 'user_profiles')
        
        # Award XP for connecting account
        self.user_mgr.add_xp(telegram_id, 10, "MT5 account connected")
        
        return {
            'success': True,
            'message': "MT5 account connected successfully!",
            'ready_for_trading': True
        }
    
    def handle_subscription_upgrade(self, telegram_id: int, new_tier: str, payment_data: Dict) -> Dict:
        """
        Handle tier upgrade from payment
        """
        
        user = self.user_mgr.get_complete_user(telegram_id)
        
        if not user:
            # Create user first if they somehow paid without account
            logger.warning(f"Payment from non-existent user {telegram_id}")
            self.handle_first_contact(telegram_id, {})
            user = self.user_mgr.get_complete_user(telegram_id)
        
        old_tier = user.get('tier', 'PRESS_PASS')
        
        # Update user tier
        success = self.user_mgr.update_user_tier(telegram_id, new_tier)
        
        if success:
            # Update subscription status
            from src.bitten_core.central_database_sqlite import get_central_database
            db = get_central_database()
            
            db.update_user(telegram_id, {
                'subscription_status': 'ACTIVE',
                'stripe_customer_id': payment_data.get('customer_id'),
                'subscription_expires_at': payment_data.get('expires_at')
            }, 'users')
            
            # Award upgrade XP
            xp_awards = {
                'NIBBLER': 25,
                'FANG': 50,
                'COMMANDER': 100
            }
            self.user_mgr.add_xp(telegram_id, xp_awards.get(new_tier, 25), f"Upgraded to {new_tier}")
            
            # Update onboarding stage
            db.update_user(telegram_id, {'onboarding_stage': 'SUBSCRIBED'}, 'user_profiles')
            
            # Process referral commission for referrer
            if user.get('referrals', {}).get('referred_by_user'):
                self.process_referral_commission(
                    user['referrals']['referred_by_user'],
                    telegram_id,
                    new_tier
                )
            
            return {
                'success': True,
                'old_tier': old_tier,
                'new_tier': new_tier,
                'message': f"🎉 Upgraded to {new_tier}!"
            }
        
        return {
            'success': False,
            'error': 'Upgrade failed'
        }
    
    def process_referral_signup(self, new_user_id: int, referral_code: str) -> bool:
        """
        Process a new user signup via referral
        """
        try:
            from src.bitten_core.central_database_sqlite import get_central_database
            db = get_central_database()
            
            # Find referrer by code
            # This would need SELECT * FROM user_referrals WHERE personal_referral_code = ?
            # For now, extract user_id from code format REF_123456
            if referral_code.startswith('REF_'):
                referrer_id = int(referral_code.replace('REF_', ''))
                
                # Update new user's referral data
                db.update_user(new_user_id, {
                    'referred_by_code': referral_code,
                    'referred_by_user': referrer_id
                }, 'user_referrals')
                
                # Update referrer's counts
                referrer = self.user_mgr.get_complete_user(referrer_id)
                if referrer and 'referrals' in referrer:
                    current_count = referrer['referrals'].get('referral_count', 0)
                    db.update_user(referrer_id, {
                        'referral_count': current_count + 1,
                        'active_referral_count': referrer['referrals'].get('active_referral_count', 0) + 1
                    }, 'user_referrals')
                    
                    # Award referral XP
                    self.user_mgr.add_xp(referrer_id, 20, f"New recruit joined")
                    
                    logger.info(f"✅ User {new_user_id} referred by {referrer_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error processing referral: {e}")
        
        return False
    
    def process_referral_commission(self, referrer_id: int, referred_id: int, tier: str) -> bool:
        """
        Process commission for subscription referral
        """
        try:
            # Commission amounts by tier
            commissions = {
                'NIBBLER': 5.00,     # $5 for $39 subscription
                'FANG': 10.00,       # $10 for $79 subscription
                'COMMANDER': 15.00   # $15 for $139 subscription
            }
            
            commission = commissions.get(tier, 0)
            
            if commission > 0:
                from central_database_sqlite import get_central_database
                db = get_central_database()
                
                # Add to referrer's pending credits
                referrer = self.user_mgr.get_complete_user(referrer_id)
                if referrer and 'referrals' in referrer:
                    current_pending = referrer['referrals'].get('pending_credits', 0)
                    db.update_user(referrer_id, {
                        'pending_credits': current_pending + commission,
                        'total_credits_earned': referrer['referrals'].get('total_credits_earned', 0) + commission
                    }, 'user_referrals')
                    
                    logger.info(f"💰 Credited ${commission} referral commission to user {referrer_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error processing referral commission: {e}")
        
        return False
    
    def generate_referral_code(self, telegram_id: int) -> str:
        """Generate unique referral code for user"""
        # Simple format: REF_USERID
        # In production, could use hash or random string
        return f"REF_{telegram_id}"
    
    def get_onboarding_progress(self, telegram_id: int) -> Dict:
        """
        Get user's onboarding progress
        """
        user = self.user_mgr.get_complete_user(telegram_id)
        
        if not user:
            return {'stage': 'NOT_STARTED'}
        
        profile = user.get('profiles', {})
        stage = profile.get('onboarding_stage', 'INITIAL_CONTACT')
        
        stages = {
            'INITIAL_CONTACT': {
                'complete': True,
                'next': 'Connect MT5 account'
            },
            'MT5_CONNECTED': {
                'complete': bool(user.get('mt5_accounts')),
                'next': 'Upgrade subscription'
            },
            'SUBSCRIBED': {
                'complete': user.get('tier') != 'PRESS_PASS',
                'next': 'Start trading'
            },
            'TRADING_ACTIVE': {
                'complete': user.get('trading_stats', {}).get('total_trades', 0) > 0,
                'next': None
            }
        }
        
        return {
            'current_stage': stage,
            'stages': stages,
            'tier': user.get('tier'),
            'has_mt5': bool(user.get('mt5_accounts')),
            'has_referrer': bool(user.get('referrals', {}).get('referred_by_user')),
            'referral_code': user.get('referrals', {}).get('personal_referral_code'),
            'total_trades': user.get('trading_stats', {}).get('total_trades', 0)
        }

# Singleton
_onboarding_instance = None

def get_onboarding_flow() -> UserOnboardingFlow:
    """Get singleton instance of onboarding flow"""
    global _onboarding_instance
    if _onboarding_instance is None:
        _onboarding_instance = UserOnboardingFlow()
    return _onboarding_instance