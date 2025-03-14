"use client"

import { useState, useEffect } from "react"
<<<<<<< HEAD
import { getIntegrationStatus, syncIntegrationData, getIntegrationData } from "@/app/lib/api-client"
=======
import { getIntegrationStatus, getIntegrationData } from "@/app/lib/api-client"
>>>>>>> origin/main
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

  // TODO: Replace with actual user and org data from auth context
  const userId = "user123"
  const orgId = "org456"

<<<<<<< HEAD
  // Check connection status on mount
  useEffect(() => {
=======
  useEffect(() => {
    // Check connection status on load
>>>>>>> origin/main
    const checkConnection = async () => {
      try {
        const status = await getIntegrationStatus("notion", userId, orgId)
        setIsConnected(status.isConnected)
        if (status.isConnected && status.credentials) {
<<<<<<< HEAD
          // Store the credentials in the correct format
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
=======
          setIntegrationParams({
            credentials: status.credentials,
            type: "Notion",
          })
        }
      } catch (error) {
        console.error("Error checking connection:", error)
>>>>>>> origin/main
      }
    }

    checkConnection()
  }, [userId, orgId])

  const fetchData = async () => {
    if (!integrationParams?.credentials) return

    setIsLoading(true)
    setError(null)
    
    try {
<<<<<<< HEAD
      // First check/update connection status
      const status = await getIntegrationStatus("notion", userId, orgId)
      setIsConnected(status.isConnected)

      if (!status.isConnected) {
        throw new Error("Notion is not connected")
      }

      if (status.status !== "active") {
        await syncIntegrationData("notion", userId, orgId)
        const updatedStatus = await getIntegrationStatus("notion", userId, orgId)
        status.status = updatedStatus.status
      }

      // Then fetch the actual data if we have credentials
      if (integrationParams?.credentials) {
        console.log("Fetching Notion data with credentials:", {
          ...integrationParams.credentials,
          access_token: "[REDACTED]"
        })

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
      } else {
        setData(status)
=======
      const notionData = await getIntegrationData("notion", integrationParams.credentials, userId, orgId)

      // Process the data
      if (notionData.pages && notionData.databases) {
        setData({
          isConnected: true,
          status: "active",
          pages: notionData.pages,
          databases: notionData.databases,
          credentials: integrationParams.credentials,
        })
      } else {
        // If the data doesn't match expected format, try to process it
        const pages: NotionPage[] = []
        const databases: NotionDatabase[] = []

        if (Array.isArray(notionData)) {
          notionData.forEach((item: any) => {
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
                name: item.name,
                items: Number.parseInt(getParam("items")) || 0,
              })
            }
          })

          setData({
            isConnected: true,
            status: "active",
            pages,
            databases,
            credentials: integrationParams.credentials,
          })
        }
>>>>>>> origin/main
      }
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

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center gap-4">
            <div className="p-2 rounded-full bg-primary/10">
              <Lightbulb className="h-8 w-8 text-primary" />
            </div>
            <div>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>Manage your Notion connection</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <NotionIntegration
              user={userId}
              org={orgId}
              integrationParams={integrationParams}
              setIntegrationParams={setIntegrationParams}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notion Data</CardTitle>
            <CardDescription>View and manage your Notion data</CardDescription>
          </CardHeader>
          <CardContent>
            {isConnected ? (
              <div className="space-y-4">
                <Button onClick={fetchData} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Loading data...
                    </>
                  ) : (
                    "Load Notion Data"
                  )}
                </Button>
                {error && (
                  <p className="text-sm text-destructive">{error}</p>
                )}
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-muted-foreground">Connect to Notion to view your data</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {data && (
        <Tabs defaultValue="pages" className="space-y-4">
          <TabsList>
            <TabsTrigger value="pages">Pages</TabsTrigger>
            <TabsTrigger value="databases">Databases</TabsTrigger>
          </TabsList>

          <TabsContent value="pages">
            <Card>
              <CardHeader>
                <CardTitle>Notion Pages</CardTitle>
                <CardDescription>Your recent Notion pages</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Title</th>
                        <th className="p-2 text-left font-medium">Last Edited</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.pages?.map((page: NotionPage) => (
                        <tr key={page.id} className="border-b">
                          <td className="p-2">{page.title}</td>
                          <td className="p-2">{new Date(page.lastEdited).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="databases">
            <Card>
              <CardHeader>
                <CardTitle>Notion Databases</CardTitle>
                <CardDescription>Your Notion databases</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Name</th>
                        <th className="p-2 text-left font-medium">Items</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.databases?.map((db: NotionDatabase) => (
                        <tr key={db.id} className="border-b">
                          <td className="p-2">{db.name}</td>
                          <td className="p-2">{db.items}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}

