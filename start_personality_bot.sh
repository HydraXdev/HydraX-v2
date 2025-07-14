#!/bin/bash
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
