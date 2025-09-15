# ⚠️ DEPRECATED TRACKING SYSTEMS - DO NOT USE ⚠️

**Date Deprecated**: September 15, 2025  
**Replaced By**: EVENT BUS SYSTEM (see CLAUDE.md)  
**Reason**: Replaced with institutional-grade Event Bus tracking system

## 🚨 CRITICAL WARNING 🚨

**DO NOT USE ANY FILES IN THIS DIRECTORY**

All tracking systems in this directory have been replaced by the Event Bus system.
The Event Bus provides:
- Single source of truth
- ACID compliance
- Event sourcing
- Correlation tracking
- 99% space savings
- No race conditions

## Files Archived Here:

### Old Tracking Files (DO NOT USE):
- `comprehensive_tracking.jsonl` - Replaced by Event Bus
- `dynamic_tracking.jsonl` - Replaced by Event Bus
- `ml_training_data.jsonl` - Replaced by Event Bus
- All tracker Python scripts - Replaced by Event Bus components

### Why These Were Deprecated:
1. **Multiple JSONL files** - Caused inconsistent data and race conditions
2. **No correlation** - Couldn't track complete trade lifecycle
3. **Space inefficient** - Would create 50,000+ files for 5,000 users
4. **Data loss** - Files could be corrupted or overwritten
5. **No ACID compliance** - No transaction guarantees

## How to Use the New System:

### Query Event Bus Database:
```bash
sqlite3 /root/HydraX-v2/bitten_events.db "SELECT * FROM events ORDER BY timestamp DESC LIMIT 10;"
```

### Publish Events:
```python
from event_bus.event_bridge import signal_generated
signal_generated({'signal_id': 'xxx', 'pattern': 'xxx', ...})
```

### Check Event Bus Status:
```bash
pm2 list | grep -E "event_bus|data_collector"
```

## ⚠️ DO NOT:
- Restore these files to production
- Use these tracking methods
- Create new tracking systems
- Reference these in any new code

## ✅ ALWAYS:
- Use Event Bus for all tracking
- Query bitten_events.db for data
- Publish events through Event Bus client
- Check CLAUDE.md for current tracking documentation

---

**These files are kept for historical reference only. The Event Bus is the ONLY approved tracking system.**