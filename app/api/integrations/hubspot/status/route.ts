import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const url = new URL(request.url)
    const userId = url.searchParams.get("userId")
    const orgId = url.searchParams.get("orgId")

    if (!userId) {
      return NextResponse.json({ detail: "Missing userId parameter" }, { status: 400 })
    }

    // Make a request to your backend with consistent parameter naming
    const backendUrl = new URL("http://localhost:8000/api/integrations/hubspot/status")
    backendUrl.searchParams.append("userId", userId)
    if (orgId) {
      backendUrl.searchParams.append("orgId", orgId)
    }

    console.log("Checking HubSpot integration status...");
    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error in HubSpot status:", error)
    return NextResponse.json({ detail: "Failed to get HubSpot integration status" }, { status: 500 })
  }
}
