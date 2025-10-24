# Lock Check Example Failures

This document shows example failure messages for each lock check rule type.

## CHECK 1: Archive v1 Import Detection

**Example Violation:**
```
✗ FAIL: Found 3 imports from archive_v1/
/root/HydraX-v2/src/signal_engine/pattern_detector.py:from archive_v1.legacy_patterns import OldPattern
/root/HydraX-v2/src/api_server/routes.py:from archive_v1.models import DeprecatedModel
/root/HydraX-v2/tools/migration_helper.py:import archive_v1.config
```

**Fix Required:**
- Remove imports from archive_v1/ directory
- Use new v2 implementations
- Update code to use current architecture

---

## CHECK 2: Banned Filename Patterns

**Example Violation:**
```
✗ FAIL: Found 5 banned filename patterns
  - /root/HydraX-v2/src/signal_engine/pattern_v1_backup.py
  - /root/HydraX-v2/src/api_server/routes_old.py
  - /root/HydraX-v2/src/fire_service/fire_v2_experimental.py
  - /root/HydraX-v2/tools/debug_helper_legacy.py
  - /root/HydraX-v2/comprehensive_tracking.jsonl
```

**Fix Required:**
- Delete versioned files (*_v1*.py, *_v2*.py)
- Remove old/backup files (*_old*.py, *_backup*.py)
- Eliminate legacy/experimental files
- Move tracking JSONL files to /tests/parity/

**Allowed Exceptions:**
- /tests/ directory (test files can have any naming)
- /migration/ directory (migration scripts exempt)
- /node_modules/ directory (dependency files exempt)
- /bitten-ui/ directory (UI dependencies exempt)

---

## CHECK 3: JSONL Business Trackers Outside /tests

**Example Violation:**
```
✗ FAIL: Found 4 JSONL trackers outside /tests/
/root/HydraX-v2/comprehensive_tracking.jsonl
/root/HydraX-v2/signal_tracking.jsonl
/root/HydraX-v2/truth_log.jsonl
/root/HydraX-v2/src/analytics/optimized_tracking.jsonl
```

**Fix Required:**
- Move all *_tracking.jsonl files to /tests/parity/
- Move truth_log.jsonl to /tests/parity/
- JSONL business trackers must only exist in test directories

**Rationale:**
- Business logic tracking creates data duplication
- Multiple tracking files lead to inconsistency
- Test fixtures should be in test directories

---

## CHECK 4: Service Directory Count

**Example Violation (Too Many):**
```
✗ FAIL: Expected 5 services, found 7
Services found:
  - analytics_worker
  - api_server
  - fire_service
  - legacy_service
  - signal_engine
  - zmq_gateway
  - deprecated_worker
```

**Example Violation (Unauthorized Service):**
```
✗ FAIL: Unauthorized service directory: xstream_processor
```

**Fix Required:**
- Remove unauthorized service directories
- Keep exactly 5 services:
  - zmq_gateway
  - signal_engine
  - fire_service
  - api_server
  - analytics_worker

**Rationale:**
- Prevents service sprawl
- Maintains clean architecture
- Enforces approved service boundaries

---

## CHECK 5: Banned Keywords in Code

**Example Violation (XSTREAM):**
```
✗ FAIL: Found 'XSTREAM' in 8 locations
/root/HydraX-v2/src/signal_engine/xstream_buffer.py:15:from xstream import XStreamBuffer
/root/HydraX-v2/src/fire_service/xstream_relay.py:42:    xstream.connect()
/root/HydraX-v2/tools/xstream_diagnostic.py:10:# XSTREAM debugging utility
  ... and 5 more
```

**Example Violation (buffer_replay):**
```
✗ FAIL: Found 'buffer_replay' in 3 locations
/root/HydraX-v2/src/signal_engine/signal_buffer.py:88:    buffer_replay.start()
/root/HydraX-v2/src/zmq_gateway/replay.py:25:from buffer_replay import ReplayEngine
```

**Example Violation (File-backed queues):**
```
✗ FAIL: Found file-backed queue 'fire.txt' in 5 locations
/root/HydraX-v2/src/fire_service/fire_executor.py:45:    with open('fire.txt', 'w') as f:
/root/HydraX-v2/tools/manual_fire.py:12:    fire_data = open('fire.txt').read()
```

**Fix Required:**
- Remove all XSTREAM references (deprecated architecture)
- Remove buffer_replay code (causes stale signal issues)
- Replace file-backed queues (fire.txt, trade_result.txt) with ZMQ/IPC
- Use proper message queue architecture

**Rationale:**
- XSTREAM was experimental and never deployed
- buffer_replay caused duplicate alerts and stale signals
- File-based communication is unreliable and slow
- ZMQ/IPC is the approved communication pattern

---

## Validation Statistics

**When all checks pass, you'll see:**

```
✓✓✓ ALL CHECKS PASSED ✓✓✓

Codebase is clean:
  ✓ No archive_v1/ imports
  ✓ No banned filename patterns
  ✓ No JSONL trackers outside /tests
  ✓ Exactly 5 authorized services
  ✓ No banned keywords

Reports generated:
  - /root/HydraX-v2/reports/lock/lock_scan_results.json
  - /root/HydraX-v2/reports/lock/allowed_services.json
  - /root/HydraX-v2/reports/lock/banned_imports.json
```

**Exit Codes:**
- `0` = All checks passed (safe to commit)
- `1` = Violations found (fix required before commit)

---

## Integration with Git Hooks

**Pre-commit hook example:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running BITTEN v2 lock checks..."
/root/HydraX-v2/.ci/lock_checks.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Lock checks failed - commit blocked"
    echo "Fix violations before committing"
    exit 1
fi

echo "✅ Lock checks passed - proceeding with commit"
exit 0
```

**CI/CD Pipeline example:**

```yaml
# .github/workflows/lock-check.yml
name: Codebase Lock Check
on: [push, pull_request]

jobs:
  lock-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run lock checks
        run: ./.ci/lock_checks.sh
```
