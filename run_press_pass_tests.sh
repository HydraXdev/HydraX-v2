#!/bin/bash
#
# Press Pass Test Runner Script
# Executes Press Pass tests with proper error handling
#

echo "🎫 BITTEN Press Pass Test Suite"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to run a test with error handling
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo ""
    echo "Running: $test_name"
    echo "----------------------------------------"
    
    if $test_command; then
        echo "✅ $test_name completed successfully"
    else
        echo "❌ $test_name failed with exit code $?"
        echo "Check logs for details"
    fi
}

# Main menu
echo ""
echo "Select test option:"
echo "1. Run full comprehensive test suite"
echo "2. Test Press Pass activation only"
echo "3. Test XP reset functionality"
echo "4. Test warning notifications"
echo "5. Test demo account provisioning"
echo "6. Test conversion to paid tier"
echo "7. Run interactive test mode"
echo "8. Generate test report"
echo ""

read -p "Enter choice (1-8): " choice

case $choice in
    1)
        echo "Running full test suite..."
        run_test "Comprehensive Test Suite" "python3 test_press_pass_comprehensive.py"
        ;;
    2)
        echo "Testing Press Pass activation..."
        run_test "Activation Test" "python3 test_press_pass_quick.py activation"
        ;;
    3)
        echo "Testing XP reset..."
        run_test "XP Reset Test" "python3 test_press_pass_quick.py xp-reset"
        ;;
    4)
        echo "Testing warnings..."
        run_test "Warning Test" "python3 test_press_pass_quick.py warnings"
        ;;
    5)
        echo "Testing demo account..."
        run_test "Demo Account Test" "python3 test_press_pass_quick.py demo"
        ;;
    6)
        echo "Testing conversion..."
        run_test "Conversion Test" "python3 test_press_pass_quick.py conversion"
        ;;
    7)
        echo "Starting interactive mode..."
        python3 test_press_pass_quick.py interactive
        ;;
    8)
        echo "Generating test report..."
        if [ -f "test_press_pass_report.json" ]; then
            echo "Test report found at: test_press_pass_report.json"
            echo ""
            echo "Summary:"
            python3 -c "
import json
with open('test_press_pass_report.json', 'r') as f:
    report = json.load(f)
    print(f\"Total Tests: {report['test_run']['total_tests']}\")
    print(f\"Passed: {report['test_run']['passed']}\")
    print(f\"Failed: {report['test_run']['failed']}\")
    print(f\"Success Rate: {(report['test_run']['passed']/report['test_run']['total_tests']*100):.1f}%\")
"
        else
            echo "No test report found. Run tests first."
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Test execution completed."
echo ""

# Check if log file was created
if [ -f "test_press_pass_comprehensive.log" ]; then
    echo "Log file: test_press_pass_comprehensive.log"
    echo "Last 10 lines of log:"
    echo "----------------------------------------"
    tail -10 test_press_pass_comprehensive.log
fi