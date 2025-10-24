# 🧠 BITTEN ZMQ ARCHITECTURE - CORE SYSTEM PRINCIPLES

**CRITICAL**: This document defines the fundamental architecture of BITTEN. All agents and developers MUST understand and follow these principles.

**Created**: August 1, 2025
**Last Updated**: October 16, 2025
**Priority**: MANDATORY READING
**Status**: PERMANENT ARCHITECTURE DEFINITION
**Tracking System**: Unified Tracker (bitten.db + unified_tracking.jsonl)

---

## 🎯 CORE DESIGN REALITY: BITTEN Is Not a Script — It's a Live Execution Platform

### What Makes BITTEN Different

**Most trading bots are:**

- Single-process applications
- File-based or HTTP-triggered
- EA-only with no external logic
- Simple signal → execution flows

**BITTEN is:**

- A multi-service, event-driven trading OS
- Powered by ZMQ sockets, not APIs or files
- A complete platform including:
  - Signal generation (Elite Guard)
  - Pattern detection (6 integrated detectors)
  - Real-time bridge control (fire_router)
  - Unified tracking system (bitten.db)
  - XP/risk scoring systems
  - MT5 trade execution
  - Live telemetry and feedback loops

---

## 🔁 ZMQ Is the System's Nervous System

**CRITICAL UNDERSTANDING**: ZMQ is not a plugin or optional component — it is the core communication protocol of the entire platform.

### Architecture Facts:

- EA connects **directly** to ZMQ sockets from MT5 using libzmq.dll
- All fire commands flow through ZMQ sockets
- All telemetry streams through ZMQ sockets
- All execution feedback returns via ZMQ sockets
- There is **NO** file fallback long-term
- There is **NO** HTTP signal dispatch
- There is **NO** API middleware layer

---

## ⚙️ Mental Model You MUST Adopt

```
[ EA on VPS ] ←→ [ ZMQ Controller ] ←→ [ Signal Engine + Unified Tracker + Fire Router ]
     ↓                    ↓                           ↓
libzmq.dll          Port 5555/5556              Elite Guard + Tracking
Direct Socket       Command/Telemetry            Real-time Logic → bitten.db
```

### Key Points:

- ZMQ replaces ALL file and HTTP logic
- Every trade is initiated over socket
- Every account update is streamed via socket
- Every confirmation is acknowledged via socket
- The EA maintains persistent socket connections

---

## ❌ Common Mistakes to AVOID

1. **DO NOT** assume ForexVPS needs an API middleware — the EA uses libzmq.dll to connect directly
2. **DO NOT** treat the EA like a webhook or REST client — it's a persistent socket listener
3. **DO NOT** remove any socket daemon or think ZMQ is optional — it's not
4. **DO NOT** implement file-based fallbacks without explicit authorization
5. **DO NOT** route signals through HTTP endpoints
6. **DO NOT** treat ZMQ as a temporary migration step

---

## ✅ Development Principles Going Forward

### 1. Core Infrastructure to ALWAYS Preserve:

- `fire_router.py` - Must use ZMQ as primary execution
- `unified_tracker.py` - Single source of truth for signal tracking
- `bitten.db` - Primary database for all system state
- `zmq_fire_publisher_daemon.py` - Command channel daemon
- `zmq_telemetry_daemon.py` - Telemetry receiver daemon
- `zmq_bitten_controller.py` - Core 3-way controller
- EA v3.005+ (ZMQ-enabled) - Never downgrade to file-based EAs

### 2. All New Features Must:

- Assume ZMQ as the primary transport layer
- Never bypass the socket infrastructure
- Integrate with existing telemetry streams
- Write to bitten.db and unified_tracking.jsonl
- Use unified_tracker for all performance analysis
- Respect the real-time, event-driven nature

### 3. System Priorities:

- Real-time socket routing
- Telemetry parsing and analysis
- Unified signal tracking (bitten.db)
- XP-triggered feedback loops
- Persistent connection management
- Zero-latency execution paths

---

## 🏗️ Current Live Implementation

As of August 1, 2025, the system is LIVE with:

### Active Components:

- **ZMQ Controller**: Running on 134.199.204.67:5555/5556
- **EA v7**: Connected from ForexVPS, sending telemetry
- **Telemetry Stream**: Balance: $3000.00, active_users: 1
- **Firewall**: Ports 5555/5556 open for EA connections

### Verified Working:

```
✅ EA Connection: Status: reconnected
✅ Telemetry Flow: Every 5 seconds
✅ Command Channel: Port 5555 ready
✅ Feedback Channel: Port 5556 streaming
✅ Active Users: 1 (EA connected)
```

---

## 🚨 PERMANENT MANDATE

**BITTEN is a platform, not a product. ZMQ is not a feature — it's the bloodstream.**

Every line of code, every system decision, every architecture choice must respect this fundamental truth. The socket infrastructure IS the system. Without it, BITTEN doesn't exist.

### This Architecture is NON-NEGOTIABLE

Any attempt to bypass, remove, or deprecate the ZMQ infrastructure is a fundamental misunderstanding of what BITTEN is. File-based execution was the past. HTTP APIs are not the future. ZMQ sockets ARE the system.

---

## 📌 For All Future Agents

**MEMORIZE THIS**: This document is your architecture anchor point for BITTEN. All future modules must assume this model unless explicitly overridden by system owner with written justification.

When in doubt:

1. Check if your solution uses ZMQ sockets
2. If not, redesign it to use ZMQ sockets
3. There is no step 3

**Build accordingly.**

---

**Document Authority**: System Architecture Definition
**Last Updated**: August 1, 2025
**Status**: PERMANENT - CORE ARCHITECTURE PRINCIPLE
