"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Loader2, CheckCircle2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface SlackIntegrationProps {
  user: string
  org: string
  integrationParams: any
  setIntegrationParams: (params: any) => void
}

export function SlackIntegration({ user, org, integrationParams, setIntegrationParams }: SlackIntegrationProps) {
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
        credentials: { access_token: "mock_slack_token" },
        type: "Slack",
      }))

      toast({
        title: "Connected successfully",
        description: "Successfully connected to Slack",
      })
    } catch (error: any) {
      setIsConnecting(false)
      toast({
        title: "Connection failed",
        description: "Failed to connect to Slack",
        variant: "destructive",
      })
    }
  }

  useEffect(() => {
    setIsConnected(integrationParams?.credentials && integrationParams?.type === "Slack" ? true : false)
  }, [integrationParams])

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Slack Integration</h3>
      <p className="text-sm text-muted-foreground">Connect to Slack to manage messages and channels.</p>

      <div className="flex justify-center">
        <Button
          onClick={isConnected ? () => {} : handleConnectClick}
          disabled={isConnecting}
          className={isConnected ? "bg-green-600 hover:bg-green-700" : ""}
        >
          {isConnected ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Slack Connected
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
      </div>
    </div>
  )
}

