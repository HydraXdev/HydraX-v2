#!/bin/bash
# Start clean signal loop services with Athena bot

# Export environment variables
export ATHENA_BOT_TOKEN=8322305650:AAHu8NmQ0rXT0LkZOlDeYop6TAUJXaXbwAg
export ATHENA_CHAT_ID=-1002581996861
export WEBAPP_BASE=https://joinbitten.com
export BRIEF_LINK_SECRET=change-me-32-bytes-minimum-secret-key-here
export ZMQ_GEN_PUB=tcp://127.0.0.1:5557
export ZMQ_EA_PUSH=tcp://127.0.0.1:5555
export ZMQ_CONFIRM_SUB=tcp://127.0.0.1:5558
export BITTEN_DB=bitten.db

# Delete old services
pm2 delete relay_to_telegram confirm_listener 2>/dev/null

# Start services
pm2 start /root/HydraX-v2/relay_to_telegram.py --name relay_to_telegram --interpreter python3
pm2 start /root/HydraX-v2/confirm_listener.py --name confirm_listener --interpreter python3

# Save PM2 configuration
pm2 save

echo "✅ Clean signal loop started with Athena bot"
pm2 list