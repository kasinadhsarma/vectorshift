"use client"

import type React from "react"
import { useState, useRef } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Textarea } from "@/app/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { Icons } from "@/app/components/icons"

interface Profile {
  name: string
  email: string
  bio: string
  avatar: string
}

export default function ProfileSettingsPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<Partial<Profile>>({})
  const { toast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [profile, setProfile] = useState<Profile>({
    name: "John Doe",
    email: "john@example.com",
    bio: "Product Manager with 5+ years of experience in SaaS products.",
    avatar: "/placeholder.svg?height=100&width=100",
  })

  const validateForm = (): boolean => {
    const newErrors: Partial<Profile> = {}

    if (!profile.name.trim()) {
      newErrors.name = "Name is required"
    }

    if (!profile.email.trim()) {
      newErrors.email = "Email is required"
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)) {
      newErrors.email = "Please enter a valid email address"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleAvatarClick = () => {
    fileInputRef.current?.click()
  }

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: "Error",
        description: "Image size should be less than 5MB",
        variant: "destructive",
      })
      return
    }

    try {
      const previewUrl = URL.createObjectURL(file)
      setProfile({ ...profile, avatar: previewUrl })

      // Simulated upload
      await new Promise((resolve) => setTimeout(resolve, 1000))

      toast({
        title: "Success",
        description: "Avatar uploaded successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to upload avatar",
        variant: "destructive",
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      toast({
        title: "Error",
        description: "Please fix the errors in the form",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)

    try {
      await new Promise((resolve) => setTimeout(resolve, 1000))
      toast({
        title: "Profile updated",
        description: "Your profile has been updated successfully.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "There was an error updating your profile.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Profile Settings</h1>
          <p className="text-muted-foreground">Manage your personal information</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Update your personal details and profile picture</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
              <div className="relative flex-shrink-0">
                <img
                  src={profile.avatar || "/placeholder.svg"}
                  alt="Profile"
                  className="h-24 w-24 rounded-full object-cover border-2 border-muted"
                />
                {isLoading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
                    <Icons.spinner className="h-6 w-6 animate-spin text-white" />
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Button variant="outline" type="button" onClick={handleAvatarClick} disabled={isLoading}>
                  Change Avatar
                </Button>
                <p className="text-sm text-muted-foreground">Max file size: 5MB. Supported formats: JPEG, PNG</p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png"
                className="hidden"
                onChange={handleAvatarChange}
              />
            </div>

            <div className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={profile.name}
                  onChange={(e) => {
                    setProfile({ ...profile, name: e.target.value })
                    if (errors.name) setErrors({ ...errors, name: undefined })
                  }}
                  className={errors.name ? "border-destructive" : ""}
                  disabled={isLoading}
                />
                {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={profile.email}
                  onChange={(e) => {
                    setProfile({ ...profile, email: e.target.value })
                    if (errors.email) setErrors({ ...errors, email: undefined })
                  }}
                  className={errors.email ? "border-destructive" : ""}
                  disabled={isLoading}
                />
                {errors.email && <p className="text-sm text-destructive">{errors.email}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bio">Bio</Label>
              <Textarea
                id="bio"
                rows={4}
                value={profile.bio}
                onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                placeholder="Tell us about yourself..."
                className="resize-none"
                disabled={isLoading}
              />
              <p className="text-sm text-muted-foreground">Brief description for your profile.</p>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col-reverse sm:flex-row gap-4 sm:justify-end">
            <Button type="button" variant="outline" onClick={() => window.history.back()} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}

