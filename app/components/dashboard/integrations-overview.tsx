"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { Badge } from "@/app/components/ui/badge"
import { Button } from "@/app/components/ui/button"
import { BarChart3, FileSpreadsheet, Lightbulb, MessageSquare } from "lucide-react"
import { useToast } from "@/app/components/ui/use-toast"
import Link from "next/link"
import { getIntegrationStatus, syncIntegrationData } from "@/app/lib/api-client"
import { type } from "os"

interface Integration {
  id: string
  name: string
  icon: React.ReactNode
  status: 'active' | 'inactive' | 'error'
  lastSync?: string
  error?: string
}

const INTEGRATIONS: Omit<Integration, "status" | "lastSync" | "error">[] = [
  {
    id: 'notion',
    name: 'Notion',
    icon: <Lightbulb className="h-5 w-5 text-primary" />,
  },
  {
    id: 'airtable',
    name: 'Airtable',
    icon: <FileSpreadsheet className="h-5 w-5 text-primary" />,
  },
  {
    id: 'hubspot',
    name: 'Hubspot',
    icon: <BarChart3 className="h-5 w-5 text-primary" />,
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: <MessageSquare className="h-5 w-5 text-primary" />,
  },
];

interface IntegrationsOverviewProps {
  onSelectIntegration: (integration: string | null) => void
  activeIntegration: string | null
}

export function IntegrationsOverview({ onSelectIntegration, activeIntegration }: IntegrationsOverviewProps) {
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    const loadIntegrationStatuses = async () => {
      try {
        const userId = localStorage.getItem('userId')
        if (!userId) return

        const updatedIntegrations: Integration[] = await Promise.all(
          INTEGRATIONS.map(async (integration) => {
            try {
              const status = await getIntegrationStatus(integration.id, userId)
              return {
                ...integration,
                status: ['active', 'inactive', 'error'].includes(status.status) ? (status.status as 'active' | 'inactive' | 'error') : 'error',
                lastSync: status.lastSync,
                error: status.error,
              }
            } catch (error) {
              console.error(`Error fetching ${integration.name} status:`, error)
              return {
                ...integration,
                status: 'error',
                error: 'Failed to fetch status',
              }
            }
          })
        )

        setIntegrations(updatedIntegrations)
      } catch (error) {
        console.error('Error loading integration statuses:', error)
        toast({
          title: "Error",
          description: "Failed to load integration statuses",
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    loadIntegrationStatuses()
  }, [toast])

  const handleSync = async (integrationId: string) => {
    try {
      const userId = localStorage.getItem('userId')
      if (!userId) throw new Error('User ID not found')

      await syncIntegrationData(integrationId, userId)
      
      // Refresh the status after sync
      const status = await getIntegrationStatus(integrationId, userId)
      setIntegrations(current =>
        current.map(integration =>
          integration.id === integrationId
            ? { ...integration, status: status.status, lastSync: status.lastSync, error: status.error }
            : integration
        )
      )

      toast({
        title: "Success",
        description: "Integration synced successfully",
      })
    } catch (error) {
      console.error('Error syncing integration:', error)
      toast({
        title: "Error",
        description: "Failed to sync integration",
        variant: "destructive",
      })
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <Badge
            variant="outline"
            className="bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
          >
            Healthy
          </Badge>
        )
      case 'inactive':
        return (
          <Badge
            variant="outline"
            className="bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400"
          >
            Inactive
          </Badge>
        )
      case 'error':
        return (
          <Badge
            variant="outline"
            className="bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400"
          >
            Issues
          </Badge>
        )
      default:
        return null
    }
  }

  const getActionButton = (integration: Integration) => {
    switch (integration.status) {
      case 'active':
        return (
          <Button variant="ghost" size="sm" onClick={() => handleSync(integration.id)}>
            Sync
          </Button>
        )
      case 'inactive':
        return (
          <Link href={`/dashboard/integrations/${integration.id}`}>
            <Button variant="ghost" size="sm">
              Connect
            </Button>
          </Link>
        )
      case 'error':
        return (
          <Link href={`/dashboard/integrations/${integration.id}`}>
            <Button variant="ghost" size="sm">
              Fix
            </Button>
          </Link>
        )
      default:
        return null
    }
  }

  const renderIntegrationItem = (integration: Integration) => (
    <div key={integration.id} className="flex items-center justify-between rounded-lg border p-4">
      <div className="flex items-center gap-4">
        <div className="rounded-full bg-primary/10 p-2">
          {integration.icon}
        </div>
        <div>
          <div className="font-medium">{integration.name}</div>
          <div className="text-sm text-muted-foreground">
            {integration.lastSync 
              ? `Last synced ${new Date(integration.lastSync).toLocaleTimeString()}`
              : 'Not connected'
            }
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {getStatusBadge(integration.status)}
        {getActionButton(integration)}
      </div>
    </div>
  )

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Integration Health</CardTitle>
          <CardDescription>Loading integrations...</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Integration Health</CardTitle>
        <CardDescription>Monitor the status of your integrations</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="all">
          <TabsList className="mb-4">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="issues">Issues</TabsTrigger>
          </TabsList>
          <TabsContent value="all" className="space-y-4">
            {integrations.map(renderIntegrationItem)}
          </TabsContent>
          <TabsContent value="active" className="space-y-4">
            {integrations
              .filter(i => i.status === 'active')
              .map(renderIntegrationItem)}
          </TabsContent>
          <TabsContent value="issues" className="space-y-4">
            {integrations
              .filter(i => i.status === 'error')
              .map(renderIntegrationItem)}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
