'use client'
import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/app/components/ui/button'
import { Card } from '@/app/components/ui/card'
import { Loader2 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import type { IntegrationProps } from './types'

export function NotionIntegration({ 
  user, 
  org, 
  integrationParams, 
  setIntegrationParams 
}: IntegrationProps) {
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [isConnecting, setIsConnecting] = useState<boolean>(false)
  const { toast } = useToast()

  // Initialize connection status
  useEffect(() => {
    setIsConnected(!!integrationParams?.credentials)
  }, [integrationParams])

  // Function to check integration status
  const checkIntegrationStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/integrations/notion/status?userId=${user}&orgId=${org}`)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to check integration status')
      }

      return data.isConnected
    } catch (error) {
      console.error('Error checking integration status:', error)
      return false
    }
  }, [user, org])

  // Handle successful authorization
  const handleAuthSuccess = useCallback(async () => {
    try {
      const isConnected = await checkIntegrationStatus()
      if (isConnected) {
        const response = await fetch(`/api/integrations/notion/data?userId=${user}&orgId=${org}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ userId: user, orgId: org }),
        })

        const data = await response.json()
        if (!response.ok) {
          throw new Error(data.detail || 'Failed to fetch Notion data')
        }

        setIsConnected(true)
        setIntegrationParams({
          credentials: data.credentials,
          type: 'Notion',
        })

        toast({
          title: 'Connected to Notion',
          description: 'Successfully connected to your Notion workspace',
        })
      }
    } catch (error) {
      console.error('Error in auth success handler:', error)
      toast({
        variant: 'destructive',
        title: 'Connection Failed',
        description: error instanceof Error ? error.message : 'Failed to connect to Notion',
      })
    } finally {
      setIsConnecting(false)
    }
  }, [user, org, setIntegrationParams, toast, checkIntegrationStatus])

  // Handle connection click
  const handleConnectClick = useCallback(async () => {
    try {
      setIsConnecting(true)
      
      const response = await fetch('/api/integrations/notion/authorize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId: user, orgId: org }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to start authorization')
      }

      const authWindow = window.open(
        data.url,
        'Notion Authorization',
        'width=600,height=700,left=200,top=100'
      )

      // Set up message listener for OAuth callback
      const handleMessage = async (event: MessageEvent) => {
        if (event.data?.type === 'NOTION_AUTH_SUCCESS') {
          window.removeEventListener('message', handleMessage)
          if (authWindow) authWindow.close()
          await handleAuthSuccess()
        } else if (event.data?.type === 'NOTION_AUTH_ERROR') {
          window.removeEventListener('message', handleMessage)
          if (authWindow) authWindow.close()
          setIsConnecting(false)
          toast({
            variant: 'destructive',
            title: 'Authorization Failed',
            description: event.data.error || 'Failed to authorize with Notion',
          })
        }
      }

      window.addEventListener('message', handleMessage)

      // Cleanup if window is closed manually
      const pollTimer = window.setInterval(() => {
        if (authWindow?.closed) {
          window.clearInterval(pollTimer)
          window.removeEventListener('message', handleMessage)
          setIsConnecting(false)
        }
      }, 500)

    } catch (error) {
      console.error('Error starting authorization:', error)
      setIsConnecting(false)
      toast({
        variant: 'destructive',
        title: 'Connection Failed',
        description: error instanceof Error ? error.message : 'Failed to connect to Notion',
      })
    }
  }, [user, org, handleAuthSuccess, toast])

  return (
    <Card className="p-6">
      <div className="flex flex-col items-center space-y-4">
        <h3 className="text-lg font-semibold">Connect to Notion</h3>
        <Button
          onClick={isConnected ? undefined : handleConnectClick}
          disabled={isConnecting}
          variant={isConnected ? "secondary" : "default"}
          className={isConnected ? "cursor-default" : ""}
        >
          {isConnecting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Connecting...
            </>
          ) : isConnected ? (
            'Connected to Notion'
          ) : (
            'Connect Notion'
          )}
        </Button>
      </div>
    </Card>
  )
}
