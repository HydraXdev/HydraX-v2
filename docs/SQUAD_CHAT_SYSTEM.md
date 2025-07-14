# BITTEN Squad Chat System

## Overview

The BITTEN Squad Chat System is a comprehensive real-time tactical communication platform designed for trading squads. It features military-themed UI, secure messaging, real-time notifications, and deep integration with the BITTEN trading ecosystem.

## Features

### 🎯 Core Chat Features
- **Real-time messaging** with WebSocket technology
- **Typing indicators** to show active participants
- **Squad-specific chat rooms** with automatic creation
- **Message history and persistence** with Redis/file storage
- **Emoji reactions** for quick responses
- **File and image sharing** with validation and security
- **Voice message support** (framework ready)
- **Message encryption** for secure communications

### ⚔️ Military-Themed UI
- **Tactical command interface** with green terminal aesthetics
- **Military ranks and callsigns** display
- **Squad-based organization** with role hierarchies
- **Command-style notifications** and alerts
- **Rank-based permissions** system

### 🔔 Advanced Notifications
- **Multi-channel delivery**: Real-time, push, email, SMS, Telegram
- **Smart notification filtering** based on user preferences
- **Mention detection** with @username and @squad support
- **Quiet hours** and do-not-disturb settings
- **Priority-based routing** for urgent communications

### 🛡️ Moderation & Security
- **Role-based moderation** (Commander, Sergeant privileges)
- **Mute, kick, and ban** functionality
- **User reporting** system with audit trails
- **Message encryption** for sensitive communications
- **File upload validation** and virus scanning ready

### 📊 Trading Integration
- **Automatic signal sharing** when trades are executed
- **Squad performance updates** from radar system
- **Achievement announcements** for milestones
- **Real-time trading activity** feeds
- **TCS score integration** for signal confidence

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BITTEN Chat System                     │
├─────────────────────────────────────────────────────────────┤
│  Frontend (chat_interface.js)                             │
│  ├── WebSocket Connection Management                       │
│  ├── Message Display & Formatting                         │
│  ├── File Upload Handling                                 │
│  ├── Notification Management                              │
│  └── UI State Management                                  │
├─────────────────────────────────────────────────────────────┤
│  Backend (squad_chat.py)                                  │
│  ├── Flask-SocketIO Server                               │
│  ├── Message Routing & Storage                           │
│  ├── User Session Management                             │
│  ├── Room Management                                     │
│  └── Real-time Event Handling                           │
├─────────────────────────────────────────────────────────────┤
│  Notifications (chat_notifications.py)                    │
│  ├── Multi-channel Delivery                              │
│  ├── User Preference Management                          │
│  ├── Smart Filtering & Routing                           │
│  └── Background Processing (Celery)                      │
├─────────────────────────────────────────────────────────────┤
│  Integration (chat_integration.py)                        │
│  ├── BITTEN System Hooks                                 │
│  ├── User Authentication                                 │
│  ├── Permission Management                               │
│  └── Data Synchronization                               │
├─────────────────────────────────────────────────────────────┤
│  Storage Layer                                            │
│  ├── Redis (Real-time data, sessions)                    │
│  ├── File System (Message archives, uploads)             │
│  └── Database (User settings, history)                   │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
src/bitten_core/
├── squad_chat.py              # Main chat system with SocketIO
├── chat_notifications.py      # Notification service
├── chat_integration.py        # BITTEN system integration
└── squad_radar.py            # Squad activity tracking (existing)

templates/
└── squad_chat_widget.html     # Chat UI component

src/ui/chat/
└── chat_interface.js          # Frontend JavaScript

examples/
└── squad_chat_demo.py         # Complete demo application

docs/
└── SQUAD_CHAT_SYSTEM.md      # This documentation
```

## Quick Start

### 1. Install Dependencies

```bash
pip install flask flask-socketio redis eventlet python-socketio celery
```

### 2. Run the Demo

```bash
cd /root/HydraX-v2
python examples/squad_chat_demo.py
```

Open http://localhost:5000 to access the demo interface.

### 3. Integration with Existing BITTEN System

```python
from flask import Flask
from src.bitten_core.chat_integration import initialize_chat_integration

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize chat system
chat_integration = initialize_chat_integration(
    app=app,
    user_profile_manager=your_user_manager,
    tier_lock_manager=your_tier_manager,
    squad_radar=your_squad_radar
)

# The chat system is now available at /chat
# API endpoints are automatically registered
```

## Configuration

### Chat Features Configuration

```json
{
  "chat_features": {
    "max_message_length": 2000,
    "max_file_size_mb": 10,
    "allowed_file_types": [
      "image/png", "image/jpeg", "image/gif", "image/webp",
      "application/pdf", "text/plain", "application/zip"
    ],
    "rate_limit_messages_per_minute": 30,
    "enable_voice_messages": true,
    "enable_gif_search": true,
    "enable_encryption": true
  }
}
```

### Permissions Configuration

```json
{
  "permissions": {
    "create_rooms": ["commander", "sergeant"],
    "moderate_users": ["commander", "sergeant"],
    "delete_messages": ["commander", "sergeant"],
    "kick_users": ["commander", "sergeant"],
    "ban_users": ["commander"],
    "access_chat_history": ["commander", "sergeant", "corporal"]
  }
}
```

### Notification Settings

```json
{
  "notification_settings": {
    "email_enabled": true,
    "push_enabled": true,
    "telegram_enabled": true,
    "quiet_hours_default": {
      "start": "22:00",
      "end": "08:00"
    }
  }
}
```

## API Reference

### WebSocket Events

#### Client to Server

| Event | Description | Parameters |
|-------|-------------|------------|
| `join_squad_room` | Join a squad chat room | `{squad_id: string}` |
| `send_message` | Send a chat message | `{room_id, content, type, metadata}` |
| `typing_start` | Start typing indicator | `{room_id: string}` |
| `typing_stop` | Stop typing indicator | `{room_id: string}` |
| `add_reaction` | Add emoji reaction | `{message_id, emoji}` |
| `moderate_user` | Moderate another user | `{target_user_id, action, duration, reason}` |

#### Server to Client

| Event | Description | Data |
|-------|-------------|------|
| `connection_confirmed` | Connection established | `{status, user_id, timestamp}` |
| `room_history` | Message history for room | `{room_id, messages[]}` |
| `new_message` | New message received | `{message object}` |
| `user_joined` | User joined room | `{user_id, username, timestamp}` |
| `user_typing` | User is typing | `{user_id, username, room_id}` |
| `user_stopped_typing` | User stopped typing | `{user_id, room_id}` |
| `reaction_added` | Reaction added to message | `{message_id, emoji, user_id, reactions}` |
| `moderation_notice` | Moderation action applied | `{action, duration, reason, moderator}` |

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/join` | Join chat system |
| POST | `/api/chat/upload` | Upload file to chat |
| GET | `/api/chat/notifications` | Get user notifications |
| POST | `/api/chat/notifications/mark_read` | Mark notifications as read |
| GET/POST | `/api/chat/settings` | Get/update chat settings |

## User Roles & Permissions

### Role Hierarchy

1. **Commander** (Highest Authority)
   - Full moderation powers (ban, kick, mute)
   - Create and manage rooms
   - Access all chat history
   - Send admin announcements

2. **Sergeant** (Squad Leader)
   - Moderate users (kick, mute)
   - Access squad chat history
   - Create squad rooms

3. **Corporal** (Senior Member)
   - Access extended chat history
   - Basic moderation (report users)

4. **Recruit** (New Member)
   - Basic chat access
   - Limited history access

### Permission Matrix

| Action | Commander | Sergeant | Corporal | Recruit |
|--------|-----------|----------|----------|---------|
| Send Messages | ✅ | ✅ | ✅ | ✅ |
| Upload Files | ✅ | ✅ | ✅ | ✅ |
| Add Reactions | ✅ | ✅ | ✅ | ✅ |
| Create Rooms | ✅ | ✅ | ❌ | ❌ |
| Delete Messages | ✅ | ✅ | ❌ | ❌ |
| Mute Users | ✅ | ✅ | ❌ | ❌ |
| Kick Users | ✅ | ✅ | ❌ | ❌ |
| Ban Users | ✅ | ❌ | ❌ | ❌ |
| View All History | ✅ | ✅ | ✅ | ❌ |
| Report Users | ✅ | ✅ | ✅ | ✅ |

## Integration Examples

### Trading Signal Integration

```python
# When a trading signal is generated
def on_signal_generated(signal_data):
    user_id = signal_data['user_id']
    user_data = get_user_data(user_id)
    
    # Send to squad chat
    chat_integration.chat_system.send_system_message(
        room_id=f"squad_{user_data['squad_id']}",
        content=f"""📡 **TACTICAL SIGNAL DETECTED**
🎯 Pair: {signal_data['pair']}
🔄 Direction: {signal_data['direction']}
⚡ TCS Score: {signal_data['tcs']:.1f}%
💰 Entry: {signal_data['entry_price']}""",
        metadata={'type': 'trading_signal', 'signal_data': signal_data}
    )
```

### Achievement Integration

```python
# When user earns achievement
def on_achievement_earned(user_id, achievement_name):
    user_data = get_user_data(user_id)
    
    chat_integration.chat_system.send_system_message(
        room_id=f"squad_{user_data['squad_id']}",
        content=f"🏆 {user_data['callsign']} earned achievement: {achievement_name}!",
        metadata={'type': 'achievement'}
    )
```

### Squad Activity Integration

```python
# When squad radar detects activity
def on_squad_activity(squad_id, activity_data):
    chat_integration.chat_system.send_system_message(
        room_id=f"squad_{squad_id}",
        content=f"🔥 Squad performance spike! Win rate: {activity_data['win_rate']:.1f}%",
        metadata={'type': 'squad_activity'}
    )
```

## Notification System

### Notification Types

- `DIRECT_MESSAGE`: Direct messages between users
- `MENTION`: User mentioned in message (@username)
- `SQUAD_MESSAGE`: General squad chat activity
- `SYSTEM_ALERT`: System-wide announcements
- `MODERATION_ACTION`: Moderation actions taken
- `FILE_SHARED`: File shared in chat
- `USER_JOINED/LEFT`: Squad member activity

### Delivery Methods

- **Real-time**: WebSocket push to connected clients
- **Push**: Browser push notifications
- **Email**: HTML email notifications
- **SMS**: Text message alerts (framework ready)
- **Telegram**: Telegram bot integration

### User Preferences

Users can configure:
- Which notification types to receive
- Delivery methods per notification type
- Quiet hours (no notifications)
- Custom mention keywords
- Email and contact preferences

## Security Features

### Message Encryption

- End-to-end encryption for sensitive rooms
- Automatic key rotation
- Secure file uploads with validation

### User Authentication

- Integration with BITTEN user system
- Session-based authentication
- Role-based access control

### Moderation Tools

- Real-time moderation actions
- Audit trail for all actions
- Automated spam detection ready
- User reporting system

## Performance Considerations

### Scalability

- **Redis** for session storage and real-time data
- **Celery** for background notification processing
- **File system** for message archival
- **WebSocket** connection pooling

### Message Storage

- Recent messages kept in memory (100 per room)
- Daily message archival to files
- Redis backup for reliability
- Configurable retention policies

### Rate Limiting

- 30 messages per minute per user (configurable)
- File upload size limits
- Connection throttling

## Deployment

### Production Requirements

- Redis server for session storage
- SMTP server for email notifications
- File storage for uploads and archives
- SSL certificates for secure WebSocket

### Environment Variables

```bash
REDIS_URL=redis://localhost:6379
CHAT_SECRET_KEY=your-secret-key
SMTP_HOST=smtp.your-provider.com
SMTP_USER=your-smtp-user
SMTP_PASS=your-smtp-password
TELEGRAM_BOT_TOKEN=your-telegram-token
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY templates/ templates/
COPY webapp/static/ webapp/static/

EXPOSE 5000
CMD ["python", "-m", "gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check firewall settings
   - Verify Redis connectivity
   - Ensure proper CORS configuration

2. **Messages Not Appearing**
   - Check Redis connection
   - Verify user permissions
   - Check room membership

3. **File Uploads Failing**
   - Check file size limits
   - Verify allowed file types
   - Check disk space

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('bitten_core.squad_chat').setLevel(logging.DEBUG)
logging.getLogger('socketio').setLevel(logging.DEBUG)
```

## Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python -m pytest tests/`
4. Run demo: `python examples/squad_chat_demo.py`

### Testing

```bash
# Run all chat system tests
python -m pytest tests/test_squad_chat.py
python -m pytest tests/test_chat_notifications.py
python -m pytest tests/test_chat_integration.py
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings for public methods
- Military-themed naming conventions

## License

Part of the BITTEN trading system. All rights reserved.

---

**⚡ STAY SHARP, STAY CONNECTED ⚡**

For support or feature requests, contact the BITTEN development team.