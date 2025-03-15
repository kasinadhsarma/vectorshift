"use client"

import { useState } from "react"
import { getIntegrationStatus, syncIntegrationData } from "@/app/lib/api-client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { AirtableIntegration } from "@/app/components/integrations/airtable-integration"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
import { FileSpreadsheet, RefreshCw } from "lucide-react"

export default function AirtableIntegrationPage() {
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
      const status = await getIntegrationStatus("airtable", userId)
      setIsConnected(status.isConnected)
      
      if (!status.isConnected) {
        throw new Error("Airtable is not connected")
      }

      if (status.status === "active") {
        setData(status)
      } else {
        await syncIntegrationData("airtable", userId)
        const updatedStatus = await getIntegrationStatus("airtable", userId)
        setData(updatedStatus)
      }
    } catch (error) {
      console.error("Error fetching data:", error)
      setError(error instanceof Error ? error.message : 'An unknown error occurred')
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
              <FileSpreadsheet className="h-8 w-8 text-primary" />
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
            <TabsTrigger value="tables">Tables</TabsTrigger>
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
                        <th className="p-2 text-left font-medium">Tables</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.bases.map((base: any) => (
                        <tr key={base.id} className="border-b">
                          <td className="p-2">{base.name}</td>
                          <td className="p-2">{base.tables}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tables">
            <Card>
              <CardHeader>
                <CardTitle>Airtable Tables</CardTitle>
                <CardDescription>Your Airtable tables</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Name</th>
                        <th className="p-2 text-left font-medium">Records</th>
                        <th className="p-2 text-left font-medium">Base</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.tables.map((table: any) => (
                        <tr key={table.id} className="border-b">
                          <td className="p-2">{table.name}</td>
                          <td className="p-2">{table.records}</td>
                          <td className="p-2">{data.bases.find((base: any) => base.id === table.baseId)?.name}</td>
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
