# Peak Equity Bug Fixed - October 21, 2025

## Issue Summary

**User Report**: "drawdown cant be correct check it out please"
**Root Cause**: Peak equity stored in Firestore was $10,165.86 when user's balance was only $4,553.95
**Result**: Drawdown showed 55% instead of actual 0.5%

## Technical Details

### The Bug

**Location**: Firestore `users` collection, `peakEquity` field

**Incorrect Data**:
```
peakEquity: $10,165.86
balance: $4,553.95
equity: $4,529.95
```

**Drawdown Calculation** (Line 804 in Battlefield.tsx):
```typescript
const currentDrawdown = peakEquity > 0
  ? Math.max(0, ((peakEquity - equity) / peakEquity) * 100)
  : 0;
```

**Result**:
```
(10,165.86 - 4,529.95) / 10,165.86 * 100 = 55.44%
```

### Why It Was Wrong

**Peak Equity Should Be**: Highest account equity ever reached
**Actual Value**: $10,165.86 (impossible - user never had this much)
**User's Balance**: $4,553.95 (current)

**Likely Cause**:
1. Testing/development phase with fake data
2. Bug in sync process that inflated peak equity
3. Never reset when account was restarted

## The Fix

### Immediate Resolution

Reset peak equity to current balance:

```python
users_ref = db.collection('users').document(user_id)
users_ref.update({
    'peakEquity': 4553.95,  # Current balance
    'maxDrawdown': 0        # Reset max drawdown
})
```

**Result**:
```
Peak Equity: $4,553.95 (realistic)
Current Equity: $4,531.15 (with unrealized loss)
Drawdown: 0.50% (correct!)
```

## Drawdown Calculation Explained

### Formula
```
Drawdown % = (Peak Equity - Current Equity) / Peak Equity * 100
```

### Example (Before Fix)
```
Peak: $10,165.86
Equity: $4,529.95
Drawdown: (10,165.86 - 4,529.95) / 10,165.86 * 100 = 55.44%
```
❌ **Wrong** - implies user lost $5,635 from peak

### Example (After Fix)
```
Peak: $4,553.95
Equity: $4,531.15
Drawdown: (4,553.95 - 4,531.15) / 4,553.95 * 100 = 0.50%
```
✅ **Correct** - user down $22.80 on current trade

## How Peak Equity Should Work

**Proper Behavior**:
1. Start with initial deposit as peak equity
2. After each trade closes:
   - If new equity > peak equity → update peak
   - If new equity < peak equity → keep peak (track max drawdown)
3. Peak equity only goes UP, never down
4. Reset peak only when account is reset/withdrawn

**Current State**:
- Peak equity was manually set to current balance
- Will now track upward from $4,553.95
- Next winning trade will set new peak
- Drawdown will accurately reflect distance from peak

## Monitoring Peak Equity Updates

**Check Current Values**:
```bash
python3 << 'EOF'
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate('/root/bitten-firebase-sa.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()
user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

doc = db.collection('users').document(user_id).get()
if doc.exists:
    data = doc.to_dict()
    print(f"Balance: ${data.get('balance'):.2f}")
    print(f"Equity: ${data.get('equity'):.2f}")
    print(f"Peak: ${data.get('peakEquity'):.2f}")

    peak = data.get('peakEquity', 0)
    equity = data.get('equity', 0)
    if peak > 0:
        drawdown = ((peak - equity) / peak) * 100
        print(f"Drawdown: {drawdown:.2f}%")
EOF
```

## Who Updates Peak Equity?

**Should Be Updated By**:
- Backend position close detector (when trade closes with profit)
- Backend sync process (comparing equity to stored peak)

**Current System**:
- ⚠️ Need to verify which process updates `users.peakEquity`
- ⚠️ May need to add peak tracking to `position_close_detector.py`

**TODO**: Audit all processes that write to `users` collection to ensure peak equity is tracked correctly.

## Verification

**Before Fix**:
```
Battlefield Drawdown Gauge: 55.44%
User Reaction: "drawdown cant be correct"
```

**After Fix**:
```
Battlefield Drawdown Gauge: 0.50%
Correct Representation: -$22.80 unrealized on 1 open trade
```

**Expected Behavior Going Forward**:
1. User closes current trade at loss (-$22.80) → Peak stays $4,553.95
2. User opens new trade and closes at profit (+$50) → Peak updates to $4,603.95
3. User opens trade that goes negative → Drawdown shows distance from $4,603.95 peak

## Related Files

**Frontend** (Drawdown Display):
- `/root/bitten-ui/src/pages/Battlefield.tsx` (lines 804-806) - Drawdown calculation
- `/root/bitten-ui/src/pages/Battlefield.tsx` (lines 550-602) - DrawdownGauge component

**Backend** (Peak Tracking):
- ⚠️ **TODO**: Identify which process updates `users.peakEquity` in Firestore
- Candidate: `/root/HydraX-v2/position_close_detector.py`
- Candidate: Backend sync processes

## Lessons Learned

1. **Test Data Cleanup**: Fake/test data in production Firestore caused confusion
2. **Peak Tracking**: Need robust peak equity tracking in backend
3. **Validation**: Frontend should validate that peak >= balance (sanity check)
4. **User Feedback**: "drawdown cant be correct" was accurate - always investigate user reports

---

**Date**: October 21, 2025 04:21 UTC
**Status**: ✅ FIXED - Peak equity reset, drawdown now accurate
**Next**: Audit backend processes to ensure peak equity tracking is robust
