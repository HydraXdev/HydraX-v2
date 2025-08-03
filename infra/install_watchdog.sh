#!/bin/bash
"""
🐕 VENOM Watchdog Installation Script
Installs and configures the VENOM engine watchdog service
"""

set -e

echo "🐍 Installing VENOM Watchdog Service..."

# Ensure running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root"
   exit 1
fi

# Install required Python packages
echo "📦 Installing Python dependencies..."
pip3 install psutil requests

# Copy service file
echo "📋 Installing systemd service..."
cp /root/HydraX-v2/infra/venom_watchdog.service /etc/systemd/system/

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable service
echo "✅ Enabling VENOM watchdog service..."
systemctl enable venom_watchdog.service

echo "🎯 Installation complete!"
echo ""
echo "📋 Usage Commands:"
echo "  Start:   systemctl start venom_watchdog"
echo "  Stop:    systemctl stop venom_watchdog"
echo "  Status:  systemctl status venom_watchdog"
echo "  Logs:    journalctl -u venom_watchdog -f"
echo "  Manual:  /root/HydraX-v2/infra/venom_watchdog.py"
echo ""
echo "📝 Log File: /root/HydraX-v2/infra/venom_watchdog.log"
echo "🔧 PID File: /root/HydraX-v2/infra/venom_watchdog.pid"
echo ""
echo "⚠️  Note: The watchdog will send Telegram alerts to user 7176191872"
echo "    Make sure the bot token is configured in the system."