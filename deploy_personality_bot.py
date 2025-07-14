#!/usr/bin/env python3
"""
DEPLOY PERSONALITY BOT - Production deployment script
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PersonalityBotDeployment')

def check_dependencies():
    """Check if all required dependencies are available"""
    required_packages = [
        'telebot',
        'pyTelegramBotAPI',
        'requests',
        'sqlite3'  # Built-in
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            elif package == 'telebot':
                import telebot
            elif package == 'pyTelegramBotAPI':
                import telebot  # Same as telebot
            else:
                __import__(package)
            logger.info(f"✅ {package} available")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"❌ {package} missing")
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    logger.info("Installing required packages...")
    
    packages_to_install = [
        'pyTelegramBotAPI',
        'requests'
    ]
    
    for package in packages_to_install:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            logger.info(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def setup_configuration():
    """Setup configuration for personality bot"""
    config_path = Path("/root/HydraX-v2/config/personality_bot_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = {
        "bot_token": "YOUR_BOT_TOKEN_HERE",
        "personality_systems": {
            "enable_full_system": True,
            "fallback_mode": True,
            "voice_personalities": [
                "DRILL_SERGEANT",
                "DOC_AEGIS", 
                "NEXUS",
                "OVERWATCH",
                "BIT"
            ]
        },
        "xp_system": {
            "base_xp_values": {
                "onboarding_complete": 50,
                "trade_request": 10,
                "trade_execution": 25,
                "education_engagement": 15,
                "achievement_unlock": 100,
                "persona_evolution": 200
            },
            "persona_multipliers": {
                "BRUTE": {"trade_request": 1.3, "quick_action": 1.2},
                "SCHOLAR": {"education_engagement": 1.5, "patience": 1.4},
                "PHANTOM": {"stealth_profit": 1.6, "risk_management": 1.3},
                "WARDEN": {"discipline": 1.3, "rule_following": 1.4},
                "FERAL": {"chaos_profit": 1.8, "instinct_trade": 1.2},
                "DEFAULT": {"consistency": 1.2, "balanced": 1.1}
            }
        },
        "persona_evolution": {
            "check_interval": 10,
            "evolution_triggers": {
                "risk_tolerance_shift": 0.3,
                "education_engagement_shift": 0.4,
                "trading_frequency_change": 2.0
            }
        },
        "database": {
            "personality_bot_db": "/root/HydraX-v2/bitten/data/personality_bot.db",
            "existing_xp_db": "/root/HydraX-v2/bitten/data/xp_system.db",
            "existing_persona_file": "/root/HydraX-v2/bitten/data/user_persona.json"
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✅ Configuration created at {config_path}")
    return config_path

def create_startup_script():
    """Create startup script for personality bot"""
    startup_script = """#!/bin/bash
# BITTEN Personality Bot Startup Script

export PYTHONPATH="/root/HydraX-v2:$PYTHONPATH"

cd /root/HydraX-v2

echo "🤖 Starting BITTEN Personality Bot..."
echo "Time: $(date)"
echo "Python version: $(python3 --version)"
echo "Working directory: $(pwd)"

# Check if bot token is set
if [ -z "$BITTEN_BOT_TOKEN" ]; then
    echo "❌ Error: BITTEN_BOT_TOKEN environment variable not set"
    echo "Please set your Telegram bot token:"
    echo "export BITTEN_BOT_TOKEN='your_token_here'"
    exit 1
fi

# Start the personality bot
python3 bitten_personality_bot.py

echo "Bot stopped at $(date)"
"""
    
    script_path = Path("/root/HydraX-v2/start_personality_bot.sh")
    with open(script_path, 'w') as f:
        f.write(startup_script)
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    logger.info(f"✅ Startup script created at {script_path}")
    return script_path

def create_systemd_service():
    """Create systemd service for personality bot"""
    service_content = """[Unit]
Description=BITTEN Personality Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/HydraX-v2
Environment=PYTHONPATH=/root/HydraX-v2
EnvironmentFile=-/root/HydraX-v2/.env
ExecStart=/usr/bin/python3 /root/HydraX-v2/bitten_personality_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    service_path = Path("/root/HydraX-v2/bitten-personality-bot.service")
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    logger.info(f"✅ Systemd service created at {service_path}")
    logger.info("To install the service:")
    logger.info("  sudo cp bitten-personality-bot.service /etc/systemd/system/")
    logger.info("  sudo systemctl daemon-reload")
    logger.info("  sudo systemctl enable bitten-personality-bot")
    logger.info("  sudo systemctl start bitten-personality-bot")
    
    return service_path

def create_environment_template():
    """Create environment template file"""
    env_template = """# BITTEN Personality Bot Environment Variables

# Telegram Bot Token (REQUIRED)
# Get this from @BotFather on Telegram
BITTEN_BOT_TOKEN=your_telegram_bot_token_here

# Database paths (optional - defaults will be used)
# PERSONALITY_BOT_DB=/root/HydraX-v2/bitten/data/personality_bot.db
# EXISTING_XP_DB=/root/HydraX-v2/bitten/data/xp_system.db

# Logging level (optional)
# LOG_LEVEL=INFO

# Development mode (optional)
# DEV_MODE=false
"""
    
    env_path = Path("/root/HydraX-v2/.env.template")
    with open(env_path, 'w') as f:
        f.write(env_template)
    
    logger.info(f"✅ Environment template created at {env_path}")
    logger.info("Copy .env.template to .env and set your bot token")
    
    return env_path

def verify_installation():
    """Verify that all components are properly installed"""
    checks = []
    
    # Check bot file exists
    bot_file = Path("/root/HydraX-v2/bitten_personality_bot.py")
    checks.append(("Personality bot file", bot_file.exists()))
    
    # Check bridge file exists
    bridge_file = Path("/root/HydraX-v2/personality_integration_bridge.py")
    checks.append(("Integration bridge file", bridge_file.exists()))
    
    # Check config file exists
    config_file = Path("/root/HydraX-v2/config/personality_bot_config.json")
    checks.append(("Configuration file", config_file.exists()))
    
    # Check startup script exists
    startup_script = Path("/root/HydraX-v2/start_personality_bot.sh")
    checks.append(("Startup script", startup_script.exists()))
    
    # Check data directory exists
    data_dir = Path("/root/HydraX-v2/bitten/data")
    checks.append(("Data directory", data_dir.exists()))
    
    # Check dependencies
    missing_deps = check_dependencies()
    checks.append(("All dependencies installed", len(missing_deps) == 0))
    
    logger.info("🔍 Installation Verification:")
    all_good = True
    for check_name, status in checks:
        status_icon = "✅" if status else "❌"
        logger.info(f"  {status_icon} {check_name}")
        if not status:
            all_good = False
    
    if missing_deps:
        logger.info(f"  Missing dependencies: {', '.join(missing_deps)}")
    
    return all_good

def print_deployment_summary():
    """Print deployment summary and next steps"""
    summary = """
🤖 BITTEN PERSONALITY BOT DEPLOYMENT COMPLETE!

📁 Files Created:
  ✅ bitten_personality_bot.py - Main personality bot
  ✅ personality_integration_bridge.py - Integration bridge
  ✅ config/personality_bot_config.json - Configuration
  ✅ start_personality_bot.sh - Startup script
  ✅ bitten-personality-bot.service - Systemd service
  ✅ .env.template - Environment template

🚀 Next Steps:

1. Set your bot token:
   cp .env.template .env
   # Edit .env and set BITTEN_BOT_TOKEN

2. Test the bot:
   export BITTEN_BOT_TOKEN='your_token_here'
   python3 bitten_personality_bot.py

3. Install as service (optional):
   sudo cp bitten-personality-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable bitten-personality-bot
   sudo systemctl start bitten-personality-bot

🎯 Bot Features:
  🔥 DRILL SERGEANT - Motivation and execution
  🩺 DOC AEGIS - Risk management
  📡 NEXUS - Community connection
  🎯 OVERWATCH - Market reality
  👾 BIT - Intuitive presence

  🧬 Persona Types: BRUTE, SCHOLAR, PHANTOM, WARDEN, FERAL, DEFAULT
  🎮 XP System with persona multipliers
  🌟 Real-time persona evolution
  💬 Multi-voice coordinated responses

Ready to transform BITTEN into the most sophisticated AI trading companion ever built! 🚀
"""
    
    print(summary)

def main():
    """Main deployment function"""
    logger.info("🚀 Starting BITTEN Personality Bot deployment...")
    
    try:
        # Check and install dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            logger.info("Installing missing dependencies...")
            if not install_dependencies():
                logger.error("❌ Failed to install dependencies")
                return False
        
        # Setup configuration
        config_path = setup_configuration()
        
        # Create startup script
        startup_script = create_startup_script()
        
        # Create systemd service
        service_path = create_systemd_service()
        
        # Create environment template
        env_template = create_environment_template()
        
        # Verify installation
        if verify_installation():
            logger.info("✅ All components verified successfully")
        else:
            logger.warning("⚠️ Some components may need attention")
        
        # Print summary
        print_deployment_summary()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)