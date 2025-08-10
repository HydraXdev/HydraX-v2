# BITTEN ZMQ ENGINEERING BLUEPRINT & MANIFESTO

## 🧠 OVERVIEW

BITTEN is not a strategy bot. It is a **military-grade distributed trading control system** that uses MetaTrader 5 terminals as **execution drones**, not thinking machines. Each MT5 terminal is turned into a **portable tactical comms node**, directed entirely by central command logic (BITTEN Core), via ZMQ sockets.

The EA does not decide, calculate, or evaluate. It **listens, obeys, and confirms**.

## 🔌 SYSTEM DESIGN OVERVIEW

Each MT5 EA instance deployed under BITTEN architecture operates as a ZMQ-connected execution unit. This system is designed for horizontal deployment across hundreds or thousands of VPSs — all communicating asynchronously and externally managed.

## 🔁 Data Flow Architecture

```
MT5 TERMINAL (PORTABLE MODE)
├── ZMQ PUSH → Tickstream/telemetry → BITTEN Core
├── ZMQ PULL ← Fire commands (entry/sl/tp/lot)
└── ZMQ PUSH → Execution confirmations → Core logging/feedback
```

## 🔑 Core ZMQ Ports (default)

* **5556** → Tick data PUSH
* **5555** ← Fire command PULL  
* **5558** → Trade result PUSH

## ⚙️ EA FUNCTIONAL ROLES

### ✅ OnInit()
* Creates ZMQ context and sockets (`ZMQ_CONNECT` only — never bind)
* Sends initial handshake packet:

```json
{
  "type": "handshake",
  "account": 843859,
  "broker": "Coinexx",
  "server": "Coinexx-Demo",
  "symbol": "BTCUSD",
  "balance": 10000.00,
  "equity": 9942.38,
  "timestamp": "2025-08-02T10:30:00Z"
}
```

* Displays chart message:
```
🎯 BITTEN ZMQ NODE: READY
```

### ✅ OnTick()
* Streams current tick via `zmq_send()` as a JSON message
* Runs `zmq_recv(..., ZMQ_DONTWAIT)` to non-blockingly check for incoming fire mission
* If fire command is received:
   * Parses packet
   * Executes trade exactly as received (no local logic)
   * Sends confirmation packet:

```json
{
  "type": "executed",
  "symbol": "BTCUSD",
  "ticket": 12345678,
  "lot": 0.12,
  "price": 67302.00,
  "result": "success"
}
```

### ✅ OnDeinit()
* Closes all sockets
* Destroys ZMQ context
* Sends optional disconnect message
* Clears chart comment

## 🔒 DOCTRINE: WHAT YOU MUST NEVER DO

BITTEN's ZMQ EA must not:
* ❌ Calculate lot size
* ❌ Bind sockets
* ❌ Use `while(true)` or `Sleep()`
* ❌ Use `WebRequest()` or `FileWrite()`
* ❌ Execute trades on its own
* ❌ Modify SL/TP/lot values
* ❌ Depend on profile paths or terminal state

This EA must:
* ✅ Always use portable-mode MT5
* ✅ Stay stateless between restarts
* ✅ Function on unknown IPs with dynamic endpoints
* ✅ Fail silently if ZMQ not connected, but never crash chart

## ☣️ FINAL WARNING

**Do not modify this EA unless you understand the entire BITTEN system.**

This EA is not a bot. It is not designed to be smart. It is designed to be **obedient**, **modular**, and **invisible**.

All logic lives in BITTEN Core. This EA is simply the execution tip of the spear — deployed blindly into potentially unstable environments with zero UI, zero context, and zero margin for error.

If you attempt to alter its behavior without understanding:
* Core timing
* Signal handling
* Risk control logic
* XP protocol dependencies

...you will break the battlefield comms layer.

And when that breaks — the mission fails.

## 🪖 Maintain discipline. Ask before altering. Only change with command approval.

**BITTEN SYSTEMS**  
*"We are not trying to win the game. We are trying to survive it long enough to learn how. Then we bite back."*

---

## 📊 MESSAGE PROTOCOL SPECIFICATIONS

### Tick Data Message
```json
{
  "type": "TICK",
  "node_id": "NODE_843859_1234567",
  "symbol": "BTCUSD",
  "bid": 67301.50,
  "ask": 67302.00,
  "spread": 5.0,
  "volume": 1234,
  "timestamp": "2025-08-02T10:30:00Z"
}
```

### OHLC Data Message
```json
{
  "type": "OHLC",
  "node_id": "NODE_843859_1234567",
  "symbol": "BTCUSD",
  "time": 1722592800,
  "open": 67300.00,
  "high": 67350.00,
  "low": 67280.00,
  "close": 67320.00,
  "timestamp": "2025-08-02T10:30:00Z"
}
```

### Fire Command (Incoming)
```json
{
  "type": "fire",
  "symbol": "BTCUSD",
  "entry": 67302.00,
  "sl": 67200.00,
  "tp": 67500.00,
  "lot": 0.12
}
```

### Execution Confirmation
```json
{
  "type": "executed",
  "symbol": "BTCUSD",
  "ticket": 12345678,
  "lot": 0.12,
  "price": 67302.00,
  "result": "success"
}
```

### Heartbeat Message
```json
{
  "type": "HEARTBEAT",
  "node_id": "NODE_843859_1234567",
  "ticks_sent": 4523,
  "timestamp": "2025-08-02T10:30:00Z"
}
```

### Disconnect Message
```json
{
  "type": "DISCONNECT",
  "node_id": "NODE_843859_1234567",
  "timestamp": "2025-08-02T10:30:00Z"
}
```

## 🛠️ DEPLOYMENT CHECKLIST

### MT5 Terminal Setup
- [ ] MT5 in portable mode (`/portable` flag)
- [ ] DLL imports enabled in settings
- [ ] Auto-trading enabled
- [ ] libzmq.dll in `MQL5\Libraries\` folder
- [ ] Correct architecture (x64 DLL for 64-bit MT5)

### Network Requirements
- [ ] Outbound TCP connections allowed
- [ ] Ports 5555, 5556, 5558 accessible
- [ ] Stable connection to command center IP
- [ ] No proxy interference with ZMQ traffic

### EA Configuration
- [ ] Magic number: 7176191872
- [ ] Bridge IP configured correctly
- [ ] Symbol attached to correct chart
- [ ] No conflicting EAs on same terminal

### Security Considerations
- [ ] VPS firewall configured
- [ ] No unnecessary ports exposed
- [ ] Terminal running with minimal privileges
- [ ] Regular security updates applied

## 📈 PERFORMANCE METRICS

The system is designed to handle:
- **Tick Rate**: Up to 1000 ticks/second per node
- **Latency**: Sub-10ms command execution
- **Nodes**: Unlimited horizontal scaling
- **Reliability**: Automatic reconnection on disconnect
- **Uptime**: 24/7 operation with no memory leaks

## 🔧 TROUBLESHOOTING

### EA Won't Attach to Chart
- Check DLL permissions enabled
- Verify libzmq.dll architecture matches MT5 (x64/x86)
- Check Journal/Experts tabs for errors
- Ensure correct import declarations (ulong for 64-bit)

### No Connection to Core
- Verify IP and ports are correct
- Check firewall/antivirus blocking
- Test with telnet to ports
- Verify ZMQ context creation succeeds

### Commands Not Executing
- Check symbol name matches exactly
- Verify account has trading permissions
- Check sufficient margin/balance
- Review trade server connection status

### Memory/Performance Issues
- Monitor VPS resources
- Check for socket leaks
- Verify proper cleanup in OnDeinit()
- Review tick filtering logic

---

## 📞 SUPPORT

For issues with BITTEN system integration:
- Check system logs first
- Document error messages with screenshots
- Include MT5 build number and OS version
- Provide network topology if relevant

Remember: This is not a trading strategy. This is infrastructure. Treat it as such.

**BITTEN SYSTEMS** - Tactical Trading Infrastructure