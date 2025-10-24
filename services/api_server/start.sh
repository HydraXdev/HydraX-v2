#!/bin/bash
# BITTEN v2.0 API Server Startup Script

set -e

echo "🚀 Starting BITTEN v2.0 API Server..."

# Change to api_server directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  WARNING: TELEGRAM_BOT_TOKEN not set"
    echo "   Bot functionality will be disabled"
fi

# Start the server
echo "✅ Starting FastAPI server on port 8888..."
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8888 \
    --reload \
    --log-level info
