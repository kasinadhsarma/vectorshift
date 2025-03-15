"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { useToast } from "@/hooks/use-toast"
import { Badge } from "@/app/components/ui/badge"
import { Loader2, CheckCircle2, AlertCircle, Lock, Unlock } from "lucide-react"
import {
  authorizeIntegration,
  getIntegrationStatus,
  disconnectIntegration,
  getSlackChannels,
  syncIntegrationData,
  IntegrationStatus,
  SlackChannel,
} from "@/app/lib/api-client"

interface SlackIntegrationProps {
  userId: string
  orgId: string
}

interface SlackWorkspace {
  id: string
  name: string
  channels: SlackChannel[]
}

export function SlackIntegration({ userId, orgId }: SlackIntegrationProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [workspace, setWorkspace] = useState<SlackWorkspace | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status: IntegrationStatus = await getIntegrationStatus('slack', userId)
        setIsConnected(status.isConnected)

        if (status.isConnected && status.credentials?.workspaceId) {
          const channels = await getSlackChannels(status.credentials.workspaceId)
          setWorkspace({
            id: status.credentials.workspaceId,
            name: 'Slack Workspace',
            channels
          })
        }

        if (status.error) {
          setError(status.error)
        }
      } catch (error) {
        console.error('Error checking Slack status:', error)
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

      const authUrl = await authorizeIntegration('slack', userId, orgId)

      const width = 600
      const height = 700
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2

      const authWindow = window.open(
        authUrl,
        'Slack Authorization',
        `width=${width},height=${height},left=${left},top=${top}`
      )

      window.addEventListener('message', async (event) => {
        if (event.data.type === 'slack-oauth-callback') {
          if (event.data.success) {
            setIsConnected(true)
            toast({
              title: "Connected successfully",
              description: "Successfully connected to Slack",
            })

            const channels = await getSlackChannels(event.data.workspaceId)
            setWorkspace({
              id: event.data.workspaceId,
              name: 'Slack Workspace',
              channels
            })
          } else {
            setError('Failed to connect to Slack')
            toast({
              title: "Connection failed",
              description: event.data.error || "Failed to connect to Slack",
              variant: "destructive",
            })
          }
          authWindow?.close()
        }
      })
    } catch (error) {
      console.error('Error connecting to Slack:', error)
      setError('Failed to initiate Slack connection')
      toast({
        title: "Connection failed",
        description: "Failed to connect to Slack",
        variant: "destructive",
      })
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await disconnectIntegration('slack', userId)
      setIsConnected(false)
      setWorkspace(null)
      toast({
        title: "Disconnected",
        description: "Successfully disconnected from Slack",
      })
    } catch (error) {
      console.error('Error disconnecting from Slack:', error)
      toast({
        title: "Error",
        description: "Failed to disconnect from Slack",
        variant: "destructive",
      })
    }
  }

  const handleSync = async () => {
    try {
      setIsSyncing(true)
      await syncIntegrationData('slack', userId)

      if (workspace) {
        const channels = await getSlackChannels(workspace.id)
        setWorkspace({
          ...workspace,
          channels
        })
      }

      toast({
        title: "Sync complete",
        description: "Successfully synced Slack data",
      })
    } catch (error) {
      console.error('Error syncing Slack data:', error)
      toast({
        title: "Sync failed",
        description: "Failed to sync Slack data",
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
        <h3 className="text-lg font-medium">Slack Integration</h3>
        <p className="text-sm text-muted-foreground">
          Connect to your Slack workspace to access and sync your channels.
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
              Disconnect Slack
            </>
          ) : isConnecting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Connecting...
            </>
          ) : (
            "Connect to Slack"
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

      {workspace && workspace.channels.length > 0 && (
        <div className="border rounded-lg p-4">
          <h4 className="font-medium mb-2">Connected Channels</h4>
          <div className="space-y-2">
            {workspace.channels.map(channel => (
              <div key={channel.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                <span className="flex items-center gap-2">
                  <span>#{channel.name}</span>
                  {channel.visibility ? (
                    <Unlock className="h-4 w-4 text-green-500" />
                  ) : (
                    <Lock className="h-4 w-4 text-yellow-500" />
                  )}
                </span>
                {channel.creation_time && (
                  <span className="text-muted-foreground">
                    Created: {new Date(parseInt(channel.creation_time) * 1000).toLocaleDateString()}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
