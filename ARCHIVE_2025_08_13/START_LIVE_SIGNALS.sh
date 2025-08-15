#!/bin/bash

clear
echo "╔══════════════════════════════════════════╗"
echo "║     BITTEN LIVE SIGNALS LAUNCHER         ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "TraderMade Status: ❌ Limited (free plan restriction)"
echo "Recommended: Use Realistic Market Simulation"
echo ""
echo "Select signal source:"
echo ""
echo "1) 🎯 REALISTIC - Market-accurate simulation (RECOMMENDED)"
echo "   • Real market sessions (Asian/London/NY)"
echo "   • Realistic price movements"
echo "   • No API needed"
echo ""
echo "2) 📊 LIVE DATA - TraderMade API (won't work with free plan)"
echo "   • Requires paid TraderMade subscription"
echo ""
echo "3) 🎲 SIMPLE - Basic random signals"
echo "   • For quick testing only"
echo ""
read -p "Enter choice (1-3) [Default: 1]: " choice

# Default to realistic if no input
if [ -z "$choice" ]; then
    choice=1
fi

case $choice in
    1)
        echo ""
        echo "🚀 Starting Realistic Market Simulation..."
        echo "• Following real market sessions"
        echo "• Accurate price movements"
        echo "• Dynamic volatility"
        echo ""
        python3 SIGNALS_REALISTIC.py
        ;;
    2)
        echo ""
        echo "📊 Attempting TraderMade Live Data..."
        echo "Note: This requires a paid API key"
        echo ""
        python3 SIGNALS_LIVE_DATA.py
        ;;
    3)
        echo ""
        echo "🎲 Starting Simple Signals..."
        echo ""
        python3 SIGNALS_COMPACT.py
        ;;
    *)
        echo "Invalid choice. Starting Realistic signals..."
        python3 SIGNALS_REALISTIC.py
        ;;
esac