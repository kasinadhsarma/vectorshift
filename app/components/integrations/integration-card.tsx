"use client"

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import { cn } from "@/lib/utils"
import type { ReactNode } from "react"

interface IntegrationCardProps {
  title: string
  description: string
  icon: ReactNode
  isConnected: boolean
  isActive: boolean
  onConnect: () => void
  onSelect: () => void
}

export function IntegrationCard({
  title,
  description,
  icon,
  isConnected,
  isActive,
  onConnect,
  onSelect,
}: IntegrationCardProps) {
  return (
    <Card className={cn("transition-all duration-200", isActive ? "ring-2 ring-primary" : "", "hover:shadow-md")}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-medium">{title}</CardTitle>
        <Badge variant={isConnected ? "default" : "outline"}>{isConnected ? "Connected" : "Disconnected"}</Badge>
      </CardHeader>
      <CardContent>
        <div className="flex items-center space-x-4">
          <div className="rounded-full bg-muted p-2">{icon}</div>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant={isConnected ? "destructive" : "default"} onClick={onConnect}>
          {isConnected ? "Disconnect" : "Connect"}
        </Button>
        <Button variant="outline" onClick={onSelect}>
          View Details
        </Button>
      </CardFooter>
    </Card>
  )
}

