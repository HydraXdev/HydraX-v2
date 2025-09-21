# BITTEN UI Safe Cleanup Plan

## Critical Issue: Routes Returning 500 Errors

**Root Cause**: CSS utility `bg-primary` and `border-border` not recognized by Tailwind CSS

## Phase 1: Critical Fixes (Apply Immediately)

### 1. Fix CSS Utilities

**Problem**: These utilities are causing build failures:
- `bg-primary` 
- `border-border`

**Solution**: Replace with working utilities from our CSS variables:
- `bg-primary` → `bg-[rgb(var(--primary))]`
- `border-border` → `border-[rgb(var(--border-default))]`

### 2. Remove Unused Imports

**Safe removals** (no functional impact):

**app/live/page.tsx**:
```typescript
// Remove: Activity, CheckCircle, XCircle
import { Wifi, WifiOff, Server, RefreshCw } from 'lucide-react'
```

**app/mission-brief/page.tsx**:
```typescript
// Remove: Target, AlertCircle, ChevronRight
// Keep: User, Clock, TrendingUp, DollarSign, etc.
```

**app/settings/page.tsx**:
```typescript
// Remove: Globe, Volume2, Toggle, RefreshCw
// Keep: Settings, Bell, Smartphone, etc.
```

**app/test/page.tsx**:
```typescript
// Remove: Send
// Keep: Zap, Activity, CheckCircle, etc.
```

## Phase 2: Type Safety (No Behavior Change)

### Replace `any` with Proper Types

**Event handlers**:
```typescript
// Before: (data: any) => void
// After: (data: SignalData) => void
```

**API responses**:
```typescript
interface BackendSignal {
  signal_id: string
  symbol: string
  direction: 'BUY' | 'SELL'
  confidence: number
  // etc.
}
```

## Phase 3: Development Dependencies

### Safe to Remove
- `ts-prune` (added during audit)

### Keep All These (Required)
- `@tailwindcss/postcss`
- `@types/node`
- `@types/react-dom`
- `eslint-config-next`
- `tailwindcss`
- `typescript`

## Implementation Order

1. **Fix CSS utilities** (critical - routes broken)
2. **Remove unused imports** (safe cleanup)
3. **Improve TypeScript types** (code quality)
4. **Remove ts-prune** (housekeeping)

## Testing After Each Phase

```bash
# After each change:
npm run build
curl http://localhost:3000/ # Should return 200
curl http://localhost:3000/live # Should return 200
```

## Guardrails

### DO NOT CHANGE
- App Router structure (`app/*/page.tsx`)
- Component exports or props
- Environment variables
- WebSocket/API endpoints
- Event bus architecture

### SAFE TO CHANGE
- Unused imports
- TypeScript types (improve, don't remove)
- CSS utility classes (fix broken ones)
- Development dependencies

---

**This plan maintains 100% API compatibility while fixing critical issues.**