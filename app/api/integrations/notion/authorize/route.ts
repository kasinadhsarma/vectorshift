import { NextResponse } from "next/server"

export async function POST(request: Request) {
  console.log("\n=== Starting Notion Authorization Process ===")
  try {
    const body = await request.json()
    const { userId, orgId } = body

    console.log(`Authorizing Notion for user: ${userId}, orgId: ${orgId || 'not provided'}`)

    const backendUrl = process.env.BACKEND_URL + "/api/integrations/notion/authorize"
    console.log(`Making request to backend: ${backendUrl}`)
    console.log("Request body:", { userId, orgId })

    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ userId, orgId }),
    })

    const responseStatus = response.status
    console.log(`Backend response status: ${responseStatus}`)

    if (!response.ok) {
      const errorText = await response.text()
      console.log(`Backend error response: ${errorText}`)
      return NextResponse.json(
        { detail: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log("Authorization URL generated successfully")

    return NextResponse.json(data)
  } catch (error) {
    console.error("Error in authorization process:", error)
    return NextResponse.json(
      { 
        detail: error instanceof Error ? error.message : "Failed to start authorization" 
      },
      { status: 500 }
    )
  } finally {
    console.log("=== Authorization Process Complete ===\n")
  }
}
