"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { Badge } from "@/app/components/ui/badge"
import { Button } from "@/app/components/ui/button"
import { BarChart3, FileSpreadsheet, Lightbulb, MessageSquare } from "lucide-react"
import Link from "next/link"

interface IntegrationsOverviewProps {
  onSelectIntegration: (integration: string | null) => void
  activeIntegration: string | null
}

export function IntegrationsOverview({ onSelectIntegration, activeIntegration }: IntegrationsOverviewProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Integration Health</CardTitle>
        <CardDescription>Monitor the status of your integrations</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="all">
          <TabsList className="mb-4">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="issues">Issues</TabsTrigger>
          </TabsList>
          <TabsContent value="all" className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-2">
                    <Lightbulb className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">Notion</div>
                    <div className="text-sm text-muted-foreground">Last synced 2 hours ago</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className="bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                  >
                    Healthy
                  </Badge>
                  <Link href="/dashboard/integrations/notion">
                    <Button variant="ghost" size="sm">
                      View
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-2">
                    <FileSpreadsheet className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">Airtable</div>
                    <div className="text-sm text-muted-foreground">Last synced 5 hours ago</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className="bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                  >
                    Healthy
                  </Badge>
                  <Link href="/dashboard/integrations/airtable">
                    <Button variant="ghost" size="sm">
                      View
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-2">
                    <BarChart3 className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">Hubspot</div>
                    <div className="text-sm text-muted-foreground">Not connected</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className="bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400"
                  >
                    Inactive
                  </Badge>
                  <Link href="/dashboard/integrations/hubspot">
                    <Button variant="ghost" size="sm">
                      Connect
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-2">
                    <MessageSquare className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">Slack</div>
                    <div className="text-sm text-muted-foreground">Last synced 1 day ago</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400">
                    Issues
                  </Badge>
                  <Link href="/dashboard/integrations/slack">
                    <Button variant="ghost" size="sm">
                      Fix
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="active" className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-2">
                    <Lightbulb className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">Notion</div>
                    <div className="text-sm text-muted-foreground">Last synced 2 hours ago</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className="bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                  >
                    Healthy
                  </Badge>
                  <Link href="/dashboard/integrations/notion">
                    <Button variant="ghost" size="sm">
                      View
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-2">
                    <FileSpreadsheet className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">Airtable</div>
                    <div className="text-sm text-muted-foreground">Last synced 5 hours ago</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className="bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                  >
                    Healthy
                  </Badge>
                  <Link href="/dashboard/integrations/airtable">
                    <Button variant="ghost" size="sm">
                      View
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="issues" className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-2">
                    <MessageSquare className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">Slack</div>
                    <div className="text-sm text-muted-foreground">Last synced 1 day ago</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400">
                    Issues
                  </Badge>
                  <Link href="/dashboard/integrations/slack">
                    <Button variant="ghost" size="sm">
                      Fix
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

