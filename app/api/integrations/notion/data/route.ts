import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { credentials, userId, orgId } = await request.json()

    // Make a request to your backend
    const response = await fetch("http://localhost:8000/api/integrations/notion/data", {
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
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()

    // Mock data for testing if backend doesn't return proper data
    const mockData = {
      pages: [
        { id: "page1", title: "Project Roadmap", lastEdited: "2023-05-15" },
        { id: "page2", title: "Meeting Notes", lastEdited: "2023-05-10" },
        { id: "page3", title: "Product Specs", lastEdited: "2023-05-05" },
      ],
      databases: [
        { id: "db1", title: "Tasks", items: 24 },
        { id: "db2", title: "Team Members", items: 8 },
      ],
    }

    return NextResponse.json(data || mockData)
  } catch (error) {
    console.error("Error in Notion data:", error)
    return NextResponse.json({ detail: "Failed to fetch Notion data" }, { status: 500 })
  }
}

