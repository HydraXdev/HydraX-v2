"""
BITTEN Chat Integration Module
Connects squad chat system with existing BITTEN infrastructure
Handles user authentication, permissions, and data synchronization
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from flask import Flask, request, session, jsonify, render_template
from flask_socketio import SocketIO

from .squad_chat import SquadChatSystem, UserRole, ChatUser
from .chat_notifications import ChatNotificationService, NotificationType, NotificationPriority
from .user_profile import UserProfile  # Assuming this exists in BITTEN
from .squad_radar import SquadRadar
from .tier_lock_manager import TierLockManager  # Assuming this exists
from .security_utils import SecurityUtils  # Assuming this exists

logger = logging.getLogger(__name__)

class ChatIntegration:
    """Integrates chat system with BITTEN infrastructure"""
    
    def __init__(
        self,
        app: Flask,
        user_profile_manager=None,
        tier_lock_manager=None,
        squad_radar=None,
        security_utils=None
    ):
        self.app = app
        self.chat_system = None
        self.notification_service = None
        
        # External dependencies
        self.user_profile_manager = user_profile_manager
        self.tier_lock_manager = tier_lock_manager
        self.squad_radar = squad_radar
        self.security_utils = security_utils
        
        # Configuration
        self.config = self._load_config()
        
        # Initialize systems
        self._initialize_chat_systems()
        self._register_flask_routes()
        self._setup_integration_hooks()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load chat integration configuration"""
        config_file = Path("config/chat_integration.json")
        
        default_config = {
            "chat_features": {
                "max_message_length": 2000,
                "max_file_size_mb": 10,
                "allowed_file_types": [
                    "image/png", "image/jpeg", "image/gif", "image/webp",
                    "application/pdf", "text/plain", "application/zip"
                ],
                "rate_limit_messages_per_minute": 30,
                "enable_voice_messages": True,
                "enable_gif_search": True,
                "enable_encryption": True
            },
            "permissions": {
                "create_rooms": ["commander", "sergeant"],
                "moderate_users": ["commander", "sergeant"],
                "delete_messages": ["commander", "sergeant"],
                "kick_users": ["commander", "sergeant"],
                "ban_users": ["commander"],
                "access_chat_history": ["commander", "sergeant", "corporal"]
            },
            "notification_settings": {
                "email_enabled": True,
                "push_enabled": True,
                "telegram_enabled": True,
                "quiet_hours_default": {
                    "start": "22:00",
                    "end": "08:00"
                }
            },
            "squad_integration": {
                "auto_create_rooms": True,
                "sync_with_squad_radar": True,
                "share_trading_signals": True,
                "enable_squad_leaderboards": True
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.error(f"Failed to load chat config: {e}")
        
        return default_config
    
    def _initialize_chat_systems(self):
        """Initialize chat and notification systems"""
        try:
            # Initialize chat system
            self.chat_system = SquadChatSystem(
                app=self.app,
                redis_url=self.config.get('redis_url', 'redis://localhost:6379')
            )
            
            # Initialize notification service
            self.notification_service = ChatNotificationService(
                redis_url=self.config.get('redis_url', 'redis://localhost:6379'),
                email_config=self.config.get('email_config'),
                telegram_config=self.config.get('telegram_config')
            )
            
            logger.info("Chat systems initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize chat systems: {e}")
            raise
    
    def _register_flask_routes(self):
        """Register Flask routes for chat functionality"""
        
        @self.app.route('/api/chat/join', methods=['POST'])
        def join_chat():
            """Join chat system"""
            try:
                data = request.json
                user_id = data.get('user_id')
                
                if not user_id:
                    return jsonify({'error': 'User ID required'}), 400
                
                # Get user data from BITTEN system
                user_data = self._get_user_data(user_id)
                if not user_data:
                    return jsonify({'error': 'User not found'}), 404
                
                # Check if user has chat access
                if not self._has_chat_access(user_data):
                    return jsonify({'error': 'Chat access denied'}), 403
                
                # Register user in chat system
                success = self.chat_system.register_user(
                    user_id=user_id,
                    username=user_data['username'],
                    callsign=user_data['callsign'],
                    role=UserRole(user_data['role']),
                    squad_id=user_data['squad_id'],
                    rank=user_data['rank']
                )
                
                if not success:
                    return jsonify({'error': 'Failed to register user'}), 500
                
                # Register for notifications
                self.notification_service.register_user(
                    user_id=user_id,
                    email=user_data.get('email'),
                    phone=user_data.get('phone'),
                    telegram_chat_id=user_data.get('telegram_chat_id')
                )
                
                # Create/join squad room
                squad_room_id = self._ensure_squad_room(user_data['squad_id'], user_id)
                
                # Set session data
                session['user_id'] = user_id
                session['chat_active'] = True
                
                return jsonify({
                    'status': 'success',
                    'room_id': squad_room_id,
                    'user_data': {
                        'username': user_data['username'],
                        'callsign': user_data['callsign'],
                        'role': user_data['role'],
                        'rank': user_data['rank']
                    }
                })
                
            except Exception as e:
                logger.error(f"Chat join error: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/api/chat/upload', methods=['POST'])
        def upload_file():
            """Handle file uploads for chat"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'error': 'Not authenticated'}), 401
                
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                
                file = request.files['file']
                room_id = request.form.get('room_id')
                
                if not file or not room_id:
                    return jsonify({'error': 'File and room_id required'}), 400
                
                # Validate file
                if not self._validate_file(file):
                    return jsonify({'error': 'Invalid file'}), 400
                
                # Save file and get URL
                file_url = self._save_uploaded_file(file, user_id, room_id)
                
                if not file_url:
                    return jsonify({'error': 'Failed to save file'}), 500
                
                return jsonify({
                    'status': 'success',
                    'file_url': file_url,
                    'filename': file.filename
                })
                
            except Exception as e:
                logger.error(f"File upload error: {e}")
                return jsonify({'error': 'Upload failed'}), 500
        
        @self.app.route('/api/chat/notifications')
        def get_notifications():
            """Get user notifications"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'error': 'Not authenticated'}), 401
                
                notifications = self.notification_service.get_user_notifications(user_id)
                unread_count = self.notification_service.get_unread_count(user_id)
                
                return jsonify({
                    'notifications': [
                        {
                            'id': n.notification_id,
                            'type': n.notification_type.value,
                            'title': n.title,
                            'message': n.message,
                            'priority': n.priority.value,
                            'created_at': n.created_at.isoformat(),
                            'read': n.metadata.get('read', False)
                        } for n in notifications
                    ],
                    'unread_count': unread_count
                })
                
            except Exception as e:
                logger.error(f"Get notifications error: {e}")
                return jsonify({'error': 'Failed to get notifications'}), 500
        
        @self.app.route('/api/chat/notifications/mark_read', methods=['POST'])
        def mark_notifications_read():
            """Mark notifications as read"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'error': 'Not authenticated'}), 401
                
                data = request.json
                notification_ids = data.get('notification_ids', [])
                
                self.notification_service.mark_notifications_read(
                    user_id, notification_ids
                )
                
                return jsonify({'status': 'success'})
                
            except Exception as e:
                logger.error(f"Mark notifications read error: {e}")
                return jsonify({'error': 'Failed to mark as read'}), 500
        
        @self.app.route('/api/chat/settings', methods=['GET', 'POST'])
        def chat_settings():
            """Get or update chat settings"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'error': 'Not authenticated'}), 401
                
                if request.method == 'GET':
                    settings = self.notification_service.notification_settings.get(user_id)
                    if settings:
                        return jsonify({
                            'enabled_types': [t.value for t in settings.enabled_types],
                            'quiet_hours_start': settings.quiet_hours_start,
                            'quiet_hours_end': settings.quiet_hours_end,
                            'mention_keywords': settings.mention_keywords,
                            'email_address': settings.email_address
                        })
                    else:
                        return jsonify({'error': 'Settings not found'}), 404
                
                elif request.method == 'POST':
                    data = request.json
                    
                    # Update settings
                    self.notification_service.update_user_settings(
                        user_id=user_id,
                        **data
                    )
                    
                    return jsonify({'status': 'success'})
                
            except Exception as e:
                logger.error(f"Chat settings error: {e}")
                return jsonify({'error': 'Settings operation failed'}), 500
        
        @self.app.route('/chat')
        def chat_page():
            """Render chat interface page"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return redirect('/login')
                
                user_data = self._get_user_data(user_id)
                if not user_data or not self._has_chat_access(user_data):
                    return render_template('access_denied.html')
                
                return render_template('squad_chat_widget.html', user_data=user_data)
                
            except Exception as e:
                logger.error(f"Chat page error: {e}")
                return render_template('error.html', error="Failed to load chat")
    
    def _setup_integration_hooks(self):
        """Setup hooks to integrate with existing BITTEN systems"""
        
        # Hook into trading signal system
        if hasattr(self.app, 'signal_system'):
            self._setup_trading_signal_hooks()
        
        # Hook into squad radar
        if self.squad_radar:
            self._setup_squad_radar_hooks()
        
        # Hook into achievement system
        if hasattr(self.app, 'achievement_system'):
            self._setup_achievement_hooks()
    
    def _setup_trading_signal_hooks(self):
        """Setup hooks for trading signal integration"""
        try:
            # When a signal is generated, share it in squad chat
            def on_signal_generated(signal_data):
                try:
                    user_id = signal_data.get('user_id')
                    if not user_id:
                        return
                    
                    user_data = self._get_user_data(user_id)
                    if not user_data:
                        return
                    
                    squad_room_id = f"squad_{user_data['squad_id']}"
                    
                    # Create signal message
                    signal_message = self._format_trading_signal(signal_data)
                    
                    # Send to squad chat
                    self.chat_system.send_system_message(
                        room_id=squad_room_id,
                        content=signal_message,
                        metadata={
                            'type': 'trading_signal',
                            'signal_data': signal_data
                        }
                    )
                    
                    # Create notifications for squad members
                    squad_members = self._get_squad_members(user_data['squad_id'])
                    
                    self.notification_service.create_squad_notification(
                        squad_id=user_data['squad_id'],
                        user_ids=squad_members,
                        title="New Trading Signal",
                        message=f"Signal: {signal_data.get('pair', 'Unknown')} {signal_data.get('direction', '')}",
                        notification_type=NotificationType.SYSTEM_ALERT,
                        priority=NotificationPriority.HIGH,
                        exclude_user_id=user_id,
                        source_room_id=squad_room_id,
                        metadata={'signal_data': signal_data}
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process signal for chat: {e}")
            
            # Register the hook (pseudo-code, actual implementation would depend on signal system)
            # self.app.signal_system.on_signal_generated(on_signal_generated)
            
        except Exception as e:
            logger.error(f"Failed to setup trading signal hooks: {e}")
    
    def _setup_squad_radar_hooks(self):
        """Setup hooks for squad radar integration"""
        try:
            # When squad radar detects interesting activity, share in chat
            def on_squad_activity(activity_data):
                try:
                    squad_id = activity_data.get('squad_id')
                    if not squad_id:
                        return
                    
                    squad_room_id = f"squad_{squad_id}"
                    activity_message = self._format_squad_activity(activity_data)
                    
                    self.chat_system.send_system_message(
                        room_id=squad_room_id,
                        content=activity_message,
                        metadata={
                            'type': 'squad_activity',
                            'activity_data': activity_data
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process squad activity for chat: {e}")
            
            # Register the hook
            # self.squad_radar.on_activity_detected(on_squad_activity)
            
        except Exception as e:
            logger.error(f"Failed to setup squad radar hooks: {e}")
    
    def _setup_achievement_hooks(self):
        """Setup hooks for achievement system integration"""
        try:
            # When user earns achievement, announce in squad chat
            def on_achievement_earned(achievement_data):
                try:
                    user_id = achievement_data.get('user_id')
                    achievement_name = achievement_data.get('name')
                    
                    if not user_id or not achievement_name:
                        return
                    
                    user_data = self._get_user_data(user_id)
                    if not user_data:
                        return
                    
                    squad_room_id = f"squad_{user_data['squad_id']}"
                    
                    achievement_message = f"🏆 {user_data['callsign']} earned achievement: {achievement_name}!"
                    
                    self.chat_system.send_system_message(
                        room_id=squad_room_id,
                        content=achievement_message,
                        metadata={
                            'type': 'achievement',
                            'achievement_data': achievement_data
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process achievement for chat: {e}")
            
            # Register the hook
            # self.app.achievement_system.on_achievement_earned(on_achievement_earned)
            
        except Exception as e:
            logger.error(f"Failed to setup achievement hooks: {e}")
    
    def _get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from BITTEN user profile system"""
        try:
            if self.user_profile_manager:
                profile = self.user_profile_manager.get_profile(user_id)
                if profile:
                    return {
                        'user_id': user_id,
                        'username': profile.username,
                        'callsign': profile.callsign or profile.username,
                        'role': profile.role,
                        'rank': profile.rank,
                        'squad_id': profile.squad_id or 'default',
                        'tier': profile.tier,
                        'email': profile.email,
                        'phone': profile.phone,
                        'telegram_chat_id': profile.telegram_chat_id
                    }
            
            # Fallback to session or default data
            return {
                'user_id': user_id,
                'username': f'User_{user_id[:6]}',
                'callsign': f'ALPHA-{user_id[:3].upper()}',
                'role': 'recruit',
                'rank': 'RECRUIT',
                'squad_id': 'default',
                'tier': 'basic'
            }
            
        except Exception as e:
            logger.error(f"Failed to get user data for {user_id}: {e}")
            return None
    
    def _has_chat_access(self, user_data: Dict[str, Any]) -> bool:
        """Check if user has access to chat system"""
        try:
            # Check tier requirements
            if self.tier_lock_manager:
                required_tier = self.config.get('required_tier', 'basic')
                if not self.tier_lock_manager.has_access(user_data['user_id'], required_tier):
                    return False
            
            # Check other access requirements
            return True
            
        except Exception as e:
            logger.error(f"Failed to check chat access: {e}")
            return False
    
    def _ensure_squad_room(self, squad_id: str, creator_id: str) -> str:
        """Ensure squad room exists, create if needed"""
        try:
            room_id = f"squad_{squad_id}"
            
            # Check if room already exists
            if room_id in self.chat_system.chat_rooms:
                return room_id
            
            # Create new squad room
            created_room_id = self.chat_system.create_squad_room(
                squad_id=squad_id,
                name=f"Squad {squad_id.upper()} Command",
                description=f"Tactical communications for Squad {squad_id.upper()}",
                created_by=creator_id,
                is_secure=self.config['chat_features']['enable_encryption']
            )
            
            if created_room_id:
                # Send welcome message
                self.chat_system.send_system_message(
                    room_id=created_room_id,
                    content=f"🎯 Squad {squad_id.upper()} tactical channel established. Welcome, operatives!",
                    metadata={'type': 'room_created'}
                )
                
                return created_room_id
            
            return room_id
            
        except Exception as e:
            logger.error(f"Failed to ensure squad room: {e}")
            return f"squad_{squad_id}"
    
    def _get_squad_members(self, squad_id: str) -> List[str]:
        """Get list of squad member user IDs"""
        try:
            if self.user_profile_manager:
                return self.user_profile_manager.get_squad_members(squad_id)
            
            # Fallback: get from chat system
            room_id = f"squad_{squad_id}"
            if room_id in self.chat_system.chat_rooms:
                return list(self.chat_system.chat_rooms[room_id].members)
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get squad members: {e}")
            return []
    
    def _validate_file(self, file) -> bool:
        """Validate uploaded file"""
        try:
            # Check file size
            max_size = self.config['chat_features']['max_file_size_mb'] * 1024 * 1024
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset position
            
            if size > max_size:
                return False
            
            # Check file type
            allowed_types = self.config['chat_features']['allowed_file_types']
            if file.content_type not in allowed_types:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False
    
    def _save_uploaded_file(self, file, user_id: str, room_id: str) -> Optional[str]:
        """Save uploaded file and return URL"""
        try:
            # Create upload directory
            upload_dir = Path(f"data/chat_uploads/{room_id}")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{user_id}_{timestamp}_{file.filename}"
            file_path = upload_dir / filename
            
            # Save file
            file.save(str(file_path))
            
            # Return URL
            return f"/chat/files/{room_id}/{filename}"
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return None
    
    def _format_trading_signal(self, signal_data: Dict[str, Any]) -> str:
        """Format trading signal for chat display"""
        try:
            pair = signal_data.get('pair', 'Unknown')
            direction = signal_data.get('direction', '').upper()
            tcs = signal_data.get('tcs', 0)
            entry_price = signal_data.get('entry_price', 0)
            
            return f"""📡 **TACTICAL SIGNAL DETECTED**
🎯 Pair: {pair}
🔄 Direction: {direction}
⚡ TCS Score: {tcs:.1f}%
💰 Entry: {entry_price}
🎪 Execute with precision!"""
            
        except Exception as e:
            logger.error(f"Failed to format trading signal: {e}")
            return "📡 New trading signal detected"
    
    def _format_squad_activity(self, activity_data: Dict[str, Any]) -> str:
        """Format squad activity for chat display"""
        try:
            activity_type = activity_data.get('type', 'unknown')
            
            if activity_type == 'high_performance':
                return f"🔥 Squad performance spike detected! Win rate: {activity_data.get('win_rate', 0):.1f}%"
            elif activity_type == 'trending_pair':
                pair = activity_data.get('pair', 'Unknown')
                count = activity_data.get('trader_count', 0)
                return f"📈 {pair} is trending - {count} squad members trading!"
            else:
                return f"📊 Squad activity update: {activity_type}"
                
        except Exception as e:
            logger.error(f"Failed to format squad activity: {e}")
            return "📊 Squad activity detected"
    
    # Public API methods
    
    def send_admin_message(self, message: str, squad_id: Optional[str] = None):
        """Send admin message to squad(s)"""
        try:
            if squad_id:
                room_id = f"squad_{squad_id}"
                self.chat_system.send_system_message(
                    room_id=room_id,
                    content=f"🔱 **COMMAND NOTICE:** {message}",
                    metadata={'type': 'admin_message', 'priority': 'high'}
                )
            else:
                # Send to all squads
                for room in self.chat_system.chat_rooms.values():
                    if room.room_id.startswith('squad_'):
                        self.chat_system.send_system_message(
                            room_id=room.room_id,
                            content=f"🔱 **COMMAND NOTICE:** {message}",
                            metadata={'type': 'admin_message', 'priority': 'high'}
                        )
            
            logger.info(f"Admin message sent: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send admin message: {e}")
    
    def get_chat_statistics(self) -> Dict[str, Any]:
        """Get chat system statistics"""
        try:
            active_users = len([u for u in self.chat_system.active_users.values() if u.is_online])
            total_rooms = len(self.chat_system.chat_rooms)
            total_messages = sum(len(msgs) for msgs in self.chat_system.recent_messages.values())
            
            return {
                'active_users': active_users,
                'total_users': len(self.chat_system.active_users),
                'total_rooms': total_rooms,
                'total_messages': total_messages,
                'typing_users': sum(len(users) for users in self.chat_system.typing_users.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat statistics: {e}")
            return {}

# Example usage and initialization
def initialize_chat_integration(app: Flask, **kwargs) -> ChatIntegration:
    """Initialize chat integration with Flask app"""
    try:
        integration = ChatIntegration(app, **kwargs)
        
        # Add to app context for access from other modules
        app.chat_integration = integration
        
        logger.info("Chat integration initialized successfully")
        return integration
        
    except Exception as e:
        logger.error(f"Failed to initialize chat integration: {e}")
        raise

if __name__ == "__main__":
    # Test initialization
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    integration = initialize_chat_integration(app)
    
    # Test admin message
    integration.send_admin_message("System maintenance in 30 minutes")
    
    # Get statistics
    stats = integration.get_chat_statistics()
    print(f"Chat statistics: {stats}")
    
    print("Chat integration test completed")