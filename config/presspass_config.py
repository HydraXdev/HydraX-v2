#!/usr/bin/env python3
"""
Press Pass Configuration
Central configuration for Press Pass system settings
"""

from datetime import timedelta

# Account Management Settings
PRESS_PASS_CONFIG = {
    # Trial Duration
    "trial_duration_days": 7,
    
    # Account Vault Settings
    "vault_file": "/root/HydraX-v2/config/presspass_account_vault.json",
    "min_available_accounts": 5,  # Alert when available accounts drop below this
    "max_concurrent_users": 50,   # Maximum simultaneous Press Pass users
    
    # Bridge Settings
    "bridge_base_port": 9100,     # Starting port for Press Pass bridges
    "bridge_port_range": 100,     # Port range (9100-9199)
    "bridge_script": "/root/HydraX-v2/bulletproof_agents/primary_agent_mt5_enhanced.py",
    
    # Terminal Settings
    "base_terminal_path": "/opt/mt5/base_terminal",
    "user_terminals_path": "/opt/mt5/user_terminals",
    "terminal_executable_paths": [
        "/opt/mt5/terminal64.exe",
        "/usr/local/bin/mt5/terminal64.exe", 
        "/opt/MetaTrader5/terminal64.exe"
    ],
    
    # Maintenance Settings
    "daily_maintenance_time": "03:00",  # 3:00 AM
    "hourly_health_checks": True,
    "cleanup_orphaned_processes": True,
    "process_tracking_file": "/root/HydraX-v2/data/presspass_processes.json",
    
    # Logging Settings
    "log_directory": "/root/HydraX-v2/logs",
    "maintenance_log": "/root/HydraX-v2/logs/presspass_maintenance.log",
    "rotation_log": "/root/HydraX-v2/logs/presspass_rotation.log",
    
    # Account Pool Distribution
    "broker_distribution": {
        "MetaQuotes-Demo": 0.4,  # 40% MetaQuotes accounts
        "Coinexx-Demo": 0.3,     # 30% Coinexx accounts  
        "ICMarkets-Demo": 0.3    # 30% ICMarkets accounts
    },
    
    # 🚨 PROTECTED ACCOUNTS - DO NOT USE FOR PRESS PASS
    "reserved_accounts": [
        100007013135,  # MASTER CLONE TEMPLATE - PERMANENTLY RESERVED
        5038318494,    # ENGINE DATA FEED - PERMANENTLY RESERVED
    ],
    
    # Security Settings
    "max_login_attempts": 3,
    "account_lockout_duration": timedelta(hours=1),
    "bridge_connection_timeout": 30,  # seconds
    
    # Performance Settings
    "process_cleanup_interval": 3600,  # 1 hour
    "health_check_interval": 3600,     # 1 hour
    "account_expiry_check_interval": 300,  # 5 minutes
    
    # Notification Settings
    "low_availability_threshold": 5,   # Alert when < 5 accounts available
    "critical_availability_threshold": 2,  # Critical alert when < 2 accounts
    
    # Trading Settings for Press Pass Users
    "default_leverage": 100,
    "default_balance": 10000.0,
    "default_currency": "USD",
    "max_lot_size": 0.1,  # Maximum lot size for Press Pass trades
    "max_trades_per_day": 10,  # Maximum trades per day for Press Pass users
    
    # Auto-upgrade Settings
    "upgrade_prompts": {
        "day_3": "You're halfway through your Press Pass trial! Upgrade to keep trading.",
        "day_6": "Your Press Pass expires tomorrow! Upgrade now to continue.",
        "day_7": "Your Press Pass has expired. Upgrade to continue trading with BITTEN."
    }
}

# Broker-Specific Settings
BROKER_SETTINGS = {
    "MetaQuotes-Demo": {
        "name": "MetaQuotes Demo",
        "server": "MetaQuotes-Demo",
        "leverage_options": [100, 200, 500],
        "default_leverage": 100,
        "currency": "USD",
        "balance": 10000.0,
        "min_deposit": 0,
        "max_demo_accounts": 20
    },
    "Coinexx-Demo": {
        "name": "Coinexx Demo",
        "server": "Coinexx-Demo", 
        "leverage_options": [100, 200],
        "default_leverage": 100,
        "currency": "USD",
        "balance": 10000.0,
        "min_deposit": 0,
        "max_demo_accounts": 15
    },
    "ICMarkets-Demo": {
        "name": "ICMarkets Demo",
        "server": "ICMarkets-Demo",
        "leverage_options": [100, 200, 500],
        "default_leverage": 500,
        "currency": "USD", 
        "balance": 10000.0,
        "min_deposit": 0,
        "max_demo_accounts": 15
    }
}

# Press Pass User Tier Configuration
PRESS_PASS_TIER = {
    "name": "PRESS_PASS",
    "display_name": "Press Pass",
    "duration_days": 7,
    "price": 0.00,  # Free trial
    "features": {
        "signals_per_day": 20,
        "fire_modes": ["SELECT"],  # Only SELECT FIRE mode
        "max_concurrent_trades": 1,
        "lot_size_limit": 0.1,
        "voice_personalities": True,
        "adaptive_personality": True,
        "real_time_signals": True,
        "telegram_alerts": True,
        "hud_interface": True,
        "performance_tracking": True,
        "auto_fire": False,  # No AUTO mode
        "premium_signals": False,
        "priority_support": False
    },
    "restrictions": {
        "demo_only": True,
        "max_daily_trades": 10,
        "weekend_trading": False,
        "bridge_priority": "low"
    }
}

# System Messages
PRESS_PASS_MESSAGES = {
    "welcome": """
🎫 **PRESS PASS ACTIVATED!**

Welcome to your 7-day free trial of BITTEN!

📊 **Your Demo Account:**
• Account: {login}
• Server: {server} 
• Broker: {broker}
• Balance: ${balance:,.0f} {currency}
• Leverage: 1:{leverage}

🎯 **What's Next:**
• Receive BITTEN signals via Telegram
• Click mission links to view trade details  
• Execute trades with one click
• Track your performance in real-time

• Use /fire to execute current missions
• Use /mode to configure firing modes
• Use /presspass to check your status

🚀 **Your BITTEN journey starts now!**
""",
    
    "status_active": """
🎫 **PRESS PASS ACTIVE**

📊 Account: {login}
🏢 Broker: {broker} ({server})
⏰ Time Remaining: {days_remaining}d {hours_remaining}h
🔗 Bridge: {bridge_status}

Your Press Pass is active! Start trading with BITTEN signals.
""",
    
    "expiry_warning_day_6": """
⚠️ **PRESS PASS EXPIRES TOMORROW!**

Your 7-day free trial ends tomorrow. Upgrade now to continue trading with BITTEN:

🔥 **NIBBLER** - $39/month
• Unlimited signals
• SELECT FIRE mode
• Voice personalities
• Priority support

Upgrade: /upgrade
""",
    
    "expired": """
❌ **PRESS PASS EXPIRED**

Your 7-day free trial has ended. Thank you for trying BITTEN!

🚀 **Ready to continue?** Upgrade to a paid tier:

🔥 **NIBBLER** - $39/month  
🐺 **FANG** - $89/month
👑 **COMMANDER** - $189/month

Upgrade: /upgrade
""",
    
    "vault_full": """
❌ **PRESS PASS TEMPORARILY UNAVAILABLE**

All demo accounts are currently assigned. Please try again in a few hours.

🔔 **Get notified:** We'll send you a message when Press Pass becomes available again.
""",
    
    "system_error": """
❌ **PRESS PASS SYSTEM ERROR**

We're experiencing technical difficulties. Please try again in a few minutes.

If the issue persists, contact support: @BITTEN_Support
"""
}

def get_config():
    """Get the complete Press Pass configuration"""
    return PRESS_PASS_CONFIG

def get_broker_settings(broker_name: str = None):
    """Get broker settings for a specific broker or all brokers"""
    if broker_name:
        return BROKER_SETTINGS.get(broker_name)
    return BROKER_SETTINGS

def get_press_pass_tier():
    """Get Press Pass tier configuration"""
    return PRESS_PASS_TIER

def get_message(message_key: str):
    """Get a specific Press Pass message template"""
    return PRESS_PASS_MESSAGES.get(message_key, "")

# Validation functions
def validate_config():
    """Validate Press Pass configuration"""
    errors = []
    
    # Check required directories
    import os
    required_dirs = [
        PRESS_PASS_CONFIG["log_directory"],
        os.path.dirname(PRESS_PASS_CONFIG["vault_file"]),
        os.path.dirname(PRESS_PASS_CONFIG["process_tracking_file"])
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {directory}: {e}")
    
    # Check broker distribution sums to 1.0
    total_distribution = sum(PRESS_PASS_CONFIG["broker_distribution"].values())
    if abs(total_distribution - 1.0) > 0.001:
        errors.append(f"Broker distribution sums to {total_distribution}, should be 1.0")
    
    # Check port range
    if PRESS_PASS_CONFIG["bridge_port_range"] < PRESS_PASS_CONFIG["max_concurrent_users"]:
        errors.append("Bridge port range is smaller than max concurrent users")
    
    return errors

if __name__ == "__main__":
    # Validate configuration
    errors = validate_config()
    
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Press Pass configuration is valid")
        
    # Print summary
    config = get_config()
    print(f"\n📋 Press Pass Configuration Summary:")
    print(f"  - Trial Duration: {config['trial_duration_days']} days")
    print(f"  - Max Concurrent Users: {config['max_concurrent_users']}")
    print(f"  - Bridge Port Range: {config['bridge_base_port']}-{config['bridge_base_port'] + config['bridge_port_range']}")
    print(f"  - Available Brokers: {len(BROKER_SETTINGS)}")
    print(f"  - Maintenance Time: {config['daily_maintenance_time']}")