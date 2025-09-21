#!/usr/bin/env node

// Test script for event bus integration
// Run this to verify the complete mission lifecycle works

import { eventBus, EVENTS } from './lib/eventBus.js'

console.log('🎯 BITTEN Event Bus Integration Test')
console.log('=' . repeat(50))

// Test logging
const logEvent = (event, data) => {
  const time = new Date().toLocaleTimeString()
  console.log(`[${time}] ${event}:`, JSON.stringify(data, null, 2))
}

// Subscribe to all events for monitoring
Object.values(EVENTS).forEach(event => {
  eventBus.on(event, (data) => logEvent(event, data))
})

console.log('✅ Subscribed to all events')

// Test sequence
const runTests = async () => {
  console.log('\n📊 Starting test sequence...\n')
  
  // 1. Create a mission
  console.log('1️⃣ Creating mission...')
  const mission = {
    id: `TEST_${Date.now()}`,
    symbol: 'EURUSD',
    direction: 'BUY',
    timeframe: 'M15',
    entry: 1.08456,
    sl: 1.08256,
    tp: 1.08856,
    pattern: 'LIQUIDITY_SWEEP_REVERSAL',
    type: 'SNIPER',
    confidence: 85,
    status: 'NEW',
    expiresIn: 15,
    openedAt: Date.now()
  }
  eventBus.emit(EVENTS.MISSION_CREATED, mission)
  await new Promise(r => setTimeout(r, 1000))
  
  // 2. Attach snapshot
  console.log('\n2️⃣ Attaching snapshot...')
  eventBus.emit(EVENTS.MISSION_SNAPSHOT, {
    id: mission.id,
    snapshot_url: 'https://cdn.bitten/test-snapshot.png',
    sha256: 'abc123'
  })
  await new Promise(r => setTimeout(r, 1000))
  
  // 3. Accept mission
  console.log('\n3️⃣ Accepting mission...')
  eventBus.emit(EVENTS.MISSION_ACCEPTED, { id: mission.id })
  await new Promise(r => setTimeout(r, 1000))
  
  // 4. Execute order
  console.log('\n4️⃣ Executing order...')
  eventBus.emit(EVENTS.ORDER_EXECUTED, {
    ticket: `TKT_${Date.now()}`,
    mission_id: mission.id,
    filled: mission.entry + 0.0002,
    sl: mission.sl,
    tp: mission.tp,
    broker: 'Demo-Broker'
  })
  await new Promise(r => setTimeout(r, 1000))
  
  // 5. Simulate price updates
  console.log('\n5️⃣ Simulating price stream...')
  let price = mission.entry
  for (let i = 0; i < 5; i++) {
    price += (Math.random() - 0.5) * 0.0005
    eventBus.emit(EVENTS.PRICE_UPDATE, {
      symbol: mission.symbol,
      t: Date.now(),
      bid: price - 0.0001,
      ask: price + 0.0001
    })
    await new Promise(r => setTimeout(r, 500))
  }
  
  // 6. Close order
  console.log('\n6️⃣ Closing order...')
  const pl = Math.random() > 0.5 ? 25.5 : -15.2
  eventBus.emit(EVENTS.ORDER_CLOSED, {
    ticket: `TKT_${mission.id}`,
    mission_id: mission.id,
    pl,
    closed: mission.entry + (pl > 0 ? 0.002 : -0.001)
  })
  await new Promise(r => setTimeout(r, 500))
  
  // 7. Award XP
  console.log('\n7️⃣ Awarding XP...')
  eventBus.emit(EVENTS.XP_EARNED, {
    amount: pl > 0 ? 100 : 0,
    reason: pl > 0 ? 'Trade Win' : 'Trade Loss',
    pl
  })
  
  console.log('\n✅ Test sequence complete!')
  console.log('=' . repeat(50))
  console.log('Check the UI at http://localhost:3001/test')
}

// Run tests after a short delay
setTimeout(runTests, 1000)

// Keep script alive
setInterval(() => {}, 1000)