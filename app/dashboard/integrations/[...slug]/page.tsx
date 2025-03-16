"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function CatchAllPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to the main integrations page
    router.replace("/dashboard/integrations")
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">Redirecting...</h2>
        <p className="text-muted-foreground">
          Taking you back to the integrations dashboard
        </p>
      </div>
    </div>
  )
}
