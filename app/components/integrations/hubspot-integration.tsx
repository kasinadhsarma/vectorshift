"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { useToast } from "@/hooks/use-toast"
import { Badge } from "@/app/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Loader2, CheckCircle2, AlertCircle, Building2, Users } from "lucide-react"
import {
  authorizeIntegration,
  getIntegrationStatus,
  disconnectIntegration,
  syncIntegrationData,
  IntegrationStatus,
  HubSpotContact,
  HubSpotCompany,
} from "@/app/lib/api-client"

interface HubspotIntegrationProps {
  userId: string
  orgId: string
}

interface HubSpotWorkspace {
  id: string
  name: string
  contacts: HubSpotContact[]
  companies: HubSpotCompany[]
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
        const status: IntegrationStatus = await getIntegrationStatus('hubspot', userId, orgId)
        setIsConnected(status.isConnected)
        setError(status.error || null)

        if (status.isConnected && Array.isArray(status.workspace)) {
          const contacts = status.workspace.filter((item): item is HubSpotContact => 
            item.type === 'contact'
          )
          const companies = status.workspace.filter((item): item is HubSpotCompany => 
            item.type === 'company'
          )
          setWorkspace({
            id: 'hubspot',
            name: 'HubSpot Workspace',
            contacts,
            companies
          })
        } else {
          setWorkspace(null)
        }
      } catch (error) {
        console.error('Error checking HubSpot status:', error)
        setError('Failed to check integration status')
        setIsConnected(false)
        setWorkspace(null)
      } finally {
        setIsLoading(false)
      }
    }

    checkStatus()
  }, [userId, orgId])

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

      const messageHandler = async (event: MessageEvent) => {
        if (event.origin !== window.location.origin) {
          return;
        }
        
        if (event.data.type === 'hubspot-oauth-callback') {
          try {
            if (event.data.success) {
              setIsConnected(true)
              toast({
                title: "Connected successfully",
                description: "Successfully connected to HubSpot",
              })

              // Fetch updated status
              const status = await getIntegrationStatus('hubspot', userId, orgId)
              if (status.isConnected && Array.isArray(status.workspace)) {
                const contacts = status.workspace.filter((item): item is HubSpotContact => 
                  item.type === 'contact'
                )
                const companies = status.workspace.filter((item): item is HubSpotCompany => 
                  item.type === 'company'
                )
                setWorkspace({
                  id: 'hubspot',
                  name: 'HubSpot Workspace',
                  contacts,
                  companies
                })
              }
            } else {
              setError('Failed to connect to HubSpot')
              toast({
                title: "Connection failed",
                description: event.data.error || "Failed to connect to HubSpot",
                variant: "destructive",
              })
            }
          } catch (error) {
            console.error('Error handling OAuth callback:', error)
            setError('Failed to complete HubSpot connection')
            toast({
              title: "Connection error",
              description: "Failed to complete HubSpot connection",
              variant: "destructive",
            })
          } finally {
            authWindow?.close()
          }
        }
      }

      window.addEventListener('message', messageHandler)
      return () => window.removeEventListener('message', messageHandler)
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

      // Refresh status
      const status = await getIntegrationStatus('hubspot', userId, orgId)
      if (status.isConnected && Array.isArray(status.workspace)) {
        const contacts = status.workspace.filter((item): item is HubSpotContact => 
          item.type === 'contact'
        )
        const companies = status.workspace.filter((item): item is HubSpotCompany => 
          item.type === 'company'
        )
        setWorkspace({
          id: 'hubspot',
          name: 'HubSpot Workspace',
          contacts,
          companies
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
          Connect to your HubSpot workspace to access and sync your CRM data.
        </p>
      </div>

      {error && error !== "Integration not connected" && (
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

      {workspace && (
        <Tabs defaultValue="contacts">
          <TabsList>
            <TabsTrigger value="contacts" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Contacts
              {workspace.contacts.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {workspace.contacts.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="companies" className="flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Companies
              {workspace.companies.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {workspace.companies.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="contacts">
            <Card>
              <CardHeader>
                <CardTitle>Contacts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {workspace.contacts.map(contact => (
                    <div key={contact.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                      <span className="flex flex-col">
                        <span>{contact.name}</span>
                        {contact.email && (
                          <span className="text-xs text-muted-foreground">{contact.email}</span>
                        )}
                      </span>
                      <div className="flex items-center gap-4">
                        {contact.company && (
                          <Badge variant="outline">{contact.company}</Badge>
                        )}
                        <span className="text-xs text-muted-foreground">
                          Last modified: {new Date(contact.last_modified_time).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                  {workspace.contacts.length === 0 && (
                    <p className="text-center text-sm text-muted-foreground">No contacts found</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="companies">
            <Card>
              <CardHeader>
                <CardTitle>Companies</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {workspace.companies.map(company => (
                    <div key={company.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                      <span className="flex flex-col">
                        <span>{company.name}</span>
                        {company.domain && (
                          <span className="text-xs text-muted-foreground">{company.domain}</span>
                        )}
                      </span>
                      <div className="flex items-center gap-4">
                        {company.industry && (
                          <Badge variant="outline">{company.industry}</Badge>
                        )}
                        <span className="text-xs text-muted-foreground">
                          Last modified: {new Date(company.last_modified_time).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                  {workspace.companies.length === 0 && (
                    <p className="text-center text-sm text-muted-foreground">No companies found</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
