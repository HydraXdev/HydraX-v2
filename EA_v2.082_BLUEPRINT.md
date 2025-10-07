# BITTEN Universal EA v2.082 — Blueprint & Schemas

## 0) Mission Profile (one glance)

**Role**: MT5 → ZMQ execution & telemetry bridge
**Contract**: NO-MODIFY / NO-PENDING (market only + close)
**User UX rule**: Users can watch + close, not modify
**Identity**: Router identity is source of truth (DEALER id = UUID)
**Magic**: 7176191872 (BITTEN positions only)

## 1) Sockets & Ports

- **5555 (DEALER, in)**: commands ⇒ fire, close_ticket, close_all, ping, wake
- **5556 (PUSH, out)**: ticks (TICK), OHLC (OHLC), hello/handshake, heartbeat (legacy)
- **5558 (PUSH, out)**: confirmations (confirmation), signal_snapshot, position_closed, (hybrid_event if used)
- **5560 (PUSH, out)**: account & position metrics (HEARTBEAT_METRICS)

## 2) Inputs (runtime knobs)

```mql5
InpVerboseLogging=false
InpBlockOppositeHedge=true  // per-symbol hedge guard
InpMaxSpreadPoints=0.0      // 0=off; else reject if spread > limit
InpDeviationPoints=5        // slippage (points)
InpTelemetryBeatSec=1       // fast live mirror cadence
InpRouterBeatSec=5
InpStreamTicks=true
InpStreamOHLC=true
InpSnapshotBars=100
InpSnapshotTF="M1"
```

## 3) Command → Event Contracts

| Inbound (5555) | What EA does | Outbound events |
|----------------|--------------|-----------------|
| fire (market BUY/SELL with SL/TP) | Validates: DLL/trading allowed, symbol quotes, direction, spread, hedge, SL/TP geometry, volume | Pre-emit: signal_snapshot (5558) → Then: confirmation (success/fail) (5558) |
| close_ticket | Closes specific BITTEN position | close_confirmation (5558) |
| close_all | Closes all BITTEN positions | close_confirmation (summary) (5558) |
| ping | Liveness | pong (5558) |
| wake | Route warmup | AWAKE (to 5555) + pong (5558) |

### Background streams

- **Ticks**: deterministic 1/sec per symbol (TICK on 5556)
- **OHLC**: M1 each minute; M5/M15 on cadence (OHLC on 5556)
- **Metrics**: 1s HEARTBEAT_METRICS with open positions array (5560)
- **Closes**: position_closed (5558) when deals exit (manual/TP/SL/SO)
- **Hello / Handshake / Heartbeats**: router hello + legacy beat on init and timer

## 4) Validation & Safety Gates

- **DLL/trading allowed** hard check at init
- **Spread guard**: reject if (ask-bid)/point > InpMaxSpreadPoints (when >0)
- **Hedge block**: if enabled, reject opposite side on same symbol
- **SL/TP geometry**:
  - BUY: SL < price < TP, min distance ≥ broker TRADE_STOPS_LEVEL
  - SELL: TP < price < SL, same min distance check
- **Volume normalization** to SYMBOL_VOLUME_STEP/MIN/MAX
- **UUID load** from bitten_deployment.cfg (DEV override: login 843859 ⇒ COMMANDER_DEV_001)

## 6) What it does vs doesn't

### Does
- ✅ Market BUY/SELL with SL/TP
- ✅ Live mirror via 1s metrics + per-symbol tick stream
- ✅ Snapshot pre-fire for web rendering
- ✅ Close by ticket / close all
- ✅ Emit trade closures with reason
- ✅ Enforce hedge/spread/SLTP/volume safety

### Doesn't
- ❌ Pending orders
- ❌ Modify SL/TP of existing positions (zero-modify)
- ❌ Manage non-BITTEN positions (filters by magic)
- ❌ Accept user-side edits (UI should not expose them)

## 7) UI / Webapp Integration (minimal but complete)

### Subscribe:
- **5560 HEARTBEAT_METRICS** → account KPIs + open positions table (the mirror)
- **5558 confirmation, position_closed, signal_snapshot** → toasts/rows

### Render:
- **Positions** keyed by ticket (or fire_id fallback) with live PnL from metrics
- **Charts** from signal_snapshot.bars + overlays (entry/sl/tp)

### Actions:
- **Button: Close Ticket** → emits close_ticket
- **Button: Close All** → emits close_all
- **No edit controls** (SL/TP/partial/etc.)

### Liveness:
- **ping/pong** round-trip for UI heartbeat when idle
- Treat a missed **HEARTBEAT_METRICS > 3× cadence** as "stale"

## 8) Deploy & Ops Checklist (10-second)

- [x] bitten_deployment.cfg present with UUID
- [x] DLLs allowed; account trading allowed
- [x] Ports reachable: 5555, 5556, 5558, 5560
- [x] InpStreamTicks/InpStreamOHLC = true for charts
- [x] InpTelemetryBeatSec = 1 for live mirror feel
- [x] InpBlockOppositeHedge = true, set InpMaxSpreadPoints as needed
- [x] Webapp listening: 5558 + 5560 (and showing "Close" only)

---

## LAW Delta (2.079 → 2.082)

### L (Added)

1. **Live mirror ready cadence**: InpTelemetryBeatSec=1 + deterministic 1/s per symbol tick push (MonitorAllSymbols) → makes UI fluid without relying on price polling.

2. **HEARTBEAT_METRICS enhanced**: includes positions[] array with ticket, fire_id, symbol, direction, open_price, current_price, volume, pnl (use as single source of truth for open state).

3. **position_closed passive event** emitted on exits with standardized reason mapping (MANUAL|TP_HIT|SL_HIT|STOP_OUT).

4. **Pre-validation signal_snapshot** includes concise metrics (dir, lot, sl, tp) alongside bars & overlays.

### A (Altered)

1. **Zero-modify stance** clarified/enforced: open-time SL/TP required & validated; no post-open edits.

2. **Hedge guard path** tightened: explicit reject for opposite side on same symbol when enabled.

3. **Ticket resolution post-fill**: history scan + fallback to active PositionSelect for robust ticket reporting in confirmation.

### W (Withdrawn / Not present)

1. **No position_open / position_update discrete events** (still optional). Current design intentionally relies on HEARTBEAT_METRICS for open/updates.

---

## 9) Known Edges / Gotchas

- **Stops level** varies by symbol/broker; SL/TP rejects will surface as REJECTED(...): SL too close/TP too close.
- **UUID discipline**: payload UUID is logged, but router identity is truth—ensure DEALER identity matches bitten_deployment.cfg.
- **Symbol availability**: EA calls SymbolSelect(symbol,true) on fire; unavailable symbols will hard-fail with a clear confirmation error.
- **Magic segregation**: Only positions with magic 7176191872 are reported/closed.