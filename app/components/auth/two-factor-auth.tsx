"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/app/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { hashUserId } from "@/app/lib/hash-utils"
import Image from "next/image"
import axios from "axios"

interface TwoFactorAuthProps {
  email: string
  onVerified: (token: string) => void
  onCancel: () => void
}

export function TwoFactorVerification({ email, onVerified, onCancel }: TwoFactorAuthProps) {
  const [code, setCode] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()
  const router = useRouter()

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      // Call the 2FA verification endpoint
      const response = await axios.post("http://localhost:8000/api/auth/2fa/login", {
        email,
        code
      })

      if (response.data.is_valid && response.data.token) {
        toast({
          title: "Verification successful",
          description: "You have successfully logged in with 2FA.",
        })
        onVerified(response.data.token)
      } else {
        setError("Invalid verification code")
        toast({
          title: "Verification failed",
          description: "Invalid verification code. Please try again.",
          variant: "destructive",
        })
      }
    } catch (err: any) {
      console.error("2FA verification error:", err)
      setError("Failed to verify code")
      toast({
        title: "Verification failed",
        description: "Failed to verify 2FA code. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold text-center">Two-Factor Authentication</CardTitle>
        <CardDescription className="text-center">
          Enter the verification code from your authenticator app
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleVerify} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="code">Verification Code</Label>
            <Input
              id="code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              autoComplete="one-time-code"
              placeholder="123456"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            {error && <p className="text-sm text-red-500">{error}</p>}
          </div>
          <Button type="submit" className="w-full" disabled={isLoading || code.length !== 6}>
            {isLoading ? "Verifying..." : "Verify"}
          </Button>
        </form>
      </CardContent>
      <CardFooter>
        <Button variant="ghost" className="w-full" onClick={onCancel}>
          Cancel
        </Button>
      </CardFooter>
    </Card>
  )
}

export function TwoFactorSetup() {
  const [qrCode, setQrCode] = useState<string | null>(null)
  const [secret, setSecret] = useState<string | null>(null)
  const [verificationCode, setVerificationCode] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [isEnabled, setIsEnabled] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    // Check if 2FA is already enabled
    const checkTwoFactorStatus = async () => {
      try {
        const token = localStorage.getItem("authToken")
        const userId = localStorage.getItem("userId")
        
        const response = await axios.get(`http://localhost:8000/api/auth/2fa/check?user_id=${userId || ''}`, {
          headers: token ? {
            Authorization: `Bearer ${token}`
          } : {}
        })

        setIsEnabled(response.data.is_enabled)
      } catch (err: any) {
        console.error("Failed to check 2FA status:", err)
      }
    }

    checkTwoFactorStatus()
  }, [])

  const handleSetup = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem("authToken")
      const userInfo = localStorage.getItem("userInfo")
      let user: any = null
      
      try {
        user = userInfo ? JSON.parse(userInfo) : null
      } catch (e) {
        console.error("Error parsing user info:", e)
      }
      
      const userId = user?.email || localStorage.getItem("userId")
      
      if (!userId) {
        throw new Error("User ID not found")
      }

      // Send token in multiple ways for flexibility
      const response = await axios.post(
        "http://localhost:8000/api/auth/2fa/setup",
        { user_id: userId, token },
        {
          headers: token ? {
            Authorization: `Bearer ${token}`
          } : {}
        }
      )

      setQrCode(response.data.qr_code_base64)
      setSecret(response.data.secret)
    } catch (err: any) {
      console.error("Failed to set up 2FA:", err)
      setError("Failed to set up two-factor authentication")
      toast({
        title: "Setup failed",
        description: err.response?.data?.detail || "Failed to set up two-factor authentication",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsVerifying(true)
    setError(null)

    try {
      const token = localStorage.getItem("authToken")
      const userInfo = localStorage.getItem("userInfo")
      let user: any = null
      
      try {
        user = userInfo ? JSON.parse(userInfo) : null
      } catch (e) {
        console.error("Error parsing user info:", e)
      }
      
      const userId = user?.email || localStorage.getItem("userId")
      
      if (!userId) {
        throw new Error("User ID not found")
      }

      const response = await axios.post(
        "http://localhost:8000/api/auth/2fa/verify",
        { code: verificationCode, user_id: userId, token },
        {
          headers: token ? {
            Authorization: `Bearer ${token}`
          } : {}
        }
      )

      if (response.data.is_valid) {
        setIsEnabled(true)
        setQrCode(null)
        setSecret(null)
        toast({
          title: "2FA Enabled",
          description: "Two-factor authentication has been successfully enabled.",
        })
      } else {
        setError("Invalid verification code")
        toast({
          title: "Verification failed",
          description: "Invalid verification code. Please try again.",
          variant: "destructive",
        })
      }
    } catch (err: any) {
      console.error("Failed to verify 2FA code:", err)
      setError("Failed to verify code")
      toast({
        title: "Verification failed",
        description: err.response?.data?.detail || "Failed to verify 2FA code",
        variant: "destructive",
      })
    } finally {
      setIsVerifying(false)
    }
  }

  const handleDisable = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem("authToken")
      const userInfo = localStorage.getItem("userInfo")
      let user: any = null
      
      try {
        user = userInfo ? JSON.parse(userInfo) : null
      } catch (e) {
        console.error("Error parsing user info:", e)
      }
      
      const userId = user?.email || localStorage.getItem("userId")

      await axios.post(
        "http://localhost:8000/api/auth/2fa/disable",
        { user_id: userId, token },
        {
          headers: token ? {
            Authorization: `Bearer ${token}`
          } : {}
        }
      )

      setIsEnabled(false)
      toast({
        title: "2FA Disabled",
        description: "Two-factor authentication has been disabled.",
      })
    } catch (err: any) {
      console.error("Failed to disable 2FA:", err)
      setError("Failed to disable two-factor authentication")
      toast({
        title: "Error",
        description: err.response?.data?.detail || "Failed to disable two-factor authentication",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (isEnabled) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Two-Factor Authentication</CardTitle>
          <CardDescription>
            Two-factor authentication is currently enabled for your account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-sm">
            You are using an authenticator app to generate verification codes for an extra layer of security.
          </p>
          <Button onClick={handleDisable} disabled={isLoading} variant="destructive">
            {isLoading ? "Disabling..." : "Disable Two-Factor Authentication"}
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (qrCode && secret) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Set Up Two-Factor Authentication</CardTitle>
          <CardDescription>
            Scan the QR code below with your authenticator app
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-center">
            <div className="border p-4 inline-block">
              <img 
                src={`data:image/png;base64,${qrCode}`} 
                alt="2FA QR Code" 
                width={200} 
                height={200} 
              />
            </div>
          </div>
          <div className="text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              If you can't scan the QR code, enter this code manually in your app:
            </p>
            <p className="font-mono bg-muted p-2 rounded text-center">{secret}</p>
          </div>
          <form onSubmit={handleVerify} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="verification-code">Verification Code</Label>
              <Input
                id="verification-code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                placeholder="Enter 6-digit code"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                required
              />
              {error && <p className="text-sm text-red-500">{error}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={isVerifying || verificationCode.length !== 6}>
              {isVerifying ? "Verifying..." : "Verify & Enable"}
            </Button>
          </form>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Two-Factor Authentication</CardTitle>
        <CardDescription>
          Add an extra layer of security to your account
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm">
          Two-factor authentication adds an additional layer of security to your account by requiring a verification 
          code from your authenticator app in addition to your password.
        </p>
        <div className="flex items-start space-x-4">
          <div className="p-2 bg-primary/10 rounded-full">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-6 w-6 text-primary"
            >
              <rect width="16" height="20" x="4" y="2" rx="2" ry="2" />
              <path d="M12 18h.01" />
            </svg>
          </div>
          <div>
            <h3 className="text-base font-medium">Use an authenticator app</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Use an app like Google Authenticator, Authy, or Microsoft Authenticator to generate verification codes.
            </p>
          </div>
        </div>
        <Button onClick={handleSetup} disabled={isLoading} className="w-full mt-4">
          {isLoading ? "Setting up..." : "Set Up Two-Factor Authentication"}
        </Button>
        {error && <p className="text-sm text-red-500">{error}</p>}
      </CardContent>
    </Card>
  )
}
