# BITTEN v2.0 API Server - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Set Telegram Bot Token
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
```

### 2. Start the Server
```bash
cd /root/HydraX-v2/services/api_server
./start.sh
```

### 3. Verify It's Running
```bash
curl http://localhost:8888/health
```

Expected output:
```json
{
  "status": "healthy",
  "timestamp": 1728395672,
  "version": "2.0.0",
  "services": {
    "api": "online",
    "websocket": "online",
    "telegram": "online",
    "database": "online"
  }
}
```

### 4. Run Tests
```bash
python3 test_api.py
```

### 5. Access Web Interface
- **War Room:** http://134.199.204.67:8888/me
- **Mission Briefing:** http://134.199.204.67:8888/brief
- **Connect Guide:** http://134.199.204.67:8888/connect

---

## 🔥 Fire Your First Signal

### Via REST API
```bash
# List signals
curl http://localhost:8888/api/signals

# Fire a signal
curl -X POST http://localhost:8888/api/signals/ELITE_GUARD_EURUSD_123/fire \
  -H "Content-Type: application/json" \
  -d '{"signal_id": "ELITE_GUARD_EURUSD_123", "user_id": "7176191872"}'
```

### Via Telegram
```
/fire ELITE_GUARD_EURUSD_123
```

### Via Web Interface
1. Go to http://134.199.204.67:8888/me
2. Click "🔫 FIRE" button on any signal

---

## 📊 Check Your Stats

### Via REST API
```bash
curl http://localhost:8888/api/users/7176191872/stats
```

### Via Telegram
```
/me
```

### Via Web Interface
Go to http://134.199.204.67:8888/me

---

## 🔍 Monitor Real-Time

### WebSocket (Browser Console)
```javascript
// Signal stream
const ws = new WebSocket('ws://134.199.204.67:8888/ws/signals');
ws.onmessage = (e) => console.log('Signal:', JSON.parse(e.data));

// Position stream
const wsPos = new WebSocket('ws://134.199.204.67:8888/ws/positions/7176191872');
wsPos.onmessage = (e) => console.log('Position:', JSON.parse(e.data));
```

---

## 🛠️ Troubleshooting

### Server Won't Start
```bash
# Check if port 8888 is already in use
ss -tuln | grep 8888

# Kill existing process
pm2 stop webapp
# or
lsof -ti:8888 | xargs kill -9
```

### Telegram Bot Not Responding
```bash
# Check token is set
echo $TELEGRAM_BOT_TOKEN

# Check logs
pm2 logs api_server | grep telegram
```

### Database Errors
```bash
# Verify database exists
ls -lh /root/HydraX-v2/bitten.db

# Check integrity
sqlite3 /root/HydraX-v2/bitten.db "PRAGMA integrity_check;"
```

---

## 📈 Production Deployment

### Using PM2
```bash
# Stop old webapp
pm2 stop webapp

# Start new API server
cd /root/HydraX-v2/services/api_server
pm2 start start.sh --name webapp

# Save configuration
pm2 save

# Enable auto-start
pm2 startup
```

### Check Status
```bash
pm2 status webapp
pm2 logs webapp --lines 50
```

---

## 📚 Learn More

- **Full Documentation:** [README.md](./README.md)
- **Deployment Guide:** [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)
- **API Docs:** http://localhost:8888/docs

---

**That's it!** 🎯 Your BITTEN v2.0 API Server is ready to handle signals, fires, and tactical operations.
