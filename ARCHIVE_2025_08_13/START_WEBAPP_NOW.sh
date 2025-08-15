#!/bin/bash
# EMERGENCY WEBAPP STARTER - NO DEPENDENCIES

echo "🚨 NUCLEAR WEBAPP RECOVERY STARTING..."
echo "Time: $(date)"

# Kill any existing processes on port 5000
echo "🔫 Killing existing processes..."
fuser -k 5000/tcp 2>/dev/null || true
sleep 2

# Start emergency server
echo "🚀 Starting nuclear webapp..."
cd /root/HydraX-v2

# Start with nohup to run in background
nohup /usr/bin/python3 EMERGENCY_WEBAPP_NUCLEAR.py > emergency_webapp.log 2>&1 &

sleep 5

# Test if it's working
echo "🧪 Testing webapp..."
curl -s http://localhost:5000/health && echo "✅ WEBAPP ONLINE" || echo "❌ WEBAPP FAILED"

echo "📊 Process check:"
ps aux | grep EMERGENCY_WEBAPP_NUCLEAR

echo "🎯 NUCLEAR RECOVERY COMPLETE"