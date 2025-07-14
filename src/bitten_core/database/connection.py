"""
BITTEN Database Connection Module

Provides database connection management with proper error handling,
connection pooling, and async support for PostgreSQL.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
import asyncpg
from asyncpg.pool import Pool
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError
import json

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'bitten_db')
        self.user = os.getenv('DB_USER', 'bitten_app')
        self.password = os.getenv('DB_PASSWORD', '')
        self.min_pool_size = int(os.getenv('DB_MIN_POOL_SIZE', '10'))
        self.max_pool_size = int(os.getenv('DB_MAX_POOL_SIZE', '20'))
        self.command_timeout = float(os.getenv('DB_COMMAND_TIMEOUT', '60'))
        self.max_inactive_connection_lifetime = float(os.getenv('DB_MAX_INACTIVE_CONNECTION_LIFETIME', '300'))
        
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_string(self) -> str:
        """Get async PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseConnection:
    """Manages database connections with pooling and error handling"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._async_pool: Optional[Pool] = None
        self._sync_engine = None
        self._sync_session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database connections"""
        if self._initialized:
            return
            
        try:
            # Create async connection pool
            self._async_pool = await asyncpg.create_pool(
                self.config.async_connection_string,
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
                command_timeout=self.config.command_timeout,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime
            )
            
            # Create sync engine for SQLAlchemy
            self._sync_engine = create_engine(
                self.config.connection_string,
                poolclass=NullPool,  # Use external pooling
                echo=False
            )
            
            # Create session factory
            self._sync_session_factory = sessionmaker(
                bind=self._sync_engine,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def close(self):
        """Close all database connections"""
        if self._async_pool:
            await self._async_pool.close()
            self._async_pool = None
            
        if self._sync_engine:
            self._sync_engine.dispose()
            self._sync_engine = None
            
        self._initialized = False
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def acquire_async(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire async database connection from pool"""
        if not self._initialized:
            await self.initialize()
            
        async with self._async_pool.acquire() as connection:
            yield connection
    
    def get_sync_session(self) -> Session:
        """Get synchronous database session"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
            
        return self._sync_session_factory()
    
    async def execute_query(self, query: str, *args, **kwargs) -> list:
        """Execute a query and return results"""
        async with self.acquire_async() as conn:
            try:
                return await conn.fetch(query, *args, **kwargs)
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise
    
    async def execute_command(self, command: str, *args, **kwargs):
        """Execute a command (no return value expected)"""
        async with self.acquire_async() as conn:
            try:
                await conn.execute(command, *args, **kwargs)
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                raise


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Get or create database connection instance"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get async database connection for use in async contexts"""
    db = get_db_connection()
    async with db.acquire_async() as conn:
        yield conn


def get_sync_db() -> Session:
    """Get sync database session for use in sync contexts"""
    db = get_db_connection()
    return db.get_sync_session()


def get_db_session() -> Session:
    """Alias for get_sync_db for backward compatibility"""
    return get_sync_db()


class DatabaseSession:
    """Context manager for sync database sessions with automatic commit/rollback"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_sync_db()
        self._should_close = session is None
        
    def __enter__(self) -> Session:
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            logger.warning(f"Database transaction rolled back due to: {exc_val}")
        else:
            try:
                self.session.commit()
            except SQLAlchemyError as e:
                self.session.rollback()
                logger.error(f"Failed to commit transaction: {e}")
                raise
        
        if self._should_close:
            self.session.close()


async def test_connection() -> bool:
    """Test database connectivity"""
    try:
        db = get_db_connection()
        await db.initialize()
        result = await db.execute_query("SELECT 1 as test")
        return result[0]['test'] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False