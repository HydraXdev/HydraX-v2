#!/usr/bin/env python3
"""
Secure all exposed tokens before GitHub push
"""
import os
import re
import glob

# Tokens to redact (found in scan)
TOKENS_TO_REDACT = [
    os.getenv("BOT_TOKEN"),  # Athena bot
    os.getenv("BOT_TOKEN"),  # Bit Commander  
    os.getenv("BOT_TOKEN"),  # Monitor bot
    os.getenv("BOT_TOKEN"),  # MT5 password (if exposed)
]

# Files to process
files_to_check = []
for ext in ['*.py', '*.json', '*.md', '*.txt', '*.yml', '*.yaml']:
    files_to_check.extend(glob.glob(f'/root/HydraX-v2/**/{ext}', recursive=True))

print(f"Checking {len(files_to_check)} files...")

modified_files = []
for filepath in files_to_check:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original = content
        
        # Replace exposed tokens with environment variables
        for token in TOKENS_TO_REDACT:
            if token in content:
                # Replace with os.getenv() call
                if "Athena" in filepath or "athena" in filepath.lower():
                    content = content.replace(f'"{token}"', 'os.getenv("ATHENA_BOT_TOKEN")')
                    content = content.replace(f"'{token}'", 'os.getenv("ATHENA_BOT_TOKEN")')
                else:
                    content = content.replace(f'"{token}"', 'os.getenv("BOT_TOKEN")')
                    content = content.replace(f"'{token}'", 'os.getenv("BOT_TOKEN")')
        
        # Generic token patterns
        content = re.sub(r'(API_KEY\s*=\s*["\'])([^"\']+)(["\'])', r'\1REDACTED\3', content)
        content = re.sub(r'(SECRET\s*=\s*["\'])([^"\']+)(["\'])', r'\1REDACTED\3', content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            modified_files.append(filepath)
            print(f"✅ Secured: {filepath}")
            
    except Exception as e:
        print(f"⚠️ Skipped {filepath}: {e}")

print(f"\n📊 Summary:")
print(f"  Files checked: {len(files_to_check)}")
print(f"  Files secured: {len(modified_files)}")

# Create .env.example
env_example = """# BITTEN Environment Variables Example
# Copy to .env and fill in your values

# Telegram Bot Tokens
BOT_TOKEN=your_main_bot_token_here
ATHENA_BOT_TOKEN=your_athena_bot_token_here

# MT5 Credentials (if using local)
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# Stripe API (for payments)
STRIPE_API_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Database
BITTEN_DB=/root/HydraX-v2/bitten.db

# WebApp
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8888
FLASK_ENV=production
SECRET_KEY=your_secret_key_here

# ZMQ Configuration
CMD_QUEUE=ipc:///tmp/bitten_cmdqueue
"""

with open('/root/HydraX-v2/.env.example', 'w') as f:
    f.write(env_example)
print("✅ Created .env.example file")