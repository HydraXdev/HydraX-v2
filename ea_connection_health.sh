#!/bin/bash
#
# EA Connection Health Check
# Quick script to verify all EA connections are working
#

echo "======================================"
echo "EA CONNECTION HEALTH CHECK"
echo "$(date)"
echo "======================================"
echo ""

# Check if servers are running
echo "📡 SERVER PROCESSES:"
echo "-------------------"

if ps aux | grep -q "[p]roduction_tcp_command_server"; then
    PID=$(ps aux | grep "[p]roduction_tcp_command_server" | awk '{print $2}')
    echo "✅ Command Server (5555): Running (PID: $PID)"
else
    echo "❌ Command Server (5555): NOT RUNNING"
fi

if ps aux | grep -q "[h]ydrasocket_universal_bridge"; then
    PID=$(ps aux | grep "[h]ydrasocket_universal_bridge" | awk '{print $2}')
    echo "✅ Universal Bridge (5559/6000): Running (PID: $PID)"
else
    echo "❌ Universal Bridge (5559/6000): NOT RUNNING"
fi

echo ""
echo "🔌 PORT STATUS:"
echo "---------------"

# Check listening ports
for PORT in 5555 5559 6000; do
    if ss -tlnp | grep -q ":$PORT "; then
        echo "✅ Port $PORT: LISTENING"
    else
        echo "❌ Port $PORT: NOT LISTENING"
    fi
done

echo ""
echo "🌐 EA CONNECTIONS (185.244.67.11):"
echo "-----------------------------------"

# Check EA connections
CONNECTION_COUNT=0

for PORT in 5555 5559 6000; do
    CONN=$(ss -tn | grep "185.244.67.11.*:$PORT.*ESTAB")
    if [ ! -z "$CONN" ]; then
        echo "✅ Port $PORT: CONNECTED"
        CONNECTION_COUNT=$((CONNECTION_COUNT + 1))
    else
        echo "⏳ Port $PORT: Not connected"
    fi
done

echo ""
echo "📊 SUMMARY:"
echo "-----------"
echo "Active EA connections: $CONNECTION_COUNT/3"

if [ $CONNECTION_COUNT -eq 3 ]; then
    echo "🎯 SYSTEM FULLY OPERATIONAL!"
elif [ $CONNECTION_COUNT -gt 0 ]; then
    echo "⚡ Partial connectivity - EA reconnection pending"
else
    echo "⏳ Waiting for EA connections..."
fi

# Check last activity
echo ""
echo "📝 RECENT ACTIVITY:"
echo "-------------------"

if [ -f /var/log/hydrasocket/tcp_command_server.log ]; then
    echo "Command Server (last 3 lines):"
    tail -3 /var/log/hydrasocket/tcp_command_server.log | sed 's/^/  /'
fi

echo ""
echo "Universal Bridge (last events):"
tail -3 /var/log/hydrasocket_universal_bridge.log 2>/dev/null | grep -E "Event:|Connected" | sed 's/^/  /'

echo ""
echo "======================================"
