"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { InfoIcon } from "lucide-react"

interface DataVisualizationProps {
  data: any
}

export function DataVisualization({ data }: DataVisualizationProps) {
  const [visualizationType, setVisualizationType] = useState("json")

  if (!data) {
    return (
      <Alert>
        <InfoIcon className="h-4 w-4" />
        <AlertTitle>No data available</AlertTitle>
        <AlertDescription>Connect to an integration and load data to visualize it here.</AlertDescription>
      </Alert>
    )
  }

  // Format data for visualization
  const formattedData = typeof data === "object" ? JSON.stringify(data, null, 2) : String(data)

  // Mock data for table view - in a real app, you'd parse the actual data
  const tableData = Array.isArray(data)
    ? data
    : typeof data === "object"
      ? Object.entries(data).map(([key, value]) => ({ key, value: JSON.stringify(value) }))
      : [{ key: "data", value: String(data) }]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Visualization</CardTitle>
        <CardDescription>Visualize your integration data in different formats</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="json" value={visualizationType} onValueChange={setVisualizationType} className="space-y-4">
          <TabsList>
            <TabsTrigger value="json">JSON</TabsTrigger>
            <TabsTrigger value="table">Table</TabsTrigger>
            <TabsTrigger value="chart">Chart</TabsTrigger>
          </TabsList>

          <TabsContent value="json" className="space-y-4">
            <div className="rounded-md bg-muted p-4">
              <pre className="text-sm font-mono overflow-auto max-h-[400px]">{formattedData}</pre>
            </div>
          </TabsContent>

          <TabsContent value="table" className="space-y-4">
            <div className="rounded-md border">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="p-2 text-left font-medium">Key</th>
                    <th className="p-2 text-left font-medium">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {tableData.map((row, index) => (
                    <tr key={index} className="border-b">
                      <td className="p-2 font-mono text-sm">{row.key}</td>
                      <td className="p-2 font-mono text-sm truncate max-w-[300px]">{row.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TabsContent>

          <TabsContent value="chart" className="space-y-4">
            <div className="flex items-center justify-center h-[400px] bg-muted/20 rounded-md">
              <div className="text-center">
                <p className="text-muted-foreground">Chart visualization would be rendered here</p>
                <p className="text-xs text-muted-foreground mt-2">
                  For a complete implementation, you would use a charting library like Chart.js or Recharts
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

