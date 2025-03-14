"use client"

import { useState } from "react"
import { getIntegrationStatus, syncIntegrationData } from "@/app/lib/api-client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { NotionIntegration } from "@/app/components/integrations/notion-integration"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
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

interface IntegrationParams {
  credentials?: Record<string, any>
  type?: string
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

<<<<<<< Updated upstream
  const fetchData = async () => {
=======
  useEffect(() => {
    // Check connection status on load
    const checkConnection = async () => {
      try {
        const status = await getIntegrationStatus("notion", userId, orgId)
        setIsConnected(status.isConnected)
        if (status.isConnected && status.credentials) {
          // Store the credentials in the correct format
          const processedCreds = status.credentials.credentials || status.credentials
          setIntegrationParams({
            credentials: {
              access_token: processedCreds.access_token,
              ...processedCreds
            },
            type: "Notion",
          })
        }
      } catch (error) {
        console.error("Error checking connection:", error)
      }
    }

    checkConnection()
  }, [userId, orgId])

  const fetchData = async () => {
    if (!integrationParams?.credentials) {
      console.error("No credentials available")
      setError("No credentials available")
      return
    }

>>>>>>> Stashed changes
    setIsLoading(true)
    setError(null)
    
    try {
<<<<<<< Updated upstream
      const status = await getIntegrationStatus("notion", userId, orgId)
      setIsConnected(status.isConnected)
      setData(status)
      
      if (!status.isConnected) {
        throw new Error("Notion is not connected")
      }
=======
      console.log("Fetching Notion data with credentials:", {
        ...integrationParams.credentials,
        access_token: integrationParams.credentials.access_token ? "[REDACTED]" : "MISSING"
      })

      const notionData = await getIntegrationData(
        "notion", 
        integrationParams.credentials,
        userId, 
        orgId
      )
>>>>>>> Stashed changes

      if (status.status !== "active") {
        await syncIntegrationData("notion", userId, orgId)
        const updatedStatus = await getIntegrationStatus("notion", userId, orgId)
        setData(updatedStatus)
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
          <Button
            variant="outline"
            size="icon"
            onClick={fetchData}
            disabled={isLoading || !isConnected}
          >
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
        <Tabs defaultValue="visualization" className="space-y-4">
          <TabsList>
            <TabsTrigger value="visualization">Visualization</TabsTrigger>
            <TabsTrigger value="pages">Pages</TabsTrigger>
            <TabsTrigger value="databases">Databases</TabsTrigger>
          </TabsList>

          <TabsContent value="visualization">
            <DataVisualization data={data} />
          </TabsContent>

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
