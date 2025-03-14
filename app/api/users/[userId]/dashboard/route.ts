import { NextResponse } from "next/server"

export async function GET(request: Request, { params }: { params: { userId: string } }) {
  try {
    const userId = params.userId

    // Make a request to your backend
    const response = await fetch(`http://localhost:8000/api/users/${userId}/dashboard`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()

    // Mock data for testing if backend doesn't return proper data
    const mockData = {
      user: {
        id: userId,
        name: "Test User",
        email: "test@example.com",
      },
      integrations: [
        { type: "notion", status: "active" },
        { type: "airtable", status: "inactive" },
        { type: "hubspot", status: "inactive" },
      ],
      recentActivity: [
        { id: 1, type: "login", timestamp: new Date().toISOString() },
        { id: 2, type: "integration_connected", integration: "notion", timestamp: new Date().toISOString() },
      ],
    }

    return NextResponse.json(data || mockData)
  } catch (error) {
    console.error("Error in user dashboard:", error)
    return NextResponse.json({ detail: "Failed to fetch user dashboard data" }, { status: 500 })
  }
}

