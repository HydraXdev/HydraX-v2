#!/bin/bash
# Start ZMQ Fire Command Publisher

echo "🚀 Starting ZMQ Fire Command Publisher"
echo "================================"
echo "Binding to tcp://*:5555 for command publishing"
echo "Binding to tcp://*:5556 for telemetry receiving"
echo ""

# Export environment variables
export USE_ZMQ=true
export ZMQ_DUAL_WRITE=true

# Start the controller
python3 /root/HydraX-v2/zmq_bitten_controller.py