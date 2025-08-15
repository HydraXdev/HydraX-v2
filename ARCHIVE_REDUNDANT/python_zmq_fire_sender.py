#!/usr/bin/env python3
"""
ZMQ Fire Command Sender
Sends trade execution commands to MT5 EA via ZMQ
"""

import zmq
import time
import json
import sys

def send_fire_command(action="BUY", symbol="XAUUSD", lot=0.1, tp=40, sl=20, uuid="user-001"):
    """
    Send a fire command to the MT5 EA
    
    Args:
        action: BUY or SELL
        symbol: Trading symbol (e.g., XAUUSD, EURUSD)
        lot: Lot size
        tp: Take profit in points
        sl: Stop loss in points
        uuid: User identifier
    """
    # Create ZMQ context and socket
    ctx = zmq.Context()
    socket = ctx.socket(zmq.PUB)
    
    # Bind to the fire port
    socket.bind("tcp://*:9001")
    print(f"📡 Fire command socket bound to tcp://*:9001")
    
    # Allow time for EA to connect
    print("⏳ Waiting 2 seconds for EA to connect...")
    time.sleep(2)
    
    # Prepare fire packet
    fire_packet = {
        "uuid": uuid,
        "action": action,
        "symbol": symbol,
        "lot": lot,
        "tp": tp,
        "sl": sl,
        "timestamp": int(time.time())
    }
    
    # Send the command
    message = json.dumps(fire_packet)
    socket.send_string(message)
    
    print(f"✅ Fire packet sent to bridge:")
    print(f"   Action: {action}")
    print(f"   Symbol: {symbol}")
    print(f"   Lot: {lot}")
    print(f"   TP: {tp} points")
    print(f"   SL: {sl} points")
    print(f"   UUID: {uuid}")
    print(f"🔥 Command: {message}")
    
    # Keep socket open for a moment
    time.sleep(1)
    
    # Cleanup
    socket.close()
    ctx.term()
    print("✅ Fire command sent successfully")

def main():
    """Main function with command line support"""
    if len(sys.argv) > 1:
        # Parse command line arguments
        action = sys.argv[1].upper() if len(sys.argv) > 1 else "BUY"
        symbol = sys.argv[2] if len(sys.argv) > 2 else "XAUUSD"
        lot = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
        tp = float(sys.argv[4]) if len(sys.argv) > 4 else 40
        sl = float(sys.argv[5]) if len(sys.argv) > 5 else 20
        uuid = sys.argv[6] if len(sys.argv) > 6 else "user-001"
        
        print(f"📊 Sending custom fire command...")
        send_fire_command(action, symbol, lot, tp, sl, uuid)
    else:
        # Default test trade
        print("🎯 Sending default test trade (BUY XAUUSD)")
        send_fire_command()
        
        print("\n💡 Usage: python3 python_zmq_fire_sender.py [ACTION] [SYMBOL] [LOT] [TP] [SL] [UUID]")
        print("   Example: python3 python_zmq_fire_sender.py SELL EURUSD 0.01 50 25 user-002")

if __name__ == "__main__":
    main()