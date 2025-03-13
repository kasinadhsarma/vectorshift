import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { userId, orgId } = await request.json()

    // Make a request to your backend
    const response = await fetch("http://localhost:8000/api/integrations/airtable/authorize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: userId, org_id: orgId }),
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error in Airtable authorize:", error)
    return NextResponse.json({ detail: "Failed to authorize Airtable integration" }, { status: 500 })
  }
}

