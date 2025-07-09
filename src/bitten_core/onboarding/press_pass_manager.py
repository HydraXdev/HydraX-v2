"""
BITTEN Press Pass Manager

Handles Press Pass activation, MetaQuotes demo account provisioning,
and nightly XP reset functionality.
"""

import logging
import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, Any, Optional
import random
import string

logger = logging.getLogger(__name__)

class PressPassManager:
    """Manages Press Pass functionality including demo account provisioning"""
    
    def __init__(self):
        self.demo_account_prefix = "BITTEN_DEMO_"
        self.default_demo_balance = 50000  # $50,000 demo balance
        
    async def provision_demo_account(self, user_id: str, callsign: str) -> Dict[str, Any]:
        """
        Provision a MetaQuotes demo account for Press Pass users
        
        Args:
            user_id: User identifier
            callsign: User's chosen callsign
            
        Returns:
            Demo account details
        """
        try:
            # Generate demo account credentials
            account_number = self._generate_demo_account_number()
            demo_password = self._generate_secure_password()
            
            # In production, this would interface with MetaQuotes API
            # For now, we simulate the account creation
            demo_account = {
                'account_number': account_number,
                'password': demo_password,
                'balance': self.default_demo_balance,
                'currency': 'USD',
                'leverage': '1:100',
                'server': 'BITTEN-Demo',
                'platform': 'MetaQuotes',
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'account_type': 'PRESS_PASS_DEMO',
                'callsign': callsign
            }
            
            logger.info(f"Provisioned demo account {account_number} for Press Pass user {user_id}")
            
            # Store account info (in production, this would be encrypted)
            await self._store_demo_account(user_id, demo_account)
            
            return {
                'success': True,
                'account': demo_account,
                'message': f"Demo account {account_number} provisioned successfully!"
            }
            
        except Exception as e:
            logger.error(f"Error provisioning demo account for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to provision demo account. Please try again."
            }
    
    def _generate_demo_account_number(self) -> str:
        """Generate unique demo account number"""
        timestamp = int(datetime.utcnow().timestamp())
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return f"{self.demo_account_prefix}{timestamp}{random_suffix}"
    
    def _generate_secure_password(self) -> str:
        """Generate secure password for demo account"""
        # Generate a secure password with letters, numbers, and symbols
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choices(chars, k=12))
        return password
    
    async def _store_demo_account(self, user_id: str, account_data: Dict[str, Any]):
        """Store demo account information securely"""
        # In production, this would store encrypted data in database
        # For now, we'll just log it
        logger.info(f"Storing demo account for user {user_id}")
        # TODO: Implement secure storage
    
    async def check_press_pass_expiry(self, user_id: str, expiry_date: datetime) -> Dict[str, Any]:
        """
        Check if Press Pass has expired
        
        Args:
            user_id: User identifier
            expiry_date: Press Pass expiry datetime
            
        Returns:
            Expiry status and remaining time
        """
        now = datetime.utcnow()
        
        if now >= expiry_date:
            return {
                'expired': True,
                'remaining_time': None,
                'message': "Your Press Pass has expired. Please upgrade to continue."
            }
        
        remaining = expiry_date - now
        days = remaining.days
        hours = remaining.seconds // 3600
        
        return {
            'expired': False,
            'remaining_time': {
                'days': days,
                'hours': hours,
                'total_hours': remaining.total_seconds() / 3600
            },
            'message': f"Press Pass active: {days} days, {hours} hours remaining"
        }
    
    async def reset_daily_xp(self, user_id: str) -> Dict[str, Any]:
        """
        Reset user's XP at midnight UTC (Press Pass limitation)
        
        Args:
            user_id: User identifier
            
        Returns:
            Reset status
        """
        try:
            # In production, this would interface with XP system
            logger.info(f"Resetting XP for Press Pass user {user_id}")
            
            # TODO: Implement actual XP reset logic
            return {
                'success': True,
                'reset_time': datetime.utcnow().isoformat(),
                'message': "Daily XP reset completed"
            }
            
        except Exception as e:
            logger.error(f"Error resetting XP for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def schedule_nightly_resets(self):
        """
        Schedule nightly XP resets for all Press Pass users
        This should run as a background task
        """
        while True:
            try:
                # Calculate time until midnight UTC
                now = datetime.utcnow()
                midnight = datetime.combine(now.date() + timedelta(days=1), time.min)
                seconds_until_midnight = (midnight - now).total_seconds()
                
                # Wait until midnight
                await asyncio.sleep(seconds_until_midnight)
                
                # Reset XP for all Press Pass users
                await self._perform_nightly_resets()
                
                # Wait a bit before calculating next midnight
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in nightly reset scheduler: {e}")
                # Wait an hour before retrying
                await asyncio.sleep(3600)
    
    async def _perform_nightly_resets(self):
        """Perform nightly XP resets for all Press Pass users"""
        try:
            # TODO: Get all Press Pass users from database
            # For now, just log
            logger.info("Performing nightly XP resets for Press Pass users")
            
            # In production:
            # 1. Query all users with is_press_pass=True
            # 2. Reset their XP
            # 3. Send notifications about the reset
            
        except Exception as e:
            logger.error(f"Error performing nightly resets: {e}")
    
    def get_press_pass_info(self) -> Dict[str, Any]:
        """Get Press Pass feature information"""
        return {
            'features': {
                'full_access': 'All BITTEN features and tools unlocked',
                'demo_account': f'${self.default_demo_balance:,} MetaQuotes practice account',
                'duration': '7 days from activation',
                'trading_signals': 'All premium signals and strategies included',
                'education': 'Complete access to BITTEN Academy',
                'support': 'Priority support during trial period'
            },
            'limitations': {
                'xp_reset': 'Experience points reset nightly at midnight UTC',
                'time_limit': 'Access expires after 7 days',
                'demo_only': 'Practice funds only, no live trading',
                'upgrade_required': 'Must upgrade to paid tier to continue after trial'
            },
            'upgrade_paths': {
                'starter': {
                    'name': 'BITTEN Starter',
                    'price': '$29/month',
                    'features': 'Keep your progress, basic signals, live trading'
                },
                'professional': {
                    'name': 'BITTEN Professional', 
                    'price': '$99/month',
                    'features': 'Advanced signals, multiple strategies, priority support'
                },
                'elite': {
                    'name': 'BITTEN Elite',
                    'price': '$299/month',
                    'features': 'All features, custom strategies, dedicated support'
                }
            }
        }
    
    async def send_expiry_reminder(self, user_id: str, days_remaining: int) -> Dict[str, Any]:
        """
        Send reminder about Press Pass expiry
        
        Args:
            user_id: User identifier
            days_remaining: Days until expiry
            
        Returns:
            Reminder status
        """
        try:
            if days_remaining == 3:
                message = "⏰ Your Press Pass expires in 3 days! Upgrade now to keep your progress."
            elif days_remaining == 1:
                message = "🚨 Last day of Press Pass! Upgrade today to continue your BITTEN journey."
            elif days_remaining == 0:
                message = "⌛ Your Press Pass expires today! Don't lose your progress - upgrade now!"
            else:
                return {'sent': False, 'reason': 'No reminder needed yet'}
            
            # TODO: Send actual notification via Telegram
            logger.info(f"Sending expiry reminder to user {user_id}: {message}")
            
            return {
                'sent': True,
                'message': message,
                'days_remaining': days_remaining
            }
            
        except Exception as e:
            logger.error(f"Error sending expiry reminder: {e}")
            return {'sent': False, 'error': str(e)}