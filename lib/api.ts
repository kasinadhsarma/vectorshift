// API utility functions

/**
 * Make a POST request to the API
 */
export async function apiPost(endpoint: string, data: any) {
  try {
    // Get auth token from localStorage
    const token = localStorage.getItem("authToken")

    // In a real app, you would make an actual API call
    // For now, we'll simulate a response

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // Mock responses based on endpoint
    if (endpoint === "/integrations/hubspot/load") {
      return [
        { id: 1, name: "John Doe", email: "john@example.com", company: "Acme Inc." },
        { id: 2, name: "Jane Smith", email: "jane@example.com", company: "Widget Co." },
        { id: 3, name: "Bob Johnson", email: "bob@example.com", company: "Tech Solutions" },
        { id: 4, name: "Alice Brown", email: "alice@example.com", company: "Acme Inc." },
        { id: 5, name: "Charlie Davis", email: "charlie@example.com", company: "Widget Co." },
      ]
    }

    // Default response
    return { success: true, message: "Operation completed successfully" }
  } catch (error) {
    console.error("API error:", error)
    throw error
  }
}

/**
 * Make a GET request to the API
 */
export async function apiGet(endpoint: string) {
  try {
    // Get auth token from localStorage
    const token = localStorage.getItem("authToken")

    // In a real app, you would make an actual API call
    // For now, we'll simulate a response

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // Default response
    return { success: true, message: "Data retrieved successfully" }
  } catch (error) {
    console.error("API error:", error)
    throw error
  }
}

