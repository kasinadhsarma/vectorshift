"use client"

import { useState, useEffect } from "react"
import axios, { type AxiosError } from "axios"
import { Button } from "@/app/components/ui/button"
import { Loader2 } from "lucide-react"
import { getIntegrationStatus, getIntegrationData } from "@/app/lib/api-client"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"

interface IntegrationParams {
  credentials?: Record<string, any>
  type?: string
}

interface AuthResponse {
  url: string
}

interface ErrorResponse {
  detail: string
}

interface ContactData {
  id: number | string
  name: string
  email: string
  company: string
}

interface CompanyData {
  id: number | string
  name: string
  domain: string
  industry: string
  phone: string
}

interface DealData {
  id: number | string
  name: string
  amount: string
  stage: string
  closeDate: string
}

interface HubSpotData {
  contacts: ContactData[]
  companies: CompanyData[]
  deals: DealData[]
}

interface HubSpotIntegrationProps {
  userId: string
  orgId: string
}

export const HubspotIntegration = ({ userId, orgId }: HubSpotIntegrationProps) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [hubspotData, setHubspotData] = useState<HubSpotData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("contacts")
  const [credentials, setCredentials] = useState<any>(null)

  useEffect(() => {
    // Check if already connected
    const checkConnection = async () => {
      try {
        const status = await getIntegrationStatus("hubspot", userId, orgId)
        setIsConnected(status.isConnected)
        if (status.isConnected && status.credentials) {
          setCredentials(status.credentials)
          fetchHubSpotData(status.credentials)
        }
      } catch (error) {
        console.error("Error checking connection:", error)
      }
    }

    checkConnection()
  }, [userId, orgId])

  const handleConnectClick = async () => {
    if (!userId || !orgId) {
      alert("Missing user or organization ID")
      return
    }

    try {
      setIsConnecting(true)
      const response = await axios.post<AuthResponse>(
        `/api/integrations/hubspot/authorize`,
        { userId, orgId },
        { headers: { "Content-Type": "application/json" } },
      )

      if (!response.data?.url) {
        throw new Error("Invalid authorization URL")
      }

      const newWindow = window.open(
        response.data.url,
        "HubSpot Authorization",
        "width=600,height=600,menubar=no,toolbar=no",
      )

      if (!newWindow) {
        throw new Error("Popup was blocked. Please allow popups and try again.")
      }

      const pollTimer = window.setInterval(() => {
        if (newWindow.closed) {
          window.clearInterval(pollTimer)
          handleWindowClosed()
        }
      }, 200)
    } catch (e) {
      setIsConnecting(false)
      const error = e as AxiosError<ErrorResponse>
      console.error("Authorization error:", error)
      alert(error.response?.data?.detail || "Failed to connect to HubSpot")
    }
  }

  const handleWindowClosed = async () => {
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000))

      const status = await getIntegrationStatus("hubspot", userId, orgId)
      if (status.isConnected) {
        setIsConnected(true)
        setCredentials(status.credentials)
        fetchHubSpotData(status.credentials)
      } else {
        throw new Error("Failed to connect to HubSpot")
      }
    } catch (e) {
      setIsConnecting(false)
      const error = e as AxiosError<ErrorResponse>
      console.error("Connection error:", error)
      alert(error.response?.data?.detail || "Failed to connect to HubSpot")
    } finally {
      setIsConnecting(false)
    }
  }

  const fetchHubSpotData = async (creds?: any) => {
    const credsToUse = creds || credentials
    if (!credsToUse) return

    try {
      setIsLoading(true)
      const data = await getIntegrationData("hubspot", credsToUse, userId, orgId)

      // Process the data to match the expected format
      const processedData: HubSpotData = {
        contacts: [],
        companies: [],
        deals: [],
      }

      // Process items based on their type
      data.forEach((item: any) => {
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

      setHubspotData(processedData)
    } catch (error) {
      console.error("Failed to fetch HubSpot data:", error)
      alert("Failed to fetch HubSpot data")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="mt-4">
      <div className="flex flex-col items-center gap-4">
        <Button
          variant={isConnected ? "outline" : "default"}
          onClick={isConnected ? undefined : handleConnectClick}
          disabled={isConnecting}
          className={isConnected ? "cursor-default opacity-100" : ""}
        >
          {isConnecting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Connecting...
            </>
          ) : isConnected ? (
            "Connected to HubSpot"
          ) : (
            "Connect to HubSpot"
          )}
        </Button>

        {isConnected && hubspotData && (
          <div className="w-full">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="contacts">Contacts</TabsTrigger>
                <TabsTrigger value="companies">Companies</TabsTrigger>
                <TabsTrigger value="deals">Deals</TabsTrigger>
              </TabsList>

              <TabsContent value="contacts" className="mt-4">
                <h4 className="font-medium mb-2">Contacts</h4>
                <div className="space-y-2">
                  {hubspotData.contacts && hubspotData.contacts.length > 0 ? (
                    hubspotData.contacts.map((contact) => (
                      <div key={contact.id} className="p-2 border rounded">
                        <p className="font-medium">{contact.name}</p>
                        <p className="text-sm text-gray-500">{contact.email}</p>
                        <p className="text-sm text-gray-500">{contact.company}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-gray-500">No contacts found</p>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="companies" className="mt-4">
                <h4 className="font-medium mb-2">Companies</h4>
                <div className="space-y-2">
                  {hubspotData.companies && hubspotData.companies.length > 0 ? (
                    hubspotData.companies.map((company) => (
                      <div key={company.id} className="p-2 border rounded">
                        <p className="font-medium">{company.name}</p>
                        <p className="text-sm text-gray-500">Domain: {company.domain}</p>
                        <p className="text-sm text-gray-500">Industry: {company.industry}</p>
                        <p className="text-sm text-gray-500">Phone: {company.phone}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-gray-500">No companies found</p>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="deals" className="mt-4">
                <h4 className="font-medium mb-2">Deals</h4>
                <div className="space-y-2">
                  {hubspotData.deals && hubspotData.deals.length > 0 ? (
                    hubspotData.deals.map((deal) => (
                      <div key={deal.id} className="p-2 border rounded">
                        <p className="font-medium">{deal.name}</p>
                        <p className="text-sm text-gray-500">Amount: {deal.amount}</p>
                        <p className="text-sm text-gray-500">Stage: {deal.stage}</p>
                        <p className="text-sm text-gray-500">Close Date: {deal.closeDate}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-gray-500">No deals found</p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        )}
      </div>
    </div>
  )
}

