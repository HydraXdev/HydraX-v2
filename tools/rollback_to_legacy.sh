#!/usr/bin/env bash
echo "Rolling back to legacy relay..."
pm2 stop signals-zmq-to-redis signals-redis-to-webapp 2>/dev/null || true
pm2 delete signals-zmq-to-redis signals-redis-to-webapp 2>/dev/null || true
pm2 restart relay_to_telegram
pm2 save
echo "Rollback complete. Legacy relay active."
