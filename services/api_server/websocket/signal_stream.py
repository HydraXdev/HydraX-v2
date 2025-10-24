"""
WebSocket signal streaming
"""
import asyncio
import json
from fastapi import WebSocket
from typing import Set
import time


class SignalStreamManager:
    """Manages WebSocket connections for signal streaming"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        self.active_connections.discard(websocket)

    async def broadcast_signal(self, signal_data: dict):
        """Broadcast signal to all connected clients"""
        message = {
            "type": "signal",
            "data": signal_data,
            "timestamp": int(time.time())
        }

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_heartbeat(self):
        """Send periodic heartbeat to keep connections alive"""
        while True:
            await asyncio.sleep(30)
            message = {
                "type": "heartbeat",
                "timestamp": int(time.time())
            }

            disconnected = set()
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)

            for conn in disconnected:
                self.disconnect(conn)


# Global instance
signal_stream_manager = SignalStreamManager()
