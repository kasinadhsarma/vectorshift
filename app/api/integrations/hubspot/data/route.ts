import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { credentials, userId, orgId } = await request.json()

    // Make a request to your backend
    const response = await fetch("http://localhost:8000/api/integrations/hubspot/data", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        credentials,
        user_id: userId,
        org_id: orgId,
      }),
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}: ${await response.text()}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error in HubSpot data:", error)
    return NextResponse.json({ detail: "Failed to fetch HubSpot data: " + (error as Error).message }, { status: 500 })
  }
}

