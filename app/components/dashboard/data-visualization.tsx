"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"

interface DataVisualizationProps {
  data: any
}

export function DataVisualization({ data }: DataVisualizationProps) {
  // Process data for visualization
  const getChartData = () => {
    if (!data) return []

    // For HubSpot
    if (data.contacts) {
      // Group contacts by company
      const companyGroups = data.contacts.reduce((acc: any, contact: any) => {
        const company = contact.company || "Unknown"
        if (!acc[company]) {
          acc[company] = 0
        }
        acc[company]++
        return acc
      }, {})

      return Object.entries(companyGroups).map(([name, value]) => ({
        name,
        value,
      }))
    }

    // For Notion
    if (data.pages || data.databases) {
      const pages = data.pages?.length || 0
      const databases = data.databases?.length || 0
      return [
        { name: "Pages", value: pages },
        { name: "Databases", value: databases },
      ]
    }

    // For Slack
    if (data.channels) {
      const publicChannels = data.channels.filter((c: any) => !c.is_private).length
      const privateChannels = data.channels.filter((c: any) => c.is_private).length
      return [
        { name: "Public Channels", value: publicChannels },
        { name: "Private Channels", value: privateChannels },
      ]
    }

    return []
  }

  const chartData = getChartData()
  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#82ca9d"]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Visualization</CardTitle>
        <CardDescription>Visual representation of your integration data</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              {chartData.length <= 5 ? (
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={true}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              ) : (
                <BarChart
                  data={chartData}
                  margin={{
                    top: 20,
                    right: 30,
                    left: 20,
                    bottom: 60,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={60} interval={0} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8">
                    {chartData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              )}
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-muted-foreground">No data available for visualization</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

