"use client"

import type React from "react"

import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface IntegrationCardProps {
  title: string
  description: string
  icon: React.ReactNode
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
    <Card
      className={cn("transition-all duration-200 hover:shadow-md", isActive && "ring-2 ring-primary")}
      onClick={onSelect}
    >
      <CardContent className="pt-6">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="p-2 rounded-full bg-primary/10">{icon}</div>
          <h3 className="font-semibold text-xl">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </CardContent>
      <CardFooter className="flex justify-center pb-6">
        <Button
          variant={isConnected ? "outline" : "default"}
          onClick={(e) => {
            e.stopPropagation()
            onConnect()
          }}
        >
          {isConnected ? "Disconnect" : "Connect"}
        </Button>
      </CardFooter>
    </Card>
  )
}

