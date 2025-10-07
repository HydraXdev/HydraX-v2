# Event Bus Schema v1 - FROZEN

**Date Frozen**: 2025-09-16 00:11 UTC
**Status**: PRODUCTION - DO NOT MODIFY
**Breaking Changes**: Require version bump to v2

## execution.outcome.v1 - LOCKED SCHEMA

### Required Fields

- `trade_id` (string) - Unique identifier for trade
- `result` (string) - Must be "WIN" or "LOSS"
- `symbol` (string) - Trading pair (e.g., "EURUSD")
- `pnl_pips` (number) - Profit/loss in pips
- `schema_version` (integer) - Must be 1

### Optional Fields

- `signal_id` (string) - Source signal identifier
- `fire_id` (string) - Fire command identifier
- `direction` (string) - "BUY" or "SELL"
- `entry_price` (number) - Entry price
- `exit_price` (number) - Exit price
- `duration_minutes` (number) - Trade duration
- `pattern_type` (string) - Pattern name
- `confidence` (number) - 0-100 confidence score
- `source` (string) - Data source identifier

### Business Rules

- `trade_id` must be unique and non-empty
- WIN results should have positive `pnl_pips`
- LOSS results should have negative `pnl_pips`
- `confidence` must be 0-100 if provided

### Example Valid Event

```json
{
  "trade_id": "fire:ELITE_RAPID_EURUSD_1757981346",
  "result": "WIN",
  "symbol": "EURUSD",
  "pnl_pips": 15.5,
  "schema_version": 1,
  "signal_id": "ELITE_RAPID_EURUSD_1757981346",
  "direction": "BUY",
  "confidence": 85.0,
  "source": "zmq-confirmation"
}
```

## Contract Tests

Located in: `/root/HydraX-v2/event_bus_schema_guard.py`

Run validation: `python3 event_bus_schema_guard.py`

## Version History

- **v1.0** (2025-09-16): Initial production schema - FROZEN
- **v2.0** (TBD): Future breaking changes only

## Modification Policy

- **NO** field additions without version bump
- **NO** field removals without version bump
- **NO** constraint changes without version bump
- **YES** documentation updates allowed
