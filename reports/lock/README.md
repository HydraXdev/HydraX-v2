# BITTEN v2 Lock Check Reports

This directory contains reports and documentation for the codebase lock system.

## Quick Links

- **[LOCK_SYSTEM_SUMMARY.md](./LOCK_SYSTEM_SUMMARY.md)** - Complete implementation summary with statistics
- **[example_failures.md](./example_failures.md)** - Example failure messages for each rule type

## Generated Reports

These JSON files are automatically generated each time lock checks run:

### lock_scan_results.json
Complete validation results with timestamp and status for all checks.

**Fields**:
- `status`: "PASS" or "FAIL"
- `total_violations`: Number of violations found
- `violations`: Array of violation descriptions
- `checks`: Status of each individual check

### allowed_services.json
Verification of service directories against allowlist.

**Fields**:
- `expected_count`: 5 (required number of services)
- `actual_count`: Number of services found
- `services`: Array of discovered service names
- `allowlist`: Array of authorized service names

### banned_imports.json
Archive v1 import detection results.

**Fields**:
- `archive_v1_imports.count`: Number of violations
- `archive_v1_imports.status`: "PASS" or "FAIL"
- `archive_v1_imports.violations`: Array of import locations

## Usage

### Run Lock Checks

```bash
cd /root/HydraX-v2
./.ci/lock_checks.sh
```

### View Reports

```bash
# View all reports
cat reports/lock/*.json | jq

# View main results
cat reports/lock/lock_scan_results.json | jq

# Check if passing
cat reports/lock/lock_scan_results.json | jq -r '.status'
```

### Interpret Results

**PASS (Exit 0)**:
```
✓✓✓ ALL CHECKS PASSED ✓✓✓
```

**FAIL (Exit 1)**:
```
✗✗✗ 3 CHECK(S) FAILED ✗✗✗
```

## Lock Check Rules

1. **Archive v1 Imports** - No imports from archive_v1/
2. **Banned Filenames** - No versioned or legacy file patterns
3. **JSONL Trackers** - Business trackers only in /tests/
4. **Service Count** - Exactly 5 authorized services
5. **Banned Keywords** - No XSTREAM, buffer_replay, or file queues

## Statistics (Last Run)

- **Python files scanned**: 900
- **Total files checked**: 15,305
- **Lines of code scanned**: 306,912
- **Service directories**: 5
- **Banned patterns**: 10

## Current Status

✅ **ALL CHECKS PASSING** - Zero violations detected

Last scan: 2025-10-08T22:21:43Z
