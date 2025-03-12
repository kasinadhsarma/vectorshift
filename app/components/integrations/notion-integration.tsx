"use client"

import { useState, useEffect } from "react"
import axios, { AxiosError, AxiosResponse } from "axios"
import { Button } from "../ui/button"
import { Loader2 } from "lucide-react"

interface IntegrationParams {
    credentials?: Record<string, any>
    type?: string
}

interface AuthResponse {
    url: string
}

interface CredentialsResponse {
    access_token: string
    workspace_id: string
    [key: string]: any
}

interface ErrorResponse {
    detail: string
}

interface NotionIntegrationProps {
    user: string
    org: string
    integrationParams?: IntegrationParams
    setIntegrationParams: (params: IntegrationParams) => void
}

export const NotionIntegration = ({ 
    user, 
    org, 
    integrationParams, 
    setIntegrationParams 
}: NotionIntegrationProps) => {
    const [isConnected, setIsConnected] = useState(false)
    const [isConnecting, setIsConnecting] = useState(false)

    // Function to open OAuth in a new window
    const handleConnectClick = async () => {
        try {
            setIsConnecting(true)

            const response: AxiosResponse<AuthResponse> = await axios.post(
                `http://localhost:8000/integrations/notion/authorize`, 
                { user_id: user, org_id: org }  // Send JSON instead of FormData
            )
            
            const authURL = response.data.url
            const newWindow = window.open(authURL, 'Notion Authorization', 'width=600, height=600')

            // Polling for the window to close
            const pollTimer = window.setInterval(() => {
                if (newWindow?.closed !== false) { 
                    window.clearInterval(pollTimer)
                    handleWindowClosed()
                }
            }, 200)
        } catch (e) {
            setIsConnecting(false)
            const error = e as AxiosError<ErrorResponse>
            alert(error.response?.data?.detail || 'Failed to connect to Notion')
        }
    }

    // Function to handle logic when the OAuth window closes
    const handleWindowClosed = async () => {
        try {
            const response: AxiosResponse<CredentialsResponse> = await axios.post(
                `http://localhost:8000/integrations/notion/credentials`, 
                { user_id: user, org_id: org }  // Send JSON instead of FormData
            )
            const credentials = response.data

            if (credentials) {
                setIsConnected(true)
                setIntegrationParams({ 
                    ...integrationParams, 
                    credentials: credentials, 
                    type: 'Notion' 
                })
            }
            setIsConnecting(false)
        } catch (e) {
            setIsConnecting(false)
            const error = e as AxiosError<ErrorResponse>
            alert(error.response?.data?.detail || 'Failed to get Notion credentials')
        }
    }

    useEffect(() => {
        setIsConnected(!!integrationParams?.credentials)
    }, [integrationParams])

    return (
        <div className="mt-4">
            <h3 className="mb-4">Parameters</h3>
            <div className="flex items-center justify-center">
                <Button
                    variant={isConnected ? "outline" : "default"}
                    onClick={isConnected ? () => {} : handleConnectClick}
                    disabled={isConnecting}
                    className={isConnected ? "cursor-default opacity-100" : ""}
                >
                    {isConnected ? 'Notion Connected' : isConnecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : 'Connect to Notion'}
                </Button>
            </div>
        </div>
    )
}
