"use client"

import { useState, useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import { Progress } from "@/app/components/ui/progress"
import { BarChart3, FileSpreadsheet, Lightbulb, MessageSquare, Plus, RefreshCw, Settings, Zap } from 'lucide-react'
import Link from "next/link"
import { useSidebar } from "@/app/components/ui/sidebar"

// Import these components from your project or create them
import { IntegrationsOverview } from "@/app/components/dashboard/integrations-overview"
import { IntegrationForm } from "@/app/components/integrations/integration-form"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"

export default function DashboardPage() {
  const [activeIntegration, setActiveIntegration] = useState<string | null>(null)
  const [integrationData, setIntegrationData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { state } = useSidebar()

  const refreshData = async () => {
    setIsLoading(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setIsLoading(false)
  }

  // Adjust layout when sidebar state changes
  useEffect(() => {
    // Force a re-render when sidebar state changes to ensure proper layout
    const handleResize = () => {
      window.dispatchEvent(new Event("resize"))
    }

    if (state === "expanded" || state === "collapsed") {
      setTimeout(handleResize, 300) // Wait for transition to complete
    }
  }, [state])

  return (
    <div className={`space-y-6 transition-all duration-300 w-full max-w-full overflow-x-hidden px-1 ${state === "collapsed" ? "md:pl-2" : ""}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Integrations Dashboard</h1>
          <p className="text-muted-foreground">Manage and visualize your third-party integrations</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={refreshData} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Integration
          </Button>
        </div>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Integrations</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4</div>
            <p className="text-xs text-muted-foreground">+2 from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Connections</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">+1 from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Syncs</CardTitle>
            <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">28</div>
            <p className="text-xs text-muted-foreground">+8 from last week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Usage</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">65%</div>
            <Progress value={65} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 lg:w-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="connect">Connect</TabsTrigger>
          <TabsTrigger value="visualize">Visualize Data</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Integrations</CardTitle>
              <CardDescription>Manage your connected services</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <div className="flex flex-col items-center justify-between rounded-lg border p-4">
                  <div className="flex w-full items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Lightbulb className="h-5 w-5 text-primary" />
                      <span className="font-medium">Notion</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Connected
                    </Badge>
                  </div>
                  <div className="mt-4 w-full">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Last sync: 2 hours ago</span>
                      <span>3 workspaces</span>
                    </div>
                    <Progress value={75} className="mt-2 h-1" />
                  </div>
                  <div className="mt-4 flex w-full justify-end">
                    <Link href="/dashboard/integrations/notion">
                      <Button variant="ghost" size="sm">
                        Manage
                      </Button>
                    </Link>
                  </div>
                </div>
                <div className="flex flex-col items-center justify-between rounded-lg border p-4">
                  <div className="flex w-full items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <FileSpreadsheet className="h-5 w-5 text-primary" />
                      <span className="font-medium">Airtable</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Connected
                    </Badge>
                  </div>
                  <div className="mt-4 w-full">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Last sync: 5 hours ago</span>
                      <span>2 bases</span>
                    </div>
                    <Progress value={60} className="mt-2 h-1" />
                  </div>
                  <div className="mt-4 flex w-full justify-end">
                    <Link href="/dashboard/integrations/airtable">
                      <Button variant="ghost" size="sm">
                        Manage
                      </Button>
                    </Link>
                  </div>
                </div>
                <div className="flex flex-col items-center justify-between rounded-lg border p-4">
                  <div className="flex w-full items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <MessageSquare className="h-5 w-5 text-primary" />
                      <span className="font-medium">Slack</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Connected
                    </Badge>
                  </div>
                  <div className="mt-4 w-full">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Last sync: 1 day ago</span>
                      <span>5 channels</span>
                    </div>
                    <Progress value={40} className="mt-2 h-1" />
                  </div>
                  <div className="mt-4 flex w-full justify-end">
                    <Link href="/dashboard/integrations/slack">
                      <Button variant="ghost" size="sm">
                        Manage
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">
                <Plus className="mr-2 h-4 w-4" />
                Add New Integration
              </Button>
            </CardFooter>
          </Card>

          <IntegrationsOverview onSelectIntegration={setActiveIntegration} activeIntegration={activeIntegration} />
        </TabsContent>

        <TabsContent value="connect" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Connect Integration</CardTitle>
              <CardDescription>Connect to your favorite services to import and manage data</CardDescription>
            </CardHeader>
            <CardContent>
              <IntegrationForm onIntegrationData={(data) => setIntegrationData(data)} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="visualize" className="space-y-4">
          <DataVisualization data={integrationData} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
