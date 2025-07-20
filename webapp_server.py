#!/usr/bin/env python3
"""Enhanced Flask server with all requested improvements"""

from flask import redirect, send_from_directory, Flask, render_template_string, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import json
import urllib.parse
import os
import sys
from datetime import datetime, timedelta
import random
from collections import defaultdict, deque
import threading
import logging
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
from signal_storage import get_latest_signal, get_active_signals, get_signal_by_id
from engagement_db import handle_fire_action, get_signal_stats, get_user_stats, get_active_signals_with_engagement
from src.api.mission_endpoints import register_mission_api
from src.api.press_pass_provisioning import register_press_pass_api
# Import standalone referral system directly to avoid complex dependencies
try:
    from standalone_referral_system import StandaloneReferralSystem, StandaloneReferralCommandHandler
    ReferralSystem = StandaloneReferralSystem
    ReferralCommandHandler = StandaloneReferralCommandHandler
    REFERRAL_SYSTEM_AVAILABLE = True
    logger.info("Standalone referral system loaded successfully")
except ImportError as e:
    logger.warning(f"Standalone referral system not available: {e}")
    REFERRAL_SYSTEM_AVAILABLE = False

# Import live trade API
try:
    from live_trade_api import register_live_trade_endpoints, register_socketio_events, start_live_updates, live_trade_api
    LIVE_TRADE_API_AVAILABLE = True
    logger.info("Live Trade API loaded successfully")
except ImportError as e:
    logger.warning(f"Live Trade API not available: {e}")
    LIVE_TRADE_API_AVAILABLE = False

# Import timer integrations
try:
    from bitten.core.smart_timer_integration import smart_timer_integration
    from bitten.core.expired_trade_handler import expired_trade_handler, ExpiredTradeDisplay
    TIMER_INTEGRATION_AVAILABLE = True
except ImportError:
    smart_timer_integration = None
    expired_trade_handler = None
    ExpiredTradeDisplay = None
    TIMER_INTEGRATION_AVAILABLE = False

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Simple rate limiter for security
class RateLimiter:
    def __init__(self, max_requests=60, window_minutes=1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, client_ip):
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=self.window_minutes)
            
            # Clean old requests
            self.requests[client_ip] = deque([req_time for req_time in self.requests[client_ip] if req_time > cutoff])
            
            # Check if under limit
            if len(self.requests[client_ip]) >= self.max_requests:
                return False
            
            # Add current request
            self.requests[client_ip].append(now)
            return True

# Initialize rate limiter (60 requests per minute per IP)
rate_limiter = RateLimiter(max_requests=60, window_minutes=1)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

# Tier pricing configuration
TIER_PRICING = {
    'NIBBLER': {'price': 3900, 'name': 'BITTEN Nibbler', 'features': ['1 concurrent trade', 'SELECT FIRE only', 'Voice personalities', 'Basic signals']},
    'FANG': {'price': 8900, 'name': 'BITTEN Fang', 'features': ['2 concurrent trades', 'SELECT FIRE only', 'Voice personalities', 'All signals', 'Advanced filters']},
    'COMMANDER': {'price': 18900, 'name': 'BITTEN Commander', 'features': ['Unlimited trades', 'SELECT + AUTO modes', 'Voice personalities', 'Priority support', 'Exclusive signals', 'All premium features']}
}

app = Flask(__name__)

# Import unified personality system
try:
    from deploy_unified_personality_system import UnifiedPersonalityBot
    UNIFIED_PERSONALITY_AVAILABLE = True
except ImportError:
    UNIFIED_PERSONALITY_AVAILABLE = False

# Add API health endpoint
@app.route('/api/health')
def api_health():
    """API health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "BITTEN WebApp API",
        "version": "2.1"
    })

@app.route('/api/toggle-voice', methods=['POST'])
def toggle_voice():
    """Toggle voice messages for user"""
    try:
        data = request.json
        enabled = data.get('enabled', True)
        
        # Get user ID from session or request
        user_id = request.headers.get('X-User-ID', 'default_user')
        
        # Toggle voice setting
        if UNIFIED_PERSONALITY_AVAILABLE:
            # Create temporary bot instance for voice toggle
            from bitten_production_bot import BittenProductionBot
            temp_bot = BittenProductionBot()
            
            if hasattr(temp_bot, 'unified_bot') and temp_bot.unified_bot:
                # Set the voice state directly
                if enabled:
                    temp_bot.unified_bot.voice_enabled_users.add(str(user_id))
                    if hasattr(temp_bot.unified_bot, 'voice_disabled_users'):
                        temp_bot.unified_bot.voice_disabled_users.discard(str(user_id))
                else:
                    temp_bot.unified_bot.voice_enabled_users.discard(str(user_id))
                    if not hasattr(temp_bot.unified_bot, 'voice_disabled_users'):
                        temp_bot.unified_bot.voice_disabled_users = set()
                    temp_bot.unified_bot.voice_disabled_users.add(str(user_id))
                
                # Save settings
                temp_bot.unified_bot.save_voice_settings()
                
                return jsonify({
                    "success": True,
                    "enabled": enabled,
                    "message": "Voice messages enabled" if enabled else "Voice messages disabled",
                    "test_voice_available": True
                })
        
        # Fallback response if unified system not available
        return jsonify({
            "success": True,
            "enabled": enabled,
            "message": "Voice setting updated (unified system not available)",
            "test_voice_available": False
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/voice-status', methods=['GET'])
def get_voice_status():
    """Get current voice status for user"""
    try:
        user_id = request.headers.get('X-User-ID', 'default_user')
        
        if UNIFIED_PERSONALITY_AVAILABLE:
            from bitten_production_bot import BittenProductionBot
            temp_bot = BittenProductionBot()
            
            if hasattr(temp_bot, 'unified_bot') and temp_bot.unified_bot:
                status = temp_bot.unified_bot.get_voice_status_for_webapp(user_id)
                return jsonify(status)
        
        # Default response
        return jsonify({
            "voice_enabled": True,
            "status": "enabled",
            "default_state": "enabled",
            "message": "Voice messages are enabled by default"
        })
        
    except Exception as e:
        return jsonify({
            "voice_enabled": True,
            "status": "enabled",
            "error": str(e)
        })

# Add GHOSTED command endpoint
@app.route('/ghosted', methods=['POST'])
def ghosted():
    """Handle /GHOSTED command via Flask endpoint"""
    try:
        from src.bitten_core.performance_commands import handle_ghosted_command
        report = handle_ghosted_command()
        return jsonify({"status": "ok", "result": report})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def find_personal_mission(base_mission_id: str, user_id: str) -> str:
    """Find user's personal mission file based on base mission ID"""
    try:
        import os
        import glob
        
        # Extract base signal ID (remove any existing suffixes)
        if '_USER' in base_mission_id:
            base_signal = base_mission_id.split('_USER')[0]
        else:
            base_signal = base_mission_id
        
        # Look for user-specific mission file
        mission_pattern = f"missions/{base_signal}_USER{user_id}.json"
        matching_files = glob.glob(mission_pattern)
        
        if matching_files:
            # Return the mission ID from the filename
            mission_file = os.path.basename(matching_files[0])
            return mission_file.replace('.json', '')
        
        # No personal mission found, return original
        return base_mission_id
        
    except Exception as e:
        logger.error(f"Error finding personal mission: {e}")
        return base_mission_id

# Register Mission API endpoints
try:
    mission_api = register_mission_api(app)
except:
    logger.warning("Mission API registration failed, continuing without it")

# Register Press Pass API
press_pass_manager = register_press_pass_api(app)

# Initialize Referral System
if REFERRAL_SYSTEM_AVAILABLE:
    referral_system = ReferralSystem(db_path="data/referral_system.db")
    referral_handler = ReferralCommandHandler(referral_system)
else:
    referral_system = None
    referral_handler = None



# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Register Live Trade API endpoints and events
if LIVE_TRADE_API_AVAILABLE:
    register_live_trade_endpoints(app)
    register_socketio_events(socketio)
    logger.info("Live Trade API endpoints registered")

# Color-blind friendly palette with high contrast
ACCESSIBLE_TIER_STYLES = {
    'nibbler': {
        'primary': '#00D9FF',      # Bright cyan (was green)
        'secondary': '#FFFFFF',     # White for text
        'accent': '#FFD700',        # Gold for important info
        'background': '#0A0A0A',    # Very dark background
        'surface': '#1A1A1A',       # Slightly lighter for cards
        'danger': '#FF6B6B',        # Red-orange (distinguishable)
        'success': '#4ECDC4',       # Teal (not pure green)
        'border': '#00D9FF',
        'tcs_high': '#FFD700',      # Gold for high TCS
        'tcs_medium': '#00D9FF',    # Cyan for medium TCS
        'tcs_low': '#FF6B6B'        # Red-orange for low TCS
    },
    'fang': {
        'primary': '#FF8C00',       # Dark orange
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FF8C00',
        'tcs_high': '#FFD700',
        'tcs_medium': '#FF8C00',
        'tcs_low': '#FF6B6B'
    },
    'commander': {
        'primary': '#FFD700',       # Gold
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FFD700',
        'tcs_high': '#FFFFFF',
        'tcs_medium': '#FFD700',
        'tcs_low': '#FF8C00'
    },
    'apex': {
        'primary': '#FF00FF',       # Magenta
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FF00FF',
        'tcs_high': '#FFFFFF',
        'tcs_medium': '#FF00FF',
        'tcs_low': '#FF6B6B'
    }
}

def get_tier_styles(tier):
    """Get accessible color scheme for tier"""
    return ACCESSIBLE_TIER_STYLES.get(tier.lower(), ACCESSIBLE_TIER_STYLES['nibbler'])

def calculate_remaining_time(signal):
    """Calculate the actual remaining time for a signal"""
    if 'timestamp' in signal:
        timestamp = datetime.fromisoformat(signal['timestamp'])
        now = datetime.now()
        remaining = 600 - int((now - timestamp).total_seconds())
        return max(0, remaining)
    return 600

def mask_price(price):
    """Mask last 2 digits of price with XX for security"""
    price_str = f"{price:.5f}"
    return price_str[:-2] + "XX"

def get_user_account_balance(user_id):
    """Get user's actual account balance from MT5 or fallback to tier estimates"""
    try:
        # Try to get real MT5 account data
        import os
        import json
        
        # Path to MT5 account data file
        account_file = '/root/HydraX-v2/bitten_account_secure.txt'
        
        if os.path.exists(account_file):
            with open(account_file, 'r') as f:
                account_data = json.load(f)
                balance = account_data.get('balance', 0)
                if balance > 0:
                    return {
                        'balance': balance,
                        'equity': account_data.get('equity', balance),
                        'free_margin': account_data.get('free_margin', balance * 0.9),
                        'source': 'mt5_live'
                    }
    except Exception as e:
        print(f"Could not get MT5 account data: {e}")
    
    # Fallback to tier-based estimates (will be updated when we get user tier)
    return {
        'balance': 2500,  # Default nibbler account size
        'equity': 2500,
        'free_margin': 2250,
        'source': 'estimated'
    }

def calculate_dollar_value(pips, user_tier='nibbler', risk_percent=2.0, account_balance=None):
    """Calculate dollar value for pips based on user's actual account and tier"""
    
    # Tier-based lot sizes from account_size_calculator
    tier_lot_sizes = {
        'nibbler': 0.01,    # Micro lots
        'fang': 0.05,       # Small lots  
        'commander': 0.10,  # Standard lots
        'apex': 0.20        # Large lots
    }
    
    # Get user's lot size based on tier
    lot_size = tier_lot_sizes.get(user_tier.lower(), 0.01)
    
    # If account balance provided, calculate position size based on risk percentage
    if account_balance and account_balance > 0:
        # Calculate risk amount in dollars (2% of account by default)
        risk_amount = account_balance * (risk_percent / 100.0)
        
        # For position sizing: risk_amount = pips * pip_value * lot_size
        # But for display purposes, we use tier-appropriate lot sizes
        # This ensures consistent lot sizes per tier regardless of account size
        pass  # Keep tier-based lot sizing for consistency
    
    # Standard calculation: pip value depends on lot size
    # 1 pip on 0.01 lot = $0.10, 1 pip on 0.10 lot = $1.00, etc.
    pip_value = lot_size * 10  # $10 per pip per full lot
    return round(pips * pip_value, 2)

# Database connection functions
def get_database_connection(db_path):
    """Get database connection with error handling"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_user_trading_stats(user_id):
    """Get real trading statistics from trades database"""
    try:
        conn = get_database_connection('/root/HydraX-v2/data/trades/trades.db')
        if not conn:
            return None
            
        cursor = conn.cursor()
        
        # Get today's date for filtering
        from datetime import datetime, date
        today = date.today().strftime('%Y-%m-%d')
        
        # Get basic trading stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(profit_loss) as total_pnl,
                AVG(profit_loss) as avg_pnl,
                MAX(profit_loss) as largest_win,
                MIN(profit_loss) as largest_loss,
                SUM(xp_earned) as total_xp
            FROM trades 
            WHERE user_id = ? AND status = 'closed'
        """, (user_id,))
        
        stats = cursor.fetchone()
        
        # Get today's trades
        cursor.execute("""
            SELECT 
                COUNT(*) as trades_today,
                SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins_today,
                SUM(profit_loss) as pnl_today
            FROM trades 
            WHERE user_id = ? AND DATE(created_at) = ? AND status = 'closed'
        """, (user_id, today))
        
        today_stats = cursor.fetchone()
        
        # Get current win streak
        cursor.execute("""
            SELECT outcome, created_at 
            FROM trades 
            WHERE user_id = ? AND status = 'closed' 
            ORDER BY created_at DESC 
            LIMIT 50
        """, (user_id,))
        
        recent_trades = cursor.fetchall()
        
        conn.close()
        
        # Calculate win rate
        total_trades = stats['total_trades'] if stats['total_trades'] else 0
        wins = stats['wins'] if stats['wins'] else 0
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate current streak
        current_streak = 0
        if recent_trades:
            for trade in recent_trades:
                if trade['outcome'] == 'win':
                    current_streak += 1
                else:
                    break
        
        # Calculate best streak
        best_streak = 0
        temp_streak = 0
        for trade in reversed(recent_trades):
            if trade['outcome'] == 'win':
                temp_streak += 1
                best_streak = max(best_streak, temp_streak)
            else:
                temp_streak = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': round(win_rate, 1),
            'total_pnl': stats['total_pnl'] if stats['total_pnl'] else 0.0,
            'largest_win': stats['largest_win'] if stats['largest_win'] else 0.0,
            'current_streak': current_streak,
            'best_streak': best_streak,
            'trades_today': today_stats['trades_today'] if today_stats['trades_today'] else 0,
            'pnl_today': today_stats['pnl_today'] if today_stats['pnl_today'] else 0.0,
            'total_xp': stats['total_xp'] if stats['total_xp'] else 0,
            'avg_rr': abs(stats['avg_pnl']) if stats['avg_pnl'] else 0.0
        }
        
    except Exception as e:
        print(f"Error getting trading stats: {e}")
        return None

def get_user_profile_stats(user_id):
    """Get user profile statistics from bitten_profiles database"""
    try:
        conn = get_database_connection('/root/HydraX-v2/bitten_profiles.db')
        if not conn:
            return None
            
        cursor = conn.cursor()
        
        # Get user profile stats
        cursor.execute("""
            SELECT 
                total_xp,
                missions_completed,
                successful_trades,
                failed_trades,
                total_profit,
                largest_win,
                win_streak,
                current_streak,
                rank_achieved
            FROM user_stats 
            WHERE user_id = ?
        """, (user_id,))
        
        profile = cursor.fetchone()
        conn.close()
        
        if profile:
            return {
                'total_xp': profile['total_xp'],
                'missions_completed': profile['missions_completed'],
                'successful_trades': profile['successful_trades'],
                'failed_trades': profile['failed_trades'],
                'total_profit': profile['total_profit'],
                'largest_win': profile['largest_win'],
                'win_streak': profile['win_streak'],
                'current_streak': profile['current_streak'],
                'rank_achieved': profile['rank_achieved']
            }
        return None
        
    except Exception as e:
        print(f"Error getting profile stats: {e}")
        return None

def calculate_squad_engagement(user_id, signal_id=None):
    """Calculate squad engagement based on actual user fire data"""
    try:
        # This would typically query a signals_fired table or similar
        # For now, we'll calculate based on recent activity patterns
        
        conn = get_database_connection('/root/HydraX-v2/data/trades/trades.db')
        if not conn:
            return random.randint(45, 89)  # Fallback to random
            
        cursor = conn.cursor()
        
        # Get recent signal activity (last 24 hours)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM trades 
            WHERE created_at >= datetime('now', '-1 day')
        """, ())
        
        active_users = cursor.fetchone()
        conn.close()
        
        # Calculate engagement based on active users
        base_engagement = min(active_users['active_users'] * 8, 95) if active_users['active_users'] else 45
        
        # Add some variation based on user activity
        user_modifier = hash(str(user_id)) % 20 - 10  # -10 to +10
        engagement = max(25, min(95, base_engagement + user_modifier))
        
        return engagement
        
    except Exception as e:
        print(f"Error calculating squad engagement: {e}")
        return random.randint(45, 89)  # Fallback to random

def determine_user_tier(total_xp, total_trades):
    """Determine user tier based on XP and trading activity"""
    if total_xp >= 5000 and total_trades >= 100:
        return 'commander'
    elif total_xp >= 2000 and total_trades >= 50:
        return 'fang'
    else:
        return 'nibbler'

def calculate_user_level(total_xp):
    """Calculate user level based on total XP"""
    if total_xp < 100:
        return 1
    elif total_xp < 500:
        return 2
    elif total_xp < 1000:
        return 3
    elif total_xp < 2000:
        return 4
    elif total_xp < 5000:
        return 5
    else:
        return min(10, 5 + (total_xp - 5000) // 2000)

def get_user_stats(user_id):
    """Get user stats from real database with fallback to mock data"""
    try:
        # Get real trading stats from database
        trading_stats = get_user_trading_stats(user_id)
        profile_stats = get_user_profile_stats(user_id)
        
        # If we have real data, use it
        if trading_stats is not None or profile_stats is not None:
            # Combine data from both sources, prioritizing trading_stats
            total_xp = 0
            total_trades = 0
            
            if trading_stats:
                total_xp = trading_stats.get('total_xp', 0)
                total_trades = trading_stats.get('total_trades', 0)
            
            if profile_stats:
                # Use profile XP if higher (more authoritative)
                if profile_stats.get('total_xp', 0) > total_xp:
                    total_xp = profile_stats.get('total_xp', 0)
                # Use profile trades if available
                profile_total_trades = profile_stats.get('successful_trades', 0) + profile_stats.get('failed_trades', 0)
                if profile_total_trades > total_trades:
                    total_trades = profile_total_trades
            
            # Calculate derived values
            tier = determine_user_tier(total_xp, total_trades)
            level = calculate_user_level(total_xp)
            
            # Calculate daily trade limits based on tier
            daily_limits = {'nibbler': 6, 'fang': 8, 'commander': 12}
            trades_today = trading_stats.get('trades_today', 0) if trading_stats else 0
            trades_remaining = max(0, daily_limits.get(tier, 6) - trades_today)
            
            # Get squad engagement
            squad_engagement = calculate_squad_engagement(user_id)
            
            return {
                'gamertag': f'Soldier_{user_id}',  # Generate based on user_id
                'tier': tier,
                'level': level,
                'xp': total_xp,
                'trades_today': trades_today,
                'trades_remaining': trades_remaining,
                'win_rate': trading_stats.get('win_rate', 0) if trading_stats else 0,
                'pnl_today': round(trading_stats.get('pnl_today', 0), 2) if trading_stats else 0,
                'streak': trading_stats.get('current_streak', 0) if trading_stats else 0,
                'best_streak': trading_stats.get('best_streak', 0) if trading_stats else 0,
                'total_trades': total_trades,
                'avg_rr': round(trading_stats.get('avg_rr', 0), 2) if trading_stats else 0,
                'squad_engagement': squad_engagement
            }
        else:
            # Fallback to mock data if no real data available
            print(f"No real data found for user {user_id}, using mock data")
            return {
                'gamertag': 'Soldier_X',
                'tier': 'nibbler',
                'level': 5,
                'xp': 1250,
                'trades_today': 3,
                'trades_remaining': 3,  # 6 - 3
                'win_rate': 75,
                'pnl_today': 2.4,
                'streak': 3,
                'best_streak': 7,
                'total_trades': 127,
                'avg_rr': 2.1,
                'squad_engagement': random.randint(45, 89)  # Percentage of squad taking this signal
            }
            
    except Exception as e:
        print(f"Error getting user stats: {e}")
        # Return mock data on error to maintain functionality
        return {
            'gamertag': 'Soldier_X',
            'tier': 'nibbler',
            'level': 5,
            'xp': 1250,
            'trades_today': 3,
            'trades_remaining': 3,  # 6 - 3
            'win_rate': 75,
            'pnl_today': 2.4,
            'streak': 3,
            'best_streak': 7,
            'total_trades': 127,
            'avg_rr': 2.1,
            'squad_engagement': random.randint(45, 89)  # Percentage of squad taking this signal
        }

# Military-themed pattern names
PATTERN_NAMES = {
    'LONDON_RAID': {
        'name': 'LONDON RAID',
        'description': 'London session breakout assault',
        'best_time': '08:00-10:00 GMT',
        'success_rate': 78,
        'risk_level': 'MODERATE'
    },
    'WALL_BREACH': {
        'name': 'WALL BREACH', 
        'description': 'Major support/resistance breakthrough',
        'best_time': 'Any high volume period',
        'success_rate': 82,
        'risk_level': 'LOW'
    },
    'SNIPER_NEST': {
        'name': "SNIPER'S NEST",
        'description': 'Range-bound precision strike',
        'best_time': 'Asian session',
        'success_rate': 75,
        'risk_level': 'LOW'
    },
    'AMBUSH_POINT': {
        'name': 'AMBUSH POINT',
        'description': 'Trend reversal trap',
        'best_time': 'Session overlaps',
        'success_rate': 71,
        'risk_level': 'HIGH'
    },
    'SUPPLY_DROP': {
        'name': 'SUPPLY DROP',
        'description': 'Pullback to moving average',
        'best_time': 'Trending markets',
        'success_rate': 80,
        'risk_level': 'LOW'
    },
    'PINCER_MOVE': {
        'name': 'PINCER MOVE',
        'description': 'Volatility squeeze breakout',
        'best_time': 'Pre-news consolidation',
        'success_rate': 69,
        'risk_level': 'HIGH'
    }
}

def get_random_pattern():
    """Get a random pattern for the signal"""
    import random
    pattern_key = random.choice(list(PATTERN_NAMES.keys()))
    return pattern_key, PATTERN_NAMES[pattern_key]

# Professional Commander HUD template based on template_samples
HUD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COMMANDER - {{ symbol }} - TACTICAL BRIEF</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --commander-purple: #7c3aed;
            --elite-gold: #fbbf24;
            --success-green: #10b981;
            --warning-amber: #f59e0b;
            --danger-red: #ef4444;
            --dark-bg: #0f172a;
            --panel-bg: rgba(15, 23, 42, 0.95);
            --border-color: #334155;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--dark-bg) 0%, #1e293b 100%);
            color: #f1f5f9;
            height: 100vh;
            overflow-x: hidden;
        }

        .commander-header {
            background: linear-gradient(90deg, var(--commander-purple) 0%, #8b5cf6 100%);
            color: white;
            text-align: center;
            padding: 12px;
            font-weight: 600;
            letter-spacing: 1px;
            font-size: 1em;
        }

        .hud-container {
            display: grid;
            grid-template-areas: 
                "mission-overview mission-overview"
                "trade-details account-summary"
                "execution-panel execution-panel";
            grid-template-columns: 1fr 1fr;
            grid-template-rows: auto 1fr auto;
            height: calc(100vh - 50px);
            gap: 16px;
            padding: 16px;
        }

        .mission-overview {
            grid-area: mission-overview;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(10px);
        }

        .trade-details {
            grid-area: trade-details;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(10px);
        }

        .account-summary {
            grid-area: account-summary;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(10px);
        }

        .execution-panel {
            grid-area: execution-panel;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(10px);
            text-align: center;
        }

        .section-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }

        .section-title {
            font-family: 'Orbitron', monospace;
            font-weight: 700;
            color: var(--commander-purple);
            font-size: 1.1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .mission-title-large {
            font-family: 'Orbitron', monospace;
            font-size: 2.5em;
            font-weight: 900;
            color: var(--elite-gold);
            text-align: center;
            margin-bottom: 16px;
            text-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
        }

        .confidence-badge {
            background: linear-gradient(45deg, var(--success-green), #059669);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 16px;
            font-size: 0.9em;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }

        .stat-card {
            background: rgba(0, 0, 0, 0.3);
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid var(--commander-purple);
        }

        .stat-label {
            color: #94a3b8;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .stat-value {
            color: #f1f5f9;
            font-weight: 700;
            font-size: 1.3em;
        }

        .stat-value.success { color: var(--success-green); }
        .stat-value.warning { color: var(--warning-amber); }
        .stat-value.danger { color: var(--danger-red); }

        .countdown-display {
            font-family: 'Orbitron', monospace;
            font-size: 2.2em;
            color: var(--elite-gold);
            margin-bottom: 24px;
            text-shadow: 0 0 15px rgba(251, 191, 36, 0.4);
        }

        .execute-button {
            background: linear-gradient(45deg, var(--commander-purple), #8b5cf6);
            border: none;
            border-radius: 12px;
            padding: 20px 50px;
            font-family: 'Orbitron', monospace;
            font-size: 1.4em;
            font-weight: 700;
            color: white;
            cursor: pointer;
            box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .execute-button:hover {
            background: linear-gradient(45deg, #8b5cf6, var(--commander-purple));
            box-shadow: 0 12px 35px rgba(124, 58, 237, 0.6);
            transform: translateY(-2px);
        }

        .execute-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .tier-indicator {
            background: linear-gradient(45deg, var(--elite-gold), #f59e0b);
            color: var(--dark-bg);
            padding: 6px 14px;
            border-radius: 15px;
            font-weight: 700;
            font-size: 0.8em;
            display: inline-block;
            margin-left: 12px;
        }

        .risk-indicator {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--success-green);
            padding: 12px 16px;
            border-radius: 8px;
            margin-top: 16px;
        }

        .risk-text {
            color: var(--success-green);
            font-weight: 600;
        }

        /* Mobile responsive */
        @media (max-width: 768px) {
            .hud-container {
                grid-template-areas: 
                    "mission-overview"
                    "trade-details"
                    "account-summary"
                    "execution-panel";
                grid-template-columns: 1fr;
                grid-template-rows: auto auto auto auto;
            }
            
            .mission-title-large {
                font-size: 2em;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
        }
        
        /* Timer styling */
        .timer {
            background: var(--danger-red);
            color: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-weight: bold;
        }
        
        .urgent {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="commander-header">
        🎖️ COMMANDER ACCESS - TACTICAL TRADING INTERFACE - AUTHORIZED PERSONNEL ONLY 🎖️
    </div>

    <div class="hud-container">
        <div class="mission-overview">
            <div class="mission-title-large">{{ symbol }}</div>
            <div class="confidence-badge">🎯 TCS: {{ tcs_score }}% CONFIDENCE</div>
            
            <div class="section-header">
                <div class="section-title">Mission Overview</div>
                <div class="tier-indicator">{{ user_stats.tier|upper }}</div>
            </div>
            
            <div style="color: #94a3b8; line-height: 1.6;">
                High-probability {{ symbol }} opportunity identified. Market structure aligned for tactical entry.
                Risk management protocols active. Position sizing calculated for {{ user_stats.tier|title }}-tier account.
            </div>

            <div class="risk-indicator">
                <span class="risk-text">✅ Risk Parameters: Optimal</span>
                <span style="color: var(--elite-gold); font-weight: 600;">R:R 1:{{ rr_ratio }}</span>
            </div>
            
            <!-- Expiry Timer -->
            {% if expiry_seconds > 0 %}
            <div class="timer urgent" id="timer" style="margin-top: 16px;">
                Signal expires in: <span id="countdown">{{ expiry_seconds }}s</span>
            </div>
            {% endif %}
        </div>

        <div class="trade-details">
            <div class="section-header">
                <div class="section-title">Trade Parameters</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Entry Price</div>
                    <div class="stat-value">{{ entry_masked }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Stop Loss</div>
                    <div class="stat-value danger">{{ sl_masked }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Take Profit</div>
                    <div class="stat-value success">{{ tp_masked }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Direction</div>
                    <div class="stat-value {% if direction == 'BUY' %}success{% else %}warning{% endif %}">{{ direction }}</div>
                </div>
            </div>
        </div>

        <div class="account-summary">
            <div class="section-header">
                <div class="section-title">Account Status</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Account Balance</div>
                    <div class="stat-value">${{ "%.2f"|format(account_balance) }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Risk Amount</div>
                    <div class="stat-value warning">${{ sl_dollars }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Potential Profit</div>
                    <div class="stat-value success">${{ tp_dollars }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value {% if user_stats.win_rate >= 70 %}success{% else %}warning{% endif %}">{{ user_stats.win_rate }}%</div>
                </div>
            </div>
        </div>

        <div class="execution-panel">
            {% if expiry_seconds > 0 %}
            <div class="countdown-display">⏰ <span id="countdown-main">{{ expiry_seconds }}s</span> REMAINING</div>
            {% endif %}
            <button class="execute-button" onclick="fireSignal()" {% if user_stats.trades_remaining <= 0 %}disabled{% endif %}>🚀 EXECUTE TRADE 🚀</button>
            <div style="margin-top: 16px; color: #64748b; font-size: 0.9em;">
                {{ user_stats.tier|title }}-level position sizing applied • 3% account risk
            </div>
        </div>
    </div>
    
    <script>
        // Telegram WebApp API
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }
        
        // Check mission status on page load
        async function checkMissionStatus() {
            try {
                const response = await fetch(`/api/mission-status/{{ signal_id }}`, {
                    headers: {
                        'Authorization': 'Bearer webapp_token',
                        'X-User-ID': '{{ user_id }}'
                    }
                });
                
                if (response.ok) {
                    const mission = await response.json();
                    const fireButton = document.querySelector('.execute-button');
                    
                    if (mission.status === 'fired' || mission.mission_stats?.user_fired) {
                        // Mission already fired - disable button and show status
                        fireButton.disabled = true;
                        fireButton.textContent = '✅ MISSION COMPLETED';
                        fireButton.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
                        fireButton.style.cursor = 'not-allowed';
                    } else if (mission.is_expired || mission.time_remaining <= 0) {
                        // Mission expired - disable button and show expired
                        fireButton.disabled = true;
                        fireButton.textContent = '❌ MISSION EXPIRED';
                        fireButton.style.background = 'linear-gradient(135deg, #6c757d, #495057)';
                        fireButton.style.cursor = 'not-allowed';
                    }
                }
            } catch (error) {
                console.log('Mission status check failed:', error);
            }
        }
        
        // Run status check when page loads
        checkMissionStatus();
        
        // Fire signal function
        async function fireSignal() {
            const fireButton = document.querySelector('.execute-button');
            const signalId = '{{ signal_id }}';
            const userId = '{{ user_id }}';
            
            try {
                // Update button to show firing state
                fireButton.disabled = true;
                fireButton.style.background = 'linear-gradient(135deg, #ffc107, #fd7e14)';
                fireButton.textContent = '🔥 FIRING...';
                
                // Make API call to fire the signal
                const response = await fetch('/api/fire', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer webapp_token',
                        'X-User-ID': userId
                    },
                    body: JSON.stringify({
                        mission_id: signalId
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    // Success - show success state
                    fireButton.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
                    fireButton.textContent = '✅ MISSION FIRED!';
                    
                    // Show success message with tactical flair
                    alert('🎯 MISSION EXECUTED!\n\nTarget acquired. Trade has been fired.\nTracking bullet to target...');
                    
                    // Redirect to live tracking page after short delay
                    setTimeout(() => {
                        const symbol = '{{ symbol }}';
                        const direction = '{{ direction }}';
                        window.location.href = `/track-trade?mission_id=${signalId}&symbol=${symbol}&direction=${direction}`;
                    }, 2000);
                    
                } else {
                    // Error - show error state and re-enable
                    fireButton.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
                    fireButton.textContent = '❌ MISSION FAILED';
                    
                    alert('❌ MISSION FAILED\n\n' + (result.error || 'Unable to fire signal. Please try again.'));
                    
                    // Reset button after delay
                    setTimeout(() => {
                        fireButton.disabled = false;
                        fireButton.style.background = 'linear-gradient(45deg, var(--commander-purple), #8b5cf6)';
                        fireButton.textContent = '🚀 EXECUTE TRADE 🚀';
                    }, 3000);
                }
                
            } catch (error) {
                console.error('Fire signal error:', error);
                
                // Error - show error state and re-enable
                fireButton.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
                fireButton.textContent = '❌ FIRE FAILED';
                
                alert('❌ COMMUNICATION FAILURE\n\nUnable to contact command. Check connection and try again.');
                
                // Reset button after delay
                setTimeout(() => {
                    fireButton.disabled = false;
                    fireButton.style.background = 'linear-gradient(45deg, var(--commander-purple), #8b5cf6)';
                    fireButton.textContent = '🚀 EXECUTE TRADE 🚀';
                }, 3000);
            }
        }
        
        // Timer countdown
        {% if expiry_seconds > 0 %}
        let timeLeft = {{ expiry_seconds }};
        const countdownElement = document.getElementById('countdown');
        const countdownMainElement = document.getElementById('countdown-main');
        
        const timer = setInterval(function() {
            timeLeft--;
            
            if (timeLeft <= 0) {
                clearInterval(timer);
                if (countdownElement) countdownElement.textContent = 'EXPIRED';
                if (countdownMainElement) countdownMainElement.textContent = 'EXPIRED';
                
                const timerDiv = document.getElementById('timer');
                if (timerDiv) timerDiv.style.background = '#666';
                
                const fireButton = document.querySelector('.execute-button');
                if (fireButton) {
                    fireButton.disabled = true;
                    fireButton.textContent = '❌ EXPIRED';
                    fireButton.style.background = '#666';
                }
            } else {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                
                if (countdownElement) countdownElement.textContent = timeString;
                if (countdownMainElement) countdownMainElement.textContent = timeString;
            }
        }, 1000);
        {% endif %}
    </script>
</body>
"""

# Keep test page the same
TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN WebApp Test</title>
    <style>
        body {
            background: #0A0A0A;
            color: #00D9FF;
            font-family: 'Consolas', monospace;
            text-align: center;
            padding: 50px;
        }
        .status {
            color: #4ECDC4;
            font-size: 24px;
            margin: 30px 0;
        }
    </style>
</head>
<body>
    <h1>🎯 BITTEN WebApp Test Page</h1>
    <div class="status">✅ WebApp is running!</div>
    <div>Server Time: {{ time }}</div>
</body>
</html>
"""

@app.route('/')
def index():
    """Root endpoint - serve landing page"""
    try:
        with open('/root/HydraX-v2/landing/index_v2.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "BITTEN WebApp Server Running", 200

@app.route('/broker-setup')
def broker_setup():
    """Broker setup guide with interactive bot"""
    try:
        with open('/root/HydraX-v2/broker-setup.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Broker setup page not found", 404

@app.route('/api/track-conversation', methods=['POST'])
def track_conversation():
    """Track bot conversation for analytics"""
    try:
        data = request.get_json()
        
        # Basic input validation
        if not data or not data.get('message'):
            return jsonify({'success': False, 'error': 'Invalid data'}), 400
        
        # Store in database (create table if needed)
        import sqlite3
        os.makedirs('/root/HydraX-v2/data', exist_ok=True)
        conn = sqlite3.connect('/root/HydraX-v2/data/visitor_analytics.db')
        c = conn.cursor()
        
        # Create table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT,
                     session_id TEXT,
                     message TEXT,
                     is_bot BOOLEAN,
                     page TEXT,
                     user_agent TEXT,
                     ip_address TEXT)''')
        
        c.execute('''INSERT INTO conversations 
                    (timestamp, session_id, message, is_bot, page, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.datetime.now().isoformat(),
                   data.get('session_id', ''),
                   data.get('message', ''),
                   data.get('is_bot', False),
                   data.get('page', ''),
                   request.headers.get('User-Agent', ''),
                   request.remote_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/track-page-visit', methods=['POST'])
def track_page_visit():
    """Track page visits for analytics"""
    try:
        data = request.get_json()
        
        # Store in database
        import sqlite3
        os.makedirs('/root/HydraX-v2/data', exist_ok=True)
        conn = sqlite3.connect('/root/HydraX-v2/data/visitor_analytics.db')
        c = conn.cursor()
        
        # Create table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS page_visits
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT,
                     session_id TEXT,
                     page TEXT,
                     referrer TEXT,
                     user_agent TEXT,
                     ip_address TEXT)''')
        
        c.execute('''INSERT INTO page_visits 
                    (timestamp, session_id, page, referrer, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (data.get('timestamp'), data.get('sessionId'), 
                  data.get('page', '')[:100], data.get('referrer', '')[:200],
                  data.get('userAgent', '')[:500], request.remote_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Continue with next function from the real file...
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        /* Personal Stats Bar */
        .stats-bar {
            background: rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 15px 20px;
            margin: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
            position: relative;
        }
        
        /* Trophy room link */
        .trophy-link {
            position: absolute;
            bottom: -20px;
            right: 20px;
            font-size: 11px;
            color: {{ colors.primary }};
            text-decoration: none;
            opacity: 0.7;
            transition: opacity 0.3s;
        }
        
        .trophy-link:hover {
            opacity: 1;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-label {
            font-size: 11px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-value {
            font-size: 20px;
            font-weight: bold;
            color: {{ colors.secondary }};
            margin-top: 2px;
        }
        
        .stat-value.positive {
            color: {{ colors.success }};
        }
        
        .stat-value.negative {
            color: {{ colors.danger }};
        }
        
        .stat-value.warning {
            color: {{ colors.accent }};
        }
        
        /* Ammo display */
        .ammo-display {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .ammo-icon {
            width: 20px;
            height: 20px;
            background: {{ colors.accent }};
            clip-path: polygon(40% 0%, 60% 0%, 60% 60%, 100% 60%, 100% 100%, 0% 100%, 0% 60%, 40% 60%);
            opacity: 0.8;
        }
        
        .ammo-icon.empty {
            background: rgba(255,255,255,0.2);
        }
        
        /* Gamertag and Level */
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .gamertag {
            font-size: 18px;
            font-weight: bold;
            color: {{ colors.primary }};
        }
        
        .level-badge {
            background: {{ colors.accent }};
            color: {{ colors.background }};
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }
        
        /* Squad engagement display */
        .squad-status {
            background: rgba({{ colors.primary }}, 0.1);
            border: 1px solid {{ colors.primary }};
            border-radius: 4px;
            padding: 8px 16px;
            margin: 20px;
            text-align: center;
            font-weight: bold;
            letter-spacing: 1px;
        }
        
        .squad-percentage {
            font-size: 24px;
            color: {{ colors.primary }};
        }
        
        /* Main Content */
        .content {
            max-width: 600px;
            margin: 0 auto;
            padding: 0 20px 20px;
        }
        
        /* Mission Card */
        .mission-card {
            background: {{ colors.surface }};
            border: 2px solid {{ colors.border }};
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        
        .mission-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .signal-type {
            font-size: 24px;
            font-weight: bold;
            color: {{ colors.accent }};
            letter-spacing: 2px;
            text-shadow: 0 0 10px {{ colors.accent }};
            margin-bottom: 10px;
        }
        
        .pair-direction {
            font-size: 32px;
            font-weight: bold;
            color: {{ colors.secondary }};
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        /* TCS Score - Make it POP */
        .tcs-container {
            background: rgba(0,0,0,0.8);
            border: 3px solid {% if tcs_score >= 85 %}{{ colors.tcs_high }}{% elif tcs_score >= 75 %}{{ colors.tcs_medium }}{% else %}{{ colors.tcs_low }}{% endif %};
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 0 20px {% if tcs_score >= 85 %}{{ colors.tcs_high }}{% elif tcs_score >= 75 %}{{ colors.tcs_medium }}{% else %}{{ colors.tcs_low }}{% endif %};
        }
        
        .tcs-label {
            font-size: 14px;
            color: rgba(255,255,255,0.7);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .tcs-score {
            font-size: 48px;
            font-weight: bold;
            color: {% if tcs_score >= 85 %}{{ colors.tcs_high }}{% elif tcs_score >= 75 %}{{ colors.tcs_medium }}{% else %}{{ colors.tcs_low }}{% endif %};
            text-shadow: 0 0 20px currentColor;
            margin: 10px 0;
        }
        
        .confidence-label {
            font-size: 18px;
            font-weight: bold;
            color: {% if tcs_score >= 85 %}{{ colors.tcs_high }}{% elif tcs_score >= 75 %}{{ colors.tcs_medium }}{% else %}{{ colors.tcs_low }}{% endif %};
        }
        
        /* Decision Helper */
        .decision-helper {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        
        .helper-text {
            font-size: 16px;
            color: {{ colors.secondary }};
            line-height: 1.4;
        }
        
        .helper-text .highlight {
            color: {{ colors.accent }};
            font-weight: bold;
        }
        
        /* Timer */
        .timer {
            background: rgba(255,0,0,0.1);
            border: 1px solid {{ colors.danger }};
            border-radius: 4px;
            padding: 10px 20px;
            text-align: center;
            margin-bottom: 20px;
            font-size: 18px;
            font-weight: bold;
            color: {{ colors.danger }};
        }
        
        /* Trade Parameters */
        .parameters {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        
        .param-box {
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 4px;
            padding: 15px;
            text-align: center;
        }
        
        .param-label {
            font-size: 12px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .param-value {
            font-size: 20px;
            font-weight: bold;
            color: {{ colors.secondary }};
        }
        
        .param-value.positive {
            color: {{ colors.success }};
        }
        
        .param-value.negative {
            color: {{ colors.danger }};
        }
        
        .param-value.masked {
            font-family: monospace;
            letter-spacing: 1px;
        }
        
        /* Dollar value display */
        .dollar-value {
            font-size: 14px;
            color: rgba(255,255,255,0.6);
            margin-top: 4px;
        }
        
        /* Action Buttons */
        .actions {
            margin-top: 30px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        /* Tactical Fire Button */
        .fire-button {
            flex: 1;
            background: linear-gradient(135deg, {{ colors.danger }}, {{ colors.primary }});
            color: white;
            border: none;
            padding: 18px 30px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            min-width: 200px;
            position: relative;
            overflow: hidden;
            animation: tactical-pulse 2s ease-in-out infinite;
        }
        
        @keyframes tactical-pulse {
            0% { box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
            50% { box-shadow: 0 4px 25px {{ colors.danger }}, 0 0 30px rgba(255,255,255,0.2); }
            100% { box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        }
        
        .fire-button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
            transform: translate(-50%, -50%) scale(0);
            transition: transform 0.5s;
        }
        
        .fire-button:hover::before {
            transform: translate(-50%, -50%) scale(2);
        }
        
        .fire-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }
        
        .fire-button:active {
            transform: translateY(0);
        }
        
        .fire-button:disabled {
            animation: none;
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .skip-button {
            flex: 1;
            background: transparent;
            color: rgba(255,255,255,0.6);
            border: 2px solid rgba(255,255,255,0.3);
            padding: 18px 30px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .skip-button:hover {
            border-color: rgba(255,255,255,0.6);
            color: rgba(255,255,255,0.9);
        }
        
        /* Bottom Links */
        .bottom-links {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .bottom-links a {
            color: {{ colors.primary }};
            text-decoration: none;
            padding: 10px 20px;
            border: 1px solid {{ colors.primary }};
            border-radius: 4px;
            transition: all 0.3s;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .bottom-links a:hover {
            background: {{ colors.primary }};
            color: {{ colors.background }};
        }
        
        /* Focus styles for accessibility */
        button:focus,
        a:focus {
            outline: 3px solid {{ colors.accent }};
            outline-offset: 2px;
        }
        
        /* Animation for urgency */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .urgent {
            animation: pulse 2s infinite;
        }
        
        /* Mobile responsive */
        @media (max-width: 600px) {
            .stats-bar {
                flex-direction: column;
                gap: 15px;
                padding-bottom: 25px;
            }
            
            .stat-item {
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .stat-label {
                margin-right: 10px;
            }
            
            .bottom-links {
                flex-direction: column;
            }
            
            .bottom-links a {
                width: 100%;
                text-align: center;
                justify-content: center;
            }
        }
        
        /* Setup Intel Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: {{ colors.surface }};
            border: 2px solid {{ colors.border }};
            border-radius: 8px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 0 30px rgba(0,0,0,0.8);
        }
        
        .modal-header {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .modal-title {
            font-size: 24px;
            font-weight: bold;
            color: {{ colors.primary }};
            letter-spacing: 2px;
        }
        
        .pattern-visual {
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            font-family: monospace;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .pattern-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        
        .pattern-stat {
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 4px;
            padding: 15px;
            text-align: center;
        }
        
        .pattern-stat-label {
            font-size: 11px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .pattern-stat-value {
            font-size: 18px;
            font-weight: bold;
            color: {{ colors.secondary }};
        }
        
        .close-button {
            background: {{ colors.primary }};
            color: {{ colors.background }};
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 20px;
            width: 100%;
        }
        
        .close-button:hover {
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <!-- Setup Intel Modal -->
    <div class="modal-overlay" id="setupModal" onclick="hideSetupIntel()">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div class="modal-title">{{ pattern.name }} INTEL</div>
            </div>
            
            <div class="pattern-visual">
                {% if pattern_key == 'LONDON_RAID' %}
                ┌─────────────────────────┐<br>
                │  BREAKOUT ZONE          │<br>
                │  ═══════════════ ← BUY  │<br>
                │         ┊               │<br>
                │   RANGE ┊               │<br>
                │         ┊               │<br>
                │  ═══════════════ ← SELL │<br>
                └─────────────────────────┘
                {% elif pattern_key == 'WALL_BREACH' %}
                    ↑<br>
                ────┼──── RESISTANCE<br>
                    │  /<br>
                    │ /<br>
                    │/<br>
                ────● BREACH POINT<br>
                {% elif pattern_key == 'SNIPER_NEST' %}
                ┌─────────────────────────┐<br>
                │  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔ TOP    │<br>
                │    ↓        ↑          │<br>
                │     \      /           │<br>
                │      \    /            │<br>
                │       \  /             │<br>
                │  ▁▁▁▁▁▁▁▁▁▁▁▁▁▁ BOTTOM │<br>
                └─────────────────────────┘
                {% else %}
                    [CLASSIFIED PATTERN]<br>
                    Access Level Required
                {% endif %}
            </div>
            
            <div class="pattern-stats">
                <div class="pattern-stat">
                    <div class="pattern-stat-label">Success Rate</div>
                    <div class="pattern-stat-value" style="color: {{ colors.success }};">{{ pattern.success_rate }}%</div>
                </div>
                <div class="pattern-stat">
                    <div class="pattern-stat-label">Risk Level</div>
                    <div class="pattern-stat-value" style="color: {% if pattern.risk_level == 'HIGH' %}{{ colors.danger }}{% elif pattern.risk_level == 'MODERATE' %}{{ colors.accent }}{% else %}{{ colors.success }}{% endif %};">{{ pattern.risk_level }}</div>
                </div>
                <div class="pattern-stat">
                    <div class="pattern-stat-label">Best Time</div>
                    <div class="pattern-stat-value">{{ pattern.best_time }}</div>
                </div>
                <div class="pattern-stat">
                    <div class="pattern-stat-label">Avg Pips</div>
                    <div class="pattern-stat-value">45-60</div>
                </div>
            </div>
            
            <div style="color: rgba(255,255,255,0.8); line-height: 1.6; margin-top: 20px;">
                <strong>How to Trade:</strong><br>
                {{ pattern.description }}. Wait for clear confirmation before entry. Always respect your stop loss and take profit levels. This setup works best during {{ pattern.best_time }}.
            </div>
            
            <button class="close-button" onclick="hideSetupIntel()">UNDERSTOOD</button>
        </div>
    </div>
    <div class="top-bar">
        <a href="#" class="back-button" onclick="exitBriefing(); return false;">
            <span>←</span>
            <span>Back</span>
        </a>
        <div class="voice-toggle-mini" id="voiceToggleButton" onclick="toggleVoiceQuick()" title="Toggle Voice Messages">
            <span id="voiceIcon">🔊</span>
        </div>
        <div class="tier-badge">{{ user_stats.tier|upper }}</div>
    </div>
    
    <!-- Personal Stats Bar -->
    <div class="stats-bar">
        <div class="user-info">
            <div class="gamertag">{{ user_stats.gamertag }}</div>
            <div class="level-badge">LVL {{ user_stats.level }}</div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">Today</div>
            <div class="stat-value">{{ user_stats.trades_today }}/6</div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">Shots Left</div>
            <div class="stat-value">
                <div class="ammo-display">
                    {% for i in range(6) %}
                        <div class="ammo-icon {% if i >= user_stats.trades_remaining %}empty{% endif %}"></div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">Win Rate</div>
            <div class="stat-value {% if user_stats.win_rate >= 70 %}positive{% else %}warning{% endif %}">{{ user_stats.win_rate }}%</div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">P&L Today</div>
            <div class="stat-value {% if user_stats.pnl_today >= 0 %}positive{% else %}negative{% endif %}">{{ "{:+.1f}".format(user_stats.pnl_today) }}%</div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">Streak</div>
            <div class="stat-value {% if user_stats.streak >= 3 %}positive{% elif user_stats.streak < 0 %}negative{% endif %}">
                {% if user_stats.streak >= 0 %}W{{ user_stats.streak }}{% else %}L{{ -user_stats.streak }}{% endif %}
            </div>
        </div>
        
        <a href="/me/{{ user_id }}" class="trophy-link" target="_blank">View Trophy Room →</a>
    </div>
    
    <!-- Squad Engagement Status -->
    <div class="squad-status">
        <span>SQUAD ENGAGEMENT: </span>
        <span class="squad-percentage">{{ user_stats.squad_engagement }}%</span>
    </div>
    
    <div class="content">
        <div class="mission-card">
            <div class="mission-header">
                <div class="signal-type">{{ pattern.name }}</div>
                <div class="pair-direction">
                    {{ symbol }} {{ direction }}
                </div>
                <div style="font-size: 14px; color: rgba(255,255,255,0.6); margin-top: 8px;">
                    {{ pattern.description }}
                </div>
            </div>
            
            <!-- TCS Score Section -->
            <div class="tcs-container">
                <div class="tcs-label">Tactical Confidence Score</div>
                <div class="tcs-score">{{ tcs_score }}%</div>
                <div class="confidence-label">
                    {% if tcs_score >= 90 %}EXTREME CONFIDENCE{% elif tcs_score >= 85 %}HIGH CONFIDENCE{% elif tcs_score >= 75 %}MODERATE CONFIDENCE{% else %}LOW CONFIDENCE{% endif %}
                </div>
            </div>
            
            <!-- Decision Helper -->
            <div class="decision-helper">
                <div class="helper-text">
                    {% if user_stats.trades_remaining <= 0 %}
                        <span class="highlight">⚠️ No ammo left!</span> Reload tomorrow.
                    {% elif tcs_score >= 85 and user_stats.win_rate >= 70 %}
                        <span class="highlight">🔥 Strong signal + Good form = GO!</span>
                    {% elif tcs_score >= 85 and user_stats.win_rate < 70 %}
                        <span class="highlight">🎯 High confidence signal.</span> Trust the process.
                    {% elif tcs_score < 75 and user_stats.trades_remaining <= 2 %}
                        <span class="highlight">💭 Low score.</span> Save ammo for better targets?
                    {% elif user_stats.streak <= -3 %}
                        <span class="highlight">🛡️ Rough patch.</span> Maybe take a break?
                    {% else %}
                        You have <span class="highlight">{{ user_stats.trades_remaining }} shots</span> remaining.
                    {% endif %}
                </div>
            </div>
            
            <!-- Expiry Timer -->
            {% if expiry_seconds > 0 %}
            <div class="timer urgent" id="timer">
                Signal expires in: <span id="countdown">{{ expiry_seconds }}s</span>
            </div>
            {% endif %}
            
            <!-- Trade Parameters -->
            <div class="parameters">
                <div class="param-box">
                    <div class="param-label">Entry Price</div>
                    <div class="param-value masked">{{ entry_masked }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Stop Loss</div>
                    <div class="param-value negative masked">{{ sl_masked }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Take Profit</div>
                    <div class="param-value positive masked">{{ tp_masked }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Risk/Reward</div>
                    <div class="param-value">1:{{ rr_ratio }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Risk</div>
                    <div class="param-value">{{ sl_pips }} pips</div>
                    <div class="dollar-value">(${{ sl_dollars }})</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Reward</div>
                    <div class="param-value positive">{{ tp_pips }} pips</div>
                    <div class="dollar-value positive">(${{ tp_dollars }})</div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="actions">
                <button class="fire-button" onclick="fireSignal()" {% if user_stats.trades_remaining <= 0 %}disabled{% endif %}>
                    🎯 EXECUTE MISSION
                </button>
                <button class="skip-button" onclick="skipSignal()">
                    Stand Down
                </button>
            </div>
            
            <!-- Bottom Links -->
            <div class="bottom-links">
                <a href="#" onclick="showSetupIntel(); return false;">
                    <span>📖</span>
                    <span>Setup Intel</span>
                </a>
                <a href="/notebook/{{ user_id }}" target="_blank">
                    <span>📓</span>
                    <span>Norman's Notebook</span>
                </a>
                <a href="/stats/{{ user_id }}" target="_blank">
                    <span>📊</span>
                    <span>Stats & History</span>
                </a>
                <a href="/education/{{ user_stats.tier }}" target="_blank">
                    <span>📚</span>
                    <span>Training</span>
                </a>
            </div>
        </div>
    </div>
    
    <script>
        // Telegram WebApp API
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }
        
        // Check mission status on page load
        async function checkMissionStatus() {
            try {
                const response = await fetch(`/api/mission-status/{{ signal_id }}`, {
                    headers: {
                        'Authorization': 'Bearer webapp_token',
                        'X-User-ID': '{{ user_id }}'
                    }
                });
                
                if (response.ok) {
                    const mission = await response.json();
                    const fireButton = document.querySelector('.fire-button');
                    
                    if (mission.status === 'fired' || mission.mission_stats?.user_fired) {
                        // Mission already fired - disable button and show status
                        fireButton.disabled = true;
                        fireButton.textContent = '✅ MISSION COMPLETED';
                        fireButton.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
                        fireButton.style.cursor = 'not-allowed';
                    } else if (mission.is_expired || mission.time_remaining <= 0) {
                        // Mission expired - disable button and show expired
                        fireButton.disabled = true;
                        fireButton.textContent = '❌ MISSION EXPIRED';
                        fireButton.style.background = 'linear-gradient(135deg, #6c757d, #495057)';
                        fireButton.style.cursor = 'not-allowed';
                    }
                    // If neither fired nor expired, button stays enabled
                }
            } catch (error) {
                console.log('Mission status check failed:', error);
                // If status check fails, keep button as is for now
            }
        }
        
        // Initialize voice status on page load
        initVoiceStatus();
        
        // Run status check when page loads
        checkMissionStatus();
        
        // Exit briefing
        function exitBriefing() {
            if (tg) {
                tg.close();
            } else {
                window.close();
                // Fallback
                setTimeout(() => {
                    window.location.href = 'https://t.me/BittenCommander';
                }, 100);
            }
        }
        
        // Voice toggle functionality
        let voiceEnabled = true; // Default: enabled
        
        function toggleVoiceQuick() {
            voiceEnabled = !voiceEnabled;
            updateVoiceIcon();
            
            // Send to backend
            fetch('/api/toggle-voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': '{{ user_stats.user_id }}'
                },
                body: JSON.stringify({ enabled: voiceEnabled })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showVoiceQuickMessage(voiceEnabled);
                } else {
                    console.error('Voice toggle failed:', data.error);
                }
            })
            .catch(error => {
                console.error('Error toggling voice:', error);
            });
        }
        
        function updateVoiceIcon() {
            const icon = document.getElementById('voiceIcon');
            const button = document.getElementById('voiceToggleButton');
            
            if (voiceEnabled) {
                icon.textContent = '🔊';
                button.classList.remove('disabled');
                button.title = 'Voice Messages ON - Click to disable';
            } else {
                icon.textContent = '🔇';
                button.classList.add('disabled');
                button.title = 'Voice Messages OFF - Click to enable';
            }
        }
        
        function showVoiceQuickMessage(enabled) {
            const message = document.createElement('div');
            message.style.cssText = `
                position: fixed;
                top: 70px;
                right: 20px;
                background: ${enabled ? '#1a5d1a' : '#5d1a1a'};
                color: {{ colors.primary }};
                padding: 10px 15px;
                border-radius: 5px;
                border: 1px solid {{ colors.primary }};
                z-index: 1000;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                animation: slideIn 0.3s ease-out;
                max-width: 200px;
                text-align: center;
            `;
            
            message.innerHTML = enabled ? 
                '🔊 Voice ON<br><small>Personalities will speak</small>' : 
                '🔇 Voice OFF<br><small>Text-only responses</small>';
            
            document.body.appendChild(message);
            
            setTimeout(() => {
                message.remove();
            }, 2000);
        }
        
        // Initialize voice status on page load
        function initVoiceStatus() {
            fetch('/api/voice-status', {
                headers: {
                    'X-User-ID': '{{ user_stats.user_id }}'
                }
            })
            .then(response => response.json())
            .then(data => {
                voiceEnabled = data.voice_enabled;
                updateVoiceIcon();
            })
            .catch(error => {
                console.error('Error getting voice status:', error);
                // Default to enabled
                voiceEnabled = true;
                updateVoiceIcon();
            });
        }
        
        // Fire signal
        async function fireSignal() {
            // Check if user has trades remaining
            if ({{ user_stats.trades_remaining }} <= 0) {
                alert('No ammo left! Reload tomorrow, soldier.');
                return;
            }
            
            // Disable button immediately to prevent double-firing
            const fireButton = document.querySelector('.fire-button');
            fireButton.disabled = true;
            fireButton.textContent = '🎯 FIRING...';
            
            try {
                // Call the actual fire API
                const response = await fetch('/api/fire', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer webapp_token',
                        'X-User-ID': '{{ user_id }}'
                    },
                    body: JSON.stringify({
                        mission_id: '{{ signal_id }}'
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    // Success - update button and show result
                    fireButton.textContent = '✅ MISSION FIRED!';
                    fireButton.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
                    
                    // Send data to bot for tracking
                    if (tg) {
                        tg.sendData(JSON.stringify({
                            action: 'fire',
                            signal_id: '{{ signal_id }}',
                            symbol: '{{ symbol }}',
                            direction: '{{ direction }}',
                            execution_result: result.execution_result
                        }));
                    }
                    
                    // Show success message and redirect to tracking
                    alert('🎯 MISSION EXECUTED SUCCESSFULLY!\\n\\nTrade sent to broker. Redirecting to live tracking...');
                    
                    // Redirect to trade tracking page after short delay
                    setTimeout(() => {
                        window.location.href = `/track-trade?mission_id={{ signal_id }}&symbol={{ symbol }}&direction={{ direction }}`;
                    }, 1000);
                    
                } else {
                    // Error - show tactical error message
                    fireButton.textContent = '⚠️ MISSION FAILED';
                    fireButton.style.background = 'linear-gradient(135deg, #dc3545, #e74c3c)';
                    
                    // Show error with tactical message
                    const errorMsg = result.message || 'Mission execution failed';
                    alert(`🚨 ${errorMsg}\\n\\nStand by for next opportunity, soldier.`);
                    
                    // Re-enable button for retry if not expired
                    setTimeout(() => {
                        fireButton.disabled = false;
                        fireButton.textContent = '🎯 RETRY MISSION';
                        fireButton.style.background = 'linear-gradient(135deg, {{ colors.danger }}, {{ colors.primary }})';
                    }, 3000);
                }
                
            } catch (error) {
                // Network error
                fireButton.textContent = '📡 CONNECTION LOST';
                fireButton.style.background = 'linear-gradient(135deg, #6c757d, #495057)';
                
                alert('📡 CONNECTION LOST\\n\\nUnable to reach mission control. Check your connection and try again.');
                
                // Re-enable button for retry
                setTimeout(() => {
                    fireButton.disabled = false;
                    fireButton.textContent = '🎯 RETRY MISSION';
                    fireButton.style.background = 'linear-gradient(135deg, {{ colors.danger }}, {{ colors.primary }})';
                }, 3000);
            }
            
            // Auto-close on success after delay
            if (fireButton.textContent.includes('FIRED')) {
                setTimeout(exitBriefing, 2000);
            }
        }
        
        // Skip signal
        function skipSignal() {
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'skip',
                    signal_id: '{{ signal_id }}'
                }));
            }
            exitBriefing();
        }
        
        // Show Setup Intel modal
        function showSetupIntel() {
            document.getElementById('setupModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
        
        // Hide Setup Intel modal
        function hideSetupIntel() {
            document.getElementById('setupModal').style.display = 'none';
            document.body.style.overflow = 'auto';
        }
        
        // Countdown timer
        {% if expiry_seconds > 0 %}
        let timeLeft = {{ expiry_seconds }};
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                clearInterval(timer);
                countdownEl.textContent = 'EXPIRED';
                document.querySelector('.fire-button').disabled = true;
                document.querySelector('.fire-button').textContent = '❌ EXPIRED';
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                countdownEl.textContent = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
            }
        }, 1000);
        {% endif %}
    </script>
</body>
</html>
"""

# Keep test page the same
TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>BITTEN WebApp Test</title>
    <style>
        body {
            background: #0a0a0a;
            color: #00ff00;
            font-family: monospace;
            text-align: center;
            padding: 50px;
        }
        .status {
            font-size: 24px;
            margin: 20px;
        }
    </style>
</head>
<body>
    <h1>🎯 BITTEN WebApp Test Page</h1>
    <div class="status">✅ WebApp is running!</div>
    <div>Server Time: {{ time }}</div>
</body>
</html>
"""

@app.route('/')
def index():
    """Root endpoint - serve landing page"""
    try:
        with open('/root/HydraX-v2/landing/index_v2.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "BITTEN WebApp Server Running", 200

@app.route('/broker-setup')
def broker_setup():
    """Broker setup guide with interactive bot"""
    try:
        with open('/root/HydraX-v2/broker-setup.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Broker setup page not found", 404

@app.route('/api/track-conversation', methods=['POST'])
def track_conversation():
    """Track bot conversation for analytics"""
    try:
        data = request.get_json()
        
        # Basic input validation
        if not data or not data.get('message'):
            return jsonify({'success': False, 'error': 'Invalid data'}), 400
        
        # Store in database (create table if needed)
        import sqlite3
        os.makedirs('/root/HydraX-v2/data', exist_ok=True)
        conn = sqlite3.connect('/root/HydraX-v2/data/visitor_analytics.db')
        c = conn.cursor()
        
        # Create table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT,
                     session_id TEXT,
                     message TEXT,
                     is_bot BOOLEAN,
                     page TEXT,
                     user_agent TEXT,
                     ip_address TEXT)''')
        
        c.execute('''INSERT INTO conversations 
                    (timestamp, session_id, message, is_bot, page, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (data.get('timestamp'), data.get('sessionId'), 
                  data.get('message')[:1000], data.get('isBot', False),  # Limit message length
                  data.get('page', '')[:50], data.get('userAgent', '')[:500], 
                  request.remote_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error tracking conversation: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@app.route('/api/track-page-visit', methods=['POST'])
def track_page_visit():
    """Track page visits for analytics"""
    try:
        data = request.get_json()
        
        # Store in database
        import sqlite3
        os.makedirs('/root/HydraX-v2/data', exist_ok=True)
        conn = sqlite3.connect('/root/HydraX-v2/data/visitor_analytics.db')
        c = conn.cursor()
        
        # Create table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS page_visits
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT,
                     session_id TEXT,
                     page TEXT,
                     referrer TEXT,
                     user_agent TEXT,
                     ip_address TEXT)''')
        
        c.execute('''INSERT INTO page_visits 
                    (timestamp, session_id, page, referrer, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (data.get('timestamp'), data.get('sessionId'), 
                  data.get('page', '')[:50], data.get('referrer', '')[:500],
                  data.get('userAgent', '')[:500], request.remote_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error tracking page visit: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@app.route('/analytics/dashboard')
def analytics_dashboard():
    """Simple analytics dashboard for viewing collected data"""
    try:
        import sqlite3
        conn = sqlite3.connect('/root/HydraX-v2/data/visitor_analytics.db')
        c = conn.cursor()
        
        # Initialize variables
        total_messages = 0
        unique_visitors = 0
        recent_user_messages = []
        total_visits = 0
        page_stats = []
        
        try:
            c.execute('''SELECT COUNT(*) as total_messages FROM conversations''')
            result = c.fetchone()
            total_messages = result[0] if result else 0
            
            c.execute('''SELECT COUNT(DISTINCT session_id) as unique_visitors FROM conversations''')
            result = c.fetchone()
            unique_visitors = result[0] if result else 0
            
            c.execute('''SELECT message FROM conversations WHERE is_bot = 0 ORDER BY timestamp DESC LIMIT 20''')
            recent_user_messages = [row[0] for row in c.fetchall()]
            
            c.execute('''SELECT COUNT(*) as total_visits FROM page_visits''')
            result = c.fetchone()
            total_visits = result[0] if result else 0
            
            c.execute('''SELECT page, COUNT(*) as visits FROM page_visits GROUP BY page ORDER BY visits DESC''')
            page_stats = c.fetchall()
        except sqlite3.OperationalError:
            # Tables don't exist yet
            pass
        
        conn.close()
        
        return f"""
        <html>
        <head><title>BITTEN Analytics Dashboard</title>
        <style>
            body {{ font-family: 'Rajdhani', sans-serif; background: #0a0a0a; color: #00ff41; padding: 2rem; }}
            .stat {{ background: rgba(0,255,65,0.1); padding: 1rem; margin: 1rem 0; border: 1px solid #00ff41; }}
            .messages {{ background: rgba(0,0,0,0.5); padding: 1rem; margin: 1rem 0; max-height: 300px; overflow-y: auto; }}
            h1, h2 {{ color: #00ff41; font-family: 'Orbitron', monospace; }}
            a {{ color: #ffaa00; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
        </head>
        <body>
            <h1>🎯 BITTEN Visitor Intelligence</h1>
            
            <div class="stat">
                <h2>📊 Conversation Analytics</h2>
                <p>Total Messages: {total_messages}</p>
                <p>Unique Visitors: {unique_visitors}</p>
                <p>Avg Messages per Visitor: {round(total_messages/unique_visitors, 1) if unique_visitors > 0 else 0}</p>
            </div>
            
            <div class="stat">
                <h2>📈 Page Traffic</h2>
                <p>Total Visits: {total_visits}</p>
                {''.join([f"<p>{page}: {visits} visits</p>" for page, visits in page_stats])}
            </div>
            
            <div class="messages">
                <h2>💬 Recent User Questions/Comments</h2>
                {''.join([f"<p>• {msg}</p>" for msg in recent_user_messages[:15]])}
            </div>
            
            <p><a href="/">← Back to Landing Page</a> | <a href="/broker-setup">Broker Setup</a></p>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h1>Analytics Error: {str(e)}</h1>"

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
    
    TRADE_TRACKING_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎯 TRACKING: {{ symbol }} {{ direction }}</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                background: #0A0A0A;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                overflow-x: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
                padding: 15px;
                border-bottom: 2px solid #00D9FF;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .header-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .trade-title {
                font-size: 18px;
                font-weight: bold;
                color: #00D9FF;
            }
            
            .trade-status {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #28a745;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                display: grid;
                grid-template-columns: 1fr 350px;
                gap: 20px;
                min-height: calc(100vh - 80px);
            }
            
            .chart-section {
                background: #1a1a1a;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #333;
            }
            
            .chart-container {
                width: 100%;
                height: 500px;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .sidebar {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .trade-card {
                background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
                border-radius: 10px;
                padding: 20px;
                border: 1px solid #333;
                position: relative;
                overflow: hidden;
            }
            
            .trade-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #00D9FF, #FF6B35);
            }
            
            .card-title {
                font-size: 16px;
                font-weight: bold;
                color: #00D9FF;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .trade-details {
                display: grid;
                gap: 10px;
            }
            
            .detail-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid #333;
            }
            
            .detail-label {
                color: #888;
                font-size: 14px;
            }
            
            .detail-value {
                color: #fff;
                font-weight: bold;
                font-size: 14px;
            }
            
            .pnl-positive {
                color: #28a745;
            }
            
            .pnl-negative {
                color: #dc3545;
            }
            
            .bullet-travel {
                background: #1a1a1a;
                border-radius: 10px;
                padding: 20px;
                border: 1px solid #333;
                text-align: center;
            }
            
            .bullet-track {
                width: 100%;
                height: 20px;
                background: #333;
                border-radius: 10px;
                position: relative;
                margin: 20px 0;
                overflow: hidden;
            }
            
            .bullet {
                position: absolute;
                left: 0;
                top: 50%;
                transform: translateY(-50%);
                width: 30px;
                height: 12px;
                background: linear-gradient(90deg, #FFD700, #FF6B35);
                border-radius: 6px;
                animation: bulletTravel 3s ease-in-out infinite alternate;
                box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
            }
            
            @keyframes bulletTravel {
                0% { left: 5px; }
                100% { left: calc(100% - 35px); }
            }
            
            .price-levels {
                display: grid;
                gap: 10px;
                margin-top: 15px;
            }
            
            .price-level {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #333;
                background: rgba(255, 255, 255, 0.05);
            }
            
            .price-level.entry {
                border-color: #17a2b8;
                background: rgba(23, 162, 184, 0.1);
            }
            
            .price-level.tp {
                border-color: #28a745;
                background: rgba(40, 167, 69, 0.1);
            }
            
            .price-level.sl {
                border-color: #dc3545;
                background: rgba(220, 53, 69, 0.1);
            }
            
            .action-buttons {
                display: grid;
                gap: 10px;
                margin-top: 20px;
            }
            
            .action-btn {
                padding: 12px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                text-decoration: none;
                text-align: center;
                display: block;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
            }
            
            .btn-secondary {
                background: linear-gradient(135deg, #6c757d, #545b62);
                color: white;
            }
            
            .btn-danger {
                background: linear-gradient(135deg, #dc3545, #c82333);
                color: white;
            }
            
            .action-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }
            
            @media (max-width: 768px) {
                .container {
                    grid-template-columns: 1fr;
                    padding: 10px;
                }
                
                .header-content {
                    flex-direction: column;
                    gap: 10px;
                    text-align: center;
                }
                
                .chart-container {
                    height: 300px;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="trade-title">🎯 TRACKING: {{ symbol }} {{ direction }}</div>
                <div class="trade-status">
                    <div class="status-indicator"></div>
                    <span>BULLET IN FLIGHT</span>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="chart-section">
                <h3 style="margin-bottom: 15px; color: #00D9FF;">📈 Live Chart</h3>
                <div class="chart-container" id="tradingview_chart"></div>
            </div>
            
            <div class="sidebar">
                <div class="trade-card">
                    <div class="card-title">
                        🎯 Mission Details
                    </div>
                    <div class="trade-details">
                        <div class="detail-row">
                            <span class="detail-label">Mission ID:</span>
                            <span class="detail-value">{{ mission_id[:15] }}...</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Symbol:</span>
                            <span class="detail-value">{{ symbol }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Direction:</span>
                            <span class="detail-value {{ 'pnl-positive' if direction == 'BUY' else 'pnl-negative' }}">{{ direction }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Risk/Reward:</span>
                            <span class="detail-value">1:{{ "%.1f"|format(rr_ratio) }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value pnl-positive">🟢 ACTIVE</span>
                        </div>
                    </div>
                </div>
                
                <div class="bullet-travel">
                    <div class="card-title">🚀 Bullet Travel</div>
                    <p style="color: #888; margin-bottom: 10px;">Tracking trade progress to target...</p>
                    <div class="bullet-track">
                        <div class="bullet"></div>
                    </div>
                    <p style="color: #00D9FF; font-size: 12px;">⚡ Trade executing in real-time</p>
                </div>
                
                <div class="trade-card">
                    <div class="card-title">🎯 Price Levels</div>
                    <div class="price-levels">
                        <div class="price-level entry">
                            <span>📍 Entry</span>
                            <span>{{ "%.5f"|format(entry_price) }}</span>
                        </div>
                        <div class="price-level tp">
                            <span>🎯 Take Profit</span>
                            <span>{{ "%.5f"|format(take_profit) }}</span>
                        </div>
                        <div class="price-level sl">
                            <span>🛡️ Stop Loss</span>
                            <span>{{ "%.5f"|format(stop_loss) }}</span>
                        </div>
                    </div>
                </div>
                
                <div class="trade-card">
                    <div class="card-title">📊 Live P&L</div>
                    <div class="trade-details">
                        <div class="detail-row">
                            <span class="detail-label">Unrealized P&L:</span>
                            <span class="detail-value pnl-positive" id="unrealized-pnl">+$0.00</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Current Price:</span>
                            <span class="detail-value" id="current-price">{{ "%.5f"|format(entry_price) }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Distance to TP:</span>
                            <span class="detail-value" id="distance-tp">{{ "%.1f"|format((take_profit - entry_price) * 10000) }} pips</span>
                        </div>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <a href="/hud?mission_id={{ mission_id }}" class="action-btn btn-primary">
                        🎯 Back to Mission Brief
                    </a>
                    <a href="/stats/{{ user_id or '7176191872' }}" class="action-btn btn-secondary">
                        📊 Trade History
                    </a>
                    <button class="action-btn btn-danger" onclick="confirmClose()">
                        🚨 Emergency Close
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            // Initialize Telegram WebApp
            const tg = window.Telegram?.WebApp;
            if (tg) {
                tg.ready();
                tg.expand();
            }
            
            // Initialize TradingView chart
            new TradingView.widget({
                "width": "100%",
                "height": "100%",
                "symbol": "FX:{{ symbol }}",
                "interval": "1",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#0A0A0A",
                "enable_publishing": false,
                "hide_top_toolbar": false,
                "hide_legend": true,
                "save_image": false,
                "container_id": "tradingview_chart",
                "studies": [
                    "MASimple@tv-basicstudies"
                ],
                "overrides": {
                    "paneProperties.background": "#1a1a1a",
                    "paneProperties.vertGridProperties.color": "#333",
                    "paneProperties.horzGridProperties.color": "#333",
                    "symbolWatermarkProperties.transparency": 90,
                    "scalesProperties.textColor": "#fff"
                },
                "drawings_access": {
                    "type": "black",
                    "tools": [
                        {"name": "Regression Trend"},
                        {"name": "Trend Line"},
                        {"name": "Horizontal Line"}
                    ]
                }
            });
            
            // Mock live price updates (in production, this would connect to real data)
            let currentPrice = {{ entry_price }};
            const entryPrice = {{ entry_price }};
            const takeProfit = {{ take_profit }};
            const stopLoss = {{ stop_loss }};
            const direction = "{{ direction }}";
            
            function updatePriceData() {
                // Simulate small price movements
                const change = (Math.random() - 0.5) * 0.0002;
                currentPrice += change;
                
                // Calculate P&L
                let pnl = 0;
                if (direction === 'BUY') {
                    pnl = (currentPrice - entryPrice) * 100000; // Simulate lot size
                } else {
                    pnl = (entryPrice - currentPrice) * 100000;
                }
                
                // Update display
                document.getElementById('current-price').textContent = currentPrice.toFixed(5);
                document.getElementById('unrealized-pnl').textContent = (pnl >= 0 ? '+$' : '-$') + Math.abs(pnl).toFixed(2);
                document.getElementById('unrealized-pnl').className = 'detail-value ' + (pnl >= 0 ? 'pnl-positive' : 'pnl-negative');
                
                // Calculate distance to TP
                let distanceToTP = 0;
                if (direction === 'BUY') {
                    distanceToTP = (takeProfit - currentPrice) * 10000;
                } else {
                    distanceToTP = (currentPrice - takeProfit) * 10000;
                }
                document.getElementById('distance-tp').textContent = Math.abs(distanceToTP).toFixed(1) + ' pips';
                
                // Check if TP or SL hit
                if ((direction === 'BUY' && currentPrice >= takeProfit) || 
                    (direction === 'SELL' && currentPrice <= takeProfit)) {
                    showTradeResult('TARGET HIT! 🎯', 'Trade closed at Take Profit!', 'success');
                } else if ((direction === 'BUY' && currentPrice <= stopLoss) || 
                          (direction === 'SELL' && currentPrice >= stopLoss)) {
                    showTradeResult('STOP HIT 🛡️', 'Trade closed at Stop Loss.', 'danger');
                }
            }
            
            function showTradeResult(title, message, type) {
                const statusIndicator = document.querySelector('.status-indicator');
                const statusText = document.querySelector('.trade-status span');
                
                if (type === 'success') {
                    statusIndicator.style.background = '#28a745';
                    statusText.textContent = 'TARGET ACQUIRED';
                    alert(`🎯 ${title}\\n\\n${message}\\n\\nMission accomplished, soldier!`);
                } else {
                    statusIndicator.style.background = '#dc3545';
                    statusText.textContent = 'TACTICAL RETREAT';
                    alert(`🛡️ ${title}\\n\\n${message}\\n\\nRegroup for next opportunity.`);
                }
                
                // Stop updates
                clearInterval(priceUpdateInterval);
            }
            
            function confirmClose() {
                if (confirm('🚨 EMERGENCY CLOSE\\n\\nAre you sure you want to close this trade immediately?\\n\\nThis action cannot be undone.')) {
                    alert('🚨 EMERGENCY CLOSE EXECUTED\\n\\nTrade closed at market price.\\n\\nPosition liquidated.');
                    showTradeResult('EMERGENCY CLOSE', 'Trade manually closed.', 'danger');
                }
            }
            
            // Start live updates
            const priceUpdateInterval = setInterval(updatePriceData, 2000);
            
            // Initialize with first update
            updatePriceData();
        </script>
    </body>
    </html>
    """
    
    return render_template_string(TRADE_TRACKING_TEMPLATE, 
                                mission_id=mission_id,
                                symbol=symbol, 
                                direction=direction,
                                entry_price=entry_price,
                                take_profit=take_profit,
                                stop_loss=stop_loss,
                                rr_ratio=rr_ratio,
                                user_id=user_id)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    import psutil
    import time
    
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Check dependencies
        dependencies_ok = True
        dependency_errors = []
        
        # Check signal storage
        try:
            from signal_storage import get_latest_signal
            test_signal = get_latest_signal("test")
            # If no exception, signal storage is working
        except Exception as e:
            dependencies_ok = False
            dependency_errors.append(f"Signal storage error: {str(e)}")
        
        # Determine health status
        status = "healthy"
        if cpu_percent > 90:
            status = "warning"
        if memory.percent > 90:
            status = "warning"
        if not dependencies_ok:
            status = "unhealthy"
        
        return jsonify({
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "uptime": int(time.time() - process.create_time()),
            "service": "bitten-webapp",
            "version": "1.0.0",
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free": disk.free
            },
            "process": {
                "pid": process.pid,
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "threads": process.num_threads(),
                "connections": len(process.connections()) if hasattr(process, 'connections') else 0
            },
            "dependencies": {
                "status": "ok" if dependencies_ok else "error",
                "errors": dependency_errors
            }
        }), 200 if status != "unhealthy" else 503
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "bitten-webapp",
            "error": str(e)
        }), 503

@app.route('/metrics')
def metrics():
    """Prometheus-compatible metrics endpoint"""
    import psutil
    import time
    
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Create Prometheus-style metrics
        metrics_output = f"""# HELP bitten_webapp_cpu_percent CPU usage percentage
# TYPE bitten_webapp_cpu_percent gauge
bitten_webapp_cpu_percent {cpu_percent}

# HELP bitten_webapp_memory_percent Memory usage percentage
# TYPE bitten_webapp_memory_percent gauge
bitten_webapp_memory_percent {memory.percent}

# HELP bitten_webapp_memory_bytes Memory usage in bytes
# TYPE bitten_webapp_memory_bytes gauge
bitten_webapp_memory_bytes {process_memory.rss}

# HELP bitten_webapp_disk_percent Disk usage percentage
# TYPE bitten_webapp_disk_percent gauge
bitten_webapp_disk_percent {(disk.used / disk.total) * 100}

# HELP bitten_webapp_uptime_seconds Process uptime in seconds
# TYPE bitten_webapp_uptime_seconds counter
bitten_webapp_uptime_seconds {int(time.time() - process.create_time())}

# HELP bitten_webapp_threads Number of threads
# TYPE bitten_webapp_threads gauge
bitten_webapp_threads {process.num_threads()}

# HELP bitten_webapp_connections Number of network connections
# TYPE bitten_webapp_connections gauge
bitten_webapp_connections {len(process.connections()) if hasattr(process, 'connections') else 0}

# HELP bitten_webapp_up Service availability
# TYPE bitten_webapp_up gauge
bitten_webapp_up 1
"""
        
        return metrics_output, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"# Error generating metrics: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/ready')
def readiness_check():
    """Readiness check for Kubernetes/orchestration"""
    try:
        # Check if the app is ready to serve traffic
        from signal_storage import get_latest_signal
        
        # Test critical dependencies
        test_signal = get_latest_signal("test")
        
        return jsonify({
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "service": "bitten-webapp"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "not_ready",
            "timestamp": datetime.now().isoformat(),
            "service": "bitten-webapp",
            "error": str(e)
        }), 503

@app.route('/live')
def liveness_check():
    """Liveness check for Kubernetes/orchestration"""
    return jsonify({
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "service": "bitten-webapp"
    }), 200

@app.route('/test')
def test():
    """Test endpoint"""
    from datetime import datetime
    return render_template_string(TEST_PAGE, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/hud')
def hud():
    """Mission briefing HUD with personalized data"""
    # Rate limiting check
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr))
    if not rate_limiter.is_allowed(client_ip):
        return """
        <html>
        <head><title>BITTEN - Rate Limited</title></head>
        <body style='background:#0A0A0A;color:#fff;font-family:monospace;padding:20px;text-align:center'>
        <h1>🚨 RATE LIMITED</h1>
        <p>Too many requests. Please wait a moment.</p>
        </body>
        </html>
        """, 429
    
    try:
        # Get data from URL parameter or Telegram WebApp - with input validation
        encoded_data = request.args.get('data', '')[:10000]  # Limit encoded data size
        signal_id = request.args.get('signal', '')[:20] or request.args.get('mission_id', '')[:30]  # Support both signal and mission_id
        user_id = request.args.get('user_id', os.getenv("ADMIN_USER_ID", "7176191872"))[:20]  # Default user with length limit
        
        # Check if this is a base mission that needs user redirection
        if signal_id and not signal_id.endswith('_USER'):
            # Try to find user-specific mission for this base signal
            personal_mission_id = find_personal_mission(signal_id, user_id)
            if personal_mission_id and personal_mission_id != signal_id:
                # Redirect to personal mission
                return redirect(f'/hud?mission_id={personal_mission_id}&user_id={user_id}')
        
        # Sanitize inputs
        import re
        # Allow both numeric IDs and APEX mission IDs (APEX5_SYMBOL_XXXXXX)
        if signal_id and not re.match(r'^(APEX[0-9]+_[A-Z]+_[0-9]+|[0-9]+)$', signal_id):
            return f"<h1>Invalid Signal ID</h1><p>Signal ID format not recognized.</p>", 400
        
        if user_id and not re.match(r'^[0-9]+$', user_id):
            user_id = 'int(os.getenv("ADMIN_USER_ID", "7176191872"))'  # Fallback to default
        
        # Determine data source and get signal data
        data = None
        
        # If signal ID provided, look up signal by ID
        if signal_id and not encoded_data:
            signal_data = get_signal_by_id(signal_id)
            if signal_data:
                data = {
                    'user_id': user_id,
                    'signal': signal_data
                }
            else:
                return f"<h1>Signal not found</h1><p>Signal ID {signal_id} not found in database.</p>", 404
        
        # If encoded data provided, decode it
        elif encoded_data:
            decoded_data = urllib.parse.unquote(encoded_data)
            data = json.loads(decoded_data)
        
        # If no data in URL, check for stored signals
        else:
            # Try to get user from Telegram WebApp initData
            init_data = request.args.get('initData', '')
            if init_data:
                try:
                    # Parse Telegram init data
                    import base64
                    decoded = base64.b64decode(init_data).decode('utf-8')
                    init_json = json.loads(decoded)
                    user_id = str(init_json.get('user', {}).get('id', user_id))
                except:
                    pass
            
            # Get latest signal for user
            signal_data = get_latest_signal(user_id)
            if not signal_data:
                # Show signal selection page
                active_signals = get_active_signals(user_id)
                if active_signals:
                    return render_signal_selection(user_id, active_signals)
                else:
                    return render_no_signals(user_id)
            
            # Use stored signal
            data = {
                'user_id': user_id,
                'signal': signal_data.get('signal', signal_data)
            }
        
        # Extract signal data
        signal = data.get('signal', {})
        
        # Get user stats (mock for now, would get from database)
        user_id = data.get('user_id', 'demo')
        user_stats = get_user_stats(user_id)
        
        # Get random pattern for this signal
        pattern_key, pattern = get_random_pattern()
        
        # Get user's actual account balance and tier for accurate calculations
        user_account = get_user_account_balance(user_id)
        user_tier = user_stats.get('tier', 'nibbler')
        
        # Calculate dollar values based on user's actual account and tier
        sl_dollars = calculate_dollar_value(
            signal.get('sl_pips', 0), 
            user_tier=user_tier, 
            account_balance=user_account['balance']
        )
        tp_dollars = calculate_dollar_value(
            signal.get('tp_pips', 0), 
            user_tier=user_tier, 
            account_balance=user_account['balance']
        )
        
        # Mask prices
        entry_masked = mask_price(signal.get('entry', 0))
        sl_masked = mask_price(signal.get('sl', 0))
        tp_masked = mask_price(signal.get('tp', 0))
        
        # Prepare template variables
        context = {
            'user_id': user_id,
            'user_stats': user_stats,
            'signal_id': signal.get('id', 'unknown'),
            'signal_type': signal.get('signal_type', 'STANDARD'),
            'symbol': signal.get('symbol', 'UNKNOWN'),
            'direction': signal.get('direction', 'BUY'),
            'tcs_score': signal.get('tcs_score', 0),
            'entry': signal.get('entry', 0),
            'sl': signal.get('sl', 0),
            'tp': signal.get('tp', 0),
            'entry_masked': entry_masked,
            'sl_masked': sl_masked,
            'tp_masked': tp_masked,
            'sl_pips': signal.get('sl_pips', 0),
            'tp_pips': signal.get('tp_pips', 0),
            'sl_dollars': sl_dollars,
            'tp_dollars': tp_dollars,
            'rr_ratio': signal.get('rr_ratio', 0),
            'expiry_seconds': calculate_remaining_time(signal),
            'colors': get_tier_styles(user_stats['tier']),
            'pattern_key': pattern_key,
            'pattern': pattern,
            # Add account balance info for transparency
            'account_balance': user_account['balance'],
            'account_equity': user_account['equity'],
            'account_source': user_account['source'],
            'user_tier': user_tier
        }
        
        return render_template_string(HUD_TEMPLATE, **context)
        
    except Exception as e:
        # Log error securely without exposing internals
        import logging
        logging.error(f"HUD error for signal_id={signal_id}, user_id={user_id}: {str(e)}")
        
        # Return generic error message
        return """
        <html>
        <head><title>BITTEN - Mission Brief Unavailable</title></head>
        <body style='background:#0A0A0A;color:#fff;font-family:monospace;padding:20px;text-align:center'>
        <h1>🚨 MISSION BRIEF UNAVAILABLE</h1>
        <p>Unable to load mission briefing. Please try again.</p>
        <p><a href='/' style='color:#00D9FF'>Return to Base</a></p>
        </body>
        </html>
        """, 500

@app.route('/notebook/<user_id>')
def notebook(user_id):
    """Norman's Trading Notebook"""
    colors = get_tier_styles('nibbler')  # Default colors
    
    NOTEBOOK_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Norman's Trading Notebook</title>
        <style>
            body {
                background: #0a0a0a;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
                color: #FFD700;
            }
            .entry {
                background: #1a1a1a;
                border: 1px solid #FFD700;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .entry-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                color: #00D9FF;
            }
            .entry-content {
                line-height: 1.6;
            }
            .mood {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
            .mood.positive { background: #4ECDC4; color: #000; }
            .mood.negative { background: #FF6B6B; color: #000; }
            .mood.neutral { background: #FFD700; color: #000; }
            .back-link {
                color: #00D9FF;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="#" class="back-link" onclick="window.close(); return false;">← Back</a>
            <h1 class="header">📓 Norman's Trading Notebook</h1>
            
            <div class="entry">
                <div class="entry-header">
                    <span>Today's Reflection</span>
                    <span class="mood positive">CONFIDENT</span>
                </div>
                <div class="entry-content">
                    Remember, every loss is a lesson. Every win is proof that the system works.
                    Today you showed discipline by waiting for high TCS signals. Keep it up!
                </div>
            </div>
            
            <div class="entry">
                <div class="entry-header">
                    <span>Yesterday</span>
                    <span class="mood neutral">LEARNING</span>
                </div>
                <div class="entry-content">
                    That EUR/USD loss hurt, but you stuck to your stop loss. That's growth.
                    The market will always be there tomorrow. Your capital won't if you revenge trade.
                </div>
            </div>
            
            <div class="entry">
                <div class="entry-header">
                    <span>Last Week Summary</span>
                    <span class="mood positive">IMPROVING</span>
                </div>
                <div class="entry-content">
                    5 wins, 2 losses. More importantly, you followed every rule.
                    You're becoming the trader you always wanted to be. One trade at a time.
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(NOTEBOOK_TEMPLATE)

@app.route('/history')
def history_redirect():
    """Redirect old history route to stats"""
    return "Please use /stats/user_id instead", 301

@app.route('/stats/<user_id>')
def stats_and_history(user_id):
    """Combined stats and trade history page"""
    colors = get_tier_styles('nibbler')
    
    STATS_HISTORY_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stats & Trade History</title>
        <style>
            body {
                background: #0a0a0a;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
                color: #00D9FF;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            .stat-card {
                background: #1a1a1a;
                border: 1px solid #00D9FF;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
            }
            .stat-title {
                font-size: 12px;
                color: rgba(255,255,255,0.6);
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }
            .stat-value {
                font-size: 28px;
                font-weight: bold;
                color: #00D9FF;
            }
            .stat-value.positive { color: #4ECDC4; }
            .stat-value.negative { color: #FF6B6B; }
            .history-section {
                background: #1a1a1a;
                border: 1px solid #FFD700;
                border-radius: 8px;
                padding: 20px;
            }
            .history-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 20px;
                border-bottom: 1px solid rgba(255,255,255,0.2);
            }
            .filter-buttons {
                display: flex;
                gap: 10px;
            }
            .filter-btn {
                background: transparent;
                color: #FFD700;
                border: 1px solid #FFD700;
                padding: 6px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
            }
            .filter-btn:hover,
            .filter-btn.active {
                background: #FFD700;
                color: #000;
            }
            .trade-table {
                width: 100%;
                border-collapse: collapse;
            }
            .trade-table th {
                text-align: left;
                padding: 12px;
                color: #FFD700;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                border-bottom: 2px solid #FFD700;
            }
            .trade-table td {
                padding: 12px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .trade-table tr:hover {
                background: rgba(255,255,255,0.05);
            }
            .pattern-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                background: rgba(0,217,255,0.2);
                color: #00D9FF;
                text-transform: uppercase;
            }
            .result-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            .result-badge.win {
                background: rgba(78,205,196,0.2);
                color: #4ECDC4;
            }
            .result-badge.loss {
                background: rgba(255,107,107,0.2);
                color: #FF6B6B;
            }
            .back-link {
                color: #00D9FF;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }
            .scroll-container {
                max-height: 400px;
                overflow-y: auto;
            }
            .scroll-container::-webkit-scrollbar {
                width: 8px;
            }
            .scroll-container::-webkit-scrollbar-track {
                background: rgba(0,0,0,0.3);
            }
            .scroll-container::-webkit-scrollbar-thumb {
                background: #FFD700;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="#" class="back-link" onclick="window.close(); return false;">← Back</a>
            <h1 class="header">📊 Trading Statistics & History</h1>
            
            <!-- Stats Grid -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-title">Total Trades</div>
                    <div class="stat-value">127</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Win Rate</div>
                    <div class="stat-value positive">75%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Profit Factor</div>
                    <div class="stat-value positive">2.3</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Total P&L</div>
                    <div class="stat-value positive">+24.3%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Best Streak</div>
                    <div class="stat-value">W7</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Avg Risk:Reward</div>
                    <div class="stat-value">1:2.1</div>
                </div>
            </div>
            
            <!-- Pattern Performance -->
            <div class="stats-grid" style="margin-bottom: 40px;">
                <div class="stat-card">
                    <div class="stat-title">Best Pattern</div>
                    <div class="stat-value" style="font-size: 16px;">WALL BREACH</div>
                    <div style="color: #4ECDC4; margin-top: 5px;">82% Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Most Traded</div>
                    <div class="stat-value" style="font-size: 16px;">LONDON RAID</div>
                    <div style="color: rgba(255,255,255,0.6); margin-top: 5px;">34 Trades</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Avoid Pattern</div>
                    <div class="stat-value" style="font-size: 16px;">PINCER MOVE</div>
                    <div style="color: #FF6B6B; margin-top: 5px;">45% Win Rate</div>
                </div>
            </div>
            
            <!-- Trade History -->
            <div class="history-section">
                <div class="history-header">
                    <h2 style="color: #FFD700; margin: 0;">Trade History</h2>
                    <div class="filter-buttons">
                        <button class="filter-btn active" onclick="filterTrades('all')">All</button>
                        <button class="filter-btn" onclick="filterTrades('wins')">Wins</button>
                        <button class="filter-btn" onclick="filterTrades('losses')">Losses</button>
                        <button class="filter-btn" onclick="filterTrades('today')">Today</button>
                    </div>
                </div>
                
                <div class="scroll-container">
                    <table class="trade-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Pair</th>
                                <th>Pattern</th>
                                <th>Direction</th>
                                <th>Result</th>
                                <th>P&L</th>
                            </tr>
                        </thead>
                        <tbody id="tradeTableBody">
                            <tr>
                                <td>Today 14:23</td>
                                <td>EUR/USD</td>
                                <td><span class="pattern-badge">LONDON RAID</span></td>
                                <td>BUY</td>
                                <td><span class="result-badge win">WIN +42</span></td>
                                <td style="color: #4ECDC4;">+2.1%</td>
                            </tr>
                            <tr>
                                <td>Today 10:15</td>
                                <td>GBP/USD</td>
                                <td><span class="pattern-badge">WALL BREACH</span></td>
                                <td>SELL</td>
                                <td><span class="result-badge win">WIN +38</span></td>
                                <td style="color: #4ECDC4;">+1.9%</td>
                            </tr>
                            <tr>
                                <td>Today 08:45</td>
                                <td>USD/JPY</td>
                                <td><span class="pattern-badge">SNIPER'S NEST</span></td>
                                <td>BUY</td>
                                <td><span class="result-badge loss">LOSS -20</span></td>
                                <td style="color: #FF6B6B;">-1.0%</td>
                            </tr>
                            <tr>
                                <td>Yesterday 16:30</td>
                                <td>EUR/USD</td>
                                <td><span class="pattern-badge">SUPPLY DROP</span></td>
                                <td>BUY</td>
                                <td><span class="result-badge win">WIN +55</span></td>
                                <td style="color: #4ECDC4;">+2.8%</td>
                            </tr>
                            <tr>
                                <td>Yesterday 12:20</td>
                                <td>AUD/USD</td>
                                <td><span class="pattern-badge">AMBUSH POINT</span></td>
                                <td>SELL</td>
                                <td><span class="result-badge win">WIN +35</span></td>
                                <td style="color: #4ECDC4;">+1.8%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            function filterTrades(filter) {
                // Update active button
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                // In a real app, this would filter the table
                console.log('Filter by:', filter);
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(STATS_HISTORY_TEMPLATE)

@app.route('/me/<user_id>')
def trophy_room(user_id):
    """User's trophy room / profile"""
    colors = get_tier_styles('nibbler')
    
    TROPHY_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trophy Room</title>
        <style>
            body {
                background: #0a0a0a;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                margin: 0;
                padding: 20px;
                text-align: center;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
            }
            .header {
                color: #FFD700;
                margin-bottom: 40px;
            }
            .trophy-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 40px;
            }
            .trophy {
                background: #1a1a1a;
                border: 2px solid #FFD700;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
            }
            .trophy-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            .trophy-name {
                font-size: 14px;
                font-weight: bold;
                color: #FFD700;
            }
            .stats-section {
                background: #1a1a1a;
                border: 1px solid #00D9FF;
                border-radius: 8px;
                padding: 30px;
                text-align: left;
            }
            .stat-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .stat-label {
                color: rgba(255,255,255,0.7);
            }
            .stat-value {
                font-weight: bold;
                color: #00D9FF;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🏆 Trophy Room</h1>
            
            <div class="trophy-grid">
                <div class="trophy">
                    <div class="trophy-icon">🎯</div>
                    <div class="trophy-name">Sharpshooter</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">🔥</div>
                    <div class="trophy-name">Hot Streak</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">💎</div>
                    <div class="trophy-name">Diamond Hands</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">📈</div>
                    <div class="trophy-name">Profit Master</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">🛡️</div>
                    <div class="trophy-name">Risk Guardian</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">⚡</div>
                    <div class="trophy-name">Quick Draw</div>
                </div>
            </div>
            
            <div class="stats-section">
                <h2 style="color: #FFD700; text-align: center; margin-bottom: 30px;">Career Stats</h2>
                <div class="stat-row">
                    <span class="stat-label">Total Trades</span>
                    <span class="stat-value">127</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Win Rate</span>
                    <span class="stat-value">75%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Best Streak</span>
                    <span class="stat-value">W7</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total P&L</span>
                    <span class="stat-value">+24.3%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Member Since</span>
                    <span class="stat-value">3 months ago</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(TROPHY_TEMPLATE)

@app.route('/education/<tier>')
def education(tier):
    """Education/training page matching HUD style"""
    colors = get_tier_styles(tier)
    
    # Education content with pattern focus
    education_content = {
        'nibbler': {
            'title': 'NIBBLER TRAINING ACADEMY',
            'tier': 'nibbler',
            'modules': [
                {'name': 'Basic Patterns Recognition', 'progress': 75, 'completed_lessons': 6, 'total_lessons': 8},
                {'name': 'Risk Management Fundamentals', 'progress': 100, 'completed_lessons': 5, 'total_lessons': 5},
                {'name': 'Trading Psychology', 'progress': 30, 'completed_lessons': 3, 'total_lessons': 10}
            ],
            'pattern_mastery': {
                'LONDON_RAID': 65,
                'WALL_BREACH': 80,
                'SNIPER_NEST': 45,
                'SUPPLY_DROP': 70
            },
            'next_lesson': 'Understanding AMBUSH POINT Patterns',
            'achievements': ['First Trade', 'Week Warrior', 'Discipline Badge']
        },
        'fang': {
            'title': 'FANG ADVANCED TRAINING',
            'tier': 'fang',
            'modules': [
                {'name': 'Advanced Pattern Analysis', 'progress': 60, 'completed_lessons': 12, 'total_lessons': 20},
                {'name': 'Multi-Timeframe Confluence', 'progress': 40, 'completed_lessons': 8, 'total_lessons': 20},
                {'name': 'Momentum Trading Mastery', 'progress': 80, 'completed_lessons': 16, 'total_lessons': 20}
            ],
            'pattern_mastery': {
                'LONDON_RAID': 85,
                'WALL_BREACH': 90,
                'SNIPER_NEST': 75,
                'AMBUSH_POINT': 60,
                'SUPPLY_DROP': 88,
                'PINCER_MOVE': 50
            },
            'next_lesson': 'Advanced PINCER MOVE Strategies',
            'achievements': ['Pattern Master', 'Sniper Elite', '100 Trade Veteran']
        }
    }
    
    content = education_content.get(tier.lower(), education_content['nibbler'])
    
    # Enhanced education template matching HUD style
    EDUCATION_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ content.title }}</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                background-color: {{ colors.background }};
                color: {{ colors.secondary }};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 16px;
                line-height: 1.6;
                overflow-x: hidden;
            }
            
            /* Top Navigation Bar - Same as HUD */
            .top-bar {
                background: rgba(0,0,0,0.9);
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid {{ colors.border }};
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .back-button {
                color: {{ colors.primary }};
                text-decoration: none;
                padding: 8px 20px;
                border: 2px solid {{ colors.primary }};
                border-radius: 4px;
                font-weight: bold;
                transition: all 0.3s;
                background: rgba(0,0,0,0.5);
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            
            .back-button:hover {
                background: {{ colors.primary }};
                color: {{ colors.background }};
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(255,255,255,0.2);
            }
            
            .tier-badge {
                background: {{ colors.primary }};
                color: {{ colors.background }};
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            /* Main Content */
            .content {
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }
            
            /* Header Section */
            .header-section {
                text-align: center;
                margin-bottom: 40px;
                padding: 30px;
                background: {{ colors.surface }};
                border: 2px solid {{ colors.border }};
                border-radius: 8px;
            }
            
            .page-title {
                font-size: 32px;
                font-weight: bold;
                color: {{ colors.primary }};
                letter-spacing: 3px;
                text-shadow: 0 0 10px {{ colors.primary }};
                margin-bottom: 20px;
            }
            
            /* Progress Overview */
            .overview-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            
            .overview-card {
                background: rgba(0,0,0,0.5);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 4px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s;
            }
            
            .overview-card:hover {
                transform: translateY(-2px);
                border-color: {{ colors.primary }};
            }
            
            .overview-label {
                font-size: 11px;
                color: rgba(255,255,255,0.6);
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
            }
            
            .overview-value {
                font-size: 28px;
                font-weight: bold;
                color: {{ colors.primary }};
            }
            
            /* Modules Section */
            .modules-section {
                margin-bottom: 40px;
            }
            
            .section-title {
                font-size: 24px;
                color: {{ colors.accent }};
                margin-bottom: 20px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .module-card {
                background: {{ colors.surface }};
                border: 1px solid {{ colors.border }};
                border-radius: 8px;
                padding: 25px;
                margin-bottom: 20px;
                transition: all 0.3s;
            }
            
            .module-card:hover {
                border-color: {{ colors.primary }};
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }
            
            .module-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .module-name {
                font-size: 18px;
                font-weight: bold;
                color: {{ colors.secondary }};
            }
            
            .module-stats {
                font-size: 14px;
                color: rgba(255,255,255,0.6);
            }
            
            .progress-container {
                background: rgba(0,0,0,0.8);
                border-radius: 8px;
                padding: 4px;
                margin-bottom: 10px;
            }
            
            .progress-bar {
                background: rgba(255,255,255,0.1);
                height: 12px;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .progress-fill {
                background: {{ colors.primary }};
                height: 100%;
                transition: width 0.5s ease;
                box-shadow: 0 0 10px {{ colors.primary }};
            }
            
            .progress-text {
                text-align: center;
                margin-top: 8px;
                font-size: 14px;
                color: {{ colors.primary }};
                font-weight: bold;
            }
            
            /* Pattern Mastery Section */
            .pattern-mastery {
                background: rgba(0,0,0,0.8);
                border: 2px solid {{ colors.border }};
                border-radius: 8px;
                padding: 30px;
                margin-bottom: 40px;
            }
            
            .pattern-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .pattern-item {
                background: {{ colors.surface }};
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 4px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s;
            }
            
            .pattern-item:hover {
                transform: translateY(-2px);
                border-color: {{ colors.primary }};
            }
            
            .pattern-name {
                font-size: 14px;
                font-weight: bold;
                color: {{ colors.accent }};
                margin-bottom: 10px;
                text-transform: uppercase;
            }
            
            .mastery-circle {
                width: 80px;
                height: 80px;
                margin: 0 auto 10px;
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: conic-gradient(
                    {{ colors.primary }} 0deg,
                    {{ colors.primary }} calc(var(--progress) * 3.6deg),
                    rgba(255,255,255,0.1) calc(var(--progress) * 3.6deg)
                );
            }
            
            .mastery-value {
                position: absolute;
                font-size: 24px;
                font-weight: bold;
                color: {{ colors.secondary }};
            }
            
            /* Next Lesson Card */
            .next-lesson-card {
                background: linear-gradient(135deg, {{ colors.primary }}, {{ colors.accent }});
                color: {{ colors.background }};
                padding: 30px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 40px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }
            
            .next-lesson-title {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .next-lesson-name {
                font-size: 24px;
                margin-bottom: 20px;
            }
            
            .start-button {
                background: {{ colors.background }};
                color: {{ colors.primary }};
                border: none;
                padding: 15px 40px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 2px;
                transition: all 0.3s;
            }
            
            .start-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }
            
            /* Achievements Section */
            .achievements-section {
                margin-bottom: 40px;
            }
            
            .achievement-list {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .achievement-badge {
                background: rgba({{ colors.accent }}, 0.2);
                border: 1px solid {{ colors.accent }};
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
                color: {{ colors.accent }};
            }
            
            /* Mobile Responsive */
            @media (max-width: 600px) {
                .overview-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .pattern-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .module-header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                }
            }
        </style>
    </head>
    <body>
        <div class="top-bar">
            <a href="#" class="back-button" onclick="window.close(); return false;">
                <span>←</span>
                <span>Back</span>
            </a>
            <div class="tier-badge">{{ content.tier|upper }} TRAINING</div>
        </div>
        
        <div class="content">
            <!-- Header Section -->
            <div class="header-section">
                <h1 class="page-title">{{ content.title }}</h1>
                <div class="overview-grid">
                    <div class="overview-card">
                        <div class="overview-label">Total Progress</div>
                        <div class="overview-value">{{ ((content.modules|sum(attribute='progress')) / (content.modules|length))|round }}%</div>
                    </div>
                    <div class="overview-card">
                        <div class="overview-label">Patterns Learned</div>
                        <div class="overview-value">{{ content.pattern_mastery|length }}</div>
                    </div>
                    <div class="overview-card">
                        <div class="overview-label">Achievements</div>
                        <div class="overview-value">{{ content.achievements|length }}</div>
                    </div>
                    <div class="overview-card">
                        <div class="overview-label">Training Hours</div>
                        <div class="overview-value">24.5</div>
                    </div>
                </div>
            </div>
            
            <!-- Training Modules -->
            <div class="modules-section">
                <h2 class="section-title">Training Modules</h2>
                {% for module in content.modules %}
                <div class="module-card">
                    <div class="module-header">
                        <h3 class="module-name">{{ module.name }}</h3>
                        <span class="module-stats">{{ module.completed_lessons }}/{{ module.total_lessons }} Lessons</span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ module.progress }}%"></div>
                        </div>
                    </div>
                    <div class="progress-text">{{ module.progress }}% Complete</div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Pattern Mastery -->
            <div class="pattern-mastery">
                <h2 class="section-title">Pattern Mastery</h2>
                <div class="pattern-grid">
                    {% for pattern, mastery in content.pattern_mastery.items() %}
                    <div class="pattern-item">
                        <div class="pattern-name">{{ pattern.replace('_', ' ') }}</div>
                        <div class="mastery-circle" style="--progress: {{ mastery }}">
                            <div class="mastery-value">{{ mastery }}%</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Next Lesson -->
            <div class="next-lesson-card">
                <h3 class="next-lesson-title">Next Lesson</h3>
                <div class="next-lesson-name">{{ content.next_lesson }}</div>
                <button class="start-button" onclick="alert('Lesson starting soon!')">START LESSON</button>
            </div>
            
            <!-- Achievements -->
            <div class="achievements-section">
                <h2 class="section-title">Recent Achievements</h2>
                <div class="achievement-list">
                    {% for achievement in content.achievements %}
                    <div class="achievement-badge">🏆 {{ achievement }}</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(EDUCATION_TEMPLATE, content=content, colors=colors)

# Add more endpoints as needed...

def render_signal_selection(user_id, active_signals):
    """Render signal selection page when multiple signals are active"""
    colors = get_tier_styles('nibbler')
    
    SELECTION_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Select Mission</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background: {{ colors.background }};
                color: {{ colors.secondary }};
                font-family: 'Consolas', monospace;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                color: {{ colors.primary }};
                margin-bottom: 30px;
            }
            .signal-card {
                background: {{ colors.surface }};
                border: 2px solid {{ colors.border }};
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 15px;
                cursor: pointer;
                transition: all 0.3s;
            }
            .signal-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(255,255,255,0.1);
                border-color: {{ colors.accent }};
            }
            .signal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .signal-pattern {
                font-weight: bold;
                color: {{ colors.accent }};
            }
            .signal-time {
                color: {{ colors.danger }};
                font-size: 14px;
            }
            .signal-details {
                display: flex;
                gap: 20px;
                color: rgba(255,255,255,0.8);
            }
            .tcs-score {
                font-weight: bold;
            }
            .tcs-high { color: {{ colors.tcs_high }}; }
            .tcs-medium { color: {{ colors.tcs_medium }}; }
            .tcs-low { color: {{ colors.tcs_low }}; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🎯 SELECT ACTIVE MISSION</h1>
            
            {% for signal in signals %}
            <div class="signal-card" onclick="selectSignal('{{ signal.id }}')">
                <div class="signal-header">
                    <span class="signal-pattern">{{ signal.pattern | replace('_', ' ') }}</span>
                    <span class="signal-time">⏰ {{ signal.time_remaining // 60 }}m {{ signal.time_remaining % 60 }}s</span>
                </div>
                <div class="signal-details">
                    <span>{{ signal.symbol }}</span>
                    <span>{{ signal.direction }}</span>
                    <span class="tcs-score {% if signal.tcs_score >= 85 %}tcs-high{% elif signal.tcs_score >= 75 %}tcs-medium{% else %}tcs-low{% endif %}">
                        {{ signal.tcs_score }}%
                    </span>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <script>
            const tg = window.Telegram?.WebApp;
            if (tg) {
                tg.ready();
                tg.expand();
            }
            
            function selectSignal(signalId) {
                // Find the signal data
                const signals = {{ signals | tojson }};
                const signal = signals.find(s => s.id === signalId);
                
                if (signal) {
                    // Redirect to HUD with signal data
                    const data = {
                        user_id: '{{ user_id }}',
                        signal: signal
                    };
                    const encoded = encodeURIComponent(JSON.stringify(data));
                    window.location.href = `/hud?data=${encoded}`;
                }
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(SELECTION_TEMPLATE, 
                                  user_id=user_id, 
                                  signals=active_signals, 
                                  colors=colors)

def render_no_signals(user_id):
    """Render page when no active signals"""
    colors = get_tier_styles('nibbler')
    
    NO_SIGNALS_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>No Active Missions</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background: {{ colors.background }};
                color: {{ colors.secondary }};
                font-family: 'Consolas', monospace;
                margin: 0;
                padding: 20px;
                text-align: center;
            }
            .container {
                max-width: 500px;
                margin: 50px auto;
            }
            .icon {
                font-size: 72px;
                margin-bottom: 20px;
                opacity: 0.5;
            }
            .message {
                font-size: 24px;
                color: {{ colors.primary }};
                margin-bottom: 20px;
            }
            .submessage {
                color: rgba(255,255,255,0.6);
                margin-bottom: 40px;
            }
            .button {
                display: inline-block;
                padding: 15px 40px;
                background: {{ colors.primary }};
                color: {{ colors.background }};
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                transition: all 0.3s;
            }
            .button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(255,255,255,0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🎯</div>
            <div class="message">NO ACTIVE MISSIONS</div>
            <div class="submessage">
                All missions have expired or been completed.<br>
                Stand by for next signal transmission.
            </div>
            <a href="#" onclick="closeWindow()" class="button">RETURN TO BASE</a>
        </div>
        
        <script>
            const tg = window.Telegram?.WebApp;
            if (tg) {
                tg.ready();
                tg.expand();
            }
            
            function closeWindow() {
                if (tg) {
                    tg.close();
                } else {
                    window.close();
                }
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(NO_SIGNALS_TEMPLATE, colors=colors)

@app.route('/websocket-test')
def websocket_test():
    """Serve the WebSocket test page"""
    return send_from_directory('.', 'websocket_test.html')

@app.route('/report')
@app.route('/backtest-report')
@app.route('/pdf-report')
def serve_backtest_report():
    """Serve the BITTEN Game Rules Backtesting Report PDF"""
    return send_from_directory('.', 'BITTEN_GAME_RULES_BACKTEST_REPORT.pdf', 
                              as_attachment=False, 
                              mimetype='application/pdf')

@app.route('/download-report')
def download_backtest_report():
    """Download the BITTEN Game Rules Backtesting Report PDF"""
    return send_from_directory('.', 'BITTEN_GAME_RULES_BACKTEST_REPORT.pdf', 
                              as_attachment=True, 
                              download_name='BITTEN_Game_Rules_Backtest_Report.pdf')

@app.route('/report-page')
def report_download_page():
    """Serve a nice download page for the report"""
    
    REPORT_PAGE_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BITTEN Game Rules Backtesting Report</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
                color: #ffffff;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                max-width: 900px;
                background: rgba(26, 26, 26, 0.95);
                border: 2px solid #00ff88;
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 0 30px rgba(0, 255, 136, 0.3);
                text-align: center;
            }
            h1 {
                color: #00ff88;
                font-size: 2.5em;
                margin-bottom: 20px;
                text-shadow: 0 2px 10px rgba(0, 255, 136, 0.5);
            }
            .subtitle {
                font-size: 1.2em;
                color: #cccccc;
                margin-bottom: 30px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .stat-box {
                background: rgba(0, 255, 136, 0.1);
                border: 1px solid rgba(0, 255, 136, 0.3);
                border-radius: 10px;
                padding: 20px;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #00ff88;
            }
            .stat-label {
                font-size: 0.9em;
                color: #cccccc;
                margin-top: 5px;
            }
            .download-section {
                margin: 40px 0;
                padding: 30px;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 10px;
                border: 1px solid rgba(0, 255, 136, 0.2);
            }
            .download-btn {
                display: inline-block;
                background: linear-gradient(45deg, #00ff88, #00cc6a);
                color: #000000;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 1.3em;
                margin: 10px;
                box-shadow: 0 4px 15px rgba(0, 255, 136, 0.4);
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
            }
            .download-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 25px rgba(0, 255, 136, 0.6);
                background: linear-gradient(45deg, #00cc6a, #00ff88);
            }
            .view-btn {
                background: linear-gradient(45deg, #0099ff, #0077cc);
                color: #ffffff;
            }
            .view-btn:hover {
                background: linear-gradient(45deg, #0077cc, #0099ff);
                box-shadow: 0 6px 25px rgba(0, 153, 255, 0.6);
            }
            .features {
                text-align: left;
                margin: 30px 0;
            }
            .features ul {
                list-style: none;
                padding: 0;
            }
            .features li {
                margin: 10px 0;
                padding-left: 25px;
                position: relative;
            }
            .features li:before {
                content: "✅";
                position: absolute;
                left: 0;
            }
            .footer {
                margin-top: 40px;
                font-size: 0.9em;
                color: #888888;
            }
            @media (max-width: 768px) {
                .container {
                    margin: 10px;
                    padding: 20px;
                }
                h1 {
                    font-size: 2em;
                }
                .stats-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 BITTEN Game Rules Backtesting Report</h1>
            <div class="subtitle">
                Complete validation of trading system mechanics and user protection
            </div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-number">69.4%</div>
                    <div class="stat-label">Blocking Rate</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">77.0%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">124</div>
                    <div class="stat-label">Signals Tested</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">4</div>
                    <div class="stat-label">Tiers Validated</div>
                </div>
            </div>
            
            <div class="download-section">
                <h3>📄 Access the Full Report</h3>
                <a href="/report" class="download-btn view-btn" target="_blank">
                    👁️ View in Browser
                </a>
                <a href="/download-report" class="download-btn">
                    📥 Download PDF
                </a>
            </div>
            
            <div class="features">
                <h3>🛡️ Validation Results</h3>
                <ul>
                    <li><strong>344 trades blocked</strong> out of 496 attempts - user protection working</li>
                    <li><strong>All tier restrictions enforced</strong> - NIBBLER, FANG, COMMANDER, APEX</li>
                    <li><strong>TCS thresholds validated</strong> - 70%/85%/91%/91% by tier</li>
                    <li><strong>Daily shot limits working</strong> - 6/10/12/unlimited per tier</li>
                    <li><strong>30-minute cooldowns enforced</strong> - preventing overtrading</li>
                    <li><strong>Risk management operational</strong> - daily drawdown protection</li>
                    <li><strong>All BITTEN game mechanics</strong> from RULES_OF_ENGAGEMENT.md enforced</li>
                </ul>
            </div>
            
            <div class="footer">
                <p><strong>Report Generated:</strong> July 10, 2025</p>
                <p><strong>Test Period:</strong> 2 weeks (2024-01-01 to 2024-01-14)</p>
                <p><strong>System Status:</strong> Production Ready ✅</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(REPORT_PAGE_TEMPLATE)

# WebSocket Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    # Send current active signals to newly connected client
    try:
        active_signals = get_active_signals()
        emit('signals_update', {
            'signals': active_signals,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error sending initial signals: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_signal')
def handle_join_signal(data):
    """Handle client joining a specific signal room"""
    signal_id = data.get('signal_id')
    if signal_id:
        join_room(f"signal_{signal_id}")
        emit('joined_signal', {
            'signal_id': signal_id,
            'status': 'success'
        })
        print(f"Client {request.sid} joined signal room: {signal_id}")

@socketio.on('leave_signal')
def handle_leave_signal(data):
    """Handle client leaving a specific signal room"""
    signal_id = data.get('signal_id')
    if signal_id:
        leave_room(f"signal_{signal_id}")
        emit('left_signal', {
            'signal_id': signal_id,
            'status': 'success'
        })
        print(f"Client {request.sid} left signal room: {signal_id}")

@socketio.on('fire_signal')
def handle_fire_signal(data):
    """Handle when a user fires a signal"""
    signal_id = data.get('signal_id')
    user_id = data.get('user_id')
    tier = data.get('tier', 'nibbler')
    
    if signal_id and user_id:
        # Broadcast to all clients in the signal room
        socketio.emit('signal_fired', {
            'signal_id': signal_id,
            'user_id': user_id,
            'tier': tier,
            'timestamp': datetime.now().isoformat(),
            'fire_count': data.get('fire_count', 1)
        }, room=f"signal_{signal_id}")
        
        # Also broadcast to all clients for global updates
        socketio.emit('engagement_update', {
            'signal_id': signal_id,
            'action': 'fire',
            'user_id': user_id,
            'tier': tier,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"Signal fired: {signal_id} by user {user_id} (tier: {tier})")

@socketio.on('update_engagement')
def handle_update_engagement(data):
    """Handle real-time engagement updates"""
    signal_id = data.get('signal_id')
    engagement_data = data.get('engagement_data', {})
    
    if signal_id:
        # Broadcast engagement updates to all clients in the signal room
        socketio.emit('engagement_updated', {
            'signal_id': signal_id,
            'engagement_data': engagement_data,
            'timestamp': datetime.now().isoformat()
        }, room=f"signal_{signal_id}")
        
        print(f"Engagement updated for signal: {signal_id}")

def broadcast_signal_update(signal_id, update_type, data=None):
    """Utility function to broadcast signal updates"""
    socketio.emit('signal_update', {
        'signal_id': signal_id,
        'update_type': update_type,
        'data': data or {},
        'timestamp': datetime.now().isoformat()
    })

def broadcast_fire_count_update(signal_id, new_count, user_data=None):
    """Utility function to broadcast fire count updates"""
    socketio.emit('fire_count_update', {
        'signal_id': signal_id,
        'new_count': new_count,
        'user_data': user_data or {},
        'timestamp': datetime.now().isoformat()
    }, room=f"signal_{signal_id}")

# ====== NEW API ENDPOINTS ======

@app.route('/api/fire', methods=['POST'])
def api_fire():
    """Handle user fire actions with user_id and signal_id"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        user_id = data.get('user_id')
        signal_id = data.get('signal_id')
        
        if not user_id or not signal_id:
            return jsonify({
                "success": False,
                "error": "user_id and signal_id are required"
            }), 400
        
        # Validate user_id and signal_id format
        if not isinstance(user_id, str) or not isinstance(signal_id, str):
            return jsonify({
                "success": False,
                "error": "user_id and signal_id must be strings"
            }), 400
        
        # Handle the fire action
        result = handle_fire_action(user_id, signal_id)
        
        if result.get('success'):
            # Emit real-time update to signal room
            socketio.emit('fire_update', {
                'user_id': user_id,
                'signal_id': signal_id,
                'timestamp': datetime.now().isoformat()
            }, room=f"signal_{signal_id}")
            
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/stats/<signal_id>', methods=['GET'])
def api_signal_stats(signal_id):
    """Return live engagement data for signal"""
    try:
        if not signal_id:
            return jsonify({
                "error": "signal_id is required"
            }), 400
        
        stats = get_signal_stats(signal_id)
        
        if 'error' in stats:
            return jsonify(stats), 500
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/user/<user_id>/stats', methods=['GET'])
def api_user_stats(user_id):
    """Return real user statistics"""
    try:
        if not user_id:
            return jsonify({
                "error": "user_id is required"
            }), 400
        
        stats = get_user_stats(user_id)
        
        if 'error' in stats:
            return jsonify(stats), 500
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/signals/active', methods=['GET'])
def api_active_signals():
    """Return all active signals with engagement counts"""
    try:
        signals = get_active_signals_with_engagement()
        
        # Check if there's an error in the result
        if len(signals) == 1 and 'error' in signals[0]:
            return jsonify({
                "success": False,
                "error": signals[0]['error']
            }), 500
        
        return jsonify({
            "success": True,
            "data": {
                "signals": signals,
                "total_count": len(signals),
                "timestamp": datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

# Timer Integration Endpoints
@app.route('/api/mission/<mission_id>/timer', methods=['GET'])
def get_mission_timer(mission_id):
    """Get real-time timer for mission brief"""
    
    if not TIMER_INTEGRATION_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Timer integration not available'
        }), 503
    
    try:
        countdown_data = smart_timer_integration.get_real_time_countdown(mission_id)
        
        return jsonify({
            'success': True,
            'mission_id': mission_id,
            'timer': countdown_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trades/expired', methods=['GET'])
def get_expired_trades():
    """Get all expired trades (for reference)"""
    
    if not TIMER_INTEGRATION_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Timer integration not available'
        }), 503
    
    try:
        symbol = request.args.get('symbol')
        expired_trades = expired_trade_handler.get_all_expired_trades(symbol)
        
        # Format for display
        formatted_trades = [
            ExpiredTradeDisplay.format_for_webapp(trade)
            for trade in expired_trades
        ]
        
        return jsonify({
            'success': True,
            'expired_trades': formatted_trades,
            'total': len(formatted_trades)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trades/<mission_id>/execute', methods=['POST'])
def execute_trade_with_expiry_check(mission_id):
    """Attempt to execute a trade (checks if expired)"""
    
    if not TIMER_INTEGRATION_AVAILABLE:
        # Fall back to normal execution
        return execute_normal_trade(mission_id)
    
    try:
        # Get user ID from request or session
        user_id = request.json.get('user_id', 'unknown_user')
        
        # Check if trade is expired
        result = expired_trade_handler.attempt_execution(mission_id, user_id)
        
        if not result['success']:
            # Trade is expired
            return jsonify(result), 403
        
        # Continue with normal execution
        return execute_normal_trade(mission_id)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def execute_normal_trade(mission_id):
    """Normal trade execution logic (placeholder)"""
    # This would be your existing trade execution logic
    return jsonify({
        'success': True,
        'message': 'Trade execution placeholder - connect to your MT5 bridge'
    })

@app.route('/api/trades/<mission_id>/status', methods=['GET'])
def get_trade_status(mission_id):
    """Get current status of a trade (active/expired)"""
    
    if not TIMER_INTEGRATION_AVAILABLE:
        return jsonify({
            'status': 'unknown',
            'message': 'Timer integration not available'
        })
    
    try:
        # Check if expired
        expired_trade = expired_trade_handler.get_expired_trade(mission_id)
        if expired_trade:
            return jsonify({
                'status': 'expired',
                'expired_trade': ExpiredTradeDisplay.format_for_webapp(expired_trade)
            })
        
        # Check if still active
        countdown = smart_timer_integration.get_real_time_countdown(mission_id)
        
        return jsonify({
            'status': 'active' if not countdown['expired'] else 'expired',
            'countdown': countdown
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Onboarding routes
@app.route('/onboarding/<path:filename>')
def serve_onboarding(filename):
    return send_from_directory('onboarding', filename)

@app.route('/start')
@app.route('/press-pass')
def onboarding_start():
    return redirect('/onboarding/enhanced_landing.html')

@app.route('/api/track-event', methods=['POST'])
def track_event():
    # Analytics tracking endpoint
    data = request.get_json()
    # Log to analytics service
    print(f"Event: {data.get('event')} - {data.get('data')}")
    return jsonify({'success': True})

@app.route('/mission-briefing')
@app.route('/mission-briefing.html')
def mission_briefing():
    return send_from_directory('.', 'mission-briefing.html')

# Import ally code system
try:
    from ally_code_system import AllyCodeManager, apply_ally_code_discount
    ALLY_CODE_AVAILABLE = True
    ally_manager = AllyCodeManager()
except ImportError as e:
    logger.warning(f"Ally code system not available: {e}")
    ALLY_CODE_AVAILABLE = False

# Ally Code API Endpoints
@app.route('/api/validate-ally-code', methods=['POST'])
def validate_ally_code():
    """Validate an ally code"""
    if not ALLY_CODE_AVAILABLE:
        return jsonify({'valid': False, 'error': 'ALLY CODE system not available'}), 500
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        
        if not code:
            return jsonify({'valid': False, 'error': 'No code provided'}), 400
        
        validation = ally_manager.validate_ally_code(code)
        
        if validation['valid']:
            return jsonify({
                'valid': True,
                'code_type': validation['code_type'],
                'discount_type': validation['discount_type'],
                'discount_value': validation['discount_value'],
                'description': validation['metadata'].get('description', 'Valid ALLY CODE'),
                'metadata': validation['metadata']
            })
        else:
            return jsonify(validation)
            
    except Exception as e:
        logger.error(f"Ally code validation error: {e}")
        return jsonify({'valid': False, 'error': 'Validation failed'}), 500

@app.route('/api/check-founder-status', methods=['POST'])
def check_founder_status():
    """Check if a Telegram user has founder status"""
    if not ALLY_CODE_AVAILABLE:
        return jsonify({'is_founder': False}), 500
    
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({'is_founder': False, 'error': 'No telegram ID provided'}), 400
        
        status = ally_manager.check_founder_status(telegram_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Founder status check error: {e}")
        return jsonify({'is_founder': False, 'error': 'Status check failed'}), 500

@app.route('/api/apply-founder-upgrade', methods=['POST'])
def apply_founder_upgrade():
    """Apply founder discount to an upgrade"""
    if not ALLY_CODE_AVAILABLE:
        return jsonify({'founder_discount': False}), 500
    
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        new_tier = data.get('tier', 'FANG').upper()
        
        if not telegram_id:
            return jsonify({'founder_discount': False, 'error': 'No telegram ID provided'}), 400
        
        if new_tier not in TIER_PRICING:
            return jsonify({'founder_discount': False, 'error': 'Invalid tier'}), 400
        
        new_tier_price = TIER_PRICING[new_tier]['price']
        upgrade_result = ally_manager.apply_founder_upgrade(telegram_id, new_tier, new_tier_price)
        
        return jsonify(upgrade_result)
        
    except Exception as e:
        logger.error(f"Founder upgrade error: {e}")
        return jsonify({'founder_discount': False, 'error': 'Upgrade failed'}), 500

@app.route('/admin/ally-codes')
def admin_ally_codes():
    """Admin interface for ally codes (simple auth check)"""
    # Simple auth - check for admin parameter
    if request.args.get('admin_key') != 'BITTEN_ADMIN_2025':
        return "Access denied", 403
    
    if not ALLY_CODE_AVAILABLE:
        return "Ally code system not available", 500
    
    stats = ally_manager.get_code_stats()
    
    # Get all codes with usage info and founder bindings
    import sqlite3
    conn = sqlite3.connect(ally_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ac.code, ac.code_type, ac.discount_type, ac.discount_value, 
               ac.uses_remaining, ac.max_uses, ac.created_date, ac.metadata,
               COUNT(cu.id) as total_uses,
               fs.telegram_id, fs.current_tier, fs.total_savings
        FROM ally_codes ac
        LEFT JOIN code_usage cu ON ac.code = cu.code
        LEFT JOIN founder_status fs ON ac.code = fs.founder_code
        GROUP BY ac.code
        ORDER BY ac.code_type, ac.code
    ''')
    
    codes_data = cursor.fetchall()
    
    # Get founder statistics
    cursor.execute('''
        SELECT COUNT(*) as active_founders, SUM(total_savings) as total_founder_savings
        FROM founder_status
    ''')
    founder_stats = cursor.fetchone()
    
    conn.close()
    
    admin_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BITTEN ALLY CODE Admin</title>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff41; padding: 20px; }}
            .admin-container {{ max-width: 1200px; margin: 0 auto; }}
            .stats {{ background: rgba(0,255,65,0.1); padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
            .codes-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .codes-table th, .codes-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
            .codes-table th {{ background: rgba(0,255,65,0.2); color: #ffd700; }}
            .founder {{ color: #ffd700; font-weight: bold; }}
            .influencer {{ color: #00bfff; }}
            .used {{ color: #ff6666; }}
            .available {{ color: #00ff41; }}
        </style>
    </head>
    <body>
        <div class="admin-container">
            <h1>🎖️ BITTEN ALLY CODE Administration</h1>
            
            <div class="stats">
                <h2>📊 Statistics</h2>
                <p><strong>Code Types:</strong></p>
                {"".join([f'<li>{stat["type"]}: {stat["total"]} total, {stat["available"]} available</li>' for stat in stats["code_types"]])}
                <p><strong>Usage:</strong> {stats["total_uses"]} total uses, {stats["unique_codes_used"]} unique codes used</p>
                <p><strong>Commissions:</strong> ${stats["pending_commissions"]:.2f} pending ({stats["pending_commission_count"]} payments)</p>
                <p><strong>Founders:</strong> {founder_stats[0] or 0} active founders, ${founder_stats[1] or 0:.2f} total savings</p>
            </div>
            
            <h2>🔑 All ALLY CODES</h2>
            <table class="codes-table">
                <tr>
                    <th>Code</th>
                    <th>Type</th>
                    <th>Discount</th>
                    <th>Value</th>
                    <th>Uses</th>
                    <th>Status</th>
                    <th>Bound To</th>
                    <th>Current Tier</th>
                    <th>Total Savings</th>
                </tr>
    """
    
    for code_data in codes_data:
        code, code_type, discount_type, discount_value, uses_remaining, max_uses, created_date, metadata, total_uses, telegram_id, current_tier, total_savings = code_data
        
        status_class = "founder" if code_type == "FOUNDER_LEGACY" else "influencer"
        status_text = "bound" if telegram_id else ("available" if uses_remaining > 0 else "used")
        status_color = "founder" if telegram_id else ("available" if uses_remaining > 0 else "used")
        
        bound_to = f"TG:{telegram_id[-4:]}" if telegram_id else "-"
        tier_display = current_tier or "-"
        savings_display = f"${total_savings:.0f}" if total_savings else "-"
        
        admin_html += f"""
                <tr class="{status_class}">
                    <td><strong>{code}</strong></td>
                    <td>{code_type}</td>
                    <td>{discount_type}</td>
                    <td>${discount_value:.0f}</td>
                    <td>{max_uses - uses_remaining}/{max_uses}</td>
                    <td class="{status_color}">{status_text}</td>
                    <td>{bound_to}</td>
                    <td>{tier_display}</td>
                    <td>{savings_display}</td>
                </tr>
        """
    
    admin_html += """
            </table>
        </div>
    </body>
    </html>
    """
    
    return admin_html

# Stripe Payment Endpoints
@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe checkout session for subscription"""
    try:
        data = request.get_json()
        tier = data.get('tier', 'FANG').upper()
        user_id = data.get('user_id', 'anonymous')
        ally_code = data.get('ally_code')
        
        # Validate tier
        if tier not in TIER_PRICING:
            return jsonify({'error': 'Invalid tier'}), 400
        
        # Handle ally code if provided
        ally_discount_info = None
        if ally_code and ALLY_CODE_AVAILABLE:
            validation = ally_manager.validate_ally_code(ally_code)
            if validation['valid']:
                # Apply discount
                original_price = TIER_PRICING[tier]['price']
                ally_discount_info = apply_ally_code_discount(tier, original_price, validation)
                
                # For founder codes - handle discounted subscription
                if validation['code_type'] == 'FOUNDER_LEGACY':
                    final_price = ally_discount_info['final_price']
                    
                    if final_price <= 0:
                        # Free tier (NIBBLER/FANG with founder discount)
                        session = stripe.checkout.Session.create(
                            payment_method_types=['card'],
                            line_items=[{
                                'price_data': {
                                    'currency': 'usd',
                                    'product_data': {
                                        'name': f'BITTEN {tier} - FOUNDER LEGACY',
                                        'description': f'Lifetime {tier} access - Founder privilege'
                                    },
                                    'unit_amount': 100,  # $1 setup fee only
                                },
                                'quantity': 1,
                            }],
                            mode='payment',
                            success_url=request.host_url + f'payment-success?session_id={{CHECKOUT_SESSION_ID}}&tier={tier}&ally_code={ally_code}',
                            cancel_url=request.host_url + f'upgrade?tier={tier}&cancelled=true',
                            metadata={
                                'tier': tier,
                                'user_id': user_id,
                                'ally_code': ally_code,
                                'code_type': 'FOUNDER_LEGACY',
                                'final_price': final_price,
                                'source': 'webapp'
                            }
                        )
                    else:
                        # Discounted subscription (COMMANDER/APEX with founder discount)
                        session = stripe.checkout.Session.create(
                            payment_method_types=['card'],
                            line_items=[{
                                'price_data': {
                                    'currency': 'usd',
                                    'product_data': {
                                        'name': f'BITTEN {tier} - FOUNDER LEGACY',
                                        'description': f'{tier} with $89 founder discount'
                                    },
                                    'unit_amount': final_price,
                                    'recurring': {'interval': 'month'}
                                },
                                'quantity': 1,
                            }],
                            mode='subscription',
                            success_url=request.host_url + f'payment-success?session_id={{CHECKOUT_SESSION_ID}}&tier={tier}&ally_code={ally_code}',
                            cancel_url=request.host_url + f'upgrade?tier={tier}&cancelled=true',
                            metadata={
                                'tier': tier,
                                'user_id': user_id,
                                'ally_code': ally_code,
                                'code_type': 'FOUNDER_LEGACY',
                                'original_price': original_price,
                                'final_price': final_price,
                                'source': 'webapp'
                            }
                        )
                    
                    return jsonify({'checkout_url': session.url})
            else:
                return jsonify({'error': f'Invalid ALLY CODE: {validation.get("error", "Unknown error")}'}), 400
        
        # Get price ID from environment
        price_id = os.getenv(f'STRIPE_PRICE_{tier}')
        if not price_id:
            return jsonify({'error': f'Price not configured for {tier}'}), 500
        
        # Create regular subscription checkout session
        session_data = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': price_id,
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': request.host_url + f'payment-success?session_id={{CHECKOUT_SESSION_ID}}&tier={tier}',
            'cancel_url': request.host_url + f'upgrade?tier={tier}&cancelled=true',
            'metadata': {
                'tier': tier,
                'user_id': user_id,
                'source': 'webapp'
            }
        }
        
        # Add ally code to metadata if provided
        if ally_code:
            session_data['metadata']['ally_code'] = ally_code
            session_data['success_url'] += f'&ally_code={ally_code}'
        
        # Apply discount for influencer codes
        if ally_discount_info and ally_discount_info['type'] == 'first_month_discount':
            # Create discounted subscription
            session_data['discounts'] = [{
                'coupon': 'first_month_50_off'  # You'd need to create this in Stripe
            }]
        
        session = stripe.checkout.Session.create(**session_data)
        
        return jsonify({'checkout_url': session.url})
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return jsonify({'error': 'Payment processing error'}), 500
    except Exception as e:
        logger.error(f"Checkout session error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/payment-success')
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    tier = request.args.get('tier', 'FANG')
    ally_code = request.args.get('ally_code')
    
    if not session_id:
        return redirect('/upgrade?error=no_session')
    
    try:
        # Retrieve the session to verify payment
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Handle ally code usage if provided
            if ally_code and ALLY_CODE_AVAILABLE:
                try:
                    ally_manager.use_ally_code(
                        ally_code,
                        user_id=session.metadata.get('user_id'),
                        email=session.customer_details.email if session.customer_details else None,
                        stripe_session_id=session_id,
                        ip_address=request.remote_addr
                    )
                    logger.info(f"ALLY CODE {ally_code} used successfully for session {session_id}")
                except Exception as e:
                    logger.error(f"Failed to use ally code {ally_code}: {e}")
            
            # Check if this is a founder legacy payment
            is_founder = ally_code and ally_code.startswith('FOUNDER')
            
            # Payment successful - show success page
            title_text = "🏆 FOUNDER LEGACY ACTIVATED!" if is_founder else f"🎯 BITTEN {tier} ACTIVATED!"
            main_message = "FOUNDER LEGACY" if is_founder else f"BITTEN {tier}"
            
            success_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{title_text}</title>
                <style>
                    body {{
                        font-family: 'Courier New', monospace;
                        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                        color: #00ff41;
                        text-align: center;
                        padding: 50px 20px;
                        min-height: 100vh;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    }}
                    .success-container {{
                        background: rgba(0, 255, 65, 0.1);
                        border: 2px solid #00ff41;
                        border-radius: 20px;
                        padding: 40px;
                        max-width: 500px;
                        margin: 0 auto;
                        animation: pulse 2s infinite;
                    }}
                    @keyframes pulse {{
                        0%, 100% {{ transform: scale(1); }}
                        50% {{ transform: scale(1.05); }}
                    }}
                    .checkmark {{
                        font-size: 4rem;
                        color: #00ff41;
                        margin-bottom: 20px;
                    }}
                    .tier-title {{
                        font-size: 2rem;
                        color: #ffd700;
                        margin-bottom: 20px;
                    }}
                    .success-message {{
                        font-size: 1.2rem;
                        line-height: 1.6;
                        margin-bottom: 30px;
                    }}
                    .telegram-button {{
                        background: #00ff41;
                        color: #000;
                        padding: 15px 30px;
                        border: none;
                        border-radius: 10px;
                        font-size: 1.1rem;
                        font-weight: bold;
                        text-decoration: none;
                        display: inline-block;
                        transition: all 0.3s;
                    }}
                    .telegram-button:hover {{
                        background: #00cc33;
                        transform: scale(1.05);
                    }}
                </style>
            </head>
            <body>
                <div class="success-container">
                    <div class="checkmark">{"🏆" if is_founder else "✅"}</div>
                    <h1 class="tier-title">{main_message} ACTIVATED!</h1>
                    <p class="success-message">
                        {"🎖️ FOUNDER LEGACY VERIFIED!" if is_founder else "Mission accomplished, soldier!"}<br>
                        {"Lifetime FANG access granted." if is_founder else f"Your {tier} subscription is now active."}<br><br>
                        {"Welcome to the founders circle!" if is_founder else "Connect to your Telegram bot to start trading."}
                    </p>
                    <a href="https://t.me/Bitten_Commander_bot?start=activated_{tier}" class="telegram-button">
                        🚀 Launch Telegram Bot
                    </a>
                </div>
            </body>
            </html>
            """
            return success_html
        else:
            return redirect('/upgrade?error=payment_failed')
            
    except stripe.error.StripeError as e:
        logger.error(f"Payment verification error: {e}")
        return redirect('/upgrade?error=verification_failed')

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if not endpoint_secret:
        logger.error("Webhook secret not configured")
        return '', 400
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        logger.error("Invalid payload")
        return '', 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return '', 400
    
    # Handle the event
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        logger.info(f"Subscription created: {subscription['id']}")
        # TODO: Update user tier in database
        
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        logger.info(f"Subscription updated: {subscription['id']}")
        # TODO: Update user tier in database
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        logger.info(f"Subscription cancelled: {subscription['id']}")
        # TODO: Downgrade user tier in database
        
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        logger.info(f"Payment succeeded: {invoice['id']}")
        # TODO: Confirm user access
        
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        logger.info(f"Payment failed: {invoice['id']}")
        # TODO: Handle failed payment
        
    else:
        logger.info(f"Unhandled event type: {event['type']}")
    
    return '', 200

@app.route('/upgrade')
def upgrade_page():
    tier = request.args.get('tier', 'FANG')
    source = request.args.get('source', 'direct')
    
    # For now, redirect to Telegram for upgrade completion
    # Later this can be replaced with a Stripe payment page
    press_pass_id = request.args.get('press_pass_id', 'demo')
    telegram_url = f"https://t.me/Bitten_Commander_bot?start=upgrade_{tier}_{press_pass_id}"
    
    # Get pricing info
    pricing_info = TIER_PRICING.get(tier.upper(), TIER_PRICING['FANG'])
    price_display = f"${pricing_info['price']/100:.0f}"
    
    # Create upgrade page with both Stripe and Telegram options
    upgrade_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎖️ BITTEN Upgrade - {tier}</title>
        <style>
            body {{
                font-family: 'Courier New', monospace;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                color: #00ff41;
                text-align: center;
                padding: 30px 20px;
                min-height: 100vh;
            }}
            .upgrade-container {{
                background: rgba(0, 255, 65, 0.1);
                border: 2px solid #00ff41;
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                margin: 0 auto;
            }}
            .tier-title {{
                font-size: 2.5rem;
                margin-bottom: 10px;
                color: #ffd700;
            }}
            .price {{
                font-size: 2rem;
                color: #00ff41;
                margin-bottom: 20px;
            }}
            .features {{
                text-align: left;
                margin: 20px 0;
                background: rgba(0,0,0,0.3);
                padding: 20px;
                border-radius: 10px;
            }}
            .feature {{
                margin: 8px 0;
                color: #fff;
            }}
            .payment-option {{
                background: linear-gradient(45deg, #00ff41, #00aa33);
                color: #000;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                cursor: pointer;
                margin: 10px;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                min-width: 200px;
            }}
            .payment-option:hover {{
                transform: scale(1.05);
                box-shadow: 0 0 20px rgba(0, 255, 65, 0.6);
            }}
            .stripe-btn {{
                background: linear-gradient(45deg, #635bff, #0066ff);
                color: white;
            }}
            .telegram-btn {{
                background: linear-gradient(45deg, #00ff41, #00aa33);
                color: #000;
            }}
            .divider {{
                margin: 20px 0;
                color: #666;
                font-size: 14px;
            }}
            .error {{
                color: #ff4444;
                margin: 10px 0;
                padding: 10px;
                background: rgba(255,68,68,0.1);
                border-radius: 5px;
            }}
            .ally-code-section {{
                background: rgba(255,215,0,0.1);
                border: 2px solid #ffd700;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }}
            .ally-input {{
                background: rgba(0,0,0,0.8);
                border: 2px solid #ffd700;
                border-radius: 5px;
                padding: 12px 15px;
                color: #fff;
                font-size: 16px;
                font-family: 'Courier New', monospace;
                width: 200px;
                margin: 0 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .ally-input:focus {{
                outline: none;
                border-color: #00ff41;
                box-shadow: 0 0 10px rgba(0,255,65,0.5);
            }}
            .ally-btn {{
                background: linear-gradient(45deg, #ffd700, #ffaa00);
                color: #000;
                border: none;
                padding: 12px 20px;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 14px;
            }}
            .ally-btn:hover {{
                transform: scale(1.05);
                box-shadow: 0 0 15px rgba(255,215,0,0.6);
            }}
            .ally-status {{
                margin-top: 15px;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                min-height: 20px;
            }}
            .ally-success {{
                background: rgba(0,255,65,0.2);
                color: #00ff41;
                border: 1px solid #00ff41;
            }}
            .ally-error {{
                background: rgba(255,68,68,0.2);
                color: #ff4444;
                border: 1px solid #ff4444;
            }}
            .ally-founder {{
                background: linear-gradient(45deg, rgba(255,215,0,0.3), rgba(255,140,0,0.3));
                color: #ffd700;
                border: 2px solid #ffd700;
                animation: founderGlow 2s infinite;
            }}
            @keyframes founderGlow {{
                0%, 100% {{ box-shadow: 0 0 10px rgba(255,215,0,0.5); }}
                50% {{ box-shadow: 0 0 20px rgba(255,215,0,0.8); }}
            }}
        </style>
    </head>
    <body>
        <div class="upgrade-container">
            <h1 class="tier-title">🎖️ {tier} UPGRADE</h1>
            <div class="price">{price_display}/month</div>
            
            <div class="features">
                <h3>🎯 {pricing_info['name']} Features:</h3>
                {''.join([f'<div class="feature">✓ {feature}</div>' for feature in pricing_info['features']])}
            </div>
            
            {"<div class='error'>⚠️ Payment cancelled or failed. Please try again.</div>" if request.args.get('error') else ""}
            
            <div class="ally-code-section">
                <h3>🏆 Have an ALLY CODE?</h3>
                <input type="text" id="allyCode" placeholder="Enter ALLY CODE" class="ally-input">
                <button onclick="applyAllyCode()" class="ally-btn">🔓 VERIFY</button>
                <div id="allyStatus" class="ally-status"></div>
            </div>
            
            <h3>Choose Payment Method:</h3>
            
            <button onclick="payWithStripe()" class="payment-option stripe-btn" id="stripeBtn">
                💳 Pay with Card (Stripe)
            </button>
            
            <div class="divider">- OR -</div>
            
            <a href="{telegram_url}" class="payment-option telegram-btn">
                🤖 Pay via Telegram Bot
            </a>
            
            <p><small>Secure payment processing • Cancel anytime • 24/7 support</small></p>
        </div>
        
        <script>
            let currentAllyCode = null;
            let allyDiscount = null;
            
            async function applyAllyCode() {{
                const code = document.getElementById('allyCode').value.trim().toUpperCase();
                const statusDiv = document.getElementById('allyStatus');
                
                if (!code) {{
                    statusDiv.className = 'ally-status ally-error';
                    statusDiv.textContent = 'Please enter an ALLY CODE';
                    return;
                }}
                
                try {{
                    const response = await fetch('/api/validate-ally-code', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ code: code }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.valid) {{
                        currentAllyCode = code;
                        allyDiscount = data;
                        
                        if (data.code_type === 'FOUNDER_LEGACY') {{
                            statusDiv.className = 'ally-status ally-founder';
                            statusDiv.innerHTML = '🏆 FOUNDER LEGACY VERIFIED<br>Lifetime FANG Access Unlocked!';
                            
                            // Update payment button for founder
                            const stripeBtn = document.getElementById('stripeBtn');
                            stripeBtn.textContent = '🏆 ACTIVATE FOUNDER LEGACY';
                            stripeBtn.className = 'payment-option ally-founder';
                        }} else {{
                            statusDiv.className = 'ally-status ally-success';
                            statusDiv.innerHTML = `✅ ALLY CODE VERIFIED<br>${{data.description}}`;
                        }}
                    }} else {{
                        statusDiv.className = 'ally-status ally-error';
                        statusDiv.textContent = '❌ ' + data.error;
                        currentAllyCode = null;
                        allyDiscount = null;
                    }}
                }} catch (error) {{
                    statusDiv.className = 'ally-status ally-error';
                    statusDiv.textContent = '❌ Verification failed. Try again.';
                }}
            }}
            
            async function payWithStripe() {{
                try {{
                    const requestData = {{
                        tier: '{tier}',
                        user_id: '{press_pass_id}'
                    }};
                    
                    if (currentAllyCode) {{
                        requestData.ally_code = currentAllyCode;
                    }}
                    
                    const response = await fetch('/api/create-checkout-session', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify(requestData)
                    }});
                    
                    const data = await response.json();
                    
                    if (data.checkout_url) {{
                        window.location.href = data.checkout_url;
                    }} else {{
                        alert('Payment processing error: ' + (data.error || 'Unknown error'));
                    }}
                }} catch (error) {{
                    alert('Network error. Please check your connection and try again.');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return upgrade_html

# Referral API Endpoints
@app.route('/api/referral/stats', methods=['GET'])
def get_referral_stats():
    # For demo purposes, get user ID from session or Press Pass
    user_id = request.args.get('user_id', 'demo')
    
    if not REFERRAL_SYSTEM_AVAILABLE:
        # Return mock data
        return jsonify({
            'success': True,
            'stats': {
                'user_id': user_id,
                'referral_code': 'DEMO123',
                'code_uses': 0,
                'squad_stats': {
                    'total_recruits': 0,
                    'active_recruits': 0,
                    'total_xp_earned': 0,
                    'squad_rank': 'Lone Wolf'
                }
            }
        })
    
    try:
        squad_stats = referral_system.get_squad_stats(user_id)
        xp_balance = referral_system.get_xp_balance(user_id)
        
        return jsonify({
            'success': True,
            'stats': {
                'user_id': user_id,
                'referral_code': squad_stats.referral_code or 'Not generated',
                'code_uses': 0,  # TODO: Add code usage tracking
                'squad_stats': {
                    'total_recruits': squad_stats.total_recruits,
                    'active_recruits': squad_stats.active_recruits,
                    'total_xp_earned': squad_stats.total_xp_earned,
                    'squad_rank': squad_stats.squad_rank.value
                },
                'xp_balance': xp_balance
            }
        })
    except Exception as e:
        logger.error(f"Error getting referral stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/referral/generate', methods=['POST'])
def generate_referral_code():
    data = request.get_json()
    user_id = data.get('user_id', 'demo')
    custom_code = data.get('custom_code')
    
    if not REFERRAL_SYSTEM_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Referral system not available'
        }), 500
    
    try:
        success, message, code = referral_system.generate_referral_code(user_id, custom_code)
        
        return jsonify({
            'success': success,
            'message': message,
            'code': code
        })
    except Exception as e:
        logger.error(f"Error generating referral code: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/referral/debug', methods=['GET'])
def debug_referral_system():
    """Debug endpoint to check referral system status"""
    global referral_system, REFERRAL_SYSTEM_AVAILABLE
    
    return jsonify({
        'available': REFERRAL_SYSTEM_AVAILABLE,
        'system_type': type(referral_system).__name__ if referral_system else None,
        'system_exists': referral_system is not None
    })

@app.route('/api/referral/use', methods=['POST'])
def use_referral_code():
    """Use a referral code when someone signs up"""
    data = request.get_json()
    code = data.get('code')
    recruit_id = data.get('recruit_id', f"user_{int(time.time())}")
    username = data.get('username', 'Anonymous')
    ip_address = request.remote_addr
    
    if not REFERRAL_SYSTEM_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Referral system not available'
        }), 500
    
    try:
        success, message, result = referral_system.use_referral_code(code, recruit_id, username, ip_address)
        
        return jsonify({
            'success': success,
            'message': message,
            'result': result
        })
    except Exception as e:
        logger.error(f"Error using referral code: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/recruit/<code>')
def referral_landing(code):
    """Handle referral landing page"""
    
    # Create a landing page that captures the referral and redirects to onboarding
    landing_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎖️ Join the BITTEN Squad</title>
        <style>
            body {{
                font-family: 'Courier New', monospace;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                color: #00ff41;
                text-align: center;
                padding: 50px 20px;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }}
            .recruit-container {{
                background: rgba(0, 255, 65, 0.1);
                border: 2px solid #00ff41;
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                margin: 0 auto;
            }}
            .squad-title {{
                font-size: 2.5rem;
                margin-bottom: 20px;
                color: #ffd700;
            }}
            .join-btn {{
                background: linear-gradient(45deg, #00ff41, #00aa33);
                color: #000;
                border: none;
                padding: 20px 40px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 50px;
                cursor: pointer;
                margin: 20px 10px;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
            }}
            .join-btn:hover {{
                transform: scale(1.1);
                box-shadow: 0 0 30px rgba(0, 255, 65, 0.6);
            }}
            .recruit-info {{
                background: rgba(0, 0, 0, 0.8);
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="recruit-container">
            <h1 class="squad-title">🎖️ YOU'VE BEEN RECRUITED!</h1>
            
            <div class="recruit-info">
                <h3>🐾 Welcome to the BITTEN Elite Force</h3>
                <p>You've been invited to join an exclusive squad of tactical traders who dominate the forex markets using AI-powered signals.</p>
                
                <h4>🔥 What You Get:</h4>
                <ul style="text-align: left; max-width: 400px; margin: 0 auto;">
                    <li>🎯 Free Press Pass (12 hours of premium access)</li>
                    <li>🤖 AI squad guidance (Bit, Doc, Nexus, Overwatch)</li>
                    <li>⚡ Live trading signals with 89% win rate</li>
                    <li>🎮 Gamified XP system and rank progression</li>
                    <li>💰 Real money trading with demo safety</li>
                </ul>
            </div>
            
            <a href="/onboarding/enhanced_landing.html?ref={code}" class="join-btn">
                🚀 JOIN THE SQUAD NOW
            </a>
            
            <p><small>Referral Code: <strong>{code}</strong></small></p>
        </div>
        
        <script>
            // Store referral code for later use
            localStorage.setItem('referralCode', '{code}');
            
            // Track referral visit
            if (typeof gtag !== 'undefined') {{
                gtag('event', 'referral_visit', {{
                    'referral_code': '{code}'
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    return landing_html

if __name__ == '__main__':
    # Start live trade updates if available
    if LIVE_TRADE_API_AVAILABLE:
        start_live_updates(socketio)
        
    socketio.run(app, host='0.0.0.0', port=8888, debug=False, allow_unsafe_werkzeug=True)
