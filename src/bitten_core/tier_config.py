"""
BITTEN Tier Configuration Management System

Centralized tier defaults and user capability management for NIBBLER, FANG, and COMMANDER tiers.
Integrates with fire_modes.db to enforce tier-based trading limits and access controls.

Author: BITTEN Core Team
Date: 2025-10-09
"""

import sqlite3
from typing import Dict, Optional, Tuple
from datetime import datetime
import os

# ============================================================================
# TIER DEFAULTS - CONSTANTS
# ============================================================================

# NIBBLER Tier - Entry level, highly restricted
NIBBLER_DEFAULTS = {
    'subscription_tier': 'NIBBLER',
    'max_slots': 1,                      # Total concurrent positions
    'max_manual_slots': 1,               # Manual fire slots
    'max_auto_slots': 0,                 # AUTO fire disabled
    'max_auto_slots_separate': 0,        # Separate AUTO tracking
    'max_trades_per_day': 6,             # Daily trade limit
    'tier_max_trades_per_day': 6,        # Tier-based daily limit
    'risk_per_trade': 0.005,             # 0.5% risk per trade
    'auto_fire_min_confidence': 80.0,    # N/A - AUTO disabled
    'auto_fire_max_confidence': 89.0,    # N/A - AUTO disabled
    'auto_fire_enabled': False,          # AUTO mode locked
    'bitmode_enabled': False,            # BITMODE locked
    'trading_enabled': True,             # Manual trading allowed
    'admin_controlled_risk': True,       # Risk locked by admin
    'admin_controlled_confidence': True, # Confidence locked by admin
    'admin_locked_slots': True,          # Slots locked by admin
    'admin_locked_daily_trades': True,   # Daily limit locked by admin
    'user_can_change_confidence': False, # Cannot modify confidence
    'user_can_change_risk': False,       # Cannot modify risk
    'user_can_change_daily_limit': False,# Cannot modify daily limit
    'user_can_change_slots': False,      # Cannot modify slots
}

# FANG Tier - Intermediate level, moderate access
FANG_DEFAULTS = {
    'subscription_tier': 'FANG',
    'max_slots': 2,                      # Total concurrent positions
    'max_manual_slots': 2,               # Manual fire slots
    'max_auto_slots': 0,                 # AUTO fire disabled
    'max_auto_slots_separate': 0,        # Separate AUTO tracking
    'max_trades_per_day': 6,             # Daily trade limit
    'tier_max_trades_per_day': 6,        # Tier-based daily limit
    'risk_per_trade': 0.01,              # 1.0% risk per trade
    'auto_fire_min_confidence': 80.0,    # N/A - AUTO disabled
    'auto_fire_max_confidence': 89.0,    # N/A - AUTO disabled
    'auto_fire_enabled': False,          # AUTO mode locked
    'bitmode_enabled': False,            # BITMODE available but OFF by default
    'trading_enabled': True,             # Manual trading allowed
    'admin_controlled_risk': True,       # Risk locked by admin
    'admin_controlled_confidence': True, # Confidence locked by admin
    'admin_locked_slots': True,          # Slots locked by admin
    'admin_locked_daily_trades': True,   # Daily limit locked by admin
    'user_can_change_confidence': False, # Cannot modify confidence
    'user_can_change_risk': False,       # Cannot modify risk
    'user_can_change_daily_limit': False,# Cannot modify daily limit
    'user_can_change_slots': False,      # Cannot modify slots
}

# COMMANDER Tier - Premium level, full access
COMMANDER_DEFAULTS = {
    'subscription_tier': 'COMMANDER',
    'max_slots': 20,                     # Total concurrent positions
    'max_manual_slots': 10,              # Manual fire slots
    'max_auto_slots': 10,                # AUTO fire slots
    'max_auto_slots_separate': 10,       # Separate AUTO tracking
    'max_trades_per_day': 6,             # Daily trade limit (can be changed)
    'tier_max_trades_per_day': 6,        # Tier-based daily limit
    'risk_per_trade': 0.04,              # 4.0% risk per trade
    'auto_fire_min_confidence': 80.0,    # AUTO confidence range
    'auto_fire_max_confidence': 89.0,    # AUTO confidence range
    'auto_fire_enabled': True,           # AUTO mode available
    'bitmode_enabled': False,            # BITMODE available but OFF by default
    'trading_enabled': True,             # Trading fully enabled
    'admin_controlled_risk': False,      # User can modify risk
    'admin_controlled_confidence': False,# User can modify confidence
    'admin_locked_slots': False,         # User can modify slots (within limits)
    'admin_locked_daily_trades': False,  # User can modify daily limit
    'user_can_change_confidence': True,  # Can modify confidence range
    'user_can_change_risk': True,        # Can modify risk percentage
    'user_can_change_daily_limit': True, # Can modify daily trade limit
    'user_can_change_slots': False,      # Slots still tier-locked
}

# Tier mapping
TIER_DEFAULTS_MAP = {
    'NIBBLER': NIBBLER_DEFAULTS,
    'FANG': FANG_DEFAULTS,
    'COMMANDER': COMMANDER_DEFAULTS,
}

# Valid tier names
VALID_TIERS = ['NIBBLER', 'FANG', 'COMMANDER']

# Database path
DB_PATH = '/root/HydraX-v2/bitten.db'


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def get_tier_defaults(tier_name: str) -> Dict:
    """
    Get default configuration for a specific tier.

    Args:
        tier_name: Tier name (NIBBLER, FANG, COMMANDER)

    Returns:
        Dict with all tier defaults

    Raises:
        ValueError: If tier_name is invalid
    """
    tier_upper = tier_name.upper()

    if tier_upper not in VALID_TIERS:
        raise ValueError(f"Invalid tier: {tier_name}. Must be one of {VALID_TIERS}")

    return TIER_DEFAULTS_MAP[tier_upper].copy()


def get_db_connection() -> sqlite3.Connection:
    """
    Get database connection with proper configuration.

    Returns:
        SQLite connection object
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn


def initialize_user_caps(user_id: str, tier: str, user_data: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Initialize or update user with tier-based defaults.

    Args:
        user_id: User ID (Telegram ID)
        tier: Tier name (NIBBLER, FANG, COMMANDER)
        user_data: Optional dict with additional user data (gamer_tag, email, etc.)

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        tier_upper = tier.upper()
        if tier_upper not in VALID_TIERS:
            return False, f"Invalid tier: {tier}. Must be one of {VALID_TIERS}"

        defaults = get_tier_defaults(tier_upper)

        # Merge with user_data if provided
        if user_data:
            defaults.update(user_data)

        # Add metadata
        defaults['user_id'] = user_id
        defaults['telegram_id'] = user_id
        defaults['updated_at'] = datetime.utcnow().isoformat()
        defaults['subscription_start_date'] = datetime.utcnow().isoformat()
        defaults['subscription_status'] = 'ACTIVE'

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT user_id FROM user_fire_modes WHERE user_id = ?", (user_id,))
        user_exists = cursor.fetchone() is not None

        if user_exists:
            # Update existing user with tier defaults
            update_fields = []
            update_values = []

            for key, value in defaults.items():
                if key != 'user_id':  # Don't update primary key
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)

            update_values.append(user_id)  # For WHERE clause

            update_query = f"""
                UPDATE user_fire_modes
                SET {', '.join(update_fields)}
                WHERE user_id = ?
            """

            cursor.execute(update_query, update_values)
            conn.commit()
            conn.close()

            return True, f"User {user_id} updated to {tier_upper} tier defaults"

        else:
            # Insert new user with tier defaults
            columns = list(defaults.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = [defaults[col] for col in columns]

            insert_query = f"""
                INSERT INTO user_fire_modes ({', '.join(columns)})
                VALUES ({placeholders})
            """

            cursor.execute(insert_query, values)
            conn.commit()
            conn.close()

            return True, f"User {user_id} initialized with {tier_upper} tier defaults"

    except Exception as e:
        return False, f"Error initializing user caps: {str(e)}"


def upgrade_user_tier(user_id: str, new_tier: str, preserve_custom_settings: bool = False) -> Tuple[bool, str]:
    """
    Upgrade user to a new tier and update all capabilities.

    Args:
        user_id: User ID (Telegram ID)
        new_tier: New tier name (NIBBLER, FANG, COMMANDER)
        preserve_custom_settings: If True, preserve user's custom settings where allowed

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        new_tier_upper = new_tier.upper()
        if new_tier_upper not in VALID_TIERS:
            return False, f"Invalid tier: {new_tier}. Must be one of {VALID_TIERS}"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get current user data
        cursor.execute("SELECT * FROM user_fire_modes WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return False, f"User {user_id} not found. Use initialize_user_caps() first."

        current_data = dict(user_row)
        old_tier = current_data.get('subscription_tier', 'NIBBLER')

        # Get new tier defaults
        new_defaults = get_tier_defaults(new_tier_upper)

        # Prepare update data
        update_data = new_defaults.copy()

        # Preserve custom settings if requested and allowed by new tier
        if preserve_custom_settings:
            # Only preserve settings that new tier allows user to change
            if new_defaults.get('user_can_change_risk'):
                if 'risk_per_trade' in current_data:
                    update_data['risk_per_trade'] = current_data['risk_per_trade']

            if new_defaults.get('user_can_change_confidence'):
                if 'auto_fire_min_confidence' in current_data:
                    update_data['auto_fire_min_confidence'] = current_data['auto_fire_min_confidence']
                if 'auto_fire_max_confidence' in current_data:
                    update_data['auto_fire_max_confidence'] = current_data['auto_fire_max_confidence']

            if new_defaults.get('user_can_change_daily_limit'):
                if 'max_trades_per_day' in current_data:
                    update_data['max_trades_per_day'] = current_data['max_trades_per_day']

        # Update metadata
        update_data['subscription_tier'] = new_tier_upper
        update_data['updated_at'] = datetime.utcnow().isoformat()
        update_data['subscription_start_date'] = datetime.utcnow().isoformat()

        # Preserve non-tier fields
        preserve_fields = [
            'gamer_tag', 'first_name', 'last_name', 'email', 'telegram_username',
            'referral_code', 'referred_by_user_id', 'account_creation_date',
            'total_trades_fired', 'total_wins', 'total_losses', 'total_pips_gained',
            'total_profit_usd', 'best_winning_streak', 'current_winning_streak',
            'broker_name', 'account_number', 'account_currency', 'account_leverage',
            'account_balance', 'account_equity', 'war_room_visits', 'telegram_messages_sent'
        ]

        for field in preserve_fields:
            if field in current_data and current_data[field] is not None:
                update_data[field] = current_data[field]

        # Build UPDATE query
        update_fields = []
        update_values = []

        for key, value in update_data.items():
            update_fields.append(f"{key} = ?")
            update_values.append(value)

        update_values.append(user_id)  # For WHERE clause

        update_query = f"""
            UPDATE user_fire_modes
            SET {', '.join(update_fields)}
            WHERE user_id = ?
        """

        cursor.execute(update_query, update_values)
        conn.commit()
        conn.close()

        # Build detailed response message
        changes = []
        changes.append(f"Tier: {old_tier} → {new_tier_upper}")
        changes.append(f"Max Slots: {current_data.get('max_slots', 1)} → {new_defaults['max_slots']}")
        changes.append(f"AUTO Slots: {current_data.get('max_auto_slots', 0)} → {new_defaults['max_auto_slots']}")
        changes.append(f"Risk: {current_data.get('risk_per_trade', 0.005)*100:.1f}% → {new_defaults['risk_per_trade']*100:.1f}%")
        changes.append(f"Daily Limit: {current_data.get('max_trades_per_day', 6)} → {new_defaults['max_trades_per_day']}")

        message = f"User {user_id} upgraded successfully!\n" + "\n".join(changes)

        return True, message

    except Exception as e:
        return False, f"Error upgrading user tier: {str(e)}"


def get_user_tier_info(user_id: str) -> Tuple[bool, Optional[Dict]]:
    """
    Get user's current tier configuration and limits.

    Args:
        user_id: User ID (Telegram ID)

    Returns:
        Tuple of (success: bool, data: Optional[Dict])
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_fire_modes WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        conn.close()

        if not user_row:
            return False, None

        user_data = dict(user_row)

        # Build tier info summary
        tier_info = {
            'user_id': user_id,
            'tier': user_data.get('subscription_tier', 'NIBBLER'),
            'limits': {
                'max_slots': user_data.get('max_slots', 1),
                'max_manual_slots': user_data.get('max_manual_slots', 1),
                'max_auto_slots': user_data.get('max_auto_slots', 0),
                'max_trades_per_day': user_data.get('max_trades_per_day', 6),
                'risk_per_trade': user_data.get('risk_per_trade', 0.005),
            },
            'current_usage': {
                'slots_in_use': user_data.get('slots_in_use', 0),
                'auto_slots_in_use': user_data.get('auto_slots_in_use', 0),
                'manual_slots_in_use': user_data.get('manual_slots_in_use', 0),
                'trades_used_today': user_data.get('trades_used_today', 0),
            },
            'features': {
                'auto_fire_enabled': user_data.get('auto_fire_enabled', False),
                'bitmode_enabled': user_data.get('bitmode_enabled', False),
                'trading_enabled': user_data.get('trading_enabled', True),
            },
            'permissions': {
                'can_change_risk': user_data.get('user_can_change_risk', False),
                'can_change_confidence': user_data.get('user_can_change_confidence', False),
                'can_change_daily_limit': user_data.get('user_can_change_daily_limit', False),
                'can_change_slots': user_data.get('user_can_change_slots', False),
            },
            'admin_locks': {
                'risk_locked': user_data.get('admin_controlled_risk', True),
                'confidence_locked': user_data.get('admin_controlled_confidence', True),
                'slots_locked': user_data.get('admin_locked_slots', True),
                'daily_trades_locked': user_data.get('admin_locked_daily_trades', True),
            }
        }

        return True, tier_info

    except Exception as e:
        return False, {'error': str(e)}


def validate_tier_limits(user_id: str, requested_action: str, **kwargs) -> Tuple[bool, str]:
    """
    Validate if user can perform requested action based on tier limits.

    Args:
        user_id: User ID (Telegram ID)
        requested_action: Action to validate ('fire', 'change_risk', 'change_slots', etc.)
        **kwargs: Additional parameters for validation

    Returns:
        Tuple of (allowed: bool, reason: str)
    """
    success, tier_info = get_user_tier_info(user_id)

    if not success:
        return False, "User not found or tier info unavailable"

    if requested_action == 'fire':
        # Check if user can fire another trade
        if tier_info['current_usage']['trades_used_today'] >= tier_info['limits']['max_trades_per_day']:
            return False, f"Daily trade limit reached ({tier_info['limits']['max_trades_per_day']})"

        if tier_info['current_usage']['slots_in_use'] >= tier_info['limits']['max_slots']:
            return False, f"Maximum concurrent positions reached ({tier_info['limits']['max_slots']})"

        if not tier_info['features']['trading_enabled']:
            return False, "Trading is currently disabled for your account"

        return True, "Fire command allowed"

    elif requested_action == 'change_risk':
        if not tier_info['permissions']['can_change_risk']:
            return False, f"Risk modification locked for {tier_info['tier']} tier"

        new_risk = kwargs.get('new_risk', tier_info['limits']['risk_per_trade'])
        if new_risk > tier_info['limits']['risk_per_trade']:
            return False, f"Risk cannot exceed tier limit of {tier_info['limits']['risk_per_trade']*100:.1f}%"

        return True, "Risk change allowed"

    elif requested_action == 'change_daily_limit':
        if not tier_info['permissions']['can_change_daily_limit']:
            return False, f"Daily limit modification locked for {tier_info['tier']} tier"

        return True, "Daily limit change allowed"

    elif requested_action == 'enable_auto_fire':
        if tier_info['limits']['max_auto_slots'] == 0:
            return False, f"AUTO fire not available for {tier_info['tier']} tier"

        return True, "AUTO fire available"

    elif requested_action == 'enable_bitmode':
        tier = tier_info['tier']
        if tier not in ['FANG', 'COMMANDER']:
            return False, f"BITMODE not available for {tier} tier"

        return True, "BITMODE available"

    else:
        return False, f"Unknown action: {requested_action}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_tier_comparison() -> Dict:
    """
    Get comparison of all tiers for display purposes.

    Returns:
        Dict with tier comparison data
    """
    comparison = {}

    for tier_name in VALID_TIERS:
        defaults = get_tier_defaults(tier_name)
        comparison[tier_name] = {
            'max_slots': defaults['max_slots'],
            'max_auto_slots': defaults['max_auto_slots'],
            'max_trades_per_day': defaults['max_trades_per_day'],
            'risk_per_trade_pct': f"{defaults['risk_per_trade']*100:.1f}%",
            'auto_fire': 'Yes' if defaults['auto_fire_enabled'] else 'No',
            'bitmode': 'Available' if tier_name in ['FANG', 'COMMANDER'] else 'No',
            'can_customize': 'Yes' if tier_name == 'COMMANDER' else 'No'
        }

    return comparison


def reset_daily_usage(user_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Reset daily usage counters for user(s).

    Args:
        user_id: Optional user ID. If None, resets all users.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        current_date = datetime.utcnow().date().isoformat()

        if user_id:
            cursor.execute("""
                UPDATE user_fire_modes
                SET trades_used_today = 0,
                    daily_auto_fires_used = 0,
                    last_daily_reset = ?
                WHERE user_id = ?
            """, (current_date, user_id))

            affected = cursor.rowcount
            conn.commit()
            conn.close()

            return True, f"Daily usage reset for user {user_id}"

        else:
            cursor.execute("""
                UPDATE user_fire_modes
                SET trades_used_today = 0,
                    daily_auto_fires_used = 0,
                    last_daily_reset = ?
            """, (current_date,))

            affected = cursor.rowcount
            conn.commit()
            conn.close()

            return True, f"Daily usage reset for {affected} users"

    except Exception as e:
        return False, f"Error resetting daily usage: {str(e)}"


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'NIBBLER_DEFAULTS',
    'FANG_DEFAULTS',
    'COMMANDER_DEFAULTS',
    'VALID_TIERS',
    'get_tier_defaults',
    'initialize_user_caps',
    'upgrade_user_tier',
    'get_user_tier_info',
    'validate_tier_limits',
    'get_tier_comparison',
    'reset_daily_usage',
]
