#\!/bin/bash
# BITTEN Redis PEL Watchdog
redis-cli XPENDING alerts telegram | awk "{print \$1}" | xargs -I{} bash -c "if [ {} -gt 50 ]; then echo \"[ALERT] PEL size {}\"; fi"

# Telegram timeout watchdog
egrep -c "TG TIMEOUT" /root/.pm2/logs/athena-broadcaster-secure-error.log 2>/dev/null | awk "{ if (\$1>10) print \"[ALERT] Telegram degraded\" }"
