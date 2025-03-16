import axios from 'axios';

// Configure axios defaults
const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add auth token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for debugging
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data
    });
    return Promise.reject(error);
  }
);

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
  error?: string;
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
  const response = await api.get(`/users/${email}/profile`);
  return response.data;
}

export async function updateUserProfile(email: string, data: Partial<ProfileData>): Promise<ProfileData> {
  const response = await api.put(`/users/${email}/profile`, data);
  return response.data;
}

export async function uploadProfileImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data.url;
}

// Integration API Methods
export async function authorizeIntegration(provider: string, userId: string, orgId: string): Promise<string> {
  const response = await api.post(`/integrations/${provider}/authorize`, {
    user_id: userId,
    org_id: orgId
  });
  return response.data.url;
}

export async function getIntegrationStatus(provider: string, userId: string, orgId?: string): Promise<IntegrationStatus> {
  try {
    const response = await api.get(`/integrations/${provider}/status`, {
      params: { user_id: userId, org_id: orgId || userId }
    });
    return response.data;
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
  await api.post(`/integrations/${provider}/disconnect`, {
    user_id: userId,
    org_id: orgId || userId
  });
}

export async function syncIntegrationData(provider: string, userId: string, orgId?: string): Promise<void> {
  await api.post(`/integrations/${provider}/sync`, {
    user_id: userId,
    org_id: orgId
  });
}

// Integration-specific methods
export async function getNotionPages(workspaceId: string): Promise<NotionPage[]> {
  const response = await api.get(`/integrations/notion/pages`, {
    params: { workspaceId }
  });
  return response.data;
}

export async function getAirtableBases(workspaceId: string): Promise<AirtableBase[]> {
  const response = await api.get(`/integrations/airtable/bases`, {
    params: { workspaceId }
  });
  return response.data;
}

export async function getAirtableRecords(baseId: string, tableId: string): Promise<any[]> {
  const response = await api.get(`/integrations/airtable/records`, {
    params: { baseId, tableId }
  });
  return response.data;
}

export async function getSlackChannels(workspaceId: string): Promise<SlackChannel[]> {
  const response = await api.get(`/integrations/slack/channels`, {
    params: { workspaceId }
  });
  return response.data;
}

export async function getHubspotContacts(workspaceId: string): Promise<HubSpotContact[]> {
  const response = await api.get(`/integrations/hubspot/contacts`, {
    params: { workspaceId }
  });
  return response.data;
}

export async function getHubspotCompanies(workspaceId: string): Promise<HubSpotCompany[]> {
  const response = await api.get(`/integrations/hubspot/companies`, {
    params: { workspaceId }
  });
  return response.data;
}
