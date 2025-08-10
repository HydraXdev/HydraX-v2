#!/usr/bin/env python3
"""
🤖 BITTEN DUAL BOT LAUNCHER
Starts both bots in parallel:
1. Trading Bot (signals, tactics, execution)
2. Voice/Personality Bot (ATHENA, DRILL, NEXUS, DOC, OBSERVER)
"""

import os
import sys
import subprocess
import logging
import signal
import time
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DualBotLauncher')

def check_bot_running(bot_name):
    """Check if specific bot is running"""
    try:
        result = subprocess.run(['pgrep', '-f', bot_name], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
    except Exception as e:
        logger.error(f"Error checking {bot_name} status: {e}")
        return []

def kill_existing_bots():
    """Kill any existing bot processes"""
    bots_to_kill = [
        'bitten_production_bot.py',
        'bitten_voice_personality_bot.py'
    ]
    
    for bot_name in bots_to_kill:
        try:
            pids = check_bot_running(bot_name)
            for pid in pids:
                if pid.strip():
                    logger.info(f"Killing existing {bot_name} process: {pid}")
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(2)
        except Exception as e:
            logger.error(f"Error killing {bot_name}: {e}")

def start_trading_bot():
    """Start the trading bot"""
    try:
        logger.info("🎯 Starting Trading Bot (signals, tactics, execution)...")
        
        os.chdir('/root/HydraX-v2')
        
        process = subprocess.Popen([
            sys.executable, 'bitten_production_bot.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        logger.info(f"✅ Trading Bot started with PID: {process.pid}")
        logger.info(f"📱 Token: 7854827710:AAE9kCptkoSl8lmQwmX940UMqFWOb3TmTI0")
        return process
        
    except Exception as e:
        logger.error(f"❌ Failed to start trading bot: {e}")
        return None

def start_voice_bot():
    """Start the voice/personality bot"""
    try:
        logger.info("🎭 Starting Voice/Personality Bot (ATHENA, DRILL, NEXUS, DOC, OBSERVER)...")
        
        os.chdir('/root/HydraX-v2')
        
        process = subprocess.Popen([
            sys.executable, 'bitten_voice_personality_bot.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        logger.info(f"✅ Voice Bot started with PID: {process.pid}")
        logger.info(f"📱 Token: 8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k")
        return process
        
    except Exception as e:
        logger.error(f"❌ Failed to start voice bot: {e}")
        return None

def monitor_bots(trading_process, voice_process):
    """Monitor both bot processes"""
    logger.info("🔍 Monitoring both bots...")
    
    while True:
        try:
            # Check if processes are still running
            trading_running = trading_process and trading_process.poll() is None
            voice_running = voice_process and voice_process.poll() is None
            
            if not trading_running:
                logger.error("❌ Trading bot stopped!")
                
            if not voice_running:
                logger.error("❌ Voice bot stopped!")
                
            if not trading_running and not voice_running:
                logger.error("❌ Both bots stopped! Exiting...")
                break
                
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            logger.info("🛑 Stopping both bots...")
            if trading_process:
                trading_process.terminate()
            if voice_process:
                voice_process.terminate()
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(10)

def main():
    """Main launcher function"""
    print("🚀 BITTEN DUAL BOT LAUNCHER")
    print("=" * 60)
    print("🎯 Trading Bot: Signals, tactics, execution")
    print("🎭 Voice Bot: ATHENA, DRILL, NEXUS, DOC, OBSERVER personalities")
    print("=" * 60)
    
    # Check for existing bots
    existing_trading = check_bot_running('bitten_production_bot.py')
    existing_voice = check_bot_running('bitten_voice_personality_bot.py')
    
    if existing_trading or existing_voice:
        print(f"⚠️ Found existing bot processes")
        response = input("Kill existing bots and restart? (y/n): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            return
        
        kill_existing_bots()
        time.sleep(3)
    
    # Start both bots
    trading_process = start_trading_bot()
    time.sleep(2)  # Small delay between starts
    voice_process = start_voice_bot()
    
    if not trading_process and not voice_process:
        print("❌ Failed to start both bots")
        return
    elif not trading_process:
        print("❌ Failed to start trading bot")
        return
    elif not voice_process:
        print("❌ Failed to start voice bot")
        return
    
    print("")
    print("✅ BOTH BOTS STARTED SUCCESSFULLY!")
    print("")
    print("🎯 TRADING BOT (7854827710...)")
    print("  📊 Handles: Signals, tactics, execution, drill reports")
    print("  📝 Log: /root/HydraX-v2/bitten_production_bot.log")
    print("")
    print("🎭 VOICE BOT (8103700393...)")
    print("  🏛️ ATHENA - Strategic Commander")
    print("  🪖 DRILL - Motivational Sergeant") 
    print("  📡 NEXUS - Recruiter Protocol")
    print("  🩺 DOC - Risk Manager")
    print("  👁️ OBSERVER - Market Watcher")
    print("  📝 Log: /root/HydraX-v2/bitten_voice_personality_bot.log")
    print("")
    print("📋 Voice Bot Commands:")
    print("  /personalities - Choose personality")
    print("  /athena - Activate ATHENA")
    print("  /drill - Activate Drill Sergeant")
    print("  /nexus - Activate NEXUS")
    print("  /doc - Activate DOC")
    print("  /observer - Activate OBSERVER")
    print("")
    print("🚀 BITTEN DUAL BOT SYSTEM OPERATIONAL!")
    print("Press Ctrl+C to stop both bots")
    
    # Monitor both bots
    monitor_bots(trading_process, voice_process)

if __name__ == "__main__":
    main()