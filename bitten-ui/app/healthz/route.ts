import { NextRequest, NextResponse } from 'next/server'

/**
 * Health Check Endpoint
 *
 * Returns system health status including:
 * - API connectivity to backend
 * - WebSocket service status
 * - Build info
 */

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  version: string
  services: {
    api: ServiceStatus
    websocket: ServiceStatus
    frontend: ServiceStatus
  }
  uptime: number
}

interface ServiceStatus {
  status: 'up' | 'down' | 'unknown'
  latency?: number
  error?: string
}

// Track when the service started
const startTime = Date.now()

async function checkAPIHealth(): Promise<ServiceStatus> {
  try {
    const startTime = Date.now()
    const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888'

    const response = await fetch(`${apiUrl}/healthz`, {
      method: 'GET',
      headers: { 'User-Agent': 'BITTEN-UI-HealthCheck/1.0' },
      signal: AbortSignal.timeout(5000) // 5 second timeout
    })

    const latency = Date.now() - startTime

    if (response.ok) {
      return { status: 'up', latency }
    } else {
      return {
        status: 'down',
        latency,
        error: `HTTP ${response.status}: ${response.statusText}`
      }
    }
  } catch (error) {
    return {
      status: 'down',
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

async function checkWebSocketHealth(): Promise<ServiceStatus> {
  // For WebSocket, we can't easily test connection in a serverless function
  // Instead, we check if the service configuration is valid
  try {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8888'

    // Basic URL validation
    new URL(wsUrl.replace('ws:', 'http:').replace('wss:', 'https:'))

    return {
      status: 'unknown' // WebSocket health needs client-side testing
    }
  } catch (error) {
    return {
      status: 'down',
      error: 'Invalid WebSocket configuration'
    }
  }
}

function checkFrontendHealth(): ServiceStatus {
  // Frontend is healthy if we can execute this function
  return { status: 'up' }
}

function determineOverallStatus(services: HealthStatus['services']): HealthStatus['status'] {
  const statuses = Object.values(services).map(service => service.status)

  if (statuses.every(status => status === 'up')) {
    return 'healthy'
  } else if (statuses.some(status => status === 'up')) {
    return 'degraded'
  } else {
    return 'unhealthy'
  }
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const startTime = Date.now()

  try {
    // Run health checks in parallel
    const [apiStatus, wsStatus] = await Promise.all([
      checkAPIHealth(),
      checkWebSocketHealth()
    ])

    const frontendStatus = checkFrontendHealth()
    const uptime = Date.now() - startTime

    const services = {
      api: apiStatus,
      websocket: wsStatus,
      frontend: frontendStatus
    }

    const healthStatus: HealthStatus = {
      status: determineOverallStatus(services),
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '0.1.0',
      services,
      uptime: Math.floor((Date.now() - startTime) / 1000)
    }

    // Set appropriate HTTP status based on health
    const httpStatus = healthStatus.status === 'healthy' ? 200 :
                      healthStatus.status === 'degraded' ? 200 : 503

    return NextResponse.json(healthStatus, {
      status: httpStatus,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Content-Type': 'application/json'
      }
    })

  } catch (error) {
    // If health check itself fails
    const errorStatus: HealthStatus = {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '0.1.0',
      services: {
        api: { status: 'unknown', error: 'Health check failed' },
        websocket: { status: 'unknown', error: 'Health check failed' },
        frontend: { status: 'down', error: 'Health check crashed' }
      },
      uptime: Math.floor((Date.now() - startTime) / 1000)
    }

    return NextResponse.json(errorStatus, {
      status: 503,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Content-Type': 'application/json'
      }
    })
  }
}