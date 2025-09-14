#!/bin/bash
# WINLOSS Report command aliases for easy execution

REPORT_SCRIPT="/root/HydraX-v2/tools/winloss_report.py"

case "$1" in
    last24h)
        python3 $REPORT_SCRIPT last24h
        ;;
    today)
        python3 $REPORT_SCRIPT today
        ;;
    yesterday)
        python3 $REPORT_SCRIPT yesterday
        ;;
    last7d)
        python3 $REPORT_SCRIPT last7d
        ;;
    custom)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: run_winloss_report.sh custom 'FROM_TIME' 'TO_TIME'"
            echo "Example: run_winloss_report.sh custom '2025-09-03 00:00' '2025-09-04 00:00'"
            exit 1
        fi
        python3 $REPORT_SCRIPT --from "$2" --to "$3"
        ;;
    *)
        echo "Usage: run_winloss_report.sh [last24h|today|yesterday|last7d|custom FROM TO]"
        echo ""
        echo "Examples:"
        echo "  run_winloss_report.sh last24h      # Last 24 hours"
        echo "  run_winloss_report.sh today        # Today so far"
        echo "  run_winloss_report.sh yesterday    # Yesterday full day"
        echo "  run_winloss_report.sh last7d       # Last 7 days"
        echo "  run_winloss_report.sh custom '2025-09-01' '2025-09-05'"
        exit 1
        ;;
esac