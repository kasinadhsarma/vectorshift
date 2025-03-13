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

interface IntegrationParameter {
  name: string
  value: string
}

interface IntegrationItem {
  id: string
  name: string
  type: string
  parameters: IntegrationParameter[]
}

interface AirtableBase {
  id: string
  name: string
  tables: number
}

interface AirtableTable {
  id: string
  name: string
  records: number
  baseId: string
}

interface AirtableData {
  bases: AirtableBase[]
  tables: AirtableTable[]
}

interface AirtableIntegrationProps {
  user: string
  org: string
  integrationParams?: IntegrationParams
  setIntegrationParams: (params: IntegrationParams) => void
}

export const AirtableIntegration = ({
  user,
  org,
  integrationParams,
  setIntegrationParams,
}: AirtableIntegrationProps) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [airtableData, setAirtableData] = useState<AirtableData | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleConnectClick = async () => {
    if (!user || !org) {
      alert("Missing user or organization ID")
      return
    }

    try {
      setIsConnecting(true)
      const response = await axios.post<AuthResponse>(
        `/api/integrations/airtable/authorize`,
        { userId: user, orgId: org },
        { headers: { "Content-Type": "application/json" } },
      )

      if (!response.data?.url) {
        throw new Error("Invalid authorization URL")
      }

      const newWindow = window.open(
        response.data.url,
        "Airtable Authorization",
        "width=600,height=600,menubar=no,toolbar=no",
      )

      if (!newWindow) {
        throw new Error("Popup was blocked. Please allow popups and try again.")
      }

      // Listen for message from popup
      const messageHandler = (event: MessageEvent) => {
        if (event.data.type === "AIRTABLE_AUTH_SUCCESS") {
          window.removeEventListener("message", messageHandler)
          handleAuthSuccess()
        } else if (event.data.type === "AIRTABLE_AUTH_ERROR") {
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
      alert(error.response?.data?.detail || "Failed to connect to Airtable")
    }
  }

  const handleAuthSuccess = async () => {
    try {
      // Verify the connection immediately
      const status = await getIntegrationStatus("airtable", user, org)
      if (status.isConnected) {
        setIsConnected(true)
        setIntegrationParams({
          credentials: status.credentials,
          type: "Airtable",
        })
        await fetchAirtableData(status.credentials)
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
    alert(`Failed to connect to Airtable: ${error}`)
    setIsConnecting(false)
  }

  const fetchAirtableData = async (credentials?: any) => {
    const creds = credentials || integrationParams?.credentials
    if (!creds) return

    try {
      setIsLoading(true)
      const items = await getIntegrationData("airtable", creds, user, org)

      // Process the items into bases and tables
      const basesMap: Record<string, AirtableBase> = {}
      const tables: AirtableTable[] = []

      items.forEach((item: IntegrationItem) => {
        const getParam = (name: string) => {
          const param = item.parameters.find((p: IntegrationParameter) => p.name === name)
          return param ? param.value : ""
        }

        if (item.type === "base") {
          basesMap[item.id] = {
            id: item.id,
            name: item.name,
            tables: Number.parseInt(getParam("tables")) || 0,
          }
        } else if (item.type === "table") {
          tables.push({
            id: item.id,
            name: item.name,
            records: Number.parseInt(getParam("records")) || 0,
            baseId: getParam("base_id"),
          })
        }
      })

      setAirtableData({
        bases: Object.values(basesMap),
        tables,
      })
    } catch (error) {
      console.error("Failed to fetch Airtable data:", error)
      alert("Failed to fetch Airtable data")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (integrationParams?.credentials) {
      setIsConnected(true)
      fetchAirtableData()
    }
  }, [integrationParams])

  const getTablesByBase = (baseId: string) => {
    return airtableData?.tables.filter((table) => table.baseId === baseId) || []
  }

  return (
    <div className="mt-4">
      <h3 className="mb-4">Airtable Integration</h3>
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
            "Connected to Airtable"
          ) : (
            "Connect to Airtable"
          )}
        </Button>

        {isConnected && airtableData && (
          <div className="w-full">
            {airtableData.bases.length > 0 ? (
              airtableData.bases.map((base) => (
                <div key={base.id} className="mb-6">
                  <h4 className="font-medium mb-2">{base.name}</h4>
                  <div className="space-y-2 pl-4">
                    {getTablesByBase(base.id).length > 0 ? (
                      getTablesByBase(base.id).map((table) => (
                        <div key={table.id} className="p-2 border rounded">
                          <p className="font-medium">{table.name}</p>
                          <p className="text-sm text-gray-500">{table.records} records</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-center text-gray-500">No tables found</p>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center text-gray-500">No bases found</p>
            )}
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
