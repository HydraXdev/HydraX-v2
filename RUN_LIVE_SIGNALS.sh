#!/bin/bash
# BITTEN Live Signal Runner
# This script starts the live signal system with all features enabled

echo "╔══════════════════════════════════════════╗"
echo "║      BITTEN LIVE SIGNALS LAUNCHER        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "🚀 Starting BITTEN Live Signal System..."
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Using virtual environment"
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Options for different start methods
echo "Select signal system to start:"
echo "1) Simple Live Signals (Recommended)"
echo "2) Advanced Signal Integration"
echo "3) Complete Signal Flow V3"
echo "4) Test WebApp Buttons"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "Starting Simple Live Signals..."
        python start_live_simple.py
        ;;
    2)
        echo "Starting Advanced Signal Integration..."
        python start_bitten_live_signals.py
        ;;
    3)
        echo "Starting Complete Signal Flow V3..."
        python start_signals_now.py
        ;;
    4)
        echo "Testing WebApp Buttons..."
        python test_webapp_button_fix.py
        ;;
    *)
        echo "Invalid choice. Starting Simple Live Signals by default..."
        python start_live_simple.py
        ;;
esac
