# VectorShift

VectorShift is a comprehensive platform that integrates various third-party services to provide a seamless experience for managing and visualizing data. The platform consists of a backend implemented using FastAPI and a frontend implemented using Next.js.

## Overview

The backend is responsible for handling authentication, managing integrations with third-party services, and providing APIs for the frontend. The frontend is responsible for providing a user-friendly interface for managing and visualizing data from the integrated services.

## Backend

The backend is implemented using FastAPI and consists of the following components:

- **Authentication**: Managed using JWT tokens, with routes defined in `backend/auth_routes.py`.
- **Dashboard**: Provides user-specific dashboard data, with routes defined in `backend/routes/dashboard.py`.
- **Integrations**: Handles integration with third-party services like Google, Airtable, Notion, Slack, and HubSpot, with routes defined in `backend/routes/integrations.py`.
- **Profiles**: Manages user profiles, with routes defined in `backend/routes/profiles.py`.
- **Middleware**: Authentication middleware defined in `backend/middleware.py`.

## Frontend

The frontend is implemented using Next.js and consists of the following components:

- **Dashboard**: Provides a user-friendly interface for managing and visualizing data from the integrated services, with components located in the `app/components/dashboard` directory.
- **Integrations**: Handles the integration process with third-party services, with components located in the `app/components/integrations` directory.
- **Authentication**: Manages user authentication, with components located in the `app/components/auth` directory.

## Setup Instructions

### Backend

1. Clone the repository:
   ```bash
   git clone https://github.com/kasinadhsarma/vectorshift.git
   cd vectorshift
   ```

2. Navigate to the backend directory:
   ```bash
   cd backend
   ```

3. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

6. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install the required dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```

## Usage Instructions

1. Open your browser and navigate to `http://localhost:3000` to access the frontend.
2. Sign up or log in to your account.
3. Connect your desired third-party services through the integrations page.
4. Manage and visualize your data through the dashboard.

For more detailed information, refer to the technical paper located in the `docs` directory.
