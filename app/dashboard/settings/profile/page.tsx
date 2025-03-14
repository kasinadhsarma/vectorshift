"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Icons } from "@/app/components/icons";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select";
import { getUserProfile, updateUserProfile, uploadProfileImage } from "@/app/lib/api-client";

interface Profile {
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  avatarUrl: string;
  company: string;
  jobTitle: string;
  timezone: string;
  preferences: Record<string, string>;
  fullName: string;
}

interface UserProfile {
  email: string;
  firstName?: string;
  lastName?: string;
  displayName?: string;
  avatarUrl?: string;
  company?: string;
  jobTitle?: string;
  timezone?: string;
  preferences?: Record<string, string>;
}

interface UploadResponse {
  imageUrl: string;
}

const timezones = [
  "UTC",
  "America/New_York",
  "America/Los_Angeles",
  "Europe/London",
  "Asia/Tokyo",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Australia/Sydney"
];

export default function ProfileSettingsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Partial<Profile>>({});
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [profile, setProfile] = useState<Profile>({
    email: "",
    fullName: "",
    firstName: "",
    lastName: "",
    displayName: "",
    avatarUrl: "",
    company: "",
    jobTitle: "",
    timezone: "UTC",
    preferences: {}
  });

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const email = localStorage.getItem('userEmail');
        if (!email) {
          throw new Error('User email not found');
        }

        const userProfile = (await getUserProfile(email)) as UserProfile;
        if (!userProfile) {
          throw new Error('User profile not found');
        }
        const profileData: Profile = {
          firstName: userProfile.firstName || "",
          lastName: userProfile.lastName || "",
          fullName: `${userProfile.firstName || ""} ${userProfile.lastName || ""}`.trim(),
          displayName: userProfile.displayName || "",
          avatarUrl: userProfile.avatarUrl || "",
          company: userProfile.company || "",
          jobTitle: userProfile.jobTitle || "",
          timezone: userProfile.timezone || "UTC",
          preferences: userProfile.preferences || {},
          email: email
        };
        setProfile(profileData);
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to load profile",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, [toast]);

  const validateForm = (): boolean => {
    const newErrors: Partial<Profile> = {};

    if (!profile.fullName?.trim()) {
      newErrors.fullName = "Name is required";
    }

    if (!profile.email?.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: "Error",
        description: "Image size should be less than 5MB",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);
      const { imageUrl: avatarUrl } = await uploadProfileImage(profile.email, file) as UploadResponse;
      setProfile({ ...profile, avatarUrl });

      await updateUserProfile(profile.email, { avatarUrl } as Partial<UserProfile>);

      toast({
        title: "Success",
        description: "Avatar uploaded successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to upload avatar",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast({
        title: "Error",
        description: "Please fix the errors in the form",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    const { fullName, ...updatedProfile } = profile;
    const [firstName, lastName] = fullName.split(' ');
    
    const profileData: Partial<UserProfile> = {
      ...updatedProfile,
      firstName,
      lastName
    };

    try {
      await updateUserProfile(profile.email, profileData as Partial<UserProfile>);
      toast({
        title: "Profile updated",
        description: "Your profile has been updated successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "There was an error updating your profile",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Icons.spinner className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Profile Settings</h1>
          <p className="text-muted-foreground">Manage your personal information and preferences</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Update your profile information and preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
              <div className="relative flex-shrink-0">
                <img
                  src={profile.avatarUrl || "/placeholder.svg"}
                  alt="Profile"
                  className="h-24 w-24 rounded-full object-cover border-2 border-muted"
                />
                {isSaving && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
                    <Icons.spinner className="h-6 w-6 animate-spin text-white" />
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Button variant="outline" type="button" onClick={handleAvatarClick} disabled={isSaving}>
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
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  value={profile.fullName}
                  onChange={(e) => {
                    setProfile({ ...profile, fullName: e.target.value });
                    if (errors.fullName) setErrors({ ...errors, fullName: undefined });
                  }}
                  className={errors.fullName ? "border-destructive" : ""}
                  disabled={isSaving}
                />
                {errors.fullName && <p className="text-sm text-destructive">{errors.fullName}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="displayName">Display Name</Label>
                <Input
                  id="displayName"
                  value={profile.displayName}
                  onChange={(e) => setProfile({ ...profile, displayName: e.target.value })}
                  disabled={isSaving}
                />
              </div>
            </div>

            <div className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={profile.email}
                  onChange={(e) => {
                    setProfile({ ...profile, email: e.target.value });
                    if (errors.email) setErrors({ ...errors, email: undefined });
                  }}
                  className={errors.email ? "border-destructive" : ""}
                  disabled={true}
                />
                {errors.email && <p className="text-sm text-destructive">{errors.email}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="company">Company</Label>
                <Input
                  id="company"
                  value={profile.company}
                  onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                  disabled={isSaving}
                />
              </div>
            </div>

            <div className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="jobTitle">Job Title</Label>
                <Input
                  id="jobTitle"
                  value={profile.jobTitle}
                  onChange={(e) => setProfile({ ...profile, jobTitle: e.target.value })}
                  disabled={isSaving}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Select
                  value={profile.timezone}
                  onValueChange={(value) => setProfile({ ...profile, timezone: value })}
                  disabled={isSaving}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select timezone" />
                  </SelectTrigger>
                  <SelectContent>
                    {timezones.map((tz) => (
                      <SelectItem key={tz} value={tz}>
                        {tz}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col-reverse sm:flex-row gap-4 sm:justify-end">
            <Button type="button" variant="outline" onClick={() => window.history.back()} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? (
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
  );
}