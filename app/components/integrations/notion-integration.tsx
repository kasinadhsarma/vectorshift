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
        if (!user || !org) {
            alert('Missing user or organization ID');
            return;
        }
        
        try {
            setIsConnecting(true);
            const response = await axios.post<AuthResponse>(
                `http://localhost:8000/api/integrations/notion/authorize`,
                { userId: user, orgId: org },
                { headers: { 'Content-Type': 'application/json' } }
            );

            if (!response.data?.url) {
                throw new Error('Invalid authorization URL');
            }

            const newWindow = window.open(
                response.data.url,
                'Notion Authorization',
                'width=600,height=600,menubar=no,toolbar=no'
            );

            if (!newWindow) {
                throw new Error('Popup was blocked. Please allow popups and try again.');
            }

            // Listen for messages from popup
            const messageHandler = (event: MessageEvent) => {
                if (event.data.error) {
                    alert(`Authorization failed: ${event.data.error}`);
                    setIsConnecting(false);
                }
            };
            window.addEventListener('message', messageHandler);

            // Poll for window close
            const pollTimer = window.setInterval(() => {
                if (newWindow.closed) {
                    window.clearInterval(pollTimer);
                    window.removeEventListener('message', messageHandler);
                    handleWindowClosed();
                }
            }, 200);

        } catch (e) {
            setIsConnecting(false);
            const error = e as AxiosError<ErrorResponse>;
            alert(error.response?.data?.detail || 'Failed to connect to Notion');
        }
    }

    // Function to handle logic when the OAuth window closes
    const handleWindowClosed = async () => {
        try {
            const data = { user_id: user, org_id: org }
            const response: AxiosResponse<CredentialsResponse> = await axios.post(
                `http://localhost:8000/api/integrations/notion/credentials`, 
                data,
                {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
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
