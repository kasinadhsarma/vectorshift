"use client"

import { useState } from "react"
import { Card, CardContent } from "@/app/components/ui/card"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { AirtableIntegration } from "@/app/components/integrations/integration-types/airtable"
import { NotionIntegration } from "@/app/components/integrations/integration-types/notion"
import { HubspotIntegration } from "@/app/components/integrations/integration-types/hubspot"
import { SlackIntegration } from "@/app/components/integrations/integration-types/slack"
import { DataForm } from "@/app/components/integrations/data-form"

interface IntegrationFormProps {
  onIntegrationData: (data: any) => void
}

const integrationMapping = {
  Notion: NotionIntegration,
  Airtable: AirtableIntegration,
  Hubspot: HubspotIntegration,
  Slack: SlackIntegration,
}

export function IntegrationForm({ onIntegrationData }: IntegrationFormProps) {
  const [integrationParams, setIntegrationParams] = useState<any>({})
  const [user, setUser] = useState("TestUser")
  const [org, setOrg] = useState("TestOrg")
  const [currType, setCurrType] = useState<keyof typeof integrationMapping | null>(null)

  const CurrIntegration = currType ? integrationMapping[currType] : null

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="user">User</Label>
          <Input id="user" value={user} onChange={(e) => setUser(e.target.value)} placeholder="Enter user ID" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="organization">Organization</Label>
          <Input
            id="organization"
            value={org}
            onChange={(e) => setOrg(e.target.value)}
            placeholder="Enter organization ID"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="integration-type">Integration Type</Label>
        <Select onValueChange={(value: string) => setCurrType(value as keyof typeof integrationMapping)}>
          <SelectTrigger id="integration-type">
            <SelectValue placeholder="Select integration type" />
          </SelectTrigger>
          <SelectContent>
            {Object.keys(integrationMapping).map((type) => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {CurrIntegration && (
        <Card className="mt-6">
          <CardContent className="pt-6">
            <CurrIntegration
              user={user}
              org={org}
              integrationParams={integrationParams}
              setIntegrationParams={setIntegrationParams}
            />
          </CardContent>
        </Card>
      )}

      {integrationParams?.credentials && (
        <Card className="mt-6">
          <CardContent className="pt-6">
            <DataForm
              integrationType={integrationParams?.type}
              credentials={integrationParams?.credentials}
              onDataLoaded={onIntegrationData}
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

