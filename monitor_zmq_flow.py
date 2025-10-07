#!/usr/bin/env python3
"""
Monitor BITTEN v3.002 ZMQ Data Flow
Shows real-time activity on all ZMQ ports
"""

import zmq
import json
import threading
import time
from datetime import datetime
from collections import defaultdict

class ZMQMonitor:
    def __init__(self):
        self.context = zmq.Context()
        self.stats = defaultdict(int)
        self.running = True
        self.last_messages = {}

    def monitor_metrics(self):
        """Monitor port 5560 - Published metrics"""
        socket = self.context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5560")
        socket.subscribe(b"")
        socket.setsockopt(zmq.RCVTIMEO, 1000)

        while self.running:
            try:
                message = socket.recv_string()
                self.stats['metrics'] += 1

                # Try to parse JSON
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    symbol = data.get('symbol') or data.get('sym', '')
                    self.last_messages['metrics'] = f"{msg_type} {symbol}"
                except:
                    # If not JSON, just show raw
                    if message.startswith('{"'):
                        self.last_messages['metrics'] = message[:50]
                    else:
                        # Skip non-JSON prefixed messages
                        parts = message.split(' ', 1)
                        if len(parts) > 1 and parts[1].startswith('{'):
                            try:
                                data = json.loads(parts[1])
                                msg_type = data.get('type', 'unknown')
                                symbol = data.get('symbol') or data.get('sym', '')
                                self.last_messages['metrics'] = f"{msg_type} {symbol}"
                            except:
                                pass
            except zmq.Again:
                pass
            except Exception as e:
                pass

        socket.close()

    def display_stats(self):
        """Display statistics every second"""
        while self.running:
            time.sleep(1)

            # Clear screen
            print("\033[2J\033[H")  # Clear screen and move cursor to top

            print("=" * 60)
            print("BITTEN v3.002 ZMQ Monitor - LIVE")
            print("=" * 60)
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            print("📊 Message Counts:")
            print(f"  Port 5560 (Metrics): {self.stats['metrics']:,} messages")
            print()

            print("📨 Last Messages:")
            for port, msg in self.last_messages.items():
                print(f"  {port}: {msg}")
            print()

            print("Press Ctrl+C to stop...")

    def run(self):
        """Start monitoring threads"""
        threads = [
            threading.Thread(target=self.monitor_metrics, daemon=True),
            threading.Thread(target=self.display_stats, daemon=True)
        ]

        for t in threads:
            t.start()

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
            self.running = False
            time.sleep(1)
            self.context.term()

if __name__ == "__main__":
    monitor = ZMQMonitor()
    monitor.run()