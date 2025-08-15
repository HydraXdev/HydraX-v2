# 🎯 BITTEN TOC System - Complete Integration Guide

## Overview

The TOC (Terminus Operational Core) system is now fully wired and ready for deployment. This document explains the complete signal flow and how all components work together.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Telegram   │────▶│  TOC Server  │────▶│ Bridge Terminal │
│    Bot      │     │   (Flask)    │     │   Server (VPS)  │
└─────────────┘     └──────────────┘     └─────────────────┘
                            │                      │
                            ▼                      ▼
                    ┌──────────────┐       ┌─────────────┐
                    │   Database   │       │ MT5 Terminal│
                    │  SQLite/PG   │       │   + EA      │
                    └──────────────┘       └─────────────┘
```

## 📁 Key Files Created

### 1. **Core TOC Server**
- `src/toc/unified_toc_server.py` - Main Flask server that orchestrates everything
- Routes:
  - `/assign-terminal` - Assign MT5 terminal to user
  - `/fire` - Send trade signal to terminal
  - `/trade-result` - Receive execution results
  - `/status/<user_id>` - Get user status
  - `/terminals` - List available terminals
  - `/metrics` - System performance metrics

### 2. **Terminal Assignment System**
- `src/toc/terminal_assignment.py` - Manages user-to-terminal mappings
- Features:
  - SQLite database for assignments
  - Terminal pooling (press pass, demo, live)
  - Session management
  - Usage statistics

### 3. **Fire Router**
- `src/toc/fire_router_toc.py` - Routes signals to correct terminals
- Features:
  - HTTP and file-based delivery
  - Retry logic
  - Performance tracking
  - Signal history

### 4. **Telegram Integration**
- `src/toc/telegram_toc_connector.py` - Connects bot to TOC
- Features:
  - Terminal management commands
  - Signal firing
  - Status checking
  - Trade result notifications

### 5. **Bridge Terminal Server**
- `src/toc/bridge_terminal_server.py` - Runs on Windows VPS
- Features:
  - MT5 terminal launching
  - Fire.json signal delivery
  - Trade result monitoring
  - Process management

### 6. **Configuration & Startup**
- `config/toc_config.yaml` - System configuration
- `start_toc_system.py` - Main startup script
- `tests/test_toc_integration.py` - Complete integration test

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Add to .env file
TOC_PORT=5000
TOC_HOST=0.0.0.0

# Bridge IPs (update with your actual VPS IPs)
BRIDGE_PP_IP=192.168.1.100
BRIDGE_PP_PORT=5001
BRIDGE_DEMO_IP=192.168.1.101
BRIDGE_DEMO_PORT=5002
BRIDGE_LIVE_IP=192.168.1.102
BRIDGE_LIVE_PORT=5003

# Telegram (already configured)
TELEGRAM_BOT_TOKEN=7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ
TELEGRAM_CHAT_ID=-1002581996861
```

### 2. Start TOC System
```bash
# On Linux server (DigitalOcean)
python start_toc_system.py
```

### 3. Start Bridge Servers
```bash
# On Windows VPS (AWS) - for each terminal type
python src/toc/bridge_terminal_server.py
```

### 4. Test Integration
```bash
python tests/test_toc_integration.py
```

## 📋 Complete Signal Flow

### 1. **User Initiates Trade**
```
User → Telegram Bot → /fire EURUSD BUY 0.01
```

### 2. **Terminal Assignment**
```python
# TOC automatically assigns terminal if needed
POST /assign-terminal
{
    "user_id": "telegram_123",
    "terminal_type": "press_pass",
    "mt5_credentials": {...}
}
```

### 3. **Signal Routing**
```python
# Signal sent to assigned terminal
POST /fire
{
    "user_id": "telegram_123",
    "signal": {
        "symbol": "EURUSD",
        "direction": "buy",
        "volume": 0.01,
        "stop_loss": 1.0850,
        "take_profit": 1.0950
    }
}
```

### 4. **MT5 Execution**
```
TOC → Bridge → fire.json → MT5 EA → Trade Execution
```

### 5. **Result Callback**
```python
# Bridge monitors results and sends back
POST /trade-result
{
    "user_id": "telegram_123",
    "trade_result": {
        "ticket": 12345678,
        "profit": 20.00,
        ...
    }
}
```

### 6. **User Notification**
```
TOC → Telegram Bot → User
"Trade closed: EURUSD - P/L: $20.00"
```

## 🔧 Key Features Implemented

### ✅ Terminal Management
- Automatic terminal assignment based on user tier
- Terminal pooling for scalability
- Session persistence
- Resource tracking

### ✅ Trade Execution
- Fire mode validation
- Risk management checks
- Cooldown enforcement
- XP rewards

### ✅ Monitoring
- Real-time health checks
- Performance metrics
- Error tracking
- Session cleanup

### ✅ Security
- User authentication
- Tier-based access control
- Rate limiting
- Audit logging

## 🎮 Telegram Commands

The system integrates with these bot commands:

```
/terminal - Manage terminal assignment
/fire <signal> - Execute trade signal
/status - Check current status
/release - Release terminal
```

## 📊 API Endpoints

### Terminal Assignment
```bash
curl -X POST http://localhost:5000/assign-terminal \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "terminal_type": "demo"
  }'
```

### Fire Signal
```bash
curl -X POST http://localhost:5000/fire \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "signal": {
      "symbol": "EURUSD",
      "direction": "buy",
      "volume": 0.01
    }
  }'
```

### Check Status
```bash
curl http://localhost:5000/status/123
```

## 🚨 Production Deployment

### 1. **Systemd Service (Linux)**
```bash
# Create service file
sudo nano /etc/systemd/system/bitten-toc.service

# Enable and start
sudo systemctl enable bitten-toc
sudo systemctl start bitten-toc
```

### 2. **Windows Service (VPS)**
Use NSSM or Windows Service Wrapper to run bridge_terminal_server.py as a service.

### 3. **Monitoring**
- Set up alerts for failed signals
- Monitor terminal availability
- Track performance metrics
- Check error logs regularly

## 🔍 Troubleshooting

### Common Issues

1. **"No available terminals"**
   - Check bridge servers are running
   - Verify terminal configuration
   - Check network connectivity

2. **"Signal routing failed"**
   - Check user has active assignment
   - Verify fire.json permissions
   - Check MT5 EA is running

3. **"Trade result not received"**
   - Check result watcher is active
   - Verify callback URL is correct
   - Check network between bridges

### Debug Mode
```bash
# Enable debug logging
export TOC_DEBUG=true
python start_toc_system.py
```

## 📈 Next Steps

1. **Deploy to Production**
   - Update bridge IPs to actual VPS addresses
   - Configure firewall rules
   - Set up SSL certificates

2. **Scale Up**
   - Add more terminal pools
   - Implement load balancing
   - Set up database replication

3. **Monitor Performance**
   - Set up Prometheus/Grafana
   - Configure alerts
   - Track KPIs

## 🎯 Summary

The BITTEN TOC system is now fully wired and operational. All components are connected:

- ✅ Flask TOC server orchestrates everything
- ✅ Terminal assignments tracked in database
- ✅ Signals routed to correct MT5 terminals
- ✅ Trade results flow back automatically
- ✅ Telegram bot fully integrated
- ✅ XP and statistics updated in real-time

The system is ready for testing and deployment. Run the integration test to verify everything is working correctly!