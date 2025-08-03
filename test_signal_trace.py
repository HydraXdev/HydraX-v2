#!/usr/bin/env python3
"""
Test Signal Trace
Injects a test signal at port 5557 and monitors the flow
"""

import zmq
import json
import time
import threading

def monitor_port_5555():
    """Monitor what EA would receive on port 5555"""
    context = zmq.Context()
    
    # Connect as PULL (like EA would)
    puller = context.socket(zmq.PULL)
    puller.connect("tcp://127.0.0.1:5555")
    puller.setsockopt(zmq.RCVTIMEO, 15000)  # 15 second timeout
    
    print("📡 Monitoring port 5555 (EA receiving port)...")
    print("-" * 60)
    
    start_time = time.time()
    message_count = 0
    
    while time.time() - start_time < 15:
        try:
            message = puller.recv_json()
            message_count += 1
            
            msg_type = message.get('type', 'unknown')
            if msg_type == 'heartbeat':
                print(f"💓 [{message_count}] Heartbeat received: {message.get('msg', '')}")
            elif msg_type == 'signal':
                print(f"🔥 [{message_count}] FIRE SIGNAL received!")
                print(f"   Signal ID: {message.get('signal_id')}")
                print(f"   Symbol: {message.get('symbol')}")
                print(f"   Action: {message.get('action')}")
                print(f"   Confidence: {message.get('confidence')}%")
            else:
                print(f"📨 [{message_count}] Other message: {msg_type}")
                
        except zmq.Again:
            print("⏰ Timeout - no message received")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            
    print(f"\n📊 Total messages received: {message_count}")
    puller.close()
    context.term()

def inject_test_signal():
    """Inject a test signal to port 5557"""
    time.sleep(2)  # Let monitor start
    
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://127.0.0.1:5558")  # Bind to different port
    
    # Give subscribers time to connect
    time.sleep(1)
    
    print("\n🚀 Injecting test signal...")
    
    # Create Elite Guard format signal
    test_signal = {
        "signal_id": "TEST_TRACE_001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "confidence": 92.5,
        "stop_loss_pips": 20,
        "target_pips": 40,
        "signal_type": "LIQUIDITY_SWEEP",
        "timestamp": time.time()
    }
    
    # Send with Elite Guard prefix
    message = f"ELITE_GUARD_SIGNAL {json.dumps(test_signal)}"
    publisher.send_string(message)
    
    print("✅ Test signal injected to port 5557")
    
    publisher.close()
    context.term()

def main():
    print("🎯 SIGNAL FLOW TRACE TEST")
    print("=" * 60)
    print("Testing: Elite Guard (5557) → Fire Publisher → EA (5555)")
    print("=" * 60)
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_port_5555)
    monitor_thread.start()
    
    # Inject test signal
    inject_test_signal()
    
    # Wait for monitor to finish
    monitor_thread.join()
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()