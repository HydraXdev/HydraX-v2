#!/bin/bash
# CUTOVER: MetaSocket Adapter Runner
# Starts the MetaSocket adapter as a PM2 service for streaming

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 CUTOVER: Starting MetaSocket Adapter${NC}"
echo "============================================================"

# Check SOURCE environment
SOURCE=${SOURCE:-ea}
echo -e "📊 SOURCE setting: ${YELLOW}$SOURCE${NC}"

if [[ "$SOURCE" != "metasocket" && "$SOURCE" != "both" ]]; then
    echo -e "${RED}❌ WARNING: SOURCE must be 'metasocket' or 'both' to run adapter${NC}"
    echo "   Set: export SOURCE=metasocket"
fi

# Check MetaSocket connection settings
MSKT_HOST=${MSKT_HOST:-127.0.0.1}
MSKT_CMD_PORT=${MSKT_CMD_PORT:-8777}
MSKT_STREAM_PORT=${MSKT_STREAM_PORT:-8778}

echo -e "📊 MetaSocket Config:"
echo -e "   Host: ${YELLOW}$MSKT_HOST${NC}"
echo -e "   CMD Port: ${YELLOW}$MSKT_CMD_PORT${NC}"
echo -e "   STREAM Port: ${YELLOW}$MSKT_STREAM_PORT${NC}"

# Test MetaSocket connectivity
echo -e "\n${BLUE}🔍 Testing MetaSocket Connectivity${NC}"

# Test CMD port
if timeout 3 bash -c "echo > /dev/tcp/$MSKT_HOST/$MSKT_CMD_PORT"; then
    echo -e "✅ CMD Port $MSKT_CMD_PORT accessible"
else
    echo -e "${RED}❌ CMD Port $MSKT_CMD_PORT not accessible${NC}"
fi

# Test STREAM port
if timeout 3 bash -c "echo > /dev/tcp/$MSKT_HOST/$MSKT_STREAM_PORT"; then
    echo -e "✅ STREAM Port $MSKT_STREAM_PORT accessible"
else
    echo -e "${RED}❌ STREAM Port $MSKT_STREAM_PORT not accessible${NC}"
fi

# Create adapter runner script
ADAPTER_SCRIPT="/root/HydraX-v2/run_metasocket_adapter_daemon.py"

cat > "$ADAPTER_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
MetaSocket Adapter Daemon
Runs the MetaSocket adapter as a persistent service
"""

import sys
import time
import signal
sys.path.append('/root/HydraX-v2')

from adapters.metasocket.adapter import MetaSocketAdapter

def signal_handler(signum, frame):
    print(f"🔄 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    print("🎯 MetaSocket Adapter Daemon Starting...")

    # Handle signals gracefully
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    adapter = None

    try:
        # Create and start adapter
        adapter = MetaSocketAdapter()
        print("✅ MetaSocket adapter initialized")

        # Start event reader thread
        adapter.start_event_reader()
        print("✅ Event reader thread started")

        # Keep daemon running
        while True:
            # Health check every 30 seconds
            health = adapter.get_health_status()
            print(f"📊 Health: {health['status']} | Events: {health['last_event_age_ms']}ms ago")

            time.sleep(30)

    except KeyboardInterrupt:
        print("🔄 Keyboard interrupt received")
    except Exception as e:
        print(f"❌ Adapter error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if adapter:
            adapter.stop_event_reader()
            print("✅ Adapter stopped gracefully")

if __name__ == '__main__':
    main()
EOF

chmod +x "$ADAPTER_SCRIPT"

# Start adapter as PM2 service
echo -e "\n${BLUE}🚀 Starting MetaSocket Adapter in PM2${NC}"

# Stop any existing adapter
pm2 delete metasocket_adapter 2>/dev/null || true

# Start new adapter
pm2 start "$ADAPTER_SCRIPT" --name metasocket_adapter --restart-delay=5000

echo -e "✅ MetaSocket adapter started in PM2"

# Show status
echo -e "\n${BLUE}📊 Service Status${NC}"
pm2 list | grep metasocket_adapter

# Show initial logs
echo -e "\n${BLUE}📋 Initial Logs (5 seconds)${NC}"
timeout 5 pm2 logs metasocket_adapter --lines 0 || true

echo -e "\n${GREEN}🎉 MetaSocket Adapter Running${NC}"
echo -e "${BLUE}Monitor with: pm2 logs metasocket_adapter${NC}"
echo -e "${BLUE}Stop with: pm2 stop metasocket_adapter${NC}"
