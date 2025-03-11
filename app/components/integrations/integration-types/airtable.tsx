"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { Loader2, CheckCircle2 } from "lucide-react"
import { useToast } from "@/app/components/ui/use-toast"
import axios from "axios"

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
      const formData = new FormData()
      formData.append("user_id", user)
      formData.append("org_id", org)
      const response = await axios.post(`http://localhost:8000/integrations/airtable/authorize`, formData)
      const authURL = response?.data

      const newWindow = window.open(authURL, "Airtable Authorization", "width=600, height=600")

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
        description: error?.response?.data?.detail || "Failed to connect to Airtable",
        variant: "destructive",
      })
    }
  }

  const handleWindowClosed = async () => {
    try {
      const formData = new FormData()
      formData.append("user_id", user)
      formData.append("org_id", org)
      const response = await axios.post(`http://localhost:8000/integrations/airtable/credentials`, formData)
      const credentials = response.data
      if (credentials) {
        setIsConnecting(false)
        setIsConnected(true)
        setIntegrationParams((prev: any) => ({ ...prev, credentials: credentials, type: "Airtable" }))
        toast({
          title: "Connected successfully",
          description: "Successfully connected to Airtable",
        })
      }
      setIsConnecting(false)
    } catch (error: any) {
      setIsConnecting(false)
      toast({
        title: "Connection failed",
        description: error?.response?.data?.detail || "Failed to get Airtable credentials",
        variant: "destructive",
      })
    }
  }

  useEffect(() => {
    setIsConnected(integrationParams?.credentials ? true : false)
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

