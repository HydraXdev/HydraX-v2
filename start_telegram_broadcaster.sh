#!/bin/bash
source /root/HydraX-v2/.secrets/athena.env
export REDIS_HOST="127.0.0.1"
export REDIS_PORT="6379"
export ALERT_STREAM="alerts"
export ALERT_GROUP="telegram"
export ALERT_CONSUMER="athena"
export WEBAPP_PUBLIC_BASE="https://joinbitten.com"
exec python3 /root/HydraX-v2/tools/telegram_broadcaster_alerts.py
