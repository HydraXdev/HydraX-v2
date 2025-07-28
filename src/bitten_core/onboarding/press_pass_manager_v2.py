"""
BITTEN Press Pass Manager V2

Enhanced Press Pass activation with real MetaQuotes demo account provisioning,
secure credential delivery, and integrated lifecycle management.
"""

import logging
import asyncio
from datetime import datetime, timedelta, time, date
from typing import Dict, Any, Optional
from ..database.connection import get_async_db
from ..metaquotes.demo_account_service import get_demo_account_service
from ..metaquotes.credential_delivery import SecureCredentialDelivery, DeliveryMethod

logger = logging.getLogger(__name__)

class PressPassManagerV2:
    """Enhanced Press Pass functionality with MetaQuotes integration"""
    
    def __init__(self):
        self.demo_service = None
        self.credential_delivery = SecureCredentialDelivery()
        self.weekly_limit = 200
        self.enlistment_bonus_xp = 50
        self._initialized = False
        
    async def initialize(self):
        """Initialize the Press Pass manager"""
        if self._initialized:
            return
            
        try:
            self.demo_service = await get_demo_account_service()
            self._initialized = True
            logger.info("PressPassManagerV2 initialized with MetaQuotes integration")
        except Exception as e:
            logger.error(f"Failed to initialize PressPassManagerV2: {e}")
            raise
            
    async def activate_press_pass(self, user_id: str, real_name: str,
                                delivery_method: DeliveryMethod = DeliveryMethod.TELEGRAM,
                                contact_info: Optional[str] = None) -> Dict[str, Any]:
        """
        Activate Press Pass with real MetaQuotes demo account provisioning
        
        Args:
            user_id: User identifier
            real_name: User's real name
            delivery_method: How to deliver credentials
            contact_info: Telegram ID or email address for delivery
            
        Returns:
            Activation result with account details
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Check weekly limit
            limit_check = await self.check_weekly_limit()
            if limit_check['limit_reached']:
                return {
                    'success': False,
                    'error': 'weekly_limit_reached',
                    'message': f"Weekly limit of {self.weekly_limit} Press Pass accounts reached. Please try again next week.",
                    'limit_info': limit_check
                }
                
            # Check if user already has Press Pass
            existing = await self._check_existing_press_pass(user_id)
            if existing:
                return {
                    'success': False,
                    'error': 'already_has_press_pass',
                    'message': 'You already have an active Press Pass',
                    'existing': existing
                }
                
            # Provision MetaQuotes demo account
            logger.info(f"Provisioning MetaQuotes demo account for user {user_id}")
            account_result = await self.demo_service.provision_account_for_user(
                user_id=user_id,
                tier='press_pass'
            )
            
            if not account_result['success']:
                logger.error(f"Failed to provision account: {account_result}")
                return {
                    'success': False,
                    'error': 'provisioning_failed',
                    'message': 'Failed to create demo account. Please try again.',
                    'details': account_result.get('error')
                }
                
            account_data = account_result['account']
            
            # Prepare credentials for delivery
            credential_package = await self.credential_delivery.prepare_credentials(
                user_id=user_id,
                account_data=account_data,
                delivery_method=delivery_method
            )
            
            # Deliver credentials based on method
            delivery_result = await self._deliver_credentials(
                credential_package,
                delivery_method,
                contact_info or user_id
            )
            
            if not delivery_result['success']:
                logger.error(f"Credential delivery failed: {delivery_result}")
                # Account is provisioned but delivery failed - still continue
                
            # Register Press Pass activation
            await self._register_press_pass_activation(
                user_id=user_id,
                account_number=account_data['account_number'],
                real_name=real_name
            )
            
            # Register for XP reset system
            await self._register_for_xp_reset(user_id)
            
            # Increment weekly counter
            await self._increment_weekly_count()
            
            # Log activation
            logger.info(f"Press Pass activated for user {user_id} with account {account_data['account_number']}")
            
            return {
                'success': True,
                'account': {
                    'account_number': account_data['account_number'],
                    'server': account_data['server'],
                    'balance': account_data['balance'],
                    'leverage': account_data['leverage'],
                    'currency': account_data['currency'],
                    'expires_at': account_data['expires_at'],
                    'platform': 'MetaTrader 5'
                },
                'delivery': delivery_result,
                'message': f"Press Pass activated! Demo account {account_data['account_number']} created successfully."
            }
            
        except Exception as e:
            logger.error(f"Error activating Press Pass for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to activate Press Pass. Please try again.'
            }
            
    async def get_account_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve demo account credentials for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Account credentials if found
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            credentials = await self.demo_service.get_user_credentials(user_id)
            if credentials:
                # Check if account is expired
                expires_at = datetime.fromisoformat(credentials['expires_at'])
                if expires_at < datetime.utcnow():
                    return None
                    
                return credentials
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving credentials for user {user_id}: {e}")
            return None
            
    async def check_account_health(self, user_id: str) -> Dict[str, Any]:
        """Check health status of user's demo account"""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Get user's account number
            async with get_async_db() as conn:
                account_number = await conn.fetchval(
                    """
                    SELECT account_number 
                    FROM user_demo_accounts
                    WHERE user_id = $1 AND status = 'active'
                    """,
                    int(user_id) if user_id.isdigit() else 0
                )
                
            if not account_number:
                return {
                    'success': False,
                    'error': 'no_active_account',
                    'message': 'No active demo account found'
                }
                
            # Check account health
            health_result = await self.demo_service.check_account_health(account_number)
            
            return health_result
            
        except Exception as e:
            logger.error(f"Error checking account health for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def resend_credentials(self, user_id: str, 
                               delivery_method: DeliveryMethod,
                               contact_info: str) -> Dict[str, Any]:
        """Resend account credentials to user"""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Get current credentials
            credentials = await self.get_account_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'error': 'no_active_account',
                    'message': 'No active account found'
                }
                
            # Prepare new credential package
            credential_package = await self.credential_delivery.prepare_credentials(
                user_id=user_id,
                account_data=credentials,
                delivery_method=delivery_method
            )
            
            # Deliver credentials
            delivery_result = await self._deliver_credentials(
                credential_package,
                delivery_method,
                contact_info
            )
            
            return delivery_result
            
        except Exception as e:
            logger.error(f"Error resending credentials for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def _deliver_credentials(self, credential_package, 
                                 delivery_method: DeliveryMethod,
                                 contact_info: str) -> Dict[str, Any]:
        """Deliver credentials using specified method"""
        if delivery_method == DeliveryMethod.TELEGRAM:
            return await self.credential_delivery.deliver_via_telegram(
                credential_package, contact_info
            )
        elif delivery_method == DeliveryMethod.EMAIL:
            return await self.credential_delivery.deliver_via_email(
                credential_package, contact_info
            )
        elif delivery_method == DeliveryMethod.QR_CODE:
            return await self.credential_delivery.generate_qr_code(
                credential_package
            )
        elif delivery_method == DeliveryMethod.API:
            return await self.credential_delivery.deliver_via_api(
                credential_package
            )
        else:
            # Default to secure link
            secure_link = await self.credential_delivery._generate_secure_link(
                credential_package
            )
            return {
                'success': True,
                'method': 'secure_link',
                'link': secure_link,
                'expires_at': credential_package.expires_at.isoformat()
            }
            
    async def _check_existing_press_pass(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Check if user already has an active Press Pass"""
        async with get_async_db() as conn:
            row = await conn.fetchrow(
                """
                SELECT uda.account_number, uda.expires_at, uda.activated_at
                FROM user_demo_accounts uda
                WHERE uda.user_id = $1 
                  AND uda.tier = 'press_pass'
                  AND uda.status = 'active'
                """,
                int(user_id) if user_id.isdigit() else 0
            )
            
            if row:
                return {
                    'account_number': row['account_number'],
                    'expires_at': row['expires_at'].isoformat(),
                    'activated_at': row['activated_at'].isoformat()
                }
            return None
            
    async def _register_press_pass_activation(self, user_id: str, 
                                            account_number: str,
                                            real_name: str):
        """Register Press Pass activation in database"""
        async with get_async_db() as conn:
            # Store in trade_logs_all as initial entry
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
                f"Press Pass Activated - Account: {account_number}"
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
            
    async def check_weekly_limit(self) -> Dict[str, Any]:
        """Check if weekly Press Pass limit has been reached"""
        try:
            today = date.today()
            current_week_start = today - timedelta(days=today.weekday())
            
            async with get_async_db() as conn:
                result = await conn.fetchval(
                    "SELECT check_weekly_press_pass_limit()"
                )
                limit_reached = result if result is not None else False
                
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
            return {
                'limit_reached': True,
                'error': str(e),
                'current_count': self.weekly_limit,
                'limit': self.weekly_limit,
                'remaining': 0
            }
            
    async def _register_for_xp_reset(self, user_id: str):
        """Register user with XP reset system"""
        try:
            async with get_async_db() as conn:
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
                reset_manager = PressPassResetManager()
                await reset_manager.add_press_pass_user(user_id)
            except ImportError:
                pass
                
        except Exception as e:
            logger.error(f"Error registering user {user_id} for XP reset: {e}")
            
    async def _increment_weekly_count(self):
        """Increment weekly Press Pass counter"""
        try:
            async with get_async_db() as conn:
                await conn.execute(
                    "SELECT increment_weekly_press_pass_count()"
                )
                
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
            
    async def get_press_pass_statistics(self) -> Dict[str, Any]:
        """Get comprehensive Press Pass statistics"""
        try:
            async with get_async_db() as conn:
                # Get current week stats
                today = date.today()
                current_week_start = today - timedelta(days=today.weekday())
                
                week_stats = await conn.fetchrow(
                    """
                    SELECT accounts_created, limit_reached
                    FROM press_pass_weekly_limits
                    WHERE week_start_date = $1
                    """,
                    current_week_start
                )
                
                # Get overall stats
                overall_stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total_press_passes,
                        COUNT(*) FILTER (WHERE status = 'active') as active_accounts,
                        COUNT(*) FILTER (WHERE status = 'expired') as expired_accounts,
                        AVG(EXTRACT(DAY FROM (deactivated_at - activated_at))) as avg_duration_days
                    FROM user_demo_accounts
                    WHERE tier = 'press_pass'
                    """
                )
                
                # Get conversion stats
                conversion_stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) FILTER (WHERE enlisted_after = true) as converted,
                        COUNT(*) as total,
                        AVG(time_to_enlist_days) as avg_time_to_convert
                    FROM conversion_signal_tracker
                    WHERE press_pass_start_date IS NOT NULL
                    """
                )
                
                return {
                    'weekly': {
                        'current_count': week_stats['accounts_created'] if week_stats else 0,
                        'limit': self.weekly_limit,
                        'remaining': self.weekly_limit - (week_stats['accounts_created'] if week_stats else 0),
                        'limit_reached': week_stats['limit_reached'] if week_stats else False
                    },
                    'overall': {
                        'total_issued': overall_stats['total_press_passes'] or 0,
                        'currently_active': overall_stats['active_accounts'] or 0,
                        'expired': overall_stats['expired_accounts'] or 0,
                        'avg_duration_days': float(overall_stats['avg_duration_days'] or 0)
                    },
                    'conversion': {
                        'total_conversions': conversion_stats['converted'] or 0,
                        'conversion_rate': (conversion_stats['converted'] / conversion_stats['total'] * 100) if conversion_stats['total'] > 0 else 0,
                        'avg_days_to_convert': float(conversion_stats['avg_time_to_convert'] or 0)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting Press Pass statistics: {e}")
            return {
                'error': str(e),
                'weekly': {},
                'overall': {},
                'conversion': {}
            }

# Singleton instance
_press_pass_manager_v2 = None

async def get_press_pass_manager() -> PressPassManagerV2:
    """Get or create the Press Pass manager singleton"""
    global _press_pass_manager_v2
    if _press_pass_manager_v2 is None:
        _press_pass_manager_v2 = PressPassManagerV2()
        await _press_pass_manager_v2.initialize()
    return _press_pass_manager_v2