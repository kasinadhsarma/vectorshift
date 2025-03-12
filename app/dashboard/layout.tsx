"use client"

import type React from "react"
import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useGoogleAuth } from "@/app/components/auth/google-auth-provider"
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
  useSidebar,
} from "@/app/components/ui/sidebar"
import { ModeToggle } from "@/app/components/theme-toggle"
import { Button } from "@/app/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/app/components/ui/avatar"
import { Badge } from "@/app/components/ui/badge"
import {
  Bell,
  LayoutDashboard,
  Settings,
  LogOut,
  Users,
  BarChart3,
  FileSpreadsheet,
  MessageSquare,
  Lightbulb,
  Search,
  HelpCircle,
  Plus,
} from "lucide-react"
import Link from "next/link"
import { Input } from "@/app/components/ui/input"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/app/components/ui/dropdown-menu"

// Create a new component for the sidebar content
function SidebarContentComponent({ children }: { children: React.ReactNode }) {
  const { state } = useSidebar()
  const pathname = usePathname()
  const { user } = useGoogleAuth()
  const router = useRouter()
  const [currentUser, setCurrentUser] = useState<{ email?: string; name?: string } | null>(null)

  useEffect(() => {
    const userInfoStr = localStorage.getItem("userInfo")
    if (userInfoStr) {
      try {
        const userInfo = JSON.parse(userInfoStr)
        setCurrentUser(userInfo)
      } catch (e) {
        console.error("Error parsing user info:", e)
      }
    }
  }, [])

  // Get page title based on pathname
  const getPageTitle = () => {
    if (pathname === "/dashboard") return "Dashboard"
    if (pathname.includes("/integrations/notion")) return "Notion Integration"
    if (pathname.includes("/integrations/airtable")) return "Airtable Integration"
    if (pathname.includes("/integrations/hubspot")) return "Hubspot Integration"
    if (pathname.includes("/integrations/slack")) return "Slack Integration"
    if (pathname.includes("/settings/profile")) return "Profile Settings"
    if (pathname.includes("/settings/account")) return "Account Settings"
    return "Dashboard"
  }

  return (
    <>
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
              className="h-6 w-6 flex-shrink-0 text-primary"
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
            <Badge variant="outline" className="ml-1 hidden md:inline-flex" data-collapsed-hide>
              Beta
            </Badge>
          </div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel className="sr-only">Dashboard</SidebarGroupLabel>
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
            <SidebarGroupLabel className="sr-only">Integrations</SidebarGroupLabel>
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
                <SidebarMenuItem>
                  <SidebarMenuButton asChild tooltip="Add Integration">
                    <Button variant="ghost" className="w-full justify-start gap-2 px-2">
                      <Plus className="h-4 w-4" />
                      <span data-collapsed-hide>Add Integration</span>
                    </Button>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
          <SidebarGroup>
            <SidebarGroupLabel className="sr-only">Settings</SidebarGroupLabel>
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
                  <Avatar>
                    <AvatarImage src={user.picture ?? "/placeholder.svg?height=32&width=32"} alt={user.name || "User"} />
                    <AvatarFallback>{user.name ? user.name[0].toUpperCase() : "U"}</AvatarFallback>
                  </Avatar>
                  <div data-state={state} data-sidebar-expanded>
                    <p className="text-sm font-medium line-clamp-1">{user.name}</p>
                    <p className="text-xs text-muted-foreground line-clamp-1">{user.email}</p>
                  </div>
                </>
              ) : currentUser ? (
                // Regular user
                <>
                  <Avatar>
                    <AvatarFallback>
                      {currentUser.name
                        ? currentUser.name[0].toUpperCase()
                        : currentUser.email
                          ? currentUser.email[0].toUpperCase()
                          : "U"}
                    </AvatarFallback>
                  </Avatar>
                  <div data-state={state} data-sidebar-expanded>
                    <p className="text-sm font-medium line-clamp-1">{currentUser.name || currentUser.email}</p>
                    {currentUser.email && currentUser.name && (
                      <p className="text-xs text-muted-foreground line-clamp-1">{currentUser.email}</p>
                    )}
                  </div>
                </>
              ) : null}
            </div>
            <Button 
              variant="ghost" 
              size="icon" 
              className="rounded-full"
              onClick={() => {
                localStorage.removeItem("authToken")
                localStorage.removeItem("userInfo")
                localStorage.removeItem("googleUser")
                document.cookie = "authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;"
                router.replace("/login")
              }}
            >
              <LogOut className="h-4 w-4" />
              <span className="sr-only">Log out</span>
            </Button>
          </div>
        </SidebarFooter>
        <SidebarRail />
      </Sidebar>
      <SidebarInset>
        <div className="flex h-full flex-col">
          <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex h-16 items-center justify-between px-6">
              <div className="flex items-center gap-4">
                <SidebarTrigger />
                <h1 className="text-lg font-semibold">{getPageTitle()}</h1>
              </div>
              <div className="flex items-center gap-4">
                <Button variant="outline" size="icon" className="rounded-full">
                  <HelpCircle className="h-4 w-4" />
                  <span className="sr-only">Help</span>
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="icon" className="rounded-full">
                      <Bell className="h-4 w-4" />
                      <span className="sr-only">Notifications</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <div className="text-center py-2 px-4">
                      <p className="text-sm text-muted-foreground">No new notifications</p>
                    </div>
                  </DropdownMenuContent>
                </DropdownMenu>
                <ModeToggle />
              </div>
            </div>
          </header>
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </SidebarInset>
    </>
  )
}

// Main layout component
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  
  // Redirect if not authenticated
  useEffect(() => {
    const token = localStorage.getItem("authToken")
    if (!token && typeof window !== "undefined") {
      router.replace("/login")
    }
  }, [router])

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex min-h-screen">
        <SidebarContentComponent children={children} />
      </div>
    </SidebarProvider>
  )
}
