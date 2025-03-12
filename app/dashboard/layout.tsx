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
  User,
  BarChart3,
  FileSpreadsheet,
  MessageSquare,
  Lightbulb,
  HelpCircle,
  Plus,
  ChevronDown,
} from "lucide-react"
import Link from "next/link"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/app/components/ui/dropdown-menu"

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
      <Sidebar variant="sidebar" collapsible="icon" className="border-r">
        <SidebarHeader className="border-b p-4">
          <div className="flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
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
            <div
              className="ml-2 transition-all duration-300 overflow-hidden whitespace-nowrap"
              data-state={state}
              style={{
                width: state === "collapsed" ? "0" : "auto",
                maxWidth: state === "collapsed" ? "0" : "150px",
                opacity: state === "collapsed" ? 0 : 1,
              }}
            >
              <span className="text-lg font-bold">VectorAI Task</span>
              <Badge variant="outline" className="ml-1 hidden md:inline-flex">
                Beta
              </Badge>
            </div>
          </div>
        </SidebarHeader>

        <SidebarContent className="px-2 py-2">
          <SidebarGroup>
            <SidebarGroupLabel className="px-2">Navigation</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={pathname === "/dashboard"} tooltip="Overview">
                    <Link href="/dashboard" className="flex items-center">
                      <LayoutDashboard className="h-4 w-4" />
                      <span className="ml-2">Overview</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          <SidebarGroup>
            <SidebarGroupLabel className="px-2">Integrations</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={pathname === "/dashboard/integrations/notion"} tooltip="Notion">
                    <Link href="/dashboard/integrations/notion" className="flex items-center">
                      <Lightbulb className="h-4 w-4" />
                      <span className="ml-2">Notion</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === "/dashboard/integrations/airtable"}
                    tooltip="Airtable"
                  >
                    <Link href="/dashboard/integrations/airtable" className="flex items-center">
                      <FileSpreadsheet className="h-4 w-4" />
                      <span className="ml-2">Airtable</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === "/dashboard/integrations/hubspot"}
                    tooltip="Hubspot"
                  >
                    <Link href="/dashboard/integrations/hubspot" className="flex items-center">
                      <BarChart3 className="h-4 w-4" />
                      <span className="ml-2">Hubspot</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={pathname === "/dashboard/integrations/slack"} tooltip="Slack">
                    <Link href="/dashboard/integrations/slack" className="flex items-center">
                      <MessageSquare className="h-4 w-4" />
                      <span className="ml-2">Slack</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild tooltip="Add Integration">
                    <Button variant="ghost" className="w-full justify-start gap-2 px-2">
                      <Plus className="h-4 w-4" />
                      <span className="ml-2">Add Integration</span>
                    </Button>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>

        <div className="mt-auto">
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <SidebarMenuButton className="w-full">
                        <div className="flex items-center gap-2">
                          <Avatar className="h-6 w-6">
                            <AvatarImage
                              src={user?.picture ?? "/placeholder.svg?height=24&width=24"}
                              alt={user?.name || "User"}
                            />
                            <AvatarFallback>{user?.name ? user.name[0].toUpperCase() : "U"}</AvatarFallback>
                          </Avatar>
                          <div
                            className="flex-1 overflow-hidden transition-all duration-300"
                            data-state={state}
                            style={{
                              maxWidth: state === "collapsed" ? "0" : "150px",
                              opacity: state === "collapsed" ? 0 : 1,
                            }}
                          >
                            <p className="truncate text-sm">{user?.name || "User"}</p>
                          </div>
                          <ChevronDown
                            className="h-4 w-4 opacity-50 transition-all duration-300"
                            data-state={state}
                            style={{
                              opacity: state === "collapsed" ? 0 : 0.5,
                              maxWidth: state === "collapsed" ? "0" : "16px",
                              overflow: "hidden",
                            }}
                          />
                        </div>
                      </SidebarMenuButton>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-56" align="start" side="right">
                      <DropdownMenuLabel>My Account</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <Link href="/dashboard/settings/profile">
                          <User className="mr-2 h-4 w-4" />
                          Profile
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href="/dashboard/settings/account">
                          <Settings className="mr-2 h-4 w-4" />
                          Settings
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => {
                          localStorage.removeItem("authToken")
                          localStorage.removeItem("userInfo")
                          localStorage.removeItem("googleUser")
                          document.cookie = "authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;"
                          router.replace("/login")
                        }}
                      >
                        <LogOut className="mr-2 h-4 w-4" />
                        Log out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </div>

        <SidebarRail />
      </Sidebar>

      <SidebarInset className="w-full max-w-full">
        <div className="flex h-full flex-col">
          <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex h-16 items-center justify-between px-4 md:px-6">
              <div className="flex items-center gap-2 md:gap-4">
                <SidebarTrigger />
                <h1 className="text-lg font-semibold truncate">{getPageTitle()}</h1>
              </div>
              <div className="flex items-center gap-2 md:gap-4">
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
          <main className="flex-1 overflow-x-hidden p-4 md:p-6">{children}</main>
        </div>
      </SidebarInset>
    </>
  )
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    const getCookieValue = (name: string) => {
      const value = `; ${document.cookie}`
      const parts = value.split(`; ${name}=`)
      if (parts.length === 2) return parts.pop()?.split(";").shift()
      return null
    }

    const sidebarState = getCookieValue("sidebar:state")
    // Only set the state if we have a valid cookie value
    if (sidebarState !== null) {
      setSidebarOpen(sidebarState === "true")
    }
  }, [])

  useEffect(() => {
    const token = localStorage.getItem("authToken")
    if (!token && typeof window !== "undefined") {
      router.replace("/login")
    }
  }, [router])

  const handleSidebarChange = (open: boolean) => {
    setSidebarOpen(open)
    // Set the cookie with a longer expiration and proper path
    document.cookie = `sidebar:state=${open}; path=/; max-age=${60 * 60 * 24 * 30}`
  }

  return (
    <SidebarProvider defaultOpen={sidebarOpen} open={sidebarOpen} onOpenChange={handleSidebarChange}>
      <div className="flex min-h-screen w-full overflow-hidden">
        <SidebarContentComponent children={children} />
      </div>
    </SidebarProvider>
  )
}

