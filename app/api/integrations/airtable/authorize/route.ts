import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { userId, orgId } = await request.json()

    // Make a request to your backend
    const response = await fetch("http://localhost:8000/api/integrations/airtable/authorize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: userId, org_id: orgId }),
    })

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Backend returned ${response.status}: ${errorText}`);
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error in Airtable authorize:", error)
    const errorMessage = error instanceof Error ? error.message : "Failed to authorize Airtable integration";
    return NextResponse.json({ detail: errorMessage }, { status: 500 });
  }
}
