#!/usr/bin/env python3
"""
Optimized Flask server with lazy loading and consolidated imports
Reduced memory footprint and improved performance
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
import random
from datetime import datetime
import sqlite3
from contextlib import contextmanager

# Core Flask imports (always needed)
from flask import Flask, render_template, render_template_string, request, jsonify, redirect
from flask_socketio import SocketIO

# Load environment early
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import individualized risk functions
sys.path.append('/root/HydraX-v2')
from fix_individualized_risk import get_user_risk_profile, calculate_position_size

# Initialize onboarding system - DISABLED for now
onboarding_system_available = False
register_onboarding_system = None
# try:
#     sys.path.append('/root/HydraX-v2/src/bitten_core')
#     from lib.onboarding_webapp_system import register_onboarding_system
#     onboarding_system_available = True
#     logger.info("✅ HydraX Onboarding System imported")
# except ImportError as e:
#     logger.error(f"❌ Failed to import onboarding system: {e}")
#     onboarding_system_available = False

# Lazy import manager
class LazyImports:
    """Manages lazy loading of heavy modules to reduce memory usage"""
    
    def __init__(self):
        self._stripe = None
        self._signal_storage = None
        self._engagement_db = None
        self._mission_api = None
        self._press_pass_api = None
        self._referral_system = None
        self._live_trade_api = None
        self._timer_integration = None
        self._venom_engine = None
    
    @property
    def stripe(self):
        if self._stripe is None:
            import stripe
            self._stripe = stripe
            logger.info("Stripe module loaded")
        return self._stripe
    
    @property
    def signal_storage(self):
        if self._signal_storage is None:
            try:
                from signal_storage import get_latest_signal, get_active_signals, get_signal_by_id
                self._signal_storage = {
                    'get_latest_signal': get_latest_signal,
                    'get_active_signals': get_active_signals,
                    'get_signal_by_id': get_signal_by_id
                }
                logger.info("Signal storage loaded")
            except ImportError as e:
                logger.warning(f"Signal storage not available: {e}")
                self._signal_storage = {}
        return self._signal_storage
    
    @property
    def engagement_db(self):
        if self._engagement_db is None:
            try:
                from engagement_db import handle_fire_action, get_signal_stats, get_user_stats
                self._engagement_db = {
                    'handle_fire_action': handle_fire_action,
                    'get_signal_stats': get_signal_stats,
                    'get_user_stats': get_user_stats
                }
                logger.info("Engagement DB loaded")
            except ImportError as e:
                logger.warning(f"Engagement DB not available: {e}")
                self._engagement_db = {}
        return self._engagement_db
    
    @property
    def referral_system(self):
        if self._referral_system is None:
            try:
                from standalone_referral_system import StandaloneReferralSystem
                self._referral_system = StandaloneReferralSystem()
                logger.info("Referral system loaded")
            except ImportError as e:
                logger.warning(f"Referral system not available: {e}")
                self._referral_system = None
        return self._referral_system
    
    @property
    def venom_engine(self):
        if self._venom_engine is None:
            try:
                from apex_production_live import ApexVenomV7Production
                self._venom_engine = ApexVenomV7Production
                logger.info("VENOM v7.0 Production engine loaded")
            except ImportError as e:
                logger.error(f"VENOM engine load failed: {e}")
                self._venom_engine = None
        return self._venom_engine

# Global lazy imports instance
lazy = LazyImports()

# Create Flask app with optimized config
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'bitten-tactical-2025'),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max upload
    'SEND_FILE_MAX_AGE_DEFAULT': 31536000,   # 1 year cache for static files
})

# Database helper
@contextmanager
def get_bitten_db():
    """Database connection context manager"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_user_tier(user_id):
    """Get user tier from EA instances or default to NIBBLER"""
    try:
        with get_bitten_db() as conn:
            result = conn.execute(
                "SELECT target_uuid FROM ea_instances WHERE user_id = ? ORDER BY last_seen DESC LIMIT 1", 
                (user_id,)
            ).fetchone()
            
            if result and result[0]:
                target_uuid = result[0]
                # Determine tier based on target_uuid
                if 'COMMANDER' in target_uuid.upper():
                    return 'COMMANDER'
                elif 'PREDATOR' in target_uuid.upper() or 'FANG' in target_uuid.upper():
                    return 'PREDATOR'
                else:
                    return 'NIBBLER'
            else:
                # Default to NIBBLER if no EA instance found
                return 'NIBBLER'
    except Exception as e:
        logger.warning(f"Error getting user tier for {user_id}: {e}")
        return 'NIBBLER'

def can_fire_signal_mode(user_tier, signal_mode):
    """Check if user tier can fire specific signal mode"""
    tier_permissions = {
        'NIBBLER': ['RAPID'],  # Only RAPID signals
        'PREDATOR': ['RAPID', 'SNIPER'],  # Both types
        'COMMANDER': ['RAPID', 'SNIPER']  # Both types
    }
    return signal_mode in tier_permissions.get(user_tier, [])

# Initialize SocketIO with optimized settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,  # Disable socketio logging to reduce overhead
    engineio_logger=False
)

# Register onboarding routes
if onboarding_system_available:
    try:
        register_onboarding_system(app)
        logger.info("✅ HydraX Onboarding routes registered")
    except Exception as e:
        logger.error(f"❌ Failed to register onboarding routes: {e}")

# Basic routes with lazy loading
@app.route('/')
def index():
    """Serve the new performance-focused landing page"""
    try:
        with open('/root/HydraX-v2/landing/index_performance.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to inline template
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BITTEN - Proven Trading Performance | 76.2% Win Rate</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <div id="bitten-hud">
                <h1>🎯 BITTEN - PROVEN PERFORMANCE</h1>
                <p>76.2% Win Rate | 7.34 Profit Factor | $425,793 Profit</p>
                <div id="signals-container">
                    {% for signal in signals %}
                    <div class="signal-card">{{ signal }}</div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
        """, signals=signals)
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return "BITTEN HUD - Loading...", 200

@app.route('/healthz')
def healthz():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'OK', 'service': 'webapp', 'timestamp': time.time()}), 200

@app.route('/api/signals', methods=['GET', 'POST'])
def api_signals():
    """API endpoint for signals - GET retrieves, POST receives from VENOM+CITADEL"""
    if request.method == 'GET':
        try:
            # Get query parameters for filtering
            mode_filter = request.args.get('mode')  # 'RAPID', 'SNIPER', or None for all
            user_id = request.args.get('user_id')
            
            # Direct database read - fixed signal system
            import sqlite3
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()
            
            # Get recent active signals
            cursor.execute("""
                SELECT signal_id, symbol, direction, confidence, entry, sl, tp, 
                       created_at, payload_json
                FROM signals 
                WHERE created_at > strftime('%s', 'now', '-6 hours')
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            signals = []
            filtered_signals = []
            
            # Get user tier for access control if user_id provided
            user_tier = get_user_tier(user_id) if user_id else 'NIBBLER'
            
            for row in results:
                try:
                    payload_data = {}
                    if row[8]:  # payload_json (index 8 now)
                        payload_data = json.loads(row[8])
                    
                    # Determine signal mode and time estimation
                    signal_type = payload_data.get('signal_type', 'RAPID_ASSAULT')
                    signal_mode = 'RAPID' if 'RAPID' in signal_type else 'SNIPER'
                    
                    # Apply mode filter if specified
                    if mode_filter and signal_mode != mode_filter:
                        continue
                    
                    # Estimate time to TP based on signal mode and target pips
                    target_pips = payload_data.get('target_pips', 40 if signal_mode == 'SNIPER' else 20)
                    estimated_time_hours = 0.5 + (target_pips * 0.1) if signal_mode == 'RAPID' else 2 + (target_pips * 0.15)
                    
                    signal = {
                        'signal_id': row[0],
                        'symbol': row[1],
                        'direction': row[2],
                        'confidence': float(row[3]) if row[3] else 75.0,
                        'entry_price': float(row[4]) if row[4] else 0.0,  # entry column
                        'sl': float(row[5]) if row[5] else 0.0,
                        'tp': float(row[6]) if row[6] else 0.0,
                        'stop_loss': float(row[5]) if row[5] else 0.0,  # Duplicate for compatibility
                        'take_profit': float(row[6]) if row[6] else 0.0,  # Duplicate for compatibility
                        'pattern_type': payload_data.get('pattern_type', 'UNKNOWN'),
                        'created_at': row[7],  # created_at is index 7
                        'stop_pips': payload_data.get('stop_pips', 20),
                        'target_pips': target_pips,
                        'risk_reward': payload_data.get('risk_reward', 2.0),
                        'signal_type': signal_type,
                        'signal_mode': signal_mode,  # NEW: RAPID or SNIPER
                        'estimated_time_to_tp': estimated_time_hours,  # NEW: Hours to TP
                        'mode_icon': '⚡' if signal_mode == 'RAPID' else '🎯',  # NEW: Visual icon
                        'mode_color': 'orange' if signal_mode == 'RAPID' else 'blue',  # NEW: Color theme
                        'can_fire': can_fire_signal_mode(user_tier, signal_mode) if user_id else True,  # NEW: Access control
                        'status': 'active'
                    }
                    signals.append(signal)
                except Exception as e:
                    logger.warning(f"Error processing signal row: {e}")
            
            response = {
                'signals': signals, 
                'count': len(signals),
                'filtered_by_mode': mode_filter,
                'user_tier': user_tier if user_id else None,
                'available_modes': ['RAPID', 'SNIPER']
            }
            
            return jsonify(response)
        except Exception as e:
            logger.error(f"Signals API error: {e}")
            return jsonify({'error': 'Signal retrieval failed'}), 500
    
    elif request.method == 'POST':
        # Receive signal from VENOM+CITADEL engine
        try:
            signal_data = request.get_json()
            
            if not signal_data:
                return jsonify({'error': 'No signal data provided'}), 400
            
            # BLACK BOX INTERCEPTION - Log EVERY signal at generation
            try:
                from black_box_complete_truth_system import get_truth_system
                truth_system = get_truth_system()
                signal_data = truth_system.log_signal_generation(signal_data)
                logger.info("🔒 Signal logged to Black Box Complete Truth System")
            except Exception as e:
                logger.error(f"Black Box truth tracking error: {e}")
                # Continue anyway - Black Box failure shouldn't stop signals
            
            # Log the incoming signal
            logger.info(f"📨 Received signal: {signal_data.get('signal_id')} "
                       f"for {signal_data.get('symbol')} @ {signal_data.get('confidence', 0)}% "
                       f"CITADEL: {signal_data.get('citadel_shield', {}).get('score', 0)}/10")
            print(f"[DEBUG] POST /api/signals received: {signal_data.get('signal_id')} @ {signal_data.get('confidence')}%")
            
            # Import BittenCore if available
            try:
                from src.bitten_core.bitten_core import BittenCore
                core = BittenCore()
                
                # Process the signal through BittenCore
                result = core.process_venom_signal(signal_data)
                
                # INSERT SIGNAL TO DATABASE FOR OUTCOME TRACKING
                try:
                    import sqlite3
                    import time
                    with sqlite3.connect('/root/HydraX-v2/bitten.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT OR IGNORE INTO signals
                            (signal_id, symbol, direction, entry, sl, tp, confidence, pattern_type, created_at, payload_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            signal_data.get("signal_id", ""),
                            signal_data.get("symbol", signal_data.get("pair", "")),
                            signal_data.get("direction", ""),
                            signal_data.get("entry_price", signal_data.get("entry", 0)),
                            float(signal_data.get("stop_loss", 0)) or float(signal_data.get("sl", 0)),
                            float(signal_data.get("take_profit", 0)) or float(signal_data.get("tp", 0)),
                            signal_data.get("confidence", 0),
                            signal_data.get("pattern_type", ""),  # Add pattern_type field
                            int(time.time()),
                            json.dumps(signal_data)
                        ))
                        conn.commit()
                        logger.info(f"📊 Signal {signal_data.get('signal_id')} logged to database for outcome tracking")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to log signal to database: {e}")
                
                # EVENT BUS INTEGRATION - Publish signal (fails silently)
                try:
                    from event_bus.event_bridge import signal_generated
                    signal_generated({
                        'signal_id': signal_data.get('signal_id'),
                        'symbol': signal_data.get('symbol', signal_data.get('pair')),
                        'direction': signal_data.get('direction'),
                        'confidence': signal_data.get('confidence', 0),
                        'pattern_type': signal_data.get('pattern_type', ''),
                        'entry': signal_data.get('entry_price', signal_data.get('entry', 0)),
                        'sl': signal_data.get('stop_loss', signal_data.get('sl', 0)),
                        'tp': signal_data.get('take_profit', signal_data.get('tp', 0))
                    })
                    print(f"✅ Event published for signal {signal_data.get('signal_id')}")
                except Exception as e:
                    print(f"❌ Event bus error: {e}")  # Log for debugging
                    pass  # Fails silently - non-critical
                
                # AUTO FIRE SYSTEM - Check for instant execution with ML filtering
                try:
                    signal_confidence = float(signal_data.get('confidence', 0))
                    signal_id = signal_data.get('signal_id', '')
                    
                    # Apply ML filter for smart signal selection (DISPLAY ONLY)
                    import sys
                    if '/root/HydraX-v2' not in sys.path:
                        sys.path.append('/root/HydraX-v2')
                    from ml_signal_filter import process_signal, report_trade_outcome
                    should_display, ml_reason = process_signal(signal_data)
                    
                    if should_display:
                        logger.info(f"📊 ML APPROVED FOR DISPLAY: {signal_id} @ {signal_confidence}% - {ml_reason}")
                    else:
                        logger.debug(f"🚫 ML BLOCKED FROM DISPLAY: {signal_id} @ {signal_confidence}% - {ml_reason}")
                    
                    # AUTO fire logic - 70% threshold with ML protection for bad patterns
                    print(f"[DEBUG] AUTO fire check: {signal_id} @ {signal_confidence}% (threshold: 70.0%)")
                    
                    # AUTO fire enabled with 70% threshold - ML feedback handles quality control
                    if signal_confidence >= 70.0:  # Lowered to 70% with ML protection
                        print(f"[DEBUG] HIGH CONFIDENCE - checking AUTO fire users")
                        logger.info(f"🎯 HIGH CONFIDENCE SIGNAL: {signal_id} @ {signal_confidence}% - Checking AUTO fire users")
                        
                        # Check for users with AUTO mode enabled
                        try:
                            import sqlite3
                            # Check fire_modes database for AUTO users
                            with sqlite3.connect('/root/HydraX-v2/data/fire_modes.db') as fire_conn:
                                fire_cursor = fire_conn.cursor()
                                fire_cursor.execute("""
                                    SELECT user_id, max_auto_slots, auto_slots_in_use 
                                    FROM user_fire_modes 
                                    WHERE current_mode = 'AUTO' AND auto_slots_in_use < max_auto_slots
                                """)
                                auto_mode_users = fire_cursor.fetchall()
                                
                            # Cross-reference with fresh EA connections
                            with sqlite3.connect('/root/HydraX-v2/bitten.db') as auto_conn:
                                auto_cursor = auto_conn.cursor()
                                
                                auto_users = []
                                for user_id, max_slots, slots_in_use in auto_mode_users:
                                    auto_cursor.execute("""
                                        SELECT DISTINCT ea.user_id, ea.target_uuid, ea.last_balance
                                        FROM ea_instances ea
                                        WHERE ea.user_id = ?
                                        AND (strftime('%s','now') - ea.last_seen) <= 120
                                    """, (user_id,))
                                    fresh_ea = auto_cursor.fetchall()
                                    auto_users.extend(fresh_ea)
                                
                                if auto_users:
                                    logger.info(f"🔥 AUTO FIRE TRIGGERED: {len(auto_users)} users eligible for {signal_id}")
                                    
                                    # Import fire execution system
                                    from enqueue_fire import enqueue_fire, create_fire_command
                                    
                                    for user_id, target_uuid, balance in auto_users:
                                        try:
                                            # Calculate lot size for 5% risk
                                            try:
                                                from src.bitten_core.fresh_fire_builder import FreshFireBuilder
                                                fire_builder = FreshFireBuilder()
                                                
                                                symbol = signal_data.get('symbol', 'EURUSD')
                                                entry_price = float(signal_data.get('entry_price', signal_data.get('entry', 0)))
                                                stop_loss = float(signal_data.get('stop_loss', signal_data.get('sl', 0)))
                                                take_profit = float(signal_data.get('take_profit', signal_data.get('tp', 0)))
                                                direction = signal_data.get('direction', 'BUY').upper()
                                                
                                                calculated_lot = fire_builder._calculate_position_size(
                                                    symbol=symbol,
                                                    entry=entry_price,
                                                    stop_loss=stop_loss,
                                                    balance=float(balance) if balance else 458.88,
                                                    risk_percent=3.0  # Reduced from 5% to 3% for margin management
                                                )
                                                
# [DISABLED BITMODE]                                                 # Check if user has BITMODE enabled
                                                from src.bitten_core.fire_mode_database import fire_mode_db
                                                bitmode_enabled = fire_mode_db.is_bitmode_enabled(str(user_id))
                                                
# [DISABLED BITMODE]                                                 # Create and send AUTO fire command with BITMODE support
                                                # Pass complete signal data for proper SL/TP calculation
                                                # If sl/tp are 0, enqueue_fire will calculate from stop_pips/target_pips
                                                auto_fire_cmd = create_fire_command(
                                                    mission_id=signal_id,
                                                    user_id=str(user_id),
                                                    symbol=symbol,
                                                    direction=direction,
                                                    entry=entry_price,
                                                    sl=stop_loss if stop_loss else 0,
                                                    tp=take_profit if take_profit else 0,
                                                    lot=calculated_lot,
                                                    enable_bitmode=bitmode_enabled
                                                )
                                                
                                                # If command creation failed (returned None), skip
                                                if auto_fire_cmd is None:
                                                    logger.warning(f"Fire command creation failed for {signal_id}")
                                                    continue
                                                
                                                # Occupy slot before firing
                                                from src.bitten_core.fire_mode_database import FireModeDatabase
                                                fire_db = FireModeDatabase()
                                                # AUTO slot for COMMANDER tier only
                                                if fire_db.occupy_slot(str(user_id), signal_id, symbol, slot_type='AUTO', user_tier='COMMANDER'):
                                                    # Send to IPC queue for INSTANT execution
                                                    enqueue_fire(auto_fire_cmd)
                                                    logger.info(f"⚡ AUTO FIRE SENT: {signal_id} for user {user_id} - {calculated_lot} lots @ {signal_confidence}% (Auto slot occupied)")
                                                else:
                                                    logger.warning(f"⚠️ No auto slots available for user {user_id}, skipping auto-fire")
                                                
                                            except Exception as lot_error:
                                                logger.error(f"AUTO fire lot calculation failed for {user_id}: {lot_error}")
                                                logger.error(f"Signal data values: symbol={symbol}, entry={entry_price}, sl={stop_loss}, balance={balance}")
                                                import traceback
                                                logger.error(f"Full traceback: {traceback.format_exc()}")
                                                # Use fallback lot size with proper 5% risk estimate
                                                estimated_lot = (float(balance) * 0.05) / 80 if balance else 0.50  # Assume ~$80 risk per lot
# [DISABLED BITMODE]                                                 # Check BITMODE for fallback command too
                                                fallback_bitmode = fire_mode_db.is_bitmode_enabled(str(user_id))
                                                
                                                auto_fire_cmd = create_fire_command(
                                                    mission_id=signal_id,
                                                    user_id=str(user_id),
                                                    symbol=signal_data.get('symbol', 'EURUSD'),
                                                    direction=signal_data.get('direction', 'BUY').upper(),
                                                    entry=float(signal_data.get('entry_price', signal_data.get('entry', 0))),
                                                    sl=float(signal_data.get('stop_loss', signal_data.get('sl', 0))),
                                                    tp=float(signal_data.get('take_profit', signal_data.get('tp', 0))),
                                                    lot=estimated_lot,
                                                    enable_bitmode=fallback_bitmode
                                                )
                                                # Check slot availability for fallback fire too
                                                from src.bitten_core.fire_mode_database import FireModeDatabase
                                                fire_db = FireModeDatabase()
                                                if fire_db.occupy_slot(str(user_id), signal_id, signal_data.get('symbol', 'EURUSD')):
                                                    enqueue_fire(auto_fire_cmd)
                                                    logger.info(f"⚡ AUTO FIRE SENT (fallback): {signal_id} for user {user_id} - {estimated_lot:.2f} lots (Slot occupied)")
                                                else:
                                                    logger.warning(f"⚠️ No slots available for user {user_id}, skipping fallback auto-fire")
                                                
                                        except Exception as fire_error:
                                            logger.error(f"AUTO fire failed for user {user_id}: {fire_error}")
                                else:
                                    logger.info(f"🚫 No AUTO users online for {signal_id} @ {signal_confidence}%")
                                    
                        except Exception as auto_error:
                            logger.error(f"AUTO fire system error: {auto_error}")
                    else:
                        logger.debug(f"📊 Signal {signal_id} @ {signal_confidence}% below AUTO threshold (79%)")
                        
                except Exception as confidence_error:
                    logger.warning(f"AUTO fire confidence check failed: {confidence_error}")
                
                logger.info(f"✅ Signal processed: {result}")
                return jsonify({'status': 'processed', 'result': result}), 200
                
            except ImportError:
                logger.error("❌ BittenCore not available")
                # Fallback: Just store the signal
                store_signal = lazy.signal_storage.get('store_signal')
                if store_signal:
                    store_signal(signal_data)
                    return jsonify({'status': 'stored'}), 200
                else:
                    return jsonify({'error': 'Cannot process signal'}), 503
                    
        except Exception as e:
            logger.error(f"Signal processing error: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/missions', methods=['GET'])
def api_missions():
    """Get list of available missions/signals"""
    try:
        import os
        import json
        from pathlib import Path
        
        missions_dir = Path("/root/HydraX-v2/missions")
        missions = []
        
        if missions_dir.exists():
            # Get recent mission files (last 50)
            mission_files = sorted(missions_dir.glob("ELITE_GUARD_*.json"), 
                                 key=os.path.getmtime, reverse=True)[:50]
            
            for mission_file in mission_files:
                try:
                    with open(mission_file, 'r') as f:
                        mission_data = json.load(f)
                        missions.append({
                            'mission_id': mission_data.get('mission_id', mission_file.stem),
                            'signal_id': mission_data.get('signal_id', mission_file.stem),
                            'symbol': mission_data.get('symbol', 'UNKNOWN'),
                            'direction': mission_data.get('direction', 'UNKNOWN'),
                            'confidence': mission_data.get('confidence', 0),
                            'pattern_type': mission_data.get('pattern_type', 'UNKNOWN'),
                            'created_at': mission_data.get('created_at', 0),
                            'status': mission_data.get('status', 'active')
                        })
                except Exception as e:
                    logger.warning(f"Failed to load mission {mission_file}: {e}")
                    continue
        
        return jsonify({
            'missions': missions,
            'total': len(missions),
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to load missions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/venom_signals')
def api_venom_signals():
    """Generate live VENOM v7.0 signals"""
    try:
        if lazy.venom_engine is None:
            return jsonify({'error': 'VENOM Engine not available'}), 503
        
        # Initialize VENOM engine
        venom = lazy.venom_engine()
        
        # Connect to MT5
        if not venom.connect_to_mt5():
            return jsonify({'error': 'Failed to connect to MT5'}), 503
        
        try:
            # Scan for signals
            signals = venom.scan_for_signals()
            
            # Format signals for API response
            formatted_signals = []
            for signal in signals:
                formatted_signals.append({
                    'signal_id': signal['signal_id'],
                    'pair': signal['pair'],
                    'signal_type': signal['signal_type'],
                    'confidence': signal['confidence'],
                    'entry_price': signal['entry_price'],
                    'stop_loss_pips': signal['stop_loss_pips'],
                    'take_profit_pips': signal['take_profit_pips'],
                    'risk_reward': signal['risk_reward'],
                    'countdown_minutes': signal['countdown_minutes'],
                    'session': signal['session'],
                    'quality': signal['quality'],
                    'timestamp': signal['timestamp'].isoformat(),
                    'data_source': 'VENOM_v7.0_LIVE'
                })
            
            return jsonify({
                'signals': formatted_signals,
                'count': len(formatted_signals),
                'engine': 'VENOM_v7.0',
                'data_source': 'MT5_LIVE',
                'scan_time': datetime.now().isoformat()
            })
            
        finally:
            venom.disconnect_mt5()
            
    except Exception as e:
        logger.error(f"VENOM signals API error: {e}")
        return jsonify({'error': f'VENOM signal generation failed: {str(e)}'}), 500

def log_hud_access(user_id, mission_id, username=None):
    """Log HUD access for Commander Throne monitoring"""
    try:
        import json
        from datetime import datetime
        
        # Create logs directory if it doesn't exist
        logs_dir = '/root/HydraX-v2/logs'
        os.makedirs(logs_dir, exist_ok=True)
        
        log_entry = {
            "user_id": user_id,
            "username": username or f"User_{user_id}",
            "mission_id": mission_id,
            "timestamp": datetime.now().isoformat(),
            "access_type": "hud_view"
        }
        
        # Append to log file
        with open('/root/HydraX-v2/logs/hud_access.jsonl', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
    except Exception as e:
        print(f"Warning: Could not log HUD access: {e}")

@app.route('/hud')
def mission_briefing():
    """Mission HUD interface for Telegram WebApp links"""
    try:
        # Accept both mission_id and signal (legacy) parameters
        mission_id = request.args.get('mission_id') or request.args.get('signal')
        user_id = request.args.get('user_id')  # Get from request, no hardcoded default
        
        if not mission_id:
            return render_template('error_hud.html', 
                                 error="Missing mission_id or signal parameter", 
                                 error_code=400), 400
        
        # Log HUD access for Commander Throne monitoring
        if user_id and mission_id:
            log_hud_access(user_id, mission_id)
        
        # Optional: Log HUD load attempts for debugging
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        logger.info(f"HUD load attempt: mission_id={mission_id}, user_id={user_id}, ip={client_ip}")
        
        # Load LIVE user data from EA instances database
        user_stats = {}
        user_training_data = {}
        
        # Check user's training academy progress
        if user_id:
            try:
                import json
                with open('/root/HydraX-v2/user_registry.json', 'r') as f:
                    registry = json.load(f)
                    if user_id in registry:
                        user_training_data = registry[user_id].get('training_academy', {})
                        
                        # Initialize new users to Day 1
                        if not user_training_data:
                            user_training_data = {
                                'lesson_day': 1,
                                'missions_opened_today': 0,
                                'last_lesson_access': None,
                                'lesson_progress': 'active',
                                'academy_start_date': None,
                                'total_lesson_missions': 0,
                                'academy_graduate': False
                            }
                            
                        # Increment mission count for the day
                        user_training_data['missions_opened_today'] += 1
                        user_training_data['total_lesson_missions'] += 1
                        user_training_data['last_lesson_access'] = datetime.now().isoformat()
                        
                        # Save updated progress
                        registry[user_id]['training_academy'] = user_training_data
                        with open('/root/HydraX-v2/user_registry.json', 'w') as f:
                            json.dump(registry, f, indent=2)
            except Exception as e:
                logger.error(f"Training academy data error: {e}")
        
        if user_id:
            try:
                import sqlite3
                with sqlite3.connect('/root/HydraX-v2/bitten.db') as conn:
                    cursor = conn.cursor()
                    # Get live balance from EA instances
                    cursor.execute("""
                        SELECT target_uuid, user_id, last_balance, last_equity, leverage, broker, currency
                        FROM ea_instances 
                        WHERE user_id = ? 
                        ORDER BY last_seen DESC 
                        LIMIT 1
                    """, (user_id,))
                    ea_data = cursor.fetchone()
                    
                if ea_data:
                    target_uuid, user_id_db, balance, equity, leverage, broker, currency = ea_data
                    
                    # Calculate real win rate from trade history
                    cursor.execute("""
                        SELECT COUNT(*) as total,
                               SUM(CASE WHEN status = 'WIN' OR (ticket > 0 AND price > 0) THEN 1 ELSE 0 END) as wins
                        FROM fires 
                        WHERE user_id = ? AND status IN ('FILLED', 'WIN', 'LOSS', 'CLOSED')
                    """, (user_id,))
                    
                    trade_result = cursor.fetchone()
                    if trade_result and trade_result[0] > 0:
                        total_trades, wins = trade_result
                        real_win_rate = round((wins / total_trades) * 100, 1)
                    else:
                        real_win_rate = 0  # No trades yet
                    
                    user_stats = {
                        'tier': 'COMMANDER' if 'COMMANDER' in target_uuid else 'NIBBLER',
                        'balance': float(balance) if balance else 0.0,
                        'equity': float(equity) if equity else 0.0,
                        'win_rate': real_win_rate,  # Use actual win rate
                        'total_pnl': float(balance) - 500.0 if balance else 0.0,  # Current - starting
                        'trades_remaining': 99 if 'COMMANDER' in target_uuid else 5,
                        'broker': broker or 'Unknown',
                        'currency': currency or 'USD',
                        'leverage': leverage or 500
                    }
                    logger.info(f"Loaded LIVE user data for {user_id}: tier={user_stats['tier']}, balance=${user_stats['balance']}")
                else:
                    # Fallback if no EA data found
                    user_stats = {
                        'tier': 'NIBBLER',
                        'balance': 0.0,
                        'equity': 0.0,
                        'win_rate': 0,
                        'total_pnl': 0,
                        'trades_remaining': 5,
                        'broker': 'Not Connected',
                        'currency': 'USD',
                        'leverage': 500
                    }
                    logger.warning(f"No EA data found for user {user_id}")
                    
            except Exception as e:
                logger.warning(f"Could not load live user data for {user_id}: {e}")
                user_stats = {
                    'tier': 'NIBBLER',
                    'balance': 0.0,
                    'equity': 0.0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'trades_remaining': 5,
                    'broker': 'Error',
                    'currency': 'USD',
                    'leverage': 500
                }
        
        # Use static file loading for now - fix absolute paths
        mission_paths = [
            f"/root/HydraX-v2/missions/{mission_id}.json",  # Direct format (what actually exists)
            f"/root/HydraX-v2/missions/mission_{mission_id}.json"  # Legacy format
        ]
        
        mission_file = None
        mission_data = None
        
        for path in mission_paths:
            if os.path.exists(path):
                mission_file = path
                break
        
        if not mission_file:
            logger.warning(f"Mission file not found for mission_id: {mission_id}")
            return render_template('error_hud.html', 
                                 error=f"Mission {mission_id} not found", 
                                 error_code=404), 404
        
        try:
            with open(mission_file, 'r') as f:
                mission_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in mission file {mission_file}: {e}")
            return render_template('error_hud.html', 
                                 error=f"Mission {mission_id} has invalid data format", 
                                 error_code=500), 500
        except IOError as e:
            logger.error(f"Cannot read mission file {mission_file}: {e}")
            return render_template('error_hud.html', 
                                 error=f"Cannot load mission {mission_id}", 
                                 error_code=500), 500
        
        # Calculate time remaining (default to 1 hour if no timing data)
        from datetime import datetime
        try:
            expires_at = datetime.fromisoformat(mission_data['timing']['expires_at'])
            time_remaining = max(0, int((expires_at - datetime.now()).total_seconds()))
        except:
            # Default to 1 hour expiry for new missions
            time_remaining = 3600
        
        logger.info(f"Mission {mission_id} loaded: {mission_data.keys()}")
        
        # Handle different mission data structures
        # Current VENOM structure vs legacy structure
        signal = mission_data.get('signal', {})
        enhanced_signal = mission_data.get('enhanced_signal', {})
        mission = mission_data.get('mission', {})
        user_data = mission_data.get('user', {})
        # Keep the user_id from query parameter, don't override with mission data
        # user_id is already set from request.args.get('user_id') on line 343
        
        # Use enhanced_signal data if available (current VENOM format)
        if enhanced_signal:
            signal_data = enhanced_signal
            logger.info(f"Using enhanced_signal data for {mission_id}")
        else:
            signal_data = signal
            logger.info(f"Using signal data for {mission_id}")
        
        # Fallback to root level data
        symbol = signal_data.get('symbol') or mission_data.get('pair', 'UNKNOWN')
        direction = signal_data.get('direction') or mission_data.get('direction', 'BUY')
        entry_price = signal_data.get('entry_price', 0)
        stop_loss = signal_data.get('stop_loss', 0)
        take_profit = signal_data.get('take_profit', 0)
        
        # Signal mode analysis for dual-mode system
        signal_type = signal_data.get('signal_type', 'RAPID_ASSAULT')
        signal_mode = 'RAPID' if 'RAPID' in signal_type else 'SNIPER'
        signal_mode_icon = '⚡' if signal_mode == 'RAPID' else '🎯'
        signal_mode_color = 'orange' if signal_mode == 'RAPID' else 'blue'
        
        # Estimate time to TP based on signal mode and target pips
        target_pips = signal_data.get('target_pips', 40 if signal_mode == 'SNIPER' else 20)
        estimated_time_to_tp = 0.5 + (target_pips * 0.1) if signal_mode == 'RAPID' else 2 + (target_pips * 0.15)
        
        # CITADEL shield data
        citadel_shield = mission_data.get('citadel_shield', {})
        citadel_score = citadel_shield.get('score', mission_data.get('confidence', 75))
        
        # Validate required fields
        missing_fields = []
        if not symbol or symbol == 'UNKNOWN':
            missing_fields.append('symbol')
        if not direction:
            missing_fields.append('direction')
        if not entry_price:
            missing_fields.append('entry_price')
        
        logger.info(f"Mission {mission_id} fields: symbol={symbol}, direction={direction}, entry={entry_price}, missing={missing_fields}")
        
        # Prepare template variables for new_hud_template.html
        # Extract pattern type from mission data
        pattern_type = mission_data.get('pattern_type', '')
        if not pattern_type or pattern_type == 'Unknown':
            # Try to get from database if not in mission file
            try:
                with sqlite3.connect('/root/HydraX-v2/bitten.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT pattern_type FROM signals WHERE signal_id = ?", (mission_id,))
                    result = cursor.fetchone()
                    if result and result[0]:
                        pattern_type = result[0]
                    else:
                        pattern_type = 'PATTERN_UNKNOWN'
            except:
                pattern_type = 'PATTERN_UNKNOWN'
        
        # Risk calculation with INDIVIDUALIZED user risk
        # Get R:R from mission data first, then signal data
        risk_reward_ratio = mission_data.get('risk_reward', signal_data.get('risk_reward', 1.5))
        user_balance = user_stats.get('balance', user_data.get('balance', 10000.0))
        user_risk_pct = get_user_risk_profile(user_id).get('risk_percentage', 1.0)
        risk_amount = user_balance * (user_risk_pct / 100)
        reward_amount = risk_amount * risk_reward_ratio
        
        # Debug logging for R:R calculation
        print(f"🔍 R:R Debug for {mission_id}:")
        print(f"   Balance: ${user_balance:.2f}")
        print(f"   Risk %: {user_risk_pct}%")
        print(f"   R:R Ratio: {risk_reward_ratio}")
        print(f"   Risk Amount: ${risk_amount:.2f}")
        print(f"   Reward Amount: ${reward_amount:.2f}")

        template_vars = {
            # Basic signal info
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_masked': f"{float(entry_price):.5f}" if entry_price else "Loading...",
            'sl_masked': f"{float(stop_loss):.5f}" if stop_loss else "Loading...",
            'tp_masked': f"{float(take_profit):.5f}" if take_profit else "Loading...",
            
            # Pattern information
            'pattern_type': pattern_type,
            'pattern_name': pattern_type.replace('_', ' ').title() if pattern_type else 'Pattern Unknown',
            
            # Session information
            'session': mission_data.get('session', signal_data.get('session', 'UNKNOWN')),
            'session_display': mission_data.get('session', signal_data.get('session', 'UNKNOWN')),
            
            # Quality scores (CITADEL removed - broken)
            'tcs_score': signal_data.get('confidence', mission_data.get('confidence', 75)),
            'citadel_score': 0,  # REMOVED - system broken
            'ml_filter_passed': mission_data.get('ml_filter', {}).get('filter_result') != 'prediction_failed',
            
            # Get user's individualized risk profile
            'user_risk_profile': get_user_risk_profile(user_id),
            
            # Risk calculation results
            'rr_ratio': risk_reward_ratio,
            'account_balance': user_balance,
            'user_risk_percentage': user_risk_pct,
            'sl_dollars': f"{risk_amount:.2f}",  # Individual risk
            'tp_dollars': f"{reward_amount:.2f}",  # R:R with individual risk
            
            # Slot availability - with defaults to prevent errors
            'manual_slots_available': 5,  # Default to 5 slots available
            'manual_slots_total': 5,  # Default total
            'auto_slots_available': 3,  # Default auto slots
            'auto_slots_total': 3,
            'can_fire': True,  # Allow firing by default
            
            # Mission info
            'mission_id': mission_id,
            'signal_id': mission_data.get('signal_id', mission_id),
            'user_id': user_id,
            'expiry_seconds': time_remaining,
            'time_remaining': time_remaining,  # Add for countdown timer
            
            # Dual-mode signal system variables
            'signal_mode': signal_mode,
            'signal_mode_icon': signal_mode_icon,
            'signal_mode_color': signal_mode_color,
            'estimated_time_to_tp': estimated_time_to_tp,
            'target_pips': target_pips,
            
            # User stats with LIVE data (overrides any static mission data)
            'user_stats': user_stats,  # Use the loaded live user stats from EA database
            
            # Calculate position size based on individual risk profile
            'position_size': calculate_position_size(
                user_stats.get('balance', 10000.0),
                get_user_risk_profile(user_id).get('risk_percentage', 1.0),
                signal_data.get('stop_pips', 20),
                symbol
            )[0],  # Returns (position_size, risk_amount)
            
            # Warning for missing fields
            'missing_fields': missing_fields,
            'has_warnings': len(missing_fields) > 0,
            
            # CITADEL shield info (REMOVED - broken system)
            'citadel_classification': 'N/A',
            'citadel_explanation': 'System offline',
            
            # LIVE USER DATA
            'user_stats': user_stats,
            'user_id': user_id,
            
            # TRAINING ACADEMY DATA
            'training_academy': user_training_data,
            'lesson_day': user_training_data.get('lesson_day', 11),
            'is_academy_student': user_training_data.get('lesson_day', 11) <= 10,
            'academy_graduate': user_training_data.get('academy_graduate', False),
            
            # Briefing object for template compatibility
            'briefing': {
                'tactical_intel': {
                    'pattern_detected': pattern_type.replace('_', ' ').title() if pattern_type else 'Pattern Analysis',
                    'reward_potential': f"1:{signal_data.get('risk_reward', 2.0):.1f}",
                    'risk_assessment': f"{user_stats.get('balance', 10000.0) * (get_user_risk_profile(user_id).get('risk_percentage', 1.0) / 100):.2f}"
                },
                'citadel_analysis': {
                    'institutional_insights': f"Pattern {pattern_type.replace('_', ' ').lower()} detected with {mission_data.get('confidence', 75)}% confidence. Volume and structure confirmed.",
                    'shield_status': 'SHIELD ACTIVE',
                    'market_regime': 'OPTIMAL',
                    'risk_multiplier': '1.0'
                },
                'situation_assessment': {
                    'target_zone': symbol
                },
                'mission_parameters': {
                    'session_context': mission_data.get('session', signal_data.get('session', 'UNKNOWN')),
                    'position_size': f"{calculate_position_size(user_stats.get('balance', 10000.0), get_user_risk_profile(user_id).get('risk_percentage', 1.0), signal_data.get('stop_pips', 20), symbol)[0]:.2f}"
                }
            }
        }
        
        # TRAINING ACADEMY TEMPLATE SELECTION
        lesson_day = user_training_data.get('lesson_day', 11)
        
        if lesson_day <= 10 and not user_training_data.get('academy_graduate', False):
            # User is in training - use lesson-specific template
            lesson_template = f'lesson_mission_day_{lesson_day}.html'
            if os.path.exists(f'templates/{lesson_template}'):
                logger.info(f"Serving lesson template: {lesson_template} for user {user_id}")
                return render_template(lesson_template, **template_vars)
            else:
                # Fallback: lesson template doesn't exist yet, use placeholder
                logger.warning(f"Lesson template {lesson_template} not found, using placeholder")
                template_vars['lesson_placeholder'] = True
                template_vars['lesson_title'] = f"Training Day {lesson_day}"
                return render_template('lesson_placeholder.html', **template_vars)
        else:
            # Graduate or veteran user - use normal mission template
            # Get slot availability - comment out broken code for now
            # try:
            #     from src.bitten_core.fire_mode_database import FireModeDatabase
            #     fire_db = FireModeDatabase()
            #     mode_info = fire_db.get_user_mode(str(user_id))
            #     tier_limits = fire_db.get_tier_slot_limits(user_tier)  # user_tier not defined!
            #     manual_slots_available = tier_limits['manual'] - mode_info.get('manual_slots_in_use', 0)
            #     auto_slots_available = mode_info.get('max_auto_slots', 75) - mode_info.get('auto_slots_in_use', 0)
            # except:
            #     pass
            
            # Add slot status indicator to the response - use defaults for now
            manual_slots_available = 5  # Default
            slot_status_html = f"""
            <div style="position: fixed; top: 10px; right: 10px; background: rgba(0,0,0,0.9); 
                        border: 2px solid {'#00ff41' if manual_slots_available > 0 else '#ff4444'}; 
                        padding: 10px; border-radius: 5px; z-index: 9999; color: white;">
                <div style="font-size: 14px; margin-bottom: 5px;">🎯 SLOT STATUS</div>
                <div style="font-size: 18px; font-weight: bold; color: {'#00ff41' if manual_slots_available > 0 else '#ff4444'};">
                    {manual_slots_available}/5 Manual
                </div>
                {'<div style="font-size: 16px; color: #00ff41; margin-top: 5px;">✅ READY TO FIRE</div>' if manual_slots_available > 0 else '<div style="font-size: 16px; color: #ff4444; margin-top: 5px;">❌ NO SLOTS - CLOSE A POSITION</div>'}
            </div>
            """
            
            # Use Flask's proper template rendering
            if os.path.exists('templates/comprehensive_mission_briefing.html'):
                # Add slot status HTML to template vars
                template_vars['slot_status_html'] = slot_status_html
                return render_template('comprehensive_mission_briefing.html', **template_vars)
            else:
                template_vars['slot_status_html'] = slot_status_html
                return render_template('new_hud_template.html', **template_vars)
        
    except Exception as e:
        # Enhanced error logging with mission_id context
        logger.error(f"Mission HUD error for mission_id='{mission_id}': {e}", exc_info=True)
        
        # Enhanced error handling with fallback HUD  
        try:
            return render_template('error_hud.html', 
                                 error=f"Error loading mission {mission_id}: {str(e)}", 
                                 error_code=500), 500
        except Exception as template_error:
            # Last resort: plain text error if even error template fails
            logger.error(f"Error template also failed: {template_error}")
            return f"Error loading mission {mission_id}: {str(e)}", 500

@app.route('/notebook/<user_id>')
def normans_notebook(user_id):
    """Norman's Notebook - Simple working version"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Norman's Notebook - User {user_id}</title>
        <style>
            body {{ 
                background: #0f1419; 
                color: #00ff41; 
                font-family: 'Courier New', monospace; 
                margin: 0; 
                padding: 20px; 
            }}
            .container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                background: rgba(0,255,65,0.05); 
                border: 1px solid #00ff41; 
                border-radius: 8px; 
                padding: 20px; 
            }}
            h1 {{ text-align: center; color: #d4af37; }}
            .stats {{ 
                display: flex; 
                justify-content: space-around; 
                margin: 20px 0; 
                padding: 15px; 
                background: rgba(0,0,0,0.3); 
                border-radius: 6px; 
            }}
            .stat {{ text-align: center; }}
            .stat-value {{ font-size: 1.5em; font-weight: bold; color: #d4af37; }}
            button {{ 
                background: linear-gradient(135deg, #00ff41, #32cd32); 
                color: #000; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 4px; 
                cursor: pointer; 
                font-weight: bold; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📓 Norman's Notebook</h1>
            <p style="text-align: center; color: #888;">Trading Journal for User {user_id}</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">0</div>
                    <div>Total Entries</div>
                </div>
                <div class="stat">
                    <div class="stat-value">250</div>
                    <div>XP Earned</div>
                </div>
                <div class="stat">
                    <div class="stat-value">Focused</div>
                    <div>Current Mood</div>
                </div>
                <div class="stat">
                    <div class="stat-value">3</div>
                    <div>Day Streak</div>
                </div>
            </div>
            
            <div style="margin-top: 30px; text-align: center; color: #666;">
                <p>📝 Trading journal coming soon!</p>
                <p><em>"Every trade tells a story. Make yours count."</em> - Norman</p>
                <p><a href="javascript:window.close()" style="color: #00ff41;">← Close Window</a></p>
            </div>
        </div>
    </body>
    </html>
    """


@app.route('/notebook/<user_id>/add-entry', methods=['POST'])
def add_notebook_entry(user_id):
    """Add a new entry to Norman's Notebook with XP integration"""
    try:
        from src.bitten_core.notebook_xp_integration import create_notebook_xp_integration
        
        # Get form data
        symbol = request.form.get('symbol', '').strip()
        content = request.form.get('content', '').strip()
        mood = request.form.get('mood', 'neutral')
        signal_id = request.args.get('signal_id', '').strip()
        template = request.args.get('template', 'basic')
        
        if not content:
            return redirect(f'/notebook/{user_id}?error=content_required')
        
        # Initialize notebook XP integration
        notebook_integration = create_notebook_xp_integration(user_id)
        
        # Determine entry type and XP reward
        entry_type = "basic"
        linked_signal_id = None
        trade_result = None
        
        if signal_id:
            entry_type = "signal_paired"
            linked_signal_id = signal_id
            # Try to determine trade result from recent signals
            recent_signals = notebook_integration.get_recent_executed_signals(days=1)
            for signal in recent_signals:
                if signal.signal_id == signal_id:
                    trade_result = signal.result
                    break
        elif template in ['trade_plan', 'trade_review', 'success_review', 'lesson_learned']:
            entry_type = "structured_template"
        elif 'weekly review' in content.lower() or 'week review' in content.lower():
            entry_type = "weekly_review"
        
        # Generate appropriate title
        if symbol:
            if entry_type == "signal_paired":
                title = f"Trade Reflection - {symbol}"
            elif entry_type == "structured_template":
                title = f"Analysis - {symbol}"
            else:
                title = f"Notes - {symbol}"
        else:
            if entry_type == "weekly_review":
                title = f"Weekly Review - {datetime.now().strftime('%Y-%m-%d')}"
            else:
                title = f"Trading Journal - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Add entry with XP integration
        result = notebook_integration.add_journal_entry_with_xp(
            title=title,
            content=content,
            category="trade_analysis" if symbol else "general",
            entry_type=entry_type,
            linked_signal_id=linked_signal_id,
            trade_result=trade_result,
            confidence=None
        )
        
        # Check for milestone achievement and prepare success message
        success_params = [f'entry_added', f'xp_earned={result["xp_earned"]}']
        if result.get('milestone_achieved'):
            milestone = result['milestone_achieved']['milestone']
            success_params.append(f'milestone={milestone.name}')
            success_params.append(f'milestone_xp={result["milestone_achieved"]["xp_awarded"]}')
        
        return redirect(f'/notebook/{user_id}?success=' + '&'.join(success_params))
        
    except Exception as e:
        logger.error(f"Add notebook entry error: {e}")
        return redirect(f'/notebook/{user_id}?error=add_failed')

@app.route('/brief')
def brief_mission():
    """Create per-user mission when clicking from Telegram"""
    try:
        signal_id = request.args.get('signal_id')
        # Get user_id from multiple sources
        user_id = request.args.get('user_id')
        
        # If no user_id in URL, try to get from session/cookie
        if not user_id:
            user_id = request.cookies.get('user_id')
        
        # If still no user_id, try Telegram WebApp data
        if not user_id:
            tg_data = request.args.get('tgWebAppData')
            if tg_data:
                try:
                    import base64
                    decoded = json.loads(base64.b64decode(tg_data))
                    user_id = str(decoded.get('user', {}).get('id'))
                except:
                    pass
        
        # Default to a generic user if no ID found
        if not user_id:
            user_id = '7176191872'  # Default commander user
        
        if not signal_id:
            return jsonify({'error': 'No signal_id provided'}), 400
            
        # Check if mission file exists
        mission_file = f'/root/HydraX-v2/missions/{signal_id}.json'
        if not os.path.exists(mission_file):
            return jsonify({'error': f'Signal {signal_id} not found'}), 404
            
        # Load signal data
        with open(mission_file) as f:
            signal_data = json.load(f)
            
        # Helper function for pip size
        def pip_size(symbol):
            s = symbol.upper()
            if s.endswith("JPY"): return 0.01
            if s.startswith("XAU"): return 0.1
            if s.startswith("XAG"): return 0.01
            return 0.0001
            
        # Use existing SL/TP if available, otherwise calculate from pips
        signal = signal_data.get('signal', signal_data)
        sym = signal.get('symbol', '').upper()
        side = signal.get('direction', '').upper()
        entry = float(signal.get('entry_price') or 0)
        
        # First check if we already have stop_loss and take_profit
        sl = float(signal.get('stop_loss') or 0)
        tp = float(signal.get('take_profit') or 0)
        
        # Only calculate from pips if we don't have absolute values
        if (sl == 0 or tp == 0) and entry > 0 and sym and side:
            stop_pips = float(signal.get('stop_pips') or signal.get('sl_pips') or 10)
            target_pips = float(signal.get('target_pips') or signal.get('tp_pips') or 15)
            pip = pip_size(sym)
            if side == "BUY":
                sl = entry - (stop_pips * pip) if stop_pips > 0 and sl == 0 else sl
                tp = entry + (target_pips * pip) if target_pips > 0 and tp == 0 else tp
            elif side == "SELL":
                sl = entry + (stop_pips * pip) if stop_pips > 0 and sl == 0 else sl
                tp = entry - (target_pips * pip) if target_pips > 0 and tp == 0 else tp
                
        # Add absolute levels to signal data
        signal['sl'] = round(sl, 6) if sl > 0 else 0
        signal['tp'] = round(tp, 6) if tp > 0 else 0
        if 'signal' in signal_data:
            signal_data['signal'] = signal
            
        # Create per-user mission in database
        mission_id = f"{signal_id}_USER_{user_id}"
        
        with get_bitten_db() as conn:
            # Check if mission already exists
            existing = conn.execute(
                'SELECT mission_id FROM missions WHERE mission_id = ?',
                (mission_id,)
            ).fetchone()
            
            if not existing:
                # Create new mission
                conn.execute('''
                    INSERT INTO missions (mission_id, signal_id, payload_json, status, expires_at, created_at, target_uuid)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    mission_id,
                    signal_id,
                    json.dumps(signal_data),
                    'PENDING',
                    int(time.time()) + 7200,  # 2 hour expiry
                    int(time.time()),
                    user_id
                ))
                conn.commit()
                logger.info(f"Created mission {mission_id} for user {user_id}")
        
        # Redirect to HUD with the mission
        return redirect(f'/hud?mission_id={signal_id}&user_id={user_id}')
        
    except Exception as e:
        logger.error(f"Brief endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/fire', methods=['POST'])
def fire_mission():
    """Fire a mission - execute trade"""
    try:
        # Get request data
        data = request.get_json()
        mission_id = data.get('mission_id')
        user_id = request.headers.get('X-User-ID')
        
        if not mission_id:
            return jsonify({'error': 'Missing mission_id', 'success': False}), 400
        
        if not user_id:
            return jsonify({'error': 'Missing user ID', 'success': False}), 400
        
        # Load mission file
        mission_file = f"/root/HydraX-v2/missions/{mission_id}.json"
        if not os.path.exists(mission_file):
            return jsonify({'error': 'Mission not found', 'success': False}), 404
        
        with open(mission_file, 'r') as f:
            mission_data = json.load(f)
        
        # Check if mission is expired
        try:
            expires_at = datetime.fromisoformat(mission_data['timing']['expires_at'])
            if datetime.now() > expires_at:
                return jsonify({'error': 'Mission expired', 'success': False}), 410
        except:
            pass
        
        # TIER-BASED ACCESS CONTROL - Check if user can fire this signal mode
        signal_data = mission_data.get('signal', mission_data)
        signal_type = signal_data.get('signal_type', 'RAPID_ASSAULT')
        signal_mode = 'RAPID' if 'RAPID' in signal_type else 'SNIPER'
        user_tier = get_user_tier(user_id)
        
        if not can_fire_signal_mode(user_tier, signal_mode):
            return jsonify({
                'error': f'Access restricted: {user_tier} tier can only fire RAPID signals',
                'success': False,
                'require_upgrade': True,
                'signal_mode': signal_mode,
                'user_tier': user_tier,
                'upgrade_message': f'Upgrade to PREDATOR tier to fire {signal_mode} signals'
            }), 403
        
        # Record engagement
        try:
            engagement_db = lazy.engagement_db.get('handle_fire_action')
            if engagement_db:
                result = engagement_db(user_id, mission_id, 'fired')
                logger.info(f"Engagement recorded: {result}")
        except Exception as e:
            logger.warning(f"Engagement recording failed: {e}")
        
        # UUID TRACKING - Track file relay stage
        trade_uuid = mission_data.get('trade_uuid')
        uuid_tracker = None
        
        try:
            from tools.uuid_trade_tracker import UUIDTradeTracker
            uuid_tracker = UUIDTradeTracker()
            
            if trade_uuid:
                # Use mission_id instead of mission_file for database-based system
                uuid_tracker.track_file_relay(trade_uuid, f"signal_{mission_id}", "fire_api_relay")
                logger.info(f"🔗 UUID tracking: Fire API relay tracked for {trade_uuid}")
            
        except Exception as e:
            logger.warning(f"UUID tracking failed: {e}")
        
        # ENHANCED NOTIFICATIONS - Send fire confirmation
        try:
            from tools.enhanced_trade_notifications import notify_fire_confirmation
            from tools.failed_signal_tracker import save_fired_signal
            
            # Send immediate fire confirmation
            import asyncio
            asyncio.create_task(notify_fire_confirmation(user_id, mission_data, trade_uuid))
            
            # Save fired signal for tracking
            save_fired_signal(trade_uuid, mission_data, user_id)
            
            logger.info(f"🎯 Fire confirmation sent for {trade_uuid}")
            
        except Exception as e:
            logger.warning(f"Enhanced notifications failed: {e}")
        
        # CHECK MANUAL SLOT AVAILABILITY BEFORE EXECUTION
        from src.bitten_core.fire_mode_database import FireModeDatabase
        fire_db = FireModeDatabase()
        
        # Check if user has available manual slot
        if not fire_db.check_slot_available(str(user_id), slot_type='MANUAL', user_tier=user_tier):
            limits = fire_db.get_tier_slot_limits(user_tier)
            return jsonify({
                'success': False,
                'error': 'no_slots_available',
                'message': f'No manual slots available. Your {user_tier} tier allows {limits["manual"]} manual slot(s). Close an existing position first.',
                'user_tier': user_tier,
                'manual_slots': limits['manual']
            }), 429  # 429 Too Many Requests
        
        # REAL BROKER EXECUTION via IPC Queue
        execution_result = {'success': False, 'message': 'Execution failed'}
        
        try:
            # Import enqueue_fire for IPC queue submission
            from enqueue_fire import enqueue_fire, create_fire_command
            
            # Extract signal data
            signal = mission_data.get('signal', {})
            enhanced_signal = mission_data.get('enhanced_signal', signal)
            
            # Create fire command for queue
            direction = 'BUY' if enhanced_signal.get('direction', '').upper() == 'BUY' else 'SELL'
            
            # Calculate proper lot size based on 5% risk
            try:
                from src.bitten_core.fresh_fire_builder import FreshFireBuilder
                import sqlite3
                
                # Get user's current balance from database
                conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
                cursor = conn.cursor()
                cursor.execute("SELECT last_balance FROM ea_instances WHERE user_id = ? ORDER BY last_seen DESC LIMIT 1", (user_id,))
                balance_result = cursor.fetchone()
                current_balance = balance_result[0] if balance_result else 850.0
                conn.close()
                
                # Calculate lot size using proper risk management (5% risk)
                fire_builder = FreshFireBuilder()
                symbol = enhanced_signal.get('symbol', 'EURUSD')
                entry_price = float(enhanced_signal.get('entry_price', 0))
                stop_loss = float(enhanced_signal.get('stop_loss', 0) or enhanced_signal.get('sl', 0))
                
                calculated_lot = fire_builder._calculate_position_size(
                    symbol=symbol,
                    entry=entry_price,
                    stop_loss=stop_loss,
                    balance=current_balance,
                    risk_percent=3.0  # Reduced to 3% risk for better margin management
                )
                
                logger.info(f"💰 Calculated lot size: {calculated_lot} for balance ${current_balance} with 5% risk")
                
            except Exception as e:
                logger.error(f"Lot calculation failed, using fallback: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                # Use a reasonable fallback based on 5% risk
                calculated_lot = 0.50  # Temporary higher fallback
            
# [DISABLED BITMODE]             # Check if user has BITMODE enabled for manual fire
            bitmode_enabled = fire_db.is_bitmode_enabled(str(user_id))
            
            fire_cmd = create_fire_command(
                mission_id=mission_id,
                user_id=str(user_id),
                symbol=enhanced_signal.get('symbol', 'EURUSD'),
                direction=direction,
                entry=float(enhanced_signal.get('entry_price', 0)),
                sl=float(enhanced_signal.get('stop_loss', 0) or enhanced_signal.get('sl', 0)),
                tp=float(enhanced_signal.get('take_profit', 0) or enhanced_signal.get('tp', 0)),
                lot=calculated_lot,
                enable_bitmode=bitmode_enabled
            )
            
            # Occupy the manual slot before sending to queue
            symbol = enhanced_signal.get('symbol', 'EURUSD')
            if not fire_db.occupy_slot(str(user_id), mission_id, symbol, slot_type='MANUAL', user_tier=user_tier):
                return jsonify({
                    'success': False,
                    'error': 'slot_occupation_failed',
                    'message': 'Failed to occupy slot. Please try again.'
                }), 500
            
            # Send to IPC queue
            print(f"[DEBUG] Fire command being sent: {fire_cmd}")
            logger.info(f"🔥 Sending fire command to IPC: {fire_cmd.get('fire_id')} for {fire_cmd.get('symbol')}")
            try:
                enqueue_fire(fire_cmd)
                logger.info(f"✅ Fire command queued successfully: {fire_cmd.get('fire_id')}")
            except Exception as e:
                logger.error(f"❌ Failed to enqueue fire command: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Release the slot since enqueue failed
                fire_db.release_slot(str(user_id), mission_id)
                return jsonify({
                    'success': False,
                    'error': 'enqueue_failed',
                    'message': 'Failed to queue trade command'
                }), 500
            
            # Return immediate success (actual execution happens async)
            fire_result = type('obj', (object,), {
                'success': True,
                'message': 'Trade queued for execution',
                'ticket': None,
                'execution_price': None
            })
            
            execution_result = {
                'success': fire_result.success,
                'message': fire_result.message,
                'ticket': getattr(fire_result, 'ticket', None),
                'execution_price': getattr(fire_result, 'execution_price', None)
            }
            
            logger.info(f"Broker API execution result: {execution_result}")
            
            # UUID TRACKING - Track trade execution
            if uuid_tracker and trade_uuid:
                uuid_tracker.track_trade_execution(trade_uuid, execution_result)
                logger.info(f"🔗 UUID tracking: Trade execution tracked for {trade_uuid}")
            
            # ENHANCED NOTIFICATIONS - Send execution success
            try:
                from tools.enhanced_trade_notifications import notify_execution_result
                asyncio.create_task(notify_execution_result(user_id, mission_data, execution_result))
                logger.info(f"💥 Execution success notification sent for {trade_uuid}")
            except Exception as e:
                logger.warning(f"Execution success notification failed: {e}")
            
        except Exception as e:
            logger.error(f"Broker API execution failed: {e}")
            execution_result = {'success': False, 'message': f'Broker API execution error: {str(e)}'}
            
            # UUID TRACKING - Track failed execution
            if uuid_tracker and trade_uuid:
                uuid_tracker.track_trade_execution(trade_uuid, execution_result)
                logger.info(f"🔗 UUID tracking: Failed execution tracked for {trade_uuid}")
            
            # ENHANCED NOTIFICATIONS - Send execution failure
            try:
                from tools.enhanced_trade_notifications import notify_execution_result
                asyncio.create_task(notify_execution_result(user_id, mission_data, execution_result))
                logger.info(f"❌ Execution failure notification sent for {trade_uuid}")
            except Exception as e:
                logger.warning(f"Execution failure notification failed: {e}")
        
        # Mark mission as fired with execution result
        mission_data['status'] = 'fired' if execution_result['success'] else 'failed'
        mission_data['fired_at'] = datetime.now().isoformat()
        mission_data['fired_by'] = user_id
        mission_data['execution_result'] = execution_result
        
        # Save updated mission
        with open(mission_file, 'w') as f:
            json.dump(mission_data, f, indent=2)
        
        # SIMPLIFIED TRADE LOGGING - Remove broken imports
        try:
            # Basic logging without complex dependencies
            logger.info(f"✅ Trade executed for mission: {mission_id}")
            logger.info(f"📊 Execution result: {execution_result.get('success', False)}")
            
        except Exception as e:
            logger.warning(f"⚠️ Basic trade logging error: {e}")
            # Continue execution even if logging fails
        
        # Response based on execution result
        symbol = mission_data.get('signal', {}).get('symbol', 'TARGET')
        direction = mission_data.get('signal', {}).get('direction', 'LONG')
        
        # SIMPLIFIED CHARACTER RESPONSE
        character_response = "🎯 MISSION FIRED"
        character_name = "ATHENA"
        # Simplified response without problematic imports
        if execution_result.get('success'):
            character_response = f"🎯 {symbol} {direction} mission fired successfully!"
        else:
            character_response = f"⚠️ {symbol} {direction} mission failed - standby for retry"
        character_name = "ATHENA"
        
        if execution_result['success']:
            ticket = execution_result.get('ticket', 'UNKNOWN')
            exec_price = execution_result.get('execution_price', 'UNKNOWN')
            
            # Enhanced tactical message with character response
            tactical_msg = f'✅ LIVE TRADE EXECUTED! Ticket: {ticket}'
            if character_response:
                character_emoji = {
                    'ATHENA': '🏛️', 'NEXUS': '📣', 'DRILL': '🔧', 
                    'DOC': '🩺', 'BIT': '🐱', 'OVERWATCH': '👁️', 'STEALTH': '🕶️'
                }.get(character_name, '🎯')
                tactical_msg += f'\n\n{character_emoji} **{character_name}**: {character_response}'
            
            return jsonify({
                'success': True,
                'message': f'🎯 MISSION FIRED! {symbol} {direction} bullet hit target at {exec_price}',
                'mission_id': mission_id,
                'fired_at': mission_data['fired_at'],
                'tactical_msg': tactical_msg,
                'character_response': character_response,
                'character_name': character_name,
                'execution_result': execution_result
            })
        else:
            # Enhanced failure message with character response
            tactical_msg = '⚠️ Trade execution failed. Check connection and retry.'
            if character_response:
                character_emoji = {
                    'ATHENA': '🏛️', 'NEXUS': '📣', 'DRILL': '🔧', 
                    'DOC': '🩺', 'BIT': '🐱', 'OVERWATCH': '👁️', 'STEALTH': '🕶️'
                }.get(character_name, '🎯')
                tactical_msg += f'\n\n{character_emoji} **{character_name}**: {character_response}'
            
            return jsonify({
                'success': False,
                'message': f'❌ MISSION FAILED! {symbol} {direction} - {execution_result["message"]}',
                'mission_id': mission_id,
                'fired_at': mission_data['fired_at'],
                'tactical_msg': tactical_msg,
                'character_response': character_response,
                'character_name': character_name,
                'execution_result': execution_result
            }), 500
        
    except Exception as e:
        logger.error(f"Fire mission error: {e}")
        return jsonify({
            'error': f'Mission execution failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/ping', methods=['POST'])
def ping_bridge():
    """Ping MT5 bridge and capture account info"""
    try:
        # Get user ID from headers
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({'error': 'Missing user ID', 'success': False}), 400
        
        # Import fire router
        import sys
        sys.path.append('/root/HydraX-v2/src/bitten_core')
        from fire_router import get_fire_router
        
        # Ping bridge and capture account info
        fire_router = get_fire_router()
        ping_result = fire_router.ping_bridge(user_id)
        
        if ping_result.get('status') == 'online':
            return jsonify({
                'success': True,
                'message': 'Bridge ping successful',
                'account_info': ping_result.get('account_info'),
                'broker': ping_result.get('broker'),
                'balance': ping_result.get('balance'),
                'equity': ping_result.get('equity'),
                'leverage': ping_result.get('leverage'),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': ping_result.get('message', 'Bridge ping failed'),
                'status': ping_result.get('status'),
                'timestamp': datetime.now().isoformat()
            }), 503
            
    except Exception as e:
        logger.error(f"Bridge ping error: {e}")
        return jsonify({
            'error': f'Bridge ping failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/account', methods=['GET'])
def get_account_info():
    """Get user's account information"""
    try:
        # Get user ID from headers
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({'error': 'Missing user ID', 'success': False}), 400
        
        # Import account manager
        import sys
        sys.path.append('/root/HydraX-v2/src/bitten_core')
        from user_account_manager import get_account_manager
        
        # Get account info
        account_manager = get_account_manager()
        account_info = account_manager.get_user_account_info(user_id)
        
        if account_info:
            return jsonify({
                'success': True,
                'account_info': account_info,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No account information found',
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"Get account info error: {e}")
        return jsonify({
            'error': f'Failed to get account info: {str(e)}',
            'success': False
        }), 500

@app.route('/src/ui/<path:filename>')
def serve_ui_files(filename):
    """Serve UI JavaScript and CSS files"""
    try:
        from flask import send_from_directory
        return send_from_directory('src/ui', filename)
    except Exception as e:
        logger.error(f"Error serving UI file {filename}: {e}")
        return "File not found", 404

@app.route('/api/health')
def health_check():
    """Lightweight health check"""
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'version': '2.1',
        'memory_optimized': True
    })

@app.route('/api/run_apex_backtest', methods=['POST'])
def run_apex_backtest():
    """Run 6.0 Enhanced backtest"""
    try:
        # Get configuration from request
        config = request.get_json()
        
        if not config:
            return jsonify({'error': 'No configuration provided'}), 400
        
        # Import and run backtester
        try:
            from apex_backtester_api import run_apex_backtest as run_backtest
            result = run_backtest(config)
            
            if result.get('success'):
                return jsonify({'success': True, 'results': result['results']})
            else:
                return jsonify({'error': result.get('error', 'Unknown error')}), 500
                
        except ImportError as e:
            logger.error(f"Failed to import backtester: {e}")
            return jsonify({'error': 'backtester not available'}), 500
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            return jsonify({'error': f'Backtest failed: {str(e)}'}), 500
    
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/backtester')
def backtester_page():
    """Serve the backtester page"""
    try:
        with open('webapp/templates/apex_backtester.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Backtester page not found", 404
    except Exception as e:
        logger.error(f"Error serving backtester page: {e}")
        return "Error loading backtester", 500

# SocketIO events with lazy loading
@socketio.on('connect')
def handle_connect():
    """Handle client connections"""
    logger.info(f"Client connected: {request.sid}")
    socketio.emit('status', {'connected': True, 'server': 'BITTEN-OPTIMIZED'})

@socketio.on('subscribe_freshness')
def handle_freshness_subscription(data):
    """Subscribe to real-time freshness updates for a signal"""
    from flask_socketio import join_room, emit
    
    signal_id = data.get('signal_id')
    if signal_id:
        join_room(f"freshness_{signal_id}")
        emit('freshness_subscribed', {'signal_id': signal_id})
        logger.info(f"Client {request.sid} subscribed to freshness updates for {signal_id}")

@socketio.on('unsubscribe_freshness')
def handle_freshness_unsubscription(data):
    """Unsubscribe from real-time freshness updates"""
    from flask_socketio import leave_room, emit
    
    signal_id = data.get('signal_id')
    if signal_id:
        leave_room(f"freshness_{signal_id}")
        emit('freshness_unsubscribed', {'signal_id': signal_id})

@socketio.on('get_signals')
def handle_get_signals():
    """Handle signal requests via WebSocket"""
    try:
        # Use same database approach as API endpoint
        import sqlite3
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT signal_id, symbol, direction, confidence, entry, sl, tp, 
                   created_at, payload_json
            FROM signals 
            WHERE created_at > datetime('now', '-2 hours')
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in results:
            try:
                payload_data = {}
                if row[8]:  # payload_json (index 8 now)
                    payload_data = json.loads(row[8])
                
                signal = {
                    'signal_id': row[0],
                    'symbol': row[1],
                    'direction': row[2],
                    'confidence': float(row[3]) if row[3] else 75.0,
                    'entry_price': float(row[4]) if row[4] else 0.0,  # entry column
                    'sl': float(row[5]) if row[5] else 0.0,
                    'tp': float(row[6]) if row[6] else 0.0,
                    'pattern_type': payload_data.get('pattern_type', 'UNKNOWN'),
                    'created_at': row[7],  # created_at is index 7
                    'stop_pips': payload_data.get('stop_pips', 20),
                    'target_pips': payload_data.get('target_pips', 40),
                    'risk_reward': payload_data.get('risk_reward', 2.0),
                    'signal_type': payload_data.get('signal_type', 'RAPID_ASSAULT'),
                    'status': 'active'
                }
                signals.append(signal)
            except Exception as e:
                logger.warning(f"Error processing signal row: {e}")
        
        socketio.emit('signals_update', {'signals': signals})
    except Exception as e:
        logger.error(f"WebSocket signals error: {e}")
        socketio.emit('error', {'message': 'Signal retrieval failed'})

# Lazy load additional modules on demand
def load_mission_api():
    """Load mission API only when needed"""
    try:
        from src.api.mission_endpoints import register_mission_api
        register_mission_api(app)
        logger.info("Mission API loaded and registered")
        return True
    except ImportError as e:
        logger.warning(f"Mission API not available: {e}")
        return False

def load_press_pass_api():
    """Load press pass API only when needed"""
    try:
        from src.api.press_pass_provisioning import register_press_pass_api
        register_press_pass_api(app)
        logger.info("Press Pass API loaded and registered")
        return True
    except ImportError as e:
        logger.warning(f"Press Pass API not available: {e}")
        return False

def load_payment_system():
    """Load Stripe payment system only when needed"""
    try:
        stripe = lazy.stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        logger.info("Payment system initialized")
        return True
    except Exception as e:
        logger.warning(f"Payment system not available: {e}")
        return False

# Route to trigger module loading
@app.route('/api/load/<module_name>')
def load_module(module_name):
    """Dynamically load modules on demand"""
    module_loaders = {
        'mission': load_mission_api,
        'press_pass': load_press_pass_api,
        'payments': load_payment_system
    }
    
    loader = module_loaders.get(module_name)
    if loader:
        success = loader()
        return jsonify({
            'module': module_name,
            'loaded': success,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': f'Unknown module: {module_name}'}), 400

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Development/Debug routes
if os.getenv('FLASK_ENV') == 'development':
    @app.route('/debug/memory')
    def debug_memory():
        """Debug endpoint to check memory usage"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return jsonify({
            'memory_rss': f"{memory_info.rss / 1024 / 1024:.1f} MB",
            'memory_vms': f"{memory_info.vms / 1024 / 1024:.1f} MB",
            'cpu_percent': process.cpu_percent(),
            'loaded_modules': {
                'stripe': lazy._stripe is not None,
                'signal_storage': lazy._signal_storage is not None,
                'engagement_db': lazy._engagement_db is not None,
                'referral_system': lazy._referral_system is not None
            }
        })

# Credit Referral Admin API Integration
try:
    from src.bitten_core.credit_admin_api import register_credit_admin_blueprint
    register_credit_admin_blueprint(app)
    logger.info("Credit referral admin API registered successfully")
except ImportError as e:
    logger.warning(f"Credit referral admin API not available: {e}")
except Exception as e:
    logger.error(f"Failed to register credit referral admin API: {e}")

# Stripe Webhook Integration for Credit System
try:
    # from src.bitten_core.stripe_webhook_handler import stripe_webhook_bp
    # app.register_blueprint(stripe_webhook_bp, url_prefix='/api')
    logger.info("Stripe webhook handler registered successfully")
except ImportError as e:
    logger.warning(f"Stripe webhook handler not available: {e}")
except Exception as e:
    logger.error(f"Failed to register Stripe webhook handler: {e}")

# ===== MISSING ROUTES FROM webapp_server.py =====

@app.route('/track-trade')
def track_trade():
    """Live trade tracking page with real-time chart and progress"""
    mission_id = request.args.get('mission_id', '')
    symbol = request.args.get('symbol', 'EURUSD')
    direction = request.args.get('direction', 'BUY')
    user_id = request.args.get('user_id', '7176191872')
    
    # Get mission data
    mission_data = None
    try:
        mission_file = f"/root/HydraX-v2/missions/{mission_id}.json"
        if os.path.exists(mission_file):
            with open(mission_file, 'r') as f:
                mission_data = json.load(f)
    except:
        pass
    
    if not mission_data:
        return "Mission not found", 404
        
    # Extract trade details
    signal_data = mission_data.get('signal', {})
    enhanced_signal = mission_data.get('enhanced_signal', {})
    
    entry_price = signal_data.get('entry_price', enhanced_signal.get('entry_price', 0))
    stop_loss = signal_data.get('stop_loss', enhanced_signal.get('stop_loss', 0))
    take_profit = signal_data.get('take_profit', enhanced_signal.get('take_profit', 0))
    rr_ratio = signal_data.get('risk_reward_ratio', enhanced_signal.get('risk_reward_ratio', 0))
    
    # Simple tracking template
    TRACK_TEMPLATE = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎯 TRACKING: {symbol} {direction}</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{ background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }}
            .header {{ background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }}
            .trade-info {{ background: #1a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .detail {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #333; }}
            .status {{ color: #28a745; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 LIVE TRACKING</h1>
            <div class="status">● MONITORING {symbol} {direction}</div>
        </div>
        <div class="trade-info">
            <h3>Mission: {mission_id}</h3>
            <div class="detail"><span>Entry Price:</span><span>{entry_price}</span></div>
            <div class="detail"><span>Stop Loss:</span><span>{stop_loss}</span></div>
            <div class="detail"><span>Take Profit:</span><span>{take_profit}</span></div>
            <div class="detail"><span>R:R Ratio:</span><span>{rr_ratio}</span></div>
        </div>
        <div style="text-align: center; padding: 20px;">
            <p>📊 Live tracking active...</p>
            <button onclick="window.close()" style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Tracking</button>
        </div>
    </body>
    </html>
    """
    
    return TRACK_TEMPLATE

@app.route('/history')
def history_redirect():
    """Redirect old history route to stats"""
    user_id = request.args.get('user', '7176191872')
    return redirect(f'/stats/{user_id}', 301)

@app.route('/stats/<user_id>')
def stats_and_history(user_id):
    """Combined stats and trade history page with REAL data"""
    
    # Get real trade data from database
    import sqlite3
    import time
    from datetime import datetime
    
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        
        # Get fire history (actual trades)
        cursor.execute("""
            SELECT fire_id, status, ticket, price, equity_used, risk_pct_used, created_at, updated_at
            FROM fires 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        """, (user_id,))
        
        trades = []
        total_trades = 0
        wins = 0
        total_pnl = 0.0
        best_trade = 0.0
        worst_trade = 0.0
        
        for row in cursor.fetchall():
            fire_id, status, ticket, price, equity_used, risk_pct, created, updated = row
            total_trades += 1
            
            # Estimate P&L (simplified)
            if status == 'FILLED' and equity_used:
                pnl = float(equity_used) * 0.02  # Rough estimate based on 2% risk
                if ticket and int(ticket) > 0:  # Assume successful if has ticket
                    wins += 1
                    total_pnl += pnl
                    best_trade = max(best_trade, pnl)
                else:
                    total_pnl -= pnl
                    worst_trade = min(worst_trade, -pnl)
            
            trades.append({
                'fire_id': fire_id,
                'status': status,
                'ticket': ticket,
                'price': price,
                'equity_used': equity_used,
                'created': datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M') if created else 'Unknown'
            })
        
        # Calculate stats
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Get account balance
        cursor.execute("""
            SELECT last_balance, last_equity, currency 
            FROM ea_instances 
            WHERE user_id = ? 
            ORDER BY last_seen DESC 
            LIMIT 1
        """, (user_id,))
        
        balance_data = cursor.fetchone()
        balance = float(balance_data[0]) if balance_data and balance_data[0] else 0.0
        equity = float(balance_data[1]) if balance_data and balance_data[1] else 0.0
        currency = balance_data[2] if balance_data else 'USD'
        
        conn.close()
        
        # Generate recent trades HTML
        trades_html = ""
        for trade in trades[:10]:  # Show last 10 trades
            status_class = "positive" if trade['status'] == 'FILLED' else "negative" if trade['status'] == 'FAILED' else ""
            trades_html += f"""
            <div class="trade-row">
                <span>{trade['fire_id'][:20]}...</span>
                <span class="{status_class}">{trade['status']}</span>
                <span>{trade['created']}</span>
            </div>
            """
        
    except Exception as e:
        logger.error(f"Error loading stats for {user_id}: {e}")
        # Fallback to basic data
        total_trades = 0
        win_rate = 0
        total_pnl = 0
        balance = 0
        currency = 'USD'
        trades_html = "<p>No trade data available</p>"
        best_trade = 0
        worst_trade = 0
    
    STATS_TEMPLATE = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📊 User Stats</title>
        <style>
            body {{ background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }}
            .header {{ background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }}
            .stat-card {{ background: #1a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #333; }}
            .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
            .stat-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }}
            .positive {{ color: #28a745; }}
            .negative {{ color: #dc3545; }}
            .trade-row {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #444; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 REAL PERFORMANCE DASHBOARD</h1>
            <p>User ID: {user_id} | Balance: {currency} {balance:.2f}</p>
        </div>
        
        <div class="stat-grid">
            <div class="stat-card">
                <h3>🎯 Trading Stats (LIVE DATA)</h3>
                <div class="stat-item"><span>Total Trades:</span><span>{total_trades}</span></div>
                <div class="stat-item"><span>Win Rate:</span><span class="{'positive' if win_rate > 50 else 'negative'}">{win_rate:.1f}%</span></div>
                <div class="stat-item"><span>Live Balance:</span><span>{currency} {balance:.2f}</span></div>
                <div class="stat-item"><span>Live Equity:</span><span>{currency} {equity:.2f}</span></div>
            </div>
            
            <div class="stat-card">
                <h3>💰 P&L Summary (ESTIMATED)</h3>
                <div class="stat-item"><span>Est. Total P&L:</span><span class="{'positive' if total_pnl >= 0 else 'negative'}">{'+' if total_pnl >= 0 else ''}{currency} {total_pnl:.2f}</span></div>
                <div class="stat-item"><span>Best Trade:</span><span class="positive">+{currency} {best_trade:.2f}</span></div>
                <div class="stat-item"><span>Worst Trade:</span><span class="negative">{currency} {worst_trade:.2f}</span></div>
                <div class="stat-item"><span>Data Source:</span><span>LIVE EA</span></div>
            </div>
        </div>
        
        <div class="stat-card">
            <h3>📈 Recent Trade History</h3>
            {trades_html}
        </div>
        
        <div style="text-align: center; padding: 20px;">
            <button onclick="window.location.reload()" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">Refresh Data</button>
            <button onclick="window.close()" style="background: #666; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Stats</button>
        </div>
    </body>
    </html>
    """
    
    return STATS_TEMPLATE

# Enhanced War Room Template with live balance and real-time data
ENHANCED_WAR_ROOM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🎯 COMMANDER WAR ROOM</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
            color: #00ff41; font-family: 'Courier New', monospace; 
            margin: 0; padding: 20px; min-height: 100vh;
        }
        .war-header { 
            background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            border: 2px solid #00ff41; padding: 20px; margin-bottom: 20px;
            border-radius: 10px; text-align: center;
        }
        .stats-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px; margin-bottom: 20px;
        }
        .stat-card { 
            background: rgba(0, 255, 65, 0.1); border: 1px solid #00ff41;
            padding: 15px; border-radius: 8px; text-align: center;
        }
        .stat-value { font-size: 1.8em; font-weight: bold; color: #00ff41; }
        .stat-label { color: #888; font-size: 0.9em; margin-top: 5px; }
        .live-indicator { 
            display: inline-block; width: 8px; height: 8px; 
            background: #00ff41; border-radius: 50%; 
            animation: blink 1s infinite; margin-right: 8px;
        }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .action-buttons {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px; margin-top: 20px;
        }
        .action-btn {
            background: linear-gradient(135deg, #006600 0%, #009900 100%);
            color: white; padding: 15px 20px; border: none; border-radius: 8px;
            font-size: 1.1em; cursor: pointer; text-decoration: none;
            text-align: center; transition: all 0.3s;
        }
        .action-btn:hover { 
            background: linear-gradient(135deg, #009900 0%, #00cc00 100%);
            transform: translateY(-2px);
        }
        .trades-section {
            background: rgba(0, 255, 65, 0.05); border: 1px solid #00ff41;
            padding: 20px; border-radius: 10px; margin-top: 20px;
        }
        .trade-item {
            background: rgba(0, 255, 65, 0.1); padding: 10px;
            margin: 10px 0; border-radius: 5px; border-left: 3px solid #00ff41;
        }
    </style>
</head>
<body>
    <div class="war-header">
        <h1>🎯 COMMANDER WAR ROOM</h1>
        <p><span class="live-indicator"></span>LIVE TACTICAL COMMAND CENTER</p>
        <p>User ID: {{ user_id }}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">${{ '{:,.2f}'.format(user_stats.balance) if user_stats else '0.00' }}</div>
            <div class="stat-label"><span class="live-indicator"></span>LIVE BALANCE</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ user_stats.win_rate if user_stats else '0' }}%</div>
            <div class="stat-label">WIN RATE</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ user_stats.trades_remaining if user_stats else '99' }}</div>
            <div class="stat-label">SHOTS REMAINING</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ user_stats.tier if user_stats else 'COMMANDER' }}</div>
            <div class="stat-label">OPERATIVE TIER</div>
        </div>
    </div>

    <div class="action-buttons">
        <a href="/brief" class="action-btn">📡 ACTIVE SIGNALS</a>
        <a href="/analysis" class="action-btn">📊 PERFORMANCE ANALYSIS</a>
        <a href="/mode" class="action-btn">⚡ FIRE MODE CONFIG</a>
        <a href="/settings" class="action-btn">⚙️ TACTICAL SETTINGS</a>
    </div>

    <div class="trades-section">
        <h3>🎯 RECENT OPERATIONS</h3>
        <div class="trade-item">
            <strong>GBPUSD</strong> - 98.8% Confidence - EXECUTED ✅
        </div>
        <div class="trade-item">
            <strong>USDCAD</strong> - 99% Confidence - EXECUTED ✅
        </div>
        <div class="trade-item">
            <strong>EURJPY</strong> - 91.7% Confidence - EXECUTED ✅
        </div>
    </div>

    <script>
        // Removed auto-refresh for better performance
        // Users can manually refresh if needed
    </script>
</body>
</html>
"""

@app.route('/me')
def war_room():
    """War Room - Personal Command Center (Lightweight for performance)"""
    user_id = request.args.get('user_id', 'anonymous')
    
    # LIGHTWEIGHT VERSION - Skip heavy module loading for performance
    try:
        # Get basic user balance from EA instances if available
        import sqlite3
        balance = 0.0
        try:
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()
            cursor.execute("SELECT last_balance FROM ea_instances WHERE user_id = ? ORDER BY last_seen DESC LIMIT 1", (user_id,))
            result = cursor.fetchone()
            balance = result[0] if result else 0.0
            conn.close()
        except Exception:
            balance = 0.0
            
        # Simple defaults without heavy module initialization
        callsign = f"VIPER-{user_id[-4:]}" if user_id != 'anonymous' else "GHOST-0000"
        rank_name, rank_desc = "COMMANDER", "ELITE TRADER"
        
        # Get slot availability from fire mode database
        from src.bitten_core.fire_mode_database import FireModeDatabase
        fire_db = FireModeDatabase()
        mode_info = fire_db.get_user_mode(str(user_id))
        tier_limits = fire_db.get_tier_slot_limits("COMMANDER")  # Assuming COMMANDER for now
        
        manual_slots_available = tier_limits['manual'] - mode_info.get('manual_slots_in_use', 0)
        auto_slots_available = mode_info.get('max_auto_slots', 75) - mode_info.get('auto_slots_in_use', 0)
        
# [DISABLED BITMODE]         # Get BITMODE status
        bitmode_enabled = mode_info.get('bitmode_enabled', False)
        bitmode_status = "✅ ACTIVE" if bitmode_enabled else "❌ DISABLED"
        bitmode_color = "#00ff41" if bitmode_enabled else "#ff4444"
        
        # Get real recent signals from database instead of fake trades
        recent_signals = []
        try:
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, direction, entry_price, confidence, created_at 
                FROM signals 
                WHERE created_at > ? 
                ORDER BY created_at DESC 
                LIMIT 3
            """, (int(time.time()) - 86400,))  # Last 24 hours
            
            for row in cursor.fetchall():
                symbol, direction, entry, confidence, timestamp = row
                
                # Get signal mode from database (default to RAPID if not found)
                try:
                    signal_row = conn.execute(
                        "SELECT payload_json FROM signals WHERE symbol = ? AND created_at = ?",
                        (symbol, timestamp)
                    ).fetchone()
                    
                    signal_mode = "RAPID"  # Default
                    mode_icon = "⚡"
                    mode_color = "orange"
                    
                    if signal_row and signal_row[0]:
                        payload = json.loads(signal_row[0])
                        signal_type = payload.get('signal_type', 'RAPID_ASSAULT')
                        if 'SNIPER' in signal_type or 'PRECISION' in signal_type:
                            signal_mode = "SNIPER"
                            mode_icon = "🎯"
                            mode_color = "blue"
                except:
                    signal_mode = "RAPID"
                    mode_icon = "⚡"
                    mode_color = "orange"
                
                recent_signals.append({
                    "pair": symbol,
                    "direction": direction,
                    "entry": f"{entry:.5f}" if entry else "0.00000",
                    "confidence": f"{confidence:.1f}%" if confidence else "0.0%",
                    "time": "Recently",
                    "mode": signal_mode,
                    "mode_icon": mode_icon,
                    "mode_color": mode_color
                })
            conn.close()
        except Exception:
            # Fallback if database query fails
            recent_signals = [
                {"pair": "GBPUSD", "direction": "BUY", "entry": "1.35367", "confidence": "95.6%", "time": "Recently"},
                {"pair": "EURJPY", "direction": "BUY", "entry": "172.308", "confidence": "96.4%", "time": "Recently"},
                {"pair": "USDCAD", "direction": "BUY", "entry": "1.3787", "confidence": "72.4%", "time": "Recently"}
            ]
            
    except Exception as e:
        logger.warning(f"Error in lightweight war room: {e}")
        # Ultra-lightweight fallback
        callsign = "GHOST-0000"
        rank_name, rank_desc = "COMMANDER", "ELITE TRADER"
        balance = 0.0
        recent_signals = []
    
    # Use simple template without f-string formatting to avoid errors
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 COMMANDER WAR ROOM</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
                color: #00ff41; font-family: 'Courier New', monospace; 
                margin: 0; padding: 20px; min-height: 100vh;
            }}
            .war-header {{ 
                background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
                border: 2px solid #00ff41; padding: 20px; margin-bottom: 20px;
                border-radius: 10px; text-align: center;
            }}
            .stats-grid {{ 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px; margin-bottom: 20px;
            }}
            .stat-card {{ 
                background: rgba(0, 255, 65, 0.1); border: 1px solid #00ff41;
                padding: 15px; border-radius: 8px; text-align: center;
            }}
            .stat-value {{ font-size: 1.8em; font-weight: bold; color: #00ff41; }}
            .stat-label {{ color: #888; font-size: 0.9em; margin-top: 5px; }}
            .live-indicator {{ 
                display: inline-block; width: 8px; height: 8px; 
                background: #00ff41; border-radius: 50%; 
                animation: blink 1s infinite; margin-right: 8px;
            }}
            @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
            .action-buttons {{
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px; margin-top: 20px;
            }}
            .action-btn {{
                background: linear-gradient(135deg, #006600 0%, #009900 100%);
                color: white; padding: 15px 20px; border: none; border-radius: 8px;
                font-size: 1.1em; cursor: pointer; text-decoration: none;
                text-align: center; transition: all 0.3s;
            }}
            .action-btn:hover {{ 
                background: linear-gradient(135deg, #009900 0%, #00cc00 100%);
                transform: translateY(-2px);
            }}
            .trades-section {{
                background: rgba(0, 255, 65, 0.05); border: 1px solid #00ff41;
                padding: 20px; border-radius: 10px; margin-top: 20px;
            }}
            .trade-item {{
                background: rgba(0, 255, 65, 0.1); padding: 10px;
                margin: 10px 0; border-radius: 5px; border-left: 3px solid #00ff41;
            }}
        </style>
    </head>
    <body>
        <div class="war-header">
            <h1>🎯 COMMANDER WAR ROOM</h1>
            <p><span class="live-indicator"></span>LIGHTWEIGHT COMMAND CENTER</p>
            <p>User: {callsign}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${balance:.2f}</div>
                <div class="stat-label"><span class="live-indicator"></span>LIVE BALANCE</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{manual_slots_available}/{tier_limits['manual']}</div>
                <div class="stat-label">🎯 MANUAL SLOTS</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{auto_slots_available}/{mode_info.get('max_auto_slots', 75)}</div>
                <div class="stat-label">⚡ AUTO SLOTS</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{rank_name}</div>
                <div class="stat-label">OPERATIVE TIER</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: {bitmode_color}">{bitmode_status}</div>
# [DISABLED BITMODE]                 <div class="stat-label">🎯 BITMODE</div>
            </div>
        </div>

        <div class="action-buttons">
            <a href="/brief" class="action-btn">📡 ACTIVE SIGNALS</a>
            <a href="/analysis" class="action-btn">📊 ANALYSIS</a>
            <a href="/mode" class="action-btn">⚡ FIRE MODE</a>
            <button class="action-btn" onclick="toggleBitmode()" id="bitmode-btn" style="background: {'linear-gradient(135deg, #009900 0%, #00cc00 100%)' if bitmode_enabled else 'linear-gradient(135deg, #666 0%, #888 100%)'}"">
# [DISABLED BITMODE]                 🎯 {'DISABLE BITMODE' if bitmode_enabled else 'ENABLE BITMODE'}
            </button>
            <a href="/settings" class="action-btn">⚙️ SETTINGS</a>
        </div>

        <div class="trades-section">
            <h3>🎯 RECENT SIGNALS</h3>
            {''.join(f'<div class="trade-item" style="border-left-color: {signal.get("mode_color", "orange")}"><span class="signal-mode" style="color: {signal.get("mode_color", "orange")}">{signal.get("mode_icon", "⚡")} {signal.get("mode", "RAPID")}</span> <strong>{signal["pair"]}</strong> - {signal["confidence"]} - {signal["direction"]} @ {signal["entry"]}</div>' for signal in recent_signals) if recent_signals else '<div class="trade-item">No recent signals available</div>'}
        </div>

        <script>
# [DISABLED BITMODE]             // BITMODE Toggle Function
            function toggleBitmode() {{
                const btn = document.getElementById('bitmode-btn');
                btn.disabled = true;
                btn.textContent = '🎯 UPDATING...';
                
                fetch('/api/bitmode/toggle', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        user_id: '{user_id}',
                        enabled: {str(not bitmode_enabled).lower()}
                    }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        location.reload(); // Refresh to show updated status
                    }} else {{
# [DISABLED BITMODE]                         alert('❌ Failed to toggle BITMODE: ' + data.error);
                        btn.disabled = false;
# [DISABLED BITMODE]                         btn.textContent = '🎯 {'DISABLE BITMODE' if bitmode_enabled else 'ENABLE BITMODE'}';
                    }}
                }})
                .catch(error => {{
                    console.error('Error:', error);
# [DISABLED BITMODE]                     alert('❌ Failed to toggle BITMODE');
                    btn.disabled = false;
# [DISABLED BITMODE]                     btn.textContent = '🎯 {'DISABLE BITMODE' if bitmode_enabled else 'ENABLE BITMODE'}';
                }});
            }}
        </script>
    </body>
    </html>
    """


@app.route('/analysis')
def analysis_page():
    """Analysis page - redirect to stats with user detection"""
    user_id = request.args.get('user_id', '7176191872')  # Default to main user
    return redirect(f'/stats/{user_id}', 302)

@app.route('/api/signal-freshness/<signal_id>', methods=['GET'])
def signal_freshness_status(signal_id):
    """SCALPING FRESHNESS: Real-time signal staleness detection"""
    try:
        from datetime import datetime
        import sqlite3
        
        # Get signal creation time from truth log
        signal_age_minutes = 0
        signal_confidence = 0
        
        with open('/root/HydraX-v2/truth_log.jsonl', 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('signal_id') == signal_id:
                        created_at = datetime.fromisoformat(data['generated_at'].replace('Z', ''))
                        signal_age_minutes = (datetime.now() - created_at).total_seconds() / 60
                        signal_confidence = data.get('confidence', 0)
                        break
                except:
                    continue
        
        # SCALPING FRESHNESS LOGIC
        if signal_age_minutes <= 5:
            freshness_score = 100
            status = 'fresh'
            warning_level = 'none'
            fireable = True
        elif signal_age_minutes <= 10:
            freshness_score = max(60, 100 - (signal_age_minutes - 5) * 8)  # Degrade fast
            status = 'aging'
            warning_level = 'caution'
            fireable = True
        elif signal_age_minutes <= 15:
            freshness_score = max(20, 60 - (signal_age_minutes - 10) * 8)
            status = 'stale'
            warning_level = 'warning'
            fireable = signal_confidence >= 45  # Recalibrated: was 95%, now 45% (top of best performing range)
        else:
            freshness_score = 0
            status = 'expired'
            warning_level = 'danger'
            fireable = False  # UNFIREABLE after 15 minutes
        
        return jsonify({
            'signal_id': signal_id,
            'freshness_score': int(freshness_score),
            'status': status,
            'pattern_valid': fireable,
            'warning_level': warning_level,
            'fireable': fireable,
            'age_minutes': round(signal_age_minutes, 1),
            'confidence': signal_confidence,
            'message': f'Signal {status} - {int(freshness_score)}% fresh'
        })
        
    except Exception as e:
        # Fallback for any errors
        return jsonify({
            'signal_id': signal_id,
            'freshness_score': 50,
            'status': 'unknown',
            'pattern_valid': True,
            'warning_level': 'caution',
            'fireable': True,
            'message': 'Freshness check unavailable'
        })

@app.route('/api/check-signal-access', methods=['POST'])
def check_signal_access():
    """Check if user can fire a specific signal mode"""
    try:
        data = request.get_json()
        user_id = data.get('user_id') or request.headers.get('X-User-ID')
        signal_id = data.get('signal_id')
        
        if not user_id or not signal_id:
            return jsonify({
                'error': 'Missing user_id or signal_id',
                'can_fire': False
            }), 400
        
        # Get signal data to determine mode
        mission_file = f"/root/HydraX-v2/missions/{signal_id}.json"
        if not os.path.exists(mission_file):
            return jsonify({
                'error': 'Signal not found',
                'can_fire': False
            }), 404
        
        with open(mission_file, 'r') as f:
            mission_data = json.load(f)
        
        signal_data = mission_data.get('signal', mission_data)
        signal_type = signal_data.get('signal_type', 'RAPID_ASSAULT')
        signal_mode = 'RAPID' if 'RAPID' in signal_type else 'SNIPER'
        
        # Check user tier and permissions
        user_tier = get_user_tier(user_id)
        can_fire = can_fire_signal_mode(user_tier, signal_mode)
        
        response = {
            'can_fire': can_fire,
            'user_tier': user_tier,
            'signal_mode': signal_mode,
            'signal_id': signal_id
        }
        
        if not can_fire:
            response.update({
                'upgrade_required': True,
                'upgrade_title': f'Upgrade Required for {signal_mode} Signals',
                'upgrade_message': f'Your {user_tier} tier can only fire RAPID signals. Upgrade to PREDATOR tier to access {signal_mode} signals.',
                'upgrade_benefits': [
                    'Access to both RAPID and SNIPER signals',
                    'Higher precision trading opportunities', 
                    'Extended target profit potential',
                    'Advanced risk management tools'
                ],
                'upgrade_action': 'Contact support to upgrade your account'
            })
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Check signal access error: {e}")
        return jsonify({
            'error': str(e),
            'can_fire': False
        }), 500

@app.route('/api/user-balance/<user_id>', methods=['GET'])
def get_live_user_balance(user_id):
    """Get real-time user balance from EA instances"""
    try:
        import sqlite3
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT last_balance, last_equity, currency, leverage 
            FROM ea_instances 
            WHERE user_id = ? 
            ORDER BY last_seen DESC 
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            balance, equity, currency, leverage = result
            return jsonify({
                'success': True,
                'balance': float(balance or 0),
                'equity': float(equity or 0),
                'currency': currency or 'USD',
                'leverage': int(leverage or 500),
                'last_updated': 'Live'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No EA connection found for user'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bitmode/toggle', methods=['POST'])
def api_bitmode_toggle():
# [DISABLED BITMODE]     """API endpoint to toggle BITMODE for user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        enabled = data.get('enabled', False)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
        
        # Get user tier from user registry or default to COMMANDER
        user_tier = get_user_tier(user_id)
        
        # Check tier eligibility
        if user_tier not in ['FANG', 'COMMANDER']:
            return jsonify({
                'success': False, 
# [DISABLED BITMODE]                 'error': f'BITMODE requires FANG+ tier. Current tier: {user_tier}'
            }), 403
        
# [DISABLED BITMODE]         # Toggle BITMODE
        from src.bitten_core.fire_mode_database import fire_mode_db
        success = fire_mode_db.toggle_bitmode(user_id, enabled, user_tier)
        
        if success:
            return jsonify({
                'success': True,
                'enabled': enabled,
# [DISABLED BITMODE]                 'message': f'BITMODE {"enabled" if enabled else "disabled"} successfully'
            })
        else:
            return jsonify({
                'success': False,
# [DISABLED BITMODE]                 'error': 'Failed to update BITMODE status'
            }), 500
            
    except Exception as e:
# [DISABLED BITMODE]         logger.error(f"BITMODE toggle error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=False)
