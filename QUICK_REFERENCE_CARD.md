# 🎯 BITTEN QUICK REFERENCE CARD

## 🚨 STOP - CHECK FIRST

```bash
# What's actually running?
ps aux | grep -E "(apex|bitten|webapp)" | grep -v grep

# What already exists?
grep -r "your_feature" --include="*.py" .

# How does it connect?
python3 bitten/interfaces/shepherd_cli.py trace module_name
```

## 📍 PRODUCTION FILES ONLY

```
Signal Generation:    apex_v5_lean.py
Main Bot:            bitten_production_bot.py
WebApp:              webapp_server.py
Signal Relay:        apex_telegram_connector.py
Command Center:      commander_throne.py
```

## 🚫 DO NOT USE

- ❌ apex_v5_live_real.py (old version)
- ❌ Any file in /archive/
- ❌ Files starting with test*, TEST*, or \_test
- ❌ Multiple bot implementations (_*bot*_.py)
- ❌ SEND\_\*.py files (30+ duplicates!)

## 🔧 ACTIVE PORTS

- 8080: Main WebApp
- 8899: Commander Throne
- 5555: MT5 Bridge (AWS)

## 📂 WHERE TO FIND THINGS

```
Core Logic:          /src/bitten_core/
Configuration:       /config/
Documentation:       /docs/
Old/Duplicate Code:  /archive/
```

## 🆘 EMERGENCY COMMANDS

```bash
# Restart webapp
systemctl restart bitten-webapp

# Check signals
tail -f trading_signals.json

# View logs
journalctl -u bitten-webapp -f
```

## 📋 BEFORE ANY TASK

1. ✅ Read CLAUDE.md Quick Reference section
2. ✅ Check DUPLICATE_FUNCTIONALITY_REPORT.md
3. ✅ Use SHEPHERD to understand connections
4. ✅ Verify feature doesn't already exist

## ⚠️ COMMON MISTAKES

- Creating new bots (we have 17+!)
- New signal generators (we have 5+!)
- New webapp servers (we have 15+!)
- Not checking existing code first

**RULE**: If it seems like a common feature, IT ALREADY EXISTS somewhere!
