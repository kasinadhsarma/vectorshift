"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { Loader2, CheckCircle2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface NotionIntegrationProps {
  user: string
  org: string
  integrationParams: any
  setIntegrationParams: (params: any) => void
}

export function NotionIntegration({ user, org, integrationParams, setIntegrationParams }: NotionIntegrationProps) {
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
        credentials: { access_token: "mock_notion_token" },
        type: "Notion",
      }))

      toast({
        title: "Connected successfully",
        description: "Successfully connected to Notion",
      })
    } catch (error: any) {
      setIsConnecting(false)
      toast({
        title: "Connection failed",
        description: "Failed to connect to Notion",
        variant: "destructive",
      })
    }
  }

  useEffect(() => {
    setIsConnected(integrationParams?.credentials && integrationParams?.type === "Notion" ? true : false)
  }, [integrationParams])

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Notion Integration</h3>
      <p className="text-sm text-muted-foreground">Connect to your Notion workspace to import databases and pages.</p>

      <div className="flex justify-center">
        <Button
          onClick={isConnected ? () => {} : handleConnectClick}
          disabled={isConnecting}
          className={isConnected ? "bg-green-600 hover:bg-green-700" : ""}
        >
          {isConnected ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Notion Connected
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
      </div>
    </div>
  )
}

