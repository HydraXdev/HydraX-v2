#!/bin/bash
#
# STRICT_EXECUTION_PROTOCOL — SMOKE TEST RUNNER
# Wrapper script for smoke_test.py
#

set -e

cd "$(dirname "$0")"

echo "🚀 BITTEN SMOKE TEST RUNNER"
echo "Testing fire pipeline: IPC → router → EA → confirmation"
echo

# Run the Python smoke test
python3 smoke_test.py

# Exit with the same code as the Python script
exit $?