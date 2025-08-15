#!/bin/bash

echo "🚀 Testing ZMQ EA v7 Connection"
echo "================================"
echo "This will start the controller and wait for your EA"
echo ""
echo "Make sure:"
echo "1. EA v7 is compiled and attached to a chart"
echo "2. libzmq.dll is in MT5 Libraries folder"
echo "3. EA parameters show:"
echo "   - Backend: tcp://134.199.204.67:5555"
echo "   - Heartbeat: tcp://134.199.204.67:5556"
echo ""
echo "Starting controller..."
echo ""

python3 /root/HydraX-v2/zmq_trade_controller.py