#!/bin/bash
# Production startup script for BITTEN webapp

echo "🚀 Starting BITTEN Webapp (Refactored)"

# Kill any existing gunicorn processes
pkill -9 -f "gunicorn.*webapp" 2>/dev/null
sleep 1

# Start with Gunicorn in daemon mode
gunicorn -b 0.0.0.0:8888 \
  webapp_server_refactored:app \
  --timeout 120 \
  --workers 1 \
  --daemon \
  --pid /tmp/webapp.pid \
  --access-logfile /var/log/webapp_access.log \
  --error-logfile /var/log/webapp_error.log

# Check if started successfully
sleep 2
if curl -s http://localhost:8888/healthz > /dev/null; then
    echo "✅ Webapp started successfully on port 8888"
    echo "PID file: /tmp/webapp.pid"
    echo "Access logs: /var/log/webapp_access.log"
    echo "Error logs: /var/log/webapp_error.log"
else
    echo "❌ Failed to start webapp"
    exit 1
fi