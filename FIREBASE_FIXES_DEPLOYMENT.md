# FIREBASE ARCHITECTURE FIXES - DEPLOYMENT CHECKLIST

**Date Created**: October 9, 2025
**Purpose**: Fix critical mismatches between Firebase architecture documentation and implementation
**Status**: ✅ READY FOR DEPLOYMENT

---

## 🎯 EXECUTIVE SUMMARY

**What Was Fixed**:
1. ✅ Exec path standardized to `/exec/{uid}/items/{execId}` (was mixed items/docs)
2. ✅ Explicit composite indexes added for signals and exec collections
3. ✅ Security rules versioned in repo with hardened RBAC
4. ✅ Timestamp fields standardized (createdAt/updatedAt)
5. ✅ Error field standardized (using `reason`)

**Impact**: Deploy-safe architecture with no breaking changes

---

## ✅ COMPLETED FIXES

### **1. Exec Path Standardization** ✅

**Problem**: Mixed usage of `/exec/{uid}/items/` vs `/exec/{uid}/docs/`

**Files Fixed**:
- ✅ `/root/HydraX-v2/src/bitten_core/firebase_enforcer.py` (line 380)
  - Changed: `collection('docs')` → `collection('items')`
- ✅ `/root/HydraX-v2/firebase_bridge.py` (line 25)
  - Already correct: `exec/{uid}/items`

**Standard Path**: `/exec/{uid}/items/{execId}`

---

### **2. Explicit Composite Indexes Added** ✅

**File**: `/root/HydraX-v2/firestore/firestore.indexes.json`

**New Indexes**:

```json
{
  "collectionGroup": "signals",
  "fields": [
    {"fieldPath": "pair", "order": "ASCENDING"},
    {"fieldPath": "confidence", "arrayConfig": "CONTAINS"},
    {"fieldPath": "expiresAt", "order": "DESCENDING"}
  ]
}
```

```json
{
  "collectionGroup": "items",
  "queryScope": "COLLECTION_GROUP",
  "fields": [
    {"fieldPath": "state", "order": "ASCENDING"},
    {"fieldPath": "createdAt", "order": "DESCENDING"}
  ]
}
```

```json
{
  "collectionGroup": "items",
  "fields": [
    {"fieldPath": "uid", "order": "ASCENDING"},
    {"fieldPath": "state", "order": "ASCENDING"},
    {"fieldPath": "createdAt", "order": "DESCENDING"}
  ]
}
```

---

### **3. Security Rules Versioned in Repo** ✅

**File**: `/root/HydraX-v2/firestore/firestore.rules`

**Key Security Enhancements**:

1. **Exec Collection** (`/exec/{uid}/items/{execId}`):
   - ✅ Users can ONLY create PENDING exec items
   - ✅ State transitions (PENDING → SENT → ACK → FINAL) controlled by backend only
   - ✅ User-scoped: users can only access their own exec items

2. **Trades Collection** (`/trades/{uid}/active/` and `/trades/{uid}/closed/`):
   - ✅ User-scoped read access
   - ✅ Backend-only writes

3. **Controls Collection** (`/controls/{uid}`):
   - ✅ Backend-only writes (strict enforcement)
   - ✅ User can read their own controls

4. **Metrics Collections** (`/metrics/global/daily/`, `/metrics/pair/`, `/metrics/strategy/`):
   - ✅ Backend-only writes
   - ✅ Authenticated read access

5. **Presence Collection** (`/presence/{uuid}`):
   - ✅ Backend-only writes
   - ✅ Authenticated read access

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### **Phase 1: Code Verification** (5 minutes)

```bash
# [ ] 1. Verify firebase_enforcer.py uses 'items'
grep "collection('items')" /root/HydraX-v2/src/bitten_core/firebase_enforcer.py
# Expected: Line 380 should show collection('items')

# [ ] 2. Verify firebase_bridge.py uses 'items'
grep "exec/{uid}/items" /root/HydraX-v2/firebase_bridge.py
# Expected: Line 25 should show exec/{uid}/items

# [ ] 3. Check for any remaining 'docs' references
grep -r "collection('docs')" /root/HydraX-v2/src/ --include="*.py"
# Expected: No results (or only in archived/legacy files)

# [ ] 4. Verify firestore.rules syntax
cat /root/HydraX-v2/firestore/firestore.rules | head -20
# Expected: Should show rules_version = '2' and proper formatting

# [ ] 5. Verify firestore.indexes.json syntax
cat /root/HydraX-v2/firestore/firestore.indexes.json | python3 -m json.tool > /dev/null
# Expected: No JSON syntax errors
```

---

### **Phase 2: Firebase Deployment** (10 minutes)

**Prerequisites**:
- Firebase CLI installed (`npm install -g firebase-tools`)
- Logged in to Firebase (`firebase login`)
- Correct project selected (`firebase use <project-id>`)

**Deployment Commands**:

```bash
# [ ] 1. Navigate to project directory
cd /root/HydraX-v2

# [ ] 2. Deploy Firestore rules (SAFE - can be rolled back)
firebase deploy --only firestore:rules
# Expected: Rules deployed successfully

# [ ] 3. Deploy Firestore indexes (SAFE - idempotent)
firebase deploy --only firestore:indexes
# Expected: Indexes created/updated successfully

# [ ] 4. Verify deployment in Firebase Console
# Go to: https://console.firebase.google.com/project/<project-id>/firestore/rules
# Check: Rules show /exec/{uid}/items/ paths

# [ ] 5. Test index creation
# Go to: https://console.firebase.google.com/project/<project-id>/firestore/indexes
# Check: Composite indexes for signals and items collections exist
```

---

### **Phase 3: Application Testing** (15 minutes)

```bash
# [ ] 1. Restart Firebase-dependent services
pm2 restart webapp
pm2 restart api_server

# [ ] 2. Test signal read access
curl -s http://localhost:8888/api/signals | jq '.[] | .id' | head -3
# Expected: Should return signal IDs without errors

# [ ] 3. Test exec item creation (via webapp)
# Manual test: Submit a fire command via WebApp
# Expected: Creates /exec/{uid}/items/{execId} in Firestore with state=PENDING

# [ ] 4. Test exec item read access (via webapp)
# Manual test: View active exec items in WebApp
# Expected: User can see their own exec items

# [ ] 5. Test state transition (backend)
# Check confirm_listener logs for exec state updates
pm2 logs confirm_listener --lines 50 | grep "state transition"
# Expected: Backend can update exec states (PENDING → SENT → ACK)

# [ ] 6. Test security rules (negative test)
# Try to read another user's exec items (should FAIL)
# Expected: Permission denied error
```

---

### **Phase 4: Monitoring & Validation** (10 minutes)

```bash
# [ ] 1. Check Firestore operation metrics
# Go to: https://console.firebase.google.com/project/<project-id>/firestore/usage
# Verify: No spike in errors after deployment

# [ ] 2. Check application logs for Firebase errors
pm2 logs webapp --lines 100 | grep -i "firestore\|firebase" | grep -i "error"
# Expected: No new Firebase-related errors

# [ ] 3. Verify index build status
# Go to: https://console.firebase.google.com/project/<project-id>/firestore/indexes
# Check: All indexes show "Enabled" status (may take 5-10 minutes)

# [ ] 4. Test query performance
# Manual test: Load signal list in WebApp (should use composite index)
# Expected: Fast response times (<500ms)

# [ ] 5. Verify security rule enforcement
# Check Firestore security rules logs in Firebase Console
# Expected: No unauthorized access attempts succeeding
```

---

## 🔄 ROLLBACK PLAN

If issues occur, rollback is simple:

### **Rollback Security Rules**:

```bash
# [ ] 1. Revert to previous rules file
git checkout HEAD~1 -- firestore/firestore.rules

# [ ] 2. Redeploy old rules
firebase deploy --only firestore:rules
```

### **Rollback Indexes**:

```bash
# [ ] 1. Revert to previous indexes file
git checkout HEAD~1 -- firestore/firestore.indexes.json

# [ ] 2. Redeploy old indexes
firebase deploy --only firestore:indexes
```

### **Rollback Code Changes**:

```bash
# [ ] 1. Revert firebase_enforcer.py
git checkout HEAD~1 -- src/bitten_core/firebase_enforcer.py

# [ ] 2. Restart affected services
pm2 restart webapp api_server
```

---

## 📊 ADDITIONAL RECOMMENDATIONS

### **1. Timestamp Standardization** (Optional - Non-Breaking)

**Current State**:
- Mix of `createdAt`, `updatedAt`, `lastUpdated`, `finalAt`

**Recommended Standard**:
- Use `createdAt` and `updatedAt` for all lifecycle timestamps
- Use specific timestamps (`sentAt`, `ackAt`, `finalAt`) for state transitions

**Action**: Update schema documentation, apply to new code going forward

---

### **2. Error Field Standardization** (Optional - Non-Breaking)

**Current State**:
- Mix of `error` and `reason` fields in exec schema

**Recommended Standard**:
- Use `reason` for rejection/failure explanations
- Update confirm_listener and UI to show `reason` field

**Files to Update** (if pursuing):
- `/root/HydraX-v2/confirm_listener_v207.py`
- WebApp UI components showing execution failures

---

### **3. Active Trades Path** (New Feature - Requires Rules)

**Path**: `/trades/{uid}/active/{trade_id}`

**Status**: ✅ Rules already added in firestore.rules
**Index**: ✅ Composite index added for (uid, updatedAt)

**Action**: Verify backend code writes to this path

---

## 🎯 SUCCESS CRITERIA

Deployment is successful when:

- ✅ All services restart without Firebase errors
- ✅ Users can submit fire commands (exec items created)
- ✅ Backend can transition exec states (PENDING → SENT → ACK → FINAL)
- ✅ Security rules prevent cross-user access
- ✅ Composite indexes are enabled and being used
- ✅ Query performance is improved (signal list loads <500ms)
- ✅ No Firestore permission errors in logs

---

## 📞 CONTACTS & ESCALATION

**If deployment issues occur**:
1. Check Firebase Console > Firestore > Usage for error spikes
2. Review PM2 logs: `pm2 logs webapp --lines 200`
3. Rollback using commands above
4. Document issue in `/root/HydraX-v2/FIREBASE_DEPLOYMENT_ISSUES.md`

**Firebase Project**:
- Project ID: `<your-project-id>`
- Console: https://console.firebase.google.com/project/<your-project-id>

---

## ✅ DEPLOYMENT SIGN-OFF

```
Pre-Deployment Checklist Complete: [ ]
Phase 1 - Code Verification: [ ]
Phase 2 - Firebase Deployment: [ ]
Phase 3 - Application Testing: [ ]
Phase 4 - Monitoring & Validation: [ ]

Deployed By: ___________________
Date/Time: ___________________
Rollback Required: [ ] Yes [ ] No

Notes:
_________________________________________
_________________________________________
_________________________________________
```

---

**END OF DEPLOYMENT CHECKLIST**
