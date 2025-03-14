import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { userId, orgId } = await request.json()

    console.log("=== Starting HubSpot Authorization Process ===");
    console.log(`Authorizing HubSpot for user: ${userId}, org: ${orgId}`);

    const response = await fetch("http://localhost:8000/api/integrations/hubspot/authorize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ userId, orgId }),
    })

    if (!response.ok) {
      console.error(`Backend error: ${response.status}`);
      const errorText = await response.text();
      throw new Error(`Backend returned ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log("Authorization URL generated successfully");
    console.log(`URL generated: ${data.url.substring(0, 50)}...`);
    console.log("=== Authorization Process Complete ===");

    return NextResponse.json(data)
  } catch (error) {
    console.error("Error in HubSpot authorize:", error)
    const errorMessage = error instanceof Error ? error.message : "Failed to authorize HubSpot integration";
    return NextResponse.json({ detail: errorMessage }, { status: 500 });
  }
}
