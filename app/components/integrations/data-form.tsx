"use client"

import { useState } from "react"
import { Button } from "@/app/components/ui/button"
import { Textarea } from "@/app/components/ui/textarea"
import { Label } from "@/app/components/ui/label"
import { Loader2 } from "lucide-react"
import { useToast } from "@/app/components/ui/use-toast"
import axios from "axios"

const endpointMapping = {
  Notion: "notion",
  Airtable: "airtable",
  Hubspot: "hubspot",
  Slack: "slack",
}

interface DataFormProps {
  integrationType: keyof typeof endpointMapping
  credentials: any
  onDataLoaded?: (data: any) => void
}

export function DataForm({ integrationType, credentials, onDataLoaded }: DataFormProps) {
  const [loadedData, setLoadedData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  const endpoint = endpointMapping[integrationType]

  const handleLoad = async () => {
    try {
      setIsLoading(true)
      const formData = new FormData()
      formData.append("credentials", JSON.stringify(credentials))
      const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData)
      const data = response.data
      setLoadedData(data)
      if (onDataLoaded) {
        onDataLoaded(data)
      }
      toast({
        title: "Data loaded successfully",
        description: `Successfully loaded data from ${integrationType}`,
      })
    } catch (error: any) {
      toast({
        title: "Error loading data",
        description: error?.response?.data?.detail || "An unknown error occurred",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="loaded-data">Loaded Data</Label>
        <Textarea
          id="loaded-data"
          value={loadedData ? JSON.stringify(loadedData, null, 2) : ""}
          readOnly
          className="h-[200px] font-mono"
          placeholder="No data loaded yet"
        />
      </div>

      <div className="flex space-x-2">
        <Button onClick={handleLoad} disabled={isLoading} className="w-full md:w-auto">
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading...
            </>
          ) : (
            "Load Data"
          )}
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            setLoadedData(null)
            if (onDataLoaded) {
              onDataLoaded(null)
            }
          }}
          disabled={isLoading || !loadedData}
          className="w-full md:w-auto"
        >
          Clear Data
        </Button>
      </div>
    </div>
  )
}

