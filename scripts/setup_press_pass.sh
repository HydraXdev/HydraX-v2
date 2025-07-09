#!/bin/bash
# Setup script for Press Pass XP Reset Service

echo "🎫 Setting up Press Pass XP Reset Service..."

# Create necessary directories
mkdir -p /root/HydraX-v2/data
mkdir -p /root/HydraX-v2/logs

# Copy service file
sudo cp /root/HydraX-v2/scripts/press_pass_reset.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the service
sudo systemctl enable press_pass_reset.service

echo "✅ Service installed!"
echo ""
echo "Available commands:"
echo "  Start service:   sudo systemctl start press_pass_reset"
echo "  Stop service:    sudo systemctl stop press_pass_reset"
echo "  View status:     sudo systemctl status press_pass_reset"
echo "  View logs:       sudo journalctl -u press_pass_reset -f"
echo ""
echo "The service will automatically start on system boot."
echo "XP resets will occur daily at 00:00 UTC with warnings at 23:00 and 23:45 UTC."