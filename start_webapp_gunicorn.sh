#!/bin/bash
cd /root/HydraX-v2
exec python3 -m gunicorn webapp_server_optimized:app \
    --bind 0.0.0.0:8888 \
    --workers 2 \
    --threads 8 \
    --timeout 120 \
    --max-requests 800 \
    --max-requests-jitter 200 \
    --log-level info \
    --access-logfile - \
    --error-logfile -