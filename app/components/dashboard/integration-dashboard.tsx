"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { IntegrationsOverview } from "@/app/components/dashboard/integrations-overview"
import { IntegrationForm } from "@/app/components/integrations/integration-form"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
import { ModeToggle } from "@/app/components/theme/mode-toggle"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"

export function IntegrationDashboard() {
  const [activeIntegration, setActiveIntegration] = useState<string | null>(null)
  const [integrationData, setIntegrationData] = useState<any>(null)

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Integrations Dashboard</h1>
          <p className="text-muted-foreground">Manage and visualize your third-party integrations</p>
        </div>
        <ModeToggle />
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="connect">Connect</TabsTrigger>
          <TabsTrigger value="visualize">Visualize Data</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
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

