"use client"

import { useState } from "react"
import { getIntegrationStatus, syncIntegrationData } from "@/app/lib/api-client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { SlackIntegration } from "@/app/components/integrations/slack-integration"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
import { Hash, RefreshCw } from "lucide-react"

interface SlackChannel {
  id: string
  name: string
  visibility: boolean
  creation_time?: string
  type: 'channel'
}

interface IntegrationData {
  isConnected: boolean
  status: string
  workspace?: SlackChannel[]
  error?: string | null
}

export default function SlackIntegrationPage() {
  const [data, setData] = useState<IntegrationData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  // TODO: Replace with actual user and org data from auth context
  const userId = "user123"
  const orgId = "user123"

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const status = await getIntegrationStatus("slack", userId)
      setIsConnected(status.isConnected)

      // Type guard to ensure we're working with SlackChannel[]
      const isSlackChannel = (item: any): item is SlackChannel => {
        return item && typeof item === 'object' && item.type === 'channel';
      };

      const isSlackChannelArray = (items: any[]): items is SlackChannel[] => {
        return items.every(isSlackChannel);
      };

      if (!status.isConnected) {
        throw new Error("Slack is not connected");
      }

      const typedData: IntegrationData = {
        isConnected: status.isConnected,
        status: status.status,
        error: status.error,
        workspace: status.workspace && Array.isArray(status.workspace) && isSlackChannelArray(status.workspace)
          ? status.workspace
          : []
      };

      setData(typedData);

      if (status.status !== "active") {
        await syncIntegrationData("slack", userId);
        const updatedStatus = await getIntegrationStatus("slack", userId);

        const updatedTypedData: IntegrationData = {
          isConnected: updatedStatus.isConnected,
          status: updatedStatus.status,
          error: updatedStatus.error,
          workspace: updatedStatus.workspace && Array.isArray(updatedStatus.workspace) && isSlackChannelArray(updatedStatus.workspace)
            ? updatedStatus.workspace
            : []
        };

        setData(updatedTypedData);
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
              <Hash className="h-8 w-8 text-primary" />
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
                        <th className="p-2 text-left font-medium">Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.workspace?.map((channel: SlackChannel) => (
                        <tr key={channel.id} className="border-b">
                          <td className="p-2">#{channel.name}</td>
                          <td className="p-2">{channel.visibility ? 'Public' : 'Private'}</td>
                          <td className="p-2">{channel.creation_time ? new Date(channel.creation_time).toLocaleDateString() : 'N/A'}</td>
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
