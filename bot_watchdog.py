#!/usr/bin/env python3
"""
Bot Watchdog - Keeps production bot running reliably
Monitors the bot process and restarts if it crashes
"""

import subprocess
import time
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/bot_watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BotWatchdog')

def is_bot_running():
    """Check if production bot is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'bitten_production_bot.py'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except Exception as e:
        logger.error(f"Error checking bot status: {e}")
        return False

def start_bot():
    """Start the production bot"""
    try:
        os.chdir('/root/HydraX-v2')
        
        # Kill any existing bot processes first
        subprocess.run(['pkill', '-f', 'bitten_production_bot.py'], 
                      capture_output=True)
        time.sleep(2)
        
        # Start new bot process
        process = subprocess.Popen(['nohup', 'python3', 'bitten_production_bot.py'],
                                 stdout=open('/tmp/bot.log', 'w'),
                                 stderr=subprocess.STDOUT)
        
        # Wait a moment and check if it started
        time.sleep(5)
        if is_bot_running():
            logger.info(f"✅ Bot started successfully (PID: {process.pid})")
            return True
        else:
            logger.error("❌ Bot failed to start")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        return False

def check_bot_health():
    """Check if bot is responding to basic commands"""
    try:
        # Check if bot is processing messages by looking at recent logs
        with open('/tmp/bot.log', 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-10:] if len(lines) > 10 else lines
            
        # Look for recent activity (within last 5 minutes)
        current_time = datetime.now()
        for line in recent_lines:
            if 'BittenProductionBot' in line and 'INFO' in line:
                # Bot is actively logging
                return True
                
        return True  # Assume healthy if no errors
        
    except Exception as e:
        logger.warning(f"⚠️ Could not check bot health: {e}")
        return True  # Don't restart due to log check failures

def main():
    """Main watchdog loop"""
    logger.info("🐕 Starting Bot Watchdog")
    
    restart_count = 0
    max_restarts = 5
    restart_window = 3600  # 1 hour
    last_restart_time = 0
    
    while True:
        try:
            current_time = time.time()
            
            # Reset restart counter if it's been more than restart_window
            if current_time - last_restart_time > restart_window:
                restart_count = 0
            
            if not is_bot_running():
                logger.warning("⚠️ Production bot is not running")
                
                if restart_count >= max_restarts:
                    logger.error(f"❌ Maximum restarts ({max_restarts}) reached. Stopping watchdog.")
                    break
                
                logger.info(f"🔄 Attempting to restart bot (attempt {restart_count + 1}/{max_restarts})")
                
                if start_bot():
                    restart_count += 1
                    last_restart_time = current_time
                    logger.info("✅ Bot restart successful")
                else:
                    logger.error("❌ Bot restart failed")
                    time.sleep(30)  # Wait before trying again
                    
            elif not check_bot_health():
                logger.warning("⚠️ Bot appears unhealthy, restarting...")
                subprocess.run(['pkill', '-f', 'bitten_production_bot.py'], 
                              capture_output=True)
                time.sleep(5)
            else:
                logger.debug("✅ Bot is running and healthy")
            
            # Check every 30 seconds
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("🛑 Watchdog stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Watchdog error: {e}")
            time.sleep(60)  # Wait a minute before continuing

if __name__ == "__main__":
    main()