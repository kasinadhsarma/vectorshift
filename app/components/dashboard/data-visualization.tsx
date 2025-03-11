"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { Alert, AlertDescription, AlertTitle } from "@/app/components/ui/alert"
import { InfoIcon } from "lucide-react"

interface DataVisualizationProps {
  data: any
}

export function DataVisualization({ data }: DataVisualizationProps) {
  const [visualizationType, setVisualizationType] = useState("chart")

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Data Visualization</CardTitle>
          <CardDescription>Connect an integration to visualize your data</CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <InfoIcon className="h-4 w-4" />
            <AlertTitle>No data available</AlertTitle>
            <AlertDescription>Connect to an integration and load data to see visualizations.</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Data Visualization</CardTitle>
          <CardDescription>Visualize your integration data</CardDescription>
        </div>
        <Select value={visualizationType} onValueChange={setVisualizationType}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="chart">Chart</SelectItem>
            <SelectItem value="table">Table</SelectItem>
            <SelectItem value="metrics">Metrics</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="chart" value={visualizationType} onValueChange={setVisualizationType}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="chart">Chart</TabsTrigger>
            <TabsTrigger value="table">Table</TabsTrigger>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
          </TabsList>
          <TabsContent value="chart" className="space-y-4">
            <div className="rounded-lg border bg-muted/40 p-6">
              <div className="h-[300px] w-full">
                <div className="flex h-full items-center justify-center">
                  <div className="space-y-2 text-center">
                    <div className="text-lg font-medium">Chart Visualization</div>
                    <div className="text-sm text-muted-foreground">
                      {Array.isArray(data) ? `Showing ${data.length} records` : "Data visualization"}
                    </div>
                    <div className="flex justify-center gap-2">
                      {Array.isArray(data) &&
                        data.map((_, i) => (
                          <div
                            key={i}
                            className="bg-primary h-[100px] w-8 rounded-t-md"
                            style={{
                              height: `${Math.max(20, Math.random() * 150)}px`,
                              opacity: 0.6 + i * 0.1,
                            }}
                          />
                        ))}
                      {!Array.isArray(data) && (
                        <div className="flex gap-2">
                          <div
                            className="bg-primary h-[100px] w-8 rounded-t-md"
                            style={{ height: "120px", opacity: 0.7 }}
                          />
                          <div
                            className="bg-primary h-[100px] w-8 rounded-t-md"
                            style={{ height: "80px", opacity: 0.8 }}
                          />
                          <div
                            className="bg-primary h-[100px] w-8 rounded-t-md"
                            style={{ height: "150px", opacity: 0.9 }}
                          />
                          <div
                            className="bg-primary h-[100px] w-8 rounded-t-md"
                            style={{ height: "60px", opacity: 1 }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="table">
            <div className="rounded-md border">
              <div className="relative w-full overflow-auto">
                <table className="w-full caption-bottom text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="h-12 px-4 text-left align-middle font-medium">ID</th>
                      <th className="h-12 px-4 text-left align-middle font-medium">Name</th>
                      <th className="h-12 px-4 text-left align-middle font-medium">Value</th>
                      <th className="h-12 px-4 text-left align-middle font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.isArray(data)
                      ? data.map((item, i) => (
                          <tr key={i} className="border-b">
                            <td className="p-4 align-middle">{item.id || i + 1}</td>
                            <td className="p-4 align-middle">{item.name || `Item ${i + 1}`}</td>
                            <td className="p-4 align-middle">{item.value || Math.floor(Math.random() * 1000)}</td>
                            <td className="p-4 align-middle">
                              <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                  i % 3 === 0
                                    ? "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
                                    : i % 3 === 1
                                      ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400"
                                      : "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400"
                                }`}
                              >
                                {i % 3 === 0 ? "Active" : i % 3 === 1 ? "Pending" : "Inactive"}
                              </span>
                            </td>
                          </tr>
                        ))
                      : Array.from({ length: 5 }).map((_, i) => (
                          <tr key={i} className="border-b">
                            <td className="p-4 align-middle">{i + 1}</td>
                            <td className="p-4 align-middle">{`Sample ${i + 1}`}</td>
                            <td className="p-4 align-middle">{Math.floor(Math.random() * 1000)}</td>
                            <td className="p-4 align-middle">
                              <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                  i % 3 === 0
                                    ? "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
                                    : i % 3 === 1
                                      ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400"
                                      : "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400"
                                }`}
                              >
                                {i % 3 === 0 ? "Active" : i % 3 === 1 ? "Pending" : "Inactive"}
                              </span>
                            </td>
                          </tr>
                        ))}
                  </tbody>
                </table>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="metrics">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-muted-foreground">Total Records</div>
                <div className="text-2xl font-bold">{Array.isArray(data) ? data.length : 42}</div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-muted-foreground">Active</div>
                <div className="text-2xl font-bold">{Array.isArray(data) ? Math.floor(data.length * 0.6) : 25}</div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-muted-foreground">Pending</div>
                <div className="text-2xl font-bold">{Array.isArray(data) ? Math.floor(data.length * 0.3) : 12}</div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-muted-foreground">Inactive</div>
                <div className="text-2xl font-bold">{Array.isArray(data) ? Math.floor(data.length * 0.1) : 5}</div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

