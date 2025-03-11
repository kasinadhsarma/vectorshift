"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Loader2, CheckCircle2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiPost } from "@/lib/api"

interface HubspotIntegrationProps {
  user: string
  org: string
  integrationParams: any
  setIntegrationParams: (params: any) => void
}

export function HubspotIntegration({ user, org, integrationParams, setIntegrationParams }: HubspotIntegrationProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const { toast } = useToast()

  const handleConnectClick = async () => {
    try {
      setIsConnecting(true)

      // Make API call to backend to get authorization URL
      const authURL = await apiPost("/integrations/hubspot/authorize", {
        user_id: user,
        org_id: org,
      })

      // Open popup window for OAuth flow
      const newWindow = window.open(authURL, "Hubspot Authorization", "width=600, height=600")

      // Poll for window close
      const pollTimer = window.setInterval(() => {
        if (newWindow?.closed !== false) {
          window.clearInterval(pollTimer)
          handleWindowClosed()
        }
      }, 200)
    } catch (error: any) {
      setIsConnecting(false)
      toast({
        title: "Connection failed",
        description: error?.message || "Failed to connect to Hubspot",
        variant: "destructive",
      })
    }
  }

  const handleWindowClosed = async () => {
    try {
      // Get credentials after OAuth flow completes
      const credentials = await apiPost("/integrations/hubspot/credentials", {
        user_id: user,
        org_id: org,
      })

      if (credentials) {
        setIsConnecting(false)
        setIsConnected(true)
        setIntegrationParams((prev: any) => ({
          ...prev,
          credentials: JSON.stringify(credentials),
          type: "Hubspot",
        }))

        toast({
          title: "Connected successfully",
          description: "Successfully connected to Hubspot",
        })
      }
    } catch (error: any) {
      setIsConnecting(false)
      toast({
        title: "Connection failed",
        description: error?.message || "Failed to get Hubspot credentials",
        variant: "destructive",
      })
    }
  }

  useEffect(() => {
    setIsConnected(integrationParams?.credentials && integrationParams?.type === "Hubspot" ? true : false)
  }, [integrationParams])

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Hubspot Integration</h3>
      <p className="text-sm text-muted-foreground">Connect to your Hubspot account to manage your CRM data.</p>

      <div className="flex justify-center">
        <Button
          onClick={isConnected ? () => {} : handleConnectClick}
          disabled={isConnecting}
          className={isConnected ? "bg-green-600 hover:bg-green-700" : ""}
        >
          {isConnected ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Hubspot Connected
            </>
          ) : isConnecting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Connecting...
            </>
          ) : (
            "Connect to Hubspot"
          )}
        </Button>
      </div>
    </div>
  )
}

