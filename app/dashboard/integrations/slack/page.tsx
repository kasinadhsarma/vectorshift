"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { SlackIntegration } from "@/app/components/integrations/slack-integration"
import { DataVisualization } from "@/app/components/dashboard/data-visualization"
import { MessageSquare, RefreshCw } from "lucide-react"

export default function SlackIntegrationPage() {
  const [integrationParams, setIntegrationParams] = useState<any>({})
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Mock user and org data
  const user = "user123"
  const org = "org456"

  const fetchData = async () => {
    setIsLoading(true)
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Mock data
      const mockData = {
        channels: [
          { id: "channel1", name: "general", members: 25, messages: 1240 },
          { id: "channel2", name: "random", members: 20, messages: 856 },
          { id: "channel3", name: "project-alpha", members: 12, messages: 432 },
        ],
        messages: [
          {
            id: "msg1",
            channel: "general",
            user: "John Doe",
            text: "Good morning team!",
            timestamp: "2023-05-20T09:00:00Z",
          },
          {
            id: "msg2",
            channel: "general",
            user: "Jane Smith",
            text: "Morning everyone!",
            timestamp: "2023-05-20T09:05:00Z",
          },
          {
            id: "msg3",
            channel: "project-alpha",
            user: "Bob Johnson",
            text: "Let's discuss the new feature",
            timestamp: "2023-05-20T10:15:00Z",
          },
        ],
        users: [
          { id: "user1", name: "John Doe", status: "active" },
          { id: "user2", name: "Jane Smith", status: "away" },
          { id: "user3", name: "Bob Johnson", status: "active" },
        ],
      }

      setData(mockData)
    } catch (error) {
      console.error("Error fetching data:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Slack Integration</h1>
          <p className="text-muted-foreground">Connect and manage your Slack workspace</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={fetchData}
            disabled={isLoading || !integrationParams?.credentials}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            <span className="sr-only">Refresh data</span>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center gap-4">
            <div className="p-2 rounded-full bg-primary/10">
              <MessageSquare className="h-8 w-8 text-primary" />
            </div>
            <div>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>Manage your Slack connection</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <SlackIntegration
              user={user}
              org={org}
              integrationParams={integrationParams}
              setIntegrationParams={setIntegrationParams}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Slack Data</CardTitle>
            <CardDescription>View and manage your Slack data</CardDescription>
          </CardHeader>
          <CardContent>
            {integrationParams?.credentials ? (
              <div className="space-y-4">
                <Button onClick={fetchData} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Loading data...
                    </>
                  ) : (
                    "Load Slack Data"
                  )}
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-muted-foreground">Connect to Slack to view your data</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {data && (
        <Tabs defaultValue="visualization" className="space-y-4">
          <TabsList>
            <TabsTrigger value="visualization">Visualization</TabsTrigger>
            <TabsTrigger value="channels">Channels</TabsTrigger>
            <TabsTrigger value="messages">Messages</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
          </TabsList>

          <TabsContent value="visualization">
            <DataVisualization data={data} />
          </TabsContent>

          <TabsContent value="channels">
            <Card>
              <CardHeader>
                <CardTitle>Slack Channels</CardTitle>
                <CardDescription>Your Slack channels</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Name</th>
                        <th className="p-2 text-left font-medium">Members</th>
                        <th className="p-2 text-left font-medium">Messages</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.channels.map((channel: any) => (
                        <tr key={channel.id} className="border-b">
                          <td className="p-2">#{channel.name}</td>
                          <td className="p-2">{channel.members}</td>
                          <td className="p-2">{channel.messages}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="messages">
            <Card>
              <CardHeader>
                <CardTitle>Recent Messages</CardTitle>
                <CardDescription>Recent messages from your Slack workspace</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Channel</th>
                        <th className="p-2 text-left font-medium">User</th>
                        <th className="p-2 text-left font-medium">Message</th>
                        <th className="p-2 text-left font-medium">Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.messages.map((message: any) => (
                        <tr key={message.id} className="border-b">
                          <td className="p-2">#{message.channel}</td>
                          <td className="p-2">{message.user}</td>
                          <td className="p-2">{message.text}</td>
                          <td className="p-2">{new Date(message.timestamp).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users">
            <Card>
              <CardHeader>
                <CardTitle>Slack Users</CardTitle>
                <CardDescription>Users in your Slack workspace</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Name</th>
                        <th className="p-2 text-left font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.users.map((user: any) => (
                        <tr key={user.id} className="border-b">
                          <td className="p-2">{user.name}</td>
                          <td className="p-2">
                            <span
                              className={`inline-block w-2 h-2 rounded-full mr-2 ${
                                user.status === "active" ? "bg-green-500" : "bg-yellow-500"
                              }`}
                            ></span>
                            {user.status}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}

