// API Client for profile and integration operations

interface ProfileData {
  email: string;
  fullName: string;
  displayName: string;
  avatarUrl: string;
  company: string;
  jobTitle: string;
  timezone: string;
  preferences: Record<string, string>;
  updatedAt?: string;
}

export async function getUserProfile(email: string): Promise<ProfileData> {
  const response = await fetch(`/api/users/${email}/profile`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch profile');
  }

  return response.json();
}

export async function updateUserProfile(email: string, data: Partial<ProfileData>): Promise<ProfileData> {
  const response = await fetch(`/api/users/${email}/profile`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update profile');
  }

  return response.json();
}

export async function uploadProfileImage(file: File): Promise<string> {
  // Create FormData
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
  }

  const data = await response.json();
  return data.url;
}

// Integration Types
export interface IntegrationStatus { // Added export
  isConnected: boolean;
  lastSync?: string;
  status: 'active' | 'inactive' | 'error';
  error?: string;
  credentials?: IntegrationCredentials;
}

interface IntegrationCredentials {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: string;
  workspaceId?: string;
  [key: string]: any;
}

// Integration API Methods
export async function authorizeIntegration(provider: string, userId: string, orgId: string): Promise<string> {
  const response = await fetch(`/integrations/${provider}/authorize`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ userId, orgId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to authorize ${provider}`);
  }

  const data = await response.json();
  return data.url;
}

export async function getIntegrationStatus(provider: string, userId: string): Promise<IntegrationStatus> {
  const response = await fetch(`/integrations/${provider}/status`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get ${provider} status`);
  }

  return response.json();
}

export async function disconnectIntegration(provider: string, userId: string): Promise<void> {
  const response = await fetch(`/integrations/${provider}/disconnect`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ userId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to disconnect ${provider}`);
  }
}

export async function syncIntegrationData(provider: string, userId: string): Promise<void> {
  const response = await fetch(`/integrations/${provider}/sync`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ userId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to sync ${provider} data`);
  }
}

// Integration-specific methods
export async function getNotionPages(workspaceId: string): Promise<any[]> {
  const response = await fetch(`/integrations/notion/pages?workspaceId=${workspaceId}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch Notion pages');
  }

  return response.json();
}

export async function getAirtableRecords(baseId: string, tableId: string): Promise<any[]> {
  const response = await fetch(`/integrations/airtable/records?baseId=${baseId}&tableId=${tableId}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch Airtable records');
  }

  return response.json();
}

export async function getSlackChannels(): Promise<any[]> {
  const response = await fetch('/integrations/slack/channels', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch Slack channels');
  }

  return response.json();
}

export async function getHubspotContacts(): Promise<any[]> {
  const response = await fetch('/integrations/hubspot/contacts', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch HubSpot contacts');
  }

  return response.json();
}
