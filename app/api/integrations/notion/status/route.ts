import { NextResponse } from "next/server"

export async function GET(request: Request) {
  console.log("\n=== Checking Notion Integration Status ===")
  try {
    const url = new URL(request.url)
    const userId = url.searchParams.get("userId")
    const orgId = url.searchParams.get("orgId")

    console.log(`Parameters received - userId: ${userId}, orgId: ${orgId}`)

    if (!userId) {
      return NextResponse.json(
        { detail: "Missing required userId parameter" },
        { status: 400 }
      )
    }

    const backendUrl = `http://localhost:8000/api/integrations/notion/status?userId=${userId}${orgId ? `&orgId=${orgId}` : ''}`
    console.log(`Making request to backend: ${backendUrl}`)

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    console.log(`Backend response status: ${response.status}`)

    if (!response.ok) {
      const errorText = await response.text()
      console.error(`Backend error response: ${errorText}`)
      return NextResponse.json(
        { detail: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log("Integration status retrieved successfully")
    console.log(`Connected: ${data.isConnected}, Status: ${data.status}`)

    return NextResponse.json(data)
  } catch (error) {
    console.error("Error checking integration status:", error)
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to check integration status" },
      { status: 500 }
    )
  } finally {
    console.log("=== Status Check Complete ===\n")
  }
}
