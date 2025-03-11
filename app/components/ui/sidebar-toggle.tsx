"use client"

import { Button } from "@/app/components/ui/button"
import { useSidebar } from "@/app/components/ui/sidebar"
import { PanelLeft } from "lucide-react"

export function SidebarToggle() {
  const { toggleSidebar } = useSidebar()

  return (
    <Button variant="ghost" size="icon" className="h-9 w-9 p-0" onClick={toggleSidebar} aria-label="Toggle Sidebar">
      <PanelLeft className="h-5 w-5" />
    </Button>
  )
}

