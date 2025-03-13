"use client"

import { useState, useEffect } from "react"
import { getIntegrationStatus, getIntegrationData } from "@/app/lib/api-client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { HubspotIntegration } from "@/app/components/integrations/hubspot-integration"
import { BarChart3, RefreshCw } from "lucide-react"

export default function HubspotIntegrationPage() {
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [credentials, setCredentials] = useState<any>(null)

  // TODO: Replace with actual user and org data from auth context
  const userId = "user123"
  const orgId = "org456"

  useEffect(() => {
    // Check connection status on load
    const checkConnection = async () => {
      try {
        const status = await getIntegrationStatus("hubspot", userId, orgId)
        setIsConnected(status.isConnected)
        if (status.isConnected && status.credentials) {
          setCredentials(status.credentials)
        }
      } catch (error) {
        console.error("Error checking connection:", error)
      }
    }

    checkConnection()
  }, [userId, orgId])

  interface Contact {
    id: string;
    name: string;
    email: string;
    company: string;
  }

  interface Company {
    id: string;
    name: string;
    domain: string;
    industry: string;
    phone: string;
  }

  interface Deal {
    id: string;
    name: string;
    amount: string;
    stage: string;
    closeDate: string;
  }

  const fetchData = async () => {
    if (!credentials) return

    setIsLoading(true)
    setError(null)
    try {
      const hubspotData = await getIntegrationData("hubspot", credentials, userId, orgId)

      // Process the data
      const processedData: { contacts: Contact[], companies: Company[], deals: Deal[] } = {
        contacts: [],
        companies: [],
        deals: [],
      }

      // Process items based on their type
      hubspotData.forEach((item: any) => {
        const getParam = (name: string) => {
          const param = item.parameters?.find((p: any) => p.name === name)
          return param ? param.value : ""
        }

        if (item.type === "contact") {
          processedData.contacts.push({
            id: item.id,
            name: item.name,
            email: getParam("email"),
            company: getParam("company"),
          })
        } else if (item.type === "company") {
          processedData.companies.push({
            id: item.id,
            name: item.name,
            domain: getParam("domain"),
            industry: getParam("industry"),
            phone: getParam("phone"),
          })
        } else if (item.type === "deal") {
          processedData.deals.push({
            id: item.id,
            name: item.name,
            amount: getParam("amount"),
            stage: getParam("stage"),
            closeDate: getParam("closedate"),
          })
        }
      })

      setData(processedData)
    } catch (err) {
      console.error("Error fetching data:", err)
      setError(err instanceof Error ? err.message : "An unknown error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">HubSpot Integration</h1>
          <p className="text-muted-foreground">Connect and manage your HubSpot CRM data</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={fetchData} disabled={isLoading || !isConnected}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            <span className="sr-only">Refresh data</span>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center gap-4">
            <div className="p-2 rounded-full bg-primary/10">
              <BarChart3 className="h-8 w-8 text-primary" />
            </div>
            <div>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>Manage your HubSpot connection</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <HubspotIntegration userId={userId} orgId={orgId} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>HubSpot Data</CardTitle>
            <CardDescription>View and manage your HubSpot data</CardDescription>
          </CardHeader>
          <CardContent>
            {isConnected ? (
              <div className="space-y-4">
                <Button onClick={fetchData} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Loading data...
                    </>
                  ) : (
                    "Load HubSpot Data"
                  )}
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-muted-foreground">Connect to HubSpot to view your data</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {data && (
        <Tabs defaultValue="contacts" className="space-y-4">
          <TabsList>
            <TabsTrigger value="contacts">Contacts</TabsTrigger>
            <TabsTrigger value="companies">Companies</TabsTrigger>
            <TabsTrigger value="deals">Deals</TabsTrigger>
          </TabsList>

          <TabsContent value="contacts">
            <Card>
              <CardHeader>
                <CardTitle>HubSpot Contacts</CardTitle>
                <CardDescription>Your HubSpot contacts</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium">Name</th>
                        <th className="p-2 text-left font-medium">Email</th>
                        <th className="p-2 text-left font-medium">Company</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.contacts?.map((contact: any) => (
                        <tr key={contact.id} className="border-b">
                          <td className="p-2">{contact.name}</td>
                          <td className="p-2">{contact.email || "N/A"}</td>
                          <td className="p-2">{contact.company || "N/A"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="companies">
            <Card>
              <CardHeader>
                <CardTitle>HubSpot Companies</CardTitle>
                <CardDescription>Your HubSpot companies</CardDescription>
              </CardHeader>
              <CardContent>
                {data.companies && data.companies.length > 0 ? (
                  <div className="rounded-md border">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b bg-muted/50">
                          <th className="p-2 text-left font-medium">Name</th>
                          <th className="p-2 text-left font-medium">Domain</th>
                          <th className="p-2 text-left font-medium">Industry</th>
                          <th className="p-2 text-left font-medium">Phone</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.companies.map((company: any) => (
                          <tr key={company.id} className="border-b">
                            <td className="p-2">{company.name}</td>
                            <td className="p-2">{company.domain || "N/A"}</td>
                            <td className="p-2">{company.industry || "N/A"}</td>
                            <td className="p-2">{company.phone || "N/A"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-muted-foreground">No company data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="deals">
            <Card>
              <CardHeader>
                <CardTitle>HubSpot Deals</CardTitle>
                <CardDescription>Your HubSpot deals</CardDescription>
              </CardHeader>
              <CardContent>
                {data.deals && data.deals.length > 0 ? (
                  <div className="rounded-md border">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b bg-muted/50">
                          <th className="p-2 text-left font-medium">Name</th>
                          <th className="p-2 text-left font-medium">Amount</th>
                          <th className="p-2 text-left font-medium">Stage</th>
                          <th className="p-2 text-left font-medium">Close Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.deals.map((deal: any) => (
                          <tr key={deal.id} className="border-b">
                            <td className="p-2">{deal.name}</td>
                            <td className="p-2">{deal.amount || "N/A"}</td>
                            <td className="p-2">{deal.stage || "N/A"}</td>
                            <td className="p-2">{deal.closeDate || "N/A"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-muted-foreground">No deal data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}

