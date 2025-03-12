"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import {
  authorizeIntegration,
  getIntegrationStatus,
  disconnectIntegration,
  getNotionPages,
  syncIntegrationData,
  IntegrationStatus, // Import IntegrationStatus
} from "@/app/lib/api-client"

interface NotionIntegrationProps {
  userId: string
  orgId: string
}

interface NotionWorkspace {
  id: string
  name: string
  pages: Array<{
    id: string
    title: string
    lastEdited: string
  }>
}

export function NotionIntegration({ userId, orgId }: NotionIntegrationProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [workspace, setWorkspace] = useState<NotionWorkspace | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status: IntegrationStatus = await getIntegrationStatus('notion', userId) //Type it properly
        setIsConnected(status.isConnected)

        if (status.isConnected && status.credentials?.workspaceId) {
          const pages = await getNotionPages(status.credentials.workspaceId)
          setWorkspace({
            id: status.credentials.workspaceId || '',
            name: 'Notion Workspace',
            pages: pages.map(page => ({
              id: page.id,
              title: page.title,
              lastEdited: page.last_edited_time
            }))
          })
        }

        if (status.error) {
          setError(status.error)
        }
      } catch (error) {
        console.error('Error checking Notion status:', error)
        setError('Failed to check integration status')
      } finally {
        setIsLoading(false)
      }
    }

    checkStatus()
  }, [userId])

  const handleConnect = async () => {
    try {
      setIsConnecting(true)
      setError(null)

      // Get authorization URL from backend
      const authUrl = await authorizeIntegration('notion', userId, orgId)

      // Open Notion OAuth page in a new window
      const width = 600
      const height = 700
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2

      const authWindow = window.open(
        authUrl,
        'Notion Authorization',
        `width=${width},height=${height},left=${left},top=${top}`
      )

      // Listen for the OAuth callback
      window.addEventListener('message', async (event) => {
        if (event.data.type === 'notion-oauth-callback') {
          if (event.data.success) {
            setIsConnected(true)
            toast({
              title: "Connected successfully",
              description: "Successfully connected to Notion",
            })

            // Load initial workspace data
            const pages = await getNotionPages(event.data.workspaceId)
            setWorkspace({
              id: event.data.workspaceId,
              name: 'Notion Workspace',
              pages: pages.map(page => ({
                id: page.id,
                title: page.title,
                lastEdited: page.last_edited_time
              }))
            })
          } else {
            setError('Failed to connect to Notion')
            toast({
              title: "Connection failed",
              description: event.data.error || "Failed to connect to Notion",
              variant: "destructive",
            })
          }
          authWindow?.close()
        }
      })
    } catch (error) {
      console.error('Error connecting to Notion:', error)
      setError('Failed to initiate Notion connection')
      toast({
        title: "Connection failed",
        description: "Failed to connect to Notion",
        variant: "destructive",
      })
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await disconnectIntegration('notion', userId)
      setIsConnected(false)
      setWorkspace(null)
      toast({
        title: "Disconnected",
        description: "Successfully disconnected from Notion",
      })
    } catch (error) {
      console.error('Error disconnecting from Notion:', error)
      toast({
        title: "Error",
        description: "Failed to disconnect from Notion",
        variant: "destructive",
      })
    }
  }

  const handleSync = async () => {
    try {
      setIsSyncing(true)
      await syncIntegrationData('notion', userId)

      // Refresh pages data
      if (workspace) {
        const pages = await getNotionPages(workspace.id)
        setWorkspace({
          ...workspace,
          pages: pages.map(page => ({
            id: page.id,
            title: page.title,
            lastEdited: page.last_edited_time
          }))
        })
      }

      toast({
        title: "Sync complete",
        description: "Successfully synced Notion data",
      })
    } catch (error) {
      console.error('Error syncing Notion data:', error)
      toast({
        title: "Sync failed",
        description: "Failed to sync Notion data",
        variant: "destructive",
      })
    } finally {
      setIsSyncing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-6">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-medium">Notion Integration</h3>
        <p className="text-sm text-muted-foreground">
          Connect to your Notion workspace to access and sync your pages and databases.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-md">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      <div className="flex gap-4">
        <Button
          onClick={isConnected ? handleDisconnect : handleConnect}
          disabled={isConnecting || isSyncing}
          variant={isConnected ? "outline" : "default"}
        >
          {isConnected ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Disconnect Notion
            </>
          ) : isConnecting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Connecting...
            </>
          ) : (
            "Connect to Notion"
          )}
        </Button>

        {isConnected && (
          <Button
            onClick={handleSync}
            disabled={isSyncing}
            variant="outline"
          >
            {isSyncing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Syncing...
              </>
            ) : (
              "Sync Data"
            )}
          </Button>
        )}
      </div>

      {workspace && workspace.pages.length > 0 && (
        <div className="border rounded-lg p-4">
          <h4 className="font-medium mb-2">Connected Pages</h4>
          <div className="space-y-2">
            {workspace.pages.map(page => (
              <div key={page.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                <span>{page.title}</span>
                <span className="text-muted-foreground">
                  Last edited: {new Date(page.lastEdited).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
