import axios from "axios";

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  image?: string;
  bio?: string;
}

const API_BASE_URL = "http://localhost:8000/api";

// Profile Management
export async function getUserProfile(userId: string): Promise<UserProfile> {
  try {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/profile`);
    return response.data;
  } catch (error) {
    console.error("Error getting user profile:", error);
    throw new Error("Failed to get user profile");
  }
}

export async function uploadProfileImage(userId: string, file: File): Promise<{ imageUrl: string }> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await axios.post(`${API_BASE_URL}/users/${userId}/profile/image`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error uploading profile image:", error);
    throw new Error("Failed to upload profile image");
  }
}

export async function updateUserProfile(userId: string, data: Partial<UserProfile>): Promise<UserProfile> {
  try {
    const response = await axios.patch(`${API_BASE_URL}/users/${userId}/profile`, data);
    return response.data;
  } catch (error) {
    console.error("Error updating user profile:", error);
    throw new Error("Failed to update user profile");
  }
}

// Integration Types
export interface IntegrationStatus {
  isConnected: boolean;
  status: "active" | "inactive" | "error";
  lastSync?: string;
  error?: string;
  credentials?: any;
  workspace?: any;
}

// Generic Integration Methods
export async function authorizeIntegration(provider: string, userId: string, orgId?: string): Promise<string> {
  try {
    const response = await axios.post(`${API_BASE_URL}/integrations/${provider}/authorize`, {
      userId,
      orgId,
    });
    return response.data.url;
  } catch (error) {
    console.error(`Error authorizing ${provider}:`, error);
    throw new Error("Failed to authorize integration");
  }
}

export async function getIntegrationStatus(provider: string, userId: string, orgId?: string): Promise<IntegrationStatus> {
  try {
    const response = await axios.get(`${API_BASE_URL}/integrations/${provider}/status`, {
      params: { userId, orgId },
    });
    return response.data;
  } catch (error) {
    console.error(`Error getting ${provider} status:`, error);
    return {
      isConnected: false,
      status: "error",
      error: "Failed to get integration status",
    };
  }
}

export async function disconnectIntegration(provider: string, userId: string, orgId?: string): Promise<void> {
  try {
    await axios.post(`${API_BASE_URL}/integrations/${provider}/disconnect`, {
      userId,
      orgId,
    });
  } catch (error) {
    console.error(`Error disconnecting ${provider}:`, error);
    throw new Error("Failed to disconnect integration");
  }
}

export async function syncIntegrationData(provider: string, userId: string, orgId?: string): Promise<void> {
  try {
    await axios.post(`${API_BASE_URL}/integrations/${provider}/sync`, {
      userId,
      orgId,
    });
  } catch (error) {
    console.error(`Error syncing ${provider} data:`, error);
    throw new Error("Failed to sync integration data");
  }
}

export async function getIntegrationData(
  provider: string,
  credentials: any,
  userId: string,
  orgId?: string
): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE_URL}/integrations/${provider}/data`, {
      credentials,
      userId,
      orgId,
    });
    return response.data;
  } catch (error) {
    console.error(`Error getting ${provider} data:`, error);
    throw new Error(`Failed to get ${provider} data`);
  }
}
