"use client"

import { useState, useEffect } from "react"
import { getIntegrationStatus, syncIntegrationData, getIntegrationData } from "@/app/lib/api-client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { NotionIntegration } from "@/app/components/integrations/notion-integration"
import { Lightbulb, RefreshCw } from "lucide-react"

interface NotionPage {
  id: string
  title: string
  lastEdited: string
}

interface NotionDatabase {
  id: string
  name: string
  items: number
}

import { NotionCredentials } from "@/app/components/integrations/types"

interface IntegrationParams {
  credentials?: NotionCredentials
  type?: "Notion" | "Airtable" | "Hubspot" | "Slack"
}

interface IntegrationData {
  isConnected: boolean
  status: string
  pages?: NotionPage[]
  databases?: NotionDatabase[]
  error?: string
  credentials?: Record<string, any>
}

export default function NotionIntegrationPage() {
  const [data, setData] = useState<IntegrationData | null>(null)
  const [integrationParams, setIntegrationParams] = useState<IntegrationParams | undefined>()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  const userId = "user123"
  const orgId = "org456"

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const status = await getIntegrationStatus("notion", userId, orgId)
        setIsConnected(status.isConnected)
        if (status.isConnected && status.credentials) {
          const processedCreds = status.credentials.credentials || status.credentials
          setIntegrationParams({
            credentials: {
              access_token: processedCreds.access_token,
              ...processedCreds
            },
            type: "Notion",
          })
          setData(status)
        }
      } catch (error) {
        console.error("Error checking connection:", error)
        setError(error instanceof Error ? error.message : "Failed to check connection status")
      }
    }
    checkConnection()
  }, [userId, orgId])

  const fetchData = async () => {
    if (!integrationParams?.credentials) return
    setIsLoading(true)
    setError(null)
    try {
      const status = await getIntegrationStatus("notion", userId, orgId)
      setIsConnected(status.isConnected)
      if (!status.isConnected) {
        throw new Error("Notion is not connected")
      }
      if (status.status !== "active") {
        await syncIntegrationData("notion", userId, orgId)
      }
      const notionData = await getIntegrationData(
        "notion", 
        integrationParams.credentials,
        userId, 
        orgId
      )
      setData({
        ...status,
        ...notionData
      })
    } catch (err) {
      console.error("Error fetching data:", err)
      setError(err instanceof Error ? err.message : "An unknown error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Notion Integration</h1>
          <p className="text-muted-foreground">Connect and manage your Notion workspace</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={fetchData} disabled={isLoading || !isConnected}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            <span className="sr-only">Refresh data</span>
          </Button>
        </div>
      </div>
    </div>
  )
}
