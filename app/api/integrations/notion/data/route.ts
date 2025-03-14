import { NextResponse } from "next/server"

export async function POST(request: Request) {
  console.log("\n=== Fetching Notion Data ===")
  try {
    const body = await request.json()
    const { userId, orgId } = body

    console.log(`Fetching data for user: ${userId}, orgId: ${orgId || 'not provided'}`)

    if (!userId) {
      return NextResponse.json(
        { detail: "Missing required userId parameter" },
        { status: 400 }
      )
    }

    const backendUrl = "http://localhost:8000/api/integrations/notion/data"
    console.log(`Making request to backend: ${backendUrl}`)

    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ userId, orgId }),
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
    console.log("Successfully fetched Notion data")

    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching Notion data:", error)
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to fetch Notion data" },
      { status: 500 }
    )
  } finally {
    console.log("=== Data Fetch Complete ===\n")
  }
}
