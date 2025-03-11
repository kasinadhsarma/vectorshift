"use client"

import { useEffect } from "react"
import { usePathname, useSearchParams } from "next/navigation"

export function Analytics() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Path changed
    const url = pathname + searchParams.toString()

    // Example tracking code - replace with your actual analytics
    console.log(`Page view: ${url}`)

    // You would typically call your analytics service here
    // Example: gtag('config', 'GA_MEASUREMENT_ID', { page_path: url })
  }, [pathname, searchParams])

  return null
}

