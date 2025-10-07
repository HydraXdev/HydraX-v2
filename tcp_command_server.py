#!/usr/bin/env python3
"""
Simple TCP Command Server for HydraSocket EA
Handles native TCP connections on port 5555 without ZMQ complexity
"""

import socket
import json
import threading
import select
import time
import sys
from datetime import datetime

# Force unbuffered output
sys.stdout = sys.stderr = open(sys.stdout.fileno(), 'w', buffering=1)

class SimpleCommandServer:
    def __init__(self):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind(('0.0.0.0', 5555))
        self.tcp_sock.listen(200)
        print(f"{datetime.now()} | TCP command server listening on port 5555")

        self.ea_connections = {}  # account_id -> socket
        self.connection_count = 0

    def run(self):
        print(f"{datetime.now()} | Server ready, waiting for EA connections...")

        while True:
            try:
                # Use select with timeout to avoid blocking
                readable, _, _ = select.select([self.tcp_sock], [], [], 0.1)

                if readable:
                    conn, addr = self.tcp_sock.accept()
                    self.connection_count += 1
                    print(f"{datetime.now()} | 📡 EA connected from {addr} (connection #{self.connection_count})")
                    threading.Thread(target=self.handle_ea, args=(conn, addr), daemon=True).start()

            except KeyboardInterrupt:
                print(f"\n{datetime.now()} | Shutting down...")
                break
            except Exception as e:
                print(f"{datetime.now()} | Error in main loop: {e}")
                time.sleep(1)

    def handle_ea(self, conn, addr):
        buffer = ""
        account_id = None

        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    print(f"{datetime.now()} | EA disconnected from {addr}")
                    break

                buffer += data.decode('utf-8')

                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            cmd = json.loads(line)
                            cmd_type = cmd.get('type', 'unknown')

                            print(f"{datetime.now()} | 📥 Command from {addr}: {cmd_type}")

                            # Extract account_id from first command
                            if not account_id and 'account_id' in cmd:
                                account_id = cmd['account_id']
                                self.ea_connections[account_id] = conn
                                print(f"{datetime.now()} | ✅ Registered EA account_id: {account_id}")

                            # Process command
                            self.process_command(cmd, conn, addr)

                        except json.JSONDecodeError as e:
                            print(f"{datetime.now()} | ❌ Invalid JSON from {addr}: {e}")
                            print(f"   Data: {line[:100]}")

        except Exception as e:
            print(f"{datetime.now()} | Connection error from {addr}: {e}")
        finally:
            if account_id and account_id in self.ea_connections:
                del self.ea_connections[account_id]
                print(f"{datetime.now()} | 🔌 Unregistered account_id: {account_id}")
            conn.close()

    def process_command(self, cmd, conn, addr):
        """Process incoming command from EA and send response"""
        cmd_type = cmd.get('type', 'unknown')
        request_ref = cmd.get('request_ref', '')

        # Build response
        response = {
            "type": "command_result",
            "request_ref": request_ref,
            "status": "success",
            "message": f"Command {cmd_type} received"
        }

        try:
            response_json = json.dumps(response) + "\n"
            conn.send(response_json.encode())
            print(f"{datetime.now()} | 📤 Sent response to {addr}: {cmd_type} -> success")
        except Exception as e:
            print(f"{datetime.now()} | ❌ Failed to send response to {addr}: {e}")

    def send_command_to_ea(self, account_id, command):
        """Send command to specific EA by account_id"""
        if account_id not in self.ea_connections:
            print(f"{datetime.now()} | ❌ No connection for account_id: {account_id}")
            return False

        try:
            conn = self.ea_connections[account_id]
            command_json = json.dumps(command) + "\n"
            conn.send(command_json.encode())
            print(f"{datetime.now()} | 📤 Sent command to account {account_id}: {command.get('type')}")
            return True
        except Exception as e:
            print(f"{datetime.now()} | ❌ Failed to send command to {account_id}: {e}")
            return False

if __name__ == "__main__":
    server = SimpleCommandServer()
    server.run()
