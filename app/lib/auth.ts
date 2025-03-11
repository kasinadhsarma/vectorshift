export const getAuthToken = () => {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('authToken')
}

export const setAuthToken = (token: string) => {
  localStorage.setItem('authToken', token)
}

export const removeAuthToken = () => {
  localStorage.removeItem('authToken')
}

export const isAuthenticated = () => {
  const token = getAuthToken()
  return !!token
}

// Add authentication headers to fetch requests
export const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken()
  
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  // If we get a 401, clear the token and redirect to login
  if (response.status === 401) {
    removeAuthToken()
    window.location.href = '/login'
    return null
  }

  return response
}

// Function to check if the current route requires authentication
export const protectedRoutes = ['/dashboard']

export const requiresAuth = (pathname: string) => {
  return protectedRoutes.some(route => pathname.startsWith(route))
}
