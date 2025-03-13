import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const url = new URL(request.url)
    const userId = url.searchParams.get("user_id")

    if (!userId) {
      return NextResponse.json({ detail: "Missing user_id parameter" }, { status: 400 })
    }

    // Make a request to your backend
    const response = await fetch(`http://localhost:8000/api/integrations/airtable/status?user_id=${userId}`, {
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
    console.error("Error in Airtable status:", error)
    return NextResponse.json({ detail: "Failed to get Airtable integration status" }, { status: 500 })
  }
}

