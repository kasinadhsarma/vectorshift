import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { credentials, userId, orgId } = await request.json()

    // Make a request to your backend
    const response = await fetch("http://localhost:8000/api/integrations/airtable/data", {
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
      bases: [
        { id: "base1", name: "Project Tracker", tables: 3 },
        { id: "base2", name: "Marketing Calendar", tables: 2 },
      ],
      tables: [
        { id: "table1", name: "Tasks", records: 45, baseId: "base1" },
        { id: "table2", name: "Team Members", records: 12, baseId: "base1" },
        { id: "table3", name: "Projects", records: 8, baseId: "base1" },
        { id: "table4", name: "Campaigns", records: 15, baseId: "base2" },
        { id: "table5", name: "Content Calendar", records: 30, baseId: "base2" },
      ],
    }

    return NextResponse.json(data || mockData)
  } catch (error) {
    console.error("Error in Airtable data:", error)
    return NextResponse.json({ detail: "Failed to fetch Airtable data" }, { status: 500 })
  }
}

