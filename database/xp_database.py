"""
XP Database Infrastructure for BITTEN
Provides complete database management for XP economy, Press Pass resets,
and transaction tracking with full PostgreSQL integration.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
import asyncpg
from asyncpg.pool import Pool
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection config
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
    'database': os.getenv('DB_NAME', 'bitten_db'),
    'user': os.getenv('DB_USER', 'bitten_app'),
    'password': os.getenv('DB_PASSWORD', 'bitten_pass')}

@dataclass
class XPBalance:
    """Data class for user XP balance"""
    user_id: int
    current_balance: int
    lifetime_earned: int
    lifetime_spent: int
    prestige_level: int = 0
    last_updated: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return data

@dataclass
class XPTransaction:
    """Data class for XP transactions"""
    transaction_id: Optional[int] = None
    user_id: int = None
    transaction_type: str = None  # 'earn', 'spend', 'reset', 'bonus'
    amount: int = 0  # Positive for earning, negative for spending
    balance_before: int = 0
    balance_after: int = 0
    description: str = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class PressPassReset:
    """Data class for Press Pass reset records"""
    reset_id: Optional[int] = None
    user_id: int = None
    xp_wiped: int = 0
    reset_at: datetime = None
    notification_sent: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.reset_at:
            data['reset_at'] = self.reset_at.isoformat()
        return data

class XPDatabase:
    """
    PostgreSQL database manager for XP economy.
    Provides async database operations for XP tracking, transactions, and Press Pass resets.
    """
    
    def __init__(self):
        """Initialize the database manager"""
        self._pool: Optional[Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self._pool = await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)
            logger.info("XP database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            logger.info("XP database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Async context manager for database connections.
        
        Yields:
            asyncpg.Connection: Database connection
        """
        async with self._pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def transaction(self):
        """
        Async context manager for database transactions.
        
        Yields:
            asyncpg.Connection: Database connection with transaction
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def initialize_tables(self):
        """
        Initialize the XP database tables if they don't exist.
        """
        async with self.get_connection() as conn:
            # Create XP balances table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS xp_balances (
                    user_id BIGINT PRIMARY KEY,
                    current_balance INTEGER NOT NULL DEFAULT 0,
                    lifetime_earned INTEGER NOT NULL DEFAULT 0,
                    lifetime_spent INTEGER NOT NULL DEFAULT 0,
                    prestige_level INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create XP transactions table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS xp_transactions (
                    transaction_id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    transaction_type VARCHAR(50) NOT NULL,
                    amount INTEGER NOT NULL,
                    balance_before INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    description TEXT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    
                    CONSTRAINT fk_user
                        FOREIGN KEY(user_id) 
                        REFERENCES xp_balances(user_id)
                        ON DELETE CASCADE
                )
            ''')
            
            # Create Press Pass reset history table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS press_pass_resets (
                    reset_id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    xp_wiped INTEGER NOT NULL,
                    reset_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    notification_sent BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Create indexes for better query performance
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_xp_transactions_user_id ON xp_transactions(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_xp_transactions_created_at ON xp_transactions(created_at DESC)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_press_pass_resets_user_id ON press_pass_resets(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_press_pass_resets_reset_at ON press_pass_resets(reset_at DESC)')
            
            logger.info("XP database tables initialized successfully")
    
    # XP Balance Operations
    
    async def get_user_balance(self, user_id: int) -> Optional[XPBalance]:
        """
        Get XP balance for a specific user.
        
        Args:
            user_id: User ID to get balance for
            
        Returns:
            XPBalance: User's XP balance or None if not found
        """
        async with self.get_connection() as conn:
            row = await conn.fetchrow('''
                SELECT user_id, current_balance, lifetime_earned, lifetime_spent, 
                       prestige_level, last_updated
                FROM xp_balances
                WHERE user_id = $1
            ''', user_id)
            
            if row:
                return XPBalance(
                    user_id=row['user_id'],
                    current_balance=row['current_balance'],
                    lifetime_earned=row['lifetime_earned'],
                    lifetime_spent=row['lifetime_spent'],
                    prestige_level=row['prestige_level'],
                    last_updated=row['last_updated']
                )
            return None
    
    async def create_user_balance(self, user_id: int, initial_balance: int = 0) -> XPBalance:
        """
        Create a new XP balance record for a user.
        
        Args:
            user_id: User ID to create balance for
            initial_balance: Initial XP balance
            
        Returns:
            XPBalance: Created balance record
        """
        async with self.get_connection() as conn:
            row = await conn.fetchrow('''
                INSERT INTO xp_balances (user_id, current_balance, lifetime_earned)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET
                    current_balance = EXCLUDED.current_balance,
                    lifetime_earned = EXCLUDED.lifetime_earned,
                    last_updated = CURRENT_TIMESTAMP
                RETURNING *
            ''', user_id, initial_balance, initial_balance)
            
            return XPBalance(
                user_id=row['user_id'],
                current_balance=row['current_balance'],
                lifetime_earned=row['lifetime_earned'],
                lifetime_spent=row['lifetime_spent'],
                prestige_level=row['prestige_level'],
                last_updated=row['last_updated']
            )
    
    async def add_xp(self, user_id: int, amount: int, description: str, 
                     metadata: Optional[Dict[str, Any]] = None) -> Tuple[XPBalance, XPTransaction]:
        """
        Add XP to a user's balance with transaction logging.
        
        Args:
            user_id: User ID to add XP to
            amount: Amount of XP to add (must be positive)
            description: Description of why XP was added
            metadata: Optional metadata for the transaction
            
        Returns:
            Tuple of (updated balance, transaction record)
        """
        if amount <= 0:
            raise ValueError("Amount must be positive when adding XP")
        
        async with self.transaction() as conn:
            # Get current balance or create new one
            current = await self.get_user_balance(user_id)
            if not current:
                current = await self.create_user_balance(user_id, 0)
            
            # Update balance
            new_balance = current.current_balance + amount
            new_lifetime = current.lifetime_earned + amount
            
            row = await conn.fetchrow('''
                UPDATE xp_balances
                SET current_balance = $2,
                    lifetime_earned = $3,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = $1
                RETURNING *
            ''', user_id, new_balance, new_lifetime)
            
            # Log transaction
            tx_row = await conn.fetchrow('''
                INSERT INTO xp_transactions 
                (user_id, transaction_type, amount, balance_before, balance_after, description, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            ''', user_id, 'earn', amount, current.current_balance, new_balance, 
                description, json.dumps(metadata or {}))
            
            balance = XPBalance(
                user_id=row['user_id'],
                current_balance=row['current_balance'],
                lifetime_earned=row['lifetime_earned'],
                lifetime_spent=row['lifetime_spent'],
                prestige_level=row['prestige_level'],
                last_updated=row['last_updated']
            )
            
            transaction = XPTransaction(
                transaction_id=tx_row['transaction_id'],
                user_id=tx_row['user_id'],
                transaction_type=tx_row['transaction_type'],
                amount=tx_row['amount'],
                balance_before=tx_row['balance_before'],
                balance_after=tx_row['balance_after'],
                description=tx_row['description'],
                metadata=json.loads(tx_row['metadata']),
                created_at=tx_row['created_at']
            )
            
            logger.info(f"Added {amount} XP to user {user_id}: {description}")
            return balance, transaction
    
    async def spend_xp(self, user_id: int, amount: int, description: str,
                       metadata: Optional[Dict[str, Any]] = None) -> Tuple[XPBalance, XPTransaction]:
        """
        Spend XP from a user's balance with transaction logging.
        
        Args:
            user_id: User ID to spend XP from
            amount: Amount of XP to spend (must be positive)
            description: Description of what XP was spent on
            metadata: Optional metadata for the transaction
            
        Returns:
            Tuple of (updated balance, transaction record)
            
        Raises:
            ValueError: If insufficient balance
        """
        if amount <= 0:
            raise ValueError("Amount must be positive when spending XP")
        
        async with self.transaction() as conn:
            # Get current balance
            current = await self.get_user_balance(user_id)
            if not current:
                raise ValueError(f"User {user_id} has no XP balance")
            
            if current.current_balance < amount:
                raise ValueError(f"Insufficient XP balance. Has: {current.current_balance}, needs: {amount}")
            
            # Update balance
            new_balance = current.current_balance - amount
            new_lifetime_spent = current.lifetime_spent + amount
            
            row = await conn.fetchrow('''
                UPDATE xp_balances
                SET current_balance = $2,
                    lifetime_spent = $3,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = $1
                RETURNING *
            ''', user_id, new_balance, new_lifetime_spent)
            
            # Log transaction
            tx_row = await conn.fetchrow('''
                INSERT INTO xp_transactions 
                (user_id, transaction_type, amount, balance_before, balance_after, description, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            ''', user_id, 'spend', -amount, current.current_balance, new_balance,
                description, json.dumps(metadata or {}))
            
            balance = XPBalance(
                user_id=row['user_id'],
                current_balance=row['current_balance'],
                lifetime_earned=row['lifetime_earned'],
                lifetime_spent=row['lifetime_spent'],
                prestige_level=row['prestige_level'],
                last_updated=row['last_updated']
            )
            
            transaction = XPTransaction(
                transaction_id=tx_row['transaction_id'],
                user_id=tx_row['user_id'],
                transaction_type=tx_row['transaction_type'],
                amount=tx_row['amount'],
                balance_before=tx_row['balance_before'],
                balance_after=tx_row['balance_after'],
                description=tx_row['description'],
                metadata=json.loads(tx_row['metadata']),
                created_at=tx_row['created_at']
            )
            
            logger.info(f"Spent {amount} XP from user {user_id}: {description}")
            return balance, transaction
    
    # Press Pass Reset Operations
    
    async def reset_press_pass_xp(self, user_id: int) -> Optional[PressPassReset]:
        """
        Reset a Press Pass user's XP to zero.
        
        Args:
            user_id: User ID to reset XP for
            
        Returns:
            PressPassReset record if XP was reset, None if no XP to reset
        """
        async with self.transaction() as conn:
            # Get current balance
            current = await self.get_user_balance(user_id)
            if not current or current.current_balance == 0:
                return None
            
            xp_to_wipe = current.current_balance
            
            # Reset balance to 0
            await conn.execute('''
                UPDATE xp_balances
                SET current_balance = 0,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = $1
            ''', user_id)
            
            # Log the reset transaction
            await conn.execute('''
                INSERT INTO xp_transactions 
                (user_id, transaction_type, amount, balance_before, balance_after, description, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', user_id, 'reset', -xp_to_wipe, xp_to_wipe, 0,
                'Press Pass nightly XP reset', json.dumps({'reset_type': 'nightly'}))
            
            # Record the reset
            reset_row = await conn.fetchrow('''
                INSERT INTO press_pass_resets (user_id, xp_wiped)
                VALUES ($1, $2)
                RETURNING *
            ''', user_id, xp_to_wipe)
            
            # Update shadow stats
            await conn.execute('''
                UPDATE press_pass_shadow_stats
                SET xp_earned_today = 0,
                    trades_executed_today = 0,
                    total_resets = total_resets + 1,
                    last_reset_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            ''', user_id)
            
            logger.info(f"Reset {xp_to_wipe} XP for Press Pass user {user_id}")
            
            return PressPassReset(
                reset_id=reset_row['reset_id'],
                user_id=reset_row['user_id'],
                xp_wiped=reset_row['xp_wiped'],
                reset_at=reset_row['reset_at'],
                notification_sent=reset_row['notification_sent']
            )
    
    async def bulk_reset_press_pass_xp(self, user_ids: List[int]) -> List[PressPassReset]:
        """
        Reset XP for multiple Press Pass users in a single transaction.
        
        Args:
            user_ids: List of user IDs to reset
            
        Returns:
            List of PressPassReset records
        """
        resets = []
        
        async with self.transaction() as conn:
            for user_id in user_ids:
                # Get current balance
                row = await conn.fetchrow('''
                    SELECT current_balance FROM xp_balances WHERE user_id = $1
                ''', user_id)
                
                if row and row['current_balance'] > 0:
                    xp_to_wipe = row['current_balance']
                    
                    # Reset balance
                    await conn.execute('''
                        UPDATE xp_balances
                        SET current_balance = 0,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE user_id = $1
                    ''', user_id)
                    
                    # Log transaction
                    await conn.execute('''
                        INSERT INTO xp_transactions 
                        (user_id, transaction_type, amount, balance_before, balance_after, description, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ''', user_id, 'reset', -xp_to_wipe, xp_to_wipe, 0,
                        'Press Pass nightly XP reset', json.dumps({'reset_type': 'bulk_nightly'}))
                    
                    # Record reset
                    reset_row = await conn.fetchrow('''
                        INSERT INTO press_pass_resets (user_id, xp_wiped)
                        VALUES ($1, $2)
                        RETURNING *
                    ''', user_id, xp_to_wipe)
                    
                    resets.append(PressPassReset(
                        reset_id=reset_row['reset_id'],
                        user_id=reset_row['user_id'],
                        xp_wiped=reset_row['xp_wiped'],
                        reset_at=reset_row['reset_at'],
                        notification_sent=reset_row['notification_sent']
                    ))
            
            # Bulk update shadow stats
            await conn.execute('''
                UPDATE press_pass_shadow_stats
                SET xp_earned_today = 0,
                    trades_executed_today = 0,
                    total_resets = total_resets + 1,
                    last_reset_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ANY($1)
            ''', user_ids)
            
            logger.info(f"Bulk reset XP for {len(resets)} Press Pass users")
            
        return resets
    
    async def mark_reset_notification_sent(self, reset_id: int):
        """Mark a reset notification as sent"""
        async with self.get_connection() as conn:
            await conn.execute('''
                UPDATE press_pass_resets
                SET notification_sent = TRUE
                WHERE reset_id = $1
            ''', reset_id)
    
    # Transaction History
    
    async def get_user_transactions(self, user_id: int, limit: int = 100) -> List[XPTransaction]:
        """
        Get transaction history for a user.
        
        Args:
            user_id: User ID to get transactions for
            limit: Maximum number of transactions to return
            
        Returns:
            List of XPTransaction records
        """
        async with self.get_connection() as conn:
            rows = await conn.fetch('''
                SELECT * FROM xp_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            ''', user_id, limit)
            
            return [
                XPTransaction(
                    transaction_id=row['transaction_id'],
                    user_id=row['user_id'],
                    transaction_type=row['transaction_type'],
                    amount=row['amount'],
                    balance_before=row['balance_before'],
                    balance_after=row['balance_after'],
                    description=row['description'],
                    metadata=json.loads(row['metadata']),
                    created_at=row['created_at']
                )
                for row in rows
            ]
    
    # Analytics and Reporting
    
    async def get_xp_statistics(self) -> Dict[str, Any]:
        """
        Get overall XP economy statistics.
        
        Returns:
            Dict containing various XP metrics
        """
        async with self.get_connection() as conn:
            # Total XP in circulation
            total_row = await conn.fetchrow('''
                SELECT 
                    SUM(current_balance) as total_circulation,
                    SUM(lifetime_earned) as total_earned,
                    SUM(lifetime_spent) as total_spent,
                    COUNT(*) as total_users
                FROM xp_balances
            ''')
            
            # Top XP holders
            top_holders = await conn.fetch('''
                SELECT user_id, current_balance
                FROM xp_balances
                ORDER BY current_balance DESC
                LIMIT 10
            ''')
            
            # Recent activity
            recent_activity = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as transactions_24h,
                    SUM(CASE WHEN transaction_type = 'earn' THEN amount ELSE 0 END) as earned_24h,
                    SUM(CASE WHEN transaction_type = 'spend' THEN ABS(amount) ELSE 0 END) as spent_24h
                FROM xp_transactions
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            ''')
            
            # Press Pass reset stats
            reset_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_resets,
                    SUM(xp_wiped) as total_xp_wiped,
                    COUNT(DISTINCT user_id) as unique_users_reset
                FROM press_pass_resets
                WHERE reset_at >= NOW() - INTERVAL '7 days'
            ''')
            
            return {
                'total_circulation': total_row['total_circulation'] or 0,
                'total_earned': total_row['total_earned'] or 0,
                'total_spent': total_row['total_spent'] or 0,
                'total_users': total_row['total_users'] or 0,
                'top_holders': [
                    {'user_id': row['user_id'], 'balance': row['current_balance']}
                    for row in top_holders
                ],
                'activity_24h': {
                    'transactions': recent_activity['transactions_24h'] or 0,
                    'earned': recent_activity['earned_24h'] or 0,
                    'spent': recent_activity['spent_24h'] or 0
                },
                'press_pass_resets_7d': {
                    'total_resets': reset_stats['total_resets'] or 0,
                    'xp_wiped': reset_stats['total_xp_wiped'] or 0,
                    'unique_users': reset_stats['unique_users_reset'] or 0
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def get_press_pass_users_for_reset(self) -> List[int]:
        """
        Get list of Press Pass users who need XP reset.
        
        Returns:
            List of user IDs with positive XP balance
        """
        async with self.get_connection() as conn:
            rows = await conn.fetch('''
                SELECT DISTINCT xb.user_id
                FROM xp_balances xb
                INNER JOIN press_pass_shadow_stats ps ON xb.user_id = ps.user_id
                WHERE xb.current_balance > 0
            ''')
            
            return [row['user_id'] for row in rows]

# Helper functions for easy access

async def init_xp_database() -> XPDatabase:
    """Initialize and return XP database instance"""
    db = XPDatabase()
    await db.initialize()
    await db.initialize_tables()
    return db

async def add_user_xp(user_id: int, amount: int, description: str) -> Tuple[XPBalance, XPTransaction]:
    """Helper function to add XP to a user"""
    db = await init_xp_database()
    try:
        return await db.add_xp(user_id, amount, description)
    finally:
        await db.close()

async def spend_user_xp(user_id: int, amount: int, description: str) -> Tuple[XPBalance, XPTransaction]:
    """Helper function to spend XP from a user"""
    db = await init_xp_database()
    try:
        return await db.spend_xp(user_id, amount, description)
    finally:
        await db.close()

async def get_user_xp_balance(user_id: int) -> Optional[XPBalance]:
    """Helper function to get user's XP balance"""
    db = await init_xp_database()
    try:
        return await db.get_user_balance(user_id)
    finally:
        await db.close()

async def reset_all_press_pass_xp() -> List[PressPassReset]:
    """Helper function to reset all Press Pass users' XP"""
    db = await init_xp_database()
    try:
        user_ids = await db.get_press_pass_users_for_reset()
        if user_ids:
            return await db.bulk_reset_press_pass_xp(user_ids)
        return []
    finally:
        await db.close()

# Main execution for testing
if __name__ == "__main__":
    async def test_xp_database():
        """Test XP database functionality"""
        print("Initializing XP database...")
        db = await init_xp_database()
        
        try:
            # Test user ID
            test_user_id = 12345
            
            # Test adding XP
            print(f"\nAdding 100 XP to user {test_user_id}...")
            balance, tx = await db.add_xp(test_user_id, 100, "Test XP award")
            print(f"✓ New balance: {balance.current_balance} XP")
            
            # Test spending XP
            print(f"\nSpending 30 XP from user {test_user_id}...")
            balance, tx = await db.spend_xp(test_user_id, 30, "Test purchase")
            print(f"✓ New balance: {balance.current_balance} XP")
            
            # Test getting balance
            print(f"\nGetting balance for user {test_user_id}...")
            balance = await db.get_user_balance(test_user_id)
            if balance:
                print(f"✓ Current balance: {balance.current_balance} XP")
                print(f"  Lifetime earned: {balance.lifetime_earned} XP")
                print(f"  Lifetime spent: {balance.lifetime_spent} XP")
            
            # Test transaction history
            print(f"\nGetting transaction history...")
            transactions = await db.get_user_transactions(test_user_id, limit=5)
            print(f"✓ Found {len(transactions)} transactions")
            
            # Test XP statistics
            print(f"\nGetting XP statistics...")
            stats = await db.get_xp_statistics()
            print(f"✓ Total XP in circulation: {stats['total_circulation']:}")
            print(f"  Total users: {stats['total_users']}")
            
            print("\n✅ XP database is ready for use!")
            
        finally:
            await db.close()
    
    # Run the test
    asyncio.run(test_xp_database())