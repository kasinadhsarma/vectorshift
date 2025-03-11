"use client"

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/app/components/ui/card"
import { IntegrationCard } from "@/app/components/integrations/integration-card"
import { BarChart3, FileSpreadsheet, MessageSquare, Lightbulb, RefreshCw } from "lucide-react"
import { useState } from "react"

interface IntegrationsOverviewProps {
  onSelectIntegration: (integration: string) => void
  activeIntegration: string | null
}

export function IntegrationsOverview({ onSelectIntegration, activeIntegration }: IntegrationsOverviewProps) {
  const [connectedIntegrations, setConnectedIntegrations] = useState<string[]>([])

  // This would typically come from your backend
  const mockStats = {
    totalIntegrations: 4,
    connectedIntegrations: connectedIntegrations.length,
    lastSyncTime: new Date().toLocaleString(),
  }

  const handleToggleConnection = (integration: string) => {
    if (connectedIntegrations.includes(integration)) {
      setConnectedIntegrations((prev) => prev.filter((i) => i !== integration))
    } else {
      setConnectedIntegrations((prev) => [...prev, integration])
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Integration Status</CardTitle>
          <RefreshCw className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {mockStats.connectedIntegrations}/{mockStats.totalIntegrations}
          </div>
          <p className="text-xs text-muted-foreground">Connected integrations</p>
        </CardContent>
        <CardFooter>
          <p className="text-xs text-muted-foreground">Last synced: {mockStats.lastSyncTime}</p>
        </CardFooter>
      </Card>

      <IntegrationCard
        title="Notion"
        description="Connect to your Notion workspace to import databases and pages."
        icon={<Lightbulb className="h-12 w-12 text-primary" />}
        isConnected={connectedIntegrations.includes("Notion")}
        isActive={activeIntegration === "Notion"}
        onConnect={() => handleToggleConnection("Notion")}
        onSelect={() => onSelectIntegration("Notion")}
      />

      <IntegrationCard
        title="Airtable"
        description="Import data from your Airtable bases and tables."
        icon={<FileSpreadsheet className="h-12 w-12 text-primary" />}
        isConnected={connectedIntegrations.includes("Airtable")}
        isActive={activeIntegration === "Airtable"}
        onConnect={() => handleToggleConnection("Airtable")}
        onSelect={() => onSelectIntegration("Airtable")}
      />

      <IntegrationCard
        title="Hubspot"
        description="Connect to Hubspot to manage your CRM data."
        icon={<BarChart3 className="h-12 w-12 text-primary" />}
        isConnected={connectedIntegrations.includes("Hubspot")}
        isActive={activeIntegration === "Hubspot"}
        onConnect={() => handleToggleConnection("Hubspot")}
        onSelect={() => onSelectIntegration("Hubspot")}
      />

      <IntegrationCard
        title="Slack"
        description="Connect to Slack to manage messages and channels."
        icon={<MessageSquare className="h-12 w-12 text-primary" />}
        isConnected={connectedIntegrations.includes("Slack")}
        isActive={activeIntegration === "Slack"}
        onConnect={() => handleToggleConnection("Slack")}
        onSelect={() => onSelectIntegration("Slack")}
      />
    </div>
  )
}

