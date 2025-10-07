#!/bin/bash
# CUTOVER: Wait for MetaSocket and test connection when available

echo "🎯 WAITING FOR METASOCKET TO COME ONLINE"
echo "============================================================"

# MetaSocket configuration
MSKT_HOST=${MSKT_HOST:-185.244.67.11}
MSKT_CMD_PORT=${MSKT_CMD_PORT:-8777}
MSKT_STREAM_PORT=${MSKT_STREAM_PORT:-8778}

echo "📊 Waiting for MetaSocket at $MSKT_HOST:$MSKT_CMD_PORT and $MSKT_HOST:$MSKT_STREAM_PORT"
echo "⏳ Will test connection every 10 seconds..."
echo ""

attempt=1
while true; do
    echo "🔍 Attempt $attempt - $(date '+%H:%M:%S')"

    # Test CMD port
    if timeout 2 bash -c "echo > /dev/tcp/$MSKT_HOST/$MSKT_CMD_PORT" 2>/dev/null; then
        echo "✅ CMD Port $MSKT_CMD_PORT is accessible!"

        # Test STREAM port
        if timeout 2 bash -c "echo > /dev/tcp/$MSKT_HOST/$MSKT_STREAM_PORT" 2>/dev/null; then
            echo "✅ STREAM Port $MSKT_STREAM_PORT is accessible!"
            echo ""
            echo "🎉 METASOCKET IS ONLINE! Running tests..."
            echo ""

            # Run comprehensive tests
            ./scripts/test_metasocket_direct.sh
            echo ""

            # Check adapter logs
            echo "📊 MetaSocket Adapter Status:"
            timeout 5 pm2 logs metasocket_adapter --lines 3
            echo ""

            # Check health endpoint
            echo "🏥 Health Endpoint Status:"
            curl -s http://localhost:8888/healthz | jq .metasocket || echo "MetaSocket health not in endpoint yet"
            echo ""

            echo "🎯 CUTOVER READY - MetaSocket streaming is live!"
            exit 0
        else
            echo "⚠️  CMD port accessible but STREAM port not ready yet"
        fi
    else
        echo "⏳ Ports not accessible yet..."
    fi

    echo ""
    sleep 10
    ((attempt++))

    # Safety break after 30 attempts (5 minutes)
    if [ $attempt -gt 30 ]; then
        echo "⏰ Timeout after 5 minutes waiting for MetaSocket"
        exit 1
    fi
done
