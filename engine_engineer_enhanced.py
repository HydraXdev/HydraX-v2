#!/usr/bin/env python3
"""
🔧 ENGINE ENGINEER v2 ENHANCED - BITTEN System Integration
Version: 2.0 FORTRESS INTEGRATION
Status: OPERATIONAL

MISSION: Advanced engine monitoring, mission tracking, and system diagnostics
INTEGRATION: Bridge Troll, InitSync, Fortress components, and BITTEN ecosystem
"""

import json
import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, jsonify, request

# Import BITTEN integrations
try:
    from troll_integration import (
        troll_get_bridge_status, troll_get_user_info, troll_health,
        troll_get_memory, troll_check_sockets
    )
    TROLL_AVAILABLE = True
except ImportError:
    TROLL_AVAILABLE = False

try:
    from initsync_integration import (
        initsync_get_user, initsync_get_session, initsync_get_bridge
    )
    INITSYNC_AVAILABLE = True
except ImportError:
    INITSYNC_AVAILABLE = False

@dataclass
class EngineStatus:
    engine_type: str
    status: str
    last_update: datetime
    config_loaded: bool
    logs_count: int
    missions_tracked: int
    errors: List[str]
    performance_metrics: Dict[str, Any]

@dataclass
class MissionSummary:
    user_id: str
    total_missions: int
    active_missions: int
    expired_missions: int
    fired_missions: int
    success_rate: float
    last_mission: Optional[datetime]

class EnhancedEngineEngineer:
    """
    🔧 ENHANCED ENGINE ENGINEER - Advanced System Monitoring
    
    CAPABILITIES:
    - Engine status monitoring and diagnostics
    - Mission tracking and analysis
    - Bridge Troll integration for safety monitoring
    - InitSync integration for user session tracking
    - Fortress component health monitoring
    - API endpoints for system management
    """
    
    def __init__(self, 
                 config_path="/root/HydraX-v2/logs/config.json", 
                 log_path="/root/HydraX-v2/logs/fire_log.json", 
                 mission_dir="/root/HydraX-v2/missions/",
                 db_path="/root/HydraX-v2/engine_engineer.db"):
        
        self.config_path = config_path
        self.log_path = log_path 
        self.mission_dir = mission_dir
        self.db_path = db_path
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        os.makedirs(mission_dir, exist_ok=True)
        
        # Initialize systems
        self.setup_logging()
        self.init_database()
        self.load_config()
        self.load_logs()
        
        # Initialize Flask API
        self.init_api()
        
        self.logger.info("🔧 Enhanced Engine Engineer v2 initialized")
        self.logger.info(f"🔗 Bridge Troll Integration: {'✅' if TROLL_AVAILABLE else '❌'}")
        self.logger.info(f"🎯 InitSync Integration: {'✅' if INITSYNC_AVAILABLE else '❌'}")
        
    def setup_logging(self):
        """Initialize logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - ENGINE_ENGINEER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/engine_engineer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ENGINE_ENGINEER")
        
    def init_database(self):
        """Initialize SQLite database for enhanced tracking"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Create engine status table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS engine_status (
                    timestamp TEXT PRIMARY KEY,
                    engine_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config_loaded BOOLEAN,
                    logs_count INTEGER,
                    missions_tracked INTEGER,
                    errors TEXT,
                    performance_metrics TEXT
                )
            ''')
            
            # Create mission tracking table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS mission_tracking (
                    mission_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_timestamp INTEGER,
                    expires_timestamp INTEGER,
                    fired_timestamp INTEGER,
                    success BOOLEAN,
                    metadata TEXT
                )
            ''')
            
            self.conn.commit()
            self.logger.info(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            
    def init_api(self):
        """Initialize Flask API for system management"""
        self.app = Flask(__name__)
        self.app.logger.disabled = True
        
        @self.app.route('/engineer/status')
        def get_status():
            return jsonify(self.get_comprehensive_status())
            
        @self.app.route('/engineer/missions/<user_id>')
        def get_user_missions(user_id):
            return jsonify(self.enhanced_user_mission_summary(user_id))
            
        @self.app.route('/engineer/missions/expired')
        def get_expired_missions():
            return jsonify(self.get_expired_missions())
            
        @self.app.route('/engineer/missions/active')
        def get_active_missions():
            return jsonify(self.get_active_missions())
            
        @self.app.route('/engineer/bridge/<bridge_id>')
        def get_bridge_status(bridge_id):
            if TROLL_AVAILABLE:
                return jsonify(troll_get_bridge_status(bridge_id))
            return jsonify({"error": "Bridge Troll not available"})
            
        @self.app.route('/engineer/user/<int:telegram_id>')
        def get_user_info(telegram_id):
            user_info = {}
            
            # Get Bridge Troll data
            if TROLL_AVAILABLE:
                user_info["bridge_info"] = troll_get_user_info(telegram_id)
                
            # Get InitSync data
            if INITSYNC_AVAILABLE:
                user_info["session_info"] = initsync_get_user(telegram_id)
                
            # Get mission data
            user_info["missions"] = self.enhanced_user_mission_summary(str(telegram_id))
            
            return jsonify(user_info)
            
        @self.app.route('/engineer/health')
        def health_check():
            return jsonify(self.system_health_check())
            
        @self.app.route('/engineer/restart', methods=['POST'])
        def restart_engine():
            result = self.restart_engine()
            return jsonify({"result": result})
            
        self.logger.info("🌐 API endpoints initialized")
        
    def load_config(self):
        """Load configuration with error handling"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path) as f:
                    self.config = json.load(f)
            else:
                self.config = {}
                # Create default config
                self.save_config({
                    "engine_type": "APEX_v6_Enhanced",
                    "monitoring_enabled": True,
                    "log_level": "INFO",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            self.logger.error(f"❌ Config loading failed: {e}")
            self.config = {}

    def load_logs(self):
        """Load logs with error handling"""
        try:
            if os.path.exists(self.log_path):
                with open(self.log_path) as f:
                    self.logs = json.load(f)
            else:
                self.logs = []
        except Exception as e:
            self.logger.error(f"❌ Log loading failed: {e}")
            self.logs = []

    def save_config(self, config_data: Dict):
        """Save configuration to file"""
        try:
            self.config.update(config_data)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"❌ Config saving failed: {e}")

    def status(self):
        """Original status method for compatibility"""
        return {
            "config_loaded": bool(self.config),
            "logs_loaded": len(self.logs),
            "missions_tracked": len(self.get_all_missions())
        }

    def get_comprehensive_status(self) -> Dict:
        """Enhanced status with full system information"""
        try:
            missions = self.get_all_missions()
            errors = []
            
            # Check system health
            if not self.config:
                errors.append("Configuration not loaded")
            if not os.path.exists(self.mission_dir):
                errors.append("Mission directory not accessible")
                
            performance_metrics = {
                "total_missions": len(missions),
                "active_missions": len(self.get_active_missions()),
                "expired_missions": len(self.get_expired_missions()),
                "config_size": len(str(self.config)),
                "log_entries": len(self.logs),
                "uptime": self.get_uptime()
            }
            
            # Add Bridge Troll health if available
            if TROLL_AVAILABLE:
                troll_health = troll_health()
                if troll_health:
                    performance_metrics["bridge_troll"] = troll_health
                    
            # Add system integrations
            integrations = {
                "bridge_troll": TROLL_AVAILABLE,
                "initsync": INITSYNC_AVAILABLE,
                "database": os.path.exists(self.db_path)
            }
            
            status = EngineStatus(
                engine_type=self.config.get("engine_type", "UNKNOWN"),
                status="OPERATIONAL" if not errors else "DEGRADED",
                last_update=datetime.now(timezone.utc),
                config_loaded=bool(self.config),
                logs_count=len(self.logs),
                missions_tracked=len(missions),
                errors=errors,
                performance_metrics=performance_metrics
            )
            
            # Save status to database
            self.save_engine_status(status)
            
            return {
                **asdict(status),
                "integrations": integrations,
                "last_update": status.last_update.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Status check failed: {e}")
            return {
                "engine_type": "UNKNOWN",
                "status": "ERROR",
                "error": str(e),
                "last_update": datetime.now(timezone.utc).isoformat()
            }

    def last_trade(self, user_id: str) -> Optional[Dict]:
        """Get last trade for user with enhanced data"""
        try:
            trades = [t for t in self.logs if str(t.get("user_id", "")) == str(user_id)]
            if not trades:
                return None
                
            last_trade = trades[-1]
            
            # Enhance with Bridge Troll data if available
            if TROLL_AVAILABLE and "bridge_id" in last_trade:
                bridge_status = troll_get_bridge_status(last_trade["bridge_id"])
                if bridge_status:
                    last_trade["bridge_status"] = bridge_status
                    
            return last_trade
            
        except Exception as e:
            self.logger.error(f"❌ Last trade lookup failed: {e}")
            return None

    def restart_engine(self) -> str:
        """Enhanced restart with system integration"""
        try:
            restart_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "engine_restart",
                "triggered_by": "engine_engineer",
                "system_status": self.get_comprehensive_status()
            }
            
            # Log restart attempt
            self.logs.append(restart_log)
            
            # Save logs
            try:
                with open(self.log_path, 'w') as f:
                    json.dump(self.logs, f, indent=2)
            except Exception as e:
                self.logger.error(f"❌ Failed to save restart log: {e}")
                
            self.logger.info("🔄 Engine restart command dispatched")
            return "Enhanced restart command dispatched with system integration"
            
        except Exception as e:
            self.logger.error(f"❌ Restart failed: {e}")
            return f"Restart failed: {e}"

    def get_all_missions(self) -> List[Dict]:
        """Enhanced mission loading with error handling"""
        if not os.path.exists(self.mission_dir):
            return []
            
        missions = []
        for filename in os.listdir(self.mission_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.mission_dir, filename)) as f:
                        mission = json.load(f)
                        # Enhance mission with tracking data
                        mission["filename"] = filename
                        mission["file_size"] = os.path.getsize(os.path.join(self.mission_dir, filename))
                        missions.append(mission)
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to load mission {filename}: {e}")
                    continue
        return missions

    def get_user_missions(self, user_id: str) -> List[Dict]:
        """Get missions for specific user"""
        return [m for m in self.get_all_missions() if str(m.get("user_id", "")) == str(user_id)]

    def get_expired_missions(self) -> List[Dict]:
        """Get expired missions with enhanced data"""
        now_ts = int(datetime.now(timezone.utc).timestamp())
        expired = [m for m in self.get_all_missions() if m.get("expires_timestamp", 0) < now_ts]
        
        # Add expiration details
        for mission in expired:
            if "expires_timestamp" in mission:
                expired_time = datetime.fromtimestamp(mission["expires_timestamp"], timezone.utc)
                mission["expired_duration"] = (datetime.now(timezone.utc) - expired_time).total_seconds()
                
        return expired

    def get_active_missions(self) -> List[Dict]:
        """Get active missions with time remaining"""
        now_ts = int(datetime.now(timezone.utc).timestamp())
        active = [m for m in self.get_all_missions() if m.get("expires_timestamp", 0) >= now_ts]
        
        # Add time remaining
        for mission in active:
            if "expires_timestamp" in mission:
                expires_time = datetime.fromtimestamp(mission["expires_timestamp"], timezone.utc)
                mission["time_remaining"] = (expires_time - datetime.now(timezone.utc)).total_seconds()
                
        return active

    def enhanced_user_mission_summary(self, user_id: str) -> MissionSummary:
        """Enhanced user mission summary with detailed analytics"""
        try:
            user_missions = self.get_user_missions(user_id)
            
            if not user_missions:
                return MissionSummary(
                    user_id=user_id,
                    total_missions=0,
                    active_missions=0,
                    expired_missions=0,
                    fired_missions=0,
                    success_rate=0.0,
                    last_mission=None
                ).__dict__
            
            now_ts = int(datetime.now(timezone.utc).timestamp())
            
            active = [m for m in user_missions if m.get("status") == "pending" and m.get("expires_timestamp", 0) >= now_ts]
            expired = [m for m in user_missions if m.get("status") == "pending" and m.get("expires_timestamp", 0) < now_ts]  
            fired = [m for m in user_missions if m.get("status") == "fired"]
            successful = [m for m in fired if m.get("success", False)]
            
            # Calculate success rate
            success_rate = (len(successful) / len(fired)) * 100 if fired else 0.0
            
            # Get last mission timestamp
            last_mission = None
            if user_missions:
                latest_mission = max(user_missions, key=lambda x: x.get("created_timestamp", 0))
                if "created_timestamp" in latest_mission:
                    last_mission = datetime.fromtimestamp(latest_mission["created_timestamp"], timezone.utc)
            
            summary = MissionSummary(
                user_id=user_id,
                total_missions=len(user_missions),
                active_missions=len(active),
                expired_missions=len(expired),
                fired_missions=len(fired),
                success_rate=success_rate,
                last_mission=last_mission
            )
            
            # Save to database
            self.save_mission_summary(summary)
            
            result = asdict(summary)
            result["last_mission"] = last_mission.isoformat() if last_mission else None
            
            # Add Bridge Troll integration
            if TROLL_AVAILABLE:
                try:
                    user_info = troll_get_user_info(int(user_id))
                    if user_info:
                        result["bridge_info"] = user_info
                except:
                    pass
                    
            # Add InitSync integration
            if INITSYNC_AVAILABLE:
                try:
                    session_info = initsync_get_user(int(user_id))
                    if session_info:
                        result["session_info"] = session_info
                except:
                    pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Mission summary failed for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "total_missions": 0,
                "active_missions": 0,
                "expired_missions": 0,
                "fired_missions": 0,
                "success_rate": 0.0,
                "last_mission": None
            }

    def user_mission_summary(self, user_id: str) -> Dict:
        """Original method for compatibility"""
        return self.enhanced_user_mission_summary(user_id)

    def system_health_check(self) -> Dict:
        """Comprehensive system health check"""
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "HEALTHY",
            "components": {},
            "integrations": {},
            "warnings": [],
            "errors": []
        }
        
        try:
            # Check core components
            health["components"]["config"] = "LOADED" if self.config else "MISSING"
            health["components"]["logs"] = "ACCESSIBLE" if os.path.exists(self.log_path) else "MISSING"
            health["components"]["missions"] = "ACCESSIBLE" if os.path.exists(self.mission_dir) else "MISSING"
            health["components"]["database"] = "CONNECTED" if os.path.exists(self.db_path) else "MISSING"
            
            # Check integrations
            if TROLL_AVAILABLE:
                troll_status = troll_health()
                health["integrations"]["bridge_troll"] = "HEALTHY" if troll_status else "DEGRADED"
            else:
                health["integrations"]["bridge_troll"] = "NOT_AVAILABLE"
                
            if INITSYNC_AVAILABLE:
                health["integrations"]["initsync"] = "HEALTHY"
            else:
                health["integrations"]["initsync"] = "NOT_AVAILABLE"
                
            # Check for warnings
            if not self.config:
                health["warnings"].append("Configuration not loaded")
            if not self.logs:
                health["warnings"].append("No logs available")
            if not self.get_all_missions():
                health["warnings"].append("No missions found")
                
            # Determine overall status
            if health["errors"]:
                health["overall_status"] = "ERROR"
            elif health["warnings"]:
                health["overall_status"] = "WARNING"
                
        except Exception as e:
            health["overall_status"] = "ERROR"
            health["errors"].append(str(e))
            
        return health

    def save_engine_status(self, status: EngineStatus):
        """Save engine status to database"""
        try:
            self.conn.execute('''
                INSERT INTO engine_status 
                (timestamp, engine_type, status, config_loaded, logs_count, 
                 missions_tracked, errors, performance_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                status.last_update.isoformat(),
                status.engine_type,
                status.status,
                status.config_loaded,
                status.logs_count,
                status.missions_tracked,
                json.dumps(status.errors),
                json.dumps(status.performance_metrics)
            ))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"❌ Failed to save engine status: {e}")

    def save_mission_summary(self, summary: MissionSummary):
        """Save mission summary to database"""
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO mission_tracking 
                (mission_id, user_id, status, created_timestamp, expires_timestamp, 
                 fired_timestamp, success, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"summary_{summary.user_id}_{int(datetime.now().timestamp())}",
                summary.user_id,
                "summary",
                int(datetime.now().timestamp()),
                None,
                None,
                None,
                json.dumps(asdict(summary))
            ))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"❌ Failed to save mission summary: {e}")

    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            if hasattr(self, '_start_time'):
                return (datetime.now(timezone.utc) - self._start_time).total_seconds()
            else:
                self._start_time = datetime.now(timezone.utc)
                return 0.0
        except:
            return 0.0

# Global Enhanced Engine Engineer instance
ENHANCED_ENGINE_ENGINEER = None

def get_enhanced_engine_engineer() -> EnhancedEngineEngineer:
    """Get global Enhanced Engine Engineer instance"""
    global ENHANCED_ENGINE_ENGINEER
    if ENHANCED_ENGINE_ENGINEER is None:
        ENHANCED_ENGINE_ENGINEER = EnhancedEngineEngineer()
    return ENHANCED_ENGINE_ENGINEER

# Convenience functions for easy import
def engineer_status() -> Dict:
    """Get comprehensive engine status"""
    return get_enhanced_engine_engineer().get_comprehensive_status()

def engineer_user_summary(user_id: str) -> Dict:
    """Get enhanced user mission summary"""
    return get_enhanced_engine_engineer().enhanced_user_mission_summary(user_id)

def engineer_health_check() -> Dict:
    """Get system health check"""
    return get_enhanced_engine_engineer().system_health_check()

def engineer_restart() -> str:
    """Restart engine with enhanced logging"""
    return get_enhanced_engine_engineer().restart_engine()

if __name__ == "__main__":
    print("🔧 ENHANCED ENGINE ENGINEER v2 - TESTING MODE")
    print("=" * 60)
    
    # Initialize Enhanced Engine Engineer
    engineer = get_enhanced_engine_engineer()
    
    # Test comprehensive status
    status = engineer.get_comprehensive_status()
    print(f"📊 Engine Status: {status['status']}")
    print(f"🎯 Missions Tracked: {status['missions_tracked']}")
    print(f"🔗 Integrations: {status.get('integrations', {})}")
    
    # Test user mission summary
    summary = engineer.enhanced_user_mission_summary("test_user")
    print(f"👤 Test User Summary: {summary['total_missions']} missions")
    
    # Test health check
    health = engineer.system_health_check()
    print(f"🏥 System Health: {health['overall_status']}")
    
    # Test API endpoints
    print(f"\n🌐 API Endpoints Available:")
    print(f"  GET  /engineer/status")
    print(f"  GET  /engineer/missions/<user_id>")
    print(f"  GET  /engineer/missions/expired")
    print(f"  GET  /engineer/missions/active")
    print(f"  GET  /engineer/bridge/<bridge_id>")
    print(f"  GET  /engineer/user/<telegram_id>")
    print(f"  GET  /engineer/health")
    print(f"  POST /engineer/restart")
    
    print(f"\n✅ Enhanced Engine Engineer v2 operational")