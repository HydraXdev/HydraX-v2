#!/usr/bin/env python3
"""
Start BITTEN bot with proper configuration
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.append('/root/HydraX-v2')

# Set up environment
os.environ['BITTEN_WEBAPP_URL'] = 'https://joinbitten.com'
os.environ['BITTEN_HUD_URL'] = 'https://joinbitten.com/hud'

# Find and load .env file
env_file = Path('/root/HydraX-v2/.env')
if env_file.exists():
    print("📋 Loading environment from .env")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

# Check for bot token
bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
if not bot_token or bot_token == 'DISABLED_FOR_SECURITY':
    print("❌ Error: Bot token not found in environment")
    print("Please set TELEGRAM_BOT_TOKEN or BOT_TOKEN in .env file")
    sys.exit(1)

print(f"✅ Bot token found: {bot_token[:10]}...")
print(f"📍 Webapp URL: {os.environ['BITTEN_WEBAPP_URL']}")
print(f"🎯 HUD URL: {os.environ['BITTEN_HUD_URL']}")

# Find the appropriate bot file
bot_files = [
    'WEBAPP_SIGNAL_BOT.py',
    'BITTEN_BOT_WITH_INTEL_CENTER.py',
    'FINAL_BOT_WORKING.py',
    'src/telegram_bot/bot.py'
]

bot_file = None
for file in bot_files:
    if Path(f'/root/HydraX-v2/{file}').exists():
        bot_file = file
        break

if not bot_file:
    print("❌ Error: No bot file found")
    sys.exit(1)

print(f"🤖 Starting bot: {bot_file}")

# Kill any existing bot processes
subprocess.run(['pkill', '-f', 'WEBAPP_SIGNAL_BOT'], capture_output=True)
subprocess.run(['pkill', '-f', 'BITTEN_BOT'], capture_output=True)

# Start the bot
try:
    subprocess.run([sys.executable, bot_file], cwd='/root/HydraX-v2')
except KeyboardInterrupt:
    print("\n⏹️  Bot stopped by user")
except Exception as e:
    print(f"❌ Error starting bot: {e}")