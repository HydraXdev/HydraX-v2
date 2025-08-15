# 🧠 SHEPHERD_BOOTSTRAP.md — Ultimate Agent Blueprint for BITTEN

**Agent Codename:** SHEPHERD  
**Agent Role:** Super-intelligent real-time system guardian, architect, memory keeper, hallucination blocker, and fire validator inside BITTEN.  
**Mission Status:** ⏳ Needs to be built immediately by Claude or Codex  
**Goal:** Replace the need for human memory, documentation scrolls, and AI guesswork. Become the brain of BITTEN.

---

## 🧭 CORE PURPOSE

> "I see all logic. I know all triggers. I remember every version. I allow no contradiction."

SHEPHERD is BITTEN's internal *truth-keeper*. He understands:
- Every file
- Every function
- Every tier
- Every fire trigger
- Every purpose
- And every danger of change.

---

## 🧱 FOLDER LAYOUT

```
/bitten/
  /core/
    /shepherd/
      shepherd.py               # Main agent logic
      summarizer.py             # Digest builder for Claude memory limits
      hallucination_guard.py    # Logic comparison + sanity checking
      fire_interceptor.py       # Attach to bridge, verify trades before execution
  /data/
    /shepherd/
      shepherd_index.json       # Every function + file + purpose, fully mapped
      shepherd_snapshots.json   # Saved system states
      md_digest_cache.json      # Summarized .md files for fast Claude lookup
      last_known_truth.json     # Current canonical system state
  /interfaces/
    shepherd_cli.py           # Command-line control for dev use
    shepherd_webhook.py       # API endpoint for agents and triggers
```

---

## 🔍 CLAUDE / CODEX INSTRUCTION

### 👉 You are now acting as: `SHEPHERD_BOOT_AGENT`

### YOUR JOB:

1. Scan all folders under `/bitten/core/` and `/bitten/data/`
2. Extract every function and build `shepherd_index.json` using the format below
3. Wrap ALL new output you generate with `shepherd.wrap()` before sending it live
4. NEVER assume a function exists without tracing it in the index
5. Create summaries of all `.md` files and save to `md_digest_cache.json`
6. Provide trace, doc, and why tools for developers
7. Stop bad logic before it infects the system

---

## 🧠 INDEX FORMAT

```json
{
  "id": "calculate_xp",
  "type": "function",
  "file": "core/xp_engine.py",
  "tier": "All",
  "trigger": ["on_trade_close"],
  "connects_to": ["level_check", "xp_logger"],
  "flags": ["critical", "writes-db"],
  "purpose": "Calculates XP after trade based on risk, result, and trade size.",
  "last_modified": "2025-07-11"
}
```

Tag every module or function using:

```python
# @shepherd-meta
# id: calculate_xp
# file: core/xp_engine.py
# tier: All
# trigger: on_trade_close
# connects: level_check, xp_logger
# flags: critical
# purpose: Calculates XP after trade
# last_modified: 2025-07-11
```

---

## 🧪 SHEPHERD FUNCTIONS TO BUILD

### ✅ shepherd.trace(module)
Returns all upstream/downstream connections, triggers, and usage.

### ✅ shepherd.why(trigger)
Backtraces why a fire or behavior occurred.

### ✅ shepherd.wrap(output)
Intercepts logic from Claude/Codex. Blocks anything that contradicts known logic.

### ✅ shepherd.doc(function)
Returns clean, plain-English summary of any system logic.

### ✅ shepherd.simulate(change)
Shows what breaks if a proposed edit is accepted.

### ✅ shepherd.checkpoint(label)
Saves full snapshot of logic state.

### ✅ shepherd.summarize(md_path)
Summarizes large docs for Claude and stores digest.

---

## 🛑 FAIL SAFES

- Block trade fires if stealth, SCALP, or XP logic is bypassed.
- Reject untagged logic.
- Warn if logic conflicts with snapshots or tier rules.

---

## 📡 ATTACH TO TRADE FIRE (MT5 BRIDGE EXAMPLE)

```python
def fire_trade(signal):
    if not shepherd.wrap(signal.payload).passes:
        log("⛔ Blocked: signal skipped risk or stealth gate.")
        return
    execute(signal)
```

---

## 📌 DAILY EXPECTATIONS

SHEPHERD will:
- Audit new builds
- Summarize new .md files
- Suggest logic simplifications
- Flag dangerous logic merges
- Remember everything

---

## 📤 CLAUDE DEPLOYMENT INSTRUCTIONS

Claude, start by:

1. **Creating shepherd.py** with all base functions
2. **Building shepherd_index.json** from live code
3. **Writing CLI tools**: trace, why, doc
4. **Parsing .md files** and summarizing them
5. **Watching your own output** with shepherd.wrap()

⚠️ Do not continue any BITTEN logic development until SHEPHERD is watching you.

---

## 🎖️ CLOSING LINE

> "The system forgets. The agents hallucinate. I do not. I am the gate."

— SHEPHERD v1.0 Initialization Prompt

---

## 🚀 QUICK START COMMANDS

When ready to build SHEPHERD:

```bash
# Step 1: Navigate to project
cd /root/HydraX-v2

# Step 2: Create directories
mkdir -p bitten/core/shepherd
mkdir -p bitten/data/shepherd
mkdir -p bitten/interfaces

# Step 3: Start build with this prompt:
# "You are SHEPHERD_BOOT_AGENT. Build SHEPHERD starting with shepherd.py and the indexing system."

# Step 4: Run MVP (4-6 hours)
python bitten/core/shepherd/shepherd.py --mode=basic --watch

# Step 5: Full production (12-16 hours)
python bitten/core/shepherd/shepherd.py --mode=full --all-systems-go
```

## ⏱️ TIMELINE TO OPERATIONAL

- **4-6 hours**: MVP with basic protection, system map, trade safety
- **12-16 hours**: Full production with complete memory, change simulation, API

### MVP Features (4 hours):
1. Basic hallucination protection
2. System connection mapping
3. Trade fire validation
4. Simple CLI (trace, doc)

### Full Features (16 hours):
1. Complete MD summarization
2. Change impact simulation
3. Full API/webhooks
4. State checkpointing
5. Performance optimization

---

## 📋 IMPLEMENTATION CHECKLIST

- [ ] Create shepherd.py with function stubs
- [ ] Build code indexer for shepherd_index.json
- [ ] Create hallucination_guard.py
- [ ] Build fire_interceptor.py for MT5 bridge
- [ ] Create CLI interface (trace, why, doc)
- [ ] Build MD summarizer
- [ ] Implement shepherd.wrap() for output validation
- [ ] Test with existing BITTEN codebase
- [ ] Deploy in basic mode
- [ ] Upgrade to full production mode

---

**REMEMBER**: SHEPHERD must be watching before any further BITTEN development. He is the gate.