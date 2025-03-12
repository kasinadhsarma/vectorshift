"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import { Progress } from "@/app/components/ui/progress"
import { BarChart3, FileSpreadsheet, Lightbulb, MessageSquare, Plus, RefreshCw, Settings, Zap } from "lucide-react"
import Link from "next/link"
import { IntegrationsOverview } from "./integrations-overview"
import { IntegrationForm } from "../integrations/integration-form"
import { DataVisualization } from "./data-visualization"

interface DashboardContentProps {
  userId: string
  isLoading: boolean
  userData: {
    integrations: {
      total: number
      active: number
      lastMonthTotal: number
      lastMonthActive: number
    }
    dataSyncs: {
      total: number
      lastWeekTotal: number
    }
    usage: number
    activeIntegrations: Array<{
      name: string
      status: string
      lastSync: string
      details: string
    }>
  }
}

export function DashboardContent({ userId, userData }: DashboardContentProps) {
  const [activeIntegration, setActiveIntegration] = useState<string | null>(null)
  const [integrationData, setIntegrationData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

  const refreshData = async () => {
    setIsLoading(true)
    // Implement actual refresh logic here
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setIsLoading(false)
  }

  return (
    <div className="space-y-6" aria-busy={isLoading}>
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

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Integrations</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userData.integrations.total}</div>
            <p className="text-xs text-muted-foreground">
              {userData.integrations.total - userData.integrations.lastMonthTotal >= 0 ? "+" : ""}
              {userData.integrations.total - userData.integrations.lastMonthTotal} from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Connections</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userData.integrations.active}</div>
            <p className="text-xs text-muted-foreground">
              {userData.integrations.active - userData.integrations.lastMonthActive >= 0 ? "+" : ""}
              {userData.integrations.active - userData.integrations.lastMonthActive} from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Syncs</CardTitle>
            <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userData.dataSyncs.total}</div>
            <p className="text-xs text-muted-foreground">
              +{userData.dataSyncs.total - userData.dataSyncs.lastWeekTotal} from last week
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Usage</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userData.usage}%</div>
            <Progress value={userData.usage} className="mt-2" />
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
              {!isLoading && userData.activeIntegrations.length > 0 ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {userData.activeIntegrations.map((integration) => (
                  <div key={integration.name} className="flex flex-col items-center justify-between rounded-lg border p-4">
                    <div className="flex w-full items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <IntegrationIcon name={integration.name} />
                        <span className="font-medium">{integration.name}</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {integration.status}
                      </Badge>
                    </div>
                    <div className="mt-4 w-full">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Last sync: {integration.lastSync}</span>
                        <span>{integration.details}</span>
                      </div>
                      <Progress value={75} className="mt-2 h-1" />
                    </div>
                    <div className="mt-4 flex w-full justify-end">
                      <Link href={`/dashboard/${userId}/integrations/${integration.name.toLowerCase()}`}>
                        <Button variant="ghost" size="sm">
                          Manage
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No active integrations. Add one to get started.</p>
                </div>
              )}
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

function IntegrationIcon({ name }: { name: string }) {
  switch (name.toLowerCase()) {
    case "notion":
      return <Lightbulb className="h-5 w-5 text-primary" />
    case "airtable":
      return <FileSpreadsheet className="h-5 w-5 text-primary" />
    case "slack":
      return <MessageSquare className="h-5 w-5 text-primary" />
    default:
      return <Settings className="h-5 w-5 text-primary" />
  }
}
