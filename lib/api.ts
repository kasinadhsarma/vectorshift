// API utility functions for making requests to the backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

/**
 * Makes a GET request to the API
 */
export async function apiGet(endpoint: string) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

/**
 * Makes a POST request to the API
 */
export async function apiPost(endpoint: string, data: any) {
  const formData = new FormData()

  // Convert data object to FormData
  Object.keys(data).forEach((key) => {
    formData.append(key, data[key])
  })

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    body: formData,
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

