import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Get the pathname
  const path = request.nextUrl.pathname

  // Handle integration routes
  if (path.startsWith('/dashboard/integrations/')) {
    const segments = path.split('/')
    // If we have an object in the URL, redirect to dashboard
    if (segments[3] && segments[3].includes('[object')) {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
  }

  // Continue with the request if no issues
  return NextResponse.next()
}

export const config = {
  matcher: [
    // Match all dashboard/integrations routes
    '/dashboard/integrations/:path*',
  ],
}
