#!/usr/bin/env python3
"""Fix Telegram broadcaster BOT_DOMAIN_INVALID issue"""
import os

# Read the broadcaster file
file_path = '/root/HydraX-v2/tools/telegram_broadcaster_alerts.py'
with open(file_path, 'r') as f:
    content = f.read()

# Fix 1: Change URL from IP to domain
content = content.replace(
    'https://134.209.204.67:8888',
    'https://joinbitten.com'
)
content = content.replace(
    'http://134.209.204.67:8888', 
    'https://joinbitten.com'
)

# Fix 2: Simplify message format - remove inline keyboard
# Find the section that creates inline keyboards
old_button = """                reply_markup = {
                    "inline_keyboard": [[{
                        "text": button_text,
                        "login_url": {
                            "url": auth_url
                        }
                    }]]
                }"""

new_button = """                # Simplified - no inline keyboard to avoid BOT_DOMAIN_INVALID
                reply_markup = None"""

content = content.replace(old_button, new_button)

# Also simplify the message sending
content = content.replace(
    'if reply_markup:\n                    payload["reply_markup"] = reply_markup',
    '# Inline keyboards disabled to fix BOT_DOMAIN_INVALID'
)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Fixed telegram_broadcaster_alerts.py")