"""
Unified TOC Server - Complete BITTEN Trade Execution System

This is the main server that wires together:
- Flask API endpoints
- Terminal assignment management
- Fire routing to MT5 terminals
- Trade result callbacks
- Telegram bot integration
- XP and statistics tracking
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from typing import Dict, Optional, List
import threading
import time
from pathlib import Path

# Import BITTEN components
from terminal_assignment import TerminalAssignment, TerminalType, TerminalStatus
from fire_router_toc import FireRouterTOC, TradeSignal, SignalType, DeliveryMethod
from ..bitten_core.xp_integration import XPIntegration
from ..bitten_core.fire_mode_validator import FireModeValidator
from ..bitten_core.risk_controller import RiskController
from ..bitten_core.database.repository import UserRepository
from ..bitten_core.database.manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize core components
db_manager = DatabaseManager()
user_repo = UserRepository(db_manager)
terminal_manager = TerminalAssignment("data/terminal_assignments.db")
fire_router = FireRouterTOC("data/terminal_assignments.db")
xp_integration = XPIntegration(db_manager)
fire_validator = FireModeValidator(db_manager)
risk_controller = RiskController(db_manager)

# Configuration
CONFIG = {
    'FLASK_PORT': int(os.getenv('TOC_PORT', '5000')),
    'FLASK_HOST': os.getenv('TOC_HOST', '0.0.0.0'),
    'BRIDGE_TERMINALS': {
        'press_pass': {
            'ip': os.getenv('BRIDGE_PP_IP', '192.168.1.100'),
            'port': int(os.getenv('BRIDGE_PP_PORT', '5001')),
            'folder': os.getenv('BRIDGE_PP_FOLDER', '/mt5/terminals/press_pass')
        },
        'demo': {
            'ip': os.getenv('BRIDGE_DEMO_IP', '192.168.1.101'),
            'port': int(os.getenv('BRIDGE_DEMO_PORT', '5002')),
            'folder': os.getenv('BRIDGE_DEMO_FOLDER', '/mt5/terminals/demo')
        },
        'live': {
            'ip': os.getenv('BRIDGE_LIVE_IP', '192.168.1.102'),
            'port': int(os.getenv('BRIDGE_LIVE_PORT', '5003')),
            'folder': os.getenv('BRIDGE_LIVE_FOLDER', '/mt5/terminals/live')
        }
    },
    'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
    'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID')
}

# Track active sessions
active_sessions = {}
session_lock = threading.Lock()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'BITTEN TOC Server',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'database': db_manager.is_connected(),
            'terminals': len(terminal_manager.get_available_terminals()) > 0,
            'active_sessions': len(active_sessions)
        }
    })


@app.route('/assign-terminal', methods=['POST'])
def assign_terminal():
    """
    Assign a terminal to a user
    
    Expected JSON:
    {
        "user_id": "telegram_user_id",
        "terminal_type": "press_pass|demo|live",
        "mt5_credentials": {
            "login": "12345",
            "password": "password",
            "server": "broker-server.com:443"
        }
    }
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        terminal_type_str = data.get('terminal_type', 'press_pass')
        mt5_credentials = data.get('mt5_credentials', {})
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Map string to enum
        terminal_type_map = {
            'press_pass': TerminalType.PRESS_PASS,
            'demo': TerminalType.DEMO,
            'live': TerminalType.LIVE
        }
        
        terminal_type = terminal_type_map.get(terminal_type_str, TerminalType.PRESS_PASS)
        
        # Get user details
        user = user_repo.get_user_by_telegram_id(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if terminal type matches user tier
        if terminal_type == TerminalType.LIVE and user.tier == 'PRESS_PASS':
            return jsonify({'error': 'Live trading not available for Press Pass users'}), 403
        
        # Assign terminal
        assignment = terminal_manager.assign_terminal(
            user_id=user_id,
            terminal_type=terminal_type,
            metadata={
                'mt5_credentials': mt5_credentials,
                'tier': user.tier,
                'assigned_by': 'TOC_API'
            }
        )
        
        if not assignment:
            return jsonify({'error': f'No available {terminal_type_str} terminals'}), 503
        
        # Store session
        with session_lock:
            active_sessions[user_id] = {
                'assignment': assignment,
                'terminal_type': terminal_type_str,
                'assigned_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
        
        # Send terminal launch command to bridge
        bridge_config = CONFIG['BRIDGE_TERMINALS'][terminal_type_str]
        launch_result = _launch_terminal_on_bridge(
            bridge_ip=assignment['ip_address'],
            bridge_port=assignment['port'],
            folder_path=assignment['folder_path'],
            mt5_credentials=mt5_credentials
        )
        
        return jsonify({
            'success': True,
            'assignment': assignment,
            'terminal_launched': launch_result,
            'message': f'Terminal {assignment["terminal_name"]} assigned to user {user_id}'
        })
        
    except Exception as e:
        logger.error(f"Terminal assignment error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/fire', methods=['POST'])
def fire_signal():
    """
    Fire a trade signal to user's assigned terminal
    
    Expected JSON:
    {
        "user_id": "telegram_user_id",
        "signal": {
            "symbol": "EURUSD",
            "direction": "buy|sell",
            "volume": 0.01,
            "stop_loss": 1.0850,
            "take_profit": 1.0950,
            "comment": "BITTEN Signal"
        }
    }
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        signal_data = data.get('signal', {})
        
        if not user_id or not signal_data:
            return jsonify({'error': 'user_id and signal required'}), 400
        
        # Get user session
        with session_lock:
            session = active_sessions.get(user_id)
        
        if not session:
            return jsonify({'error': 'No active terminal assignment for user'}), 404
        
        # Get user for validation
        user = user_repo.get_user_by_telegram_id(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate fire mode and risk
        fire_mode = user.fire_mode or 'MANUAL'
        validation = fire_validator.validate_fire_action(user_id, fire_mode, signal_data['symbol'])
        
        if not validation['allowed']:
            return jsonify({
                'success': False,
                'error': validation['reason'],
                'cooldown_remaining': validation.get('cooldown_remaining')
            }), 403
        
        # Check risk limits
        risk_check = risk_controller.check_trade_allowed(
            user_id=user_id,
            symbol=signal_data['symbol'],
            volume=signal_data.get('volume', 0.01)
        )
        
        if not risk_check['allowed']:
            return jsonify({
                'success': False,
                'error': risk_check['reason']
            }), 403
        
        # Create trade signal
        trade_signal = TradeSignal(
            user_id=user_id,
            signal_type=SignalType.OPEN_POSITION,
            symbol=signal_data['symbol'],
            direction=signal_data['direction'],
            volume=signal_data.get('volume', 0.01),
            stop_loss=signal_data.get('stop_loss'),
            take_profit=signal_data.get('take_profit'),
            comment=signal_data.get('comment', 'BITTEN Signal'),
            magic_number=signal_data.get('magic_number', 12345),
            metadata={
                'fire_mode': fire_mode,
                'tier': user.tier,
                'tcs_score': signal_data.get('tcs_score', 0)
            }
        )
        
        # Route signal to terminal
        terminal_type = TerminalType[session['terminal_type'].upper()]
        response = fire_router.route_signal(
            signal=trade_signal,
            terminal_type=terminal_type,
            preferred_terminal_id=session['assignment']['terminal_id']
        )
        
        # Update session activity
        with session_lock:
            if user_id in active_sessions:
                active_sessions[user_id]['last_activity'] = datetime.now().isoformat()
        
        # Log trade attempt
        if response.success:
            # Award XP for successful signal routing
            xp_integration.award_xp(
                user_id=user_id,
                amount=10,
                reason='trade_signal_fired',
                metadata={'symbol': signal_data['symbol']}
            )
        
        return jsonify({
            'success': response.success,
            'message': response.message,
            'terminal': response.terminal_name,
            'delivery_method': response.delivery_method,
            'signal_id': response.response_data.get('signal_id') if response.response_data else None
        })
        
    except Exception as e:
        logger.error(f"Fire signal error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/trade-result', methods=['POST'])
def trade_result_callback():
    """
    Receive trade execution results from MT5 terminals
    
    Expected JSON:
    {
        "user_id": "telegram_user_id",
        "terminal_id": 1,
        "trade_result": {
            "ticket": 12345678,
            "symbol": "EURUSD",
            "type": "buy",
            "volume": 0.01,
            "open_price": 1.0900,
            "close_price": 1.0920,
            "profit": 20.00,
            "commission": -0.10,
            "swap": 0,
            "closed_at": "2025-01-09T10:30:00"
        }
    }
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        trade_result = data.get('trade_result', {})
        
        if not user_id or not trade_result:
            return jsonify({'error': 'user_id and trade_result required'}), 400
        
        # Process trade result
        profit = trade_result.get('profit', 0)
        
        # Update user statistics
        user_repo.update_trade_stats(
            user_id=user_id,
            trade_result=trade_result
        )
        
        # Award XP based on profit
        if profit > 0:
            xp_amount = min(int(profit), 100)  # Cap at 100 XP per trade
            xp_integration.award_xp(
                user_id=user_id,
                amount=xp_amount,
                reason='profitable_trade',
                metadata={'profit': profit, 'symbol': trade_result['symbol']}
            )
        
        # Update risk controller with trade result
        risk_controller.update_trade_result(
            user_id=user_id,
            symbol=trade_result['symbol'],
            profit=profit
        )
        
        # Send notification to user via Telegram
        if CONFIG['TELEGRAM_BOT_TOKEN']:
            _send_telegram_notification(
                user_id=user_id,
                message=f"Trade closed: {trade_result['symbol']} - P/L: ${profit:.2f}"
            )
        
        return jsonify({
            'success': True,
            'message': 'Trade result processed',
            'xp_awarded': profit > 0
        })
        
    except Exception as e:
        logger.error(f"Trade result processing error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/status/<user_id>', methods=['GET'])
def user_status(user_id):
    """Get user's current terminal assignment and trading status"""
    try:
        # Get user
        user = user_repo.get_user_by_telegram_id(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get active assignments
        assignments = terminal_manager.get_user_assignments(user_id, active_only=True)
        
        # Get session info
        with session_lock:
            session = active_sessions.get(user_id)
        
        # Get today's stats
        daily_stats = risk_controller.get_daily_stats(user_id)
        
        return jsonify({
            'user': {
                'id': user_id,
                'tier': user.tier,
                'fire_mode': user.fire_mode,
                'xp': user.xp_total,
                'level': user.level
            },
            'assignments': assignments,
            'session': session,
            'daily_stats': daily_stats,
            'cooldowns': fire_validator.get_user_cooldowns(user_id)
        })
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/release-terminal/<user_id>', methods=['POST'])
def release_terminal(user_id):
    """Release user's terminal assignment"""
    try:
        # Release terminal
        released = terminal_manager.release_terminal(user_id)
        
        # Clear session
        with session_lock:
            if user_id in active_sessions:
                del active_sessions[user_id]
        
        return jsonify({
            'success': released,
            'message': f'Terminal released for user {user_id}' if released else 'No active assignment found'
        })
        
    except Exception as e:
        logger.error(f"Terminal release error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/terminals', methods=['GET'])
def list_terminals():
    """List all terminals and their status"""
    try:
        terminal_type = request.args.get('type')
        
        if terminal_type:
            terminals = terminal_manager.get_available_terminals(
                TerminalType[terminal_type.upper()]
            )
        else:
            terminals = terminal_manager.get_available_terminals()
        
        stats = terminal_manager.get_statistics()
        
        return jsonify({
            'terminals': terminals,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Terminal listing error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/metrics', methods=['GET'])
def system_metrics():
    """Get system performance metrics"""
    try:
        metrics = {
            'fire_router': fire_router.stats,
            'active_sessions': len(active_sessions),
            'terminal_stats': terminal_manager.get_statistics(),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({'error': str(e)}), 500


# Helper functions
def _launch_terminal_on_bridge(bridge_ip: str, bridge_port: int, 
                              folder_path: str, mt5_credentials: Dict) -> bool:
    """Send command to bridge to launch MT5 terminal"""
    try:
        url = f"http://{bridge_ip}:{bridge_port}/launch-terminal"
        payload = {
            'folder_path': folder_path,
            'credentials': mt5_credentials
        }
        
        response = requests.post(url, json=payload, timeout=30)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Failed to launch terminal on bridge: {e}")
        return False


def _send_telegram_notification(user_id: str, message: str):
    """Send notification to user via Telegram"""
    try:
        # This would integrate with your Telegram bot
        # For now, just log it
        logger.info(f"Telegram notification for {user_id}: {message}")
        
    except Exception as e:
        logger.error(f"Telegram notification error: {e}")


# Background tasks
def cleanup_stale_sessions():
    """Cleanup inactive sessions periodically"""
    while True:
        try:
            time.sleep(3600)  # Run every hour
            
            with session_lock:
                now = datetime.now()
                stale_users = []
                
                for user_id, session in active_sessions.items():
                    last_activity = datetime.fromisoformat(session['last_activity'])
                    if (now - last_activity).total_seconds() > 86400:  # 24 hours
                        stale_users.append(user_id)
                
                for user_id in stale_users:
                    terminal_manager.release_terminal(user_id)
                    del active_sessions[user_id]
                    logger.info(f"Cleaned up stale session for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")


# Initialize terminals on startup
def initialize_terminals():
    """Initialize default terminals in the database"""
    try:
        # Check if terminals already exist
        existing = terminal_manager.get_available_terminals()
        if existing:
            logger.info(f"Found {len(existing)} existing terminals")
            return
        
        # Add default terminals
        for terminal_type, config in CONFIG['BRIDGE_TERMINALS'].items():
            terminal_id = terminal_manager.add_terminal(
                terminal_name=f"{terminal_type.upper()}-01",
                terminal_type=TerminalType[terminal_type.upper()],
                ip_address=config['ip'],
                port=config['port'],
                folder_path=config['folder'],
                max_users=10 if terminal_type == 'press_pass' else 5,
                metadata={
                    'broker': 'MetaQuotes',
                    'version': '5.0.36',
                    'region': 'US-East'
                }
            )
            logger.info(f"Added {terminal_type} terminal with ID {terminal_id}")
            
    except Exception as e:
        logger.error(f"Terminal initialization error: {e}")


if __name__ == '__main__':
    # Initialize terminals
    initialize_terminals()
    
    # Start background tasks
    cleanup_thread = threading.Thread(target=cleanup_stale_sessions, daemon=True)
    cleanup_thread.start()
    
    # Start Flask server
    logger.info(f"Starting BITTEN TOC Server on {CONFIG['FLASK_HOST']}:{CONFIG['FLASK_PORT']}")
    app.run(
        host=CONFIG['FLASK_HOST'],
        port=CONFIG['FLASK_PORT'],
        debug=False
    )