"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { NotionIntegration } from "@/components/integrations/notion-integration"
import { AirtableIntegration } from "@/components/integrations/airtable-integration"
import { HubspotIntegration } from "@/components/integrations/hubspot-integration"
import { SlackIntegration } from "@/components/integrations/slack-integration"

interface IntegrationFormProps {
  onIntegrationData: (data: any) => void
}

export function IntegrationForm({ onIntegrationData }: IntegrationFormProps) {
  const [activeTab, setActiveTab] = useState("notion")
  const [integrationParams, setIntegrationParams] = useState<any>({})

  // Mock user and org data - in a real app, this would come from auth context
  const user = "user123"
  const org = "org456"

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
      <TabsList className="grid grid-cols-4 w-full">
        <TabsTrigger value="notion">Notion</TabsTrigger>
        <TabsTrigger value="airtable">Airtable</TabsTrigger>
        <TabsTrigger value="hubspot">Hubspot</TabsTrigger>
        <TabsTrigger value="slack">Slack</TabsTrigger>
      </TabsList>
      <TabsContent value="notion">
        <NotionIntegration
          user={user}
          org={org}
          integrationParams={integrationParams}
          setIntegrationParams={setIntegrationParams}
        />
      </TabsContent>
      <TabsContent value="airtable">
        <AirtableIntegration
          user={user}
          org={org}
          integrationParams={integrationParams}
          setIntegrationParams={setIntegrationParams}
        />
      </TabsContent>
      <TabsContent value="hubspot">
        <HubspotIntegration
          user={user}
          org={org}
          integrationParams={integrationParams}
          setIntegrationParams={setIntegrationParams}
        />
      </TabsContent>
      <TabsContent value="slack">
        <SlackIntegration
          user={user}
          org={org}
          integrationParams={integrationParams}
          setIntegrationParams={setIntegrationParams}
        />
      </TabsContent>
    </Tabs>
  )
}

