"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { NotionIntegration } from "@/app/components/integrations/notion-integration"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
import { Lightbulb, RefreshCw } from "lucide-react"

export default function NotionIntegrationPage() {
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
        pages: [
          { id: "page1", title: "Project Overview", lastEdited: "2023-05-15" },
          { id: "page2", title: "Meeting Notes", lastEdited: "2023-05-20" },
          { id: "page3", title: "Product Roadmap", lastEdited: "2023-05-18" },
        ],
        databases: [
          { id: "db1", name: "Tasks", items: 24 },
          { id: "db2", name: "Projects", items: 8 },
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
          <h1 className="text-3xl font-bold tracking-tight">Notion Integration</h1>
          <p className="text-muted-foreground">Connect and manage your Notion workspace</p>
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
              <Lightbulb className="h-8 w-8 text-primary" />
            </div>
            <div>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>Manage your Notion connection</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <NotionIntegration
              user={user}
              org={org}
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
            {integrationParams?.credentials ? (
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
                      {data.pages.map((page: any) => (
                        <tr key={page.id} className="border-b">
                          <td className="p-2">{page.title}</td>
                          <td className="p-2">{page.lastEdited}</td>
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
                      {data.databases.map((db: any) => (
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

