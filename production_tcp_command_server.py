#!/usr/bin/env python3
"""
Production TCP Command Server for HydraSocket EA
Robust server with proper error handling, reconnection support, and monitoring
"""

import json
import os
import signal
import socket
import sys
import threading
import time
from collections import deque
from datetime import datetime

# Unbuffered output for logging
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 1)


class ProductionTCPCommandServer:
    def __init__(self, port=5555):
        self.port = port
        self.running = True
        self.server_socket = None
        self.ea_connections = {}  # account_id -> {'socket': socket, 'addr': address, 'connected_at': time}
        self.command_queue = deque(maxlen=100)  # Store pending commands
        self.stats = {
            "connections_accepted": 0,
            "messages_received": 0,
            "messages_sent": 0,
            "errors": 0,
            "server_start_time": time.time(),
        }

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n{datetime.now()} | Received signal {signum}, shutting down gracefully...")
        self.running = False

    def start_server(self):
        """Initialize and start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Set socket options for better performance
            self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(10)
            self.server_socket.settimeout(1.0)  # 1 second timeout for accept()

            print(f"{datetime.now()} | ✅ TCP Command Server started on 0.0.0.0:{self.port}")
            print(f"{datetime.now()} | Waiting for EA connections from 185.244.67.11...")
            return True

        except Exception as e:
            print(f"{datetime.now()} | ❌ Failed to start server: {e}")
            return False

    def accept_connections(self):
        """Main loop to accept incoming connections"""
        while self.running:
            try:
                # Check for new connections (with timeout)
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.stats["connections_accepted"] += 1

                    # Set socket options for the client
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    client_socket.settimeout(60.0)  # 60 second timeout for client operations

                    print(f"{datetime.now()} | 📡 EA CONNECTED from {client_address}")
                    print(f"{datetime.now()} | Connection #{self.stats['connections_accepted']}")

                    # Start handler thread for this connection
                    handler = threading.Thread(
                        target=self.handle_client, args=(client_socket, client_address), daemon=True
                    )
                    handler.start()

                except socket.timeout:
                    # No new connections, continue loop
                    pass

                # Periodic status update every 30 seconds
                if int(time.time()) % 30 == 0:
                    self.print_status()

            except Exception as e:
                if self.running:
                    print(f"{datetime.now()} | Error in accept loop: {e}")
                    self.stats["errors"] += 1
                    time.sleep(1)

    def handle_client(self, client_socket, client_address):
        """Handle individual EA client connection"""
        buffer = ""
        account_id = None
        last_heartbeat = time.time()

        try:
            # Send initial handshake
            handshake = {"type": "server_ready", "version": "1.0.0", "timestamp": time.time()}
            client_socket.send((json.dumps(handshake) + "\n").encode("utf-8"))

            while self.running:
                try:
                    # Receive data with timeout
                    data = client_socket.recv(4096)

                    if not data:
                        print(f"{datetime.now()} | Connection closed by {client_address}")
                        break

                    buffer += data.decode("utf-8", errors="ignore")
                    last_heartbeat = time.time()

                    # Process complete JSON messages
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)

                        if line.strip():
                            try:
                                message = json.loads(line)
                                self.stats["messages_received"] += 1

                                # Extract account_id if present
                                if "account_id" in message and not account_id:
                                    account_id = message["account_id"]
                                    self.ea_connections[account_id] = {
                                        "socket": client_socket,
                                        "addr": client_address,
                                        "connected_at": time.time(),
                                    }
                                    print(f"{datetime.now()} | ✅ Registered account: {account_id}")

                                    # Send queued feed_set command if this is first connection
                                    self.send_initial_feed_set(client_socket)

                                # Process the message
                                self.process_message(message, client_socket, client_address)

                            except json.JSONDecodeError as e:
                                print(f"{datetime.now()} | JSON error from {client_address}: {e}")
                                self.stats["errors"] += 1

                except socket.timeout:
                    # Check for heartbeat timeout (90 seconds)
                    if time.time() - last_heartbeat > 90:
                        print(f"{datetime.now()} | Heartbeat timeout for {client_address}")
                        break

                except Exception as e:
                    print(f"{datetime.now()} | Error handling client {client_address}: {e}")
                    self.stats["errors"] += 1
                    break

        finally:
            # Clean up connection
            if account_id and account_id in self.ea_connections:
                del self.ea_connections[account_id]
                print(f"{datetime.now()} | 🔌 Disconnected account: {account_id}")

            try:
                client_socket.close()
            except:
                pass

    def process_message(self, message, client_socket, client_address):
        """Process incoming message from EA"""
        msg_type = message.get("type", "unknown")

        print(f"{datetime.now()} | 📥 {msg_type} from {client_address[0]}")

        # Handle different message types
        if msg_type == "heartbeat":
            # Respond to heartbeat
            response = {"type": "heartbeat_ack", "timestamp": time.time()}
            self.send_response(client_socket, response)

        elif msg_type == "configure_feed":
            # EA is ready for feed configuration
            print(f"{datetime.now()} | EA requesting feed configuration")
            self.send_initial_feed_set(client_socket)

        else:
            # Generic acknowledgment
            response = {"type": "command_result", "request_ref": message.get("request_ref", ""), "status": "success"}
            self.send_response(client_socket, response)

    def send_initial_feed_set(self, client_socket):
        """Send initial feed configuration to EA"""
        feed_command = {
            "type": "feed_set",
            "request_ref": f"init-feed-{int(time.time())}",
            "target_uuid": "COMMANDER_DEV_001",
            "symbols": "XAUUSD,EURUSD,GBPJPY,USDJPY,GBPUSD,USDCAD,USDCHF,AUDUSD,NZDUSD,EURJPY,EURGBP,EURCAD,EURAUD,AUDJPY,NZDJPY,GBPCAD,CHFJPY,GBPCHF,EURCHF",
            "tfs": "M1,M5,H1",
            "lookback": 200,
            "midbar": 0,
            "midbar_sec": 15,
        }

        if self.send_response(client_socket, feed_command):
            print(f"{datetime.now()} | 📤 Sent feed_set command to EA")

    def send_response(self, client_socket, response_dict):
        """Send response to EA client"""
        try:
            response_json = json.dumps(response_dict) + "\n"
            client_socket.send(response_json.encode("utf-8"))
            self.stats["messages_sent"] += 1
            return True
        except Exception as e:
            print(f"{datetime.now()} | Failed to send response: {e}")
            self.stats["errors"] += 1
            return False

    def print_status(self):
        """Print server status"""
        uptime = int(time.time() - self.stats["server_start_time"])
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60

        active_connections = len(self.ea_connections)

        if active_connections > 0 or self.stats["messages_received"] > 0:
            print(
                f"{datetime.now()} | STATUS: Uptime {hours}h {minutes}m | "
                f"Connections: {active_connections} | "
                f"Messages: {self.stats['messages_received']}/{self.stats['messages_sent']} | "
                f"Errors: {self.stats['errors']}"
            )

    def run(self):
        """Main server run method"""
        if not self.start_server():
            return

        print(f"{datetime.now()} | Server ready for connections")
        print(f"{datetime.now()} | Expected EA IP: 185.244.67.11")
        print(f"{datetime.now()} | Listening on all interfaces (0.0.0.0:{self.port})")

        try:
            self.accept_connections()
        finally:
            # Clean shutdown
            print(f"{datetime.now()} | Shutting down server...")

            # Close all client connections
            for account_id, conn_info in list(self.ea_connections.items()):
                try:
                    conn_info["socket"].close()
                except:
                    pass

            # Close server socket
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass

            print(f"{datetime.now()} | Server shutdown complete")
            self.print_status()


if __name__ == "__main__":
    server = ProductionTCPCommandServer(port=5555)
    server.run()
