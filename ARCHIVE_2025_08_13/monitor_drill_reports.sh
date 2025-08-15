#!/bin/bash

# Monitor drill report scheduler health and status

PROJECT_ROOT="/root/HydraX-v2"
LOG_DIR="$PROJECT_ROOT/logs"
SUMMARY_FILE="$LOG_DIR/drill_reports_summary.json"

echo "🪖 DRILL REPORT SCHEDULER MONITOR"
echo "================================="
echo ""

# Check if cron job exists
if crontab -l 2>/dev/null | grep -q "send_daily_drill_reports.py"; then
    echo "✅ Cron job: ACTIVE"
else
    echo "❌ Cron job: NOT FOUND"
fi

# Check health
if python3 "$PROJECT_ROOT/send_daily_drill_reports.py" health > /dev/null 2>&1; then
    echo "✅ Health check: PASS"
else
    echo "❌ Health check: FAIL"
fi

# Check recent execution
if [[ -f "$SUMMARY_FILE" ]]; then
    echo "📊 Recent executions:"
    python3 -c "
import json
import sys
try:
    with open('$SUMMARY_FILE', 'r') as f:
        data = json.load(f)
    
    # Show last 5 executions
    for record in data[-5:]:
        status = '✅' if record.get('success', False) else '❌'
        print(f'  {status} {record.get(\"date\", \"unknown\")} - {record.get(\"reports_sent\", 0)} reports, {record.get(\"errors_encountered\", 0)} errors')
except:
    print('  No execution data available')
"
else
    echo "📊 No execution history found"
fi

echo ""
echo "📂 Log files:"
echo "  - Scheduler: $LOG_DIR/drill_reports_scheduler.log"
echo "  - Cron: $LOG_DIR/drill_scheduler_cron.log"
echo "  - Summary: $SUMMARY_FILE"
