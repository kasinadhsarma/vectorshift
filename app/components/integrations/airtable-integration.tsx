"use client"

import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { getIntegrationStatus, authorizeIntegration } from "@/app/lib/api-client";
import { useToast } from "@/hooks/use-toast";

interface AirtableIntegrationProps {
    userId: string;
    orgId: string;
}

export function AirtableIntegration({ userId, orgId }: AirtableIntegrationProps) {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { toast } = useToast();

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const status = await getIntegrationStatus("airtable", userId, orgId);
                setIsConnected(status.isConnected);
                if (status.error) {
                    setError(status.error);
                }
            } catch (error) {
                console.error("Error checking Airtable status:", error);
                setError("Failed to check integration status");
            }
        };

        checkStatus();
    }, [userId, orgId]);

    const handleConnect = async () => {
        try {
            setIsConnecting(true);
            setError(null);

            const authUrl = await authorizeIntegration("airtable", userId, orgId);

            const width = 600;
            const height = 700;
            const left = window.screenX + (window.outerWidth - width) / 2;
            const top = window.screenY + (window.outerHeight - height) / 2;

            const authWindow = window.open(
                authUrl,
                "Airtable Authorization",
                `width=${width},height=${height},left=${left},top=${top}`
            );

            const messageHandler = async (event: MessageEvent) => {
                if (event.origin !== window.location.origin) {
                    return;
                }

                if (event.data.type === "airtable-oauth-callback") {
                    try {
                        if (event.data.success) {
                            setIsConnected(true);
                            toast({
                                title: "Connected successfully",
                                description: "Successfully connected to Airtable",
                            });
                        } else {
                            setError("Failed to connect to Airtable");
                            toast({
                                title: "Connection failed",
                                description: event.data.error || "Failed to connect to Airtable",
                                variant: "destructive",
                            });
                        }
                    } catch (error) {
                        console.error("Error handling OAuth callback:", error);
                        setError("Failed to complete Airtable connection");
                        toast({
                            title: "Connection error",
                            description: "Failed to complete Airtable connection",
                            variant: "destructive",
                        });
                    } finally {
                        authWindow?.close();
                    }
                }
            };

            window.addEventListener("message", messageHandler);
            return () => window.removeEventListener("message", messageHandler);

        } catch (error) {
            console.error("Error connecting to Airtable:", error);
            setError("Failed to initiate Airtable connection");
            toast({
                title: "Connection failed",
                description: "Failed to connect to Airtable",
                variant: "destructive",
            });
        } finally {
            setIsConnecting(false);
        }
    };

    return (
        <div className="space-y-4">
            {error && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-md">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                </div>
            )}

            <Button
                onClick={handleConnect}
                disabled={isConnecting}
                variant={isConnected ? "outline" : "default"}
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
    );
}
