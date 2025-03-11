"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useGoogleAuth } from "@/components/auth/google-auth-provider"
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarInset,
  SidebarTrigger,
  SidebarRail,
} from "@/components/ui/sidebar"
import { ModeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import {
  LayoutDashboard,
  Settings,
  LogOut,
  Users,
  BarChart3,
  FileSpreadsheet,
  MessageSquare,
  Lightbulb,
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const { user, logout } = useGoogleAuth()
  const router = useRouter()

  // Redirect if not authenticated
  useEffect(() => {
    const token = localStorage.getItem("authToken")
    if (!token && typeof window !== "undefined") {
      router.replace("/login")
    }
  }, [router])

  // Get authentication information
  const [currentUser, setCurrentUser] = useState<{email?: string} | null>(null)
  
  useEffect(() => {
    const authToken = localStorage.getItem("authToken")
    if (!authToken && typeof window !== "undefined") {
      router.replace("/login")
      return
    }

    // Try to get user info from localStorage
    const userInfoStr = localStorage.getItem("userInfo")
    if (userInfoStr) {
      try {
        const userInfo = JSON.parse(userInfoStr)
        setCurrentUser(userInfo)
      } catch (e) {
        console.error("Error parsing user info:", e)
      }
    }
  }, [router])

  if (!currentUser && !user) {
    return null // Don't render anything until we have user information
  }

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex min-h-screen">
        <Sidebar variant="sidebar" collapsible="icon">
          <SidebarHeader className="border-b p-4">
            <div className="flex items-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-6 w-6 flex-shrink-0"
              >
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                <polyline points="14 2 14 8 20 8" />
                <path d="M8 13h2" />
                <path d="M8 17h2" />
                <path d="M14 13h2" />
                <path d="M14 17h2" />
              </svg>
              <span className="text-lg font-bold overflow-hidden transition-all duration-200" data-collapsed-hide>
                VectorAI Task
              </span>
            </div>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Dashboard</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === "/dashboard"} tooltip="Overview">
                      <Link href="/dashboard">
                        <LayoutDashboard className="h-4 w-4" />
                        <span data-collapsed-hide>Overview</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
            <SidebarGroup>
              <SidebarGroupLabel>Integrations</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      asChild
                      isActive={pathname === "/dashboard/integrations/notion"}
                      tooltip="Notion"
                    >
                      <Link href="/dashboard/integrations/notion">
                        <Lightbulb className="h-4 w-4" />
                        <span data-collapsed-hide>Notion</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      asChild
                      isActive={pathname === "/dashboard/integrations/airtable"}
                      tooltip="Airtable"
                    >
                      <Link href="/dashboard/integrations/airtable">
                        <FileSpreadsheet className="h-4 w-4" />
                        <span data-collapsed-hide>Airtable</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      asChild
                      isActive={pathname === "/dashboard/integrations/hubspot"}
                      tooltip="Hubspot"
                    >
                      <Link href="/dashboard/integrations/hubspot">
                        <BarChart3 className="h-4 w-4" />
                        <span data-collapsed-hide>Hubspot</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === "/dashboard/integrations/slack"} tooltip="Slack">
                      <Link href="/dashboard/integrations/slack">
                        <MessageSquare className="h-4 w-4" />
                        <span data-collapsed-hide>Slack</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
            <SidebarGroup>
              <SidebarGroupLabel>Settings</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === "/dashboard/settings/profile"} tooltip="Profile">
                      <Link href="/dashboard/settings/profile">
                        <Users className="h-4 w-4" />
                        <span data-collapsed-hide>Profile</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === "/dashboard/settings/account"} tooltip="Account">
                      <Link href="/dashboard/settings/account">
                        <Settings className="h-4 w-4" />
                        <span data-collapsed-hide>Account</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter className="border-t p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {user ? (
                  // Google user
                  <>
                    <img
                      src={user.picture || "/placeholder.svg?height=32&width=32"}
                      alt={user.name}
                      className="h-8 w-8 rounded-full"
                    />
                    <div className="overflow-hidden transition-all duration-200" data-collapsed-hide>
                      <p className="text-sm font-medium">{user.name}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                  </>
                ) : currentUser ? (
                  // Regular user
                  <>
                    <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                      {currentUser.email ? currentUser.email[0].toUpperCase() : "U"}
                    </div>
                    <div className="overflow-hidden transition-all duration-200" data-collapsed-hide>
                      <p className="text-sm font-medium">{currentUser.email}</p>
                    </div>
                  </>
                ) : null}
              </div>
              <Button variant="ghost" size="icon" onClick={() => {
                localStorage.removeItem("authToken")
                localStorage.removeItem("userInfo")
                localStorage.removeItem("googleUser")
                document.cookie = 'authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;'
                router.replace("/login")
              }}>
                <LogOut className="h-4 w-4" />
                <span className="sr-only">Log out</span>
              </Button>
            </div>
          </SidebarFooter>
          <SidebarRail />
        </Sidebar>
        <SidebarInset>
          <div className="flex h-full flex-col">
            <header className="border-b">
              <div className="flex h-16 items-center justify-between px-6">
                <div className="flex items-center gap-4">
                  <SidebarTrigger />
                  <h1 className="text-lg font-semibold">Dashboard</h1>
                </div>
                <div className="flex items-center gap-4">
                  <ModeToggle />
                </div>
              </div>
            </header>
            <main className="flex-1 overflow-auto p-6">{children}</main>
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
