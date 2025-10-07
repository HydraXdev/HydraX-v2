# MetaSocket CUTOVER Runbook

**Status**: Ready for CUTOVER
**Date**: 2025-09-25
**Version**: 1.0

## Overview

This document provides the complete procedure for switching the BITTEN trading system from EA/ZMQ source to MetaSocket source while maintaining all existing v1 JSON contracts.

## Pre-CUTOVER Checklist

### 1. Environment Verification

```bash
# Run verification script
./scripts/cutover_verify.sh

# Should show all green checkmarks except SOURCE warning (expected)
```

### 2. MetaSocket Service Status

Ensure MetaSocket is running and accessible:
- **CMD TCP**: localhost:8777
- **STREAM TCP**: localhost:8778
- **Demo Account**: Ready for testing

### 3. Backup Current State

```bash
# Backup current config
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Backup command router
cp command_router.py command_router.py.backup

# Record current PM2 status
pm2 list > pm2_status_before_cutover.txt
```

## CUTOVER Procedure

### Phase 1: Switch to MetaSocket Source

```bash
# Set SOURCE environment variable
export SOURCE=metasocket

# Update .env file
sed -i 's/^SOURCE=.*/SOURCE=metasocket/' .env

# Verify settings
grep SOURCE .env
echo "SOURCE=$SOURCE"
```

### Phase 2: Restart Services

```bash
# Restart command router to pick up new SOURCE
pm2 restart command_router

# Restart webapp to enable MetaSocket health monitoring
pm2 restart webapp

# Wait for services to stabilize
sleep 5

# Verify services
pm2 list | grep -E "command_router|webapp"
```

### Phase 3: Verification

```bash
# Check health endpoint includes MetaSocket metrics
curl -s http://localhost:8888/healthz | jq .

# Should now show:
# {
#   "status": "OK",
#   "metasocket": {
#     "status": "ok",
#     "last_event_age_ms": <number>,
#     "event_lag_ms_p95": <number>,
#     "order_latency_ms_p95": <number>
#   }
# }
```

### Phase 4: Smoke Tests

```bash
# Run golden test suite
./scripts/run_metasocket_tests.sh

# All 4 tests should pass:
# ✅ Test 01: Order Latency (<500ms p95) - PASSED
# ✅ Test 02: Manual Close - PASSED
# ✅ Test 03: SL/TP Handling - PASSED
# ✅ Test 04: Reconnect/Recovery - PASSED
```

### Phase 5: Live Monitoring

Monitor logs for first 30 minutes:

```bash
# Monitor command router for MetaSocket routing
pm2 logs command_router --lines 20

# Look for log messages like:
# "[CUTOVER] ROUTED fire FIRE_ID_123 → MetaSocket"

# Monitor webapp for MetaSocket health
pm2 logs webapp --lines 20

# Check for any errors or warnings
```

## ROLLBACK Procedure

If issues are detected, immediately rollback:

```bash
# Execute rollback script
./scripts/rollback_to_ea.sh

# Script will:
# 1. Set SOURCE=ea
# 2. Restart services
# 3. Verify rollback success
```

Manual rollback if script fails:

```bash
# Set environment
export SOURCE=ea
sed -i 's/^SOURCE=.*/SOURCE=ea/' .env

# Restart services
pm2 restart command_router
pm2 restart webapp

# Verify
curl -s http://localhost:8888/healthz | jq .
```

## Monitoring & Alerts

### Key Metrics to Watch

1. **Order Latency**: Should remain <500ms p95
2. **Error Rate**: Should be <1% for MetaSocket orders
3. **Circuit Breaker**: Should not trigger repeatedly
4. **Event Lag**: Should be <100ms average

### Alert Conditions

- **Critical**: Order latency >1000ms p95
- **Critical**: Error rate >5%
- **Warning**: Circuit breaker >3 triggers/hour
- **Warning**: Event lag >500ms

### Health Check URLs

- **Webapp Health**: http://localhost:8888/healthz
- **MetaSocket Metrics**: Included in webapp health when SOURCE=metasocket

## Architecture Changes

### Before (EA Source)
```
Signal → Command Router → EA (ZMQ) → MT5 → Confirmation
```

### After (MetaSocket Source)
```
Signal → Command Router → MetaSocket (TCP) → MT5 → Confirmation
```

### Unchanged Components

- **Signal Generation**: Elite Guard patterns unchanged
- **Event Bus**: Redis/ZMQ flows unchanged
- **Web Interface**: Same HUD and API endpoints
- **JSON Contracts**: All v1 schemas frozen and preserved

## Files Modified

### Core Integration
- `adapters/metasocket/adapter.py` - MetaSocket client adapter
- `command_router.py` - SOURCE-based routing logic
- `webapp_server_optimized.py` - Health endpoint enhancement
- `.env` - SOURCE configuration

### Testing & Operations
- `tests/metasocket/01_order_latency_test.py`
- `tests/metasocket/02_manual_close_test.py`
- `tests/metasocket/03_sl_tp_test.py`
- `tests/metasocket/04_reconnect_test.py`
- `scripts/run_metasocket_tests.sh`
- `scripts/cutover_verify.sh`
- `scripts/rollback_to_ea.sh`

## Frozen v1 JSON Schemas

These schemas MUST NOT change during cutover:

### Tick Event
```json
{
  "symbol": "EURUSD",
  "bid": 1.08901,
  "ask": 1.08903,
  "timestamp": 1695648000
}
```

### Position Event
```json
{
  "ticket": 123456789,
  "symbol": "EURUSD",
  "direction": "BUY",
  "volume": 0.10,
  "open_price": 1.08900,
  "current_price": 1.08950,
  "profit": 5.00,
  "status": "OPEN"
}
```

### Account Summary
```json
{
  "balance": 10000.00,
  "equity": 10050.00,
  "margin": 109.00,
  "free_margin": 9941.00,
  "margin_level": 9220.18
}
```

## Support Information

### Success Criteria
- ✅ All fire commands route to MetaSocket when SOURCE=metasocket
- ✅ Order latency <500ms p95
- ✅ Error rate <1%
- ✅ Health endpoint includes MetaSocket metrics
- ✅ Rollback capability tested and working

### Escalation
If CUTOVER issues cannot be resolved within 15 minutes:
1. Execute immediate rollback: `./scripts/rollback_to_ea.sh`
2. Verify EA source working normally
3. Schedule maintenance window for investigation

### Post-CUTOVER Tasks
- [ ] Monitor for 24 hours
- [ ] Update documentation with actual performance metrics
- [ ] Plan gradual rollout to production accounts
- [ ] Archive old EA-specific code after 30 days stability

---

**CUTOVER READY**: All components implemented and tested
**ROLLBACK READY**: Clean rollback procedure verified
**CONTRACTS FROZEN**: All v1 JSON schemas preserved