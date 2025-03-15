import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second

async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${BACKEND_URL}/health`)
    return response.ok
  } catch {
    return false
  }
}

async function retryWithBackoff(fn: () => Promise<Response>, retries = MAX_RETRIES): Promise<Response> {
  try {
    return await fn()
  } catch (error) {
    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * (MAX_RETRIES - retries + 1)))
      return retryWithBackoff(fn, retries - 1)
    }
    throw error
  }
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const userId = searchParams.get('userId')
  const orgId = searchParams.get('orgId')

  if (!userId || !orgId) {
    return NextResponse.json(
      { 
        status: 'error',
        detail: 'Missing required parameters',
        requiredParams: ['userId', 'orgId']
      },
      { status: 400 }
    )
  }

  try {
    // Check backend health first
    const isBackendHealthy = await checkBackendHealth()
    if (!isBackendHealthy) {
      return NextResponse.json({
        status: 'error',
        detail: 'Backend service is unavailable',
        serviceStatus: {
          backend: 'unavailable'
        }
      }, { status: 503 })
    }

    const response = await retryWithBackoff(() => 
      fetch(
        `${BACKEND_URL}/integrations/notion/status?userId=${userId}&orgId=${orgId}`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          cache: 'no-store'
        }
      )
    )

    const data = await response.json()
    
    if (!response.ok) {
      return NextResponse.json({
        status: 'error',
        detail: data.error || 'Failed to check integration status',
        statusCode: response.status,
        serviceStatus: {
          backend: 'available',
          notion: 'unavailable'
        }
      }, { status: response.status })
    }
    
    return NextResponse.json({
      status: 'success',
      isConnected: !!data.credentials,
      credentials: data.credentials,
      serviceStatus: {
        backend: 'available',
        notion: data.credentials ? 'connected' : 'disconnected'
      }
    })
  } catch (error) {
    console.error('Error checking Notion integration status:', error)
    return NextResponse.json({
      status: 'error',
      detail: error instanceof Error ? error.message : 'Internal server error',
      serviceStatus: {
        backend: 'error',
        notion: 'unknown'
      }
    }, { status: 500 })
  }
}
