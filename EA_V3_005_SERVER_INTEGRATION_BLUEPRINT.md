# EA v3.005 Server Integration Blueprint

## Critical Changes from Previous Versions

### 1. Handshake Now Includes Position Reconciliation

**Message Type:** `handshake` (sent once on EA startup to port 5556)

**New Fields:**

```json
{
  "type": "handshake",
  "reconnect": true/false,  // NEW: true if EA has open positions
  "open_positions": [       // NEW: array of current positions
    {
      "ticket": 12345,
      "symbol": "XAUUSD",
      "direction": "BUY",
      "fire_id": "sig_xyz_123",
      "open_price": "2865.50",
      "volume": "0.01",
      "pnl": 12.50
    }
  ],
  // ... existing fields (uuid, balance, equity, etc)
}
```

**Server Action Required:**

- If `reconnect=false`: Reset daily trade counter for this UUID
- If `reconnect=true`: Validate open_positions against server state, DON'T reset counter
- Update user_positions[uuid] with the positions array (EA state is source of truth)

**Why This Matters:**
Prevents users from exceeding 6 trades/day limit after EA crash/restart.

---

### 2. DEALER Keepalive Messages

**Message Type:** `dealer_heartbeat` (sent every 5 seconds to port 5555)

```json
{
  "type": "dealer_heartbeat",
  "uuid": "USER_123",
  "node_id": "NODE_843859_123",
  "timestamp": 1759451234
}
```

**Server Action Required:**

- Command router should ignore these (no response needed)
- Use them to update "last seen" timestamp for connection monitoring

**Why This Matters:**
Prevents router from aging out EA connections during idle periods.

---

### 3. Direction Canonicalization

**Change:** All outbound events now use standardized "BUY"/"SELL" (never "long", "sell", "b", etc)

**Affected Messages:**

- `position_opened`

**Server Action:**
Your hedge protection logic can now rely on `direction` field being exactly "BUY" or "SELL".

---

### 4. SafeNum Protection

**Change:** Balance, equity, margin values are now sanitized to prevent NaN/Inf

**Impact:**
You should never receive `NaN`, `Infinity`, or `-Infinity` in numeric fields. If you do, it means broker glitched and EA caught it.

---

### 5. Heartbeats Now on Port 5556

**Change:** Heartbeats moved from port 5560 to port 5556 (same as ticks/handshake)

**Reason:** Port 5560 was configured as PUB socket, EA needs PULL socket for PUSH messages.

**Server Action:**
Your existing receiver on port 5556 now gets three message types:

- `type: "handshake"`
- `type: "tick"`
- `type: "heartbeat"`

---

## Message Flow Summary

```
Port 5556 (EA → Server PULL):
├─ handshake (on startup, includes position reconciliation)
├─ tick (continuous if InpStreamTicks=true)
├─ heartbeat (every 1 second, has balance/equity)
└─ disconnect (on EA shutdown)

Port 5558 (EA → Server PULL):
├─ position_opened (immediate on trade execution)
├─ position_closed (immediate on trade close)
├─ confirmation (ack for fire/close commands)
└─ pong (response to ping)

Port 5555 (Server → EA ROUTER/DEALER):
├─ fire (open position command)
├─ close (close specific position)
├─ close_all (close all positions)
├─ ping (health check)
└─ dealer_heartbeat (EA sends these, you ignore)

Port 5560 (EA → Server PULL):
└─ position_update (every 1 second per open position)
```

---

## Position State Reconciliation Logic

```python
def on_handshake(msg):
    uuid = msg["uuid"]
    is_reconnect = msg.get("reconnect", False)
    ea_positions = msg.get("open_positions", [])

    if not is_reconnect:
        # Fresh start - initialize user
        daily_trades[uuid] = 0
        user_positions[uuid] = []
        user_balance[uuid] = msg["balance"]
    else:
        # Reconnect - reconcile state
        server_positions = user_positions.get(uuid, [])
        ea_tickets = {p["ticket"] for p in ea_positions}
        server_tickets = {p["ticket"] for p in server_positions}

        # Log mismatches for monitoring
        if ea_tickets != server_tickets:
            missing_on_server = ea_tickets - server_tickets
            missing_on_ea = server_tickets - ea_tickets
            log.warning(f"Position mismatch {uuid}: EA={ea_tickets} Server={server_tickets}")

        # EA is source of truth
        user_positions[uuid] = ea_positions

        # DON'T reset daily_trades counter
```

---

## Tunable Parameters (Exposed as EA Inputs)

These can be changed without recompiling:

- `InpRouterBeatSec`: DEALER keepalive interval (default 5s)
- `InpSndHWM`: Send high water mark (default 10000)
- `InpRcvHWM`: Receive high water mark (default 1000)
- `InpLingerMs`: Socket linger on close (default 0)

If you need to tune backpressure behavior, ask users to adjust these inputs.

---

## Version Identifier

All handshakes include `"version": "3.005"` - use this for monitoring/debugging.
