#!/bin/bash
# Deploy ZMQ Market Data Pipeline
# Sets up the complete LIVE data flow from MT5 to VENOM

echo "=" 
echo "🚀 BITTEN ZMQ Market Data Pipeline Deployment"
echo "="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Step 1: Install ZMQ if needed
echo "📦 Step 1: Checking ZMQ installation..."
if ! python3 -c "import zmq" 2>/dev/null; then
    echo "Installing python3-zmq..."
    apt-get update
    apt-get install -y python3-zmq
    pip3 install pyzmq
else
    echo "✅ ZMQ already installed"
fi

# Step 2: Stop existing services
echo -e "\n🛑 Step 2: Stopping existing services..."
systemctl stop market-data-receiver 2>/dev/null || true
systemctl stop zmq-market-streamer 2>/dev/null || true
systemctl stop venom-zmq-adapter 2>/dev/null || true

# Step 3: Make scripts executable
echo -e "\n🔧 Step 3: Setting permissions..."
chmod +x /root/HydraX-v2/zmq_market_streamer.py
chmod +x /root/HydraX-v2/venom_zmq_adapter.py
chmod +x /root/HydraX-v2/test_zmq_market_flow.py

# Step 4: Install systemd service
echo -e "\n⚙️ Step 4: Installing systemd service..."
cp /root/HydraX-v2/zmq_market_streamer.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable zmq-market-streamer

# Step 5: Start the service
echo -e "\n🚀 Step 5: Starting ZMQ market streamer..."
systemctl start zmq-market-streamer
sleep 2

# Check status
if systemctl is-active --quiet zmq-market-streamer; then
    echo "✅ ZMQ market streamer is running"
    systemctl status zmq-market-streamer --no-pager | head -10
else
    echo "❌ Failed to start ZMQ market streamer"
    journalctl -u zmq-market-streamer -n 20 --no-pager
    exit 1
fi

# Step 6: Test the pipeline
echo -e "\n🧪 Step 6: Testing the pipeline..."
python3 /root/HydraX-v2/test_zmq_market_flow.py

echo -e "\n✅ Deployment complete!"
echo
echo "📋 Next steps:"
echo "1. Update MT5 EA to use ZMQ publisher on port 5555"
echo "2. Integrate VENOM engine with ZMQ adapter"
echo "3. Monitor logs: journalctl -u zmq-market-streamer -f"
echo
echo "🔍 Useful commands:"
echo "- Check status: systemctl status zmq-market-streamer"
echo "- View logs: journalctl -u zmq-market-streamer -f"
echo "- Restart: systemctl restart zmq-market-streamer"
echo "- Test flow: python3 /root/HydraX-v2/test_zmq_market_flow.py"