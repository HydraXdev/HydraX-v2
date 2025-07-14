#!/usr/bin/env python3
"""
BITTEN Unified Startup Script
Starts all components in the correct order with proper configuration
"""

import os
import sys
import subprocess
import asyncio
import time
from datetime import datetime

# Configuration
BOT_TOKEN = 'os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")'
CHAT_ID = 'int(os.getenv("CHAT_ID", "-1002581996861"))'
WEBAPP_PORT = 8888
WEBAPP_URL = f'http://134.199.204.67:{WEBAPP_PORT}'

def print_banner():
    """Display startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🎯 B.I.T.T.E.N. 🎯                        ║
║         Bot-Integrated Tactical Trading Engine               ║
║                   SYSTEM STARTUP                             ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"🕐 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 WebApp URL: {WEBAPP_URL}")
    print(f"💬 Telegram Chat: {CHAT_ID}")
    print("="*60)

def check_processes():
    """Check if components are already running"""
    print("\n🔍 Checking existing processes...")
    
    # Check webapp
    webapp_check = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    if 'webapp_server.py' in webapp_check.stdout:
        print("✅ WebApp already running")
    else:
        print("❌ WebApp not running")
    
    # Check signal bot
    if 'SIGNAL' in webapp_check.stdout and 'python' in webapp_check.stdout:
        print("✅ Signal bot already running")
    else:
        print("❌ Signal bot not running")

def kill_existing():
    """Kill existing processes to restart clean"""
    print("\n🛑 Stopping existing processes...")
    
    # Kill webapp
    subprocess.run(['pkill', '-f', 'webapp_server.py'], capture_output=True)
    
    # Kill signal bots
    subprocess.run(['pkill', '-f', 'SIGNALS_'], capture_output=True)
    subprocess.run(['pkill', '-f', 'START_SIGNALS'], capture_output=True)
    
    time.sleep(2)
    print("✅ Existing processes stopped")

def start_webapp():
    """Start the WebApp server"""
    print("\n🌐 Starting WebApp server...")
    
    # Create simple webapp starter that uses correct URL
    webapp_config = f'''
import os
os.environ['WEBAPP_URL'] = '{WEBAPP_URL}'
os.environ['WEBAPP_PORT'] = '{WEBAPP_PORT}'
'''
    
    with open('/tmp/webapp_config.py', 'w') as f:
        f.write(webapp_config)
    
    # Start webapp in background
    subprocess.Popen(
        ['python3', 'webapp_server.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd='/root/HydraX-v2'
    )
    
    time.sleep(3)
    print(f"✅ WebApp started on port {WEBAPP_PORT}")

def start_signal_bot():
    """Start the signal generation bot"""
    print("\n📡 Starting Signal Bot...")
    
    # Use the realistic signal bot as it's the most complete
    subprocess.Popen(
        ['python3', 'SIGNALS_REALISTIC.py'],
        stdout=open('/root/HydraX-v2/logs/signal_bot.log', 'a'),
        stderr=subprocess.STDOUT,
        cwd='/root/HydraX-v2'
    )
    
    time.sleep(2)
    print("✅ Signal bot started (REALISTIC mode)")

def send_startup_notification():
    """Send startup notification to Telegram"""
    print("\n📨 Sending startup notification...")
    
    notification_script = f'''
import asyncio
import telegram

async def notify():
    bot = telegram.Bot(token='{BOT_TOKEN}')
    message = """🚀 **BITTEN SYSTEM ONLINE**

✅ WebApp: {WEBAPP_URL}
✅ Signal Engine: ACTIVE
✅ TOC: Ready for operations

All systems operational. Ready for trading!"""
    
    await bot.send_message(
        chat_id='{CHAT_ID}',
        text=message,
        parse_mode='Markdown'
    )

asyncio.run(notify())
'''
    
    with open('/tmp/notify_startup.py', 'w') as f:
        f.write(notification_script)
    
    subprocess.run(['python3', '/tmp/notify_startup.py'])
    print("✅ Startup notification sent")

def create_logs_dir():
    """Ensure logs directory exists"""
    os.makedirs('/root/HydraX-v2/logs', exist_ok=True)

def main():
    """Main startup sequence"""
    print_banner()
    
    # Setup
    create_logs_dir()
    check_processes()
    
    # Ask to restart
    response = input("\n🔄 Restart all services? (y/n): ")
    if response.lower() == 'y':
        kill_existing()
        start_webapp()
        start_signal_bot()
        send_startup_notification()
    
    print("\n✅ BITTEN System Startup Complete!")
    print("\n📌 Quick Commands:")
    print("  - Check logs: tail -f logs/signal_bot.log")
    print("  - Test signal: python3 WEBAPP_WORKING_SIGNAL.py")
    print("  - Check webapp: curl http://localhost:8888/test")
    print("\n🎯 System ready for operations!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Startup cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during startup: {e}")