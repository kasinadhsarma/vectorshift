"use client"

import { useState } from "react"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent } from "@/app/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { useToast } from "@/hooks/use-toast"
import { FileSpreadsheet, Lightbulb, MessageSquare, BarChart3, Loader2 } from "lucide-react"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"

interface IntegrationFormProps {
  onIntegrationData: (data: any) => void
}

export function IntegrationForm({ onIntegrationData }: IntegrationFormProps) {
  const { toast } = useToast()
  const [selectedIntegration, setSelectedIntegration] = useState("notion")
  const [isConnecting, setIsConnecting] = useState(false)
  const [apiKey, setApiKey] = useState("")

  const handleConnect = async () => {
    if (!apiKey) {
      toast({
        title: "Error",
        description: `Please enter your ${getIntegrationName(selectedIntegration)} API key`,
        variant: "destructive",
      })
      return
    }

    setIsConnecting(true)

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Mock data based on integration
      let mockData

      switch (selectedIntegration) {
        case "notion":
          mockData = {
            pages: [
              { id: "page1", title: "Project Roadmap", lastEdited: "2023-05-15" },
              { id: "page2", title: "Meeting Notes", lastEdited: "2023-05-10" },
              { id: "page3", title: "Product Specs", lastEdited: "2023-05-05" },
            ],
            databases: [
              { id: "db1", title: "Tasks", items: 24 },
              { id: "db2", title: "Team Members", items: 8 },
            ],
          }
          break
        case "airtable":
          mockData = {
            bases: [
              { id: "base1", name: "Project Tracker", tables: 3 },
              { id: "base2", name: "Marketing Calendar", tables: 2 },
            ],
            tables: [
              { id: "table1", name: "Tasks", records: 45, baseId: "base1" },
              { id: "table2", name: "Team Members", records: 12, baseId: "base1" },
              { id: "table3", name: "Projects", records: 8, baseId: "base1" },
              { id: "table4", name: "Campaigns", records: 15, baseId: "base2" },
              { id: "table5", name: "Content Calendar", records: 30, baseId: "base2" },
            ],
          }
          break
        case "hubspot":
          mockData = [
            { id: 1, name: "John Doe", email: "john@example.com", company: "Acme Inc." },
            { id: 2, name: "Jane Smith", email: "jane@example.com", company: "Widget Co." },
            { id: 3, name: "Bob Johnson", email: "bob@example.com", company: "Tech Solutions" },
            { id: 4, name: "Alice Brown", email: "alice@example.com", company: "Acme Inc." },
            { id: 5, name: "Charlie Davis", email: "charlie@example.com", company: "Widget Co." },
          ]
          break
        case "slack":
          mockData = {
            channels: [
              { id: "C01", name: "general", members: 45, messages: 1250 },
              { id: "C02", name: "random", members: 42, messages: 980 },
              { id: "C03", name: "engineering", members: 15, messages: 2340 },
              { id: "C04", name: "marketing", members: 8, messages: 560 },
            ],
            users: [
              { id: "U01", name: "John Doe", status: "active" },
              { id: "U02", name: "Jane Smith", status: "active" },
              { id: "U03", name: "Bob Johnson", status: "away" },
            ],
          }
          break
        default:
          mockData = {}
      }

      onIntegrationData(mockData)

      toast({
        title: "Connected",
        description: `Successfully connected to ${getIntegrationName(selectedIntegration)}`,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to connect to ${getIntegrationName(selectedIntegration)}`,
        variant: "destructive",
      })
    } finally {
      setIsConnecting(false)
    }
  }

  const getIntegrationName = (key: string) => {
    switch (key) {
      case "notion":
        return "Notion"
      case "airtable":
        return "Airtable"
      case "hubspot":
        return "Hubspot"
      case "slack":
        return "Slack"
      default:
        return key
    }
  }

  const getIntegrationIcon = (key: string) => {
    switch (key) {
      case "notion":
        return <Lightbulb className="h-5 w-5" />
      case "airtable":
        return <FileSpreadsheet className="h-5 w-5" />
      case "hubspot":
        return <BarChart3 className="h-5 w-5" />
      case "slack":
        return <MessageSquare className="h-5 w-5" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="notion" value={selectedIntegration} onValueChange={setSelectedIntegration}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="notion">Notion</TabsTrigger>
          <TabsTrigger value="airtable">Airtable</TabsTrigger>
          <TabsTrigger value="hubspot">Hubspot</TabsTrigger>
          <TabsTrigger value="slack">Slack</TabsTrigger>
        </TabsList>
        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          {["notion", "airtable", "hubspot", "slack"].map((integration) => (
            <Card
              key={integration}
              className={`cursor-pointer transition-all ${
                selectedIntegration === integration ? "ring-2 ring-primary" : ""
              }`}
              onClick={() => setSelectedIntegration(integration)}
            >
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-2">{getIntegrationIcon(integration)}</div>
                  <div>
                    <div className="font-medium">{getIntegrationName(integration)}</div>
                    <div className="text-sm text-muted-foreground">
                      Connect to your {getIntegrationName(integration)} account
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="api-key">{getIntegrationName(selectedIntegration)} API Key</Label>
            <Input
              id="api-key"
              type="password"
              placeholder={`Enter your ${getIntegrationName(selectedIntegration)} API key`}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              You can find your API key in your {getIntegrationName(selectedIntegration)} account settings.
            </p>
          </div>
          <Button onClick={handleConnect} disabled={isConnecting || !apiKey}>
            {isConnecting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Connecting...
              </>
            ) : (
              `Connect to ${getIntegrationName(selectedIntegration)}`
            )}
          </Button>
        </div>
      </Tabs>
    </div>
  )
}

