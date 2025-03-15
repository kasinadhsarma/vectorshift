import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const userId = searchParams.get('userId')
  const orgId = searchParams.get('orgId')

  if (!userId || !orgId) {
    return NextResponse.json(
      { detail: 'Missing required parameters' },
      { status: 400 }
    )
  }

  try {
    const response = await fetch(
      `http://localhost:8000/integrations/airtable/status?userId=${userId}&orgId=${orgId}`,
      {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        cache: 'no-store'
      }
    )

    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || 'Failed to check integration status')
    }
    
    return NextResponse.json({
      isConnected: !!data.credentials,
      credentials: data.credentials
    })
  } catch (error) {
    console.error('Error checking Airtable integration status:', error)
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }
}
