import { NextResponse } from "next/server"

export async function GET(request: Request) {
<<<<<<< HEAD
  console.log("\n=== Checking Notion Integration Status ===")
=======
  console.log("\n=== Checking Notion Integration Status ===");
>>>>>>> origin/main
  try {
    const url = new URL(request.url)
    const userId = url.searchParams.get("userId")
    const orgId = url.searchParams.get("orgId")

<<<<<<< HEAD
    console.log(`Parameters received - userId: ${userId}, orgId: ${orgId}`)

    if (!userId) {
      return NextResponse.json(
        { detail: "Missing required userId parameter" },
        { status: 400 }
      )
    }

    const backendUrl = `http://localhost:8000/api/integrations/notion/status?userId=${userId}${orgId ? `&orgId=${orgId}` : ''}`
    console.log(`Making request to backend: ${backendUrl}`)
=======
    console.log(`Parameters received - userId: ${userId}, orgId: ${orgId || 'not provided'}`);

    if (!userId) {
      console.log("Error: Missing userId parameter");
      return NextResponse.json({ detail: "Missing userId parameter" }, { status: 400 })
    }

    const backendUrl = `http://localhost:8000/api/integrations/notion/status?userId=${userId}${orgId ? `&orgId=${orgId}` : ''}`;
    console.log(`Making request to backend: ${backendUrl}`);
>>>>>>> origin/main

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

<<<<<<< HEAD
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
    console.log("Integration status retrieved successfully")
    console.log(`Connected: ${data.isConnected}, Status: ${data.status}`)

    return NextResponse.json(data)
  } catch (error) {
    console.error("Error checking integration status:", error)
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to check integration status" },
      { status: 500 }
    )
  } finally {
    console.log("=== Status Check Complete ===\n")
=======
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
>>>>>>> origin/main
  }
}
