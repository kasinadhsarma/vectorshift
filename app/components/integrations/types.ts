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

export interface NotionCredentials {
  access_token: string;
  bot_id: string;
  workspace_name?: string;
  workspace_id?: string;
  owner?: {
    user: {
      id: string;
      name?: string;
      avatar_url?: string;
      type?: 'person' | 'bot';
      person?: {
        email: string;
      };
    };
  };
}

export interface NotionState {
  state: string;
  user_id: string;
  org_id: string;
}

export interface IntegrationParams {
  credentials?: NotionCredentials;
  type?: 'Notion' | 'Airtable' | 'Hubspot' | 'Slack';
}

export interface IntegrationProps {
  user: string;
  org?: string;
  integrationParams?: IntegrationParams;
  setIntegrationParams: (params: IntegrationParams) => void;
}
