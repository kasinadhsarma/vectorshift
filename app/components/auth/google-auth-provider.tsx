"use client"

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { GOOGLE_AUTH_URL } from "./google-auth-config"

interface GoogleAuthContextProps {
  user: {
    name: string | null
    email: string | null
    picture: string | null
  } | null
  isLoading: boolean
  login: () => Promise<void>
  logout: () => Promise<void>
}

const GoogleAuthContext = createContext<GoogleAuthContextProps | undefined>(undefined)

interface GoogleAuthProviderProps {
  children: ReactNode
}

export function GoogleAuthProvider({ children }: GoogleAuthProviderProps) {
  const [user, setUser] = useState<{ name: string | null; email: string | null; picture: string | null } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedUser = localStorage.getItem("googleUser")
      const token = localStorage.getItem("authToken")
      if (storedUser && token) {
        setUser(JSON.parse(storedUser))
      }
    }
  }, [])

  const handleAuthMessage = useCallback((event: MessageEvent) => {
    if (event.data?.token && event.data?.user) {
      const userData = {
        name: event.data.user.name,
        email: event.data.user.email,
        picture: event.data.user.picture,
      }
      setUser(userData)
      localStorage.setItem("googleUser", JSON.stringify(userData))
      localStorage.setItem("authToken", event.data.token)
      
      // Create a URL-safe user ID from email
      const userId = encodeURIComponent(userData.email.split('@')[0])
      router.push(`/dashboard/${userId}`)
    }
  }, [router])

  useEffect(() => {
    window.addEventListener("message", handleAuthMessage)
    return () => window.removeEventListener("message", handleAuthMessage)
  }, [handleAuthMessage])

  const login = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(GOOGLE_AUTH_URL)
      const { url } = await response.json()
      
      const width = 500
      const height = 600
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2

      window.open(
        url,
        "Google Auth",
        `width=${width},height=${height},left=${left},top=${top}`
      )
    } catch (error) {
      console.error("Failed to initiate Google login:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      setUser(null)
      localStorage.removeItem("googleUser")
      localStorage.removeItem("authToken")
      router.push("/")
    } finally {
      setIsLoading(false)
    }
  }

  return <GoogleAuthContext.Provider value={{ user, isLoading, login, logout }}>{children}</GoogleAuthContext.Provider>
}

export function useGoogleAuth() {
  const context = useContext(GoogleAuthContext)
  if (!context) {
    throw new Error("useGoogleAuth must be used within a GoogleAuthProvider")
  }
  return context
}
