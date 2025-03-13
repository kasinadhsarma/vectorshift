"use client"

import { useState, useEffect } from "react"
import axios, { type AxiosError } from "axios"
import { Button } from "@/app/components/ui/button"
import { Loader2 } from "lucide-react"
import { getIntegrationStatus, getIntegrationData } from "@/app/lib/api-client"

interface IntegrationParams {
  credentials?: Record<string, any>
  type?: string
}

interface AuthResponse {
  url: string
}

interface ErrorResponse {
  detail: string
}

interface NotionPage {
  id: string
  title: string
  lastEdited: string
}

interface NotionDatabase {
  id: string
  title: string
  items: number
}

interface NotionData {
  pages: NotionPage[]
  databases: NotionDatabase[]
}

interface NotionIntegrationProps {
  user: string
  org: string
  integrationParams?: IntegrationParams
  setIntegrationParams: (params: IntegrationParams) => void
}

export const NotionIntegration = ({ user, org, integrationParams, setIntegrationParams }: NotionIntegrationProps) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [notionData, setNotionData] = useState<NotionData | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Check if already connected
    const checkConnection = async () => {
      try {
        const status = await getIntegrationStatus("notion", user, org)
        setIsConnected(status.isConnected)
        if (status.isConnected && status.credentials) {
          setIntegrationParams({
            credentials: status.credentials,
            type: "Notion",
          })
        }
      } catch (error) {
        console.error("Error checking connection:", error)
      }
    }

    checkConnection()
  }, [user, org, setIntegrationParams])

  const handleConnectClick = async () => {
    if (!user || !org) {
      alert("Missing user or organization ID")
      return
    }

    try {
      setIsConnecting(true)
      const response = await axios.post<AuthResponse>(
        `/api/integrations/notion/authorize`,
        { userId: user, orgId: org },
        { headers: { "Content-Type": "application/json" } },
      )

      if (!response.data?.url) {
        throw new Error("Invalid authorization URL")
      }

      const newWindow = window.open(
        response.data.url,
        "Notion Authorization",
        "width=600,height=600,menubar=no,toolbar=no",
      )

      if (!newWindow) {
        throw new Error("Popup was blocked. Please allow popups and try again.")
      }

      // Listen for message from popup
      const messageHandler = (event: MessageEvent) => {
        if (event.data.type === "NOTION_AUTH_SUCCESS") {
          window.removeEventListener("message", messageHandler)
          handleAuthSuccess()
        } else if (event.data.type === "NOTION_AUTH_ERROR") {
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
          handleAuthSuccess() // Assume success if window closed normally
        }
      }, 200)
    } catch (e) {
      setIsConnecting(false)
      const error = e as AxiosError<ErrorResponse>
      console.error("Authorization error:", error)

      // Handle server connection errors
      if (error.code === 'ECONNREFUSED') {
        alert("Cannot connect to the backend server. Please ensure the backend server is running and try again.")
        return
      }

      // Log detailed error information for debugging
      console.log("Detailed error information:", {
        code: error.code,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message
      })

      // Show user-friendly error message
      const errorMessage = 
        error.response?.data?.detail ||
        (error.code === 'ECONNREFUSED' ? "Backend server is not running" : error.message) ||
        "Failed to connect to Notion"
      
      alert(errorMessage)
    }
  }

  const handleAuthSuccess = async () => {
    try {
      // Verify the connection immediately
      const status = await getIntegrationStatus("notion", user, org)
      if (status.isConnected) {
        setIsConnected(true)
        setIntegrationParams({
          credentials: status.credentials,
          type: "Notion",
        })
        await fetchNotionData(status.credentials)
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
    alert(`Failed to connect to Notion: ${error}`)
    setIsConnecting(false)
  }

  const fetchNotionData = async (credentials?: any) => {
    const creds = credentials || integrationParams?.credentials
    if (!creds) return

    try {
      setIsLoading(true)
      const data = await getIntegrationData("notion", creds, user, org)

      // Process the data
      if (data.pages && data.databases) {
        setNotionData({
          pages: data.pages,
          databases: data.databases,
        })
      } else {
        // If the data doesn't match expected format, try to process it
        const pages: NotionPage[] = []
        const databases: NotionDatabase[] = []

        if (Array.isArray(data)) {
          data.forEach((item: any) => {
            if (item.type === "page") {
              const getParam = (name: string) => {
                const param = item.parameters?.find((p: any) => p.name === name)
                return param ? param.value : ""
              }

              pages.push({
                id: item.id,
                title: item.name,
                lastEdited: getParam("last_edited") || new Date().toISOString(),
              })
            } else if (item.type === "database") {
              const getParam = (name: string) => {
                const param = item.parameters?.find((p: any) => p.name === name)
                return param ? param.value : ""
              }

              databases.push({
                id: item.id,
                title: item.name,
                items: Number.parseInt(getParam("items")) || 0,
              })
            }
          })

          setNotionData({ pages, databases })
        }
      }
    } catch (error) {
      console.error("Failed to fetch Notion data:", error)
      alert("Failed to fetch Notion data")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (integrationParams?.credentials) {
      setIsConnected(true)
      fetchNotionData()
    }
  }, [integrationParams])

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
            "Connected to Notion"
          ) : (
            "Connect to Notion"
          )}
        </Button>

        {isConnected && notionData && (
          <div className="w-full">
            <h4 className="font-medium mb-2">Pages</h4>
            <div className="space-y-2">
              {notionData.pages.length > 0 ? (
                notionData.pages.map((page) => (
                  <div key={page.id} className="p-2 border rounded">
                    <p className="font-medium">{page.title}</p>
                    <p className="text-sm text-gray-500">
                      Last edited: {new Date(page.lastEdited).toLocaleDateString()}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500">No pages found</p>
              )}
            </div>

            <h4 className="font-medium mb-2 mt-4">Databases</h4>
            <div className="space-y-2">
              {notionData.databases.length > 0 ? (
                notionData.databases.map((db) => (
                  <div key={db.id} className="p-2 border rounded">
                    <p className="font-medium">{db.title}</p>
                    <p className="text-sm text-gray-500">{db.items} items</p>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500">No databases found</p>
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
