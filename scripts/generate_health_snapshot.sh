#!/bin/bash
###############################################################################
# BITTEN v2.0 Health Snapshot Generator
# Generates comprehensive system health report with visual dashboard
###############################################################################

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/root/HydraX-v2/health_snapshots"
REPORT_FILE="$OUTPUT_DIR/health_snapshot_$TIMESTAMP.html"

mkdir -p "$OUTPUT_DIR"

###############################################################################
# HTML Header
###############################################################################

cat > "$REPORT_FILE" <<'HTML_HEADER'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN v2.0 Health Snapshot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #0f0;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            border: 2px solid #0f0;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
        }
        h1 { color: #0f0; font-size: 32px; margin-bottom: 10px; text-shadow: 0 0 10px #0f0; }
        .timestamp { color: #888; font-size: 14px; }
        .section {
            background: #1a1a1a;
            border: 1px solid #333;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
        }
        .section-title {
            color: #0f0;
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #0f0;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        .status-card {
            background: #222;
            border: 1px solid #444;
            padding: 15px;
            border-radius: 5px;
        }
        .status-card.pass { border-left: 4px solid #0f0; }
        .status-card.warn { border-left: 4px solid #ff0; }
        .status-card.fail { border-left: 4px solid #f00; }
        .metric-label { color: #888; font-size: 12px; margin-bottom: 5px; }
        .metric-value { color: #0f0; font-size: 24px; font-weight: bold; }
        .metric-value.warn { color: #ff0; }
        .metric-value.fail { color: #f00; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        th { color: #0f0; font-weight: bold; background: #222; }
        td { color: #ccc; }
        .status-online { color: #0f0; }
        .status-offline { color: #f00; }
        .status-warn { color: #ff0; }
        code {
            background: #000;
            padding: 2px 6px;
            border-radius: 3px;
            color: #0f0;
            font-family: 'Courier New', monospace;
        }
        .summary {
            background: #2a2a2a;
            border: 2px solid #0f0;
            padding: 20px;
            margin-top: 30px;
            border-radius: 10px;
            text-align: center;
        }
        .summary .overall-status {
            font-size: 48px;
            font-weight: bold;
            margin: 20px 0;
        }
        .summary .overall-status.healthy { color: #0f0; text-shadow: 0 0 20px #0f0; }
        .summary .overall-status.degraded { color: #ff0; text-shadow: 0 0 20px #ff0; }
        .summary .overall-status.critical { color: #f00; text-shadow: 0 0 20px #f00; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 BITTEN v2.0 Health Snapshot</h1>
            <div class="timestamp">Generated: TIMESTAMP_PLACEHOLDER</div>
        </div>
HTML_HEADER

# Replace timestamp placeholder
sed -i "s/TIMESTAMP_PLACEHOLDER/$(date '+%Y-%m-%d %H:%M:%S UTC')/" "$REPORT_FILE"

###############################################################################
# Service Health Check
###############################################################################

echo '<div class="section">' >> "$REPORT_FILE"
echo '<div class="section-title">📦 Service Health</div>' >> "$REPORT_FILE"
echo '<div class="status-grid">' >> "$REPORT_FILE"

# Check each v2 service
for service in zmq_gateway signal_engine fire_service api_server analytics_worker; do
    if pm2 list 2>/dev/null | grep -q "$service.*online"; then
        STATUS="pass"
        STATUS_TEXT="ONLINE"
        COLOR="status-online"
    else
        STATUS="fail"
        STATUS_TEXT="OFFLINE"
        COLOR="status-offline"
    fi

    cat >> "$REPORT_FILE" <<EOF
<div class="status-card $STATUS">
    <div class="metric-label">$service</div>
    <div class="metric-value">
        <span class="$COLOR">$STATUS_TEXT</span>
    </div>
</div>
EOF
done

echo '</div></div>' >> "$REPORT_FILE"

###############################################################################
# ZMQ Port Bindings
###############################################################################

echo '<div class="section">' >> "$REPORT_FILE"
echo '<div class="section-title">🔌 ZMQ Port Bindings</div>' >> "$REPORT_FILE"
echo '<table><tr><th>Port</th><th>Purpose</th><th>Status</th></tr>' >> "$REPORT_FILE"

for PORT_INFO in "5555:Fire Commands" "5556:Market Data In" "5557:Signals Pub" "5558:Confirmations" "5560:Market Data Out"; do
    PORT=$(echo $PORT_INFO | cut -d: -f1)
    PURPOSE=$(echo $PORT_INFO | cut -d: -f2)

    if ss -tulpen 2>/dev/null | grep -q ":$PORT"; then
        STATUS='<span class="status-online">✅ BOUND</span>'
    else
        STATUS='<span class="status-offline">❌ NOT BOUND</span>'
    fi

    echo "<tr><td>$PORT</td><td>$PURPOSE</td><td>$STATUS</td></tr>" >> "$REPORT_FILE"
done

echo '</table></div>' >> "$REPORT_FILE"

###############################################################################
# Database Health
###############################################################################

echo '<div class="section">' >> "$REPORT_FILE"
echo '<div class="section-title">🗄️ Database Health</div>' >> "$REPORT_FILE"
echo '<div class="status-grid">' >> "$REPORT_FILE"

# PostgreSQL connection test
if PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SELECT 1;" >/dev/null 2>&1; then
    PG_STATUS="pass"
    PG_STATUS_TEXT="CONNECTED"
    PG_COLOR="status-online"
else
    PG_STATUS="fail"
    PG_STATUS_TEXT="DISCONNECTED"
    PG_COLOR="status-offline"
fi

cat >> "$REPORT_FILE" <<EOF
<div class="status-card $PG_STATUS">
    <div class="metric-label">PostgreSQL v2</div>
    <div class="metric-value">
        <span class="$PG_COLOR">$PG_STATUS_TEXT</span>
    </div>
</div>
EOF

# Connection count
CONN_COUNT=$(PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -t -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'bitten_v2';" 2>/dev/null || echo "0")
CONN_COUNT=$(echo $CONN_COUNT | tr -d ' ')

if [ "$CONN_COUNT" -lt 50 ]; then
    CONN_STATUS="pass"
    CONN_COLOR=""
elif [ "$CONN_COUNT" -lt 80 ]; then
    CONN_STATUS="warn"
    CONN_COLOR="warn"
else
    CONN_STATUS="fail"
    CONN_COLOR="fail"
fi

cat >> "$REPORT_FILE" <<EOF
<div class="status-card $CONN_STATUS">
    <div class="metric-label">Active Connections</div>
    <div class="metric-value $CONN_COLOR">$CONN_COUNT / 100</div>
</div>
EOF

# Table row counts
SIGNALS_COUNT=$(PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -t -c "SELECT COUNT(*) FROM signals;" 2>/dev/null || echo "0")
FIRES_COUNT=$(PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -t -c "SELECT COUNT(*) FROM fires;" 2>/dev/null || echo "0")

cat >> "$REPORT_FILE" <<EOF
<div class="status-card pass">
    <div class="metric-label">Signals Count</div>
    <div class="metric-value">$SIGNALS_COUNT</div>
</div>
<div class="status-card pass">
    <div class="metric-label">Fires Count</div>
    <div class="metric-value">$FIRES_COUNT</div>
</div>
EOF

echo '</div></div>' >> "$REPORT_FILE"

###############################################################################
# System Resources
###############################################################################

echo '<div class="section">' >> "$REPORT_FILE"
echo '<div class="section-title">💻 System Resources</div>' >> "$REPORT_FILE"
echo '<div class="status-grid">' >> "$REPORT_FILE"

# Memory usage
MEM_USAGE=$(free | awk '/Mem:/ {printf "%.0f", ($3/$2)*100}')
if [ "$MEM_USAGE" -lt 70 ]; then
    MEM_STATUS="pass"
    MEM_COLOR=""
elif [ "$MEM_USAGE" -lt 85 ]; then
    MEM_STATUS="warn"
    MEM_COLOR="warn"
else
    MEM_STATUS="fail"
    MEM_COLOR="fail"
fi

cat >> "$REPORT_FILE" <<EOF
<div class="status-card $MEM_STATUS">
    <div class="metric-label">Memory Usage</div>
    <div class="metric-value $MEM_COLOR">${MEM_USAGE}%</div>
</div>
EOF

# Disk usage
DISK_USAGE=$(df -h /var/lib/postgresql | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 70 ]; then
    DISK_STATUS="pass"
    DISK_COLOR=""
elif [ "$DISK_USAGE" -lt 85 ]; then
    DISK_STATUS="warn"
    DISK_COLOR="warn"
else
    DISK_STATUS="fail"
    DISK_COLOR="fail"
fi

cat >> "$REPORT_FILE" <<EOF
<div class="status-card $DISK_STATUS">
    <div class="metric-label">Disk Usage (PostgreSQL)</div>
    <div class="metric-value $DISK_COLOR">${DISK_USAGE}%</div>
</div>
EOF

# CPU load
CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | cut -d, -f1 | xargs)

cat >> "$REPORT_FILE" <<EOF
<div class="status-card pass">
    <div class="metric-label">CPU Load (1 min)</div>
    <div class="metric-value">$CPU_LOAD</div>
</div>
EOF

# System uptime
UPTIME=$(uptime -p | sed 's/up //')

cat >> "$REPORT_FILE" <<EOF
<div class="status-card pass">
    <div class="metric-label">System Uptime</div>
    <div class="metric-value" style="font-size: 16px;">$UPTIME</div>
</div>
EOF

echo '</div></div>' >> "$REPORT_FILE"

###############################################################################
# Overall Status Summary
###############################################################################

# Calculate overall status
TOTAL_CHECKS=0
PASSED_CHECKS=0
CRITICAL_FAILURES=0

# Count service checks
for service in zmq_gateway signal_engine fire_service api_server analytics_worker; do
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if pm2 list 2>/dev/null | grep -q "$service.*online"; then
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
    fi
done

# Database check
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if PGPASSWORD='bitten_secure_2025' psql -h localhost -p 5433 -U bitten_admin -d bitten_v2 -c "SELECT 1;" >/dev/null 2>&1; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
fi

# ZMQ ports check
for PORT in 5555 5556 5557 5558 5560; do
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if ss -tulpen 2>/dev/null | grep -q ":$PORT"; then
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
done

# Determine overall status
if [ $CRITICAL_FAILURES -eq 0 ]; then
    OVERALL_STATUS="HEALTHY"
    OVERALL_CLASS="healthy"
elif [ $CRITICAL_FAILURES -lt 3 ]; then
    OVERALL_STATUS="DEGRADED"
    OVERALL_CLASS="degraded"
else
    OVERALL_STATUS="CRITICAL"
    OVERALL_CLASS="critical"
fi

cat >> "$REPORT_FILE" <<EOF
<div class="summary">
    <div class="metric-label">Overall System Status</div>
    <div class="overall-status $OVERALL_CLASS">$OVERALL_STATUS</div>
    <div>
        <span style="color: #0f0; font-size: 20px;">$PASSED_CHECKS</span> /
        <span style="color: #888; font-size: 20px;">$TOTAL_CHECKS</span>
        <span style="color: #888;">checks passed</span>
    </div>
</div>
EOF

###############################################################################
# Footer
###############################################################################

cat >> "$REPORT_FILE" <<'EOF'
    </div>
</body>
</html>
EOF

###############################################################################
# Output
###############################################################################

echo "✅ Health snapshot generated: $REPORT_FILE"
echo "📊 Overall Status: $OVERALL_STATUS ($PASSED_CHECKS/$TOTAL_CHECKS checks passed)"

# Create symlink to latest
ln -sf "$REPORT_FILE" "$OUTPUT_DIR/latest.html"

echo "🌐 View report: file://$REPORT_FILE"
echo "🌐 Or latest: file://$OUTPUT_DIR/latest.html"
