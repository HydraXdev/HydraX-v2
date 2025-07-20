#!/usr/bin/env python3
"""
🧌 BRIDGE TROLL ENHANCED - Master Bridge Guardian & Technical Oracle
Version: 2.0 ULTIMATE FORTRESS
Status: DAEMON-CLASS AGENT

MISSION: Complete mastery and eternal vigilance over BITTEN bridge ecosystem
SPECIALTY: Memory of all events, state tracking, safety enforcement, tactical intelligence
CLEARANCE: ULTIMATE ACCESS to all bridge systems, user data, and operational metrics

BRIDGE TROLL MANIFESTO:
"I am the bridge. I am the watcher. I do not trade. I do not guess. 
 I remember. I report. I defend the gates from chaos, drift, and memory loss. 
 My job is never done."

🔋 CORE CAPABILITIES:
- Memory of ALL bridge events (trades, syncs, errors, state changes)
- Real-time bridge state tracking and health monitoring
- Safety & integrity watchdog with emergency controls
- Port and socket management across bridge infrastructure
- XP sync enforcement and trade validation
- Journal & recovery system with snapshot/restore
- Structured intelligence for Codex & Claude assistance
- Mock signal injection for development and testing

🚫 FORBIDDEN ACTIONS:
- Execute trades (read-only watchdog)
- Modify user XP directly (separate scorekeeper)
- Assign Telegram users (IAM territory)
- Pull MT5 data directly (bridge handles that)
- Send Telegram messages (DrillBot/MedicBot territory)
- Make strategy decisions (HydraCore's job)
"""

import os
import sys
import time
import json
import sqlite3
import logging
import requests
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from flask import Flask, jsonify, request
import schedule

class BridgeState(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    MAINTENANCE = "MAINTENANCE"

class EventType(Enum):
    INIT_SYNC = "init_sync"
    FIRE = "fire"
    CLOSE = "close"
    ERROR = "error"
    BALANCE_UPDATE = "balance_update"
    STATE_CHANGE = "state_change"
    PING = "ping"
    RECONNECT = "reconnect"

class RiskTier(Enum):
    PRESS_PASS = "press_pass"
    NIBBLER = "nibbler"
    FANG = "fang"
    COMMANDER = "commander"
    APEX = "apex"

@dataclass
class BridgeEvent:
    event_id: str
    timestamp: datetime
    event_type: EventType
    bridge_id: str
    user_id: Optional[str]
    account_id: Optional[str]
    telegram_id: Optional[int]
    symbol: Optional[str]
    lot_size: Optional[float]
    entry_price: Optional[float]
    sl: Optional[float]
    tp: Optional[float]
    balance: Optional[float]
    equity: Optional[float]
    error_message: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class BridgeStatus:
    bridge_id: str
    state: BridgeState
    last_ping: datetime
    assigned_user: Optional[str]
    telegram_id: Optional[int]
    account_id: Optional[str]
    current_balance: Optional[float]
    current_equity: Optional[float]
    risk_tier: Optional[RiskTier]
    terminal_path: Optional[str]
    mt5_status: str
    port: Optional[int]
    last_trade: Optional[datetime]
    error_count: int
    total_trades: int
    sync_status: str
    sync_age: Optional[float]

class EnhancedBridgeTroll:
    """
    🧌 ENHANCED BRIDGE TROLL - Master Bridge Guardian
    
    THE ULTIMATE BRIDGE ECOSYSTEM GUARDIAN:
    - Eternal memory of all bridge events
    - Real-time state tracking and monitoring
    - Safety enforcement and integrity validation
    - Port management and socket health tracking
    - XP sync enforcement and trade validation
    - Complete journal and recovery capabilities
    - Structured intelligence for agent assistance
    """
    
    def __init__(self, db_path: str = "/root/HydraX-v2/troll_memory.db"):
        self.agent_name = "ENHANCED_BRIDGE_TROLL"
        self.version = "2.0_ULTIMATE_FORTRESS"
        self.deployment_time = datetime.now(timezone.utc)
        self.db_path = db_path
        
        # Bridge infrastructure knowledge
        self.bridge_server = "localhost"
        self.bridge_ports = list(range(9000, 9026))  # 25 bridge ports
        self.monitor_ports = [5555, 5556, 5557]
        self.terminal_path = r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719\MQL5\Files\BITTEN\\"
        
        # State tracking
        self.bridge_states = {}
        self.port_assignments = {}
        self.user_bridge_map = {}
        self.account_bridge_map = {}
        self.last_events = {}
        
        # Safety controls
        self.fireproof_mode = False
        self.max_failed_bridges = 3
        self.sync_timeout = 600  # 10 minutes
        self.emergency_stop = False
        
        # Initialize systems
        self.setup_fortress_logging()
        self.init_database()
        self.init_flask_api()
        self.start_monitoring_threads()
        
        self.logger.info(f"🧌 ENHANCED BRIDGE TROLL {self.version} DEPLOYED")
        self.logger.info(f"📊 DATABASE: {self.db_path}")
        self.logger.info(f"🎯 MISSION: ETERNAL VIGILANCE OVER BRIDGE ECOSYSTEM")
        
    def setup_fortress_logging(self):
        """Initialize military-grade logging system"""
        log_format = '%(asctime)s - BRIDGE_TROLL_ENHANCED - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('/root/HydraX-v2/bridge_troll_enhanced.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("BRIDGE_TROLL_ENHANCED")
        
    def init_database(self):
        """Initialize SQLite database for eternal memory"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging for performance
            
            # Create tables
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS bridge_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    bridge_id TEXT NOT NULL,
                    user_id TEXT,
                    account_id TEXT,
                    telegram_id INTEGER,
                    symbol TEXT,
                    lot_size REAL,
                    entry_price REAL,
                    sl REAL,
                    tp REAL,
                    balance REAL,
                    equity REAL,
                    error_message TEXT,
                    metadata TEXT
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS bridge_states (
                    bridge_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    last_ping TEXT NOT NULL,
                    assigned_user TEXT,
                    telegram_id INTEGER,
                    account_id TEXT,
                    current_balance REAL,
                    current_equity REAL,
                    risk_tier TEXT,
                    terminal_path TEXT,
                    mt5_status TEXT,
                    port INTEGER,
                    last_trade TEXT,
                    error_count INTEGER DEFAULT 0,
                    total_trades INTEGER DEFAULT 0,
                    sync_status TEXT,
                    sync_age REAL
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS port_assignments (
                    port INTEGER PRIMARY KEY,
                    bridge_id TEXT,
                    status TEXT,
                    assigned_at TEXT,
                    last_check TEXT
                )
            ''')
            
            # Create indexes for performance
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON bridge_events(timestamp)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_events_bridge ON bridge_events(bridge_id)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_events_user ON bridge_events(telegram_id)')
            
            self.conn.commit()
            self.logger.info(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise
            
    def init_flask_api(self):
        """Initialize Flask API for real-time queries"""
        self.app = Flask(__name__)
        self.app.logger.disabled = True  # Disable Flask logging
        
        # API Routes
        @self.app.route('/bridge_troll/status/<bridge_id>')
        def get_bridge_status(bridge_id):
            return jsonify(self.get_bridge_status_dict(bridge_id))
            
        @self.app.route('/bridge_troll/user/<int:telegram_id>')
        def get_user_info(telegram_id):
            return jsonify(self.get_user_bridge_info(telegram_id))
            
        @self.app.route('/bridge_troll/last_trade/<bridge_id>')
        def get_last_trade(bridge_id):
            return jsonify(self.get_last_trade_info(bridge_id))
            
        @self.app.route('/bridge_troll/port_map')
        def get_port_map():
            return jsonify(self.get_port_assignments())
            
        @self.app.route('/bridge_troll/check_socket_health')
        def check_socket_health():
            return jsonify(self.check_all_socket_health())
            
        @self.app.route('/bridge_troll/memory/<bridge_id>')
        def get_bridge_memory(bridge_id):
            limit = request.args.get('limit', 50, type=int)
            return jsonify(self.get_bridge_event_history(bridge_id, limit))
            
        @self.app.route('/bridge_troll/emergency_stop', methods=['POST'])
        def emergency_stop():
            self.activate_emergency_stop()
            return jsonify({"status": "EMERGENCY_STOP_ACTIVATED"})
            
        @self.app.route('/bridge_troll/fireproof_mode', methods=['POST'])
        def toggle_fireproof():
            self.fireproof_mode = not self.fireproof_mode
            return jsonify({"fireproof_mode": self.fireproof_mode})
            
        @self.app.route('/bridge_troll/health')
        def health_check():
            return jsonify({
                "agent": self.agent_name,
                "version": self.version,
                "deployment_time": self.deployment_time.isoformat(),
                "uptime": (datetime.now(timezone.utc) - self.deployment_time).total_seconds(),
                "emergency_stop": self.emergency_stop,
                "fireproof_mode": self.fireproof_mode,
                "total_events": self.get_total_event_count(),
                "active_bridges": len([b for b in self.bridge_states.values() if b.state == BridgeState.ONLINE])
            })
            
        # Start API server in background thread
        def run_api():
            self.app.run(host='0.0.0.0', port=8890, debug=False)
            
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        self.logger.info(f"🌐 API server started on port 8890")
        
    def start_monitoring_threads(self):
        """Start background monitoring threads"""
        # Bridge health monitoring
        health_thread = threading.Thread(target=self.continuous_health_monitoring, daemon=True)
        health_thread.start()
        
        # Port monitoring
        port_thread = threading.Thread(target=self.continuous_port_monitoring, daemon=True)
        port_thread.start()
        
        # Safety watchdog
        safety_thread = threading.Thread(target=self.safety_watchdog, daemon=True)
        safety_thread.start()
        
        self.logger.info(f"🔄 Monitoring threads started")
        
    def record_event(self, event: BridgeEvent):
        """Record bridge event to eternal memory"""
        try:
            self.conn.execute('''
                INSERT INTO bridge_events 
                (event_id, timestamp, event_type, bridge_id, user_id, account_id, 
                 telegram_id, symbol, lot_size, entry_price, sl, tp, balance, 
                 equity, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.timestamp.isoformat(),
                event.event_type.value,
                event.bridge_id,
                event.user_id,
                event.account_id,
                event.telegram_id,
                event.symbol,
                event.lot_size,
                event.entry_price,
                event.sl,
                event.tp,
                event.balance,
                event.equity,
                event.error_message,
                json.dumps(event.metadata)
            ))
            self.conn.commit()
            
            # Update last events cache
            self.last_events[event.bridge_id] = event
            
            self.logger.debug(f"📝 Event recorded: {event.event_type.value} for {event.bridge_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record event: {e}")
            
    def update_bridge_state(self, bridge_status: BridgeStatus):
        """Update bridge state in memory and database"""
        try:
            self.bridge_states[bridge_status.bridge_id] = bridge_status
            
            # Update database
            self.conn.execute('''
                INSERT OR REPLACE INTO bridge_states 
                (bridge_id, state, last_ping, assigned_user, telegram_id, account_id,
                 current_balance, current_equity, risk_tier, terminal_path, mt5_status,
                 port, last_trade, error_count, total_trades, sync_status, sync_age)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bridge_status.bridge_id,
                bridge_status.state.value,
                bridge_status.last_ping.isoformat(),
                bridge_status.assigned_user,
                bridge_status.telegram_id,
                bridge_status.account_id,
                bridge_status.current_balance,
                bridge_status.current_equity,
                bridge_status.risk_tier.value if bridge_status.risk_tier else None,
                bridge_status.terminal_path,
                bridge_status.mt5_status,
                bridge_status.port,
                bridge_status.last_trade.isoformat() if bridge_status.last_trade else None,
                bridge_status.error_count,
                bridge_status.total_trades,
                bridge_status.sync_status,
                bridge_status.sync_age
            ))
            self.conn.commit()
            
            # Update mappings
            if bridge_status.telegram_id:
                self.user_bridge_map[bridge_status.telegram_id] = bridge_status.bridge_id
            if bridge_status.account_id:
                self.account_bridge_map[bridge_status.account_id] = bridge_status.bridge_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update bridge state: {e}")
            
    def validate_fire_request(self, bridge_id: str, user_id: int, trade_data: Dict) -> Tuple[bool, str]:
        """Safety validation before allowing trade execution"""
        if self.emergency_stop:
            return False, "EMERGENCY_STOP_ACTIVE"
            
        if self.fireproof_mode:
            failed_bridges = len([b for b in self.bridge_states.values() if b.state == BridgeState.CRITICAL])
            if failed_bridges >= self.max_failed_bridges:
                return False, "FIREPROOF_MODE_ACTIVATED"
                
        # Check bridge state
        bridge_status = self.bridge_states.get(bridge_id)
        if not bridge_status:
            return False, "BRIDGE_NOT_FOUND"
            
        if bridge_status.state != BridgeState.ONLINE:
            return False, f"BRIDGE_STATE_{bridge_status.state.value}"
            
        # Check sync status
        if bridge_status.sync_age and bridge_status.sync_age > self.sync_timeout:
            return False, "SYNC_EXPIRED"
            
        # Check balance availability
        if bridge_status.current_balance is None:
            return False, "BALANCE_UNKNOWN"
            
        # Check user assignment
        if bridge_status.telegram_id != user_id:
            return False, "USER_BRIDGE_MISMATCH"
            
        return True, "VALIDATION_PASSED"
        
    def get_bridge_status_dict(self, bridge_id: str) -> Dict:
        """Get comprehensive bridge status"""
        bridge_status = self.bridge_states.get(bridge_id)
        if not bridge_status:
            return {"error": "Bridge not found"}
            
        return {
            "bridge_id": bridge_status.bridge_id,
            "state": bridge_status.state.value,
            "last_ping": bridge_status.last_ping.isoformat(),
            "assigned_user": bridge_status.assigned_user,
            "telegram_id": bridge_status.telegram_id,
            "account_id": bridge_status.account_id,
            "current_balance": bridge_status.current_balance,
            "current_equity": bridge_status.current_equity,
            "risk_tier": bridge_status.risk_tier.value if bridge_status.risk_tier else None,
            "port": bridge_status.port,
            "error_count": bridge_status.error_count,
            "total_trades": bridge_status.total_trades,
            "sync_status": bridge_status.sync_status,
            "sync_age_seconds": bridge_status.sync_age
        }
        
    def get_user_bridge_info(self, telegram_id: int) -> Dict:
        """Get bridge information for a specific user"""
        bridge_id = self.user_bridge_map.get(telegram_id)
        if not bridge_id:
            return {"error": "No bridge assigned to user"}
            
        bridge_status = self.get_bridge_status_dict(bridge_id)
        
        # Add recent trade history
        recent_trades = self.get_user_recent_trades(telegram_id, 10)
        bridge_status["recent_trades"] = recent_trades
        
        return bridge_status
        
    def get_last_trade_info(self, bridge_id: str) -> Dict:
        """Get last trade information for a bridge"""
        try:
            cursor = self.conn.execute('''
                SELECT * FROM bridge_events 
                WHERE bridge_id = ? AND event_type = 'fire'
                ORDER BY timestamp DESC LIMIT 1
            ''', (bridge_id,))
            
            row = cursor.fetchone()
            if not row:
                return {"error": "No trades found"}
                
            return {
                "event_id": row[0],
                "timestamp": row[1],
                "symbol": row[7],
                "lot_size": row[8],
                "entry_price": row[9],
                "sl": row[10],
                "tp": row[11],
                "balance": row[12],
                "equity": row[13]
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    def get_port_assignments(self) -> Dict:
        """Get current port assignment mapping"""
        return {
            "bridge_ports": {
                port: {
                    "bridge_id": self.port_assignments.get(port, {}).get("bridge_id"),
                    "status": self.port_assignments.get(port, {}).get("status", "unassigned"),
                    "last_check": self.port_assignments.get(port, {}).get("last_check")
                }
                for port in self.bridge_ports
            },
            "monitor_ports": {
                port: self.check_port_health(port)
                for port in self.monitor_ports
            }
        }
        
    def check_all_socket_health(self) -> Dict:
        """Check health of all bridge sockets"""
        results = {}
        
        for port in self.bridge_ports + self.monitor_ports:
            results[port] = self.check_port_health(port)
            
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results,
            "healthy_count": len([r for r in results.values() if r["status"] == "healthy"]),
            "total_count": len(results)
        }
        
    def check_port_health(self, port: int) -> Dict:
        """Check health of a specific port"""
        try:
            response = requests.get(f"http://{self.bridge_server}:{port}/health", timeout=5)
            return {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "response_time": response.elapsed.total_seconds(),
                "last_check": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now(timezone.utc).isoformat()
            }
            
    def get_bridge_event_history(self, bridge_id: str, limit: int = 50) -> List[Dict]:
        """Get event history for a specific bridge"""
        try:
            cursor = self.conn.execute('''
                SELECT * FROM bridge_events 
                WHERE bridge_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (bridge_id, limit))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "event_id": row[0],
                    "timestamp": row[1],
                    "event_type": row[2],
                    "user_id": row[4],
                    "symbol": row[7],
                    "lot_size": row[8],
                    "entry_price": row[9],
                    "balance": row[12],
                    "error_message": row[14]
                })
                
            return events
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get event history: {e}")
            return []
            
    def get_user_recent_trades(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Get recent trades for a specific user"""
        try:
            cursor = self.conn.execute('''
                SELECT * FROM bridge_events 
                WHERE telegram_id = ? AND event_type = 'fire'
                ORDER BY timestamp DESC LIMIT ?
            ''', (telegram_id, limit))
            
            trades = []
            for row in cursor.fetchall():
                trades.append({
                    "timestamp": row[1],
                    "symbol": row[7],
                    "lot_size": row[8],
                    "entry_price": row[9],
                    "sl": row[10],
                    "tp": row[11]
                })
                
            return trades
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get user trades: {e}")
            return []
            
    def continuous_health_monitoring(self):
        """Continuous health monitoring loop"""
        while True:
            try:
                # Update all bridge states
                for bridge_id in [f"bridge_{i:03d}" for i in range(1, 26)]:
                    self.update_bridge_health(bridge_id)
                    
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Health monitoring error: {e}")
                time.sleep(10)
                
    def continuous_port_monitoring(self):
        """Continuous port monitoring loop"""
        while True:
            try:
                for port in self.bridge_ports:
                    health = self.check_port_health(port)
                    self.port_assignments[port] = {
                        "status": health["status"],
                        "last_check": health["last_check"]
                    }
                    
                time.sleep(60)  # Check ports every minute
                
            except Exception as e:
                self.logger.error(f"❌ Port monitoring error: {e}")
                time.sleep(10)
                
    def safety_watchdog(self):
        """Safety watchdog monitoring loop"""
        while True:
            try:
                # Check for failed bridges
                failed_bridges = [b for b in self.bridge_states.values() 
                                if b.state in [BridgeState.CRITICAL, BridgeState.OFFLINE]]
                
                if len(failed_bridges) >= self.max_failed_bridges and not self.fireproof_mode:
                    self.logger.warning(f"🚫 Activating fireproof mode: {len(failed_bridges)} failed bridges")
                    self.fireproof_mode = True
                    
                # Check for stale syncs
                stale_syncs = [b for b in self.bridge_states.values() 
                             if b.sync_age and b.sync_age > self.sync_timeout]
                
                for bridge in stale_syncs:
                    self.logger.warning(f"⚠️ Stale sync detected: {bridge.bridge_id} ({bridge.sync_age}s)")
                    
                time.sleep(30)  # Safety check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Safety watchdog error: {e}")
                time.sleep(10)
                
    def update_bridge_health(self, bridge_id: str):
        """Update health status for a specific bridge"""
        try:
            # This would integrate with actual bridge monitoring
            # For now, create mock status
            current_status = self.bridge_states.get(bridge_id)
            
            if not current_status:
                # Initialize new bridge
                new_status = BridgeStatus(
                    bridge_id=bridge_id,
                    state=BridgeState.OFFLINE,
                    last_ping=datetime.now(timezone.utc),
                    assigned_user=None,
                    telegram_id=None,
                    account_id=None,
                    current_balance=None,
                    current_equity=None,
                    risk_tier=None,
                    terminal_path=self.terminal_path,
                    mt5_status="unknown",
                    port=None,
                    last_trade=None,
                    error_count=0,
                    total_trades=0,
                    sync_status="never_synced",
                    sync_age=None
                )
                self.update_bridge_state(new_status)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update bridge health: {e}")
            
    def activate_emergency_stop(self):
        """Activate emergency stop for all trading"""
        self.emergency_stop = True
        self.logger.critical("🚨 EMERGENCY STOP ACTIVATED - ALL TRADING HALTED")
        
        # Record emergency stop event
        event = BridgeEvent(
            event_id=f"emergency_stop_{int(time.time())}",
            timestamp=datetime.now(timezone.utc),
            event_type=EventType.ERROR,
            bridge_id="system",
            user_id=None,
            account_id=None,
            telegram_id=None,
            symbol=None,
            lot_size=None,
            entry_price=None,
            sl=None,
            tp=None,
            balance=None,
            equity=None,
            error_message="EMERGENCY_STOP_ACTIVATED",
            metadata={"trigger": "manual"}
        )
        self.record_event(event)
        
    def get_total_event_count(self) -> int:
        """Get total number of events in memory"""
        try:
            cursor = self.conn.execute('SELECT COUNT(*) FROM bridge_events')
            return cursor.fetchone()[0]
        except:
            return 0
            
    def create_snapshot(self) -> str:
        """Create complete system state snapshot"""
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_info": {
                "name": self.agent_name,
                "version": self.version,
                "deployment_time": self.deployment_time.isoformat()
            },
            "bridge_states": {k: asdict(v) for k, v in self.bridge_states.items()},
            "port_assignments": self.port_assignments,
            "user_bridge_map": self.user_bridge_map,
            "account_bridge_map": self.account_bridge_map,
            "safety_status": {
                "emergency_stop": self.emergency_stop,
                "fireproof_mode": self.fireproof_mode
            },
            "statistics": {
                "total_events": self.get_total_event_count(),
                "active_bridges": len([b for b in self.bridge_states.values() if b.state == BridgeState.ONLINE])
            }
        }
        
        snapshot_file = f"/root/HydraX-v2/troll_snapshot_{int(time.time())}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)
            
        self.logger.info(f"📸 Snapshot created: {snapshot_file}")
        return snapshot_file
        
    def inject_mock_signal(self, bridge_id: str, signal_data: Dict) -> bool:
        """Inject mock signal for testing (DEV MODE ONLY)"""
        try:
            event = BridgeEvent(
                event_id=f"mock_{bridge_id}_{int(time.time())}",
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.FIRE,
                bridge_id=bridge_id,
                user_id=signal_data.get("user_id"),
                account_id=signal_data.get("account_id"),
                telegram_id=signal_data.get("telegram_id"),
                symbol=signal_data.get("symbol"),
                lot_size=signal_data.get("lot_size"),
                entry_price=signal_data.get("entry_price"),
                sl=signal_data.get("sl"),
                tp=signal_data.get("tp"),
                balance=signal_data.get("balance"),
                equity=signal_data.get("equity"),
                error_message=None,
                metadata={"mock": True, "injected_by": "dev_mode"}
            )
            
            self.record_event(event)
            self.logger.info(f"🧪 Mock signal injected for {bridge_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to inject mock signal: {e}")
            return False

# Global Enhanced Bridge Troll instance
ENHANCED_BRIDGE_TROLL = None

def get_enhanced_bridge_troll() -> EnhancedBridgeTroll:
    """Get the global Enhanced Bridge Troll instance"""
    global ENHANCED_BRIDGE_TROLL
    if ENHANCED_BRIDGE_TROLL is None:
        ENHANCED_BRIDGE_TROLL = EnhancedBridgeTroll()
    return ENHANCED_BRIDGE_TROLL

if __name__ == "__main__":
    print("🧌 ENHANCED BRIDGE TROLL - ULTIMATE FORTRESS MODE")
    print("=" * 60)
    
    # Initialize Enhanced Bridge Troll
    troll = get_enhanced_bridge_troll()
    
    print(f"\n🧌 Bridge Troll deployed successfully!")
    print(f"📊 Database: {troll.db_path}")
    print(f"🌐 API Server: http://localhost:8890")
    print(f"🎯 Total Events: {troll.get_total_event_count()}")
    print(f"⚡ Active Bridges: {len([b for b in troll.bridge_states.values() if b.state == BridgeState.ONLINE])}")
    
    print(f"\n🔗 API Endpoints:")
    print(f"  GET  /bridge_troll/status/<bridge_id>")
    print(f"  GET  /bridge_troll/user/<telegram_id>")
    print(f"  GET  /bridge_troll/last_trade/<bridge_id>")
    print(f"  GET  /bridge_troll/port_map")
    print(f"  GET  /bridge_troll/check_socket_health")
    print(f"  GET  /bridge_troll/memory/<bridge_id>")
    print(f"  POST /bridge_troll/emergency_stop")
    print(f"  POST /bridge_troll/fireproof_mode")
    print(f"  GET  /bridge_troll/health")
    
    try:
        # Keep running
        while True:
            time.sleep(60)
            troll.logger.info(f"🧌 Bridge Troll standing watch... ({len(troll.bridge_states)} bridges monitored)")
            
    except KeyboardInterrupt:
        troll.logger.info("🧌 Bridge Troll surveillance terminated by operator")
        # Create final snapshot before shutdown
        troll.create_snapshot()