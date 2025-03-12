# Technical Paper: Backend and Frontend Architecture

## Backend Implementation using FastAPI

The backend of the project is implemented using FastAPI. The following are the key components and routes defined in the backend:

### Authentication Routes
- **File:** `backend/auth_routes.py`
- **Description:** This file contains the routes for user authentication, including signup, login, password reset, and token verification.

### Dashboard Routes
- **File:** `backend/routes/dashboard.py`
- **Description:** This file contains the routes for fetching and refreshing user-specific dashboard data, including integration statistics and sync data.

### Integration Routes
- **File:** `backend/routes/integrations.py`
- **Description:** This file contains the routes for handling OAuth authorization, fetching credentials, and syncing data for various third-party integrations like Notion, Airtable, Slack, and HubSpot.

### Profile Routes
- **File:** `backend/routes/profiles.py`
- **Description:** This file contains the routes for fetching and updating user profile information.

## Frontend Implementation using Next.js

The frontend of the project is implemented using Next.js. The following are the key components and their locations:

### Dashboard Components
- **File:** `app/components/dashboard/dashboard-content.tsx`
- **Description:** This file contains the main dashboard component that displays integration statistics, active integrations, and data visualization tabs.

- **File:** `app/components/dashboard/data-visualization.tsx`
- **Description:** This file contains the component for visualizing integration data in different formats like charts, tables, and metrics.

## Integration with Third-Party Services

The project integrates with various third-party services like Google, Airtable, Notion, Slack, and HubSpot. The integration logic is handled in the following files:

### Google Integration
- **File:** `backend/integrations/google_auth.py`
- **Description:** This file contains the logic for Google OAuth authentication, including generating the authorization URL, handling the callback, and fetching user information.

### Airtable Integration
- **File:** `backend/integrations/airtable.py`
- **Description:** This file contains the logic for Airtable OAuth authentication, including generating the authorization URL, handling the callback, and fetching bases and tables.

### Notion Integration
- **File:** `backend/integrations/notion.py`
- **Description:** This file contains the logic for Notion OAuth authentication, including generating the authorization URL, handling the callback, and fetching databases and pages.

### Slack Integration
- **File:** `backend/integrations/slack.py`
- **Description:** This file contains the logic for Slack OAuth authentication, including generating the authorization URL, handling the callback, and fetching channels.

### HubSpot Integration
- **File:** `backend/integrations/hubspot.py`
- **Description:** This file contains the logic for HubSpot OAuth authentication, including generating the authorization URL, handling the callback, and fetching contacts.

## Authentication Management using JWT Tokens

Authentication in the project is managed using JWT tokens. The middleware for handling JWT authentication is defined in the following file:

### JWT Middleware
- **File:** `backend/middleware.py`
- **Description:** This file contains the middleware for verifying JWT tokens, extracting user information, and handling CORS configuration.
