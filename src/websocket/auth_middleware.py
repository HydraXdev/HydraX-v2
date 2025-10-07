#!/usr/bin/env python3
"""
WebSocket Authentication Middleware
Handles JWT authentication for Socket.IO connections
"""

from functools import wraps
from flask import request
from flask_socketio import disconnect
import logging

from src.security.jwt_manager import get_jwt_manager

logger = logging.getLogger(__name__)

class WebSocketAuth:
    """WebSocket authentication handler"""

    def __init__(self):
        self.jwt_manager = get_jwt_manager()
        # Store authenticated connections: {sid: {user_id, claims}}
        self.authenticated_sessions = {}

    def authenticate_connection(self, sid: str, token: str) -> dict:
        """
        Authenticate a WebSocket connection

        Args:
            sid: Socket.IO session ID
            token: JWT token

        Returns:
            Authentication result dictionary
        """
        try:
            # Validate token
            claims = self.jwt_manager.validate_token(token)

            # Store authenticated session
            self.authenticated_sessions[sid] = {
                'user_id': claims['sub'],
                'mission_session_id': claims.get('ms'),
                'scopes': claims.get('scopes', []),
                'claims': claims
            }

            logger.info(f"✅ Authenticated WebSocket connection {sid} for user {claims['sub']}")

            return {
                'authenticated': True,
                'user_id': claims['sub'],
                'scopes': claims.get('scopes', [])
            }

        except Exception as e:
            logger.warning(f"⚠️ WebSocket authentication failed for {sid}: {e}")
            return {
                'authenticated': False,
                'error': str(e)
            }

    def get_session_data(self, sid: str) -> dict:
        """Get authenticated session data"""
        return self.authenticated_sessions.get(sid, {})

    def is_authenticated(self, sid: str) -> bool:
        """Check if session is authenticated"""
        return sid in self.authenticated_sessions

    def has_scope(self, sid: str, required_scope: str) -> bool:
        """Check if session has required scope"""
        session = self.authenticated_sessions.get(sid, {})
        scopes = session.get('scopes', [])
        return required_scope in scopes

    def get_user_id(self, sid: str) -> str:
        """Get user ID from session"""
        session = self.authenticated_sessions.get(sid, {})
        return session.get('user_id', '')

    def disconnect_session(self, sid: str):
        """Clean up disconnected session"""
        if sid in self.authenticated_sessions:
            user_id = self.authenticated_sessions[sid]['user_id']
            del self.authenticated_sessions[sid]
            logger.info(f"✅ Cleaned up WebSocket session {sid} for user {user_id}")

    def authorize_topic(self, sid: str, topic: str) -> bool:
        """
        Authorize topic subscription for session

        Args:
            sid: Socket.IO session ID
            topic: Topic name (e.g., 'user.profile', 'mission.alert/123')

        Returns:
            True if authorized, False otherwise
        """
        session = self.authenticated_sessions.get(sid, {})
        if not session:
            return False

        user_id = session['user_id']
        mission_session_id = session.get('mission_session_id')

        # User-scoped topics
        if topic.startswith('user.'):
            return True  # User can access their own topics

        # Mission alert topics
        if topic.startswith('mission.alert/'):
            # Extract alert ID from topic
            # Topic format: mission.alert/{alert_id}
            alert_id_str = topic.split('/')[-1]
            # Allow subscription (will validate alert belongs to user's session server-side)
            return True

        # Trade topics
        if topic.startswith('trades.'):
            return True  # User can access their own trades

        # Stats topics
        if topic.startswith('stats.'):
            return True  # User can access their own stats

        # System topics
        if topic == 'system.status':
            return True  # Public system status

        # Default deny
        logger.warning(f"⚠️ Denied topic subscription: {topic} for user {user_id}")
        return False


# Global instance
_ws_auth = None

def get_ws_auth() -> WebSocketAuth:
    """Get or create global WebSocket auth instance"""
    global _ws_auth
    if _ws_auth is None:
        _ws_auth = WebSocketAuth()
    return _ws_auth


def require_ws_auth(f):
    """Decorator to require WebSocket authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ws_auth = get_ws_auth()
        sid = request.sid

        if not ws_auth.is_authenticated(sid):
            logger.warning(f"⚠️ Unauthenticated WebSocket request from {sid}")
            disconnect()
            return

        return f(*args, **kwargs)
    return decorated_function


def require_ws_scope(required_scope: str):
    """Decorator to require specific scope"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ws_auth = get_ws_auth()
            sid = request.sid

            if not ws_auth.is_authenticated(sid):
                disconnect()
                return

            if not ws_auth.has_scope(sid, required_scope):
                logger.warning(f"⚠️ Insufficient scope for {sid}: required {required_scope}")
                disconnect()
                return

            return f(*args, **kwargs)
        return decorated_function
    return decorator


if __name__ == '__main__':
    # Test
    auth = get_ws_auth()

    # Mock session
    test_sid = "test_sid_123"

    # Mock token (would come from JWT manager in real usage)
    test_token = "mock_token"

    # Test authentication
    result = auth.authenticate_connection(test_sid, test_token)
    print(f"Auth result: {result}")

    # Test topic authorization
    topics = [
        'user.profile',
        'mission.alert/123',
        'trades.open',
        'trades.delta',
        'stats.equity',
        'system.status',
        'admin.dashboard'  # Should be denied
    ]

    for topic in topics:
        authorized = auth.authorize_topic(test_sid, topic)
        print(f"Topic {topic}: {'✅ Authorized' if authorized else '❌ Denied'}")
