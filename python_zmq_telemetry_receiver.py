#!/usr/bin/env python3
"""
ZMQ Telemetry Receiver
Receives balance, equity, and trade results from MT5 EA
"""

import zmq
import json
import time
from datetime import datetime
from collections import defaultdict

class TelemetryReceiver:
    def __init__(self, port=9101):
        self.port = port
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.PULL)
        self.socket.bind(f"tcp://*:{port}")
        
        # Track telemetry by user
        self.user_data = defaultdict(dict)
        self.start_time = time.time()
        self.message_count = 0
        
        print(f"📡 Telemetry receiver listening on tcp://*:{port}")
        print("📊 Waiting for telemetry from MT5 EA...\n")
    
    def format_telemetry(self, data):
        """Format telemetry data for display"""
        msg_type = data.get('type', 'telemetry')
        uuid = data.get('uuid', 'unknown')
        
        if msg_type == 'trade_result':
            # Trade result message
            success = data.get('success', False)
            message = data.get('message', '')
            ticket = data.get('ticket', 0)
            
            status = "✅ SUCCESS" if success else "❌ FAILED"
            output = f"\n🔥 TRADE RESULT - {uuid}\n"
            output += f"   Status: {status}\n"
            output += f"   Message: {message}\n"
            if ticket > 0:
                output += f"   Ticket: {ticket}\n"
            output += f"   Time: {datetime.now().strftime('%H:%M:%S')}\n"
            
        else:
            # Regular telemetry
            balance = data.get('balance', 0)
            equity = data.get('equity', 0)
            margin = data.get('margin', 0)
            free_margin = data.get('free_margin', 0)
            profit = data.get('profit', 0)
            positions = data.get('positions', 0)
            
            # Track changes
            last_data = self.user_data[uuid]
            balance_changed = last_data.get('balance', balance) != balance
            positions_changed = last_data.get('positions', positions) != positions
            
            # Update stored data
            self.user_data[uuid] = data
            
            # Format output
            output = f"\n📊 TELEMETRY - {uuid}"
            if balance_changed or positions_changed:
                output += " 🔔 CHANGED"
            output += f"\n"
            output += f"   Balance: ${balance:,.2f}"
            if balance_changed:
                output += " ⚡"
            output += f"\n"
            output += f"   Equity: ${equity:,.2f}\n"
            output += f"   Profit: ${profit:,.2f}"
            if profit > 0:
                output += " 📈"
            elif profit < 0:
                output += " 📉"
            output += f"\n"
            output += f"   Margin Used: ${margin:,.2f}\n"
            output += f"   Free Margin: ${free_margin:,.2f}\n"
            output += f"   Open Positions: {positions}"
            if positions_changed:
                output += " 🔄"
            output += f"\n"
            output += f"   Time: {datetime.now().strftime('%H:%M:%S')}\n"
        
        return output
    
    def run(self):
        """Main event loop"""
        try:
            while True:
                # Receive message
                message = self.socket.recv()
                self.message_count += 1
                
                try:
                    # Parse JSON
                    data = json.loads(message.decode())
                    
                    # Format and display
                    print(self.format_telemetry(data))
                    
                    # Show stats every 10 messages
                    if self.message_count % 10 == 0:
                        uptime = int(time.time() - self.start_time)
                        print(f"📈 Stats: {self.message_count} messages received, {len(self.user_data)} users tracked, uptime: {uptime}s")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse message: {e}")
                    print(f"   Raw: {message}")
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down telemetry receiver...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.socket.close()
        self.ctx.term()
        print("✅ Telemetry receiver shutdown complete")

def main():
    """Main entry point"""
    import sys
    
    # Get port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9101
    
    print("🚀 BITTEN ZMQ Telemetry Receiver")
    print("=" * 50)
    print(f"Port: {port}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Create and run receiver
    receiver = TelemetryReceiver(port)
    receiver.run()

if __name__ == "__main__":
    main()