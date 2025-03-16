// app/lib/api-client.ts

import { fetchWithAuth } from './auth';

// Interface definitions
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

export interface IntegrationItem {
  id: string;
  type: 'page' | 'database' | 'contact' | 'company' | 'base' | 'channel';
  name?: string;
  title?: string;
  lastEdited?: string;
  items?: number;
  email?: string;
  company?: string;
  domain?: string;
  industry?: string;
  last_modified_time?: string;
  visibility?: boolean;
  creation_time?: string;
  url?: string;
}

export interface NotionPage extends IntegrationItem {
  type: 'page';
  title?: string;
  lastEdited?: string;
  last_modified_time?: string;
}

export interface NotionDatabase extends IntegrationItem {
  type: 'database';
  name: string;
  items: number;
}

export interface AirtableBase extends IntegrationItem {
  type: 'base';
  name: string;
  last_modified_time: string;
  url?: string;
}

export interface HubSpotContact extends IntegrationItem {
  type: 'contact';
  name: string;
  email?: string;
  company?: string;
  last_modified_time: string;
}

export interface HubSpotCompany extends IntegrationItem {
  type: 'company';
  name: string;
  domain?: string;
  industry?: string;
  last_modified_time: string;
}

export interface SlackChannel extends IntegrationItem {
  type: 'channel';
  name: string;
  visibility: boolean;
  creation_time?: string;
}

export interface IntegrationStatus {
  isConnected: boolean;
  status: 'active' | 'inactive' | 'error';
  lastSync?: string;
  error?: string | null;
  credentials?: IntegrationCredentials;
  pages?: NotionPage[];
  databases?: NotionDatabase[];
  workspace?: Array<NotionPage | NotionDatabase | HubSpotContact | HubSpotCompany | AirtableBase | SlackChannel>;
}

interface IntegrationCredentials {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: string;
  workspaceId?: string;
  [key: string]: any;
}

// Profile API Methods
export async function getUserProfile(email: string): Promise<ProfileData> {
  const response = await fetchWithAuth(`/api/users/${email}/profile`);
  if (!response?.ok) {
    throw new Error('Failed to get user profile');
  }
  return await response.json();
}

export async function updateUserProfile(email: string, data: Partial<ProfileData>): Promise<ProfileData> {
  const response = await fetchWithAuth(`/api/users/${email}/profile`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  if (!response?.ok) {
    throw new Error('Failed to update user profile');
  }
  return await response.json();
}

export async function uploadProfileImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetchWithAuth('/api/upload', {
    method: 'POST',
    body: formData,
  });
  if (!response?.ok) {
    throw new Error('Failed to upload profile image');
  }
  const data = await response.json();
  return data.url;
}

// Integration API Methods
export async function authorizeIntegration(provider: string, userId: string, orgId: string): Promise<string> {
  const response = await fetchWithAuth(`/api/integrations/${provider}/authorize`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, org_id: orgId }),
  });
  if (!response?.ok) {
    throw new Error('Failed to authorize integration');
  }
  const data = await response.json();
  return data.url;
}

export async function getIntegrationStatus(provider: string, userId: string, orgId?: string): Promise<IntegrationStatus> {
  try {
    const response = await fetchWithAuth(`/api/integrations/${provider}/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    if (!response?.ok) {
      throw new Error('Failed to get integration status');
    }
    
    return await response.json();
  } catch (error) {
      console.error(`Failed to get ${provider} status:`, error);
      return {
        isConnected: false,
        status: 'error',
        error: error instanceof Error ? error.message : 'Failed to check integration status'
      };
  }
}

export async function disconnectIntegration(provider: string, userId: string, orgId?: string): Promise<void> {
  const response = await fetchWithAuth(`/api/integrations/${provider}/disconnect`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, org_id: orgId || userId }),
  });
  if (!response?.ok) {
    throw new Error('Failed to disconnect integration');
  }
}

export async function syncIntegrationData(provider: string, userId: string, orgId?: string): Promise<void> {
  const response = await fetchWithAuth(`/api/integrations/${provider}/sync`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, org_id: orgId }),
  });
  if (!response?.ok) {
    throw new Error('Failed to sync integration data');
  }
}

// Integration-specific methods
export async function getNotionPages(userId: string, orgId: string): Promise<NotionPage[]> {
  const url = new URL(`/api/integrations/notion/pages`, window.location.origin);
  url.search = new URLSearchParams({ user_id: userId, org_id: orgId }).toString();
  const response = await fetchWithAuth(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response?.ok) {
    throw new Error('Failed to get notion pages');
  }
  return await response.json();
}

export async function getAirtableBases(userId: string, orgId: string): Promise<AirtableBase[]> {
  const url = new URL(`/api/integrations/airtable/bases`, window.location.origin);
  url.search = new URLSearchParams({ user_id: userId, org_id: orgId }).toString();
  const response = await fetchWithAuth(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response?.ok) {
    throw new Error('Failed to get airtable bases');
  }
  return await response.json();
}

export async function getAirtableRecords(baseId: string, tableId: string): Promise<any[]> {
  const url = new URL(`/api/integrations/airtable/records`, window.location.origin);
  url.search = new URLSearchParams({ baseId, tableId }).toString();
  const response = await fetchWithAuth(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response?.ok) {
    throw new Error('Failed to get airtable records');
  }
  return await response.json();
}

export async function getSlackChannels(userId: string, orgId: string): Promise<SlackChannel[]> {
  const url = new URL(`/api/integrations/slack/channels`, window.location.origin);
  url.search = new URLSearchParams({ user_id: userId, org_id: orgId }).toString();
  const response = await fetchWithAuth(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response?.ok) {
    throw new Error('Failed to get slack channels');
  }
  return await response.json();
}

export async function getHubSpotContacts(userId: string, orgId: string): Promise<HubSpotContact[]> {
  const url = new URL(`/api/integrations/hubspot/contacts`, window.location.origin);
  url.search = new URLSearchParams({ user_id: userId, org_id: orgId }).toString();
  const response = await fetchWithAuth(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response?.ok) {
    throw new Error('Failed to get hubspot contacts');
  }
  return await response.json();
}

export async function getHubSpotCompanies(userId: string, orgId: string): Promise<HubSpotCompany[]> {
  const url = new URL(`/api/integrations/hubspot/companies`, window.location.origin);
  url.search = new URLSearchParams({ user_id: userId, org_id: orgId }).toString();
  const response = await fetchWithAuth(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response?.ok) {
    throw new Error('Failed to get hubspot companies');
  }
  return await response.json();
}