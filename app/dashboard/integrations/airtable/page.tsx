"use client"

import { useState } from "react"
import { getIntegrationStatus, syncIntegrationData } from "@/app/lib/api-client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { AirtableIntegration } from "@/app/components/integrations/airtable-integration"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
import { Database, RefreshCw } from "lucide-react"

interface AirtableBase {
  id: string
  name: string
  url: string
  last_modified_time: string
}

interface IntegrationData {
  isConnected: boolean
  status: string
  workspace?: AirtableBase[]
  error?: string
}

export default function AirtableIntegrationPage() {
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
      const status = await getIntegrationStatus("airtable", userId)
      setIsConnected(status.isConnected)
      // Type guard to ensure we're working with AirtableBase[]
      const isAirtableBase = (item: any): item is AirtableBase => {
        return item && typeof item === 'object' && 'url' in item;
      };

      const isAirtableBaseArray = (items: any[]): items is AirtableBase[] => {
        return items.every(isAirtableBase);
      };

      if (!status.isConnected) {
        throw new Error("Airtable is not connected");
      }

      const typedData: IntegrationData = {
        isConnected: status.isConnected,
        status: status.status,
        error: status.error,
        workspace: status.workspace && Array.isArray(status.workspace) && isAirtableBaseArray(status.workspace) 
          ? status.workspace 
          : []
      };

      setData(typedData);

      if (status.status !== "active") {
        await syncIntegrationData("airtable", userId);
        const updatedStatus = await getIntegrationStatus("airtable", userId);
        
        const updatedTypedData: IntegrationData = {
          isConnected: updatedStatus.isConnected,
          status: updatedStatus.status,
          error: updatedStatus.error,
          workspace: updatedStatus.workspace && Array.isArray(updatedStatus.workspace) && isAirtableBaseArray(updatedStatus.workspace)
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
          <h1 className="text-3xl font-bold tracking-tight">Airtable Integration</h1>
          <p className="text-muted-foreground">Connect and manage your Airtable bases</p>
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
              <Database className="h-8 w-8 text-primary" />
            </div>
            <div>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>Manage your Airtable connection</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <AirtableIntegration
              userId={userId}
              orgId={orgId}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Airtable Data</CardTitle>
            <CardDescription>View and manage your Airtable data</CardDescription>
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
                    "Load Airtable Data"
                  )}
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-muted-foreground">Connect to Airtable to view your data</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {data && (
        <Tabs defaultValue="visualization" className="space-y-4">
          <TabsList>
            <TabsTrigger value="visualization">Visualization</TabsTrigger>
            <TabsTrigger value="bases">Bases</TabsTrigger>
          </TabsList>

          <TabsContent value="visualization">
            <DataVisualization data={data} />
          </TabsContent>

          <TabsContent value="bases">
            <Card>
              <CardHeader>
                <CardTitle>Airtable Bases</CardTitle>
                <CardDescription>Your Airtable bases</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Name</th>
                        <th className="p-2 text-left font-medium">Last Modified</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.workspace?.map((base: AirtableBase) => (
                        <tr key={base.id} className="border-b">
                          <td className="p-2">
                            <a href={base.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                              {base.name}
                            </a>
                          </td>
                          <td className="p-2">{new Date(base.last_modified_time).toLocaleDateString()}</td>
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
