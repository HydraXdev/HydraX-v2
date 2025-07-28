#!/usr/bin/env python3
"""
🤖 BITTEN PRODUCTION BOT - SINGLE POINT LAUNCHER
Starts the consolidated production bot with all integrated systems
"""

import os
import sys
import subprocess
import logging
import signal
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BotLauncher')

def check_bot_running():
    """Check if bot is already running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'bitten_production_bot.py'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
    except Exception as e:
        logger.error(f"Error checking bot status: {e}")
        return []

def kill_existing_bots():
    """Kill any existing bot processes"""
    try:
        pids = check_bot_running()
        for pid in pids:
            if pid.strip():
                logger.info(f"Killing existing bot process: {pid}")
                os.kill(int(pid), signal.SIGTERM)
                time.sleep(2)
        
        # Force kill if still running
        remaining = check_bot_running()
        for pid in remaining:
            if pid.strip():
                logger.info(f"Force killing bot process: {pid}")
                os.kill(int(pid), signal.SIGKILL)
                
    except Exception as e:
        logger.error(f"Error killing existing bots: {e}")

def start_production_bot():
    """Start the main production bot"""
    try:
        logger.info("🤖 Starting BITTEN Production Bot...")
        
        # Change to correct directory
        os.chdir('/root/HydraX-v2')
        
        # Start the bot
        process = subprocess.Popen([
            sys.executable, 'bitten_production_bot.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        logger.info(f"✅ Bot started with PID: {process.pid}")
        return process
        
    except Exception as e:
        logger.error(f"❌ Failed to start production bot: {e}")
        return None

def main():
    """Main launcher function"""
    print("🚀 BITTEN PRODUCTION BOT LAUNCHER")
    print("=" * 50)
    
    # Check for existing bots
    existing = check_bot_running()
    if existing:
        print(f"⚠️ Found {len(existing)} existing bot process(es)")
        response = input("Kill existing bots and restart? (y/n): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            return
        
        kill_existing_bots()
        time.sleep(3)
    
    # Start production bot
    process = start_production_bot()
    if not process:
        print("❌ Failed to start bot")
        return
    
    print("✅ Production bot started successfully!")
    print(f"📊 PID: {process.pid}")
    print(f"📝 Log file: /root/HydraX-v2/bitten_production_bot.log")
    print("")
    print("🎯 Bot Features Active:")
    print("  ✅ Tactical strategy selection")
    print("  ✅ Daily drill reports")
    print("  ✅ Real trade execution")
    print("  ✅ Zero simulation integration")
    print("  ✅ Achievement system")
    print("")
    print("📋 Available Commands:")
    print("  /tactical - Select daily strategy")
    print("  /drill - Get drill report") 
    print("  /fire - Execute mission")
    print("  /status - System status")
    print("")
    print("🚀 BITTEN Production Bot is OPERATIONAL!")

if __name__ == "__main__":
    main()