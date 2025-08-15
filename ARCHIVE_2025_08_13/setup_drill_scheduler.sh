#!/bin/bash

# =============================================================================
# BITTEN Daily Drill Report Scheduler Setup
# Sets up automated cron job for 6 PM daily drill reports
# =============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project settings
PROJECT_ROOT="/root/HydraX-v2"
SCRIPT_PATH="$PROJECT_ROOT/send_daily_drill_reports.py"
LOG_DIR="$PROJECT_ROOT/logs"
CRON_TIME="0 18 * * *"  # 6 PM daily
PYTHON_PATH=$(which python3)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "🪖 BITTEN DRILL REPORT SCHEDULER SETUP"
    echo "======================================"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        print_warning "This script should be run as root or with sudo for system-wide cron setup"
        print_status "Continuing with user-level cron setup..."
    fi
    
    # Check if project directory exists
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        print_error "Project directory not found: $PROJECT_ROOT"
        exit 1
    fi
    
    # Check if Python script exists
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        print_error "Drill report script not found: $SCRIPT_PATH"
        exit 1
    fi
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    print_success "Prerequisites check passed"
}

# Function to make script executable
setup_script_permissions() {
    print_status "Setting up script permissions..."
    
    chmod +x "$SCRIPT_PATH"
    
    if [[ -x "$SCRIPT_PATH" ]]; then
        print_success "Script made executable"
    else
        print_error "Failed to make script executable"
        exit 1
    fi
}

# Function to test the script
test_script() {
    print_status "Testing drill report script..."
    
    # Test health check
    if python3 "$SCRIPT_PATH" health; then
        print_success "Health check passed"
    else
        print_warning "Health check failed - script may still work but check logs"
    fi
    
    # Test import dependencies
    print_status "Testing Python dependencies..."
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from src.bitten_core.daily_drill_report import DailyDrillReportSystem
    print('✅ Drill report system import successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" || {
        print_error "Python dependencies test failed"
        exit 1
    }
    
    print_success "Script testing completed"
}

# Function to setup cron job
setup_cron_job() {
    print_status "Setting up cron job..."
    
    # Define the cron job entry
    CRON_JOB="$CRON_TIME cd $PROJECT_ROOT && $PYTHON_PATH $SCRIPT_PATH >> $LOG_DIR/drill_scheduler_cron.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "send_daily_drill_reports.py"; then
        print_warning "Drill report cron job already exists"
        
        # Ask user if they want to replace it
        read -p "Do you want to replace the existing cron job? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Keeping existing cron job"
            return 0
        fi
        
        # Remove existing cron job
        crontab -l 2>/dev/null | grep -v "send_daily_drill_reports.py" | crontab -
        print_status "Removed existing cron job"
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    if crontab -l 2>/dev/null | grep -q "send_daily_drill_reports.py"; then
        print_success "Cron job added successfully"
        print_status "Cron job: $CRON_JOB"
    else
        print_error "Failed to add cron job"
        exit 1
    fi
}

# Function to setup log rotation
setup_log_rotation() {
    print_status "Setting up log rotation..."
    
    # Create logrotate configuration
    LOGROTATE_CONFIG="/etc/logrotate.d/bitten-drill-reports"
    
    if [[ $EUID -eq 0 ]]; then
        cat > "$LOGROTATE_CONFIG" << EOF
$LOG_DIR/drill_reports_scheduler.log
$LOG_DIR/drill_scheduler_cron.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF
        print_success "Log rotation configured"
    else
        print_warning "Skipping log rotation setup (requires root access)"
    fi
}

# Function to create monitoring script
create_monitoring_script() {
    print_status "Creating monitoring script..."
    
    MONITOR_SCRIPT="$PROJECT_ROOT/monitor_drill_reports.sh"
    
    cat > "$MONITOR_SCRIPT" << 'EOF'
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
EOF

    chmod +x "$MONITOR_SCRIPT"
    print_success "Monitoring script created: $MONITOR_SCRIPT"
}

# Function to show next execution time
show_next_execution() {
    print_status "Calculating next execution time..."
    
    # Get current time and next 6 PM
    CURRENT_HOUR=$(date +%H)
    TODAY_6PM=$(date -d "today 18:00" "+%Y-%m-%d %H:%M:%S")
    TOMORROW_6PM=$(date -d "tomorrow 18:00" "+%Y-%m-%d %H:%M:%S")
    
    if [[ $CURRENT_HOUR -lt 18 ]]; then
        NEXT_EXECUTION="$TODAY_6PM"
    else
        NEXT_EXECUTION="$TOMORROW_6PM"
    fi
    
    print_success "Next execution: $NEXT_EXECUTION"
}

# Function to run dry test
run_dry_test() {
    print_status "Running dry test execution..."
    
    read -p "Do you want to run a test execution now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Executing test run..."
        cd "$PROJECT_ROOT"
        python3 "$SCRIPT_PATH" || print_warning "Test execution failed - check logs for details"
    else
        print_status "Skipping test execution"
    fi
}

# Function to display setup summary
display_summary() {
    echo ""
    echo "🎯 SETUP COMPLETE!"
    echo "=================="
    echo ""
    print_success "Daily drill report scheduler is now active"
    echo ""
    echo "📋 Configuration:"
    echo "  • Schedule: Daily at 6:00 PM"
    echo "  • Script: $SCRIPT_PATH"
    echo "  • Logs: $LOG_DIR/"
    echo "  • Monitor: $PROJECT_ROOT/monitor_drill_reports.sh"
    echo ""
    echo "🔧 Management commands:"
    echo "  • View cron jobs: crontab -l"
    echo "  • Edit cron jobs: crontab -e"
    echo "  • Remove this job: crontab -l | grep -v send_daily_drill_reports.py | crontab -"
    echo "  • Test health: python3 $SCRIPT_PATH health"
    echo "  • Monitor status: $PROJECT_ROOT/monitor_drill_reports.sh"
    echo ""
    echo "📊 The system will now automatically send drill reports to all users"
    echo "    with daily trading stats every day at 6 PM."
    echo ""
    print_success "DRILL SERGEANT SCHEDULER READY FOR DUTY! 🪖"
}

# Main execution
main() {
    print_header
    
    # Execute setup steps
    check_prerequisites
    setup_script_permissions
    test_script
    setup_cron_job
    setup_log_rotation
    create_monitoring_script
    show_next_execution
    run_dry_test
    display_summary
}

# Handle script interruption
trap 'print_error "Setup interrupted"; exit 1' INT TERM

# Execute main function
main "$@"