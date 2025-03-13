import axios from "axios"

// Define types
export interface IntegrationStatus {
  isConnected: boolean
  status: "active" | "inactive" | "error"
  lastSync?: string
  error?: string
  credentials?: any
  workspace?: any
}

// Get integration status
export async function getIntegrationStatus(
  integrationType: string,
  userId: string,
  orgId?: string,
): Promise<IntegrationStatus> {
  try {
    const response = await axios.get(`/api/integrations/${integrationType}/status`, {
      params: { userId, orgId },
    })
    return response.data
  } catch (error) {
    console.error(`Error getting ${integrationType} status:`, error)
    return {
      isConnected: false,
      status: "error",
      error: "Failed to get integration status",
    }
  }
}

// Sync integration data
export async function syncIntegrationData(integrationType: string, userId: string, orgId?: string): Promise<any> {
  try {
    const response = await axios.post(`/api/integrations/${integrationType}/sync`, {
      userId,
      orgId,
    })
    return response.data
  } catch (error) {
    console.error(`Error syncing ${integrationType} data:`, error)
    throw new Error("Failed to sync integration data")
  }
}

// Authorize integration
export async function authorizeIntegration(
  integrationType: string,
  userId: string,
  orgId?: string,
): Promise<{ url: string }> {
  try {
    const response = await axios.post(`/api/integrations/${integrationType}/authorize`, {
      userId,
      orgId,
    })
    return response.data
  } catch (error) {
    console.error(`Error authorizing ${integrationType}:`, error)
    throw new Error("Failed to authorize integration")
  }
}

// Disconnect integration
export async function disconnectIntegration(integrationType: string, userId: string, orgId?: string): Promise<any> {
  try {
    const response = await axios.post(`/api/integrations/${integrationType}/disconnect`, {
      userId,
      orgId,
    })
    return response.data
  } catch (error) {
    console.error(`Error disconnecting ${integrationType}:`, error)
    throw new Error("Failed to disconnect integration")
  }
}

// Get integration data
export async function getIntegrationData(
  integrationType: string,
  credentials: any,
  userId: string,
  orgId?: string,
): Promise<any> {
  try {
    const response = await axios.post(`/api/integrations/${integrationType}/data`, {
      credentials,
      userId,
      orgId,
    })
    return response.data
  } catch (error) {
    console.error(`Error getting ${integrationType} data:`, error)
    throw new Error(`Failed to get ${integrationType} data`)
  }
}
