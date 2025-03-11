"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Loader2, CheckCircle2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface AirtableIntegrationProps {
  user: string
  org: string
  integrationParams: any
  setIntegrationParams: (params: any) => void
}

export function AirtableIntegration({ user, org, integrationParams, setIntegrationParams }: AirtableIntegrationProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const { toast } = useToast()

  const handleConnectClick = async () => {
    try {
      setIsConnecting(true)
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Mock successful connection
      setIsConnecting(false)
      setIsConnected(true)
      setIntegrationParams((prev: any) => ({
        ...prev,
        credentials: { access_token: "mock_airtable_token" },
        type: "Airtable",
      }))

      toast({
        title: "Connected successfully",
        description: "Successfully connected to Airtable",
      })
    } catch (error: any) {
      setIsConnecting(false)
      toast({
        title: "Connection failed",
        description: "Failed to connect to Airtable",
        variant: "destructive",
      })
    }
  }

  useEffect(() => {
    setIsConnected(integrationParams?.credentials && integrationParams?.type === "Airtable" ? true : false)
  }, [integrationParams])

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Airtable Integration</h3>
      <p className="text-sm text-muted-foreground">Connect to your Airtable account to import data from your bases.</p>

      <div className="flex justify-center">
        <Button
          onClick={isConnected ? () => {} : handleConnectClick}
          disabled={isConnecting}
          className={isConnected ? "bg-green-600 hover:bg-green-700" : ""}
        >
          {isConnected ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Airtable Connected
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
      </div>
    </div>
  )
}

