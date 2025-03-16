"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Switch } from "@/app/components/ui/switch"
import { useToast } from "@/hooks/use-toast"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { TwoFactorSetup } from "@/app/components/auth/two-factor-auth"
import { Badge } from "@/app/components/ui/badge"
import { getIntegrationStatus, disconnectIntegration } from "@/app/lib/api-client"
import { Loader2, Check, X, FileSpreadsheet, BarChart3, MessageSquare, Lightbulb } from "lucide-react"
import axios from "axios"

interface Integration {
  id: string
  name: string
  isConnected: boolean
  icon: React.ReactNode
  status: 'active' | 'inactive' | 'error'
  lastSync?: string
}

export default function AccountSettingsPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isLoadingIntegrations, setIsLoadingIntegrations] = useState(true)
  const { toast } = useToast()
  const [settings, setSettings] = useState({
    emailNotifications: true,
    marketingEmails: false,
  })

  // Integrations list with their icons
  const INTEGRATIONS = [
    {
      id: 'notion',
      name: 'Notion',
      icon: <Lightbulb className="h-5 w-5 text-primary" />,
    },
    {
      id: 'airtable',
      name: 'Airtable',
      icon: <FileSpreadsheet className="h-5 w-5 text-primary" />,
    },
    {
      id: 'hubspot',
      name: 'HubSpot',
      icon: <BarChart3 className="h-5 w-5 text-primary" />,
    },
    {
      id: 'slack',
      name: 'Slack',
      icon: <MessageSquare className="h-5 w-5 text-primary" />,
    },
  ];

  // Load integration statuses on component mount
  useEffect(() => {
    const loadIntegrationStatuses = async () => {
      try {
        const userId = localStorage.getItem('userId')
        if (!userId) return

        const updatedIntegrations: Integration[] = await Promise.all(
          INTEGRATIONS.map(async (integration) => {
            try {
              const status = await getIntegrationStatus(integration.id, userId)
              
              return {
                ...integration,
                isConnected: status.isConnected,
                status: ['active', 'inactive', 'error'].includes(status.status) 
                  ? (status.status as 'active' | 'inactive' | 'error') 
                  : 'inactive',
                lastSync: status.lastSync,
              }
            } catch (error) {
              console.error(`Error fetching ${integration.name} status:`, error)
              return {
                ...integration,
                isConnected: false,
                status: 'error'
              }
            }
          })
        )

        setIntegrations(updatedIntegrations)
      } catch (error) {
        console.error('Error loading integration statuses:', error)
      } finally {
        setIsLoadingIntegrations(false)
      }
    }

    loadIntegrationStatuses()
  }, [])

  // Load user settings
  useEffect(() => {
    const loadUserSettings = async () => {
      try {
        const token = localStorage.getItem('authToken')
        if (!token) return

        // For demonstration - in a real app we would load actual settings from the API
        setSettings({
          emailNotifications: true,
          marketingEmails: false,
        })
      } catch (error) {
        console.error('Error loading user settings:', error)
      }
    }

    loadUserSettings()
  }, [])

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordLoading(true)

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      toast({
        title: "Passwords don't match",
        description: "Please make sure your new passwords match.",
        variant: "destructive",
      })
      setPasswordLoading(false)
      return
    }

    try {
      const token = localStorage.getItem('authToken')
      if (!token) throw new Error('Not authenticated')

      // In a real app, we would call the API to update the password
      await new Promise((resolve) => setTimeout(resolve, 1000))

      toast({
        title: "Password updated",
        description: "Your password has been updated successfully.",
      })

      // Reset form
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
    } catch (error) {
      toast({
        title: "Error",
        description: "There was an error updating your password.",
        variant: "destructive",
      })
    } finally {
      setPasswordLoading(false)
    }
  }

  const handleSettingsSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const token = localStorage.getItem('authToken')
      if (!token) throw new Error('Not authenticated')

      // In a real app, we would call the API to update the settings
      await new Promise((resolve) => setTimeout(resolve, 1000))

      toast({
        title: "Settings updated",
        description: "Your notification settings have been updated successfully.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "There was an error updating your settings.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleDisconnectIntegration = async (integrationId: string) => {
    try {
      const userId = localStorage.getItem('userId')
      if (!userId) throw new Error('User ID not found')

      // Disconnect the integration
      await disconnectIntegration(integrationId, userId)

      // Update the integration status in the state
      setIntegrations(prevIntegrations => 
        prevIntegrations.map(integration => 
          integration.id === integrationId
            ? { ...integration, isConnected: false, status: 'inactive' }
            : integration
        )
      )

      toast({
        title: "Integration disconnected",
        description: `The ${integrationId} integration has been disconnected.`,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to disconnect ${integrationId}.`,
        variant: "destructive",
      })
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <Badge
            variant="outline"
            className="bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
          >
            Connected
          </Badge>
        )
      case 'inactive':
        return (
          <Badge
            variant="outline"
            className="bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400"
          >
            Disconnected
          </Badge>
        )
      case 'error':
        return (
          <Badge
            variant="outline"
            className="bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400"
          >
            Error
          </Badge>
        )
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Account Settings</h1>
        <p className="text-muted-foreground">Manage your account preferences and security</p>
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
        </TabsList>
        
        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Settings</CardTitle>
              <CardDescription>Manage how you receive notifications</CardDescription>
            </CardHeader>
            <form onSubmit={handleSettingsSubmit}>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="email-notifications">Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive notifications about your account activity</p>
                  </div>
                  <Switch
                    id="email-notifications"
                    checked={settings.emailNotifications}
                    onCheckedChange={(checked) => setSettings({ ...settings, emailNotifications: checked })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="marketing-emails">Marketing Emails</Label>
                    <p className="text-sm text-muted-foreground">Receive emails about new features and offers</p>
                  </div>
                  <Switch
                    id="marketing-emails"
                    checked={settings.marketingEmails}
                    onCheckedChange={(checked) => setSettings({ ...settings, marketingEmails: checked })}
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-end">
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? "Saving..." : "Save Settings"}
                </Button>
              </CardFooter>
            </form>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Danger Zone</CardTitle>
              <CardDescription>Irreversible account actions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <h3 className="text-lg font-medium">Delete Account</h3>
                <p className="text-sm text-muted-foreground">
                  Once you delete your account, there is no going back. Please be certain.
                </p>
              </div>
            </CardContent>
            <CardFooter>
              <Button variant="destructive">Delete Account</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>Update your password to keep your account secure</CardDescription>
            </CardHeader>
            <form onSubmit={handlePasswordSubmit}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password">Current Password</Label>
                  <Input 
                    id="current-password" 
                    type="password" 
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new-password">New Password</Label>
                  <Input 
                    id="new-password" 
                    type="password" 
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm-password">Confirm New Password</Label>
                  <Input 
                    id="confirm-password" 
                    type="password" 
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-end">
                <Button type="submit" disabled={passwordLoading}>
                  {passwordLoading ? "Updating..." : "Update Password"}
                </Button>
              </CardFooter>
            </form>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Two-Factor Authentication</CardTitle>
              <CardDescription>Add an extra layer of security to your account</CardDescription>
            </CardHeader>
            <CardContent>
              <TwoFactorSetup />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Connected Services</CardTitle>
              <CardDescription>Manage your connected third-party services and integrations</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingIntegrations ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="space-y-4">
                  {integrations.map((integration) => (
                    <div key={integration.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="rounded-full bg-primary/10 p-2">
                          {integration.icon}
                        </div>
                        <div>
                          <h3 className="font-medium">{integration.name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {integration.isConnected
                              ? integration.lastSync
                                ? `Last synced: ${new Date(integration.lastSync).toLocaleDateString()}`
                                : "Connected"
                              : "Not connected"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {getStatusBadge(integration.status)}
                        {integration.isConnected ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDisconnectIntegration(integration.id)}
                          >
                            Disconnect
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.location.href = `/dashboard/integrations/${integration.id}`}
                          >
                            Connect
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

    </div>
  )
}
