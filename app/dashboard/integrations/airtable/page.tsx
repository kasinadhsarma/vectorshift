"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AirtableIntegration } from "@/components/integrations/airtable-integration"
import { DataVisualization } from "@/components/dashboard/data-visualization"
import { FileSpreadsheet, RefreshCw } from "lucide-react"

export default function AirtableIntegrationPage() {
  const [integrationParams, setIntegrationParams] = useState<any>({})
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Mock user and org data
  const user = "user123"
  const org = "org456"

  const fetchData = async () => {
    setIsLoading(true)
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Mock data
      const mockData = {
        bases: [
          { id: "base1", name: "Project Tracker", tables: 3 },
          { id: "base2", name: "Marketing Calendar", tables: 2 },
        ],
        tables: [
          { id: "table1", name: "Tasks", records: 45, baseId: "base1" },
          { id: "table2", name: "Team Members", records: 12, baseId: "base1" },
          { id: "table3", name: "Projects", records: 8, baseId: "base1" },
          { id: "table4", name: "Campaigns", records: 15, baseId: "base2" },
          { id: "table5", name: "Content Calendar", records: 30, baseId: "base2" },
        ],
      }

      setData(mockData)
    } catch (error) {
      console.error("Error fetching data:", error)
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
            disabled={isLoading || !integrationParams?.credentials}
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
              user={user}
              org={org}
              integrationParams={integrationParams}
              setIntegrationParams={setIntegrationParams}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Airtable Data</CardTitle>
            <CardDescription>View and manage your Airtable data</CardDescription>
          </CardHeader>
          <CardContent>
            {integrationParams?.credentials ? (
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

