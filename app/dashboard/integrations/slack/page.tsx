"use client"

import { useState } from "react"
import { getIntegrationStatus, syncIntegrationData } from "@/app/lib/api-client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { SlackIntegration } from "@/app/components/integrations/slack-integration"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
import { MessageSquare, RefreshCw } from "lucide-react"

export default function SlackIntegrationPage() {
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  // TODO: Replace with actual user and org data from auth context
  const userId = "user123"
  const orgId = "org456"

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const status = await getIntegrationStatus("slack", userId)
      setIsConnected(status.isConnected)
      
      if (!status.isConnected) {
        throw new Error("Slack is not connected")
      }

      if (status.status === "active") {
        setData(status.workspace)
      } else {
        await syncIntegrationData("slack", userId)
        const updatedStatus = await getIntegrationStatus("slack", userId)
        setData(updatedStatus.workspace)
      }
    } catch (error) {
      console.error("Error fetching data:", error)
      setError(error.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Slack Integration</h1>
          <p className="text-muted-foreground">Connect and manage your Slack workspace</p>
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
              <MessageSquare className="h-8 w-8 text-primary" />
            </div>
            <div>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>Manage your Slack connection</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <SlackIntegration
              userId={userId}
              orgId={orgId}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Slack Data</CardTitle>
            <CardDescription>View and manage your Slack data</CardDescription>
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
                    "Load Slack Data"
                  )}
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-muted-foreground">Connect to Slack to view your data</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {data && (
        <Tabs defaultValue="visualization" className="space-y-4">
          <TabsList>
            <TabsTrigger value="visualization">Visualization</TabsTrigger>
            <TabsTrigger value="channels">Channels</TabsTrigger>
            <TabsTrigger value="messages">Messages</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
          </TabsList>

          <TabsContent value="visualization">
            <DataVisualization data={data} />
          </TabsContent>

          <TabsContent value="channels">
            <Card>
              <CardHeader>
                <CardTitle>Slack Channels</CardTitle>
                <CardDescription>Your Slack channels</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Name</th>
                        <th className="p-2 text-left font-medium">Visibility</th>
                        <th className="p-2 text-left font-medium">Creation Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.channels?.map((channel: any) => (
                        <tr key={channel.id} className="border-b">
                          <td className="p-2">#{channel.name}</td>
                          <td className="p-2">{channel.visibility ? "Public" : "Private"}</td>
                          <td className="p-2">{new Date(parseInt(channel.creation_time) * 1000).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="messages">
            <Card>
              <CardHeader>
                <CardTitle>Recent Messages</CardTitle>
                <CardDescription>Recent messages from your Slack workspace</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-4">
                  <p className="text-muted-foreground">Message data will be displayed here when available</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users">
            <Card>
              <CardHeader>
                <CardTitle>Slack Users</CardTitle>
                <CardDescription>Users in your Slack workspace</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-4">
                  <p className="text-muted-foreground">User data will be displayed here when available</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
