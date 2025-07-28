"""
BITTEN Press Pass Manager

Handles Press Pass activation, MetaQuotes demo account provisioning,
and nightly XP reset functionality.
"""

import logging
import asyncio
from datetime import datetime, timedelta, time, date
from typing import Dict, Any, Optional
import random
import string
from ..database.connection import get_async_db, get_db_connection, DatabaseSession
import asyncpg

logger = logging.getLogger(__name__)

class PressPassManager:
    """Manages Press Pass functionality including demo account provisioning"""
    
    def __init__(self):
        self.demo_account_prefix = "BITTEN_DEMO_"
        self.default_demo_balance = 50000  # $50,000 demo balance
        self.weekly_limit = 200  # Maximum 200 Press Pass accounts per week
        self.enlistment_bonus_xp = 50  # Bonus XP when upgrading to paid
        
    async def check_weekly_limit(self) -> Dict[str, Any]:
        """Check if weekly Press Pass limit has been reached"""
        try:
            # Get Monday of current week
            today = date.today()
            current_week_start = today - timedelta(days=today.weekday())
            
            async with get_async_db() as conn:
                # Check if weekly limit has been reached using the database function
                result = await conn.fetchval(
                    "SELECT check_weekly_press_pass_limit()"
                )
                limit_reached = result if result is not None else False
                
                # Get current count for this week
                row = await conn.fetchrow(
                    """
                    SELECT accounts_created, limit_reached 
                    FROM press_pass_weekly_limits 
                    WHERE week_start_date = $1
                    """,
                    current_week_start
                )
                
                if row:
                    current_week_count = row['accounts_created']
                    limit_reached = row['limit_reached']
                else:
                    # Create week record if it doesn't exist
                    await conn.execute(
                        """
                        INSERT INTO press_pass_weekly_limits (week_start_date, accounts_created)
                        VALUES ($1, 0)
                        ON CONFLICT (week_start_date) DO NOTHING
                        """,
                        current_week_start
                    )
                    current_week_count = 0
                    limit_reached = False
            
            return {
                'limit_reached': limit_reached,
                'current_count': current_week_count,
                'limit': self.weekly_limit,
                'remaining': max(0, self.weekly_limit - current_week_count),
                'week_start': current_week_start.isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking weekly limit: {e}")
            # Return safe default on error (block new accounts)
            return {
                'limit_reached': True, 
                'error': str(e),
                'current_count': self.weekly_limit,
                'limit': self.weekly_limit,
                'remaining': 0,
                'week_start': current_week_start.isoformat() if 'current_week_start' in locals() else None
            }
    
    async def provision_demo_account(self, user_id: str, real_name: str) -> Dict[str, Any]:
        """
        Provision a MetaQuotes demo account for Press Pass users
        
        Args:
            user_id: User identifier  
            real_name: User's real name (no callsign for Press Pass)
            
        Returns:
            Demo account details
        """
        try:
            # Check weekly limit first
            limit_check = await self.check_weekly_limit()
            if limit_check['limit_reached']:
                return {
                    'success': False,
                    'error': 'weekly_limit_reached',
                    'message': f"Weekly limit of {self.weekly_limit} Press Pass accounts reached. Please try again next week."
                }
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
                'real_name': real_name,
                'tier': 'PRESS_PASS',  # Flag for XP reset system
                'xp_reset_nightly': True
            }
            
            logger.info(f"Provisioned demo account {account_number} for Press Pass user {user_id}")
            
            # Store account info (in production, this would be encrypted)
            await self._store_demo_account(user_id, demo_account)
            
            # Add user to XP reset system
            await self._register_for_xp_reset(user_id)
            
            # Increment weekly counter
            await self._increment_weekly_count()
            
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
        try:
            async with get_async_db() as conn:
                # Store demo account in trade_logs_all table as initial entry
                await conn.execute(
                    """
                    INSERT INTO trade_logs_all (
                        user_id, tier, symbol, entry_time, direction, 
                        lot_size, entry_price, strategy_used, 
                        trade_tag, status, xp_earned
                    ) VALUES (
                        $1, 'press_pass', 'SYSTEM', $2, 'info',
                        0, 0, 'press_pass_activation',
                        $3, 'closed', 0
                    )
                    """,
                    int(user_id) if user_id.isdigit() else 0,
                    datetime.utcnow(),
                    f"Demo Account: {account_data['account_number']}"
                )
                
                # Initialize press pass shadow stats
                await conn.execute(
                    """
                    INSERT INTO press_pass_shadow_stats (
                        user_id, xp_earned_today, trades_executed_today,
                        total_resets, last_reset_at
                    ) VALUES ($1, 0, 0, 0, NULL)
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    int(user_id) if user_id.isdigit() else 0
                )
                
                # Initialize conversion tracking
                await conn.execute(
                    """
                    INSERT INTO conversion_signal_tracker (
                        user_id, press_pass_start_date, press_pass_duration_days,
                        enlisted_after, conversion_source
                    ) VALUES ($1, $2, 7, FALSE, 'telegram')
                    ON CONFLICT (user_id) DO UPDATE SET
                        press_pass_start_date = EXCLUDED.press_pass_start_date
                    """,
                    int(user_id) if user_id.isdigit() else 0,
                    datetime.utcnow()
                )
                
                logger.info(f"Stored demo account for user {user_id} in database")
                
        except Exception as e:
            logger.error(f"Error storing demo account for user {user_id}: {e}")
            # Don't raise - account creation was successful even if storage fails
    
    async def _register_for_xp_reset(self, user_id: str):
        """Register user with XP reset system"""
        try:
            async with get_async_db() as conn:
                # Ensure user exists in shadow stats table
                await conn.execute(
                    """
                    INSERT INTO press_pass_shadow_stats (
                        user_id, xp_earned_today, trades_executed_today,
                        total_resets, last_reset_at
                    ) VALUES ($1, 0, 0, 0, NULL)
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    int(user_id) if user_id.isdigit() else 0
                )
                
                logger.info(f"Registered user {user_id} for nightly XP resets")
                
            # Import here to avoid circular dependencies
            try:
                from ..press_pass_reset import PressPassResetManager
                # Notify reset manager if available
                reset_manager = PressPassResetManager()
                await reset_manager.add_press_pass_user(user_id)
            except ImportError:
                # Reset manager not available, but user is registered in DB
                pass
                
        except Exception as e:
            logger.error(f"Error registering user {user_id} for XP reset: {e}")
    
    async def _increment_weekly_count(self):
        """Increment weekly Press Pass counter"""
        try:
            async with get_async_db() as conn:
                # Call the database function to increment the counter
                await conn.execute(
                    "SELECT increment_weekly_press_pass_count()"
                )
                
                # Get updated count for logging
                today = date.today()
                current_week_start = today - timedelta(days=today.weekday())
                
                current_count = await conn.fetchval(
                    """
                    SELECT accounts_created 
                    FROM press_pass_weekly_limits 
                    WHERE week_start_date = $1
                    """,
                    current_week_start
                )
                
                logger.info(f"Incremented weekly Press Pass counter. Current count: {current_count}/{self.weekly_limit}")
                
        except Exception as e:
            logger.error(f"Error incrementing weekly counter: {e}")
            # Don't raise - we still want to continue with account creation even if counter fails
    
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
            async with get_async_db() as conn:
                # Get current XP before reset
                current_xp = await conn.fetchval(
                    """
                    SELECT xp_earned_today 
                    FROM press_pass_shadow_stats 
                    WHERE user_id = $1
                    """,
                    int(user_id) if user_id.isdigit() else 0
                )
                
                if current_xp is None:
                    return {
                        'success': False,
                        'error': 'User not found in Press Pass system'
                    }
                
                # Reset XP using the database function
                await conn.execute(
                    """
                    UPDATE press_pass_shadow_stats
                    SET xp_earned_today = 0,
                        trades_executed_today = 0,
                        total_resets = total_resets + 1,
                        last_reset_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                    """,
                    int(user_id) if user_id.isdigit() else 0
                )
                
                logger.info(f"Reset XP for Press Pass user {user_id}. Previous XP: {current_xp}")
                
                return {
                    'success': True,
                    'reset_time': datetime.utcnow().isoformat(),
                    'previous_xp': current_xp,
                    'message': f"Daily XP reset completed. Lost {current_xp} XP."
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
            async with get_async_db() as conn:
                # Call the database function to reset all Press Pass XP
                await conn.execute("SELECT reset_daily_press_pass_xp()")
                
                # Get count of affected users for logging
                reset_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) 
                    FROM press_pass_shadow_stats 
                    WHERE last_reset_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'
                    """
                )
                
                logger.info(f"Performed nightly XP resets for {reset_count} Press Pass users")
                
                # Get list of users who had XP reset for notifications
                users_reset = await conn.fetch(
                    """
                    SELECT user_id, xp_earned_today
                    FROM press_pass_shadow_stats
                    WHERE last_reset_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'
                        AND xp_earned_today > 0
                    """
                )
                
                # Send notifications (implement based on your notification system)
                for user in users_reset:
                    try:
                        # TODO: Send notification to user about XP reset
                        logger.debug(f"User {user['user_id']} had {user['xp_earned_today']} XP reset")
                    except Exception as e:
                        logger.error(f"Failed to notify user {user['user_id']}: {e}")
                        
        except Exception as e:
            logger.error(f"Error performing nightly resets: {e}")
    
    def get_press_pass_info(self) -> Dict[str, Any]:
        """Get Press Pass feature information"""
        return {
            'features': {
                'full_access': 'All BITTEN features and tools unlocked',
                'demo_account': f'${self.default_demo_balance:} MetaQuotes practice account',
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
                    'name': 'BITTEN NIBBLER',
                    'price': '$39/month',
                    'features': 'Keep your progress, basic signals, live trading'
                },
                'professional': {
                    'name': 'BITTEN FANG', 
                    'price': '$89/month',
                    'features': 'Advanced signals, multiple strategies, priority support'
                },
                'elite': {
                    'name': 'BITTEN COMMANDER',
                    'price': '$189/month',
                    'features': 'All features, unlimited trades, elite support'
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
    
    async def upgrade_to_paid_tier(self, user_id: str, new_tier: str) -> Dict[str, Any]:
        """
        Upgrade Press Pass user to paid tier
        
        Args:
            user_id: User identifier
            new_tier: Target tier (NIBBLER, FANG, COMMANDER)
            
        Returns:
            Upgrade status and current XP preserved
        """
        try:
            async with get_async_db() as conn:
                # Get current XP (what they have TODAY when they enlist)
                current_xp = await conn.fetchval(
                    """
                    SELECT xp_earned_today 
                    FROM press_pass_shadow_stats 
                    WHERE user_id = $1
                    """,
                    int(user_id) if user_id.isdigit() else 0
                )
                
                if current_xp is None:
                    current_xp = 0
                    
                final_xp = current_xp + self.enlistment_bonus_xp
                
                # Begin transaction for upgrade
                async with conn.transaction():
                    # Update conversion tracker
                    await conn.execute(
                        """
                        UPDATE conversion_signal_tracker
                        SET enlisted_after = TRUE,
                            enlisted_date = CURRENT_TIMESTAMP,
                            enlisted_tier = $2,
                            press_pass_end_date = CURRENT_TIMESTAMP,
                            time_to_enlist_days = EXTRACT(DAY FROM CURRENT_TIMESTAMP - press_pass_start_date)::INTEGER,
                            xp_preserved_at_enlistment = $3,
                            enlistment_bonus_xp = $4,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = $1
                        """,
                        int(user_id) if user_id.isdigit() else 0,
                        new_tier.upper(),
                        current_xp,
                        self.enlistment_bonus_xp
                    )
                    
                    # Remove from Press Pass shadow stats (they're no longer Press Pass)
                    await conn.execute(
                        """
                        DELETE FROM press_pass_shadow_stats
                        WHERE user_id = $1
                        """,
                        int(user_id) if user_id.isdigit() else 0
                    )
                    
                    # Log the upgrade in trade_logs_all
                    await conn.execute(
                        """
                        INSERT INTO trade_logs_all (
                            user_id, tier, symbol, entry_time, direction,
                            lot_size, entry_price, strategy_used,
                            trade_tag, status, xp_earned
                        ) VALUES (
                            $1, $2, 'SYSTEM', $3, 'info',
                            0, 0, 'tier_upgrade',
                            $4, 'closed', $5
                        )
                        """,
                        int(user_id) if user_id.isdigit() else 0,
                        new_tier.lower(),
                        datetime.utcnow(),
                        f"Upgraded from Press Pass to {new_tier}",
                        final_xp
                    )
                
                logger.info(f"Upgraded Press Pass user {user_id} to {new_tier}. XP preserved: {current_xp} + {self.enlistment_bonus_xp} bonus = {final_xp}")
                
                return {
                    'success': True,
                    'previous_tier': 'PRESS_PASS',
                    'new_tier': new_tier,
                    'current_xp_preserved': current_xp,
                    'enlistment_bonus': self.enlistment_bonus_xp,
                    'final_xp': final_xp,
                    'message': f"Enlisted as {new_tier}! Current XP ({current_xp}) preserved + {self.enlistment_bonus_xp} enlistment bonus!"
                }
                
        except Exception as e:
            logger.error(f"Error upgrading user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Upgrade failed. Please try again."
            }