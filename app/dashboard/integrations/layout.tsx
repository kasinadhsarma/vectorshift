"use client"

import { useParams } from "next/navigation"

export default function IntegrationsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const params = useParams()

  // If we get an invalid route, redirect to the dashboard
  if (typeof params?.provider === "object") {
    window.location.href = "/dashboard"
    return null
  }

  return <>{children}</>
}
