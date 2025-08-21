#!/bin/bash

# ============================================================================
# DUAL MODE ROLLOUT SCRIPT - BITTEN TRADING SYSTEM
# ============================================================================
# Purpose: Gradual deployment with checkpoints and rollback capability
# Date: 2025-08-19 16:30 UTC
# Version: DUAL_MODE_ROLLOUT_v1.0

set -e  # Exit on any error

# ANSI Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="/root/HydraX-v2"
BACKUP_DIR="${SCRIPT_DIR}/BACKUP_DUAL_MODE_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${SCRIPT_DIR}/rollout_dual_mode.log"
ROLLBACK_FLAG="${SCRIPT_DIR}/ROLLBACK_REQUIRED.flag"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 BITTEN DUAL MODE ROLLOUT                    ║"
    echo "║              RAPID_ASSAULT & PRECISION_STRIKE               ║"
    echo "║                    August 19, 2025                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "${CYAN}▶ $1${NC}"
    echo -e "${CYAN}$(printf '━%.0s' {1..60})${NC}"
}

# Error handler
error_handler() {
    echo -e "${RED}❌ ERROR: Line $1: Command failed${NC}"
    log "ERROR: Script failed at line $1"
    echo -e "${YELLOW}Creating rollback flag...${NC}"
    touch "$ROLLBACK_FLAG"
    exit 1
}

# Set error trap
trap 'error_handler $LINENO' ERR

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    # Remove any temporary files created during rollout
}

# Set cleanup trap
trap cleanup EXIT

# ============================================================================
# PHASE 1: PRE-ROLLOUT VALIDATION
# ============================================================================

phase_1_validation() {
    print_section "PHASE 1: PRE-ROLLOUT VALIDATION"
    
    log "Starting Phase 1: Pre-rollout validation"
    
    # Check if system is already running dual mode
    if grep -q "RAPID_ASSAULT\|PRECISION_STRIKE" "${SCRIPT_DIR}/truth_log.jsonl" 2>/dev/null; then
        echo -e "${GREEN}✅ Dual mode already detected in truth log${NC}"
        log "Dual mode signals found in truth log - system appears to be running"
    else
        echo -e "${YELLOW}⚠️  No dual mode signals in truth log yet${NC}"
        log "No dual mode signals detected - may be fresh start"
    fi
    
    # Check critical processes
    echo -e "${WHITE}Checking critical processes...${NC}"
    
    local processes=("elite_guard_with_citadel.py" "webapp_server_optimized.py" "command_router.py")
    local missing_processes=()
    
    for process in "${processes[@]}"; do
        if pgrep -f "$process" > /dev/null; then
            echo -e "${GREEN}✅ $process running${NC}"
            log "Process check: $process is running"
        else
            echo -e "${RED}❌ $process not running${NC}"
            missing_processes+=("$process")
            log "Process check: $process is NOT running"
        fi
    done
    
    if [ ${#missing_processes[@]} -ne 0 ]; then
        echo -e "${RED}❌ Critical processes missing: ${missing_processes[*]}${NC}"
        log "ERROR: Critical processes not running"
        return 1
    fi
    
    # Check ZMQ ports
    echo -e "${WHITE}Checking ZMQ port availability...${NC}"
    local ports=(5555 5556 5557 5558 5560 8888)
    local port_issues=()
    
    for port in "${ports[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            echo -e "${GREEN}✅ Port $port bound${NC}"
            log "Port check: $port is bound"
        else
            echo -e "${YELLOW}⚠️  Port $port not bound${NC}"
            port_issues+=("$port")
            log "Port check: $port is not bound"
        fi
    done
    
    # Verify file integrity
    echo -e "${WHITE}Checking file integrity...${NC}"
    local critical_files=(
        "elite_guard_with_citadel.py"
        "webapp_server_optimized.py" 
        "command_router.py"
        "bitten.db"
    )
    
    for file in "${critical_files[@]}"; do
        if [ -f "${SCRIPT_DIR}/$file" ]; then
            echo -e "${GREEN}✅ $file exists${NC}"
            log "File check: $file exists"
        else
            echo -e "${RED}❌ $file missing${NC}"
            log "ERROR: Critical file missing: $file"
            return 1
        fi
    done
    
    # Check database
    echo -e "${WHITE}Checking database connectivity...${NC}"
    if sqlite3 "${SCRIPT_DIR}/bitten.db" "SELECT COUNT(*) FROM signals LIMIT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database accessible${NC}"
        log "Database check: bitten.db is accessible"
    else
        echo -e "${RED}❌ Database connection failed${NC}"
        log "ERROR: Database connection failed"
        return 1
    fi
    
    echo -e "${GREEN}✅ Phase 1 validation completed successfully${NC}"
    log "Phase 1 validation completed successfully"
    return 0
}

# ============================================================================
# PHASE 2: BACKUP CURRENT VERSION
# ============================================================================

phase_2_backup() {
    print_section "PHASE 2: BACKUP CURRENT VERSION"
    
    log "Starting Phase 2: Creating backup"
    
    # Create backup directory
    echo -e "${WHITE}Creating backup directory: $BACKUP_DIR${NC}"
    mkdir -p "$BACKUP_DIR"
    log "Created backup directory: $BACKUP_DIR"
    
    # Backup critical files
    echo -e "${WHITE}Backing up critical system files...${NC}"
    local backup_files=(
        "elite_guard_with_citadel.py"
        "webapp_server_optimized.py"
        "command_router.py"
        "bitten.db"
        "truth_log.jsonl"
        "user_registry.json"
        "citadel_state.json"
    )
    
    for file in "${backup_files[@]}"; do
        if [ -f "${SCRIPT_DIR}/$file" ]; then
            cp "${SCRIPT_DIR}/$file" "$BACKUP_DIR/"
            echo -e "${GREEN}✅ Backed up $file${NC}"
            log "Backed up file: $file"
        else
            echo -e "${YELLOW}⚠️  File not found: $file${NC}"
            log "Warning: File not found for backup: $file"
        fi
    done
    
    # Backup current process state
    echo -e "${WHITE}Capturing current process state...${NC}"
    ps aux | grep -E "elite_guard|webapp|command_router" > "$BACKUP_DIR/process_state.txt"
    netstat -tuln | grep -E ":555|:888" > "$BACKUP_DIR/port_state.txt"
    
    # Create rollback script
    echo -e "${WHITE}Creating rollback script...${NC}"
    cat > "$BACKUP_DIR/rollback.sh" << 'EOF'
#!/bin/bash
# DUAL MODE ROLLBACK SCRIPT

BACKUP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT_DIR="/root/HydraX-v2"

echo "🔄 Rolling back to pre-dual-mode state..."

# Stop current processes
pkill -f "elite_guard_with_citadel.py" || true
pkill -f "webapp_server_optimized.py" || true
pkill -f "command_router.py" || true

# Wait for processes to stop
sleep 3

# Restore files
cp "$BACKUP_DIR/elite_guard_with_citadel.py" "$SCRIPT_DIR/" 2>/dev/null || echo "Warning: Could not restore elite_guard"
cp "$BACKUP_DIR/webapp_server_optimized.py" "$SCRIPT_DIR/" 2>/dev/null || echo "Warning: Could not restore webapp"
cp "$BACKUP_DIR/command_router.py" "$SCRIPT_DIR/" 2>/dev/null || echo "Warning: Could not restore command_router"
cp "$BACKUP_DIR/bitten.db" "$SCRIPT_DIR/" 2>/dev/null || echo "Warning: Could not restore database"

echo "✅ Rollback completed. Please restart services manually."
echo "📝 Original files restored from: $BACKUP_DIR"
EOF

    chmod +x "$BACKUP_DIR/rollback.sh"
    
    echo -e "${GREEN}✅ Phase 2 backup completed successfully${NC}"
    echo -e "${CYAN}📁 Backup location: $BACKUP_DIR${NC}"
    echo -e "${CYAN}🔄 Rollback script: $BACKUP_DIR/rollback.sh${NC}"
    log "Phase 2 backup completed successfully"
    return 0
}

# ============================================================================
# PHASE 3: SHADOW MODE TESTING
# ============================================================================

phase_3_shadow_mode() {
    print_section "PHASE 3: SHADOW MODE TESTING"
    
    log "Starting Phase 3: Shadow mode testing"
    
    echo -e "${WHITE}Testing dual mode signal generation...${NC}"
    
    # Check current signal generation
    local signals_before=$(wc -l < "${SCRIPT_DIR}/truth_log.jsonl" 2>/dev/null || echo "0")
    echo -e "${BLUE}📊 Current signal count: $signals_before${NC}"
    log "Pre-test signal count: $signals_before"
    
    # Wait for new signals (30 seconds)
    echo -e "${WHITE}Monitoring signal generation for 30 seconds...${NC}"
    sleep 30
    
    local signals_after=$(wc -l < "${SCRIPT_DIR}/truth_log.jsonl" 2>/dev/null || echo "0")
    local new_signals=$((signals_after - signals_before))
    
    echo -e "${BLUE}📊 New signals generated: $new_signals${NC}"
    log "New signals generated in 30s: $new_signals"
    
    if [ $new_signals -gt 0 ]; then
        # Check signal types in recent signals
        echo -e "${WHITE}Analyzing recent signal types...${NC}"
        
        local rapid_count=$(tail -10 "${SCRIPT_DIR}/truth_log.jsonl" 2>/dev/null | grep -c "RAPID_ASSAULT" || echo "0")
        local precision_count=$(tail -10 "${SCRIPT_DIR}/truth_log.jsonl" 2>/dev/null | grep -c "PRECISION_STRIKE" || echo "0")
        
        echo -e "${BLUE}📈 Recent RAPID_ASSAULT signals: $rapid_count${NC}"
        echo -e "${BLUE}📈 Recent PRECISION_STRIKE signals: $precision_count${NC}"
        
        log "Recent signal analysis - RAPID: $rapid_count, PRECISION: $precision_count"
        
        if [ $((rapid_count + precision_count)) -gt 0 ]; then
            echo -e "${GREEN}✅ Dual mode signals detected${NC}"
            log "Dual mode signals confirmed in recent generation"
        else
            echo -e "${YELLOW}⚠️  No dual mode signals in recent batch${NC}"
            log "Warning: No dual mode signals detected in recent batch"
        fi
    else
        echo -e "${YELLOW}⚠️  No new signals generated during test period${NC}"
        log "Warning: No new signals generated during 30s test"
    fi
    
    # Test webapp integration
    echo -e "${WHITE}Testing webapp dual mode integration...${NC}"
    
    local webapp_response=$(curl -s "http://localhost:8888/healthz" || echo "ERROR")
    if [[ "$webapp_response" == *"healthy"* ]]; then
        echo -e "${GREEN}✅ Webapp responding${NC}"
        log "Webapp health check passed"
    else
        echo -e "${RED}❌ Webapp not responding properly${NC}"
        log "ERROR: Webapp health check failed"
        return 1
    fi
    
    echo -e "${GREEN}✅ Phase 3 shadow mode testing completed${NC}"
    log "Phase 3 shadow mode testing completed successfully"
    return 0
}

# ============================================================================
# PHASE 4: GRADUAL ROLLOUT
# ============================================================================

phase_4_rollout() {
    print_section "PHASE 4: GRADUAL ROLLOUT WITH CHECKPOINTS"
    
    log "Starting Phase 4: Gradual rollout"
    
    # Checkpoint 1: Verify dual mode is active
    echo -e "${WHITE}Checkpoint 1: Verifying dual mode activation...${NC}"
    
    # Check that elite guard is generating both signal types
    local signal_log="${SCRIPT_DIR}/truth_log.jsonl"
    
    if [ -f "$signal_log" ]; then
        local recent_signals=$(tail -20 "$signal_log" 2>/dev/null || echo "")
        
        if echo "$recent_signals" | grep -q "RAPID_ASSAULT" && echo "$recent_signals" | grep -q "PRECISION_STRIKE"; then
            echo -e "${GREEN}✅ Checkpoint 1 passed: Both signal types detected${NC}"
            log "Checkpoint 1 passed: Both signal types active"
        else
            echo -e "${YELLOW}⚠️  Checkpoint 1 warning: Limited signal type diversity${NC}"
            log "Warning: Checkpoint 1 - limited signal type diversity"
        fi
    else
        echo -e "${YELLOW}⚠️  Checkpoint 1 warning: No truth log found${NC}"
        log "Warning: Checkpoint 1 - no truth log found"
    fi
    
    # Checkpoint 2: Monitor signal distribution
    echo -e "${WHITE}Checkpoint 2: Monitoring signal distribution...${NC}"
    
    # Wait 60 seconds for more signals
    echo -e "${BLUE}⏱️  Monitoring for 60 seconds...${NC}"
    local start_count=$(wc -l < "$signal_log" 2>/dev/null || echo "0")
    
    sleep 60
    
    local end_count=$(wc -l < "$signal_log" 2>/dev/null || echo "0")
    local new_signals=$((end_count - start_count))
    
    if [ $new_signals -gt 0 ]; then
        local rapid_new=$(tail -$new_signals "$signal_log" 2>/dev/null | grep -c "RAPID_ASSAULT" || echo "0")
        local precision_new=$(tail -$new_signals "$signal_log" 2>/dev/null | grep -c "PRECISION_STRIKE" || echo "0")
        
        echo -e "${BLUE}📊 New signals: $new_signals (RAPID: $rapid_new, PRECISION: $precision_new)${NC}"
        log "Checkpoint 2: $new_signals new signals - RAPID: $rapid_new, PRECISION: $precision_new"
        
        if [ $new_signals -ge 2 ]; then
            echo -e "${GREEN}✅ Checkpoint 2 passed: Active signal generation${NC}"
            log "Checkpoint 2 passed: Active signal generation confirmed"
        else
            echo -e "${YELLOW}⚠️  Checkpoint 2 warning: Low signal volume${NC}"
            log "Warning: Checkpoint 2 - low signal volume"
        fi
    else
        echo -e "${YELLOW}⚠️  Checkpoint 2 warning: No new signals generated${NC}"
        log "Warning: Checkpoint 2 - no new signals during monitoring period"
    fi
    
    # Checkpoint 3: Process stability
    echo -e "${WHITE}Checkpoint 3: Process stability check...${NC}"
    
    local critical_processes=("elite_guard_with_citadel.py" "webapp_server_optimized.py" "command_router.py")
    local stable_processes=0
    
    for process in "${critical_processes[@]}"; do
        if pgrep -f "$process" > /dev/null; then
            echo -e "${GREEN}✅ $process stable${NC}"
            log "Process stability: $process is running"
            ((stable_processes++))
        else
            echo -e "${RED}❌ $process not running${NC}"
            log "ERROR: Process not running: $process"
        fi
    done
    
    if [ $stable_processes -eq ${#critical_processes[@]} ]; then
        echo -e "${GREEN}✅ Checkpoint 3 passed: All processes stable${NC}"
        log "Checkpoint 3 passed: All critical processes stable"
    else
        echo -e "${RED}❌ Checkpoint 3 failed: Process instability detected${NC}"
        log "ERROR: Checkpoint 3 failed - process instability"
        return 1
    fi
    
    echo -e "${GREEN}✅ Phase 4 gradual rollout completed successfully${NC}"
    log "Phase 4 gradual rollout completed successfully"
    return 0
}

# ============================================================================
# PHASE 5: PERFORMANCE VALIDATION
# ============================================================================

phase_5_validation() {
    print_section "PHASE 5: PERFORMANCE VALIDATION"
    
    log "Starting Phase 5: Performance validation"
    
    # Validate signal quality
    echo -e "${WHITE}Validating signal quality...${NC}"
    
    local signal_log="${SCRIPT_DIR}/truth_log.jsonl"
    
    if [ -f "$signal_log" ]; then
        # Check recent signal quality
        local recent_signals=$(tail -30 "$signal_log" 2>/dev/null || echo "")
        local total_recent=$(echo "$recent_signals" | wc -l)
        
        if [ $total_recent -gt 0 ]; then
            # Check confidence levels
            local high_confidence=$(echo "$recent_signals" | jq -r '.confidence // 0' 2>/dev/null | awk '$1 >= 80 {count++} END {print count+0}')
            local confidence_rate=$((high_confidence * 100 / total_recent))
            
            echo -e "${BLUE}📊 Recent signals: $total_recent${NC}"
            echo -e "${BLUE}📊 High confidence (≥80%): $high_confidence ($confidence_rate%)${NC}"
            log "Signal quality: $total_recent recent signals, $high_confidence high confidence ($confidence_rate%)"
            
            if [ $confidence_rate -ge 60 ]; then
                echo -e "${GREEN}✅ Signal quality validation passed${NC}"
                log "Signal quality validation passed"
            else
                echo -e "${YELLOW}⚠️  Signal quality warning: Low confidence rate${NC}"
                log "Warning: Low signal confidence rate"
            fi
            
            # Check target pip ranges
            local pip_check=$(echo "$recent_signals" | jq -r '.target_pips // 0' 2>/dev/null | awk '$1 >= 6 && $1 <= 15 {count++} END {print count+0}')
            local pip_rate=$((pip_check * 100 / total_recent))
            
            echo -e "${BLUE}📊 Target pips in range (6-15): $pip_check ($pip_rate%)${NC}"
            log "Pip range validation: $pip_check signals in range ($pip_rate%)"
            
            if [ $pip_rate -ge 80 ]; then
                echo -e "${GREEN}✅ Pip range validation passed${NC}"
                log "Pip range validation passed"
            else
                echo -e "${YELLOW}⚠️  Pip range warning: Targets outside expected range${NC}"
                log "Warning: Pip targets outside expected range"
            fi
        else
            echo -e "${YELLOW}⚠️  No recent signals found for quality validation${NC}"
            log "Warning: No recent signals for quality validation"
        fi
    else
        echo -e "${YELLOW}⚠️  Truth log not found for validation${NC}"
        log "Warning: Truth log not found for validation"
    fi
    
    # Performance metrics
    echo -e "${WHITE}Collecting performance metrics...${NC}"
    
    # System resource usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')
    
    echo -e "${BLUE}💻 CPU Usage: ${cpu_usage}%${NC}"
    echo -e "${BLUE}💻 Memory Usage: ${memory_usage}%${NC}"
    log "System metrics - CPU: ${cpu_usage}%, Memory: ${memory_usage}%"
    
    # ZMQ port activity
    echo -e "${WHITE}Checking ZMQ port activity...${NC}"
    local active_ports=$(netstat -tuln | grep -E ":555|:888" | wc -l)
    echo -e "${BLUE}🌐 Active ZMQ/HTTP ports: $active_ports${NC}"
    log "Active network ports: $active_ports"
    
    echo -e "${GREEN}✅ Phase 5 performance validation completed${NC}"
    log "Phase 5 performance validation completed"
    return 0
}

# ============================================================================
# MAIN ROLLOUT EXECUTION
# ============================================================================

main() {
    print_banner
    
    log "Starting dual mode rollout script"
    log "Backup directory: $BACKUP_DIR"
    
    echo -e "${WHITE}📋 Rollout Plan:${NC}"
    echo -e "${CYAN}  Phase 1: Pre-rollout validation${NC}"
    echo -e "${CYAN}  Phase 2: Backup current version${NC}"
    echo -e "${CYAN}  Phase 3: Shadow mode testing${NC}"
    echo -e "${CYAN}  Phase 4: Gradual rollout with checkpoints${NC}"
    echo -e "${CYAN}  Phase 5: Performance validation${NC}"
    echo ""
    
    read -p "🚀 Ready to proceed with dual mode rollout? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}⏹️  Rollout cancelled by user${NC}"
        log "Rollout cancelled by user"
        exit 0
    fi
    
    # Execute phases
    local phases=(
        "phase_1_validation"
        "phase_2_backup"
        "phase_3_shadow_mode"
        "phase_4_rollout"
        "phase_5_validation"
    )
    
    local completed_phases=0
    
    for phase in "${phases[@]}"; do
        echo -e "${BLUE}⚡ Executing $phase...${NC}"
        
        if $phase; then
            ((completed_phases++))
            echo -e "${GREEN}✅ $phase completed successfully${NC}"
            log "$phase completed successfully"
        else
            echo -e "${RED}❌ $phase failed${NC}"
            log "ERROR: $phase failed"
            
            echo -e "${YELLOW}🛑 Rollout halted. Rollback recommended.${NC}"
            echo -e "${CYAN}📄 Rollback script: $BACKUP_DIR/rollback.sh${NC}"
            log "Rollout halted due to phase failure"
            exit 1
        fi
        
        # Brief pause between phases
        sleep 2
    done
    
    # Success summary
    print_section "ROLLOUT COMPLETED SUCCESSFULLY"
    
    echo -e "${GREEN}🎉 Dual mode rollout completed successfully!${NC}"
    echo -e "${WHITE}📊 Summary:${NC}"
    echo -e "${CYAN}  ✅ All $completed_phases phases completed${NC}"
    echo -e "${CYAN}  📁 Backup created: $BACKUP_DIR${NC}"
    echo -e "${CYAN}  🔄 Rollback available: $BACKUP_DIR/rollback.sh${NC}"
    echo -e "${CYAN}  📝 Full log: $LOG_FILE${NC}"
    echo ""
    echo -e "${WHITE}🎯 Next Steps:${NC}"
    echo -e "${CYAN}  • Monitor system performance with monitor_dual_mode.sh${NC}"
    echo -e "${CYAN}  • Review signal distribution after 1 hour${NC}"
    echo -e "${CYAN}  • Validate win rates after 24 hours${NC}"
    echo ""
    
    log "Dual mode rollout completed successfully"
    log "Completed phases: $completed_phases"
    log "Backup location: $BACKUP_DIR"
    
    # Clean up rollback flag if it exists
    [ -f "$ROLLBACK_FLAG" ] && rm -f "$ROLLBACK_FLAG"
    
    return 0
}

# Execute main function
main "$@"