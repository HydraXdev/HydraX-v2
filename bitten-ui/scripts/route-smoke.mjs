#!/usr/bin/env node

/**
 * Route Smoke Test
 *
 * Validates all critical routes return 200 OK
 * Usage: node scripts/route-smoke.mjs [--base-url=http://localhost:3000]
 */

import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

// Configuration
const DEFAULT_BASE_URL = 'http://localhost:3000'
const TIMEOUT = 10000 // 10 seconds
const args = process.argv.slice(2)
const baseUrl = args.find(arg => arg.startsWith('--base-url='))?.split('=')[1] || DEFAULT_BASE_URL

// Routes to test
const routes = [
  { path: '/', name: 'War Room (Root)' },
  { path: '/mission-brief', name: 'Mission Brief' },
  { path: '/mission-brief?id=demo-001', name: 'Mission Brief with ID' },
  { path: '/xp', name: 'XP Dashboard' },
  { path: '/settings', name: 'Settings' },
  { path: '/live', name: 'Live Integration' },
  { path: '/test', name: 'Test Harness' }
]

// ANSI colors
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
}

async function testRoute(route) {
  const url = `${baseUrl}${route.path}`
  const startTime = Date.now()

  try {
    const { stdout } = await execAsync(`curl -s -I --max-time 10 "${url}"`, { timeout: TIMEOUT })
    const elapsed = Date.now() - startTime
    const statusLine = stdout.split('\n')[0]
    const status = statusLine.split(' ')[1]

    if (status === '200') {
      console.log(`${colors.green}✓${colors.reset} ${route.name.padEnd(25)} ${colors.green}200 OK${colors.reset} (${elapsed}ms)`)
      return { success: true, status, elapsed, url }
    } else {
      console.log(`${colors.red}✗${colors.reset} ${route.name.padEnd(25)} ${colors.red}${status || 'UNKNOWN'}${colors.reset} (${elapsed}ms)`)
      return { success: false, status, elapsed, url, error: statusLine }
    }
  } catch (error) {
    const elapsed = Date.now() - startTime
    console.log(`${colors.red}✗${colors.reset} ${route.name.padEnd(25)} ${colors.red}ERROR${colors.reset} (${elapsed}ms) - ${error.message}`)
    return { success: false, elapsed, url, error: error.message }
  }
}

async function runSmokeTest() {
  console.log(`${colors.bold}${colors.blue}🧪 BITTEN UI Route Smoke Test${colors.reset}`)
  console.log(`${colors.blue}Base URL: ${baseUrl}${colors.reset}`)
  console.log(`${colors.blue}Timeout: ${TIMEOUT}ms${colors.reset}\n`)

  const results = []

  for (const route of routes) {
    const result = await testRoute(route)
    results.push(result)
  }

  // Summary
  const passed = results.filter(r => r.success).length
  const failed = results.filter(r => !r.success).length
  const avgTime = Math.round(results.reduce((sum, r) => sum + r.elapsed, 0) / results.length)

  console.log(`\n${colors.bold}📊 Summary:${colors.reset}`)
  console.log(`${colors.green}✓ Passed: ${passed}${colors.reset}`)
  if (failed > 0) {
    console.log(`${colors.red}✗ Failed: ${failed}${colors.reset}`)
  }
  console.log(`⏱️  Average response time: ${avgTime}ms`)

  // Exit with appropriate code
  if (failed > 0) {
    console.log(`\n${colors.red}💥 Smoke test FAILED${colors.reset}`)
    process.exit(1)
  } else {
    console.log(`\n${colors.green}🎉 All routes healthy!${colors.reset}`)
    process.exit(0)
  }
}

// Health check for server availability
async function checkServerHealth() {
  try {
    await execAsync(`curl -s --max-time 5 "${baseUrl}" > /dev/null`)
    return true
  } catch {
    return false
  }
}

// Main execution
async function main() {
  console.log(`${colors.yellow}🔍 Checking server availability...${colors.reset}`)

  const serverUp = await checkServerHealth()
  if (!serverUp) {
    console.log(`${colors.red}💥 Server not responding at ${baseUrl}${colors.reset}`)
    console.log(`${colors.yellow}💡 Make sure the dev server is running: npm run dev${colors.reset}`)
    process.exit(1)
  }

  await runSmokeTest()
}

main().catch(error => {
  console.error(`${colors.red}💥 Smoke test crashed:${colors.reset}`, error)
  process.exit(1)
})