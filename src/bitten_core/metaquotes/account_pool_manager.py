"""
MetaQuotes Demo Account Pool Manager

Manages a pool of pre-provisioned demo accounts for instant assignment
to users, ensuring fast onboarding and optimal user experience.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

from .demo_account_service import (
    DemoAccountService, 
    DemoAccountConfig,
    MetaQuotesAPIClient,
    CredentialEncryption
)
from ...database.connection import get_async_db

logger = logging.getLogger(__name__)

@dataclass 
class PoolConfig:
    """Configuration for account pool management"""
    min_available_accounts: int = 50  # Minimum accounts to keep ready
    max_pool_size: int = 200  # Maximum total accounts in pool
    target_buffer: int = 75  # Target number of available accounts
    provision_batch_size: int = 10  # Accounts to provision in one batch
    health_check_interval_minutes: int = 30
    cleanup_interval_hours: int = 6
    account_expiry_days: int = 30

class AccountPoolManager:
    """Manages the pool of pre-provisioned demo accounts"""
    
    def __init__(self, config: Optional[PoolConfig] = None):
        self.config = config or PoolConfig()
        self.demo_service = None
        self.is_running = False
        self.tasks = []
        
    async def initialize(self):
        """Initialize the pool manager"""
        self.demo_service = DemoAccountService()
        await self.demo_service.initialize()
        logger.info("AccountPoolManager initialized")
        
    async def start(self):
        """Start pool management background tasks"""
        if self.is_running:
            logger.warning("AccountPoolManager already running")
            return
            
        self.is_running = True
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._pool_maintenance_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        logger.info("AccountPoolManager started with 3 background tasks")
        
    async def stop(self):
        """Stop all background tasks"""
        self.is_running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("AccountPoolManager stopped")
        
    async def _pool_maintenance_loop(self):
        """Maintain optimal pool size"""
        while self.is_running:
            try:
                await self._check_and_replenish_pool()
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Pool maintenance error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
                
    async def _health_check_loop(self):
        """Periodically check health of pooled accounts"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.health_check_interval_minutes * 60)
                await self._perform_health_checks()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                
    async def _cleanup_loop(self):
        """Clean up expired and problematic accounts"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)
                await self._cleanup_pool()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                
    async def _check_and_replenish_pool(self):
        """Check pool status and provision new accounts if needed"""
        async with get_async_db() as conn:
            # Get current pool statistics
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'available') as available_count,
                    COUNT(*) FILTER (WHERE status = 'assigned') as assigned_count,
                    COUNT(*) FILTER (WHERE status = 'expired') as expired_count,
                    COUNT(*) as total_count
                FROM demo_account_pool
                WHERE health_status != 'expired'
                """
            )
            
            available = stats['available_count'] or 0
            total = stats['total_count'] or 0
            
            logger.info(f"Pool status: {available} available, {total} total")
            
            # Check if we need to provision more accounts
            if available < self.config.min_available_accounts and total < self.config.max_pool_size:
                # Calculate how many to provision
                needed = min(
                    self.config.target_buffer - available,
                    self.config.max_pool_size - total,
                    self.config.provision_batch_size
                )
                
                if needed > 0:
                    logger.info(f"Provisioning {needed} new demo accounts")
                    await self._provision_batch(needed)
                    
    async def _provision_batch(self, count: int):
        """Provision a batch of demo accounts"""
        provisioned = 0
        failed = 0
        
        # Create provisioning tasks
        tasks = []
        for _ in range(count):
            task = asyncio.create_task(self._provision_single_account())
            tasks.append(task)
            
        # Wait for all provisioning to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to provision account: {result}")
                failed += 1
            elif result and result.get('success'):
                provisioned += 1
            else:
                failed += 1
                
        logger.info(f"Batch provisioning complete: {provisioned} succeeded, {failed} failed")
        
    async def _provision_single_account(self) -> Dict[str, Any]:
        """Provision a single demo account for the pool"""
        try:
            config = DemoAccountConfig(
                initial_balance=50000.0,
                currency="USD",
                leverage="1:100",
                expiry_days=self.config.account_expiry_days,
                server="BITTEN-Demo"
            )
            
            # Use the demo service's API client
            async with self.demo_service.api_client:
                api_response = await self.demo_service.api_client.create_demo_account(config)
                
                if not api_response['success']:
                    return {'success': False, 'error': 'API failed'}
                    
                account_data = api_response['data']
                
                # Encrypt password
                encrypted_password = self.demo_service.encryption.encrypt_password(
                    account_data['password'],
                    'bitten-demo-key-2025-01'
                )
                
                # Store in pool
                async with get_async_db() as conn:
                    pool_id = await conn.fetchval(
                        """
                        INSERT INTO demo_account_pool (
                            account_number, account_password, account_server,
                            initial_balance, current_balance, leverage, currency,
                            mt5_login, mt5_company, broker_name,
                            expires_at, status, health_status,
                            provisioning_metadata
                        ) VALUES ($1, $2, $3, $4, $4, $5, $6, $7, $8, $9, $10, 'available', 'healthy', $11::jsonb)
                        RETURNING pool_id
                        """,
                        account_data['account_number'],
                        encrypted_password,
                        account_data['server'],
                        account_data['balance'],
                        account_data['leverage'],
                        account_data['currency'],
                        account_data.get('mt5_login'),
                        account_data.get('company', 'BITTEN Financial Services'),
                        account_data.get('broker_name', 'BITTEN Trading'),
                        datetime.fromisoformat(account_data['expires_at']),
                        json.dumps({
                            'provisioned_at': datetime.utcnow().isoformat(),
                            'platform': account_data.get('platform', 'MetaTrader5')
                        })
                    )
                    
                logger.info(f"Added account {account_data['account_number']} to pool (ID: {pool_id})")
                return {'success': True, 'pool_id': pool_id}
                
        except Exception as e:
            logger.error(f"Error provisioning account: {e}")
            return {'success': False, 'error': str(e)}
            
    async def _perform_health_checks(self):
        """Check health of all available accounts"""
        logger.info("Starting health checks for pooled accounts")
        
        async with get_async_db() as conn:
            # Get accounts needing health check
            accounts = await conn.fetch(
                """
                SELECT pool_id, account_number
                FROM demo_account_pool
                WHERE status = 'available'
                  AND (last_health_check IS NULL 
                       OR last_health_check < CURRENT_TIMESTAMP - INTERVAL '1 hour')
                LIMIT 50
                """
            )
            
            logger.info(f"Checking health of {len(accounts)} accounts")
            
            # Check each account
            tasks = []
            for account in accounts:
                task = asyncio.create_task(
                    self._check_single_account_health(
                        account['pool_id'],
                        account['account_number']
                    )
                )
                tasks.append(task)
                
            # Wait for all checks
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def _check_single_account_health(self, pool_id: int, account_number: str):
        """Check health of a single account"""
        try:
            result = await self.demo_service.check_account_health(account_number)
            
            if not result['success']:
                # Mark as degraded
                async with get_async_db() as conn:
                    await conn.execute(
                        """
                        UPDATE demo_account_pool
                        SET health_status = 'degraded',
                            error_log = error_log || $1::jsonb
                        WHERE pool_id = $2
                        """,
                        json.dumps([{
                            'timestamp': datetime.utcnow().isoformat(),
                            'error': result.get('error', 'Health check failed')
                        }]),
                        pool_id
                    )
                    
        except Exception as e:
            logger.error(f"Health check failed for account {account_number}: {e}")
            
    async def _cleanup_pool(self):
        """Clean up expired and problematic accounts"""
        logger.info("Starting pool cleanup")
        
        async with get_async_db() as conn:
            # Clean up expired accounts
            expired_count = await self.demo_service.cleanup_expired_accounts()
            
            # Remove accounts with repeated health failures
            removed = await conn.execute(
                """
                UPDATE demo_account_pool
                SET status = 'error',
                    health_status = 'offline'
                WHERE status = 'available'
                  AND health_status = 'degraded'
                  AND last_health_check < CURRENT_TIMESTAMP - INTERVAL '24 hours'
                """
            )
            
            logger.info(f"Cleanup complete: {expired_count} expired, {removed} unhealthy accounts removed")
            
    async def get_pool_statistics(self) -> Dict[str, Any]:
        """Get current pool statistics"""
        async with get_async_db() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'available' AND health_status = 'healthy') as healthy_available,
                    COUNT(*) FILTER (WHERE status = 'available') as total_available,
                    COUNT(*) FILTER (WHERE status = 'assigned') as assigned,
                    COUNT(*) FILTER (WHERE status = 'expired') as expired,
                    COUNT(*) FILTER (WHERE status = 'error') as error,
                    COUNT(*) as total,
                    MIN(provisioned_at) FILTER (WHERE status = 'available') as oldest_available,
                    MAX(provisioned_at) FILTER (WHERE status = 'available') as newest_available
                FROM demo_account_pool
                """
            )
            
            # Get provisioning rate
            recent_provisions = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM demo_account_pool
                WHERE provisioned_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                """
            )
            
            return {
                'healthy_available': stats['healthy_available'] or 0,
                'total_available': stats['total_available'] or 0,
                'assigned': stats['assigned'] or 0,
                'expired': stats['expired'] or 0,
                'error': stats['error'] or 0,
                'total': stats['total'] or 0,
                'oldest_available': stats['oldest_available'].isoformat() if stats['oldest_available'] else None,
                'newest_available': stats['newest_available'].isoformat() if stats['newest_available'] else None,
                'provisions_last_hour': recent_provisions or 0,
                'pool_health': 'healthy' if (stats['healthy_available'] or 0) >= self.config.min_available_accounts else 'low'
            }
            
    async def force_replenish(self, count: int) -> Dict[str, Any]:
        """Force replenishment of the pool"""
        logger.info(f"Force replenishing pool with {count} accounts")
        
        # Check current pool size
        async with get_async_db() as conn:
            current_total = await conn.fetchval(
                "SELECT COUNT(*) FROM demo_account_pool WHERE status != 'expired'"
            )
            
            if current_total >= self.config.max_pool_size:
                return {
                    'success': False,
                    'error': 'pool_at_capacity',
                    'message': f'Pool is at maximum capacity ({self.config.max_pool_size})'
                }
                
            # Provision requested accounts
            to_provision = min(count, self.config.max_pool_size - current_total)
            await self._provision_batch(to_provision)
            
            return {
                'success': True,
                'provisioned': to_provision,
                'message': f'Provisioned {to_provision} new accounts'
            }

# Singleton instance
_pool_manager = None

async def get_pool_manager() -> AccountPoolManager:
    """Get or create the pool manager singleton"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = AccountPoolManager()
        await _pool_manager.initialize()
    return _pool_manager