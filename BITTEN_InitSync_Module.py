#!/usr/bin/env python3
"""
🎯 BITTEN INITSYNC MODULE - Critical System Initialization & Synchronization
Version: 1.0 FORTRESS INTEGRATION
Status: OPERATIONAL - BRIDGE INTEGRATED

MISSION: Complete initialization and synchronization of BITTEN ecosystem components
- User authentication and session management
- Bridge assignment and validation
- Tier verification and risk profile setup
- Multi-platform state synchronization
- Recovery and failover procedures

INTEGRATION POINTS:
- Enhanced Bridge Troll system
- Telegram Bot authentication
- WebApp session management
- MT5 EA initialization
- Persona and XP systems
"""

import os
import sys
import json
import time
import sqlite3
import logging
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import uuid

# Import Bridge Troll integration
try:
    from troll_integration import (
        troll_record_sync, troll_record_error, troll_get_bridge_status,
        troll_get_user_info, troll_validate_fire, TROLL_INTEGRATION
    )
    TROLL_AVAILABLE = True
except ImportError:
    TROLL_AVAILABLE = False
    logging.warning("⚠️ Bridge Troll integration not available")

class InitSyncStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    RECOVERY = "RECOVERY"

class UserTier(Enum):
    PRESS_PASS = "press_pass"
    NIBBLER = "nibbler"
    FANG = "fang"
    COMMANDER = "commander"
    APEX = "apex"

class Platform(Enum):
    TELEGRAM = "telegram"
    WEBAPP = "webapp"
    MT5_EA = "mt5_ea"
    API = "api"

@dataclass
class InitSyncSession:
    session_id: str
    telegram_id: int
    user_id: str
    bridge_id: Optional[str]
    account_id: Optional[str]
    tier: UserTier
    platforms: List[Platform]
    status: InitSyncStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    auth_token: str
    balance: Optional[float]
    equity: Optional[float]
    persona: Optional[str]
    xp_level: int
    risk_profile: Dict[str, Any]
    session_data: Dict[str, Any]
    error_message: Optional[str]

@dataclass
class BridgeAssignment:
    bridge_id: str
    telegram_id: int
    account_id: str
    assigned_at: datetime
    tier: UserTier
    status: str
    last_sync: Optional[datetime]
    sync_data: Dict[str, Any]

class BITTENInitSync:
    """
    🎯 BITTEN INITIALIZATION & SYNCHRONIZATION MODULE
    
    CORE RESPONSIBILITIES:
    - Complete user authentication and session management
    - Bridge assignment and health validation
    - Cross-platform state synchronization
    - Tier verification and risk profile setup
    - Recovery procedures and failover handling
    """
    
    def __init__(self, db_path: str = "/root/HydraX-v2/bitten_initsync.db"):
        self.module_name = "BITTEN_INITSYNC"
        self.version = "1.0_FORTRESS_INTEGRATION"
        self.db_path = db_path
        self.session_timeout = 3600  # 1 hour default
        self.max_concurrent_sessions = 1000
        
        # Bridge integration
        self.bridge_server = "localhost"
        self.bridge_ports = [5555, 5556, 5557]
        
        # Active sessions cache
        self.active_sessions = {}
        self.bridge_assignments = {}
        self.pending_syncs = {}
        
        # Initialize systems
        self.setup_logging()
        self.init_database()
        self.start_background_tasks()
        
        self.logger.info(f"🎯 BITTEN INITSYNC MODULE {self.version} INITIALIZED")
        self.logger.info(f"📊 Database: {self.db_path}")
        self.logger.info(f"🔗 Bridge Troll Integration: {'✅' if TROLL_AVAILABLE else '❌'}")
        
    def setup_logging(self):
        """Initialize logging system"""
        log_format = '%(asctime)s - BITTEN_INITSYNC - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('/root/HydraX-v2/bitten_initsync.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("BITTEN_INITSYNC")
        
    def init_database(self):
        """Initialize SQLite database for session management"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute('PRAGMA journal_mode=WAL')
            
            # Create tables
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS init_sessions (
                    session_id TEXT PRIMARY KEY,
                    telegram_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    bridge_id TEXT,
                    account_id TEXT,
                    tier TEXT NOT NULL,
                    platforms TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    auth_token TEXT NOT NULL,
                    balance REAL,
                    equity REAL,
                    persona TEXT,
                    xp_level INTEGER DEFAULT 0,
                    risk_profile TEXT,
                    session_data TEXT,
                    error_message TEXT
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS bridge_assignments (
                    bridge_id TEXT PRIMARY KEY,
                    telegram_id INTEGER NOT NULL,
                    account_id TEXT NOT NULL,
                    assigned_at TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_sync TEXT,
                    sync_data TEXT
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_history (
                    sync_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    sync_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    data TEXT,
                    error_message TEXT
                )
            ''')
            
            # Create indexes
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_telegram ON init_sessions(telegram_id)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON init_sessions(status)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_assignments_telegram ON bridge_assignments(telegram_id)')
            
            self.conn.commit()
            self.logger.info(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise
            
    def start_background_tasks(self):
        """Start background monitoring and cleanup tasks"""
        # Session cleanup thread
        cleanup_thread = threading.Thread(target=self.session_cleanup_loop, daemon=True)
        cleanup_thread.start()
        
        # Sync monitoring thread
        sync_thread = threading.Thread(target=self.sync_monitoring_loop, daemon=True)
        sync_thread.start()
        
        self.logger.info(f"🔄 Background tasks started")
        
    def create_session(self, telegram_id: int, user_id: str, tier: str, 
                      platforms: List[str], **kwargs) -> Tuple[bool, str, Optional[InitSyncSession]]:
        """Create new initialization session"""
        try:
            # Generate session ID and auth token
            session_id = f"init_{telegram_id}_{int(time.time())}"
            auth_token = self.generate_auth_token(telegram_id, session_id)
            
            # Create session object
            now = datetime.now(timezone.utc)
            session = InitSyncSession(
                session_id=session_id,
                telegram_id=telegram_id,
                user_id=user_id,
                bridge_id=None,  # Will be assigned during sync
                account_id=None,
                tier=UserTier(tier),
                platforms=[Platform(p) for p in platforms],
                status=InitSyncStatus.PENDING,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(seconds=self.session_timeout),
                auth_token=auth_token,
                balance=kwargs.get('balance'),
                equity=kwargs.get('equity'),
                persona=kwargs.get('persona'),
                xp_level=kwargs.get('xp_level', 0),
                risk_profile=kwargs.get('risk_profile', {}),
                session_data=kwargs.get('session_data', {}),
                error_message=None
            )
            
            # Save to database
            self.save_session(session)
            
            # Add to active sessions
            self.active_sessions[session_id] = session
            
            self.logger.info(f"✅ Session created: {session_id} for user {telegram_id}")
            return True, session_id, session
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create session: {e}")
            return False, str(e), None
            
    def initialize_user(self, session_id: str) -> Tuple[bool, str]:
        """Initialize user with complete system setup"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False, "Session not found"
                
            if session.status != InitSyncStatus.PENDING:
                return False, f"Invalid session status: {session.status.value}"
                
            # Update status to in progress
            session.status = InitSyncStatus.IN_PROGRESS
            session.updated_at = datetime.now(timezone.utc)
            self.save_session(session)
            
            self.logger.info(f"🚀 Starting initialization for session {session_id}")
            
            # Step 1: Assign bridge
            bridge_assigned, bridge_msg = self.assign_bridge(session)
            if not bridge_assigned:
                session.status = InitSyncStatus.FAILED
                session.error_message = f"Bridge assignment failed: {bridge_msg}"
                self.save_session(session)
                return False, bridge_msg
                
            # Step 2: Validate tier and setup risk profile
            tier_valid, tier_msg = self.validate_tier_setup(session)
            if not tier_valid:
                session.status = InitSyncStatus.FAILED
                session.error_message = f"Tier validation failed: {tier_msg}"
                self.save_session(session)
                return False, tier_msg
                
            # Step 3: Initialize platforms
            for platform in session.platforms:
                platform_init, platform_msg = self.initialize_platform(session, platform)
                if not platform_init:
                    self.logger.warning(f"⚠️ Platform {platform.value} initialization failed: {platform_msg}")
                    # Continue with other platforms
                    
            # Step 4: Sync with Bridge Troll
            if TROLL_AVAILABLE:
                troll_sync, troll_msg = self.sync_with_bridge_troll(session)
                if not troll_sync:
                    self.logger.warning(f"⚠️ Bridge Troll sync failed: {troll_msg}")
                    
            # Step 5: Final validation
            final_valid, final_msg = self.final_validation(session)
            if not final_valid:
                session.status = InitSyncStatus.FAILED
                session.error_message = f"Final validation failed: {final_msg}"
                self.save_session(session)
                return False, final_msg
                
            # Mark as completed
            session.status = InitSyncStatus.COMPLETED
            session.updated_at = datetime.now(timezone.utc)
            self.save_session(session)
            
            self.logger.info(f"✅ Initialization completed for session {session_id}")
            return True, "Initialization completed successfully"
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            # Update session with error
            if 'session' in locals():
                session.status = InitSyncStatus.FAILED
                session.error_message = str(e)
                self.save_session(session)
            return False, str(e)
            
    def assign_bridge(self, session: InitSyncSession) -> Tuple[bool, str]:
        """Assign bridge to user session"""
        try:
            # Find available bridge based on tier
            bridge_id = self.find_available_bridge(session.tier)
            if not bridge_id:
                return False, "No available bridges for tier"
                
            # Check bridge health if Troll available
            if TROLL_AVAILABLE:
                bridge_status = troll_get_bridge_status(bridge_id)
                if not bridge_status or bridge_status.get('state') != 'ONLINE':
                    return False, f"Bridge {bridge_id} not online"
                    
            # Assign bridge
            session.bridge_id = bridge_id
            session.account_id = self.generate_account_id(session.telegram_id, bridge_id)
            
            # Create bridge assignment record
            assignment = BridgeAssignment(
                bridge_id=bridge_id,
                telegram_id=session.telegram_id,
                account_id=session.account_id,
                assigned_at=datetime.now(timezone.utc),
                tier=session.tier,
                status="assigned",
                last_sync=None,
                sync_data={}
            )
            
            self.save_bridge_assignment(assignment)
            self.bridge_assignments[bridge_id] = assignment
            
            self.logger.info(f"🌉 Bridge assigned: {bridge_id} to user {session.telegram_id}")
            return True, f"Bridge {bridge_id} assigned"
            
        except Exception as e:
            self.logger.error(f"❌ Bridge assignment failed: {e}")
            return False, str(e)
            
    def find_available_bridge(self, tier: UserTier) -> Optional[str]:
        """Find available bridge for user tier"""
        # Tier-based bridge allocation
        tier_bridge_ranges = {
            UserTier.PRESS_PASS: range(1, 6),    # bridges 001-005
            UserTier.NIBBLER: range(6, 11),      # bridges 006-010
            UserTier.FANG: range(11, 16),        # bridges 011-015
            UserTier.COMMANDER: range(16, 21),   # bridges 016-020
            UserTier.APEX: range(21, 26)         # bridges 021-025
        }
        
        bridge_range = tier_bridge_ranges.get(tier, range(1, 6))
        
        for bridge_num in bridge_range:
            bridge_id = f"bridge_{bridge_num:03d}"
            
            # Check if bridge is already assigned
            if bridge_id in self.bridge_assignments:
                continue
                
            # Check bridge health if Troll available
            if TROLL_AVAILABLE:
                bridge_status = troll_get_bridge_status(bridge_id)
                if bridge_status and bridge_status.get('state') == 'ONLINE':
                    return bridge_id
            else:
                # Fallback: assume bridge is available
                return bridge_id
                
        return None
        
    def validate_tier_setup(self, session: InitSyncSession) -> Tuple[bool, str]:
        """Validate user tier and setup risk profile"""
        try:
            # Tier validation rules
            tier_configs = {
                UserTier.PRESS_PASS: {
                    "max_lot_size": 0.01,
                    "max_daily_loss": 50.0,
                    "fire_modes": ["manual"],
                    "session_duration": 3600  # 1 hour
                },
                UserTier.NIBBLER: {
                    "max_lot_size": 0.1,
                    "max_daily_loss": 200.0,
                    "fire_modes": ["manual"],
                    "session_duration": 86400  # 24 hours
                },
                UserTier.FANG: {
                    "max_lot_size": 0.5,
                    "max_daily_loss": 500.0,
                    "fire_modes": ["manual"],
                    "session_duration": 86400
                },
                UserTier.COMMANDER: {
                    "max_lot_size": 1.0,
                    "max_daily_loss": 1000.0,
                    "fire_modes": ["manual", "semi_auto", "full_auto"],
                    "session_duration": 86400
                },
                UserTier.APEX: {
                    "max_lot_size": 2.0,
                    "max_daily_loss": 2000.0,
                    "fire_modes": ["manual", "semi_auto", "full_auto"],
                    "session_duration": 86400
                }
            }
            
            tier_config = tier_configs.get(session.tier)
            if not tier_config:
                return False, f"Invalid tier: {session.tier.value}"
                
            # Setup risk profile
            session.risk_profile = tier_config.copy()
            session.risk_profile["tier"] = session.tier.value
            session.risk_profile["setup_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update session timeout for tier
            session.expires_at = session.created_at + timedelta(seconds=tier_config["session_duration"])
            
            self.logger.info(f"✅ Tier validated: {session.tier.value} for user {session.telegram_id}")
            return True, "Tier validation successful"
            
        except Exception as e:
            self.logger.error(f"❌ Tier validation failed: {e}")
            return False, str(e)
            
    def initialize_platform(self, session: InitSyncSession, platform: Platform) -> Tuple[bool, str]:
        """Initialize specific platform integration"""
        try:
            if platform == Platform.TELEGRAM:
                return self.init_telegram_platform(session)
            elif platform == Platform.WEBAPP:
                return self.init_webapp_platform(session)
            elif platform == Platform.MT5_EA:
                return self.init_mt5_platform(session)
            elif platform == Platform.API:
                return self.init_api_platform(session)
            else:
                return False, f"Unknown platform: {platform.value}"
                
        except Exception as e:
            self.logger.error(f"❌ Platform {platform.value} initialization failed: {e}")
            return False, str(e)
            
    def init_telegram_platform(self, session: InitSyncSession) -> Tuple[bool, str]:
        """Initialize Telegram bot integration"""
        try:
            # Setup Telegram session data
            telegram_data = {
                "user_id": session.user_id,
                "telegram_id": session.telegram_id,
                "tier": session.tier.value,
                "bridge_id": session.bridge_id,
                "account_id": session.account_id,
                "auth_token": session.auth_token,
                "fire_modes": session.risk_profile.get("fire_modes", ["manual"]),
                "initialized_at": datetime.now(timezone.utc).isoformat()
            }
            
            session.session_data["telegram"] = telegram_data
            
            self.logger.info(f"✅ Telegram platform initialized for user {session.telegram_id}")
            return True, "Telegram platform initialized"
            
        except Exception as e:
            return False, str(e)
            
    def init_webapp_platform(self, session: InitSyncSession) -> Tuple[bool, str]:
        """Initialize WebApp integration"""
        try:
            # Setup WebApp session data
            webapp_data = {
                "session_id": session.session_id,
                "auth_token": session.auth_token,
                "bridge_id": session.bridge_id,
                "tier": session.tier.value,
                "risk_profile": session.risk_profile,
                "webapp_url": f"https://joinbitten.com?session={session.session_id}",
                "initialized_at": datetime.now(timezone.utc).isoformat()
            }
            
            session.session_data["webapp"] = webapp_data
            
            self.logger.info(f"✅ WebApp platform initialized for user {session.telegram_id}")
            return True, "WebApp platform initialized"
            
        except Exception as e:
            return False, str(e)
            
    def init_mt5_platform(self, session: InitSyncSession) -> Tuple[bool, str]:
        """Initialize MT5 EA integration"""
        try:
            # Setup MT5 EA configuration
            mt5_data = {
                "bridge_id": session.bridge_id,
                "account_id": session.account_id,
                "terminal_path": f"C:\\Users\\Administrator\\AppData\\Roaming\\MetaQuotes\\Terminal\\173477FF1060D99CE79296FC73108719\\MQL5\\Files\\BITTEN\\",
                "ea_magic": 50000 + session.telegram_id % 200,
                "max_lot_size": session.risk_profile.get("max_lot_size", 0.01),
                "max_daily_loss": session.risk_profile.get("max_daily_loss", 50.0),
                "initialized_at": datetime.now(timezone.utc).isoformat()
            }
            
            session.session_data["mt5"] = mt5_data
            
            self.logger.info(f"✅ MT5 platform initialized for user {session.telegram_id}")
            return True, "MT5 platform initialized"
            
        except Exception as e:
            return False, str(e)
            
    def init_api_platform(self, session: InitSyncSession) -> Tuple[bool, str]:
        """Initialize API access"""
        try:
            # Setup API configuration
            api_data = {
                "auth_token": session.auth_token,
                "api_key": self.generate_api_key(session.telegram_id),
                "rate_limit": self.get_tier_rate_limit(session.tier),
                "endpoints": [
                    "/api/v1/signals",
                    "/api/v1/trades",
                    "/api/v1/balance",
                    "/api/v1/status"
                ],
                "initialized_at": datetime.now(timezone.utc).isoformat()
            }
            
            session.session_data["api"] = api_data
            
            self.logger.info(f"✅ API platform initialized for user {session.telegram_id}")
            return True, "API platform initialized"
            
        except Exception as e:
            return False, str(e)
            
    def sync_with_bridge_troll(self, session: InitSyncSession) -> Tuple[bool, str]:
        """Sync session with Bridge Troll system"""
        try:
            if not TROLL_AVAILABLE:
                return True, "Bridge Troll not available - skipping"
                
            # Prepare sync data
            sync_data = {
                "user_id": session.user_id,
                "account_id": session.account_id,
                "balance": session.balance or 0.0,
                "equity": session.equity or 0.0,
                "tier": session.tier.value,
                "risk_profile": session.risk_profile,
                "metadata": {
                    "session_id": session.session_id,
                    "auth_token": session.auth_token,
                    "platforms": [p.value for p in session.platforms]
                }
            }
            
            # Record sync with Bridge Troll
            success = troll_record_sync(session.bridge_id, session.telegram_id, sync_data)
            
            if success:
                self.logger.info(f"✅ Bridge Troll sync completed for session {session.session_id}")
                return True, "Bridge Troll sync successful"
            else:
                return False, "Bridge Troll sync failed"
                
        except Exception as e:
            self.logger.error(f"❌ Bridge Troll sync failed: {e}")
            return False, str(e)
            
    def final_validation(self, session: InitSyncSession) -> Tuple[bool, str]:
        """Perform final validation before marking session complete"""
        try:
            # Check required fields
            required_fields = [
                ('bridge_id', session.bridge_id),
                ('account_id', session.account_id),
                ('tier', session.tier),
                ('auth_token', session.auth_token)
            ]
            
            for field_name, field_value in required_fields:
                if not field_value:
                    return False, f"Missing required field: {field_name}"
                    
            # Check platform initialization
            for platform in session.platforms:
                platform_key = platform.value
                if platform_key not in session.session_data:
                    return False, f"Platform {platform_key} not initialized"
                    
            # Check bridge assignment
            if session.bridge_id not in self.bridge_assignments:
                return False, "Bridge assignment not found"
                
            # Validate Bridge Troll integration
            if TROLL_AVAILABLE:
                bridge_status = troll_get_bridge_status(session.bridge_id)
                if not bridge_status:
                    return False, "Bridge status validation failed"
                    
            self.logger.info(f"✅ Final validation passed for session {session.session_id}")
            return True, "Final validation successful"
            
        except Exception as e:
            self.logger.error(f"❌ Final validation failed: {e}")
            return False, str(e)
            
    def get_session(self, session_id: str) -> Optional[InitSyncSession]:
        """Get session by ID"""
        try:
            # Check cache first
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                if session.expires_at > datetime.now(timezone.utc):
                    return session
                else:
                    # Session expired
                    del self.active_sessions[session_id]
                    return None
                    
            # Load from database
            cursor = self.conn.execute('''
                SELECT * FROM init_sessions WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Convert to session object
            session = self.row_to_session(row)
            
            # Check if expired
            if session.expires_at <= datetime.now(timezone.utc):
                session.status = InitSyncStatus.EXPIRED
                self.save_session(session)
                return None
                
            # Add to cache
            self.active_sessions[session_id] = session
            return session
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get session: {e}")
            return None
            
    def save_session(self, session: InitSyncSession):
        """Save session to database"""
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO init_sessions 
                (session_id, telegram_id, user_id, bridge_id, account_id, tier, platforms, 
                 status, created_at, updated_at, expires_at, auth_token, balance, equity, 
                 persona, xp_level, risk_profile, session_data, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.telegram_id,
                session.user_id,
                session.bridge_id,
                session.account_id,
                session.tier.value,
                json.dumps([p.value for p in session.platforms]),
                session.status.value,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.expires_at.isoformat(),
                session.auth_token,
                session.balance,
                session.equity,
                session.persona,
                session.xp_level,
                json.dumps(session.risk_profile),
                json.dumps(session.session_data),
                session.error_message
            ))
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save session: {e}")
            
    def save_bridge_assignment(self, assignment: BridgeAssignment):
        """Save bridge assignment to database"""
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO bridge_assignments 
                (bridge_id, telegram_id, account_id, assigned_at, tier, status, last_sync, sync_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                assignment.bridge_id,
                assignment.telegram_id,
                assignment.account_id,
                assignment.assigned_at.isoformat(),
                assignment.tier.value,
                assignment.status,
                assignment.last_sync.isoformat() if assignment.last_sync else None,
                json.dumps(assignment.sync_data)
            ))
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save bridge assignment: {e}")
            
    def row_to_session(self, row) -> InitSyncSession:
        """Convert database row to session object"""
        return InitSyncSession(
            session_id=row[0],
            telegram_id=row[1],
            user_id=row[2],
            bridge_id=row[3],
            account_id=row[4],
            tier=UserTier(row[5]),
            platforms=[Platform(p) for p in json.loads(row[6])],
            status=InitSyncStatus(row[7]),
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9]),
            expires_at=datetime.fromisoformat(row[10]),
            auth_token=row[11],
            balance=row[12],
            equity=row[13],
            persona=row[14],
            xp_level=row[15] or 0,
            risk_profile=json.loads(row[16]) if row[16] else {},
            session_data=json.loads(row[17]) if row[17] else {},
            error_message=row[18]
        )
        
    def generate_auth_token(self, telegram_id: int, session_id: str) -> str:
        """Generate secure authentication token"""
        data = f"{telegram_id}:{session_id}:{time.time()}:{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()
        
    def generate_account_id(self, telegram_id: int, bridge_id: str) -> str:
        """Generate account ID for bridge assignment"""
        return f"BITTEN_{telegram_id}_{bridge_id.replace('bridge_', '')}"
        
    def generate_api_key(self, telegram_id: int) -> str:
        """Generate API key for user"""
        data = f"api_key:{telegram_id}:{time.time()}:{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
        
    def get_tier_rate_limit(self, tier: UserTier) -> int:
        """Get API rate limit for user tier"""
        limits = {
            UserTier.PRESS_PASS: 10,    # 10 requests per minute
            UserTier.NIBBLER: 60,       # 60 requests per minute
            UserTier.FANG: 120,         # 120 requests per minute
            UserTier.COMMANDER: 300,    # 300 requests per minute
            UserTier.APEX: 600          # 600 requests per minute
        }
        return limits.get(tier, 10)
        
    def session_cleanup_loop(self):
        """Background task to clean up expired sessions"""
        while True:
            try:
                now = datetime.now(timezone.utc)
                
                # Clean expired sessions from cache
                expired_sessions = []
                for session_id, session in self.active_sessions.items():
                    if session.expires_at <= now:
                        expired_sessions.append(session_id)
                        
                for session_id in expired_sessions:
                    del self.active_sessions[session_id]
                    self.logger.info(f"🧹 Cleaned expired session: {session_id}")
                    
                # Update database
                self.conn.execute('''
                    UPDATE init_sessions SET status = ? WHERE expires_at <= ? AND status != ?
                ''', (InitSyncStatus.EXPIRED.value, now.isoformat(), InitSyncStatus.EXPIRED.value))
                self.conn.commit()
                
                time.sleep(300)  # Clean every 5 minutes
                
            except Exception as e:
                self.logger.error(f"❌ Session cleanup error: {e}")
                time.sleep(60)
                
    def sync_monitoring_loop(self):
        """Background task to monitor sync health"""
        while True:
            try:
                # Monitor active sessions
                for session_id, session in self.active_sessions.items():
                    if session.status == InitSyncStatus.IN_PROGRESS:
                        # Check if session has been in progress too long
                        duration = datetime.now(timezone.utc) - session.updated_at
                        if duration.total_seconds() > 300:  # 5 minutes
                            self.logger.warning(f"⚠️ Session {session_id} stuck in progress")
                            
                time.sleep(60)  # Monitor every minute
                
            except Exception as e:
                self.logger.error(f"❌ Sync monitoring error: {e}")
                time.sleep(60)

# Global InitSync instance
BITTEN_INITSYNC = None

def get_bitten_initsync() -> BITTENInitSync:
    """Get global BITTEN InitSync instance"""
    global BITTEN_INITSYNC
    if BITTEN_INITSYNC is None:
        BITTEN_INITSYNC = BITTENInitSync()
    return BITTEN_INITSYNC

# Convenience functions
def init_user_session(telegram_id: int, user_id: str, tier: str, platforms: List[str], **kwargs) -> Tuple[bool, str, Optional[str]]:
    """Initialize new user session"""
    initsync = get_bitten_initsync()
    success, session_id_or_error, session = initsync.create_session(telegram_id, user_id, tier, platforms, **kwargs)
    if success and session:
        init_success, init_msg = initsync.initialize_user(session.session_id)
        return init_success, init_msg, session.session_id if init_success else None
    return success, session_id_or_error, None

def get_user_session(session_id: str) -> Optional[InitSyncSession]:
    """Get user session by ID"""
    initsync = get_bitten_initsync()
    return initsync.get_session(session_id)

def validate_session_auth(session_id: str, auth_token: str) -> bool:
    """Validate session authentication"""
    session = get_user_session(session_id)
    return session and session.auth_token == auth_token

if __name__ == "__main__":
    print("🎯 BITTEN INITSYNC MODULE - TESTING MODE")
    print("=" * 50)
    
    # Initialize module
    initsync = get_bitten_initsync()
    
    # Test session creation
    success, session_id, session = initsync.create_session(
        telegram_id=123456789,
        user_id="test_user",
        tier="fang",
        platforms=["telegram", "webapp"],
        balance=1000.0,
        persona="scholar"
    )
    
    if success and session:
        print(f"✅ Session created: {session_id}")
        
        # Test initialization
        init_success, init_msg = initsync.initialize_user(session.session_id)
        print(f"🚀 Initialization: {init_success} - {init_msg}")
        
        if init_success:
            # Test session retrieval
            retrieved_session = initsync.get_session(session.session_id)
            print(f"📊 Retrieved session: {retrieved_session.status.value if retrieved_session else 'None'}")
            print(f"🌉 Bridge assigned: {retrieved_session.bridge_id if retrieved_session else 'None'}")
            print(f"🎯 Account ID: {retrieved_session.account_id if retrieved_session else 'None'}")
    else:
        print(f"❌ Session creation failed: {session_id}")
    
    print(f"\n✅ BITTEN InitSync Module operational")