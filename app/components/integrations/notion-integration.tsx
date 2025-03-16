"use client"

import { useState, useEffect } from "react";
import axios, { AxiosError } from "axios";
import { Button } from "../ui/button";
import { Loader2 } from "lucide-react";
import { getIntegrationStatus } from "@/app/lib/api-client";

interface IntegrationParams {
    credentials?: Record<string, any>;
    type?: string;
}

interface AuthResponse {
    url: string;
}

interface ErrorResponse {
    detail: string;
}

interface NotionIntegrationProps {
    user: string;
    org: string;
    integrationParams?: IntegrationParams;
    setIntegrationParams: (params: IntegrationParams) => void;
}

export const NotionIntegration = ({ 
    user, 
    org, 
    integrationParams, 
    setIntegrationParams 
}: NotionIntegrationProps) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    const handleConnectClick = async () => {
        if (!user || !org) {
            alert("Missing user or organization ID");
            return;
        }
        
        try {
            setIsConnecting(true);
            const response = await axios.post<AuthResponse>(
                `/api/integrations/notion/authorize`,
                { userId: user, orgId: org },
                { headers: { "Content-Type": "application/json" } }
            );

            if (!response.data?.url) {
                throw new Error("Invalid authorization URL");
            }

            const newWindow = window.open(
                response.data.url,
                "Notion Authorization",
                "width=600,height=600,menubar=no,toolbar=no"
            );

            if (!newWindow) {
                throw new Error("Popup was blocked. Please allow popups and try again.");
            }

            const pollTimer = window.setInterval(() => {
                if (newWindow.closed) {
                    window.clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 200);
        } catch (e) {
            setIsConnecting(false);
            const error = e as AxiosError<ErrorResponse>;
            console.error("Authorization error:", error);
            alert(error.response?.data?.detail || "Failed to connect to Notion");
        }
    };

    const handleWindowClosed = async () => {
        try {
            await new Promise(resolve => setTimeout(resolve, 1000));

            const status = await getIntegrationStatus("notion", user, org);
            if (status.isConnected) {
                setIsConnected(true);
                setIntegrationParams({ 
                    credentials: status.credentials,
                    type: "Notion" 
                });
            } else {
                throw new Error("Failed to connect to Notion");
            }
        } catch (e) {
            setIsConnecting(false);
            const error = e as AxiosError<ErrorResponse>;
            console.error("Connection error:", error);
            alert(error.response?.data?.detail || "Failed to connect to Notion");
        }
    };

    useEffect(() => {
        setIsConnected(!!integrationParams?.credentials);
    }, [integrationParams]);

    return (
        <div className="mt-4">
            <h3 className="mb-4">Integration Status</h3>
            <div className="flex items-center justify-center">
                <Button
                    variant={isConnected ? "outline" : "default"}
                    onClick={isConnected ? undefined : handleConnectClick}
                    disabled={isConnecting}
                    className={isConnected ? "cursor-default opacity-100" : ""}
                >
                    {isConnected ? "Notion Connected" : isConnecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Connect to Notion"}
                </Button>
            </div>
        </div>
    );
};
