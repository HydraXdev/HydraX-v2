#!/usr/bin/env python3
"""
Hybrid Command Server - Handles BOTH ZMQ and Native TCP on Port 5555

This server replaces command_router.py and provides:
1. ZMQ ROUTER socket for Brain/IPC communication (BITTEN legacy)
2. Native TCP server for HydraSocket EA connections

Architecture:
    Brain/IPC (ZMQ) ──┐
                      ├──> Port 5555 Hybrid Server ──> Command Processing
    EA (Native TCP) ──┘

The server detects the protocol type and routes accordingly:
- ZMQ traffic: Processed as ZMQ ROUTER pattern
- TCP traffic: Processed as JSONL over native sockets
"""

import zmq
import socket
import select
import json
import time
import logging
import threading
import sqlite3
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HybridServer')


class HybridCommandServer:
    """Hybrid server handling both ZMQ and native TCP protocols"""

    def __init__(self, port=5555, ipc_path="ipc:///tmp/bitten_cmdqueue"):
        self.port = port
        self.ipc_path = ipc_path
        self.running = True

        # ZMQ setup
        self.zmq_context = zmq.Context()
        self.zmq_router = None
        self.ipc_pull = None

        # TCP setup
        self.tcp_server = None
        self.ea_connections = {}  # {socket: {'address': addr, 'buffer': bytes}}

        # Statistics
        self.stats = {
            'zmq_messages': 0,
            'tcp_messages': 0,
            'ea_connections': 0,
            'commands_forwarded': 0
        }

    def setup_zmq_router(self):
        """Set up ZMQ ROUTER for Brain communication"""
        try:
            self.zmq_router = self.zmq_context.socket(zmq.ROUTER)
            # Note: We CAN'T bind both ZMQ and raw TCP to same port
            # So we bind ZMQ to a different endpoint
            self.zmq_router.bind("tcp://*:5554")  # Use 5554 for ZMQ instead
            logger.info(f"✅ ZMQ ROUTER bound to port 5554")
            return True
        except Exception as e:
            logger.error(f"❌ ZMQ ROUTER setup failed: {e}")
            return False

    def setup_ipc_pull(self):
        """Set up ZMQ PULL for IPC queue"""
        try:
            self.ipc_pull = self.zmq_context.socket(zmq.PULL)
            self.ipc_pull.bind(self.ipc_path)
            logger.info(f"✅ IPC PULL bound to {self.ipc_path}")
            return True
        except Exception as e:
            logger.error(f"❌ IPC setup failed: {e}")
            return False

    def setup_tcp_server(self):
        """Set up native TCP server for EA connections"""
        try:
            self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_server.setblocking(False)  # Non-blocking for select()
            self.tcp_server.bind(('0.0.0.0', self.port))
            self.tcp_server.listen(5)
            logger.info(f"✅ TCP server bound to port {self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ TCP server setup failed: {e}")
            return False

    def handle_tcp_connection(self, client_socket):
        """Handle new TCP connection from EA"""
        try:
            client_socket.setblocking(False)
            addr = client_socket.getpeername()
            self.ea_connections[client_socket] = {
                'address': addr,
                'buffer': b'',
                'connected_at': time.time()
            }
            self.stats['ea_connections'] += 1
            logger.info(f"📡 EA connected from {addr} (total connections: {self.stats['ea_connections']})")
        except Exception as e:
            logger.error(f"❌ Failed to handle new connection: {e}")
            try:
                client_socket.close()
            except:
                pass

    def handle_tcp_data(self, client_socket):
        """Handle data from EA connection"""
        try:
            data = client_socket.recv(4096)

            if not data:
                # Connection closed
                addr = self.ea_connections[client_socket]['address']
                logger.info(f"🔌 EA disconnected: {addr}")
                del self.ea_connections[client_socket]
                client_socket.close()
                return

            conn_info = self.ea_connections[client_socket]
            conn_info['buffer'] += data

            # Process complete JSONL messages (terminated with \n)
            while b'\n' in conn_info['buffer']:
                line, conn_info['buffer'] = conn_info['buffer'].split(b'\n', 1)

                if line.strip():
                    try:
                        message = json.loads(line.decode('utf-8'))
                        self.stats['tcp_messages'] += 1
                        self.process_ea_message(message, client_socket)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON from EA: {e}")
                        logger.debug(f"   Data: {line[:100]}")

        except socket.error as e:
            if e.errno not in (11, 35):  # EAGAIN, EWOULDBLOCK
                logger.error(f"❌ TCP receive error: {e}")
                if client_socket in self.ea_connections:
                    del self.ea_connections[client_socket]
                try:
                    client_socket.close()
                except:
                    pass

    def process_ea_message(self, message, client_socket):
        """Process message received from EA"""
        msg_type = message.get('type', 'unknown')
        logger.info(f"📥 EA message: {msg_type}")

        # EA might send heartbeats or confirmations
        # Forward confirmations to confirm_listener via ZMQ
        if msg_type in ('confirmation', 'position_opened', 'position_closed', 'sl_hit', 'tp_hit'):
            self.forward_confirmation(message)

    def forward_confirmation(self, confirmation):
        """Forward EA confirmation to confirm_listener"""
        # TODO: Send to port 5558 or appropriate confirmation handler
        logger.info(f"📤 Confirmation: {confirmation.get('fire_id', 'NO_ID')}")

    def send_to_ea(self, command_dict, target_socket=None):
        """Send command to EA via TCP as JSONL"""
        command_json = json.dumps(command_dict, separators=(',', ':'))
        payload = (command_json + '\n').encode('utf-8')

        if target_socket:
            # Send to specific EA
            sockets = [target_socket]
        else:
            # Broadcast to all connected EAs
            sockets = list(self.ea_connections.keys())

        sent_count = 0
        for sock in sockets:
            try:
                sock.send(payload)
                sent_count += 1
                logger.info(f"📤 Sent to EA: {command_dict.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"❌ Send to EA failed: {e}")

        return sent_count > 0

    def process_ipc_commands(self):
        """Process commands from IPC queue"""
        try:
            if self.ipc_pull.poll(0):  # Non-blocking poll
                command = self.ipc_pull.recv_json(zmq.NOBLOCK)
                self.stats['commands_forwarded'] += 1

                cmd_type = command.get('type', 'unknown')
                cmd_id = command.get('fire_id') or command.get('request_ref', 'NO_ID')
                logger.info(f"📥 IPC command: {cmd_type} {cmd_id}")

                # Forward to EA
                self.send_to_ea(command)

        except zmq.Again:
            pass
        except Exception as e:
            logger.error(f"❌ IPC processing error: {e}")

    def run(self):
        """Main server loop using select()"""
        logger.info("="*70)
        logger.info("🚀 HYBRID COMMAND SERVER STARTING")
        logger.info("="*70)
        logger.info(f"TCP Server: 0.0.0.0:{self.port} (for EA connections)")
        logger.info(f"ZMQ ROUTER: tcp://*:5554 (for Brain)")
        logger.info(f"IPC PULL: {self.ipc_path}")
        logger.info("="*70)

        # Setup all endpoints
        if not self.setup_tcp_server():
            return
        if not self.setup_zmq_router():
            return
        if not self.setup_ipc_pull():
            return

        logger.info("✅ All endpoints ready")

        # Main event loop
        while self.running:
            try:
                # Build list of sockets to monitor
                read_sockets = [self.tcp_server] + list(self.ea_connections.keys())

                # Use select with timeout
                readable, _, exceptional = select.select(read_sockets, [], read_sockets, 0.1)

                # Handle TCP server (new connections)
                if self.tcp_server in readable:
                    try:
                        client_socket, addr = self.tcp_server.accept()
                        self.handle_tcp_connection(client_socket)
                    except:
                        pass

                # Handle existing EA connections
                for sock in readable:
                    if sock != self.tcp_server and sock in self.ea_connections:
                        self.handle_tcp_data(sock)

                # Handle exceptional conditions
                for sock in exceptional:
                    if sock in self.ea_connections:
                        logger.warning(f"⚠️ Exception on socket, closing")
                        del self.ea_connections[sock]
                        sock.close()

                # Process IPC commands
                self.process_ipc_commands()

            except KeyboardInterrupt:
                logger.info("\n🛑 Shutting down...")
                break
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}")
                time.sleep(1)

        # Cleanup
        self.running = False
        for sock in list(self.ea_connections.keys()):
            try:
                sock.close()
            except:
                pass
        if self.tcp_server:
            self.tcp_server.close()
        if self.zmq_router:
            self.zmq_router.close()
        if self.ipc_pull:
            self.ipc_pull.close()
        self.zmq_context.term()


if __name__ == '__main__':
    server = HybridCommandServer()
    server.run()
