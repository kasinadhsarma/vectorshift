import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { requiresAuth } from './lib/auth'

// This function can be marked `async` if using `await` inside
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check if the path requires authentication
  if (requiresAuth(pathname)) {
    const token = request.cookies.get('authToken')?.value || request.headers.get('authorization')?.replace('Bearer ', '')

    // If there's no token and trying to access protected route,
    // redirect to login page with return URL
    if (!token) {
      const url = new URL('/login', request.url)
      url.searchParams.set('returnUrl', pathname)
      return NextResponse.redirect(url)
    }

    // Add token to response headers for client access
    const response = NextResponse.next()
    response.headers.set('x-auth-token', token)
    return response
  }

  // If user is authenticated and tries to access auth pages (login, signup),
  // redirect to dashboard
  if (['/login', '/signup', '/forgot-password'].includes(pathname)) {
    const token = request.cookies.get('authToken')?.value || request.headers.get('authorization')?.replace('Bearer ', '')
    if (token) {
      const response = NextResponse.redirect(new URL('/dashboard', request.url))
      response.headers.set('x-auth-token', token)
      return response
    }
  }

  return NextResponse.next()
}

// Configure which routes to run middleware on
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/login',
    '/signup',
    '/forgot-password',
  ]
}
