"""
🎯 BITTEN Database Connection Manager
Handles PostgreSQL connections, sessions, and migrations
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.engine import Engine
from alembic import command
from alembic.config import Config

from .models import Base

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self):
        # Get from environment or use defaults
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'bitten_production')
        self.username = os.getenv('DB_USER', 'bitten_app')
        self.password = os.getenv('DB_PASSWORD', '')  # Must be set via environment
        
        # Connection pool settings
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        
        # Build connection string
        self.connection_string = (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )
        
        # SSL mode for production
        if os.getenv('DB_SSL_MODE'):
            self.connection_string += f"?sslmode={os.getenv('DB_SSL_MODE')}"

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        
    @property
    def engine(self) -> Engine:
        """Get or create database engine"""
        if self._engine is None:
            self._engine = create_engine(
                self.config.connection_string,
                poolclass=pool.QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,  # Verify connections before using
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
            )
            
            # Add event listeners
            self._setup_event_listeners()
            
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._session_factory
    
    @property
    def scoped_session(self) -> scoped_session:
        """Get scoped session for thread-safe operations"""
        if self._scoped_session is None:
            self._scoped_session = scoped_session(self.session_factory)
        return self._scoped_session
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Set session parameters on connect"""
            with dbapi_conn.cursor() as cursor:
                # Set timezone to UTC
                cursor.execute("SET timezone TO 'UTC'")
                # Set statement timeout (30 seconds)
                cursor.execute("SET statement_timeout TO '30s'")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Verify connection on checkout from pool"""
            # This is handled by pool_pre_ping=True
            pass
    
    @contextmanager
    def session_scope(self) -> Session:
        """
        Provide a transactional scope for database operations
        
        Usage:
            with db.session_scope() as session:
                user = session.query(User).first()
                session.commit()
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_all_tables(self):
        """Create all tables (for development)"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("All database tables created")
    
    def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    def init_alembic(self):
        """Initialize Alembic for migrations"""
        alembic_cfg = Config("alembic.ini")
        command.init(alembic_cfg, "migrations")
        logger.info("Alembic initialized")
    
    def create_migration(self, message: str):
        """Create a new migration"""
        alembic_cfg = Config("alembic.ini")
        command.revision(alembic_cfg, autogenerate=True, message=message)
        logger.info(f"Migration created: {message}")
    
    def upgrade_database(self, revision: str = "head"):
        """Upgrade database to revision"""
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, revision)
        logger.info(f"Database upgraded to: {revision}")
    
    def downgrade_database(self, revision: str):
        """Downgrade database to revision"""
        alembic_cfg = Config("alembic.ini")
        command.downgrade(alembic_cfg, revision)
        logger.info(f"Database downgraded to: {revision}")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status"""
        pool = self.engine.pool
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total': pool.checkedin() + pool.checkedout()
        }
    
    def close(self):
        """Close all connections"""
        if self._scoped_session:
            self._scoped_session.remove()
        
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """Get or create global database manager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def get_db_session() -> Session:
    """Get a database session"""
    return get_db_manager().scoped_session()

# Convenience functions
def init_database():
    """Initialize database (create tables)"""
    db = get_db_manager()
    db.create_all_tables()
    logger.info("Database initialized")

def close_database():
    """Close database connections"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None

# Health check function
def check_database_health() -> Dict[str, Any]:
    """Check database health"""
    try:
        db = get_db_manager()
        
        # Test connection
        with db.session_scope() as session:
            result = session.execute("SELECT 1").scalar()
            
        pool_status = db.get_pool_status()
        
        return {
            'status': 'healthy',
            'connected': True,
            'pool_status': pool_status
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'connected': False,
            'error': str(e)
        }