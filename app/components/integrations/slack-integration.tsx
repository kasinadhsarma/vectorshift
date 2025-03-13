"use client"

import { useState, useEffect } from "react"
import axios, { type AxiosError } from "axios"
import { Button } from "@/app/components/ui/button"
import { Loader2 } from "lucide-react"
import { getIntegrationStatus, getIntegrationData } from "@/app/lib/api-client"

interface SlackChannel {
  id: string
  name: string
  members: number
  is_private: boolean
  topic: string
  purpose: string
}

interface SlackUser {
  id: string
  name: string
  real_name: string
  email: string
  title: string
  status_text: string
  status_emoji: string
}

interface SlackTeam {
  id: string
  name: string
}

interface SlackData {
  channels: SlackChannel[]
  users: SlackUser[]
  team: SlackTeam
}

interface SlackIntegrationProps {
  userId: string
  orgId: string
}

interface ErrorResponse {
  detail: string
}

export const SlackIntegration = ({ userId, orgId }: SlackIntegrationProps) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [slackData, setSlackData] = useState<SlackData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [credentials, setCredentials] = useState<any>(null)

  useEffect(() => {
    // Check if already connected
    const checkConnection = async () => {
      try {
        const status = await getIntegrationStatus("slack", userId, orgId)
        setIsConnected(status.isConnected)
        if (status.isConnected && status.credentials) {
          setCredentials(status.credentials)
          fetchSlackData(status.credentials)
        }
      } catch (error) {
        console.error("Error checking connection:", error)
      }
    }

    checkConnection()
  }, [userId, orgId])

  const handleConnectClick = async () => {
    if (!userId || !orgId) {
      alert("Missing user or organization ID")
      return
    }

    try {
      setIsConnecting(true)
      const response = await axios.post(
        `/api/integrations/slack/authorize`,
        { userId, orgId },
        { headers: { "Content-Type": "application/json" } },
      )

      if (!response.data?.url) {
        throw new Error("Invalid authorization URL")
      }

      const newWindow = window.open(
        response.data.url,
        "Slack Authorization",
        "width=600,height=600,menubar=no,toolbar=no",
      )

      if (!newWindow) {
        throw new Error("Popup was blocked. Please allow popups and try again.")
      }

      // Listen for message from popup
      const messageHandler = (event: MessageEvent) => {
        if (event.data.type === "SLACK_AUTH_SUCCESS") {
          window.removeEventListener("message", messageHandler)
          handleAuthSuccess(event.data.org_id, event.data.user_id)
        } else if (event.data.type === "SLACK_AUTH_ERROR") {
          window.removeEventListener("message", messageHandler)
          handleAuthError(event.data.error)
        }
      }

      window.addEventListener("message", messageHandler)

      // Also poll for window close in case message isn't received
      const pollTimer = window.setInterval(() => {
        if (newWindow.closed) {
          window.clearInterval(pollTimer)
          window.removeEventListener("message", messageHandler)
          handleAuthSuccess(orgId, userId) // Assume success if window closed normally
        }
      }, 200)
    } catch (e) {
      setIsConnecting(false)
      const error = e as AxiosError<ErrorResponse>
      console.error("Authorization error:", error)
      alert(error.response?.data?.detail || "Failed to connect to Slack")
    }
  }

  const handleAuthSuccess = async (org_id: string, user_id: string) => {
    try {
      // Verify the connection immediately
      const status = await getIntegrationStatus("slack", user_id, org_id)
      if (status.isConnected) {
        setIsConnected(true)
        setCredentials(status.credentials)
        await fetchSlackData(status.credentials)
      } else {
        throw new Error("Connection verification failed")
      }
    } catch (error) {
      console.error("Error verifying connection:", error)
      handleAuthError(error instanceof Error ? error.message : "Failed to verify connection")
    } finally {
      setIsConnecting(false)
    }
  }

  const handleAuthError = (error: string) => {
    console.error("Authentication error:", error)
    alert(`Failed to connect to Slack: ${error}`)
    setIsConnecting(false)
  }

  const fetchSlackData = async (creds?: any) => {
    const credsToUse = creds || credentials
    if (!credsToUse) return

    try {
      setIsLoading(true)
      const data = await getIntegrationData("slack", credsToUse, userId, orgId)
      setSlackData(data)
    } catch (error) {
      console.error("Failed to fetch Slack data:", error)
      alert("Failed to fetch Slack data")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="mt-4">
      <div className="flex flex-col items-center gap-4">
        <Button
          variant={isConnected ? "outline" : "default"}
          onClick={isConnected ? undefined : handleConnectClick}
          disabled={isConnecting}
          className={isConnected ? "cursor-default opacity-100" : ""}
        >
          {isConnecting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Connecting...
            </>
          ) : isConnected ? (
            "Connected to Slack"
          ) : (
            "Connect to Slack"
          )}
        </Button>

        {isConnected && slackData && (
          <div className="w-full">
            <h4 className="font-medium mb-2">Team: {slackData.team.name}</h4>

            <h5 className="font-medium mb-2 mt-4">Channels</h5>
            <div className="space-y-2">
              {slackData.channels && slackData.channels.length > 0 ? (
                slackData.channels.map((channel) => (
                  <div key={channel.id} className="p-2 border rounded">
                    <p className="font-medium">#{channel.name}</p>
                    <p className="text-sm text-gray-500">
                      {channel.is_private ? "Private" : "Public"} • {channel.members} members
                    </p>
                    {channel.topic && <p className="text-sm text-gray-500">Topic: {channel.topic}</p>}
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500">No channels found</p>
              )}
            </div>

            <h5 className="font-medium mb-2 mt-4">Users</h5>
            <div className="space-y-2">
              {slackData.users && slackData.users.length > 0 ? (
                slackData.users.slice(0, 5).map((user) => (
                  <div key={user.id} className="p-2 border rounded">
                    <p className="font-medium">{user.real_name || user.name}</p>
                    {user.title && <p className="text-sm text-gray-500">{user.title}</p>}
                    {user.email && <p className="text-sm text-gray-500">{user.email}</p>}
                    {user.status_text && (
                      <p className="text-sm text-gray-500">
                        {user.status_emoji} {user.status_text}
                      </p>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500">No users found</p>
              )}
              {slackData.users && slackData.users.length > 5 && (
                <p className="text-center text-sm text-gray-500">+ {slackData.users.length - 5} more users</p>
              )}
            </div>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        )}
      </div>
    </div>
  )
}
