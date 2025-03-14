import { NextResponse } from "next/server";

export async function GET(request: Request) {
  console.log("\n=== Processing Slack OAuth Callback ===");
  try {
    const url = new URL(request.url);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");
    const error = url.searchParams.get("error");
    const errorDescription = url.searchParams.get("error_description");

    console.log(`Received callback with code: ${code ? code.substring(0, 5) + '...' : 'none'}`);
    console.log(`State: ${state ? state.substring(0, 5) + '...' : 'none'}`);

    if (error) {
      console.error("OAuth error:", error, errorDescription);
      throw new Error(`OAuth error: ${error} - ${errorDescription}`);
    }

    if (!code || !state) {
      throw new Error("Missing required parameters");
    }

    // Parse state to get user_id and org_id
    const [_, org_id, user_id] = state.split('.');
    if (!org_id || !user_id) {
      throw new Error("Invalid state format");
    }

    const backendUrl = "http://localhost:8000/api/integrations/slack/oauth2callback";
    console.log(`Making request to backend: ${backendUrl}`);

    const searchParams = new URLSearchParams({
      code,
      state,
      org_id,
      user_id
    });

    const response = await fetch(`${backendUrl}?${searchParams.toString()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const responseStatus = response.status;
    console.log(`Backend response status: ${responseStatus}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend error response: ${errorText}`);
      throw new Error(`Backend error: ${errorText}`);
    }

    // Close the popup window and send a message to the parent
    return new NextResponse(
      `
      <html>
        <script>
          if (window.opener) {
            window.opener.postMessage({ 
              type: "SLACK_AUTH_SUCCESS",
              org_id: "${org_id}",
              user_id: "${user_id}"
            }, "*");
            window.close();
          }
        </script>
        <body>
          Authentication successful! You can close this window.
        </body>
      </html>
      `,
      {
        headers: {
          "Content-Type": "text/html",
        },
      }
    );
  } catch (error) {
    console.error("Error in Slack OAuth callback:", error);
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    
    // Return an error page that also attempts to close the window
    return new NextResponse(
      `
      <html>
        <script>
          if (window.opener) {
            window.opener.postMessage({ 
              type: "SLACK_AUTH_ERROR", 
              error: "${errorMessage}" 
            }, "*");
            window.close();
          }
        </script>
        <body>
          Authentication failed: ${errorMessage}
          <br>
          You can close this window.
        </body>
      </html>
      `,
      {
        headers: {
          "Content-Type": "text/html",
        },
      }
    );
  } finally {
    console.log("=== OAuth Callback Processing Complete ===\n");
  }
}
