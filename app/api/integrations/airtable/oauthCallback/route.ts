import { NextResponse } from "next/server";

export async function GET(request: Request) {
  console.log("\n=== Processing Airtable OAuth Callback ===");
  try {
    const url = new URL(request.url);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");
    const error = url.searchParams.get("error");
    const errorDescription = url.searchParams.get("error_description");
    const codeChallenge = url.searchParams.get("code_challenge");
    const codeChallengeMethod = url.searchParams.get("code_challenge_method");

    console.log(`Received callback with code: ${code ? code.substring(0, 5) + '...' : 'none'}`);
    console.log(`State: ${state ? state.substring(0, 5) + '...' : 'none'}`);
    console.log(`PKCE params: challenge=${!!codeChallenge}, method=${codeChallengeMethod}`);

    if (error) {
      console.error("OAuth error:", error, errorDescription);
      throw new Error(`OAuth error: ${error} - ${errorDescription}`);
    }

    if (!code || !state) {
      throw new Error("Missing required parameters");
    }

    const backendUrl = "http://localhost:8000/api/integrations/airtable/oauth2callback";
    console.log(`Making request to backend: ${backendUrl}`);

    const searchParams = new URLSearchParams({
      code,
      state,
      ...(codeChallenge && { code_challenge: codeChallenge }),
      ...(codeChallengeMethod && { code_challenge_method: codeChallengeMethod })
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
            window.opener.postMessage({ type: "AIRTABLE_AUTH_SUCCESS" }, "*");
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
    console.error("Error in Airtable OAuth callback:", error);
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    
    // Return an error page that also attempts to close the window
    return new NextResponse(
      `
      <html>
        <script>
          if (window.opener) {
            window.opener.postMessage({ type: "AIRTABLE_AUTH_ERROR", error: "${errorMessage}" }, "*");
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
