# BITTEN UI Integration Usage Guide

## Quick Start

### 1. Initialize Event Integration in Your App

Add to your root layout or app component:

```tsx
// app/layout.tsx
"use client"

import { useEventIntegration } from '@/lib/useEventIntegration'

export default function RootLayout({ children }) {
  // Initialize event bus and WebSocket connections
  useEventIntegration({
    enableMissionStream: true,
    enablePriceStream: true,
    symbols: ['EURUSD', 'GBPJPY', 'XAUUSD'],
    userId: '7176191872'
  })

  return (
    <html>
      <body>{children}</body>
    </html>
  )
}
```

### 2. Listen for Mission Events

In your War Room or any component:

```tsx
import { useEffect } from 'react'
import { eventBus, EVENTS } from '@/lib/eventBus'
import { useUI } from '@/lib/store'

export default function WarRoom() {
  const { missions } = useUI()

  useEffect(() => {
    // Listen for new missions
    const unsubscribe = eventBus.on(EVENTS.MISSION_CREATED, (mission) => {
      console.log('New mission:', mission)
      // Store will be updated automatically by integration hook
    })

    return () => unsubscribe()
  }, [])

  return (
    <div>
      {missions.map(mission => (
        <MissionCard key={mission.id} mission={mission} />
      ))}
    </div>
  )
}
```

### 3. Subscribe to Price Updates

For live price display in Mission Brief:

```tsx
import { usePriceSubscription } from '@/lib/useEventIntegration'
import { useState } from 'react'

export default function LivePriceDisplay({ symbol }) {
  const [price, setPrice] = useState({ bid: 0, ask: 0 })

  usePriceSubscription(symbol, (priceData) => {
    setPrice(priceData)
    // Calculate P&L based on entry price
  })

  return (
    <div>
      <div>Bid: {price.bid}</div>
      <div>Ask: {price.ask}</div>
      <div>Mid: {(price.bid + price.ask) / 2}</div>
    </div>
  )
}
```

### 4. Execute Missions

Using the mission lifecycle hook:

```tsx
import { useMissionLifecycle } from '@/lib/useEventIntegration'
import { executeMission } from '@/lib/api'

export default function MissionActions({ mission }) {
  const { acceptMission, executeMission, closeMission } = useMissionLifecycle(mission.id)

  const handleExecute = async () => {
    // For production with real API:
    const response = await executeMission(mission, userId)
    if (response.status === 'ok') {
      // Store updated automatically via event
      toast.success('Trade executed!')
    }
  }

  return (
    <div>
      <button onClick={acceptMission}>Accept</button>
      <button onClick={handleExecute}>Execute</button>
      <button onClick={() => closeMission()}>Close</button>
    </div>
  )
}
```

## Event Bus API

### Core Events

```typescript
// Mission events
EVENTS.MISSION_CREATED    // New mission available
EVENTS.MISSION_UPDATED    // Status change
EVENTS.MISSION_SNAPSHOT   // Snapshot ready
EVENTS.MISSION_ACCEPTED   // User accepted
EVENTS.MISSION_EXECUTED   // Trade opened
EVENTS.MISSION_CLOSED     // Trade closed

// Order events
EVENTS.ORDER_EXECUTED     // Fill confirmation
EVENTS.ORDER_CLOSED       // Close confirmation
EVENTS.ORDER_FAILED       // Execution failed

// Price events
EVENTS.PRICE_UPDATE       // New price tick
EVENTS.PRICE_CONNECTED    // Stream connected
EVENTS.PRICE_DISCONNECTED // Stream disconnected

// XP events
EVENTS.XP_EARNED          // XP awarded
EVENTS.LEVEL_UP           // Level increased
```

### Subscribing to Events

```typescript
import { eventBus, EVENTS } from '@/lib/eventBus'

// Subscribe
const unsubscribe = eventBus.on(EVENTS.MISSION_CREATED, (data) => {
  console.log('New mission:', data)
})

// One-time listener
eventBus.once(EVENTS.ORDER_EXECUTED, (data) => {
  console.log('Order executed once:', data)
})

// Unsubscribe
unsubscribe()
// or
eventBus.off(EVENTS.MISSION_CREATED, handler)
```

### Emitting Events

```typescript
// Emit custom events
eventBus.emit('custom.event', { data: 'value' })

// Emit standard events
eventBus.emit(EVENTS.XP_EARNED, {
  amount: 100,
  reason: 'Trade Win'
})
```

## WebSocket Integration

### Mission Stream

Automatically connects when `useEventIntegration` is initialized with `enableMissionStream: true`.

Manual control:

```typescript
import { getMissionStream } from '@/lib/websocket'

const stream = getMissionStream()
stream.connect()
// ... later
stream.disconnect()
```

### Price Stream

Per-symbol streams, auto-managed:

```typescript
import { getPriceStream } from '@/lib/websocket'

const stream = getPriceStream('EURUSD')
stream.connect()

// Listen for updates via event bus
eventBus.on('price.EURUSD', (price) => {
  console.log('EURUSD:', price)
})
```

## API Integration

### Execute Trade

```typescript
import { executeMission } from '@/lib/api'

const response = await executeMission(mission, userId)
if (response.status === 'ok') {
  console.log('Ticket:', response.ticket)
  console.log('Filled at:', response.filled)
}
```

### Close Position

```typescript
import { closePosition } from '@/lib/api'

const response = await closePosition(ticket, userId)
if (response.status === 'ok') {
  console.log('P/L:', response.pl)
}
```

### Request Snapshot

```typescript
import { requestSnapshot } from '@/lib/api'

const response = await requestSnapshot(mission)
if (response.status === 'ok') {
  console.log('Snapshot URL:', response.image_url)
}
```

## Store Integration

The event integration automatically updates the Zustand store:

- New missions from `MISSION_CREATED` → added to `store.missions`
- Status updates from `MISSION_UPDATED` → updates mission in store
- Snapshots from `MISSION_SNAPSHOT` → updates `mission.snapshotUrl`
- Order events → updates mission status and records XP

## Production Checklist

### Environment Variables

```env
NEXT_PUBLIC_API_BASE_URL=https://api.bitten
NEXT_PUBLIC_WS_BASE_URL=wss://api.bitten
NEXT_PUBLIC_CDN_URL=https://cdn.bitten
```

### Authentication

```typescript
import { bittenAPI } from '@/lib/api'

// Set auth token after login
bittenAPI.setAuthToken(userToken)
```

### Error Handling

```typescript
try {
  const response = await executeMission(mission, userId)
  if (response.status === 'error') {
    toast.error(response.error || 'Execution failed')
  }
} catch (error) {
  console.error('Network error:', error)
  toast.error('Connection failed')
}
```

### Connection Status

```tsx
export function ConnectionIndicator() {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const handleConnect = () => setConnected(true)
    const handleDisconnect = () => setConnected(false)

    eventBus.on(EVENTS.WS_CONNECTED, handleConnect)
    eventBus.on(EVENTS.WS_DISCONNECTED, handleDisconnect)

    return () => {
      eventBus.off(EVENTS.WS_CONNECTED, handleConnect)
      eventBus.off(EVENTS.WS_DISCONNECTED, handleDisconnect)
    }
  }, [])

  return (
    <div className={connected ? 'bg-green-500' : 'bg-red-500'}>
      {connected ? 'Connected' : 'Disconnected'}
    </div>
  )
}
```

## Testing

### Mock Mode

For development without backend:

```typescript
// lib/mock.ts
export function mockMissionStream() {
  setInterval(() => {
    eventBus.emit(EVENTS.MISSION_CREATED, {
      id: `mock_${Date.now()}`,
      symbol: 'EURUSD',
      // ... mock data
    })
  }, 10000)
}

// In development
if (process.env.NODE_ENV === 'development') {
  mockMissionStream()
}
```

### Manual Testing

1. Open browser console
2. Test event emission:

```javascript
// In browser console
window.eventBus = eventBus // Expose for testing

// Emit test event
eventBus.emit('mission.created', {
  id: 'test_123',
  symbol: 'EURUSD',
  // ...
})
```

## Performance Considerations

1. **Debounce price updates** for UI rendering:
```typescript
import { debounce } from 'lodash'

const updatePrice = debounce((price) => {
  setPrice(price)
}, 100)

usePriceSubscription(symbol, updatePrice)
```

2. **Limit mission queue** size:
```typescript
// In store
if (missions.length > 50) {
  missions = missions.slice(-50) // Keep last 50
}
```

3. **Clean up old events**:
```typescript
// Periodically clean XP events
if (xpEvents.length > 100) {
  xpEvents = xpEvents.slice(0, 100)
}
```