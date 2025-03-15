"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { useToast } from "@/app/components/ui/use-toast"
import { Badge } from "@/app/components/ui/badge"
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import {
  authorizeIntegration,
  getIntegrationStatus,
  disconnectIntegration,
  getAirtableBases,
  syncIntegrationData,
  IntegrationStatus,
} from "@/app/lib/api-client"

interface AirtableIntegrationProps {
  userId: string
  orgId: string
}

import { AirtableBase } from "@/app/lib/api-client"

interface AirtableWorkspace {
  id: string
  name: string
  bases: Array<AirtableBase>
}

export function AirtableIntegration({ userId, orgId }: AirtableIntegrationProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [workspace, setWorkspace] = useState<AirtableWorkspace | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status: IntegrationStatus = await getIntegrationStatus('airtable', userId)
        setIsConnected(status.isConnected)

        if (status.isConnected && status.credentials?.workspaceId) {
          const bases = await getAirtableBases(status.credentials.workspaceId)
          setWorkspace({
            id: status.credentials.workspaceId,
            name: 'Airtable Workspace',
            bases
          })
        }

        if (status.error) {
          setError(status.error)
        }
      } catch (error) {
        console.error('Error checking Airtable status:', error)
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

      const authUrl = await authorizeIntegration('airtable', userId, orgId)

      const width = 600
      const height = 700
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2

      const authWindow = window.open(
        authUrl,
        'Airtable Authorization',
        `width=${width},height=${height},left=${left},top=${top}`
      )

      window.addEventListener('message', async (event) => {
        if (event.data.type === 'airtable-oauth-callback') {
          if (event.data.success) {
            setIsConnected(true)
            toast({
              title: "Connected successfully",
              description: "Successfully connected to Airtable",
            })

            const bases = await getAirtableBases(event.data.workspaceId)
            setWorkspace({
              id: event.data.workspaceId,
              name: 'Airtable Workspace',
              bases
            })
          } else {
            setError('Failed to connect to Airtable')
            toast({
              title: "Connection failed",
              description: event.data.error || "Failed to connect to Airtable",
              variant: "destructive",
            })
          }
          authWindow?.close()
        }
      })
    } catch (error) {
      console.error('Error connecting to Airtable:', error)
      setError('Failed to initiate Airtable connection')
      toast({
        title: "Connection failed",
        description: "Failed to connect to Airtable",
        variant: "destructive",
      })
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await disconnectIntegration('airtable', userId)
      setIsConnected(false)
      setWorkspace(null)
      toast({
        title: "Disconnected",
        description: "Successfully disconnected from Airtable",
      })
    } catch (error) {
      console.error('Error disconnecting from Airtable:', error)
      toast({
        title: "Error",
        description: "Failed to disconnect from Airtable",
        variant: "destructive",
      })
    }
  }

  const handleSync = async () => {
    try {
      setIsSyncing(true)
      await syncIntegrationData('airtable', userId)

      if (workspace) {
        const bases = await getAirtableBases(workspace.id)
        setWorkspace({
          ...workspace,
          bases
        })
      }

      toast({
        title: "Sync complete",
        description: "Successfully synced Airtable data",
      })
    } catch (error) {
      console.error('Error syncing Airtable data:', error)
      toast({
        title: "Sync failed",
        description: "Failed to sync Airtable data",
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
        <h3 className="text-lg font-medium">Airtable Integration</h3>
        <p className="text-sm text-muted-foreground">
          Connect to your Airtable workspace to access and sync your bases.
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
              Disconnect Airtable
            </>
          ) : isConnecting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Connecting...
            </>
          ) : (
            "Connect to Airtable"
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

      {workspace && workspace.bases.length > 0 && (
        <div className="border rounded-lg p-4">
          <h4 className="font-medium mb-2">Connected Bases</h4>
          <div className="space-y-2">
            {workspace.bases.map(base => (
              <div key={base.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                <span>{base.name}</span>
                <span className="text-muted-foreground">
                  Last modified: {new Date(base.last_modified_time).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
