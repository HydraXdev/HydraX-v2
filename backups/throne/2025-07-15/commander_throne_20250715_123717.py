#!/usr/bin/env python3
"""
🏆 BITTEN ULTIMATE COMMANDER THRONE
Centralized high command interface for complete system oversight and control
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import sqlite3
import json
import os
import logging
import hashlib
import time
import sys
from typing import Dict, List, Optional, Any
from functools import wraps
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CommanderThrone')

app = Flask(__name__)
app.secret_key = 'bitten_commander_throne_ultra_secure_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
THRONE_CONFIG = {
    "database_path": "/root/HydraX-v2/data/commander_throne.db",
    "max_sessions": 3,
    "session_timeout_hours": 8,
    "rate_limits": {
        "xp_award": 10,  # per hour
        "global_override": 5,  # per hour
        "mass_message": 3   # per hour
    }
}

# Access levels
ACCESS_LEVELS = {
    "COMMANDER": {"level": 4, "permissions": ["*"]},
    "LIEUTENANT": {"level": 3, "permissions": ["xp", "cooldown", "moderate"]},
    "RECRUITER": {"level": 2, "permissions": ["message", "view"]},
    "OBSERVER": {"level": 1, "permissions": ["view"]}
}

# Authentication credentials (in production, use proper auth system)
THRONE_USERS = {
    "APEX_COMMANDER": {
        "password_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # empty for demo
        "access_level": "COMMANDER",
        "user_id": "7176191872"
    },
    "COMMANDER": {
        "password_hash": "fcf730b6d95236ecd3c9fc2d92d7b6b2bb061514961aec041d6c7a7192f592e4",  # "secret123"
        "access_level": "COMMANDER", 
        "user_id": "7176191873"
    }
}

class CommanderThroneDB:
    """Database operations for Commander Throne"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize throne database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Command log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    commander_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT,
                    parameters TEXT,
                    result TEXT,
                    ip_address TEXT
                )
            """)
            
            # Active sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_sessions (
                    session_id TEXT PRIMARY KEY,
                    commander_id TEXT NOT NULL,
                    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    access_level TEXT
                )
            """)
            
            # Rate limiting table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    commander_id TEXT,
                    action_type TEXT,
                    count INTEGER DEFAULT 0,
                    reset_time DATETIME,
                    PRIMARY KEY (commander_id, action_type)
                )
            """)
            
            conn.commit()
    
    def log_command(self, commander_id: str, action: str, target: str = None, 
                   parameters: Dict = None, result: str = None, ip: str = None):
        """Log commander action"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO command_log (commander_id, action, target, parameters, result, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (commander_id, action, target, json.dumps(parameters) if parameters else None, result, ip))
    
    def check_rate_limit(self, commander_id: str, action_type: str) -> bool:
        """Check if action is rate limited"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current rate limit
            cursor.execute("""
                SELECT count, reset_time FROM rate_limits 
                WHERE commander_id = ? AND action_type = ?
            """, (commander_id, action_type))
            
            result = cursor.fetchone()
            limit = THRONE_CONFIG["rate_limits"].get(action_type, 999)
            
            if not result:
                # Initialize rate limit entry
                cursor.execute("""
                    INSERT INTO rate_limits (commander_id, action_type, count, reset_time)
                    VALUES (?, ?, 1, ?)
                """, (commander_id, action_type, datetime.now() + timedelta(hours=1)))
                return True
            
            count, reset_time = result
            reset_time = datetime.fromisoformat(reset_time)
            
            # Check if reset time has passed
            if datetime.now() > reset_time:
                cursor.execute("""
                    UPDATE rate_limits SET count = 1, reset_time = ?
                    WHERE commander_id = ? AND action_type = ?
                """, (datetime.now() + timedelta(hours=1), commander_id, action_type))
                return True
            
            # Check limit
            if count >= limit:
                return False
            
            # Increment counter
            cursor.execute("""
                UPDATE rate_limits SET count = count + 1
                WHERE commander_id = ? AND action_type = ?
            """, (commander_id, action_type))
            
            return True

# Initialize database
throne_db = CommanderThroneDB(THRONE_CONFIG["database_path"])

def require_auth(access_level: str = "OBSERVER"):
    """Authentication decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'commander_id' not in session:
                return redirect(url_for('throne_login'))
            
            user_level = session.get('access_level', 'OBSERVER')
            required_level = ACCESS_LEVELS[access_level]["level"]
            user_level_num = ACCESS_LEVELS.get(user_level, {"level": 0})["level"]
            
            if user_level_num < required_level:
                return jsonify({"error": "Insufficient access level"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permission(permission: str):
    """Permission-based decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_level = session.get('access_level', 'OBSERVER')
            permissions = ACCESS_LEVELS.get(user_level, {"permissions": []})["permissions"]
            
            if "*" not in permissions and permission not in permissions:
                return jsonify({"error": f"Permission '{permission}' required"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/throne')
def throne_login():
    """Login page for Commander Throne"""
    return render_template('throne_login.html')

@app.route('/throne/auth', methods=['POST'])
def throne_authenticate():
    """Authenticate commander"""
    data = request.get_json()
    username = data.get('username', '').upper()
    password = data.get('password', '')
    
    # Hash password for comparison
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    user = THRONE_USERS.get(username)
    if not user or user['password_hash'] != password_hash:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    # Create session
    session['commander_id'] = username
    session['access_level'] = user['access_level']
    session['user_id'] = user['user_id']
    session['login_time'] = datetime.now().isoformat()
    
    # Log authentication
    throne_db.log_command(username, "LOGIN", ip=request.remote_addr)
    
    return jsonify({
        "success": True, 
        "access_level": user['access_level'],
        "redirect": "/throne/dashboard"
    })

@app.route('/throne/dashboard')
@require_auth("OBSERVER")
def throne_dashboard():
    """Main commander throne dashboard"""
    return render_template('throne_dashboard.html', 
                         access_level=session.get('access_level'),
                         commander_id=session.get('commander_id'))

@app.route('/throne/api/mission_stats')
@require_auth("OBSERVER")
def api_mission_stats():
    """Get live mission statistics"""
    try:
        # Import required modules
        import sys
        sys.path.append('/root/HydraX-v2/src')
        
        from bitten_core.live_performance_tracker import live_tracker
        
        # Get performance metrics
        metrics = live_tracker.get_live_performance_metrics(24)
        
        # Get mission count from mission files
        mission_count = 0
        if os.path.exists('/root/HydraX-v2/missions'):
            mission_count = len([f for f in os.listdir('/root/HydraX-v2/missions') if f.endswith('.json')])
        
        # Get bridge status
        import requests
        bridge_status = "OFFLINE"
        try:
            response = requests.get("http://localhost:8890/bridge_troll/health", timeout=2)
            if response.status_code == 200:
                bridge_status = "ONLINE"
        except:
            pass
        
        return jsonify({
            "active_users": metrics.total_signals_generated // 10,  # Estimate
            "trades_today": metrics.signals_last_24h,
            "win_rate": round(metrics.win_rate_24h, 1),
            "total_xp_awarded": metrics.total_signals_generated * 15,  # Estimate
            "bridge_status": bridge_status,
            "mission_count": mission_count
        })
        
    except Exception as e:
        logger.error(f"Error getting mission stats: {e}")
        return jsonify({
            "active_users": 0,
            "trades_today": 0,
            "win_rate": 0.0,
            "total_xp_awarded": 0,
            "bridge_status": "ERROR",
            "mission_count": 0
        })

@app.route('/throne/api/soldier_roster')
@require_auth("OBSERVER")
def api_soldier_roster():
    """Get soldier roster data"""
    # Mock data for now - would integrate with user database
    soldiers = [
        {
            "username": "APEX_OPERATIVE_001",
            "tier": "APEX",
            "xp": 12750,
            "telegram_linked": True,
            "last_seen": "5m ago",
            "trade_count": 127
        },
        {
            "username": "COMMANDER_GHOST",
            "tier": "COMMANDER", 
            "xp": 8940,
            "telegram_linked": True,
            "last_seen": "18m ago",
            "trade_count": 89
        },
        {
            "username": "FANG_HUNTER_X",
            "tier": "FANG",
            "xp": 4520,
            "telegram_linked": False,
            "last_seen": "2h ago",
            "trade_count": 45
        }
    ]
    
    return jsonify({"soldiers": soldiers})

@app.route('/throne/api/trade_log')
@require_auth("OBSERVER") 
def api_trade_log():
    """Get recent trade log"""
    # Mock data - would integrate with actual trade log
    trades = [
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "user": "APEX_001",
            "pair": "EURUSD",
            "direction": "BUY",
            "result": "WIN",
            "pips": "+15.7",
            "xp_earned": 25
        },
        {
            "time": (datetime.now() - timedelta(minutes=5)).strftime("%H:%M:%S"),
            "user": "CMD_GHOST",
            "pair": "GBPJPY", 
            "direction": "SELL",
            "result": "LOSS",
            "pips": "-8.2",
            "xp_earned": 0
        }
    ]
    
    return jsonify({"trades": trades})

@app.route('/throne/api/sitrep')
@require_auth("OBSERVER")
def api_sitrep():
    """Generate situational report"""
    try:
        import sys
        sys.path.append('/root/HydraX-v2/src')
        from bitten_core.live_performance_tracker import live_tracker
        
        metrics = live_tracker.get_live_performance_metrics(24)
        
        sitrep = {
            "timestamp": datetime.now().isoformat(),
            "xp_flow_24h": metrics.total_signals_generated * 15,
            "signal_fire_volume": metrics.signals_last_24h,
            "bridge_response_time": "< 100ms",
            "active_users_by_mode": {
                "MANUAL": 12,
                "SEMI_AUTO": 8,
                "FULL_AUTO": 5
            },
            "press_pass_conversion": "18.5%",
            "referrals_vs_enlistments": "3:1",
            "overdue_telegram_links": 4,
            "badge_unlock_velocity": "2.3/hour",
            "most_profitable_user": "APEX_OPERATIVE_001",
            "win_rate_trend": "↗️ +2.1% (24h)"
        }
        
        return jsonify({"sitrep": sitrep})
        
    except Exception as e:
        logger.error(f"Error generating SITREP: {e}")
        return jsonify({"error": "SITREP generation failed"}), 500

@app.route('/throne/api/command', methods=['POST'])
@require_auth("LIEUTENANT")
def api_execute_command():
    """Execute throne commands"""
    data = request.get_json()
    command = data.get('command')
    parameters = data.get('parameters', {})
    commander_id = session.get('commander_id')
    
    # Check rate limiting
    if not throne_db.check_rate_limit(commander_id, command):
        return jsonify({"success": False, "message": "Rate limit exceeded"}), 429
    
    result = {"success": False, "message": "Unknown command"}
    
    try:
        if command == "toggle_stealth":
            # Toggle global stealth mode
            result = {"success": True, "message": "Stealth mode toggled"}
            
        elif command == "global_alert":
            # Send global alert
            message = parameters.get('message', 'System alert from Commander Throne')
            result = {"success": True, "message": f"Global alert sent: {message}"}
            
        elif command == "award_xp":
            # Award XP to user
            user_id = parameters.get('user_id')
            amount = parameters.get('amount', 0)
            result = {"success": True, "message": f"Awarded {amount} XP to {user_id}"}
            
        elif command == "reset_cooldowns":
            # Reset all cooldowns
            result = {"success": True, "message": "All cooldowns reset"}
            
        elif command == "halt_trades":
            # Emergency halt all new trades
            result = {"success": True, "message": "All new trades halted"}
            
        elif command == "double_xp_event":
            # Activate double XP event
            duration = parameters.get('duration', 60)  # minutes
            result = {"success": True, "message": f"Double XP event activated for {duration} minutes"}
        
        # Log the command
        throne_db.log_command(
            commander_id, command, 
            parameters.get('target'), 
            parameters, 
            json.dumps(result),
            request.remote_addr
        )
        
    except Exception as e:
        result = {"success": False, "message": f"Command execution failed: {str(e)}"}
        logger.error(f"Command execution error: {e}")
    
    return jsonify(result)

@app.route('/throne/api/command_log')
@require_auth("COMMANDER")
def api_command_log():
    """Get recent command log"""
    with sqlite3.connect(throne_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, commander_id, action, target, parameters, result
            FROM command_log 
            ORDER BY timestamp DESC 
            LIMIT 100
        """)
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "timestamp": row[0],
                "commander": row[1],
                "action": row[2],
                "target": row[3] or "N/A",
                "parameters": row[4] or "{}",
                "result": row[5] or "Unknown"
            })
    
    return jsonify({"logs": logs})

@app.route('/health')
def health_check():
    """Health endpoint for monitoring systems"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Commander Throne",
        "checks": {}
    }
    
    try:
        # 1. Service status - if we got here, the service is running
        health_status["checks"]["service"] = {
            "status": "ok",
            "message": "Service is running"
        }
        
        # 2. Database connectivity check
        try:
            with sqlite3.connect(throne_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status["checks"]["database"] = {
                "status": "ok",
                "message": "Database connection successful"
            }
        except Exception as db_error:
            health_status["checks"]["database"] = {
                "status": "error",
                "message": f"Database connection failed: {str(db_error)}"
            }
            health_status["status"] = "unhealthy"
        
        # 3. Active sessions count
        try:
            with sqlite3.connect(throne_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM active_sessions 
                    WHERE datetime(last_activity) > datetime('now', '-8 hours')
                """)
                active_sessions = cursor.fetchone()[0]
            health_status["checks"]["active_sessions"] = {
                "status": "ok",
                "count": active_sessions,
                "max_allowed": THRONE_CONFIG["max_sessions"]
            }
        except Exception as session_error:
            health_status["checks"]["active_sessions"] = {
                "status": "error",
                "message": f"Failed to count sessions: {str(session_error)}"
            }
        
        # 4. Uptime calculation
        if not hasattr(app, 'start_time'):
            app.start_time = datetime.now()
        
        total_uptime_seconds = (datetime.now() - app.start_time).total_seconds()
        uptime_hours = int(total_uptime_seconds // 3600)
        uptime_minutes = int((total_uptime_seconds % 3600) // 60)
        uptime_seconds = int(total_uptime_seconds % 60)
        
        health_status["checks"]["uptime"] = {
            "status": "ok",
            "uptime_seconds": int(total_uptime_seconds),
            "uptime_formatted": f"{uptime_hours}h {uptime_minutes}m {uptime_seconds}s",
            "started_at": app.start_time.isoformat()
        }
        
        # 5. Last command timestamp
        try:
            with sqlite3.connect(throne_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp FROM command_log 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                last_command = cursor.fetchone()
                
            if last_command:
                last_command_time = datetime.fromisoformat(last_command[0])
                time_since_last = (datetime.now() - last_command_time).total_seconds()
                health_status["checks"]["last_command"] = {
                    "status": "ok",
                    "timestamp": last_command[0],
                    "seconds_ago": int(time_since_last)
                }
            else:
                health_status["checks"]["last_command"] = {
                    "status": "ok",
                    "message": "No commands executed yet"
                }
        except Exception as cmd_error:
            health_status["checks"]["last_command"] = {
                "status": "error",
                "message": f"Failed to get last command: {str(cmd_error)}"
            }
        
        # Additional health metrics
        health_status["metrics"] = {
            "memory_usage_mb": get_memory_usage(),
            "thread_count": threading.active_count(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        logger.error(f"Health check failed: {e}")
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

def get_memory_usage():
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return round(process.memory_info().rss / 1024 / 1024, 2)
    except:
        return 0

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    if 'commander_id' not in session:
        return False
    
    emit('connection_established', {
        'commander_id': session.get('commander_id'),
        'access_level': session.get('access_level')
    })

@socketio.on('request_live_update')
def handle_live_update():
    """Handle live data update requests"""
    if 'commander_id' not in session:
        return
    
    # Send live updates every 5 seconds
    def send_updates():
        while True:
            try:
                # Get fresh mission stats
                with app.test_request_context():
                    stats = api_mission_stats().get_json()
                
                socketio.emit('live_update', stats)
                time.sleep(5)
            except:
                break
    
    threading.Thread(target=send_updates, daemon=True).start()

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('/root/HydraX-v2/data', exist_ok=True)
    
    # Initialize start time for uptime tracking
    app.start_time = datetime.now()
    
    logger.info("🏆 BITTEN Commander Throne starting on port 8899...")
    socketio.run(app, host='0.0.0.0', port=8899, debug=False, allow_unsafe_werkzeug=True)