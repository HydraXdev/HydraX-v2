#!/usr/bin/env bash
echo "Cutting over to Redis durable fanout..."
pm2 stop relay_to_telegram 2>/dev/null || true
pm2 start signals-zmq-to-redis signals-redis-to-webapp 2>/dev/null || true
pm2 save
echo "Cutover complete. Redis fanout active."
