"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { useToast } from "@/hooks/use-toast"
import { Badge } from "@/app/components/ui/badge"
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import {
  authorizeIntegration,
  getIntegrationStatus,
  disconnectIntegration,
  getHubspotContacts,
  syncIntegrationData,
  IntegrationStatus,
  HubSpotContact,
} from "@/app/lib/api-client"

interface HubspotIntegrationProps {
  userId: string
  orgId: string
}

interface HubSpotWorkspace {
  id: string
  name: string
  contacts: HubSpotContact[]
}

export function HubspotIntegration({ userId, orgId }: HubspotIntegrationProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [workspace, setWorkspace] = useState<HubSpotWorkspace | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status: IntegrationStatus = await getIntegrationStatus('hubspot', userId)
        setIsConnected(status.isConnected)

        if (status.isConnected && status.credentials?.workspaceId) {
          const contacts = await getHubspotContacts(status.credentials.workspaceId)
          setWorkspace({
            id: status.credentials.workspaceId,
            name: 'HubSpot Workspace',
            contacts
          })
        }

        if (status.error) {
          setError(status.error)
        }
      } catch (error) {
        console.error('Error checking HubSpot status:', error)
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

      const authUrl = await authorizeIntegration('hubspot', userId, orgId)

      const width = 600
      const height = 700
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2

      const authWindow = window.open(
        authUrl,
        'HubSpot Authorization',
        `width=${width},height=${height},left=${left},top=${top}`
      )

      window.addEventListener('message', async (event) => {
        if (event.data.type === 'hubspot-oauth-callback') {
          if (event.data.success) {
            setIsConnected(true)
            toast({
              title: "Connected successfully",
              description: "Successfully connected to HubSpot",
            })

            const contacts = await getHubspotContacts(event.data.workspaceId)
            setWorkspace({
              id: event.data.workspaceId,
              name: 'HubSpot Workspace',
              contacts
            })
          } else {
            setError('Failed to connect to HubSpot')
            toast({
              title: "Connection failed",
              description: event.data.error || "Failed to connect to HubSpot",
              variant: "destructive",
            })
          }
          authWindow?.close()
        }
      })
    } catch (error) {
      console.error('Error connecting to HubSpot:', error)
      setError('Failed to initiate HubSpot connection')
      toast({
        title: "Connection failed",
        description: "Failed to connect to HubSpot",
        variant: "destructive",
      })
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await disconnectIntegration('hubspot', userId)
      setIsConnected(false)
      setWorkspace(null)
      toast({
        title: "Disconnected",
        description: "Successfully disconnected from HubSpot",
      })
    } catch (error) {
      console.error('Error disconnecting from HubSpot:', error)
      toast({
        title: "Error",
        description: "Failed to disconnect from HubSpot",
        variant: "destructive",
      })
    }
  }

  const handleSync = async () => {
    try {
      setIsSyncing(true)
      await syncIntegrationData('hubspot', userId)

      if (workspace) {
        const contacts = await getHubspotContacts(workspace.id)
        setWorkspace({
          ...workspace,
          contacts
        })
      }

      toast({
        title: "Sync complete",
        description: "Successfully synced HubSpot data",
      })
    } catch (error) {
      console.error('Error syncing HubSpot data:', error)
      toast({
        title: "Sync failed",
        description: "Failed to sync HubSpot data",
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
        <h3 className="text-lg font-medium">HubSpot Integration</h3>
        <p className="text-sm text-muted-foreground">
          Connect to your HubSpot workspace to access and sync your contacts.
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
              Disconnect HubSpot
            </>
          ) : isConnecting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Connecting...
            </>
          ) : (
            "Connect to HubSpot"
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

      {workspace && workspace.contacts.length > 0 && (
        <div className="border rounded-lg p-4">
          <h4 className="font-medium mb-2">Connected Contacts</h4>
          <div className="space-y-2">
            {workspace.contacts.map(contact => (
              <div key={contact.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                <span className="flex flex-col">
                  <span>{contact.name}</span>
                  {contact.email && (
                    <span className="text-xs text-muted-foreground">{contact.email}</span>
                  )}
                </span>
                <span className="text-muted-foreground">
                  Last modified: {new Date(contact.last_modified_time).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
