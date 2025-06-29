#!/bin/bash

curl -s -X POST "https://api.telegram.org/bot7514837840:AAHpbmpQCOnXeiz-4QRTKehrgPLQinA9Guo/setWebhook" \
-H "Content-Type: application/json" \
-d '{"url":"https://joinbitten.com/status"}'
