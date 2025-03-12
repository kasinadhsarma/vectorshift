"use client"

import { useState } from "react"
import { getIntegrationStatus, syncIntegrationData } from "@/app/lib/api-client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { HubspotIntegration } from "@/app/components/integrations/hubspot-integration"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
import { BarChart3, RefreshCw } from "lucide-react"

export default function HubspotIntegrationPage() {
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
      const status = await getIntegrationStatus("hubspot", userId)
      setIsConnected(status.isConnected)
      
      if (!status.isConnected) {
        throw new Error("HubSpot is not connected")
      }

      if (status.status === "active") {
        setData(status.workspace)
      } else {
        await syncIntegrationData("hubspot", userId)
        const updatedStatus = await getIntegrationStatus("hubspot", userId)
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
          <h1 className="text-3xl font-bold tracking-tight">Hubspot Integration</h1>
          <p className="text-muted-foreground">Connect and manage your Hubspot CRM data</p>
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
              <BarChart3 className="h-8 w-8 text-primary" />
            </div>
            <div>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>Manage your Hubspot connection</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <HubspotIntegration
              userId={userId}
              orgId={orgId}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Hubspot Data</CardTitle>
            <CardDescription>View and manage your Hubspot data</CardDescription>
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
                    "Load Hubspot Data"
                  )}
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-muted-foreground">Connect to Hubspot to view your data</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {data && (
        <Tabs defaultValue="visualization" className="space-y-4">
          <TabsList>
            <TabsTrigger value="visualization">Visualization</TabsTrigger>
            <TabsTrigger value="contacts">Contacts</TabsTrigger>
            <TabsTrigger value="companies">Companies</TabsTrigger>
            <TabsTrigger value="deals">Deals</TabsTrigger>
          </TabsList>

          <TabsContent value="visualization">
            <DataVisualization data={data} />
          </TabsContent>

          <TabsContent value="contacts">
            <Card>
              <CardHeader>
                <CardTitle>Hubspot Contacts</CardTitle>
                <CardDescription>Your Hubspot contacts</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Name</th>
                        <th className="p-2 text-left font-medium">Email</th>
                        <th className="p-2 text-left font-medium">Company</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.contacts?.map((contact: any) => (
                        <tr key={contact.id} className="border-b">
                          <td className="p-2">{contact.name}</td>
                          <td className="p-2">{contact.email || "N/A"}</td>
                          <td className="p-2">{contact.company || "N/A"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="companies">
            <Card>
              <CardHeader>
                <CardTitle>Hubspot Companies</CardTitle>
                <CardDescription>Your Hubspot companies</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-4">
                  <p className="text-muted-foreground">Company data will be displayed here when available</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="deals">
            <Card>
              <CardHeader>
                <CardTitle>Hubspot Deals</CardTitle>
                <CardDescription>Your Hubspot deals</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-4">
                  <p className="text-muted-foreground">Deal data will be displayed here when available</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
