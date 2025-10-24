# SLOT ALLOCATION ROOT CAUSE ANALYSIS
**Date**: October 16, 2025 14:40 UTC
**Issue**: Auto-fire accumulated 15+ positions when max is 10

## THE PROBLEM

**Symptoms:**
- EA reports: 15-16 actual open positions
- fire_modes.db shows: 9/10 slots used
- Database has: 373 SENT fire records
- Auto-fire continues firing despite being over limit

## ROOT CAUSE IDENTIFIED

The database trigger `prevent_auto_slot_overflow` is **BLOCKING** the enhanced_slot_manager from syncing EA truth:

```sql
CREATE TRIGGER prevent_auto_slot_overflow
BEFORE UPDATE ON user_fire_modes  
WHEN NEW.auto_slots_in_use > NEW.max_auto_slots
BEGIN
    SELECT RAISE(ABORT, 'Auto slots cannot exceed maximum');
END
```

**Why this breaks the system:**

1. User somehow accumulates 15 positions (possibly from before trigger was added)
2. enhanced_slot_manager tries to sync: `UPDATE ... SET auto_slots_in_use = 15 WHERE max = 10`
3. Trigger ABORTS the update with: `IntegrityError: Auto slots cannot exceed maximum`
4. fire_modes.db stays at old value (9/10)
5. Auto-fire checks fire_modes.db, sees 9/10, thinks 1 slot available
6. Auto-fire sends more trades
7. Problem gets worse

## THE VICIOUS CYCLE

```
EA: 15 positions → Try to sync → Trigger blocks → fire_modes: 9/10
                                                           ↓
                                                   Auto-fire sees slot available
                                                           ↓
                                                   Fires another trade
                                                           ↓
EA: 16 positions → Try to sync → Trigger blocks → fire_modes: 9/10
```

## WHY THE TRIGGER WAS ADDED

From SLOT_OVERFLOW_FIX.md (September 16, 2025):
- Added to prevent `occupy_slot()` from incrementing beyond max
- Was meant to be a safety guard
- **Unintended consequence**: Blocks truth synchronization

## THE REAL ISSUE

The trigger protects against **incremental overflow** (occupy_slot going from 9→11) but **prevents truth sync** when system is already in overflow state.

## SOLUTION APPROACH

### Option 1: Remove Trigger, Fix occupy_slot()
- Remove `prevent_auto_slot_overflow` trigger
- Keep the `MIN()` bounds check in occupy_slot() (already there)
- Allow truth sync even when over limit
- Fix auto-fire to check EA truth instead of fire_modes

### Option 2: Modify Trigger to Allow Truth Sync
- Change trigger to only block increments via occupy_slot()
- Allow sync operations from enhanced_slot_manager
- Requires tracking operation source (complex)

### Option 3: Make Auto-Fire Check EA Truth Directly
- Keep trigger as-is
- Change auto-fire slot check to query `ea_instances.open_positions`
- Bypass fire_modes.db entirely for slot availability
- **RECOMMENDED** - Uses source of truth directly

## IMMEDIATE FIXES NEEDED

1. **Drop the trigger** (it's doing more harm than good)
2. **Modify webapp auto-fire** to check `ea_instances.open_positions` directly
3. **Clean up 373 stale SENT records** to prevent database bloat
4. **Let positions close naturally** (already happening - went from 16→15)
5. **Monitor that new auto-fires respect EA truth**

## FILES TO MODIFY

1. `/root/HydraX-v2/src/bitten_core/fire_mode_database.py` - Drop trigger
2. `/root/HydraX-v2/webapp_server_optimized.py:790-801` - Check EA truth
3. `/root/HydraX-v2/enhanced_slot_manager.py` - Add error handling for sync failures

## EXPECTED OUTCOME

- Auto-fire will stop when EA positions >= max
- Slot sync will work correctly
- Positions will close naturally over time
- System will return to normal state
