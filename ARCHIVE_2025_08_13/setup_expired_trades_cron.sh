#!/bin/bash
# Setup cron job for expired trades cleanup

# Create log directory if it doesn't exist
sudo mkdir -p /var/log/bitten
sudo chown $USER:$USER /var/log/bitten

# Create cron job entry
CRON_JOB="0 * * * * /usr/bin/python3 /root/HydraX-v2/cleanup_expired_trades.py >> /var/log/bitten/cron.log 2>&1"

# Add to crontab if not already present
(crontab -l 2>/dev/null | grep -v "cleanup_expired_trades.py"; echo "$CRON_JOB") | crontab -

echo "✅ Cron job setup complete!"
echo "📋 Expired trades will be cleaned up every hour"
echo "📝 Logs will be written to /var/log/bitten/expired_trades_cleanup.log"
echo ""
echo "To verify cron job:"
echo "  crontab -l | grep cleanup_expired_trades"
echo ""
echo "To test manually:"
echo "  /usr/bin/python3 /root/HydraX-v2/cleanup_expired_trades.py"