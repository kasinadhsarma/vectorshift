<<<<<<< HEAD
// API Client for profile and integration operations
import axios from 'axios';
=======
import axios from "axios"
>>>>>>> origin/main

export interface UserProfile {
  id: string
  name: string
  email: string
  image?: string
  bio?: string
}

<<<<<<< HEAD
const API_BASE_URL = 'http://localhost:8000/api';

// Profile Management
export async function getUserProfile(email: string): Promise<ProfileData> {
  const response = await fetch(`/api/users/${email}/profile`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch profile');
=======
export async function getUserProfile(userId: string): Promise<UserProfile> {
  try {
    const response = await axios.get(`/api/users/${userId}/profile`)
    return response.data
  } catch (error) {
    console.error('Error getting user profile:', error)
    throw new Error('Failed to get user profile')
>>>>>>> origin/main
  }
}

export async function uploadProfileImage(userId: string, file: File): Promise<{ imageUrl: string }> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await axios.post(`/api/users/${userId}/profile/image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error) {
    console.error('Error uploading profile image:', error)
    throw new Error('Failed to upload profile image')
  }
}

<<<<<<< HEAD
export async function uploadProfileImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to upload image');
=======
export async function updateUserProfile(userId: string, data: Partial<UserProfile>): Promise<UserProfile> {
  try {
    const response = await axios.patch(`/api/users/${userId}/profile`, data)
    return response.data
  } catch (error) {
    console.error('Error updating user profile:', error)
    throw new Error('Failed to update user profile')
>>>>>>> origin/main
  }
}

// Define types
export interface IntegrationStatus {
  isConnected: boolean
  status: "active" | "inactive" | "error"
  lastSync?: string
  error?: string
  credentials?: any
  workspace?: any
}

<<<<<<< HEAD
export interface AirtableBase {
  id: string;
  name: string;
  last_modified_time: string;
  type: 'base';
  url?: string;
}

export interface HubSpotContact {
  id: string;
  name: string;
  email?: string;
  company?: string;
  last_modified_time: string;
  type: 'contact';
}

export interface SlackChannel {
  id: string;
  name: string;
  visibility: boolean;
  creation_time?: string;
  type: 'channel';
}

interface IntegrationCredentials {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: string;
  workspaceId?: string;
  [key: string]: any;
}

// Generic Integration Methods
export async function authorizeIntegration(provider: string, userId: string, orgId: string): Promise<string> {
  const response = await axios.post(`${API_BASE_URL}/integrations/${provider}/authorize`, {
    userId,
    orgId
  });
  return response.data.url;
}

export async function getIntegrationStatus(provider: string, userId: string, orgId?: string): Promise<IntegrationStatus> {
  const response = await axios.get(`${API_BASE_URL}/integrations/${provider}/status`, {
    params: { user_id: userId, org_id: orgId }
  });
  return response.data;
}

export async function disconnectIntegration(provider: string, userId: string, orgId?: string): Promise<void> {
  await axios.post(`${API_BASE_URL}/integrations/${provider}/disconnect`, {
    user_id: userId,
    org_id: orgId
  });
}

export async function syncIntegrationData(provider: string, userId: string, orgId?: string): Promise<void> {
  await axios.post(`${API_BASE_URL}/integrations/${provider}/sync`, {
    user_id: userId,
    org_id: orgId
  });
}

export async function getIntegrationData(
  integrationType: string,
  credentials: any,
  userId: string,
  orgId?: string,
): Promise<any> {
  try {
    // Extract access token and ensure proper credentials structure
    let processedCredentials = null;

    if (typeof credentials === 'string') {
      try {
        processedCredentials = JSON.parse(credentials);
      } catch (e) {
        processedCredentials = { access_token: credentials };
      }
    } else if (credentials.credentials?.access_token) {
      processedCredentials = {
        access_token: credentials.credentials.access_token,
        ...credentials.credentials
      };
    } else if (credentials.access_token) {
      processedCredentials = credentials;
    } else {
      throw new Error('Invalid credentials format');
    }

    const response = await axios.post(`${API_BASE_URL}/integrations/${integrationType}/data`, {
      credentials: processedCredentials,
      userId,
      orgId,
    });

    return response.data;
  } catch (error) {
    console.error(`Error getting ${integrationType} data:`, error);
    const errorMessage = error instanceof Error ? error.message : `Failed to get ${integrationType} data`;
    throw new Error(errorMessage);
  }
}

// Integration-specific methods
export async function getNotionPages(workspaceId: string): Promise<NotionPage[]> {
  const response = await fetch(`/api/integrations/notion/pages?workspaceId=${workspaceId}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch Notion pages');
=======
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
>>>>>>> origin/main
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
