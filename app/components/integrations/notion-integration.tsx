"use client"

import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Loader2, CheckCircle2, AlertCircle, FileText, Database } from "lucide-react";
import { 
    getIntegrationStatus, 
    authorizeIntegration, 
    disconnectIntegration,
    syncIntegrationData,
    NotionPage,
    NotionDatabase,
    IntegrationStatus
} from "@/app/lib/api-client";
import { useToast } from "@/hooks/use-toast";

interface NotionIntegrationProps {
    userId: string;
    orgId: string;
}

interface NotionWorkspace {
    pages: NotionPage[];
    databases: NotionDatabase[];
}

export function NotionIntegration({ userId, orgId }: NotionIntegrationProps) {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [workspace, setWorkspace] = useState<NotionWorkspace | null>(null);
    const { toast } = useToast();

    const processWorkspaceData = (status: IntegrationStatus) => {
        if (status.isConnected && Array.isArray(status.workspace)) {
            const pages = status.workspace.filter((item): item is NotionPage => 
                item.type === 'page'
            );
            const databases = status.workspace.filter((item): item is NotionDatabase => 
                item.type === 'database'
            );
            setWorkspace({ pages, databases });
        } else {
            setWorkspace(null);
        }
    };

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const status = await getIntegrationStatus("notion", userId, orgId);
                setIsConnected(status.isConnected);
                processWorkspaceData(status);
                if (status.error) {
                    setError(status.error);
                }
            } catch (error) {
                console.error("Error checking Notion status:", error);
                setError("Failed to check integration status");
            }
        };

        checkStatus();
    }, [userId, orgId]);

    const handleConnect = async () => {
        try {
            setIsConnecting(true);
            setError(null);

            const authUrl = await authorizeIntegration("notion", userId, orgId);

            const width = 600;
            const height = 700;
            const left = window.screenX + (window.outerWidth - width) / 2;
            const top = window.screenY + (window.outerHeight - height) / 2;

            const authWindow = window.open(
                authUrl,
                "Notion Authorization",
                `width=${width},height=${height},left=${left},top=${top}`
            );

            const messageHandler = async (event: MessageEvent) => {
                if (event.origin !== window.location.origin) {
                    return;
                }

                if (event.data.type === "notion-oauth-callback") {
                    try {
                        if (event.data.success) {
                            setIsConnected(true);
                            toast({
                                title: "Connected successfully",
                                description: "Successfully connected to Notion",
                            });

                            // Fetch updated status
                            const status = await getIntegrationStatus("notion", userId, orgId);
                            processWorkspaceData(status);
                        } else {
                            setError("Failed to connect to Notion");
                            toast({
                                title: "Connection failed",
                                description: event.data.error || "Failed to connect to Notion",
                                variant: "destructive",
                            });
                        }
                    } catch (error) {
                        console.error("Error handling OAuth callback:", error);
                        setError("Failed to complete Notion connection");
                        toast({
                            title: "Connection error",
                            description: "Failed to complete Notion connection",
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
            console.error("Error connecting to Notion:", error);
            setError("Failed to initiate Notion connection");
            toast({
                title: "Connection failed",
                description: "Failed to connect to Notion",
                variant: "destructive",
            });
        } finally {
            setIsConnecting(false);
        }
    };

    const handleDisconnect = async () => {
        try {
            await disconnectIntegration("notion", userId);
            setIsConnected(false);
            setWorkspace(null);
            toast({
                title: "Disconnected",
                description: "Successfully disconnected from Notion",
            });
        } catch (error) {
            console.error("Error disconnecting from Notion:", error);
            toast({
                title: "Error",
                description: "Failed to disconnect from Notion",
                variant: "destructive",
            });
        }
    };

    const handleSync = async () => {
        try {
            setIsSyncing(true);
            await syncIntegrationData("notion", userId);

            // Refresh status
            const status = await getIntegrationStatus("notion", userId, orgId);
            processWorkspaceData(status);

            toast({
                title: "Sync complete",
                description: "Successfully synced Notion data",
            });
        } catch (error) {
            console.error("Error syncing Notion data:", error);
            toast({
                title: "Sync failed",
                description: "Failed to sync Notion data",
                variant: "destructive",
            });
        } finally {
            setIsSyncing(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <h3 className="text-lg font-medium">Notion Integration</h3>
                <p className="text-sm text-muted-foreground">
                    Connect to your Notion workspace to access and sync your pages and databases.
                </p>
            </div>

            {error && error !== "Integration not connected" && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-md">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                </div>
            )}

            <div className="flex gap-4">
                <Button
                    onClick={isConnected ? handleDisconnect : handleConnect}
                    disabled={isConnecting || isSyncing}
                    variant={isConnected ? "outline" : "default"}
                >
                    {isConnected ? (
                        <>
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                            Disconnect Notion
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

                {isConnected && (
                    <Button
                        onClick={handleSync}
                        disabled={isSyncing}
                        variant="outline"
                    >
                        {isSyncing ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Syncing...
                            </>
                        ) : (
                            "Sync Data"
                        )}
                    </Button>
                )}
            </div>

            {workspace && (
                <Tabs defaultValue="pages">
                    <TabsList>
                        <TabsTrigger value="pages" className="flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            Pages
                            {workspace.pages.length > 0 && (
                                <Badge variant="secondary" className="ml-2">
                                    {workspace.pages.length}
                                </Badge>
                            )}
                        </TabsTrigger>
                        <TabsTrigger value="databases" className="flex items-center gap-2">
                            <Database className="h-4 w-4" />
                            Databases
                            {workspace.databases.length > 0 && (
                                <Badge variant="secondary" className="ml-2">
                                    {workspace.databases.length}
                                </Badge>
                            )}
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="pages">
                        <Card>
                            <CardHeader>
                                <CardTitle>Pages</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2">
                                    {workspace.pages.map(page => (
                                        <div key={page.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                                            <span>{page.title || page.name || 'Untitled'}</span>
                                            <span className="text-xs text-muted-foreground">
                                                Last edited: {(() => {
                                                    const date = page.lastEdited || page.last_modified_time;
                                                    if (!date) return 'Never';
                                                    try {
                                                        return new Date(date).toLocaleDateString();
                                                    } catch {
                                                        return 'Invalid date';
                                                    }
                                                })()}
                                            </span>
                                        </div>
                                    ))}
                                    {workspace.pages.length === 0 && (
                                        <p className="text-center text-sm text-muted-foreground">No pages found</p>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="databases">
                        <Card>
                            <CardHeader>
                                <CardTitle>Databases</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2">
                                    {workspace.databases.map(database => (
                                        <div key={database.id} className="flex justify-between text-sm p-2 bg-muted/50 rounded">
                                            <span>{database.name || database.title || 'Untitled'}</span>
                                            <Badge variant="outline">{database.items || 0} items</Badge>
                                        </div>
                                    ))}
                                    {workspace.databases.length === 0 && (
                                        <p className="text-center text-sm text-muted-foreground">No databases found</p>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            )}
        </div>
    );
}
