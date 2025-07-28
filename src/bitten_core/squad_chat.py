"""
BITTEN Squad Chat System
Real-time tactical communications for squad coordination
Features: Real-time messaging, typing indicators, squad rooms, moderation tools
"""

import os
import json
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import asyncio
import base64

from flask import Flask, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import redis
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of chat messages"""
    TEXT = "text"
    EMOJI_REACTION = "emoji_reaction"
    GIF = "gif"
    IMAGE = "image"
    FILE = "file"
    VOICE = "voice"
    SYSTEM = "system"
    TRADE_SIGNAL = "trade_signal"

class UserRole(Enum):
    """User roles in squad chat"""
    COMMANDER = "commander"
    SERGEANT = "sergeant"
    CORPORAL = "corporal"
    RECRUIT = "recruit"
    OBSERVER = "observer"

class ModerationAction(Enum):
    """Moderation actions available"""
    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"
    REPORT = "report"
    WARN = "warn"

@dataclass
class ChatUser:
    """User in the chat system"""
    user_id: str
    username: str
    callsign: str
    role: UserRole
    squad_id: str
    rank: str
    is_online: bool = False
    last_seen: Optional[datetime] = None
    is_typing: bool = False
    typing_timeout: Optional[datetime] = None
    muted_until: Optional[datetime] = None
    permissions: Set[str] = field(default_factory=set)

@dataclass
class ChatMessage:
    """Chat message structure"""
    message_id: str
    user_id: str
    username: str
    callsign: str
    squad_id: str
    room_id: str
    content: str
    message_type: MessageType
    timestamp: datetime
    edited: bool = False
    edited_at: Optional[datetime] = None
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> user_ids
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    encrypted: bool = False

@dataclass
class ChatRoom:
    """Chat room configuration"""
    room_id: str
    squad_id: str
    name: str
    description: str
    is_secure: bool = False
    max_members: int = 50
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    members: Set[str] = field(default_factory=set)
    moderators: Set[str] = field(default_factory=set)
    archived: bool = False

class SquadChatSystem:
    """Main squad chat system using Flask-SocketIO"""
    
    def __init__(self, app: Flask = None, redis_url: str = "redis://localhost:6379"):
        self.app = app
        self.socketio = None
        self.redis_client = None
        self.encryption_key = None
        
        # In-memory stores
        self.active_users: Dict[str, ChatUser] = {}
        self.chat_rooms: Dict[str, ChatRoom] = {}
        self.recent_messages: Dict[str, List[ChatMessage]] = {}
        self.typing_users: Dict[str, Set[str]] = {}  # room_id -> user_ids
        
        # Data directories
        self.data_dir = Path("data/squad_chat")
        self.message_archive_dir = self.data_dir / "messages"
        self.user_data_dir = self.data_dir / "users"
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.message_archive_dir.mkdir(parents=True, exist_ok=True)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self._init_encryption()
        
        # Initialize Redis
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.info("Connected to Redis for chat system")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory store: {e}")
            self.redis_client = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app"""
        self.app = app
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='eventlet',
            logger=True,
            engineio_logger=False
        )
        
        # Register socket event handlers
        self._register_socket_events()
        
        # Load existing data
        self._load_chat_data()
        
        # Setup cleanup tasks
        self._schedule_cleanup_tasks()
    
    def _init_encryption(self):
        """Initialize encryption for secure messages"""
        key_file = self.data_dir / "chat_encryption.key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)
        
        self.cipher = Fernet(self.encryption_key)
    
    def _register_socket_events(self):
        """Register all socket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle user connection"""
            user_id = session.get('user_id')
            if not user_id:
                logger.warning("Connection rejected: No user_id in session")
                return False
            
            logger.info(f"User {user_id} connected to chat")
            
            # Update user status
            if user_id in self.active_users:
                self.active_users[user_id].is_online = True
                self.active_users[user_id].last_seen = datetime.now()
            
            emit('connection_confirmed', {
                'status': 'connected',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle user disconnection"""
            user_id = session.get('user_id')
            if user_id and user_id in self.active_users:
                self.active_users[user_id].is_online = False
                self.active_users[user_id].last_seen = datetime.now()
                
                # Remove from typing indicators
                self._clear_user_typing(user_id)
                
                logger.info(f"User {user_id} disconnected from chat")
        
        @self.socketio.on('join_squad_room')
        def handle_join_room(data):
            """Handle joining a squad room"""
            user_id = session.get('user_id')
            squad_id = data.get('squad_id')
            
            if not user_id or not squad_id:
                emit('error', {'message': 'Invalid join request'})
                return
            
            # Verify user can join this squad
            if not self._can_user_join_squad(user_id, squad_id):
                emit('error', {'message': 'Access denied to squad'})
                return
            
            room_id = f"squad_{squad_id}"
            join_room(room_id)
            
            # Send recent messages
            recent_messages = self._get_recent_messages(room_id, limit=50)
            emit('room_history', {
                'room_id': room_id,
                'messages': [self._serialize_message(msg) for msg in recent_messages]
            })
            
            # Notify room of new member
            emit('user_joined', {
                'user_id': user_id,
                'username': self.active_users[user_id].username if user_id in self.active_users else 'Unknown',
                'timestamp': datetime.now().isoformat()
            }, room=room_id)
            
            logger.info(f"User {user_id} joined squad room {squad_id}")
        
        @self.socketio.on('send_message')
        def handle_send_message(data):
            """Handle sending a message"""
            user_id = session.get('user_id')
            if not user_id or user_id not in self.active_users:
                emit('error', {'message': 'Not authenticated'})
                return
            
            user = self.active_users[user_id]
            
            # Check if user is muted
            if user.muted_until and datetime.now() < user.muted_until:
                emit('error', {'message': 'You are muted'})
                return
            
            # Validate message data
            room_id = data.get('room_id')
            content = data.get('content', '').strip()
            message_type = MessageType(data.get('type', 'text'))
            
            if not room_id or not content:
                emit('error', {'message': 'Invalid message data'})
                return
            
            # Check message length
            if len(content) > 2000:
                emit('error', {'message': 'Message too long (max 2000 characters)'})
                return
            
            # Create message
            message = ChatMessage(
                message_id=str(uuid.uuid4()),
                user_id=user_id,
                username=user.username,
                callsign=user.callsign,
                squad_id=user.squad_id,
                room_id=room_id,
                content=content,
                message_type=message_type,
                timestamp=datetime.now(),
                reply_to=data.get('reply_to'),
                metadata=data.get('metadata', {})
            )
            
            # Encrypt if secure room
            if room_id in self.chat_rooms and self.chat_rooms[room_id].is_secure:
                message.content = self._encrypt_content(message.content)
                message.encrypted = True
            
            # Store message
            self._store_message(message)
            
            # Broadcast to room
            emit('new_message', self._serialize_message(message), room=room_id)
            
            # Clear typing indicator
            self._clear_user_typing_in_room(user_id, room_id)
            
            logger.info(f"Message sent by {user_id} in room {room_id}")
        
        @self.socketio.on('typing_start')
        def handle_typing_start(data):
            """Handle typing indicator start"""
            user_id = session.get('user_id')
            room_id = data.get('room_id')
            
            if not user_id or not room_id:
                return
            
            # Add to typing users
            if room_id not in self.typing_users:
                self.typing_users[room_id] = set()
            
            self.typing_users[room_id].add(user_id)
            
            # Set timeout
            if user_id in self.active_users:
                self.active_users[user_id].is_typing = True
                self.active_users[user_id].typing_timeout = datetime.now() + timedelta(seconds=5)
            
            # Broadcast typing indicator
            emit('user_typing', {
                'user_id': user_id,
                'username': self.active_users[user_id].username if user_id in self.active_users else 'Unknown',
                'room_id': room_id
            }, room=room_id, include_self=False)
        
        @self.socketio.on('typing_stop')
        def handle_typing_stop(data):
            """Handle typing indicator stop"""
            user_id = session.get('user_id')
            room_id = data.get('room_id')
            
            if not user_id or not room_id:
                return
            
            self._clear_user_typing_in_room(user_id, room_id)
        
        @self.socketio.on('add_reaction')
        def handle_add_reaction(data):
            """Handle emoji reaction"""
            user_id = session.get('user_id')
            message_id = data.get('message_id')
            emoji = data.get('emoji')
            
            if not user_id or not message_id or not emoji:
                emit('error', {'message': 'Invalid reaction data'})
                return
            
            # Find and update message
            message = self._find_message(message_id)
            if not message:
                emit('error', {'message': 'Message not found'})
                return
            
            # Add reaction
            if emoji not in message.reactions:
                message.reactions[emoji] = []
            
            if user_id not in message.reactions[emoji]:
                message.reactions[emoji].append(user_id)
                
                # Store updated message
                self._store_message(message)
                
                # Broadcast reaction
                emit('reaction_added', {
                    'message_id': message_id,
                    'emoji': emoji,
                    'user_id': user_id,
                    'reactions': message.reactions
                }, room=message.room_id)
        
        @self.socketio.on('moderate_user')
        def handle_moderate_user(data):
            """Handle moderation actions"""
            moderator_id = session.get('user_id')
            target_user_id = data.get('target_user_id')
            action = data.get('action')
            duration = data.get('duration', 300)  # Default 5 minutes
            reason = data.get('reason', 'No reason provided')
            
            if not moderator_id or not target_user_id or not action:
                emit('error', {'message': 'Invalid moderation request'})
                return
            
            # Check moderator permissions
            if not self._has_moderation_permission(moderator_id):
                emit('error', {'message': 'Insufficient permissions'})
                return
            
            # Apply moderation action
            success = self._apply_moderation_action(
                moderator_id, target_user_id, action, duration, reason
            )
            
            if success:
                emit('moderation_applied', {
                    'action': action,
                    'target_user_id': target_user_id,
                    'moderator_id': moderator_id,
                    'reason': reason,
                    'duration': duration
                })
                
                logger.info(f"Moderation action {action} applied by {moderator_id} on {target_user_id}")
            else:
                emit('error', {'message': 'Failed to apply moderation action'})
    
    def _can_user_join_squad(self, user_id: str, squad_id: str) -> bool:
        """Check if user can join a squad room"""
        if user_id not in self.active_users:
            return False
        
        user = self.active_users[user_id]
        return user.squad_id == squad_id or user.role in [UserRole.COMMANDER, UserRole.SERGEANT]
    
    def _get_recent_messages(self, room_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get recent messages for a room"""
        if room_id not in self.recent_messages:
            return []
        
        messages = self.recent_messages[room_id]
        return messages[-limit:] if len(messages) > limit else messages
    
    def _store_message(self, message: ChatMessage):
        """Store message in memory and persistent storage"""
        room_id = message.room_id
        
        # Store in memory
        if room_id not in self.recent_messages:
            self.recent_messages[room_id] = []
        
        self.recent_messages[room_id].append(message)
        
        # Keep only recent messages in memory (last 100 per room)
        if len(self.recent_messages[room_id]) > 100:
            self.recent_messages[room_id] = self.recent_messages[room_id][-100:]
        
        # Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.lpush(
                    f"chat_messages:{room_id}",
                    json.dumps(asdict(message), default=str)
                )
                self.redis_client.ltrim(f"chat_messages:{room_id}", 0, 999)  # Keep last 1000
            except Exception as e:
                logger.error(f"Failed to store message in Redis: {e}")
        
        # Archive daily messages to files
        self._archive_message(message)
    
    def _archive_message(self, message: ChatMessage):
        """Archive message to daily file"""
        try:
            date_str = message.timestamp.strftime("%Y-%m-%d")
            archive_file = self.message_archive_dir / f"{message.room_id}_{date_str}.jsonl"
            
            with open(archive_file, 'a') as f:
                f.write(json.dumps(asdict(message), default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to archive message: {e}")
    
    def _find_message(self, message_id: str) -> Optional[ChatMessage]:
        """Find message by ID in recent messages"""
        for room_messages in self.recent_messages.values():
            for message in room_messages:
                if message.message_id == message_id:
                    return message
        return None
    
    def _serialize_message(self, message: ChatMessage) -> Dict[str, Any]:
        """Serialize message for client"""
        data = asdict(message)
        
        # Convert datetime to ISO string
        data['timestamp'] = message.timestamp.isoformat()
        if message.edited_at:
            data['edited_at'] = message.edited_at.isoformat()
        
        # Decrypt content if encrypted
        if message.encrypted:
            try:
                data['content'] = self._decrypt_content(message.content)
            except Exception as e:
                logger.error(f"Failed to decrypt message: {e}")
                data['content'] = "[Encrypted message - decryption failed]"
        
        return data
    
    def _encrypt_content(self, content: str) -> str:
        """Encrypt message content"""
        return base64.b64encode(self.cipher.encrypt(content.encode())).decode()
    
    def _decrypt_content(self, encrypted_content: str) -> str:
        """Decrypt message content"""
        return self.cipher.decrypt(base64.b64decode(encrypted_content)).decode()
    
    def _clear_user_typing(self, user_id: str):
        """Clear typing indicator for user across all rooms"""
        for room_id in list(self.typing_users.keys()):
            if user_id in self.typing_users[room_id]:
                self.typing_users[room_id].remove(user_id)
                
                # Broadcast typing stopped
                self.socketio.emit('user_stopped_typing', {
                    'user_id': user_id,
                    'room_id': room_id
                }, room=room_id)
        
        # Clear user typing status
        if user_id in self.active_users:
            self.active_users[user_id].is_typing = False
            self.active_users[user_id].typing_timeout = None
    
    def _clear_user_typing_in_room(self, user_id: str, room_id: str):
        """Clear typing indicator for user in specific room"""
        if room_id in self.typing_users and user_id in self.typing_users[room_id]:
            self.typing_users[room_id].remove(user_id)
            
            # Broadcast typing stopped
            self.socketio.emit('user_stopped_typing', {
                'user_id': user_id,
                'room_id': room_id
            }, room=room_id)
        
        # Clear user typing status
        if user_id in self.active_users:
            self.active_users[user_id].is_typing = False
            self.active_users[user_id].typing_timeout = None
    
    def _has_moderation_permission(self, user_id: str) -> bool:
        """Check if user has moderation permissions"""
        if user_id not in self.active_users:
            return False
        
        user = self.active_users[user_id]
        return user.role in [UserRole.COMMANDER, UserRole.SERGEANT]
    
    def _apply_moderation_action(
        self,
        moderator_id: str,
        target_user_id: str,
        action: str,
        duration: int,
        reason: str
    ) -> bool:
        """Apply moderation action"""
        try:
            if target_user_id not in self.active_users:
                return False
            
            target_user = self.active_users[target_user_id]
            
            if action == ModerationAction.MUTE.value:
                target_user.muted_until = datetime.now() + timedelta(seconds=duration)
                
                # Notify target user
                self.socketio.emit('moderation_notice', {
                    'action': 'muted',
                    'duration': duration,
                    'reason': reason,
                    'moderator': self.active_users[moderator_id].username
                }, room=target_user_id)
                
            elif action == ModerationAction.KICK.value:
                # Remove from all rooms
                for room_id in rooms(target_user_id):
                    leave_room(room_id, sid=target_user_id)
                
                # Disconnect user
                self.socketio.disconnect(target_user_id)
                
            elif action == ModerationAction.REPORT.value:
                # Log report for admin review
                self._log_user_report(moderator_id, target_user_id, reason)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply moderation action: {e}")
            return False
    
    def _log_user_report(self, reporter_id: str, reported_id: str, reason: str):
        """Log user report"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'reporter_id': reporter_id,
            'reported_id': reported_id,
            'reason': reason
        }
        
        reports_file = self.data_dir / "user_reports.jsonl"
        with open(reports_file, 'a') as f:
            f.write(json.dumps(report_data) + '\n')
    
    def _load_chat_data(self):
        """Load existing chat data"""
        # Load users
        try:
            users_file = self.data_dir / "users.json"
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                    
                for user_data in users_data:
                    user = ChatUser(
                        user_id=user_data['user_id'],
                        username=user_data['username'],
                        callsign=user_data['callsign'],
                        role=UserRole(user_data['role']),
                        squad_id=user_data['squad_id'],
                        rank=user_data['rank'],
                        permissions=set(user_data.get('permissions', []))
                    )
                    self.active_users[user.user_id] = user
        except Exception as e:
            logger.error(f"Failed to load user data: {e}")
        
        # Load rooms
        try:
            rooms_file = self.data_dir / "rooms.json"
            if rooms_file.exists():
                with open(rooms_file, 'r') as f:
                    rooms_data = json.load(f)
                    
                for room_data in rooms_data:
                    room = ChatRoom(
                        room_id=room_data['room_id'],
                        squad_id=room_data['squad_id'],
                        name=room_data['name'],
                        description=room_data['description'],
                        is_secure=room_data.get('is_secure', False),
                        max_members=room_data.get('max_members', 50),
                        created_at=datetime.fromisoformat(room_data['created_at']),
                        created_by=room_data['created_by'],
                        members=set(room_data.get('members', [])),
                        moderators=set(room_data.get('moderators', []))
                    )
                    self.chat_rooms[room.room_id] = room
        except Exception as e:
            logger.error(f"Failed to load room data: {e}")
    
    def _schedule_cleanup_tasks(self):
        """Schedule periodic cleanup tasks"""
        def cleanup_typing_timeouts():
            """Clean up expired typing indicators"""
            current_time = datetime.now()
            
            for user_id, user in self.active_users.items():
                if (user.is_typing and user.typing_timeout and 
                    current_time > user.typing_timeout):
                    self._clear_user_typing(user_id)
        
        # Schedule cleanup every 10 seconds
        self.socketio.start_background_task(self._periodic_cleanup, cleanup_typing_timeouts, 10)
    
    def _periodic_cleanup(self, cleanup_func, interval_seconds):
        """Run periodic cleanup"""
        while True:
            try:
                cleanup_func()
                self.socketio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                self.socketio.sleep(interval_seconds)
    
    # Public API methods
    
    def register_user(
        self,
        user_id: str,
        username: str,
        callsign: str,
        role: UserRole,
        squad_id: str,
        rank: str
    ) -> bool:
        """Register a new user in the chat system"""
        try:
            user = ChatUser(
                user_id=user_id,
                username=username,
                callsign=callsign,
                role=role,
                squad_id=squad_id,
                rank=rank
            )
            
            self.active_users[user_id] = user
            
            # Save to persistent storage
            self._save_users()
            
            logger.info(f"Registered user {username} ({callsign}) in chat system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            return False
    
    def create_squad_room(
        self,
        squad_id: str,
        name: str,
        description: str,
        created_by: str,
        is_secure: bool = False
    ) -> Optional[str]:
        """Create a new squad chat room"""
        try:
            room_id = f"squad_{squad_id}_{len(self.chat_rooms)}"
            
            room = ChatRoom(
                room_id=room_id,
                squad_id=squad_id,
                name=name,
                description=description,
                is_secure=is_secure,
                created_by=created_by
            )
            
            self.chat_rooms[room_id] = room
            
            # Save to persistent storage
            self._save_rooms()
            
            logger.info(f"Created squad room {name} for squad {squad_id}")
            return room_id
            
        except Exception as e:
            logger.error(f"Failed to create squad room: {e}")
            return None
    
    def send_system_message(
        self,
        room_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Send a system message to a room"""
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            user_id="SYSTEM",
            username="BITTEN Command",
            callsign="HQ",
            squad_id="SYSTEM",
            room_id=room_id,
            content=content,
            message_type=MessageType.SYSTEM,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self._store_message(message)
        
        if self.socketio:
            self.socketio.emit('new_message', self._serialize_message(message), room=room_id)
    
    def _save_users(self):
        """Save users to persistent storage"""
        try:
            users_data = []
            for user in self.active_users.values():
                users_data.append({
                    'user_id': user.user_id,
                    'username': user.username,
                    'callsign': user.callsign,
                    'role': user.role.value,
                    'squad_id': user.squad_id,
                    'rank': user.rank,
                    'permissions': list(user.permissions)
                })
            
            with open(self.data_dir / "users.json", 'w') as f:
                json.dump(users_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
    
    def _save_rooms(self):
        """Save rooms to persistent storage"""
        try:
            rooms_data = []
            for room in self.chat_rooms.values():
                rooms_data.append({
                    'room_id': room.room_id,
                    'squad_id': room.squad_id,
                    'name': room.name,
                    'description': room.description,
                    'is_secure': room.is_secure,
                    'max_members': room.max_members,
                    'created_at': room.created_at.isoformat(),
                    'created_by': room.created_by,
                    'members': list(room.members),
                    'moderators': list(room.moderators)
                })
            
            with open(self.data_dir / "rooms.json", 'w') as f:
                json.dump(rooms_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save rooms: {e}")

# Example integration with Flask app
if __name__ == "__main__":
    from flask import Flask, render_template, session, request
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Initialize chat system
    chat_system = SquadChatSystem(app)
    
    @app.route('/')
    def index():
        return render_template('squad_chat_widget.html')
    
    @app.route('/api/join_chat', methods=['POST'])
    def join_chat():
        """API endpoint to join chat"""
        data = request.json
        
        user_id = data.get('user_id')
        username = data.get('username')
        callsign = data.get('callsign', username)
        squad_id = data.get('squad_id')
        role = UserRole(data.get('role', 'recruit'))
        rank = data.get('rank', 'RECRUIT')
        
        if not all([user_id, username, squad_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Register user
        success = chat_system.register_user(user_id, username, callsign, role, squad_id, rank)
        
        if success:
            session['user_id'] = user_id
            return jsonify({'status': 'success', 'message': 'Ready to join chat'})
        else:
            return jsonify({'error': 'Failed to register user'}), 500
    
    if __name__ == '__main__':
        chat_system.socketio.run(app, debug=True, host='0.0.0.0', port=5000)