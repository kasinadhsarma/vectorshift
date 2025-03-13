import { NextResponse } from "next/server"

export async function GET(request: Request) {
  console.log("\n=== Checking Notion Integration Status ===");
  try {
    const url = new URL(request.url)
    const userId = url.searchParams.get("userId")
    const orgId = url.searchParams.get("orgId")

    console.log(`Parameters received - userId: ${userId}, orgId: ${orgId || 'not provided'}`);

    if (!userId) {
      console.log("Error: Missing userId parameter");
      return NextResponse.json({ detail: "Missing userId parameter" }, { status: 400 })
    }

    const backendUrl = `http://localhost:8000/api/integrations/notion/status?userId=${userId}${orgId ? `&orgId=${orgId}` : ''}`;
    console.log(`Making request to backend: ${backendUrl}`);

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    const responseStatus = response.status;
    console.log(`Backend response status: ${responseStatus}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.log(`Backend error response: ${errorText}`);
      throw new Error(`Backend returned ${responseStatus}: ${errorText}`);
    }

    const data = await response.json();
    console.log("Integration status retrieved successfully");
    console.log(`Connected: ${data.isConnected}, Status: ${data.status}`);
    return NextResponse.json(data);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    console.error("Error checking Notion integration status:", errorMessage);
    return NextResponse.json(
      { detail: `Failed to get Notion integration status: ${errorMessage}` },
      { status: 500 }
    );
  } finally {
    console.log("=== Status Check Complete ===\n");
  }
}
