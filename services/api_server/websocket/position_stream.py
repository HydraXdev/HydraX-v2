"""
WebSocket position streaming
"""
import asyncio
import json
from fastapi import WebSocket
from typing import Set, Dict
import time


class PositionStreamManager:
    """Manages WebSocket connections for position updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> websockets

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client for a specific user"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket client"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_position_update(self, user_id: str, position_data: dict):
        """Broadcast position update to specific user's connections"""
        if user_id not in self.active_connections:
            return

        message = {
            "type": "position",
            "data": position_data,
            "timestamp": int(time.time())
        }

        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, user_id)

    async def broadcast_fire_update(self, user_id: str, fire_data: dict):
        """Broadcast fire execution update to specific user"""
        if user_id not in self.active_connections:
            return

        message = {
            "type": "fire",
            "data": fire_data,
            "timestamp": int(time.time())
        }

        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn, user_id)


# Global instance
position_stream_manager = PositionStreamManager()
