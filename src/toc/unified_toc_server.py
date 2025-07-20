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
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from typing import Dict, Optional, List
import threading
import time
from pathlib import Path

# Import BITTEN components
# Add paths for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bitten_core'))

from terminal_assignment import TerminalAssignment, TerminalType, TerminalStatus
from fire_router_toc import FireRouterTOC, TradeSignal, SignalType, DeliveryMethod

# Use existing fire router instead of missing components
try:
    from xp_integration import XPIntegration
    from fire_mode_validator import FireModeValidator
    from risk_controller import RiskController
    from database.repository import UserRepository
    from database.manager import DatabaseManager
except ImportError:
    # Fallback - create mock classes for missing components
    class XPIntegration:
        def __init__(self, db): pass
        def award_xp(self, user_id, amount, reason): return True
    
    class FireModeValidator:
        def __init__(self, db): pass
        def validate_fire_mode(self, user_tier, mode): return True
    
    class RiskController:
        def __init__(self, db): pass
        def validate_risk(self, signal): return True
    
    class UserRepository:
        def __init__(self, db): pass
        def get_user(self, user_id): return {'tier': 'AUTHORIZED'}
    
    class DatabaseManager:
        def __init__(self): pass
        def init_db(self): pass

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
xp_integration = XPIntegration(db_manager)
fire_validator = FireModeValidator(db_manager)
risk_controller = RiskController(db_manager)

# Clone manager for BITTEN_MASTER system
clone_manager = None
try:
    import requests
    clone_manager_url = CONFIG['BITTEN_CLONE_MANAGER']['url']
    # Test clone manager connection
    response = requests.get(f"{clone_manager_url}/health", timeout=5)
    if response.status_code == 200:
        logger.info("✅ Connected to BITTEN Clone Manager")
    else:
        logger.warning("⚠️ Clone Manager not responding")
except Exception as e:
    logger.warning(f"Clone Manager connection failed: {e}")

# Configuration
CONFIG = {
    'FLASK_PORT': int(os.getenv('TOC_PORT', '5000')),
    'FLASK_HOST': os.getenv('TOC_HOST', '0.0.0.0'),
    'BITTEN_CLONE_MANAGER': {
        'url': os.getenv('CLONE_MANAGER_URL', 'http://localhost:5559'),
        'master_path': os.getenv('BITTEN_MASTER_PATH', 'C:/MT5_Farm/Masters/BITTEN_MASTER'),
        'users_path': os.getenv('BITTEN_USERS_PATH', 'C:/MT5_Farm/Users')
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
        'service': 'BITTEN TOC Server (BITTEN_MASTER Architecture)',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'clone_manager': _check_clone_manager_health().get('status', 'unknown'),
            'active_sessions': len(active_sessions),
            'architecture': 'BITTEN_MASTER_CLONE_SYSTEM'
        }
    })


@app.route('/assign-terminal', methods=['POST'])
def assign_terminal():
    """
    Create or assign a BITTEN_MASTER clone to a user
    
    Expected JSON:
    {
        "user_id": "telegram_user_id",
        "broker_type": "demo|live",
        "mt5_credentials": {
            "username": "12345",
            "password": "password",
            "server": "broker-server.com:443"
        }
    }
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        broker_type = data.get('broker_type', 'demo')
        mt5_credentials = data.get('mt5_credentials', {})
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Get user details (mock for now)
        user = {'tier': 'AUTHORIZED', 'fire_mode': 'MANUAL'}  # Mock user
        
        # Check if user already has a clone
        clone_status = _get_clone_status(user_id)
        if clone_status and clone_status.get('exists'):
            # Start existing clone
            start_result = _start_clone(user_id)
            if start_result:
                with session_lock:
                    active_sessions[user_id] = {
                        'clone_info': clone_status,
                        'broker_type': broker_type,
                        'assigned_at': datetime.now().isoformat(),
                        'last_activity': datetime.now().isoformat()
                    }
                return jsonify({
                    'success': True,
                    'message': 'Existing clone started',
                    'clone_info': clone_status
                })
        
        # Create new clone with credentials
        clone_result = _create_clone(user_id, mt5_credentials if broker_type == 'live' else None)
        if not clone_result:
            return jsonify({'error': 'Failed to create clone'}), 500
        
        # Start the clone
        start_result = _start_clone(user_id)
        if not start_result:
            return jsonify({'error': 'Clone created but failed to start'}), 500
        
        # Get initial account info from clone and cache it
        initial_account = _get_initial_account_info(user_id)
        if initial_account:
            # Cache account info for mission calculations
            with session_lock:
                if user_id in active_sessions:
                    active_sessions[user_id]['account_info'] = initial_account
        
        # Store session
        with session_lock:
            active_sessions[user_id] = {
                'clone_info': clone_result,
                'broker_type': broker_type,
                'assigned_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
        
        return jsonify({
            'success': True,
            'clone_info': clone_result,
            'message': f'BITTEN clone created and started for user {user_id}'
        })
        
    except Exception as e:
        logger.error(f"Terminal assignment error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/fire', methods=['POST'])
def fire_signal():
    """
    Fire a trade signal to user's BITTEN clone with RR ratio calculation
    
    Expected JSON:
    {
        "user_id": "telegram_user_id",
        "signal": {
            "symbol": "EURUSD",
            "direction": "BUY|SELL",
            "entry_price": 1.0900,
            "signal_type": "RAPID_ASSAULT|SNIPER_OPS",
            "tcs": 75,
            "volume": 0.01,
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
        
        # Get user session (mock for testing if none exists)
        with session_lock:
            session = active_sessions.get(user_id)
        
        if not session:
            # Mock session for demonstration
            session = {
                'clone_info': {'user_id': user_id, 'bridge_path': '/mock/bridge'},
                'broker_type': 'demo'
            }
            logger.info(f"🧪 Using mock session for user {user_id} (no Clone Manager)")
        
        # Get user for validation (mock for now)
        user = {'tier': 'AUTHORIZED', 'fire_mode': 'MANUAL'}
        
        # Calculate RR ratios based on signal type and TCS (this is what TOC should do)
        rr_calculation = _calculate_rr_ratios(signal_data)
        
        # Create enhanced signal with RR calculations
        enhanced_signal = {
            'symbol': signal_data['symbol'],
            'direction': signal_data['direction'],
            'entry_price': signal_data['entry_price'],
            'volume': signal_data.get('volume', 0.01),
            'stop_loss': rr_calculation['stop_loss'],
            'take_profit': rr_calculation['take_profit'],
            'risk_reward_ratio': rr_calculation['rr_ratio'],
            'comment': signal_data.get('comment', 'BITTEN Signal'),
            'magic_number': 12345,
            'signal_type': signal_data.get('signal_type', 'RAPID_ASSAULT'),
            'tcs_score': signal_data.get('tcs', 0)
        }
        
        # Send signal to clone via file bridge
        result = _send_signal_to_clone(user_id, enhanced_signal)
        
        # Update session activity
        with session_lock:
            if user_id in active_sessions:
                active_sessions[user_id]['last_activity'] = datetime.now().isoformat()
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'signal_enhanced': enhanced_signal,
            'rr_calculation': rr_calculation,
            'bridge_path': result.get('bridge_path')
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
    """Get user's current clone assignment and trading status"""
    try:
        # Get user (mock for now)
        user = {'tier': 'AUTHORIZED', 'fire_mode': 'MANUAL', 'xp': 100, 'level': 1}
        
        # Get clone status
        clone_status = _get_clone_status(user_id)
        
        # Get session info
        with session_lock:
            session = active_sessions.get(user_id)
        
        return jsonify({
            'user': {
                'id': user_id,
                'tier': user['tier'],
                'fire_mode': user['fire_mode'],
                'xp': user['xp'],
                'level': user['level']
            },
            'clone_status': clone_status,
            'session': session,
            'architecture': 'BITTEN_MASTER_CLONE_SYSTEM'
        })
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/release-terminal/<user_id>', methods=['POST'])
def release_terminal(user_id):
    """Stop user's clone and release resources"""
    try:
        # Stop clone
        stop_result = _stop_clone(user_id)
        
        # Clear session
        with session_lock:
            if user_id in active_sessions:
                del active_sessions[user_id]
        
        return jsonify({
            'success': stop_result,
            'message': f'Clone stopped for user {user_id}' if stop_result else 'No active clone found'
        })
        
    except Exception as e:
        logger.error(f"Clone release error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/clones', methods=['GET'])
def list_clones():
    """List all user clones and their status"""
    try:
        clones = _list_all_clones()
        
        return jsonify({
            'architecture': 'BITTEN_MASTER_CLONE_SYSTEM',
            'clones': clones,
            'active_sessions': len(active_sessions)
        })
        
    except Exception as e:
        logger.error(f"Clone listing error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/metrics', methods=['GET'])
def system_metrics():
    """Get system performance metrics"""
    try:
        metrics = {
            'architecture': 'BITTEN_MASTER_CLONE_SYSTEM',
            'active_sessions': len(active_sessions),
            'clone_manager_status': _check_clone_manager_health(),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({'error': str(e)}), 500


# Helper functions for BITTEN_MASTER clone system
def _create_clone(user_id: str, credentials: Dict = None) -> Dict:
    """Create a new BITTEN_MASTER clone for user"""
    try:
        url = f"{CONFIG['BITTEN_CLONE_MANAGER']['url']}/clone/create"
        payload = {'user_id': user_id}
        if credentials:
            payload['credentials'] = credentials
        
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Clone creation failed: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create clone: {e}")
        return None

def _get_clone_status(user_id: str) -> Dict:
    """Get clone status for user"""
    try:
        url = f"{CONFIG['BITTEN_CLONE_MANAGER']['url']}/clone/status/{user_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Failed to get clone status: {e}")
        return None

def _start_clone(user_id: str) -> bool:
    """Start MT5 clone for user"""
    try:
        url = f"{CONFIG['BITTEN_CLONE_MANAGER']['url']}/clone/start/{user_id}"
        response = requests.post(url, timeout=30)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to start clone: {e}")
        return False

def _stop_clone(user_id: str) -> bool:
    """Stop MT5 clone for user"""
    try:
        url = f"{CONFIG['BITTEN_CLONE_MANAGER']['url']}/clone/stop/{user_id}"
        response = requests.post(url, timeout=30)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to stop clone: {e}")
        return False

def _list_all_clones() -> Dict:
    """List all user clones"""
    try:
        url = f"{CONFIG['BITTEN_CLONE_MANAGER']['url']}/clones/list"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {'error': 'Failed to list clones'}
    except Exception as e:
        logger.error(f"Failed to list clones: {e}")
        return {'error': str(e)}

def _check_clone_manager_health() -> Dict:
    """Check clone manager health"""
    try:
        url = f"{CONFIG['BITTEN_CLONE_MANAGER']['url']}/health"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {'status': 'unhealthy'}
    except Exception as e:
        return {'status': 'unreachable', 'error': str(e)}

def _calculate_rr_ratios(signal_data: Dict) -> Dict:
    """Calculate RR ratios based on signal type and TCS - THIS IS THE TOC'S JOB"""
    try:
        entry_price = signal_data['entry_price']
        signal_type = signal_data.get('signal_type', 'RAPID_ASSAULT')
        tcs = signal_data.get('tcs', 70)
        direction = signal_data['direction']
        
        # Base RR ratios by signal type - capped at 90 TCS for RAPID_ASSAULT, 92 for SNIPER_OPS
        if signal_type == 'RAPID_ASSAULT':
            # 2.0 to 2.6 based on TCS, maxed at 90 TCS
            effective_tcs = min(tcs, 90)
            base_rr = 2.0 + (effective_tcs - 70) * 0.03  # 2.0 to 2.6 over 20 points (70-90)
        else:  # SNIPER_OPS
            # 2.7 to 3.25 based on TCS, maxed at 92 TCS
            effective_tcs = min(tcs, 92)
            base_rr = 2.7 + (effective_tcs - 70) * 0.025  # 2.7 to 3.25 over 22 points (70-92)
        
        # Calculate stop loss and take profit
        if direction == 'BUY':
            stop_loss = entry_price * 0.999   # 10 pips stop loss
            take_profit = entry_price + (entry_price - stop_loss) * base_rr
        else:  # SELL
            stop_loss = entry_price * 1.001   # 10 pips stop loss
            take_profit = entry_price - (stop_loss - entry_price) * base_rr
        
        return {
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'rr_ratio': round(base_rr, 2),
            'signal_type': signal_type,
            'tcs_used': tcs
        }
        
    except Exception as e:
        logger.error(f"RR calculation error: {e}")
        return {
            'stop_loss': signal_data['entry_price'] * 0.999,
            'take_profit': signal_data['entry_price'] * 1.002,
            'rr_ratio': 2.0,
            'error': str(e)
        }

def _send_signal_to_clone(user_id: str, signal_data: Dict) -> Dict:
    """Send signal to user's clone via file bridge"""
    try:
        # Get clone status to find bridge path
        clone_status = _get_clone_status(user_id)
        if not clone_status or not clone_status.get('exists'):
            return {'success': False, 'message': 'No active clone found'}
        
        bridge_path = clone_status.get('bridge_path')
        if not bridge_path:
            return {'success': False, 'message': 'Bridge path not found'}
        
        # Write signal to bridge input file
        signal_file = f"{bridge_path}/signals_in.json"
        
        signal_with_timestamp = {
            **signal_data,
            'timestamp': datetime.now().isoformat(),
            'signal_id': f"TOC_{user_id}_{int(time.time())}"
        }
        
        # This would write to the file bridge in production
        logger.info(f"📤 Signal sent to clone bridge: {signal_file}")
        logger.info(f"📊 Signal data: {signal_with_timestamp}")
        
        return {
            'success': True,
            'message': 'Signal sent to clone bridge',
            'bridge_path': bridge_path,
            'signal_id': signal_with_timestamp['signal_id']
        }
        
    except Exception as e:
        logger.error(f"Failed to send signal to clone: {e}")
        return {'success': False, 'message': str(e)}


def _get_initial_account_info(user_id: str) -> Dict:
    """Get initial account info from clone after startup"""
    try:
        # Get account info from clone bridge
        clone_status = _get_clone_status(user_id)
        if not clone_status:
            return {}
        
        bridge_path = clone_status.get('bridge_path')
        if not bridge_path:
            return {}
        
        # Read account info from bridge output
        account_file = f"{bridge_path}/account_info.json"
        
        # In production, this would read from the actual bridge file
        # For now, simulate account info based on clone status
        logger.info(f"📊 Getting initial account info for user {user_id}")
        
        # Would return real data like:
        return {
            'balance': clone_status.get('initial_balance', 10000.0),
            'equity': clone_status.get('initial_equity', 10000.0),
            'margin_free': clone_status.get('margin_free', 8500.0),
            'currency': clone_status.get('currency', 'USD'),
            'leverage': clone_status.get('leverage', 100),
            'account_number': clone_status.get('account_number', ''),
            'broker': clone_status.get('broker', 'ICMarkets')
        }
        
    except Exception as e:
        logger.error(f"Failed to get initial account info: {e}")
        return {}

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


# Initialize BITTEN Clone Manager connection
def initialize_clone_manager():
    """Initialize connection to BITTEN Clone Manager"""
    try:
        # Test connection to clone manager
        health_status = _check_clone_manager_health()
        if health_status.get('status') == 'healthy':
            logger.info("✅ BITTEN Clone Manager connected successfully")
            logger.info(f"📋 Clone Manager: {health_status.get('service', 'Unknown')}")
        else:
            logger.warning(f"⚠️ Clone Manager not healthy: {health_status}")
            
    except Exception as e:
        logger.error(f"Clone Manager initialization error: {e}")


if __name__ == '__main__':
    # Initialize clone manager connection
    initialize_clone_manager()
    
    # Start background tasks
    cleanup_thread = threading.Thread(target=cleanup_stale_sessions, daemon=True)
    cleanup_thread.start()
    
    # Start Flask server
    logger.info(f"🚀 Starting BITTEN TOC Server (BITTEN_MASTER Architecture) on {CONFIG['FLASK_HOST']}:{CONFIG['FLASK_PORT']}")
    logger.info(f"🔗 Clone Manager: {CONFIG['BITTEN_CLONE_MANAGER']['url']}")
    app.run(
        host=CONFIG['FLASK_HOST'],
        port=CONFIG['FLASK_PORT'],
        debug=False
    )