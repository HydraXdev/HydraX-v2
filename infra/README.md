# 🐍 VENOM Watchdog Daemon

A robust Python daemon that monitors the `venom_scalp_master.py` process and automatically restarts it if it dies. Includes Telegram notifications and comprehensive logging.

## 🎯 Features

- **Process Monitoring**: Checks every 60 seconds if VENOM engine is running
- **Auto-Restart**: Automatically restarts failed processes with logging
- **Telegram Alerts**: Sends notifications to operator (user_id: 7176191872)
- **Duplicate Protection**: Prevents multiple watchdog instances
- **Comprehensive Logging**: Maintains detailed logs in `venom_watchdog.log`
- **Zombie Cleanup**: Kills stuck/zombie processes before restart
- **Graceful Shutdown**: Handles SIGINT/SIGTERM properly

## 📁 Files

```
/root/HydraX-v2/infra/
├── venom_watchdog.py        # Main watchdog daemon
├── venom_watchdog.service   # Systemd service file
├── install_watchdog.sh      # Installation script
├── test_watchdog.py         # Test script
├── venom_watchdog.log       # Log file (created on first run)
├── venom_watchdog.pid       # PID file (created when running)
└── README.md               # This file
```

## 🚀 Installation

### Method 1: Systemd Service (Recommended)

```bash
# Install as system service
sudo /root/HydraX-v2/infra/install_watchdog.sh

# Start the service
sudo systemctl start venom_watchdog

# Check status
sudo systemctl status venom_watchdog

# View logs
sudo journalctl -u venom_watchdog -f
```

### Method 2: Manual Run

```bash
# Run directly (will run in foreground)
python3 /root/HydraX-v2/infra/venom_watchdog.py

# Run in background
nohup python3 /root/HydraX-v2/infra/venom_watchdog.py > /dev/null 2>&1 &
```

## 🔧 Configuration

The watchdog monitors `/root/HydraX-v2/venom_scalp_master.py` by default. Key settings:

```python
SCRIPT_NAME = "venom_scalp_master.py"          # Process name to monitor
SCRIPT_PATH = "/root/HydraX-v2/venom_scalp_master.py"  # Full path to script
CHECK_INTERVAL = 60                            # Check every 60 seconds
OPERATOR_USER_ID = "7176191872"               # Telegram alert recipient
```

## 📊 Monitoring

### Log File
```bash
# View live logs
tail -f /root/HydraX-v2/infra/venom_watchdog.log

# View recent logs
cat /root/HydraX-v2/infra/venom_watchdog.log | tail -20
```

### Systemd Logs
```bash
# Live system logs
journalctl -u venom_watchdog -f

# Recent logs
journalctl -u venom_watchdog --since "1 hour ago"
```

### Process Status
```bash
# Check if watchdog is running
ps aux | grep venom_watchdog

# Check PID file
cat /root/HydraX-v2/infra/venom_watchdog.pid

# Check if VENOM is running
ps aux | grep venom_scalp_master
```

## 📱 Telegram Alerts

The watchdog sends alerts for:

1. **Startup**: When watchdog starts monitoring
2. **Restart**: When VENOM engine is restarted
3. **Failure**: When restart attempts fail
4. **Shutdown**: When watchdog stops

Example alert:
```
🐍 VENOM Engine Restart Alert

Status: Engine restarted automatically
Time: 2025-07-30 12:34:56 UTC
Restart Count: #3
Script: venom_scalp_master.py
Server: HydraX-v2 Production

Watchdog: Process monitoring active ✅
Next Check: 60 seconds

The VENOM engine has been restored and is generating signals.
```

## 🧪 Testing

```bash
# Test watchdog functionality
python3 /root/HydraX-v2/infra/test_watchdog.py

# Test alerts (will not actually send)
python3 -c "
import sys; sys.path.append('/root/HydraX-v2/infra')
from venom_watchdog import VenomWatchdog
w = VenomWatchdog()
print(w.format_startup_alert())
"
```

## 🛠️ Troubleshooting

### Watchdog Won't Start
```bash
# Check for duplicate processes
ps aux | grep venom_watchdog

# Remove stale PID file
rm -f /root/HydraX-v2/infra/venom_watchdog.pid

# Check permissions
ls -la /root/HydraX-v2/infra/venom_watchdog.py
```

### VENOM Won't Restart
```bash
# Check if script exists
ls -la /root/HydraX-v2/venom_scalp_master.py

# Check script permissions
chmod +x /root/HydraX-v2/venom_scalp_master.py

# Manual test
python3 /root/HydraX-v2/venom_scalp_master.py
```

### No Telegram Alerts
```bash
# Check bot token configuration
python3 -c "
from config_loader import get_bot_token
print('Bot token loaded:', bool(get_bot_token()))
"

# Test Telegram API
curl -X POST "https://api.telegram.org/bot<TOKEN>/getMe"
```

## 🔐 Security

- Runs with minimal privileges
- PID file prevents duplicate instances
- Logs rotation to prevent disk usage
- Graceful shutdown on system signals
- No hardcoded secrets (uses config_loader)

## 📈 Performance

- **Memory Usage**: ~20-30MB
- **CPU Usage**: <1% (mostly idle)
- **Disk I/O**: Minimal (log writes only)
- **Network**: Only for Telegram alerts

## 🔄 Service Management

```bash
# Start
systemctl start venom_watchdog

# Stop
systemctl stop venom_watchdog

# Restart
systemctl restart venom_watchdog

# Enable auto-start
systemctl enable venom_watchdog

# Disable auto-start
systemctl disable venom_watchdog

# Status
systemctl status venom_watchdog
```

## 📝 Log Format

```
2025-07-30 12:34:56,789 - VenomWatchdog - INFO - 🐕 VENOM Watchdog initialized
2025-07-30 12:34:56,790 - VenomWatchdog - INFO - 📊 Check interval: 60 seconds
2025-07-30 12:34:56,791 - VenomWatchdog - INFO - 🎯 Target script: venom_scalp_master.py
2025-07-30 12:34:56,792 - VenomWatchdog - INFO - ✅ VENOM engine already running
2025-07-30 12:35:56,793 - VenomWatchdog - ERROR - ❌ VENOM engine process has died - restarting
2025-07-30 12:35:59,794 - VenomWatchdog - INFO - ✅ VENOM engine started successfully (Restart #1)
```

## 🎯 Success Criteria

The watchdog is working correctly when you see:
- ✅ No duplicate process errors
- ✅ Regular health check logs (every 60s)
- ✅ Automatic restarts when VENOM dies
- ✅ Telegram alerts received
- ✅ Clean log rotation

---

**Your VENOM engine now has a loyal guard dog! 🐕**