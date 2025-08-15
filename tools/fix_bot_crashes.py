#!/usr/bin/env python3
"""Add crash protection to bitten-production-bot"""
import os

file_path = '/root/HydraX-v2/bitten_production_bot.py'

# Read the bot file
with open(file_path, 'r') as f:
    lines = f.readlines()

# Find the main loop and add protection
protection_code = """
# CRASH PROTECTION ADDED
import traceback
import time

def safe_bot_run():
    consecutive_failures = 0
    while True:
        try:
            # Original bot code here
            bot.polling(non_stop=True, interval=0, timeout=60)
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            wait_time = min(300, 30 * consecutive_failures)  # Max 5 min backoff
            print(f"[BOT-ERROR] Crash {consecutive_failures}: {e}")
            print(f"[BOT-ERROR] Traceback: {traceback.format_exc()}")
            print(f"[BOT-RECOVERY] Waiting {wait_time}s before restart...")
            time.sleep(wait_time)
            if consecutive_failures > 10:
                print("[BOT-FATAL] Too many failures, exiting")
                break

# Replace bot.polling with protected version
"""

# Find where bot.polling is called
for i, line in enumerate(lines):
    if 'bot.polling(' in line and not line.strip().startswith('#'):
        # Comment out the original line
        lines[i] = '# ' + line
        # Add our protection after it
        lines.insert(i+1, 'safe_bot_run()  # Protected polling\n')
        break

# Add the protection function before the main execution
main_idx = -1
for i, line in enumerate(lines):
    if '__name__' in line and '__main__' in line:
        main_idx = i
        break

if main_idx > 0:
    lines.insert(main_idx, protection_code)

# Write back
with open(file_path, 'w') as f:
    f.writelines(lines)

print("✅ Added crash protection to bot")