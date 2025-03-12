export interface NotionPage {
  id: string;
  title: string;
  lastEdited: string;
}

export interface NotionWorkspace {
  id: string;
  name: string;
  icon?: string;
  pages: NotionPage[];
}

export interface IntegrationStatus {
  isConnected: boolean;
  status: 'active' | 'inactive' | 'error';
  lastSync?: string;
  error?: string;
  workspace?: NotionWorkspace;
  credentials?: IntegrationCredentials;
}

export interface IntegrationCredentials {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: string;
  workspaceId?: string;
  [key: string]: any;
}
