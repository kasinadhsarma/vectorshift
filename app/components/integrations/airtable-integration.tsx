"use client"

import { useState } from "react"
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { Badge } from "@/app/components/ui/badge"
import { Loader2 } from "lucide-react"

interface AirtableIntegrationProps {
  user: string
  org: string
  integrationParams: any
  setIntegrationParams: (params: any) => void
}

export function AirtableIntegration({ user, org, integrationParams, setIntegrationParams }: AirtableIntegrationProps) {
  const { toast } = useToast()
  const [isConnecting, setIsConnecting] = useState(false)
  const [apiKey, setApiKey] = useState("")

  const handleConnect = async () => {
    if (!apiKey) {
      toast({
        title: "Error",
        description: "Please enter your Airtable API key",
        variant: "destructive",
      })
      return
    }

    setIsConnecting(true)

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))

      setIntegrationParams({
        ...integrationParams,
        credentials: {
          apiKey,
        },
        status: "connected",
        connectedAt: new Date().toISOString(),
      })

      toast({
        title: "Connected",
        description: "Successfully connected to Airtable",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to Airtable",
        variant: "destructive",
      })
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    setIsConnecting(true)

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000))

      setIntegrationParams({
        ...integrationParams,
        credentials: null,
        status: "disconnected",
      })

      toast({
        title: "Disconnected",
        description: "Successfully disconnected from Airtable",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to disconnect from Airtable",
        variant: "destructive",
      })
    } finally {
      setIsConnecting(false)
    }
  }

  return (
    <div className="space-y-4">
      {integrationParams?.credentials ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="text-lg font-medium">Connection Status</h3>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className="bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                >
                  Connected
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Connected{" "}
                  {integrationParams.connectedAt
                    ? new Date(integrationParams.connectedAt).toLocaleDateString()
                    : "recently"}
                </span>
              </div>
            </div>
            <Button variant="outline" onClick={handleDisconnect} disabled={isConnecting}>
              {isConnecting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Disconnecting...
                </>
              ) : (
                "Disconnect"
              )}
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="api-key">Airtable API Key</Label>
            <Input
              id="api-key"
              type="password"
              placeholder="Enter your Airtable API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              You can find your API key in your Airtable account settings.
            </p>
          </div>
          <Button onClick={handleConnect} disabled={isConnecting || !apiKey}>
            {isConnecting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Connecting...
              </>
            ) : (
              "Connect to Airtable"
            )}
          </Button>
        </div>
      )}
    </div>
  )
}

