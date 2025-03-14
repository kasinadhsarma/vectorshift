import { NextResponse } from "next/server"

export async function POST(request: Request) {
<<<<<<< HEAD
  console.log("\n=== Starting Notion Authorization Process ===")
  try {
    const body = await request.json()
    const { userId, orgId } = body

    console.log(`Authorizing Notion for user: ${userId}, orgId: ${orgId || 'not provided'}`)

    const backendUrl = process.env.BACKEND_URL + "/api/integrations/notion/authorize"
    console.log(`Making request to backend: ${backendUrl}`)
    console.log("Request body:", { userId, orgId })
=======
  console.log("\n=== Starting Notion Authorization Process ===");
  try {
    const body = await request.json();
    const { userId, orgId } = body;

    console.log(`Authorizing Notion for user: ${userId}, orgId: ${orgId || 'not provided'}`);

    const backendUrl = "http://localhost:8000/api/integrations/notion/authorize";
    console.log(`Making request to backend: ${backendUrl}`);
    console.log("Request body:", { userId, orgId });
>>>>>>> origin/main

    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ userId, orgId }),
    })

<<<<<<< HEAD
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
=======
    const responseStatus = response.status;
    console.log(`Backend response status: ${responseStatus}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.log(`Backend error response: ${errorText}`);
      throw new Error(`Backend returned ${responseStatus}: ${errorText}`);
    }

    const data = await response.json();
    console.log("Authorization URL generated successfully");
    console.log(`URL generated: ${data.url.substring(0, 50)}...`); // Log partial URL for security

    return NextResponse.json(data);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    console.error("Error in Notion authorize:", errorMessage);
    return NextResponse.json(
      { detail: `Failed to authorize Notion integration: ${errorMessage}` },
      { status: 500 }
    );
  } finally {
    console.log("=== Authorization Process Complete ===\n");
>>>>>>> origin/main
  }
}
