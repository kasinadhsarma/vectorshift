import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const url = new URL(request.url)
    const userId = url.searchParams.get("user_id")
    const orgId = url.searchParams.get("org_id")

    if (!userId) {
      return NextResponse.json({ detail: "Missing user_id parameter" }, { status: 400 })
    }

    // Make a request to your backend
    const response = await fetch(
      `http://localhost:8000/api/integrations/slack/status?user_id=${userId}&org_id=${orgId || ""}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    )

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error in Slack status:", error)
    return NextResponse.json({ detail: "Failed to get Slack integration status" }, { status: 500 })
  }
}

