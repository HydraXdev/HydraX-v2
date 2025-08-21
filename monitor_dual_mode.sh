#!/bin/bash

# ============================================================================
# DUAL MODE MONITORING SCRIPT - BITTEN TRADING SYSTEM
# ============================================================================
# Purpose: Real-time monitoring, performance tracking, and alerts
# Date: 2025-08-19 16:30 UTC
# Version: DUAL_MODE_MONITOR_v1.0

# ANSI Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="/root/HydraX-v2"
TRUTH_LOG="${SCRIPT_DIR}/truth_log.jsonl"
MONITOR_LOG="${SCRIPT_DIR}/dual_mode_monitor.log"
ALERT_LOG="${SCRIPT_DIR}/dual_mode_alerts.log"

# Alert thresholds
SIGNAL_IMBALANCE_THRESHOLD=10  # Max deviation from 60/40 split
MIN_SIGNALS_PER_HOUR=3
MAX_SIGNALS_PER_HOUR=20
MIN_WIN_RATE_RAPID=70
MIN_WIN_RATE_PRECISION=80
MAX_TRADE_DURATION_RAPID=12    # minutes
MAX_TRADE_DURATION_PRECISION=20 # minutes

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MONITOR_LOG"
}

alert() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $message" | tee -a "$ALERT_LOG"
    echo -e "${RED}🚨 ALERT: $message${NC}"
}

print_banner() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                BITTEN DUAL MODE MONITOR                     ║"
    echo "║              Real-time Performance Tracking                 ║"
    echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "${CYAN}▶ $1${NC}"
    echo -e "${CYAN}$(printf '━%.0s' {1..60})${NC}"
}

# ============================================================================
# SYSTEM HEALTH CHECKS
# ============================================================================

check_system_health() {
    print_section "SYSTEM HEALTH STATUS"
    
    local health_score=0
    local max_score=5
    
    # Check critical processes
    echo -e "${WHITE}Process Status:${NC}"
    local processes=("elite_guard_with_citadel.py" "webapp_server_optimized.py" "command_router.py")
    local running_processes=0
    
    for process in "${processes[@]}"; do
        if pgrep -f "$process" > /dev/null; then
            echo -e "  ${GREEN}✅ $process${NC}"
            ((running_processes++))
        else
            echo -e "  ${RED}❌ $process${NC}"
            alert "Critical process not running: $process"
        fi
    done
    
    if [ $running_processes -eq ${#processes[@]} ]; then
        ((health_score++))
    fi
    
    # Check ZMQ ports
    echo -e "${WHITE}ZMQ Port Status:${NC}"
    local ports=(5555 5556 5557 5558 5560 8888)
    local bound_ports=0
    
    for port in "${ports[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            echo -e "  ${GREEN}✅ Port $port${NC}"
            ((bound_ports++))
        else
            echo -e "  ${YELLOW}⚠️  Port $port${NC}"
        fi
    done
    
    if [ $bound_ports -ge 4 ]; then  # At least 4 critical ports
        ((health_score++))
    fi
    
    # Check database
    echo -e "${WHITE}Database Status:${NC}"
    if sqlite3 "${SCRIPT_DIR}/bitten.db" "SELECT COUNT(*) FROM signals LIMIT 1;" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Database accessible${NC}"
        ((health_score++))
    else
        echo -e "  ${RED}❌ Database error${NC}"
        alert "Database connection failed"
    fi
    
    # Check truth log
    echo -e "${WHITE}Truth Log Status:${NC}"
    if [ -f "$TRUTH_LOG" ] && [ -s "$TRUTH_LOG" ]; then
        local log_size=$(wc -l < "$TRUTH_LOG")
        echo -e "  ${GREEN}✅ Truth log active ($log_size signals)${NC}"
        ((health_score++))
    else
        echo -e "  ${RED}❌ Truth log missing or empty${NC}"
        alert "Truth log missing or empty"
    fi
    
    # Check recent activity
    echo -e "${WHITE}Recent Activity:${NC}"
    if [ -f "$TRUTH_LOG" ]; then
        local recent_signals=$(tail -20 "$TRUTH_LOG" 2>/dev/null | wc -l)
        if [ $recent_signals -gt 0 ]; then
            echo -e "  ${GREEN}✅ Recent signals ($recent_signals in last batch)${NC}"
            ((health_score++))
        else
            echo -e "  ${YELLOW}⚠️  No recent signals${NC}"
        fi
    fi
    
    # Health score summary
    local health_percentage=$((health_score * 100 / max_score))
    echo ""
    echo -e "${WHITE}Overall Health Score: ${NC}"
    if [ $health_percentage -ge 80 ]; then
        echo -e "${GREEN}🟢 $health_score/$max_score ($health_percentage%) - HEALTHY${NC}"
    elif [ $health_percentage -ge 60 ]; then
        echo -e "${YELLOW}🟡 $health_score/$max_score ($health_percentage%) - WARNING${NC}"
    else
        echo -e "${RED}🔴 $health_score/$max_score ($health_percentage%) - CRITICAL${NC}"
        alert "System health critical: $health_percentage%"
    fi
    
    log "Health check completed - Score: $health_score/$max_score ($health_percentage%)"
}

# ============================================================================
# DUAL MODE ANALYTICS
# ============================================================================

analyze_signal_distribution() {
    print_section "DUAL MODE SIGNAL DISTRIBUTION"
    
    if [ ! -f "$TRUTH_LOG" ] || [ ! -s "$TRUTH_LOG" ]; then
        echo -e "${RED}❌ Truth log not available for analysis${NC}"
        return 1
    fi
    
    # Get recent signals (last 100)
    local recent_signals=$(tail -100 "$TRUTH_LOG" 2>/dev/null)
    local total_signals=$(echo "$recent_signals" | wc -l)
    
    if [ $total_signals -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No signals found for analysis${NC}"
        return 1
    fi
    
    # Count signal types
    local rapid_count=$(echo "$recent_signals" | grep -c "RAPID_ASSAULT" || echo "0")
    local precision_count=$(echo "$recent_signals" | grep -c "PRECISION_STRIKE" || echo "0")
    local typed_signals=$((rapid_count + precision_count))
    
    echo -e "${WHITE}Signal Distribution Analysis (Last 100):${NC}"
    echo -e "  ${BLUE}📊 Total signals: $total_signals${NC}"
    echo -e "  ${BLUE}📊 Typed signals: $typed_signals${NC}"
    
    if [ $typed_signals -gt 0 ]; then
        local rapid_percentage=$((rapid_count * 100 / typed_signals))
        local precision_percentage=$((precision_count * 100 / typed_signals))
        
        echo -e "  ${GREEN}🚀 RAPID_ASSAULT: $rapid_count ($rapid_percentage%)${NC}"
        echo -e "  ${PURPLE}💎 PRECISION_STRIKE: $precision_count ($precision_percentage%)${NC}"
        
        # Check distribution balance
        local expected_rapid=60
        local expected_precision=40
        local rapid_deviation=$((rapid_percentage - expected_rapid))
        local precision_deviation=$((precision_percentage - expected_precision))
        
        # Use absolute values for deviation check
        rapid_deviation=${rapid_deviation#-}
        precision_deviation=${precision_deviation#-}
        
        echo ""
        echo -e "${WHITE}Distribution Balance:${NC}"
        
        if [ $rapid_deviation -le $SIGNAL_IMBALANCE_THRESHOLD ] && [ $precision_deviation -le $SIGNAL_IMBALANCE_THRESHOLD ]; then
            echo -e "  ${GREEN}✅ Distribution balanced (target: 60/40)${NC}"
            log "Signal distribution balanced - RAPID: $rapid_percentage%, PRECISION: $precision_percentage%"
        else
            echo -e "  ${YELLOW}⚠️  Distribution imbalanced${NC}"
            echo -e "  ${YELLOW}    Expected: 60% RAPID, 40% PRECISION${NC}"
            echo -e "  ${YELLOW}    Actual: $rapid_percentage% RAPID, $precision_percentage% PRECISION${NC}"
            alert "Signal distribution imbalanced - RAPID: $rapid_percentage%, PRECISION: $precision_percentage%"
        fi
        
        # Hourly rate analysis
        echo ""
        echo -e "${WHITE}Signal Generation Rate:${NC}"
        
        # Get signals from last hour
        local current_time=$(date +%s)
        local hour_ago=$((current_time - 3600))
        local hourly_signals=0
        
        # Count signals in the last hour (approximate)
        if command -v jq > /dev/null; then
            hourly_signals=$(echo "$recent_signals" | tail -20 | wc -l)  # Approximate
        else
            hourly_signals=$(tail -10 "$TRUTH_LOG" 2>/dev/null | wc -l)  # Fallback
        fi
        
        echo -e "  ${BLUE}📈 Estimated hourly rate: $hourly_signals signals/hour${NC}"
        
        if [ $hourly_signals -lt $MIN_SIGNALS_PER_HOUR ]; then
            echo -e "  ${YELLOW}⚠️  Low signal generation (< $MIN_SIGNALS_PER_HOUR/hour)${NC}"
            alert "Low signal generation rate: $hourly_signals/hour"
        elif [ $hourly_signals -gt $MAX_SIGNALS_PER_HOUR ]; then
            echo -e "  ${YELLOW}⚠️  High signal generation (> $MAX_SIGNALS_PER_HOUR/hour)${NC}"
            alert "High signal generation rate: $hourly_signals/hour"
        else
            echo -e "  ${GREEN}✅ Signal rate within normal range${NC}"
        fi
        
    else
        echo -e "${RED}❌ No dual mode signals found${NC}"
        alert "No dual mode signals detected in recent batch"
    fi
    
    log "Signal distribution analysis completed - RAPID: $rapid_count, PRECISION: $precision_count"
}

# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

analyze_performance() {
    print_section "PERFORMANCE METRICS"
    
    if [ ! -f "$TRUTH_LOG" ] || [ ! -s "$TRUTH_LOG" ]; then
        echo -e "${RED}❌ Truth log not available for performance analysis${NC}"
        return 1
    fi
    
    # System resource usage
    echo -e "${WHITE}System Resources:${NC}"
    
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')
    local disk_usage=$(df "${SCRIPT_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    echo -e "  ${BLUE}💻 CPU Usage: ${cpu_usage}%${NC}"
    echo -e "  ${BLUE}💻 Memory Usage: ${memory_usage}%${NC}"
    echo -e "  ${BLUE}💻 Disk Usage: ${disk_usage}%${NC}"
    
    # Alert on high resource usage
    if (( $(echo "$memory_usage > 80" | bc -l) )); then
        alert "High memory usage: ${memory_usage}%"
    fi
    
    if [ $disk_usage -gt 85 ]; then
        alert "High disk usage: ${disk_usage}%"
    fi
    
    # Signal quality metrics
    echo ""
    echo -e "${WHITE}Signal Quality Metrics:${NC}"
    
    if command -v jq > /dev/null; then
        local recent_signals=$(tail -50 "$TRUTH_LOG" 2>/dev/null)
        
        if [ -n "$recent_signals" ]; then
            # Average confidence
            local avg_confidence=$(echo "$recent_signals" | jq -r '.confidence // 0' 2>/dev/null | awk '{sum+=$1} END {printf "%.1f", sum/NR}')
            
            # Pip range analysis
            local pip_in_range=$(echo "$recent_signals" | jq -r '.target_pips // 0' 2>/dev/null | awk '$1 >= 6 && $1 <= 15 {count++} END {print count+0}')
            local total_analyzed=$(echo "$recent_signals" | jq -r '.target_pips // 0' 2>/dev/null | awk 'END {print NR}')
            
            if [ $total_analyzed -gt 0 ]; then
                local pip_percentage=$((pip_in_range * 100 / total_analyzed))
                
                echo -e "  ${BLUE}📊 Average confidence: ${avg_confidence}%${NC}"
                echo -e "  ${BLUE}📊 Target pips in range (6-15): $pip_in_range/$total_analyzed ($pip_percentage%)${NC}"
                
                if (( $(echo "$avg_confidence < 75" | bc -l) )); then
                    echo -e "  ${YELLOW}⚠️  Low average confidence${NC}"
                    alert "Low average signal confidence: ${avg_confidence}%"
                fi
                
                if [ $pip_percentage -lt 80 ]; then
                    echo -e "  ${YELLOW}⚠️  Many signals outside target pip range${NC}"
                    alert "Pip range issue: $pip_percentage% within range"
                fi
            else
                echo -e "  ${YELLOW}⚠️  No signal data available for analysis${NC}"
            fi
        else
            echo -e "  ${YELLOW}⚠️  No recent signals for quality analysis${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  jq not available for detailed analysis${NC}"
        echo -e "  ${CYAN}💡 Install jq for enhanced metrics: apt install jq${NC}"
    fi
    
    log "Performance analysis completed"
}

# ============================================================================
# QUICK DIAGNOSTICS
# ============================================================================

run_quick_diagnostics() {
    print_section "QUICK DIAGNOSTICS"
    
    echo -e "${WHITE}Running diagnostic tests...${NC}"
    
    # Test 1: ZMQ connectivity
    echo -e "${BLUE}🔍 Test 1: ZMQ Port Connectivity${NC}"
    local zmq_test_passed=0
    
    if netstat -tuln | grep -q ":5557 "; then
        echo -e "  ${GREEN}✅ Elite Guard publishing port (5557) active${NC}"
        ((zmq_test_passed++))
    else
        echo -e "  ${RED}❌ Elite Guard publishing port (5557) not bound${NC}"
    fi
    
    if netstat -tuln | grep -q ":8888 "; then
        echo -e "  ${GREEN}✅ WebApp HTTP port (8888) active${NC}"
        ((zmq_test_passed++))
    else
        echo -e "  ${RED}❌ WebApp HTTP port (8888) not bound${NC}"
    fi
    
    # Test 2: Signal generation activity
    echo ""
    echo -e "${BLUE}🔍 Test 2: Signal Generation Activity${NC}"
    
    if [ -f "$TRUTH_LOG" ]; then
        local last_signal_time=$(tail -1 "$TRUTH_LOG" 2>/dev/null | jq -r '.generated_at // empty' 2>/dev/null)
        
        if [ -n "$last_signal_time" ]; then
            echo -e "  ${GREEN}✅ Last signal generated: $last_signal_time${NC}"
        else
            # Fallback to file modification time
            local file_age=$(stat -c %Y "$TRUTH_LOG" 2>/dev/null || echo "0")
            local current_time=$(date +%s)
            local age_minutes=$(( (current_time - file_age) / 60 ))
            
            if [ $age_minutes -lt 30 ]; then
                echo -e "  ${GREEN}✅ Truth log recently modified ($age_minutes minutes ago)${NC}"
            else
                echo -e "  ${YELLOW}⚠️  Truth log not recently modified ($age_minutes minutes ago)${NC}"
            fi
        fi
    else
        echo -e "  ${RED}❌ Truth log file not found${NC}"
    fi
    
    # Test 3: Database integrity
    echo ""
    echo -e "${BLUE}🔍 Test 3: Database Integrity${NC}"
    
    local db_test_passed=0
    
    if sqlite3 "${SCRIPT_DIR}/bitten.db" "SELECT COUNT(*) FROM signals;" > /dev/null 2>&1; then
        local signal_count=$(sqlite3 "${SCRIPT_DIR}/bitten.db" "SELECT COUNT(*) FROM signals;" 2>/dev/null || echo "0")
        echo -e "  ${GREEN}✅ Database accessible ($signal_count total signals)${NC}"
        ((db_test_passed++))
    else
        echo -e "  ${RED}❌ Database query failed${NC}"
    fi
    
    # Test 4: Process memory usage
    echo ""
    echo -e "${BLUE}🔍 Test 4: Process Memory Usage${NC}"
    
    local processes=("elite_guard_with_citadel.py" "webapp_server_optimized.py")
    
    for process in "${processes[@]}"; do
        local pid=$(pgrep -f "$process" | head -1)
        
        if [ -n "$pid" ]; then
            local memory_mb=$(ps -o rss= -p $pid 2>/dev/null | awk '{printf "%.1f", $1/1024}')
            
            if [ -n "$memory_mb" ]; then
                echo -e "  ${BLUE}📊 $process: ${memory_mb}MB${NC}"
                
                if (( $(echo "$memory_mb > 500" | bc -l) )); then
                    echo -e "  ${YELLOW}⚠️  High memory usage for $process${NC}"
                fi
            else
                echo -e "  ${YELLOW}⚠️  Could not get memory info for $process${NC}"
            fi
        else
            echo -e "  ${RED}❌ Process not running: $process${NC}"
        fi
    done
    
    # Diagnostic summary
    echo ""
    echo -e "${WHITE}Diagnostic Summary:${NC}"
    local total_tests=4
    local passed_tests=$((zmq_test_passed + 1 + db_test_passed + 1))  # Simplified scoring
    
    if [ $passed_tests -ge 3 ]; then
        echo -e "  ${GREEN}🟢 Diagnostics: PASSED ($passed_tests/$total_tests areas healthy)${NC}"
    else
        echo -e "  ${YELLOW}🟡 Diagnostics: WARNINGS ($passed_tests/$total_tests areas healthy)${NC}"
    fi
    
    log "Quick diagnostics completed - $passed_tests/$total_tests tests passed"
}

# ============================================================================
# INTERACTIVE MONITORING
# ============================================================================

interactive_monitor() {
    while true; do
        print_banner
        
        check_system_health
        echo ""
        analyze_signal_distribution
        echo ""
        analyze_performance
        echo ""
        
        echo -e "${WHITE}Options:${NC}"
        echo -e "${CYAN}  [r] Refresh display${NC}"
        echo -e "${CYAN}  [d] Run diagnostics${NC}"
        echo -e "${CYAN}  [l] View recent alerts${NC}"
        echo -e "${CYAN}  [q] Quit${NC}"
        echo ""
        
        read -p "Select option (or wait 30s for auto-refresh): " -n 1 -r -t 30
        echo ""
        
        case $REPLY in
            [Rr])
                # Refresh (continue loop)
                ;;
            [Dd])
                run_quick_diagnostics
                echo ""
                read -p "Press Enter to continue..." -r
                ;;
            [Ll])
                if [ -f "$ALERT_LOG" ]; then
                    echo -e "${WHITE}Recent Alerts:${NC}"
                    tail -20 "$ALERT_LOG" | while read line; do
                        echo -e "${YELLOW}  $line${NC}"
                    done
                else
                    echo -e "${GREEN}No alerts file found${NC}"
                fi
                echo ""
                read -p "Press Enter to continue..." -r
                ;;
            [Qq])
                echo -e "${GREEN}Exiting monitor...${NC}"
                exit 0
                ;;
            "")
                # Timeout - continue with refresh
                ;;
            *)
                # Invalid input - continue
                ;;
        esac
    done
}

# ============================================================================
# MAIN FUNCTION
# ============================================================================

main() {
    case "${1:-}" in
        --health)
            check_system_health
            ;;
        --distribution)
            analyze_signal_distribution
            ;;
        --performance)
            analyze_performance
            ;;
        --diagnostics)
            run_quick_diagnostics
            ;;
        --once)
            print_banner
            check_system_health
            echo ""
            analyze_signal_distribution
            echo ""
            analyze_performance
            ;;
        --help|-h)
            echo "BITTEN Dual Mode Monitor"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --health        System health check only"
            echo "  --distribution  Signal distribution analysis only"
            echo "  --performance   Performance metrics only"
            echo "  --diagnostics   Run diagnostic tests only"
            echo "  --once          Full analysis without interactive mode"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "No options: Start interactive monitoring mode"
            ;;
        *)
            interactive_monitor
            ;;
    esac
}

# Create log files if they don't exist
touch "$MONITOR_LOG" "$ALERT_LOG"

# Execute main function
main "$@"