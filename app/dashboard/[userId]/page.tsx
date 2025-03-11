"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { useGoogleAuth } from "@/app/components/auth/google-auth-provider"
import { DashboardContent } from "@/app/components/dashboard/dashboard-content"
import { BACKEND_URL } from "@/app/components/auth/google-auth-config"

export default function UserDashboardPage() {
  const { userId } = useParams()
  const { user } = useGoogleAuth()
  const [userData, setUserData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchUserData = async () => {
      if (!user) return
      try {
        const token = localStorage.getItem("authToken")
        if (!token) {
          throw new Error("No auth token found")
        }

        const response = await fetch(`${BACKEND_URL}/api/users/${userId}/dashboard`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        })
        if (response.ok) {
          const data = await response.json()
          setUserData(data)
        }
      } catch (error) {
        console.error("Failed to fetch user dashboard data:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchUserData()
  }, [userId, user])

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!user) {
    return <div>Please log in to view your dashboard.</div>
  }

  return <DashboardContent userId={userId as string} userData={userData} />
}
