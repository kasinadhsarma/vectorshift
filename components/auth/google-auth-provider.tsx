"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/components/ui/use-toast"
import { apiGet } from "@/lib/api"

interface GoogleUser {
  sub: string
  name: string
  given_name: string
  family_name: string
  picture: string
  email: string
  email_verified: boolean
}

interface GoogleAuthContextType {
  user: GoogleUser | null
  isLoading: boolean
  login: () => Promise<void>
  logout: () => void
}

const GoogleAuthContext = createContext<GoogleAuthContextType | undefined>(undefined)

export function GoogleAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<GoogleUser | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { toast } = useToast()

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem("authToken") // Use same key as regular login
    if (token) {
      const userData = localStorage.getItem("googleUser")
      if (userData) {
        setUser(JSON.parse(userData))
      }
    }
  }, [])

  // Handle message from popup window
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.token && event.data.user) {
        // Store token and user data
        localStorage.setItem("authToken", event.data.token)  // Use same key as regular login
        localStorage.setItem("googleUser", JSON.stringify(event.data.user))

        // Update state
        setUser(event.data.user)
        setIsLoading(false)

        // Show success toast
        toast({
          title: "Authentication successful",
          description: `Welcome, ${event.data.user.name}!`,
        })

        // Redirect to dashboard
        router.push("/dashboard")
      }
    }

    window.addEventListener("message", handleMessage)
    return () => window.removeEventListener("message", handleMessage)
  }, [router, toast])

  const login = async () => {
    setIsLoading(true)

    try {
      const response = await apiGet("/auth/google/url")
      
      if (!response.url) {
        throw new Error("Failed to get authentication URL")
      }

      // Open popup for authentication
      const width = 500
      const height = 600
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2

      const popup = window.open(
        response.url,
        "Google Authentication",
        `width=${width},height=${height},left=${left},top=${top},scrollbars=yes`
      )

      // Check if popup was blocked
      if (!popup) {
        throw new Error("Popup was blocked. Please allow popups for this site.")
      }

      // Poll popup to detect when it closes
      const pollTimer = setInterval(() => {
        if (popup.closed) {
          clearInterval(pollTimer)
          setIsLoading(false)
        }
      }, 500)
    } catch (error) {
      setIsLoading(false)
      toast({
        title: "Authentication failed",
        description: "There was a problem authenticating with Google",
        variant: "destructive",
      })
    }
  }

  const logout = () => {
    localStorage.removeItem("authToken") // Use same key as regular login
    localStorage.removeItem("googleUser")
    setUser(null)
    router.push("/login")
    toast({
      title: "Logged out",
      description: "You have been logged out successfully",
    })
  }

  return <GoogleAuthContext.Provider value={{ user, isLoading, login, logout }}>{children}</GoogleAuthContext.Provider>
}

export function useGoogleAuth() {
  const context = useContext(GoogleAuthContext)
  if (context === undefined) {
    throw new Error("useGoogleAuth must be used within a GoogleAuthProvider")
  }
  return context
}
