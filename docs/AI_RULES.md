# AI_RULES.md – HydraX Firebase Wiring Rules for AI Agents

**⚠️ READ THIS BEFORE MODIFYING ANY CODE ⚠️**

This document defines the architectural boundaries and rules for AI agents (Claude Code, Grok, etc.) working on the HydraX system. **All AI agents MUST follow these rules without exception.**

---

## 🎯 Core Principle: Two-Layer Separation

HydraX operates with **strict separation** between two layers:

### 1️⃣ Trading Core (Server-Side) – **HANDS OFF**
- **Location**: Server at 134.199.204.67
- **Technology**: Python, ZMQ, SQLite/PostgreSQL
- **Components**:
  - ZMQ bridge and command router
  - MT5 EA communication
  - Signal generation engines (Elite Guard)
  - Trade execution and confirmation
  - Position tracking and risk management
  - All `*.py` files in root and `/services/`

**❌ YOU CANNOT MODIFY THESE FILES ❌**

### 2️⃣ App Layer (Firebase) – **YOU MAY WORK HERE**
- **Location**: Firebase project (Firestore, Functions, Hosting)
- **Technology**: Next.js, TypeScript, Firebase SDK
- **Components**:
  - PWA frontend (`/app`, `/bitten-ui`)
  - Cloud Functions (`/functions`)
  - Firestore rules (`/infra`)
  - Documentation (`/docs`)

**✅ YOU CAN MODIFY THESE FILES ✅**

---

## 📁 File Modification Matrix

### ✅ ALLOWED (App Layer)
```
app/**                    # PWA frontend
functions/**              # Firebase Cloud Functions
infra/**                  # Firestore rules, indexes
docs/**                   # Documentation
bitten-ui/**              # Next.js UI components
firebase.json             # Firebase configuration
firestore.rules           # Security rules
firestore.indexes.json    # Database indexes
```

### ❌ FORBIDDEN (Trading Core)
```
services/**               # Trading services
bridge/**                 # ZMQ bridge
legacy/**                 # Legacy code
*.py files in root        # Python backend
command_router.py         # Command routing
webapp_server_optimized.py # Flask webapp
elite_guard*.py           # Signal generation
zmq_*.py                  # ZMQ infrastructure
confirm_listener*.py      # Trade confirmations
enqueue_fire.py           # Fire command creation
Any database scripts      # Server DB management
```

---

## 🔄 Correct Architecture Patterns

### ✅ CORRECT: Firestore-First Pattern

**User initiates action:**
```typescript
// 1. User clicks button in UI
async function executeTrade(symbol: string, direction: 'BUY' | 'SELL') {
  const execId = generateId();

  // 2. Write request to Firestore
  await setDoc(doc(db, `exec/${uid}/${execId}`), {
    status: 'PENDING',
    symbol,
    direction,
    requestedAt: serverTimestamp()
  });

  // 3. UI automatically updates via listener (see below)
}

// 4. Listen for server response
onSnapshot(doc(db, `exec/${uid}/${execId}`), (snap) => {
  const data = snap.data();
  if (data.status === 'FILLED') {
    showSuccessNotification(`Trade filled at ${data.fillPrice}`);
  }
});
```

**Server processes (you don't write this, but understand it):**
```python
# Bridge watches Firestore
# Validates request
# Sends ZMQ command to MT5
# Updates Firestore with result:
#   PENDING → SENT → ACKED → FILLED
```

### ❌ WRONG: Direct HTTP Pattern

```typescript
// ❌ NEVER DO THIS - Bypasses architecture
async function executeTrade(symbol: string) {
  const response = await fetch('http://134.199.204.67:8888/api/fire', {
    method: 'POST',
    body: JSON.stringify({ symbol, direction: 'BUY' })
  });
  // This violates the two-layer separation!
}
```

### ❌ WRONG: Trading Logic in Cloud Functions

```typescript
// ❌ NEVER DO THIS - Trading logic belongs on server
export const executeTrade = onCall(async (data) => {
  const zmq = require('zeromq'); // FORBIDDEN
  const socket = zmq.socket('dealer');
  socket.connect('tcp://134.199.204.67:5555');
  // This is trading core logic, not app layer!
});
```

### ✅ CORRECT: Cloud Function for Sync Only

```typescript
// ✅ Cloud Functions should only sync data, not execute trades
export const syncExecToPostgres = onDocumentWritten(
  'exec/{uid}/{execId}',
  async (event) => {
    const data = event.data.after.data();

    // Sync to server database (mirror only)
    await fetch(`${SERVER_URL}/api/firestore-sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        collection: 'exec',
        docId: event.params.execId,
        data: data
      })
    });
  }
);
```

---

## 🔒 Firestore Security Rules Template

**Copy this pattern for all collections:**

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Helper: Check if request is from service account
    function isService() {
      return request.auth.token.admin == true;
    }

    // User execution requests
    match /exec/{uid}/{execId} {
      allow create: if request.auth.uid == uid;      // User can create
      allow read:   if request.auth.uid == uid || isService();
      allow update: if isService();                  // Only server updates
      allow delete: if isService();                  // Only server deletes
    }

    // User controls (read-only for users)
    match /controls/{uid} {
      allow read:   if request.auth.uid == uid || isService();
      allow write:  if isService();                  // Server sets limits
    }

    // User preferences (user can modify)
    match /users/{uid} {
      allow read:   if request.auth.uid == uid || isService();
      allow update: if request.auth.uid == uid;      // User can update prefs
      allow create: if isService();                  // Server creates account
    }

    // Signals (read-only for users)
    match /signals/{signalId} {
      allow read:   if request.auth != null;         // Any authenticated user
      allow write:  if isService();                  // Only server publishes
    }
  }
}
```

---

## 📊 Data Flow Reference

### Signal Generation → User Notification
```
MT5 EA → ZMQ (5556) → Bridge → Firestore /signals → Cloud Function → FCM → User Device
                                    ↓
                              UI onSnapshot listener → Update display
```

### User Action → Trade Execution
```
User clicks FIRE → Firestore /exec (PENDING) → Bridge watches → Validates
                                                      ↓
                                                ZMQ (5555) → EA → MT5
                                                      ↓
                                                Confirmation → Bridge
                                                      ↓
                                                Firestore /exec (FILLED)
                                                      ↓
                                                UI onSnapshot → Show success
```

### Performance Tracking
```
Bridge → Firestore /signals (outcome) → Cloud Function → Sync to PostgreSQL
              ↓
        Analytics dashboard queries PostgreSQL
```

---

## 🚫 Common Mistakes to Avoid

### 1. Bypassing Firestore
```typescript
// ❌ WRONG
const res = await fetch('/api/execute-trade'); // Direct server call

// ✅ CORRECT
await setDoc(doc(db, `exec/${uid}/${id}`), { status: 'PENDING' });
```

### 2. Trading Logic in UI
```typescript
// ❌ WRONG
function calculatePositionSize(balance: number, risk: number) {
  return balance * risk / 100; // This belongs on server
}

// ✅ CORRECT - Let server calculate
await setDoc(doc(db, `exec/${uid}/${id}`), {
  requestedRiskPercent: 2 // Server will calculate lot size
});
```

### 3. Modifying Authoritative Fields
```typescript
// ❌ WRONG
await updateDoc(doc(db, `controls/${uid}`), {
  max_slots: 10 // User escalating privileges
});

// ✅ CORRECT - Only update UI preferences
await updateDoc(doc(db, `users/${uid}`), {
  theme: 'dark', // Non-authoritative preference
  notifications: true
});
```

### 4. Creating Backend Services in Frontend
```typescript
// ❌ WRONG - app/server.ts
const express = require('express');
const app = express();
app.listen(3000); // NO backend servers in app layer!

// ✅ CORRECT - Use Firebase Hosting
// Build Next.js → Deploy to Firebase Hosting
// npm run build && firebase deploy --only hosting
```

---

## ✅ AI Agent Task Template

**Copy/paste this for EVERY task involving app layer:**

```
CONTEXT:
HydraX is a two-layer system:
- Trading core (Python/ZMQ on server) - DO NOT MODIFY
- App layer (Firebase/Next.js) - YOU MAY MODIFY

ALLOWED FILES:
app/**, functions/**, infra/**, docs/**, bitten-ui/**

FORBIDDEN FILES:
services/**, bridge/**, *.py files, command_router.py, etc.

TASK:
[Describe the specific task]

REQUIREMENTS:
1. All user actions write to Firestore first
2. UI updates via onSnapshot() listeners
3. Cloud Functions sync data to server DB (if needed)
4. No trading logic in client or Functions
5. Respect Firestore Security Rules
6. No direct HTTP calls to server from client

ACCEPTANCE:
- Code compiles and passes type checking
- Firebase deploy succeeds
- Real-time updates work
- Security rules enforced
- No violation of two-layer separation
```

---

## 🎯 Pre-Submission Checklist

Before considering ANY task complete:

- [ ] **No ZMQ imports** in `app/` or `functions/`
- [ ] **No trading logic** in client code
- [ ] **All user actions** write to Firestore first
- [ ] **UI updates** use `onSnapshot()` listeners
- [ ] **Cloud Functions** only sync data (no execution)
- [ ] **Security rules** prevent unauthorized access
- [ ] **TypeScript** compiles without errors
- [ ] **Tests pass** (if applicable)
- [ ] **Firebase deploy** succeeds without errors
- [ ] **Server files** remain untouched

---

## 🆘 When Confused or Uncertain

**If you are unsure about:**
- Whether a file can be modified → **STOP and ASK**
- Where logic should live → **STOP and ASK**
- How data should flow → **STOP and ASK**
- Security rule implementation → **STOP and ASK**

**Never assume. Always clarify.**

---

## 📚 Additional References

- **SESSION_START.md** - Full AI agent execution rules
- **ARCHITECTURE.md** - Complete system architecture
- **CLAUDE.md** - BITTEN system documentation
- **Firebase Documentation** - [firebase.google.com/docs](https://firebase.google.com/docs)

---

## 🔐 Security Principles

1. **Principle of Least Privilege**: Users can only access their own data
2. **Server Authority**: Server is always source of truth
3. **Client Validation**: Client validates for UX, server enforces for security
4. **No Secrets in Client**: All API keys, tokens in Cloud Functions only
5. **Audit Trail**: All actions logged to Firestore with timestamps

---

## 🎓 Learning Resources

**If you're new to this architecture:**

1. Read Firebase Security Rules docs
2. Understand Firestore `onSnapshot()` pattern
3. Learn Cloud Functions triggers (`onDocumentWritten`, etc.)
4. Study the request/response pattern (user writes PENDING, server writes FILLED)
5. Review existing code in `functions/` for examples

**DO NOT:**
- Start coding without understanding the pattern
- Copy patterns from other projects that don't use this architecture
- Implement "quick fixes" that bypass the rules

---

## ⚖️ Final Authority

**This document is the authoritative source for app layer development rules.**

If any other documentation conflicts with these rules:
1. Follow this document
2. Report the conflict
3. Request clarification

**These rules exist to:**
- Prevent breaking the trading engine
- Maintain security boundaries
- Ensure scalability
- Enable real-time updates
- Keep logic where it belongs

**Violating these rules will result in:**
- Broken production systems
- Security vulnerabilities
- Rejected code changes
- Wasted development time

---

**Last Updated**: October 13, 2025
**Document Version**: 1.0
**Status**: AUTHORITATIVE - MUST FOLLOW
