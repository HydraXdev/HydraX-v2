#!/usr/bin/env node

// Direct test of event bus functionality
import { EventEmitter } from 'events'

// Create a simple event bus
class EventBus extends EventEmitter {
  constructor() {
    super()
    this.setMaxListeners(100)
  }

  emit(event, data) {
    console.log(`📨 Emitting: ${event}`, data)
    return super.emit(event, data)
  }

  on(event, handler) {
    console.log(`👂 Subscribed to: ${event}`)
    return super.on(event, handler)
  }
}

const eventBus = new EventBus()

const EVENTS = {
  MISSION_CREATED: 'mission.created',
  MISSION_UPDATED: 'mission.updated',
  MISSION_SNAPSHOT: 'mission.snapshot',
  MISSION_ACCEPTED: 'mission.accepted',
  MISSION_EXECUTED: 'mission.executed',
  MISSION_CLOSED: 'mission.closed',
  ORDER_EXECUTED: 'order.executed',
  ORDER_CLOSED: 'order.closed',
  ORDER_FAILED: 'order.failed',
  PRICE_UPDATE: 'price.update',
  PRICE_CONNECTED: 'price.connected',
  PRICE_DISCONNECTED: 'price.disconnected',
  XP_EARNED: 'xp.earned',
  LEVEL_UP: 'level.up',
  WS_CONNECTED: 'ws.connected',
  WS_DISCONNECTED: 'ws.disconnected',
  WS_ERROR: 'ws.error'
}

console.log('\n🎯 BITTEN Event Bus Test')
console.log('=' . repeat(50))

// Test mission lifecycle
let missionState = {}
let xpTotal = 1250

// Subscribe to events
eventBus.on(EVENTS.MISSION_CREATED, (data) => {
  missionState[data.id] = { ...data, status: 'NEW' }
  console.log(`✅ Mission created: ${data.id}`)
})

eventBus.on(EVENTS.MISSION_SNAPSHOT, (data) => {
  if (missionState[data.id]) {
    missionState[data.id].snapshotUrl = data.snapshot_url
    console.log(`📷 Snapshot attached: ${data.id}`)
  }
})

eventBus.on(EVENTS.MISSION_ACCEPTED, (data) => {
  if (missionState[data.id]) {
    missionState[data.id].status = 'ACCEPTED'
    console.log(`🤝 Mission accepted: ${data.id}`)
  }
})

eventBus.on(EVENTS.ORDER_EXECUTED, (data) => {
  if (missionState[data.mission_id]) {
    missionState[data.mission_id].status = 'LIVE'
    missionState[data.mission_id].ticket = data.ticket
    console.log(`🚀 Order executed: ${data.ticket}`)
  }
})

eventBus.on(EVENTS.ORDER_CLOSED, (data) => {
  if (missionState[data.mission_id]) {
    missionState[data.mission_id].status = 'CLOSED'
    missionState[data.mission_id].pl = data.pl
    console.log(`💰 Order closed: P/L ${data.pl}`)
  }
})

eventBus.on(EVENTS.XP_EARNED, (data) => {
  xpTotal += data.amount
  console.log(`✨ XP earned: +${data.amount} (Total: ${xpTotal})`)
})

// Run test sequence
const runTest = async () => {
  console.log('\n🚀 Starting test sequence...\n')
  
  const missionId = `TEST_${Date.now()}`
  
  // 1. Create mission
  eventBus.emit(EVENTS.MISSION_CREATED, {
    id: missionId,
    symbol: 'EURUSD',
    direction: 'BUY',
    entry: 1.08456,
    sl: 1.08256,
    tp: 1.08856
  })
  
  await new Promise(r => setTimeout(r, 500))
  
  // 2. Attach snapshot
  eventBus.emit(EVENTS.MISSION_SNAPSHOT, {
    id: missionId,
    snapshot_url: 'https://cdn.bitten/snapshot.png'
  })
  
  await new Promise(r => setTimeout(r, 500))
  
  // 3. Accept mission
  eventBus.emit(EVENTS.MISSION_ACCEPTED, {
    id: missionId
  })
  
  await new Promise(r => setTimeout(r, 500))
  
  // 4. Execute order
  eventBus.emit(EVENTS.ORDER_EXECUTED, {
    ticket: 'TKT_123456',
    mission_id: missionId,
    filled: 1.08458
  })
  
  await new Promise(r => setTimeout(r, 500))
  
  // 5. Close order with profit
  eventBus.emit(EVENTS.ORDER_CLOSED, {
    ticket: 'TKT_123456',
    mission_id: missionId,
    pl: 42.5
  })
  
  await new Promise(r => setTimeout(r, 500))
  
  // 6. Award XP
  eventBus.emit(EVENTS.XP_EARNED, {
    amount: 100,
    reason: 'Trade Win'
  })
  
  console.log('\n🏁 Test complete!')
  console.log('\nFinal Mission State:')
  console.log(JSON.stringify(missionState[missionId], null, 2))
  console.log(`\nTotal XP: ${xpTotal}`)
  console.log('=' . repeat(50))
  
  // Test passed if mission went through all states
  const mission = missionState[missionId]
  if (mission && 
      mission.status === 'CLOSED' && 
      mission.snapshotUrl && 
      mission.ticket && 
      mission.pl !== undefined) {
    console.log('\n✅ ALL TESTS PASSED!')
    process.exit(0)
  } else {
    console.log('\n❌ Some tests failed!')
    process.exit(1)
  }
}

// Run the test
runTest()