#!/bin/bash
# Monitor for EA connection to port 5555

echo "====================================================================="
echo "🔍 Monitoring for EA Connection to Port 5555"
echo "====================================================================="
echo "Started: $(date)"
echo ""
echo "Current Status:"
echo "  - Hybrid Server: $(ps aux | grep hybrid_command_server | grep -v grep | awk '{print "PID "$2}')"
echo "  - TCP Server on 5555: $(ss -tlnp | grep :5555 | awk '{print $4}')"
echo ""
echo "EA Connection Status:"
ss -tn | grep "185.244.67.11" | grep -E ":5555|:5559|:6000" || echo "  - No active connections from EA yet"
echo ""
echo "Waiting for EA to connect to port 5555..."
echo "  (EA uses exponential backoff, max 32 seconds between attempts)"
echo ""

count=0
while [ $count -lt 120 ]; do
    # Check for established connection
    if ss -tn | grep ":5555" | grep "ESTAB" > /dev/null; then
        echo ""
        echo "✅✅✅ EA CONNECTED TO PORT 5555! ✅✅✅"
        echo "Time: $(date)"
        echo ""

        # Show connection details
        echo "Connection Details:"
        ss -tn | grep ":5555.*ESTAB"
        echo ""

        # Show hybrid server logs
        echo "Hybrid Server Logs (last 10 lines):"
        tail -10 /var/log/hybrid_command_server.log
        echo ""

        echo "🚀 feed_set command should be sent automatically"
        echo "   Watch Universal Bridge for market data:"
        echo "   tail -f /var/log/hydrasocket_universal_bridge.log | grep 'bar_closed\\|custom_bar'"

        exit 0
    fi

    # Print dot every 2 seconds
    echo -n "."
    sleep 2
    count=$((count+1))
done

echo ""
echo "⏱️ Timeout after 4 minutes - EA hasn't connected to port 5555 yet"
echo ""
echo "Debug Info:"
echo "  Hybrid Server Status:"
ps aux | grep hybrid_command_server | grep -v grep
echo ""
echo "  Port 5555 Status:"
ss -tlnp | grep :5555
echo ""
echo "  EA Connections (all ports):"
ss -tn | grep "185.244.67.11"
