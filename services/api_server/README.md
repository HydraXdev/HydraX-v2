# BITTEN v2.0 API Server

FastAPI-based REST API + WebSocket + Telegram Bot Integration for BITTEN trading system.

## Architecture

```
api_server/
├── main.py                    # FastAPI application
├── config.py                  # Configuration management
├── models.py                  # SQLAlchemy & Pydantic models
├── rest/                      # REST API endpoints
│   ├── signals.py             # Signal management
│   ├── fires.py               # Fire execution
│   ├── users.py               # User statistics
│   └── auth.py                # Authentication
├── websocket/                 # WebSocket handlers
│   ├── signal_stream.py       # Real-time signals
│   └── position_stream.py     # Real-time positions
├── telegram/                  # Telegram bot
│   ├── bot.py                 # Bot application
│   └── commands.py            # Command handlers
├── templates/                 # HTML templates
│   ├── war_room.html          # User dashboard
│   ├── mission_briefing.html  # Signal briefing
│   └── connect.html           # MT5 onboarding
└── requirements.txt           # Python dependencies
```

## Features

### REST API (Port 8888)

- `GET /health` - Health check
- `GET /api/signals` - List active signals
- `GET /api/signals/{signal_id}` - Get signal details
- `POST /api/signals/{signal_id}/fire` - Execute fire command
- `GET /api/users/{user_id}` - Get user details
- `GET /api/users/{user_id}/stats` - Get user statistics
- `GET /api/users/{user_id}/positions` - Get active positions

### WebSocket Streaming

- `ws://host:8888/ws/signals` - Real-time signal stream
- `ws://host:8888/ws/positions/{user_id}` - Real-time position updates

### Telegram Bot

- `/fire <signal_id>` - Execute fire command
- `/BITMODE ON|OFF` - Toggle BITMODE
- `/me` - View stats
- `/brief` - View mission briefing
- `/help` - Show commands

### HTML Pages

- `/me` - War Room (user dashboard)
- `/brief` - Mission Briefing
- `/connect` - MT5 Connection Guide

## Installation

1. Install dependencies:
```bash
cd /root/HydraX-v2/services/api_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export DATABASE_URL="sqlite:////root/HydraX-v2/bitten.db"
```

3. Start the server:
```bash
./start.sh
# OR
uvicorn main:app --host 0.0.0.0 --port 8888 --reload
```

## Configuration

Edit `config.py` or set environment variables:

- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 8888)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `DATABASE_URL` - Database connection string
- `REDIS_HOST` - Redis host for WebSocket pub/sub
- `DEBUG` - Debug mode (default: False)

## API Examples

### List Active Signals
```bash
curl http://localhost:8888/api/signals
```

### Fire a Signal
```bash
curl -X POST http://localhost:8888/api/signals/ELITE_GUARD_EURUSD_123/fire \
  -H "Content-Type: application/json" \
  -d '{"signal_id": "ELITE_GUARD_EURUSD_123", "user_id": "7176191872"}'
```

### Get User Stats
```bash
curl http://localhost:8888/api/users/7176191872/stats
```

### WebSocket Connection (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8888/ws/signals');
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log('Signal:', msg);
};
```

## Integration with Existing System

This service replaces `webapp_server_optimized.py` with:

- Modern FastAPI framework (vs Flask)
- Native WebSocket support (vs Flask-SocketIO)
- Async/await for better performance
- Type safety with Pydantic models
- Better Telegram bot integration
- Cleaner separation of concerns

### Migration Notes

1. **Database**: Uses same SQLite database (`/root/HydraX-v2/bitten.db`)
2. **Fire Queue**: Uses same IPC queue (`ipc:///tmp/bitten_cmdqueue`)
3. **Port**: Same port 8888 for compatibility
4. **Templates**: HTML templates modernized with WebSocket support

## Development

### Run in Development Mode
```bash
export DEBUG=True
uvicorn main:app --reload
```

### Run Tests
```bash
pytest tests/
```

### Add New Endpoint
1. Create route in `rest/` directory
2. Add router to `main.py`
3. Update models if needed

## Production Deployment

### Using PM2
```bash
pm2 start start.sh --name api_server
pm2 save
```

### Using systemd
```bash
sudo cp bitten-api.service /etc/systemd/system/
sudo systemctl enable bitten-api
sudo systemctl start bitten-api
```

## Monitoring

- Health check: `http://localhost:8888/health`
- Logs: Check uvicorn output or PM2 logs
- Metrics: WebSocket connection count, API request rates

## Troubleshooting

### Bot Not Starting
- Check `TELEGRAM_BOT_TOKEN` is set
- Verify token with BotFather
- Check firewall allows Telegram API access

### WebSocket Disconnects
- Check Redis connection (if enabled)
- Verify WebSocket URL uses `ws://` not `http://`
- Check client-side error handling

### Fire Commands Not Working
- Verify IPC queue exists: `/tmp/bitten_cmdqueue`
- Check `command_router` is running
- Verify EA connection in database

## Version History

- **2.0.0** (2025-10-08) - Initial FastAPI implementation
  - REST API with all core endpoints
  - WebSocket streaming for signals and positions
  - Telegram bot integration
  - Modern HTML templates with real-time updates

## License

BITTEN Trading System - Proprietary
