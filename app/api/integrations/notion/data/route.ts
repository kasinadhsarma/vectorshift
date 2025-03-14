import { NextResponse } from "next/server"

export async function POST(request: Request) {
<<<<<<< HEAD
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
=======
  try {
    const { credentials, userId, orgId } = await request.json()

    // Make a request to your backend
    const response = await fetch("http://localhost:8000/api/integrations/notion/data", {
>>>>>>> origin/main
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
<<<<<<< HEAD
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
=======
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
>>>>>>> origin/main
  }
}
