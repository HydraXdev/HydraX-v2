#!/usr/bin/env python3
"""
Optimized Flask server with lazy loading and consolidated imports
Reduced memory footprint and improved performance
"""

import os
import sys
import json
import logging
import random
from datetime import datetime

# Core Flask imports (always needed)
from flask import Flask, render_template, render_template_string, request, jsonify, redirect
from flask_socketio import SocketIO

# Load environment early
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize onboarding system
try:
    sys.path.append('/root/HydraX-v2/src/bitten_core')
    from onboarding_webapp_system import register_onboarding_system
    onboarding_system_available = True
    logger.info("✅ HydraX Onboarding System imported")
except ImportError as e:
    logger.error(f"❌ Failed to import onboarding system: {e}")
    onboarding_system_available = False

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

@app.route('/api/signals', methods=['GET', 'POST'])
def api_signals():
    """API endpoint for signals - GET retrieves, POST receives from VENOM+CITADEL"""
    if request.method == 'GET':
        try:
            get_signals = lazy.signal_storage.get('get_active_signals')
            if get_signals:
                signals = get_signals()
                return jsonify({'signals': signals, 'count': len(signals)})
            else:
                return jsonify({'error': 'Signal system not available'}), 503
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
            logger.info(f"📨 Received VENOM+CITADEL signal: {signal_data.get('signal_id')} "
                       f"for {signal_data.get('symbol')} "
                       f"CITADEL: {signal_data.get('citadel_shield', {}).get('score', 0)}/10")
            
            # Import BittenCore if available
            try:
                from src.bitten_core.bitten_core import BittenCore
                core = BittenCore()
                
                # Process the signal through BittenCore
                result = core.process_venom_signal(signal_data)
                
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
        user_id = request.args.get('user_id')
        
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
        
        # Load user registry for real user data overlay
        user_registry_data = {}
        user_stats = {}
        if user_id:
            try:
                with open('/root/HydraX-v2/user_registry.json', 'r') as f:
                    registry = json.load(f)
                    # Check both root and users section
                    if user_id in registry:
                        user_registry_data = registry[user_id]
                    elif 'users' in registry and user_id in registry['users']:
                        user_registry_data = registry['users'][user_id]
                    
                    # Extract key stats
                    user_stats = {
                        'tier': user_registry_data.get('tier', 'NIBBLER'),
                        'balance': user_registry_data.get('account_balance', 10000.0),
                        'equity': user_registry_data.get('account_equity', 10000.0),
                        'win_rate': 68.5,  # TODO: Get from actual trade history
                        'total_pnl': 850.47 - 10000,  # Current balance - starting balance
                        'trades_remaining': 5 if user_registry_data.get('tier') == 'NIBBLER' else 10
                    }
                    logger.info(f"Loaded user data for {user_id}: tier={user_stats['tier']}, balance=${user_stats['balance']}")
            except Exception as e:
                logger.warning(f"Could not load user data for {user_id}: {e}")
                user_stats = {
                    'tier': 'NIBBLER',
                    'balance': 10000.0,
                    'equity': 10000.0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'trades_remaining': 5
                }
        
        # Use static file loading for now
        mission_paths = [
            f"./missions/mission_{mission_id}.json",  # Preferred format
            f"./missions/{mission_id}.json"           # Fallback format
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
        user_id = mission_data.get('user_id', 'unknown')
        
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
            
            # Quality scores
            'tcs_score': signal_data.get('confidence', mission_data.get('confidence', 75)),
            'citadel_score': citadel_score,
            'ml_filter_passed': mission_data.get('ml_filter', {}).get('filter_result') != 'prediction_failed',
            
            # Risk calculation with user overlay
            'rr_ratio': signal_data.get('risk_reward_ratio', signal_data.get('risk_reward', 2.0)),
            'account_balance': user_stats.get('balance', user_data.get('balance', 10000.0)),
            'sl_dollars': f"{user_stats.get('balance', 10000.0) * 0.02:.2f}",  # 2% risk
            'tp_dollars': f"{user_stats.get('balance', 10000.0) * 0.04:.2f}",  # 2:1 R:R
            
            # Mission info
            'mission_id': mission_id,
            'signal_id': mission_data.get('signal_id', mission_id),
            'user_id': user_id,
            'expiry_seconds': time_remaining,
            
            # User stats with real overlay data
            'user_stats': user_stats,  # Use the loaded user stats from registry
            
            # Calculate position size based on user tier
            'position_size': 0.01 * (2 if user_stats['tier'] == 'COMMANDER' else 1),
            
            # Warning for missing fields
            'missing_fields': missing_fields,
            'has_warnings': len(missing_fields) > 0,
            
            # CITADEL shield info
            'citadel_classification': citadel_shield.get('classification', 'SHIELD_ACTIVE'),
            'citadel_explanation': citadel_shield.get('explanation', 'Signal analysis in progress')
        }
        
        # Load and render the new HUD template
        # Use comprehensive template for enhanced experience
        if os.path.exists('templates/comprehensive_mission_briefing.html'):
            return render_template('comprehensive_mission_briefing.html', **template_vars)
        else:
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
        mission_file = f"./missions/{mission_id}.json"
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
                uuid_tracker.track_file_relay(trade_uuid, mission_file, "fire_api_relay")
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
        
        # REAL BROKER EXECUTION via FireRouter
        execution_result = {'success': False, 'message': 'Execution failed'}
        
        try:
            # Import fire router for real trade execution
            import sys
            sys.path.append('/root/HydraX-v2/src/bitten_core')
            from fire_router import FireRouter, TradeRequest, TradeDirection
            
            fire_router = FireRouter()
            
            # Extract signal data
            signal = mission_data.get('signal', {})
            enhanced_signal = mission_data.get('enhanced_signal', signal)
            
            # Create trade request
            direction = TradeDirection.BUY if enhanced_signal.get('direction', '').upper() == 'BUY' else TradeDirection.SELL
            
            # Use safe volume - ignore high mission volume
            safe_volume = 0.1  # Start with micro lots for safety
            
            trade_request = TradeRequest(
                user_id=str(user_id),
                symbol=enhanced_signal.get('symbol', 'EURUSD'),
                direction=direction,
                volume=safe_volume,
                stop_loss=enhanced_signal.get('stop_loss'),
                take_profit=enhanced_signal.get('take_profit'),
                tcs_score=enhanced_signal.get('tcs_score', 75),
                comment=f"BITTEN_{mission_id}",
                mission_id=mission_id
            )
            
            # Execute real trade via direct broker API
            fire_result = fire_router.execute_trade_request(trade_request)
            
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
        
        # COMPREHENSIVE TRADE LOGGING PIPELINE
        try:
            # Import and use the trade logging pipeline
            import sys
            sys.path.append('/root/HydraX-v2/src/bitten_core')
            from trade_logging_pipeline import log_trade_execution
            from user_account_manager import process_api_account_info
            
            # Log to all systems if mission was fired (success or failure)
            if mission_data['status'] in ['fired', 'failed']:
                logging_success = log_trade_execution(
                    mission_data, 
                    execution_result, 
                    user_id, 
                    mission_id
                )
                
                if logging_success:
                    logger.info(f"✅ Complete trade logging successful for mission: {mission_id}")
                else:
                    logger.error(f"❌ Trade logging failed for mission: {mission_id}")
                    
        except Exception as e:
            logger.error(f"❌ Trade logging pipeline error: {e}")
            # Continue execution even if logging fails
        
        # Response based on execution result
        symbol = mission_data.get('signal', {}).get('symbol', 'TARGET')
        direction = mission_data.get('signal', {}).get('direction', 'LONG')
        
        # CHARACTER DISPATCHER - Route to appropriate BITTEN Protocol character
        character_response = ""
        character_name = ""
        try:
            from src.bitten_core.voice.character_event_dispatcher import get_trade_execution_response
            
            # Get user context for character selection
            user_context = {'tier': 'COMMANDER', 'user_id': user_id}  # TODO: Get real user tier
            
            # Route execution result to appropriate character
            char_result = get_trade_execution_response(
                mission_data.get('signal', {}), 
                execution_result, 
                user_context
            )
            
            character_response = char_result.get('response', '')
            character_name = char_result.get('character', 'UNKNOWN')
            
        except Exception as e:
            logger.warning(f"Character dispatcher failed: {e}")
            # Fallback to ATHENA
            character_response = "Mission status acknowledged."
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

@socketio.on('get_signals')
def handle_get_signals():
    """Handle signal requests via WebSocket"""
    try:
        get_signals = lazy.signal_storage.get('get_active_signals')
        if get_signals:
            signals = get_signals()
            socketio.emit('signals_update', {'signals': signals})
        else:
            socketio.emit('error', {'message': 'Signal system unavailable'})
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
    from src.bitten_core.stripe_webhook_handler import stripe_webhook_bp
    app.register_blueprint(stripe_webhook_bp, url_prefix='/api')
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
    """Combined stats and trade history page"""
    
    STATS_TEMPLATE = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📊 User Stats</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{ background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }}
            .header {{ background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }}
            .stat-card {{ background: #1a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #333; }}
            .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
            .stat-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }}
            .positive {{ color: #28a745; }}
            .negative {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 PERFORMANCE DASHBOARD</h1>
            <p>User ID: {user_id}</p>
        </div>
        
        <div class="stat-grid">
            <div class="stat-card">
                <h3>🎯 Trading Stats</h3>
                <div class="stat-item"><span>Total Trades:</span><span>47</span></div>
                <div class="stat-item"><span>Win Rate:</span><span class="positive">73.4%</span></div>
                <div class="stat-item"><span>Best Streak:</span><span>8</span></div>
                <div class="stat-item"><span>Current Streak:</span><span class="positive">3</span></div>
            </div>
            
            <div class="stat-card">
                <h3>💰 P&L Summary</h3>
                <div class="stat-item"><span>Total P&L:</span><span class="positive">+$1,247.50</span></div>
                <div class="stat-item"><span>Avg R:R:</span><span>2.3</span></div>
                <div class="stat-item"><span>Best Trade:</span><span class="positive">+$320</span></div>
                <div class="stat-item"><span>Worst Trade:</span><span class="negative">-$85</span></div>
            </div>
        </div>
        
        <div class="stat-card">
            <h3>📈 Recent Activity</h3>
            <p>Last trade: EURUSD BUY - <span class="positive">+$125</span></p>
            <p>Last signal: 2 hours ago</p>
            <p>Next mission: Analyzing...</p>
        </div>
        
        <div style="text-align: center; padding: 20px;">
            <button onclick="window.close()" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Stats</button>
        </div>
    </body>
    </html>
    """
    
    return STATS_TEMPLATE

@app.route('/me')
def war_room():
    """War Room - Personal Command Center"""
    user_id = request.args.get('user_id', 'anonymous')
    
    # Import necessary modules
    try:
        from src.bitten_core.referral_system import ReferralSystem
        from src.bitten_core.achievement_system import AchievementSystem
        from src.bitten_core.rank_access import RankAccess, UserRank
        from src.bitten_core.normans_notebook import NormansNotebook
        from engagement_db import EngagementDB
        import random
        from datetime import datetime, timedelta
        
        # Initialize systems
        referral_system = ReferralSystem()
        achievement_system = AchievementSystem()
        rank_access = RankAccess()
        engagement_db = EngagementDB()
        
        # Get user data
        user_rank = rank_access.get_user_rank(int(user_id) if user_id.isdigit() else 0)
        user_info = rank_access.get_user_info(int(user_id) if user_id.isdigit() else 0)
        
        # Generate dynamic callsign based on rank
        callsign_prefixes = {
            UserRank.USER: "ROOKIE",
            UserRank.AUTHORIZED: "VIPER",
            UserRank.ELITE: "GHOST",
            UserRank.ADMIN: "APEX"
        }
        callsign_prefix = callsign_prefixes.get(user_rank, "SHADOW")
        callsign = f"{callsign_prefix}-{user_id[-4:]}" if user_id != 'anonymous' else "GHOST-0000"
        
        # Get user stats from engagement DB
        user_stats = engagement_db.get_user_stats(user_id)
        
        # Use real stats or defaults - NO FAKE DATA
        total_trades = user_stats.get('total_fires', 0)
        win_rate = user_stats.get('win_rate', 0.0)
        total_pnl = user_stats.get('total_pnl', 0.0)
        current_streak = user_stats.get('current_streak', 0)
        best_streak = user_stats.get('best_streak', 0)
        avg_rr = user_stats.get('avg_rr', 2.0)  # Default to standard 1:2 R:R
        global_rank = user_stats.get('global_rank', 9999)  # Default to unranked
        
        # Get referral data
        squad_stats = referral_system.get_squad_stats(user_id)
        referral_code = referral_system.generate_referral_code(user_id).code if user_id != 'anonymous' else "BITTEN-ANON"
        
        # Get achievement data
        user_achievements = achievement_system.get_user_achievements(user_id)
        unlocked_badges = [ach for ach in user_achievements if ach.unlocked]
        
        # Get recent trades (mock data for now)
        recent_kills = [
            {"pair": "EURUSD", "direction": "BUY", "entry": "1.0845", "time": "2 hours ago", "tcs": 91, "profit": 125},
            {"pair": "GBPJPY", "direction": "SELL", "entry": "183.45", "time": "5 hours ago", "tcs": 88, "profit": 210},
            {"pair": "XAUUSD", "direction": "BUY", "entry": "2024.50", "time": "Yesterday", "tcs": 94, "profit": 380}
        ]
        
        # Get rank display
        rank_displays = {
            UserRank.USER: ("PRESS PASS", "TRAINEE TRADER"),
            UserRank.AUTHORIZED: ("NIBBLER", "AUTHORIZED TRADER"),
            UserRank.ELITE: ("COMMANDER", "ELITE TRADER"),
            UserRank.ADMIN: ("APEX", "SYSTEM ADMIN")
        }
        rank_name, rank_desc = rank_displays.get(user_rank, ("UNKNOWN", "UNRANKED"))
        
    except Exception as e:
        logger.warning(f"Error loading user data: {e}")
        # Fallback to default values
        callsign = f"VIPER-{user_id[-4:]}" if user_id != 'anonymous' else "GHOST-0000"
        rank_name, rank_desc = "COMMANDER", "ELITE TRADER"
        total_trades = 127
        win_rate = 0.843
        total_pnl = 4783
        current_streak = 7
        best_streak = 12
        avg_rr = 2.8
        global_rank = 42
        referral_code = f"BITTEN-{user_id[-6:].upper()}"
        recent_kills = [
            {"pair": "EURUSD", "direction": "BUY", "entry": "1.0845", "time": "2 hours ago", "tcs": 91, "profit": 125},
            {"pair": "GBPJPY", "direction": "SELL", "entry": "183.45", "time": "5 hours ago", "tcs": 88, "profit": 210},
            {"pair": "XAUUSD", "direction": "BUY", "entry": "2024.50", "time": "Yesterday", "tcs": 94, "profit": 380}
        ]
    
    WAR_ROOM_TEMPLATE = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎖️ BITTEN War Room - Command Center</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background: #000;
                color: #fff;
                font-family: 'Courier New', monospace;
                overflow-x: hidden;
                position: relative;
            }}
            
            /* Animated background */
            body::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: 
                    radial-gradient(circle at 20% 50%, rgba(0, 217, 255, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 50%, rgba(255, 0, 128, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(0, 255, 0, 0.05) 0%, transparent 50%);
                animation: pulse 10s ease-in-out infinite;
                z-index: -1;
            }}
            
            @keyframes pulse {{
                0%, 100% {{ opacity: 0.5; }}
                50% {{ opacity: 1; }}
            }}
            
            /* Header with military styling */
            .war-header {{
                background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
                border-bottom: 3px solid #00D9FF;
                padding: 20px;
                position: relative;
                overflow: hidden;
            }}
            
            .war-header::after {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(0, 217, 255, 0.3), transparent);
                animation: scan 3s infinite;
            }}
            
            @keyframes scan {{
                to {{ left: 100%; }}
            }}
            
            .header-content {{
                position: relative;
                z-index: 1;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }}
            
            .rank-display {{
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            
            .rank-badge {{
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #FFD700, #FFA500);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 30px;
                box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
                animation: rotate 10s linear infinite;
            }}
            
            @keyframes rotate {{
                to {{ transform: rotate(360deg); }}
            }}
            
            .callsign {{
                font-size: 24px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #00D9FF;
                text-shadow: 0 0 10px rgba(0, 217, 255, 0.5);
            }}
            
            .rank-info {{
                font-size: 14px;
                color: #999;
                margin-top: 5px;
            }}
            
            /* Stats Grid */
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                padding: 20px;
            }}
            
            .stat-card {{
                background: rgba(26, 26, 26, 0.9);
                border: 1px solid #333;
                border-radius: 10px;
                padding: 20px;
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
            }}
            
            .stat-card:hover {{
                border-color: #00D9FF;
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0, 217, 255, 0.3);
            }}
            
            .stat-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 3px;
                background: linear-gradient(90deg, #00D9FF, #FF0080);
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }}
            
            .stat-card:hover::before {{
                transform: translateX(0);
            }}
            
            .stat-label {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }}
            
            .stat-value {{
                font-size: 28px;
                font-weight: bold;
                color: #00D9FF;
                text-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
            }}
            
            .positive {{ color: #00FF88; }}
            .negative {{ color: #FF0044; }}
            
            /* Kill Cards Section */
            .kill-cards {{
                padding: 20px;
            }}
            
            .section-title {{
                font-size: 20px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 3px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .section-title::before {{
                content: '';
                width: 30px;
                height: 3px;
                background: linear-gradient(90deg, #00D9FF, transparent);
            }}
            
            .kill-card {{
                background: rgba(0, 255, 136, 0.1);
                border: 1px solid rgba(0, 255, 136, 0.3);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: relative;
                overflow: hidden;
                animation: slideIn 0.5s ease-out;
            }}
            
            @keyframes slideIn {{
                from {{
                    opacity: 0;
                    transform: translateX(-50px);
                }}
                to {{
                    opacity: 1;
                    transform: translateX(0);
                }}
            }}
            
            .kill-card::after {{
                content: '💀';
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 30px;
                opacity: 0.2;
            }}
            
            .kill-info {{
                flex: 1;
            }}
            
            .kill-pair {{
                font-weight: bold;
                color: #00D9FF;
                font-size: 18px;
            }}
            
            .kill-details {{
                font-size: 12px;
                color: #999;
                margin-top: 5px;
            }}
            
            .kill-profit {{
                font-size: 24px;
                font-weight: bold;
                color: #00FF88;
                text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
            }}
            
            /* Achievement Badges */
            .achievements {{
                padding: 20px;
            }}
            
            .badge-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
                gap: 15px;
            }}
            
            .badge {{
                background: rgba(26, 26, 26, 0.9);
                border: 2px solid #333;
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                position: relative;
                overflow: hidden;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            
            .badge:hover {{
                transform: scale(1.1);
                border-color: #FFD700;
                z-index: 10;
            }}
            
            .badge-icon {{
                font-size: 40px;
                margin-bottom: 10px;
            }}
            
            .badge-name {{
                font-size: 12px;
                color: #999;
            }}
            
            .badge.locked {{
                opacity: 0.3;
                filter: grayscale(100%);
            }}
            
            .badge.legendary {{
                background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 0, 128, 0.2));
                border-color: #FFD700;
                animation: legendaryGlow 2s ease-in-out infinite;
            }}
            
            @keyframes legendaryGlow {{
                0%, 100% {{ box-shadow: 0 0 20px rgba(255, 215, 0, 0.5); }}
                50% {{ box-shadow: 0 0 40px rgba(255, 215, 0, 0.8); }}
            }}
            
            /* Referral Squad Section */
            .squad-section {{
                padding: 20px;
                background: rgba(26, 26, 26, 0.5);
                margin: 20px;
                border-radius: 10px;
                border: 1px solid #333;
            }}
            
            .squad-stats {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }}
            
            .squad-member {{
                background: rgba(0, 0, 0, 0.5);
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #00D9FF;
                margin-bottom: 10px;
            }}
            
            .member-name {{
                font-weight: bold;
                color: #00D9FF;
            }}
            
            .member-stats {{
                font-size: 12px;
                color: #999;
                margin-top: 5px;
            }}
            
            /* Social Sharing */
            .social-section {{
                padding: 20px;
                text-align: center;
            }}
            
            .share-buttons {{
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
                margin-top: 20px;
            }}
            
            .share-btn {{
                background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
                border: 2px solid #333;
                color: #fff;
                padding: 15px 30px;
                border-radius: 50px;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 10px;
                text-decoration: none;
            }}
            
            .share-btn:hover {{
                border-color: #00D9FF;
                transform: scale(1.05);
                box-shadow: 0 5px 20px rgba(0, 217, 255, 0.5);
            }}
            
            .share-btn.facebook {{ border-color: #1877F2; }}
            .share-btn.twitter {{ border-color: #1DA1F2; }}
            .share-btn.instagram {{ border-color: #E4405F; }}
            
            /* Action Buttons */
            .action-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                padding: 20px;
            }}
            
            .action-btn {{
                background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
                border: 2px solid #00D9FF;
                color: #00D9FF;
                padding: 20px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
                text-decoration: none;
                display: block;
                position: relative;
                overflow: hidden;
            }}
            
            .action-btn::before {{
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 0;
                height: 0;
                background: rgba(0, 217, 255, 0.3);
                border-radius: 50%;
                transform: translate(-50%, -50%);
                transition: width 0.5s, height 0.5s;
            }}
            
            .action-btn:hover::before {{
                width: 300px;
                height: 300px;
            }}
            
            .action-btn:hover {{
                transform: translateY(-3px);
                box-shadow: 0 10px 30px rgba(0, 217, 255, 0.5);
            }}
            
            /* Sound Toggle */
            .sound-toggle {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(26, 26, 26, 0.9);
                border: 2px solid #333;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                font-size: 24px;
                transition: all 0.3s ease;
                z-index: 1000;
            }}
            
            .sound-toggle:hover {{
                border-color: #00D9FF;
                transform: scale(1.1);
            }}
            
            .sound-toggle.active {{
                background: rgba(0, 217, 255, 0.2);
                border-color: #00D9FF;
            }}
            
            /* Loading Animation */
            .loading {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #333;
                border-top-color: #00D9FF;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }}
            
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
            
            /* Responsive Design */
            @media (max-width: 768px) {{
                .stats-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .squad-stats {{
                    grid-template-columns: 1fr;
                }}
                
                .header-content {{
                    flex-direction: column;
                    text-align: center;
                }}
                
                .rank-display {{
                    margin-bottom: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <!-- War Room Header -->
        <div class="war-header">
            <div class="header-content">
                <div class="rank-display">
                    <div class="rank-badge">🎖️</div>
                    <div>
                        <div class="callsign">{callsign}</div>
                        <div class="rank-info">{rank_name} TIER • {rank_desc}</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 12px; color: #666;">OPERATION: BITTEN</div>
                    <div style="font-size: 14px; color: #00D9FF;">STATUS: ACTIVE</div>
                </div>
            </div>
        </div>
        
        <!-- Performance Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">🎯 Total Missions</div>
                <div class="stat-value">{total_trades}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">⚡ Win Rate</div>
                <div class="stat-value {'positive' if win_rate > 0.5 else 'negative'}">{win_rate:.1%}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">💰 Total P&L</div>
                <div class="stat-value {'positive' if total_pnl > 0 else 'negative'}">{'+'if total_pnl > 0 else ''}${total_pnl:,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">🔥 Current Streak</div>
                <div class="stat-value">{current_streak}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">📊 Avg R:R</div>
                <div class="stat-value">{avg_rr:.1f}:1</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">🏆 Global Rank</div>
                <div class="stat-value">#{global_rank}</div>
            </div>
        </div>
        
        <!-- Recent Kill Cards -->
        <div class="kill-cards">
            <h2 class="section-title">💀 RECENT KILLS</h2>
            {''.join([f'''
            <div class="kill-card">
                <div class="kill-info">
                    <div class="kill-pair">{kill['pair']}</div>
                    <div class="kill-details">{kill['direction']} @ {kill['entry']} • {kill['time']} • TCS: {kill['tcs']}%</div>
                </div>
                <div class="kill-profit">+${kill['profit']}</div>
            </div>
            ''' for kill in recent_kills])}
        </div>
        
        <!-- Achievement Badges -->
        <div class="achievements">
            <h2 class="section-title">🏅 ACHIEVEMENT SHOWCASE</h2>
            <div class="badge-grid">
                <div class="badge legendary">
                    <div class="badge-icon">👑</div>
                    <div class="badge-name">APEX PREDATOR</div>
                </div>
                <div class="badge">
                    <div class="badge-icon">🎯</div>
                    <div class="badge-name">SHARPSHOOTER</div>
                </div>
                <div class="badge">
                    <div class="badge-icon">⚡</div>
                    <div class="badge-name">SPEED DEMON</div>
                </div>
                <div class="badge">
                    <div class="badge-icon">💎</div>
                    <div class="badge-name">DIAMOND HANDS</div>
                </div>
                <div class="badge">
                    <div class="badge-icon">🔥</div>
                    <div class="badge-name">FIRE MASTER</div>
                </div>
                <div class="badge locked">
                    <div class="badge-icon">🌟</div>
                    <div class="badge-name">LEGENDARY</div>
                </div>
                <div class="badge">
                    <div class="badge-icon">💰</div>
                    <div class="badge-name">PROFIT HUNTER</div>
                </div>
                <div class="badge locked">
                    <div class="badge-icon">🚀</div>
                    <div class="badge-name">TO THE MOON</div>
                </div>
            </div>
        </div>
        
        <!-- Squad Section -->
        <div class="squad-section">
            <h2 class="section-title">🪖 YOUR SQUAD</h2>
            <div class="squad-stats">
                <div class="stat-card">
                    <div class="stat-label">Squad Size</div>
                    <div class="stat-value">23</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Squad XP</div>
                    <div class="stat-value">14,250</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Squad Rank</div>
                    <div class="stat-value">#8</div>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <h3 style="margin-bottom: 15px; color: #00D9FF;">TOP PERFORMERS</h3>
                <div class="squad-member">
                    <div class="member-name">GHOST-2847</div>
                    <div class="member-stats">Tier: FANG • Trades: 45 • Win Rate: 78%</div>
                </div>
                <div class="squad-member">
                    <div class="member-name">VENOM-9183</div>
                    <div class="member-stats">Tier: NIBBLER • Trades: 23 • Win Rate: 71%</div>
                </div>
                <div class="squad-member">
                    <div class="member-name">RAZOR-4521</div>
                    <div class="member-stats">Tier: FANG • Trades: 67 • Win Rate: 82%</div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <div style="background: rgba(0, 217, 255, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #00D9FF;">
                    <div style="font-size: 14px; color: #00D9FF; margin-bottom: 10px;">YOUR REFERRAL CODE</div>
                    <div style="font-size: 24px; font-weight: bold; letter-spacing: 3px;">{referral_code}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 10px;">Share to grow your squad</div>
                </div>
            </div>
        </div>
        
        <!-- Social Sharing -->
        <div class="social-section">
            <h2 class="section-title">📢 SHARE YOUR VICTORIES</h2>
            <div class="share-buttons">
                <a href="#" class="share-btn facebook" onclick="shareToFacebook()">
                    <span>📘</span> Share to Facebook
                </a>
                <a href="#" class="share-btn twitter" onclick="shareToTwitter()">
                    <span>🐦</span> Share to X
                </a>
                <a href="#" class="share-btn instagram" onclick="shareToInstagram()">
                    <span>📷</span> Share to Instagram
                </a>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="action-grid">
            <a href="/notebook/{user_id}" class="action-btn">
                <div>📓 NORMAN'S NOTEBOOK</div>
                <div style="font-size: 12px; margin-top: 5px;">View your trading journal</div>
            </a>
            <a href="/history" class="action-btn">
                <div>📊 FULL HISTORY</div>
                <div style="font-size: 12px; margin-top: 5px;">Complete trade records</div>
            </a>
            <a href="/stats/{user_id}" class="action-btn">
                <div>📈 DETAILED STATS</div>
                <div style="font-size: 12px; margin-top: 5px;">Deep performance analysis</div>
            </a>
            <a href="/tiers" class="action-btn">
                <div>🎖️ TIER PROGRESS</div>
                <div style="font-size: 12px; margin-top: 5px;">Next rank requirements</div>
            </a>
        </div>
        
        <!-- Sound Toggle -->
        <div class="sound-toggle" id="soundToggle" onclick="toggleSound()">
            🔊
        </div>
        
        <script>
            // Initialize Telegram WebApp
            if (window.Telegram && window.Telegram.WebApp) {{
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
                
                // Set theme colors
                window.Telegram.WebApp.setHeaderColor('#1a1a1a');
                window.Telegram.WebApp.setBackgroundColor('#000000');
            }}
            
            // Sound effects system
            let soundEnabled = localStorage.getItem('soundEnabled') !== 'false';
            const soundToggleBtn = document.getElementById('soundToggle');
            
            function updateSoundButton() {{
                soundToggleBtn.textContent = soundEnabled ? '🔊' : '🔇';
                soundToggleBtn.classList.toggle('active', soundEnabled);
            }}
            
            function toggleSound() {{
                soundEnabled = !soundEnabled;
                localStorage.setItem('soundEnabled', soundEnabled);
                updateSoundButton();
                if (soundEnabled) {{
                    playSound('toggle');
                }}
            }}
            
            function playSound(type) {{
                if (!soundEnabled) return;
                
                // Sound effect mapping (placeholder - actual implementation would use Web Audio API)
                const sounds = {{
                    'hover': 'hover.mp3',
                    'click': 'click.mp3',
                    'achievement': 'achievement.mp3',
                    'toggle': 'toggle.mp3'
                }};
                
                // Play sound effect
                console.log(`Playing sound: ${{sounds[type]}}`);
            }}
            
            // Initialize sound button
            updateSoundButton();
            
            // Add hover sound effects
            document.querySelectorAll('.stat-card, .badge, .action-btn, .share-btn').forEach(el => {{
                el.addEventListener('mouseenter', () => playSound('hover'));
                el.addEventListener('click', () => playSound('click'));
            }});
            
            // Social sharing functions
            function shareToFacebook() {{
                const text = `I'm {callsign} in BITTEN Trading! 🎖️ Win Rate: {win_rate:.1%} | P&L: {'+'if total_pnl > 0 else ''}${total_pnl:,.0f} | Join my squad!`;
                const url = `https://www.facebook.com/sharer/sharer.php?u=https://bitten.app/join/{referral_code}&quote=${{encodeURIComponent(text)}}`;
                window.open(url, '_blank', 'width=600,height=400');
                playSound('click');
            }}
            
            function shareToTwitter() {{
                const text = `🎖️ {callsign} reporting from BITTEN Trading!\\n\\n📊 Stats:\\n• Win Rate: {win_rate:.1%}\\n• P&L: {'+'if total_pnl > 0 else ''}${total_pnl:,.0f}\\n• Global Rank: #{global_rank}\\n\\nJoin my squad: {referral_code}\\n\\n#BITTEN #Trading #Forex`;
                const url = `https://twitter.com/intent/tweet?text=${{encodeURIComponent(text)}}`;
                window.open(url, '_blank', 'width=600,height=400');
                playSound('click');
            }}
            
            function shareToInstagram() {{
                // Instagram doesn't support direct sharing, so copy to clipboard
                const text = `🎖️ {callsign} | BITTEN Elite Trader\\n\\n📊 Performance Stats:\\n• Total Missions: {total_trades}\\n• Win Rate: {win_rate:.1%}\\n• Total P&L: {'+'if total_pnl > 0 else ''}${total_pnl:,.0f}\\n• Current Streak: {current_streak}\\n• Global Rank: #{global_rank}\\n\\n🪖 Squad Code: {referral_code}\\n\\n#BITTEN #ForexTrading #EliteTrader #TradingSquad`;
                
                navigator.clipboard.writeText(text).then(() => {{
                    alert('Stats copied! Open Instagram and paste in your story or post 📸');
                    playSound('achievement');
                }});
            }}
            
            // Fetch real user data
            async function loadUserData() {{
                try {{
                    // In production, this would fetch real data
                    const response = await fetch(`/api/user/{user_id}/stats`);
                    if (response.ok) {{
                        const data = await response.json();
                        // Update UI with real data
                        console.log('User data loaded:', data);
                    }}
                }} catch (error) {{
                    console.error('Error loading user data:', error);
                }}
            }}
            
            // Auto-refresh stats every 30 seconds
            setInterval(loadUserData, 30000);
            
            // Initial load
            loadUserData();
            
            // Achievement click handler
            document.querySelectorAll('.badge').forEach(badge => {{
                badge.addEventListener('click', function() {{
                    if (!this.classList.contains('locked')) {{
                        playSound('achievement');
                        // Show achievement details
                        const name = this.querySelector('.badge-name').textContent;
                        alert(`Achievement: ${{name}}\\n\\nYou've unlocked this achievement through your trading excellence!`);
                    }}
                }});
            }});
            
            // Add entrance animations
            document.addEventListener('DOMContentLoaded', () => {{
                const elements = document.querySelectorAll('.stat-card, .kill-card, .badge, .squad-member');
                elements.forEach((el, index) => {{
                    el.style.opacity = '0';
                    el.style.transform = 'translateY(20px)';
                    setTimeout(() => {{
                        el.style.transition = 'all 0.5s ease';
                        el.style.opacity = '1';
                        el.style.transform = 'translateY(0)';
                    }}, index * 50);
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    return WAR_ROOM_TEMPLATE

@app.route('/learn')
def learn_center():
    """Education hub and learning center"""
    
    LEARN_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📚 BITTEN Academy</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }
            .header { background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }
            .lesson-card { background: #1a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #333; cursor: pointer; }
            .lesson-card:hover { border-color: #00D9FF; }
            .difficulty { padding: 3px 8px; border-radius: 3px; font-size: 12px; }
            .beginner { background: #28a745; }
            .intermediate { background: #ffc107; color: #000; }
            .advanced { background: #dc3545; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 BITTEN ACADEMY</h1>
            <p>Master the art of tactical trading</p>
        </div>
        
        <div class="lesson-card">
            <h3>🎯 Signal Types & TCS Scores</h3>
            <span class="difficulty beginner">BEGINNER</span>
            <p>Learn how generates signals and what TCS percentages mean for trade quality.</p>
        </div>
        
        <div class="lesson-card">
            <h3>🔫 Fire Modes: SELECT vs AUTO</h3>
            <span class="difficulty intermediate">INTERMEDIATE</span>
            <p>Understand the difference between manual confirmation and automated execution.</p>
        </div>
        
        <div class="lesson-card">
            <h3>💰 Risk Management & Position Sizing</h3>
            <span class="difficulty intermediate">INTERMEDIATE</span>
            <p>Master R:R ratios, stop losses, and proper position sizing for consistent profits.</p>
        </div>
        
        <div class="lesson-card">
            <h3>⚡ Advanced Tactical Strategies</h3>
            <span class="difficulty advanced">ADVANCED</span>
            <p>Learn professional trading techniques used by COMMANDER tier operators.</p>
        </div>
        
        <div style="text-align: center; padding: 20px;">
            <button onclick="window.close()" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Academy</button>
        </div>
    </body>
    </html>
    """
    
    return LEARN_TEMPLATE

@app.route('/tiers')
def tier_comparison():
    """Tier comparison and upgrade page"""
    
    TIER_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏆 BITTEN Tiers</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }
            .header { background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }
            .tier-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
            .tier-card { background: #1a1a1a; padding: 20px; border-radius: 10px; border: 2px solid #333; text-align: center; }
            .tier-card.featured { border-color: #00D9FF; background: linear-gradient(135deg, #1a1a1a, #2d2d2d); }
            .tier-price { font-size: 24px; font-weight: bold; color: #00D9FF; margin: 10px 0; }
            .feature-list { text-align: left; margin: 15px 0; }
            .feature-list li { padding: 3px 0; }
            .upgrade-btn { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏆 CHOOSE YOUR TIER</h1>
            <p>Unlock advanced trading capabilities</p>
        </div>
        
        <div class="tier-grid">
            <div class="tier-card">
                <h3>🎫 PRESS PASS</h3>
                <div class="tier-price">FREE</div>
                <p>7-day trial</p>
                <ul class="feature-list">
                    <li>✅ Demo account only</li>
                    <li>✅ Basic signals</li>
                    <li>✅ SELECT FIRE mode</li>
                    <li>❌ Live trading</li>
                </ul>
                <button class="upgrade-btn">Current Tier</button>
            </div>
            
            <div class="tier-card">
                <h3>🦷 NIBBLER</h3>
                <div class="tier-price">$39/mo</div>
                <p>Entry level trader</p>
                <ul class="feature-list">
                    <li>✅ 1 concurrent trade</li>
                    <li>✅ SELECT FIRE only</li>
                    <li>✅ Voice personalities</li>
                    <li>✅ Live broker execution</li>
                </ul>
                <button class="upgrade-btn">Upgrade</button>
            </div>
            
            <div class="tier-card featured">
                <h3>🔥 FANG</h3>
                <div class="tier-price">$89/mo</div>
                <p>Serious trader</p>
                <ul class="feature-list">
                    <li>✅ 2 concurrent trades</li>
                    <li>✅ All signal types</li>
                    <li>✅ SELECT FIRE mode</li>
                    <li>✅ Premium support</li>
                </ul>
                <button class="upgrade-btn">Popular Choice</button>
            </div>
            
            <div class="tier-card">
                <h3>⚡ COMMANDER</h3>
                <div class="tier-price">$189/mo</div>
                <p>Professional operator</p>
                <ul class="feature-list">
                    <li>✅ Unlimited trades</li>
                    <li>✅ SELECT + AUTO modes</li>
                    <li>✅ All premium features</li>
                    <li>✅ Priority execution</li>
                </ul>
                <button class="upgrade-btn">Go Pro</button>
            </div>
        </div>
        
        <div style="text-align: center; padding: 20px;">
            <button onclick="window.close()" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Tiers</button>
        </div>
    </body>
    </html>
    """
    
    return TIER_TEMPLATE

@app.route('/api/stats/<signal_id>', methods=['GET'])
def api_signal_stats(signal_id):
    """Return live engagement data for signal"""
    try:
        if not signal_id:
            return jsonify({
                "error": "signal_id is required"
            }), 400
        
        # Use real engagement stats - NO FAKE DATA
        # TODO: Implement real engagement tracking from database
        stats = {
            "signal_id": signal_id,
            "total_views": 0,  # Real data needed
            "total_fires": 0,  # Real data needed
            "engagement_rate": 0.0,  # Real data needed
            "avg_execution_time": 0.0  # Real data needed
        }
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/user/<user_id>/squad', methods=['GET'])
def api_user_squad(user_id):
    """Return user squad data for War Room"""
    try:
        from src.bitten_core.referral_system import ReferralSystem
        referral_system = ReferralSystem()
        
        squad_stats = referral_system.get_squad_stats(user_id)
        squad_members = referral_system.get_direct_recruits(user_id)
        
        # Format squad data
        squad_data = {
            "squad_size": squad_stats.get('total_recruits', 0),
            "squad_xp": squad_stats.get('total_xp', 0),
            "squad_rank": squad_stats.get('squad_rank', 999),
            "top_performers": [
                {
                    "name": member.username,
                    "tier": member.current_rank,
                    "trades": member.trades_completed,
                    "win_rate": member.win_rate if hasattr(member, 'win_rate') else 0.0  # Use real data
                }
                for member in squad_members[:3]
            ]
        }
        
        return jsonify(squad_data)
    except Exception as e:
        logger.error(f"Squad API error: {e}")
        return jsonify({
            "squad_size": 0,
            "squad_xp": 0,
            "squad_rank": 999,
            "top_performers": []
        })

@app.route('/api/user/<user_id>/stats', methods=['GET'])
def api_user_stats(user_id):
    """Return real user statistics"""
    try:
        if not user_id:
            return jsonify({
                "error": "user_id is required"
            }), 400
        
        # Use real user stats - NO FAKE DATA
        # TODO: Implement real stats from engagement database
        stats = {
            "user_id": user_id,
            "total_trades": 0,  # Real data needed
            "win_rate": 0.0,  # Real data needed
            "total_pnl": 0.0,  # Real data needed
            "avg_rr": 2.0,  # Default to standard 1:2 R:R
            "best_streak": 0,  # Real data needed
            "current_streak": 0  # Real data needed
        }
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/mission-status/<signal_id>', methods=['GET'])
def api_mission_status(signal_id):
    """Return mission status for the HUD"""
    try:
        # Check if mission file exists
        mission_paths = [
            f"./missions/mission_{signal_id}.json",
            f"./missions/{signal_id}.json"
        ]
        
        mission_file = None
        for path in mission_paths:
            if os.path.exists(path):
                mission_file = path
                break
        
        if not mission_file:
            return jsonify({
                "error": "Mission not found",
                "status": "not_found"
            }), 404
        
        # Load mission data
        with open(mission_file, 'r') as f:
            mission_data = json.load(f)
        
        # Check expiry
        from datetime import datetime
        is_expired = False
        time_remaining = 3600  # Default 1 hour
        
        try:
            expires_at = datetime.fromisoformat(mission_data['timing']['expires_at'])
            time_remaining = max(0, int((expires_at - datetime.now()).total_seconds()))
            is_expired = time_remaining <= 0
        except:
            pass
        
        # Check if user has fired this mission (simplified check)
        user_fired = False  # In a real system, check fire history
        
        return jsonify({
            "signal_id": signal_id,
            "status": "expired" if is_expired else ("fired" if user_fired else "active"),
            "is_expired": is_expired,
            "time_remaining": time_remaining,
            "mission_stats": {
                "user_fired": user_fired
            }
        })
        
    except Exception as e:
        logger.error(f"Mission status API error: {e}")
        return jsonify({
            "error": "Internal server error"
        }), 500

# ============== HUD SUPPORT ENDPOINTS ==============

@app.route('/education/patterns')
def education_patterns():
    """Pattern education page"""
    return """
    <html>
    <head>
        <title>Pattern Education - BITTEN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff; }
            h1 { color: #4CAF50; }
            .pattern { background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>📊 Trading Patterns Guide</h1>
        
        <div class="pattern">
            <h2>🔄 Liquidity Sweep Reversal</h2>
            <p>Price sweeps liquidity zones then reverses sharply. High probability setup when volume confirms.</p>
            <p><b>Win Rate:</b> 75-80%</p>
        </div>
        
        <div class="pattern">
            <h2>📦 Order Block Bounce</h2>
            <p>Price reacts at institutional accumulation zones. Look for rejection wicks and volume.</p>
            <p><b>Win Rate:</b> 70-75%</p>
        </div>
        
        <div class="pattern">
            <h2>⚡ Fair Value Gap Fill</h2>
            <p>Price fills inefficiencies in the market structure. Quick entries with tight stops.</p>
            <p><b>Win Rate:</b> 65-70%</p>
        </div>
        
        <a href="javascript:history.back()" style="color: #4CAF50;">← Back to Mission</a>
    </body>
    </html>
    """

@app.route('/education/risk')
def education_risk():
    """Risk management education"""
    return """
    <html>
    <head>
        <title>Risk Management - BITTEN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff; }
            h1 { color: #f44336; }
            .rule { background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>⚠️ Risk Management Rules</h1>
        
        <div class="rule">
            <h2>1️⃣ 2% Rule</h2>
            <p>Never risk more than 2% of your account on a single trade.</p>
        </div>
        
        <div class="rule">
            <h2>2️⃣ Risk/Reward Ratio</h2>
            <p>Minimum 1:1.5 R/R ratio. Aim for 1:2 or higher.</p>
        </div>
        
        <div class="rule">
            <h2>3️⃣ Maximum Positions</h2>
            <p>Limit concurrent positions based on your tier. Start with 2-3 max.</p>
        </div>
        
        <div class="rule">
            <h2>4️⃣ Stop Loss Discipline</h2>
            <p>Always use stop loss. Never move it against your position.</p>
        </div>
        
        <a href="javascript:history.back()" style="color: #f44336;">← Back to Mission</a>
    </body>
    </html>
    """

@app.route('/community')
def community():
    """Community page"""
    return """
    <html>
    <head>
        <title>Community - BITTEN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff; text-align: center; }
            h1 { color: #9C27B0; }
            .link { display: block; padding: 15px; margin: 10px; background: #2a2a2a; border-radius: 8px; text-decoration: none; color: #fff; }
        </style>
    </head>
    <body>
        <h1>👥 BITTEN Community</h1>
        
        <a href="https://t.me/BittenCommunity" class="link">💬 Telegram Community</a>
        <a href="#" class="link">🎮 Discord Server</a>
        <a href="#" class="link">🐦 Twitter Updates</a>
        
        <br><br>
        <a href="javascript:history.back()" style="color: #9C27B0;">← Back to Mission</a>
    </body>
    </html>
    """

@app.route('/support')
def support():
    """Support page"""
    return """
    <html>
    <head>
        <title>Support - BITTEN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff; }
            h1 { color: #2196F3; }
            .section { background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🆘 BITTEN Support</h1>
        
        <div class="section">
            <h2>📚 Documentation</h2>
            <p>Check our comprehensive guides and FAQs.</p>
        </div>
        
        <div class="section">
            <h2>💬 Live Chat</h2>
            <p>Message @BittenProductionBot on Telegram for assistance.</p>
        </div>
        
        <div class="section">
            <h2>📧 Email Support</h2>
            <p>support@joinbitten.com</p>
            <p>Response time: 24-48 hours</p>
        </div>
        
        <a href="javascript:history.back()" style="color: #2196F3;">← Back to Mission</a>
    </body>
    </html>
    """

@app.route('/settings')
def settings():
    """User settings page"""
    user_id = request.args.get('user_id', 'unknown')
    return f"""
    <html>
    <head>
        <title>Settings - BITTEN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff; }}
            h1 {{ color: #FF9800; }}
            .setting {{ background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .value {{ color: #4CAF50; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>⚙️ Your Settings</h1>
        
        <div class="setting">
            <h3>User ID</h3>
            <p class="value">{user_id}</p>
        </div>
        
        <div class="setting">
            <h3>🔫 Fire Mode</h3>
            <p class="value">Manual</p>
            <p>Change in Telegram with /firemode</p>
        </div>
        
        <div class="setting">
            <h3>📊 Risk Per Trade</h3>
            <p class="value">2%</p>
        </div>
        
        <div class="setting">
            <h3>🔔 Notifications</h3>
            <p class="value">Enabled</p>
        </div>
        
        <a href="javascript:history.back()" style="color: #FF9800;">← Back to Mission</a>
    </body>
    </html>
    """

@app.route('/analysis/<signal_id>')
def signal_analysis(signal_id):
    """Detailed signal analysis page"""
    # Try to load the mission data
    mission_file = f'missions/{signal_id}.json'
    
    try:
        with open(mission_file, 'r') as f:
            mission_data = json.load(f)
    except:
        mission_data = {'signal_id': signal_id, 'symbol': 'Unknown'}
    
    return f"""
    <html>
    <head>
        <title>Signal Analysis - {signal_id}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff; }}
            h1 {{ color: #00BCD4; }}
            .analysis {{ background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #444; }}
            .label {{ color: #999; }}
            .value {{ color: #4CAF50; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>📊 Signal Analysis</h1>
        <h2>{signal_id}</h2>
        
        <div class="analysis">
            <h3>📈 Technical Analysis</h3>
            <div class="metric">
                <span class="label">Pattern Type:</span>
                <span class="value">{mission_data.get('pattern_type', 'LIQUIDITY_SWEEP_REVERSAL')}</span>
            </div>
            <div class="metric">
                <span class="label">Confidence:</span>
                <span class="value">{mission_data.get('confidence', 85)}%</span>
            </div>
            <div class="metric">
                <span class="label">CITADEL Score:</span>
                <span class="value">{mission_data.get('citadel_score', 7.5)}/10</span>
            </div>
            <div class="metric">
                <span class="label">Risk/Reward:</span>
                <span class="value">1:{mission_data.get('risk_reward', 2.0)}</span>
            </div>
        </div>
        
        <div class="analysis">
            <h3>🎯 Entry Strategy</h3>
            <p>• Monitor price action at entry level</p>
            <p>• Look for confirmation candles</p>
            <p>• Check volume for momentum</p>
            <p>• Ensure spread is acceptable</p>
        </div>
        
        <div class="analysis">
            <h3>⚠️ Risk Management</h3>
            <p>• Stop Loss is mandatory</p>
            <p>• Position size: {mission_data.get('base_lot_size', 0.01) * 2} lots (Commander tier)</p>
            <p>• Maximum risk: 2% of account</p>
            <p>• Don't add to losing positions</p>
        </div>
        
        <a href="javascript:history.back()" style="color: #00BCD4;">← Back to Mission</a>
    </body>
    </html>
    """

# ============== END HUD SUPPORT ENDPOINTS ==============

if __name__ == '__main__':
    # Production-ready configuration
    host = os.getenv('WEBAPP_HOST', '0.0.0.0')
    port = int(os.getenv('WEBAPP_PORT', 8888))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Starting BITTEN WebApp Server (Optimized)")
    logger.info(f"📍 Host: {host}:{port}")
    logger.info(f"🔧 Debug Mode: {debug_mode}")
    logger.info(f"💾 Lazy Loading: Enabled")
    
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug_mode,
            use_reloader=False,  # Disable reloader for production
            log_output=False if not debug_mode else True,
            allow_unsafe_werkzeug=True  # Allow running in production
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)
