"use client"

import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { 
  Boxes, 
  Database, 
  Hash, 
  Lightbulb,
} from "lucide-react"

const integrations = [
  {
    name: "Notion",
    href: "/dashboard/integrations/notion",
    icon: Lightbulb,
    description: "Connect and manage your Notion workspace, sync documents and databases.",
    status: "Ready to connect"
  },
  {
    name: "Airtable",
    href: "/dashboard/integrations/airtable",
    icon: Database,
    description: "Connect your Airtable bases and sync your data seamlessly.",
    status: "Ready to connect"
  },
  {
    name: "Slack",
    href: "/dashboard/integrations/slack",
    icon: Hash,
    description: "Connect to Slack and manage your workspace channels and messages.",
    status: "Ready to connect"
  },
  {
    name: "HubSpot",
    href: "/dashboard/integrations/hubspot",
    icon: Boxes,
    description: "Connect to HubSpot CRM and sync your contacts, companies, and deals.",
    status: "Ready to connect"
  }
]

export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {integrations.map((integration) => (
          <Link key={integration.href} href={integration.href}>
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
              <CardHeader className="flex flex-row items-center gap-4">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <integration.icon className="h-8 w-8 text-primary" />
                </div>
                <div>
                  <CardTitle>{integration.name}</CardTitle>
                  <CardDescription>{integration.status}</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {integration.description}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
