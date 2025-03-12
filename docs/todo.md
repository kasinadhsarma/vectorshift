### **1️⃣ Setup the Project**  
- [x] **Install frontend dependencies**  
  - Navigate to the `/app` directory and run:  
    ```bash
    npm install
    npm run start
    ```
  - This ensures that all required frontend libraries are installed and the application runs correctly.

- [x] **Setup backend virtual environment**  
  - Navigate to the `/backend` directory and create a virtual environment:  
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux  
    venv\Scripts\activate     # On Windows  
    ```
  - Install dependencies:  
    ```bash
    pip install -r requirements.txt
    ```

- [x] **Install backend dependencies and run the server**  
  - Start the FastAPI server:  
    ```bash
    uvicorn main:app --reload
    ```
  - This launches the backend to handle API requests.

- [x] **Start Redis instance**  
  - Run the command:  
    ```bash
    redis-server
    ```
  - Redis is used for handling background tasks and caching.

---

### **2️⃣ Implement OAuth for All Integrations**  

#### **🔹 Notion OAuth Integration**  
- [ ] **Modify `notion.py` to implement OAuth authentication**  
  - Implement `authorize_notion()` → Redirects users to Notion's OAuth consent screen.  
  - Implement `oauth2callback_notion()` → Handles the OAuth callback and retrieves tokens.  
  - Implement `get_notion_credentials()` → Fetch stored credentials for authentication.  

- [ ] **Obtain client credentials from Notion**  
  - Sign up for a Notion developer account.  
  - Create an app and get the **Client ID & Client Secret** for OAuth authentication.  

- [ ] **Implement OAuth in frontend (`/app/dashboard/integrations/notion/page.tsx`)**  
  - Modify `notion/page.tsx` to enable user authentication via OAuth.  

#### **🔹 Airtable OAuth Integration**  
- [ ] **Modify `airtable.py` to implement OAuth authentication**  
  - Implement `authorize_airtable()` → Redirects users to Airtable's OAuth consent screen.  
  - Implement `oauth2callback_airtable()` → Handles the OAuth callback and retrieves tokens.  
  - Implement `get_airtable_credentials()` → Fetch stored credentials for authentication.  

- [ ] **Obtain client credentials from Airtable**  
  - Sign up for an Airtable developer account.  
  - Create an app and get the **Client ID & Client Secret** for OAuth authentication.  

- [ ] **Implement OAuth in frontend (`/app/dashboard/integrations/airtable/page.tsx`)**  
  - Modify `airtable/page.tsx` to enable user authentication via OAuth.  

#### **🔹 HubSpot OAuth Integration**  
- [ ] **Modify `hubspot.py` to implement OAuth authentication**  
  - Implement `authorize_hubspot()` → Redirects users to HubSpot's OAuth consent screen.  
  - Implement `oauth2callback_hubspot()` → Handles the OAuth callback and retrieves tokens.  
  - Implement `get_hubspot_credentials()` → Fetch stored credentials for authentication.  

- [ ] **Obtain client credentials from HubSpot**  
  - Sign up for a HubSpot developer account.  
  - Create an app and get the **Client ID & Client Secret** for OAuth authentication.  

- [ ] **Implement OAuth in frontend (`/app/dashboard/integrations/hubspot/page.tsx`)**  
  - Modify `hubspot/page.tsx` to enable user authentication via OAuth.  

#### **🔹 Slack OAuth Integration**  
- [ ] **Modify `slack.py` to implement OAuth authentication**  
  - Implement `authorize_slack()` → Redirects users to Slack's OAuth consent screen.  
  - Implement `oauth2callback_slack()` → Handles the OAuth callback and retrieves tokens.  
  - Implement `get_slack_credentials()` → Fetch stored credentials for authentication.  

- [ ] **Obtain client credentials from Slack**  
  - Sign up for a Slack developer account.  
  - Create an app and get the **Client ID & Client Secret** for OAuth authentication.  

- [ ] **Implement OAuth in frontend (`/app/dashboard/integrations/slack/page.tsx`)**  
  - Modify `slack/page.tsx` to enable user authentication via OAuth.  

---

### **3️⃣ Fetch & Display Data for All Integrations**  
- [ ] **Fetch and display Notion data**  
  - Implement `get_items_notion()` in `notion.py`.  
  - Use the Notion API to retrieve data and convert it into `IntegrationItem` objects.  
  - Verify that fetched data is correctly displayed in `/app/dashboard/integrations/notion/page.tsx`.  

- [ ] **Fetch and display Airtable data**  
  - Implement `get_items_airtable()` in `airtable.py`.  
  - Use the Airtable API to retrieve data and convert it into `IntegrationItem` objects.  
  - Verify that fetched data is correctly displayed in `/app/dashboard/integrations/airtable/page.tsx`.  

- [ ] **Fetch and display HubSpot data**  
  - Implement `get_items_hubspot()` in `hubspot.py`.  
  - Use the HubSpot API to retrieve data and convert it into `IntegrationItem` objects.  
  - Verify that fetched data is correctly displayed in `/app/dashboard/integrations/hubspot/page.tsx`.  

- [ ] **Fetch and display Slack data**  
  - Implement `get_items_slack()` in `slack.py`.  
  - Use the Slack API to retrieve data and convert it into `IntegrationItem` objects.  
  - Verify that fetched data is correctly displayed in `/app/dashboard/integrations/slack/page.tsx`.  

---

### **4️⃣ Final Testing & Debugging**  
- [ ] **Test OAuth authentication for all integrations**  
  - Ensure users can successfully authenticate via Notion, Airtable, HubSpot, and Slack.  

- [ ] **Verify API responses for all integrations**  
  - Check that data is being retrieved and displayed correctly.  

- [ ] **Fix any bugs or issues**  
  - Debug errors and refine code for better performance.  

---

### **5️⃣ Prepare Submission**  
- [ ] **Zip completed code**  
  - Name the zip file as `kasinadhsarma_Technical_Assessment.zip`.  

- [ ] **Record a walkthrough video**  
  - Explain your implementation, code structure, and demonstrate functionality.  
  - Save the file as `kasinadhsarma_ScreenRecording.mp4`.  

- [ ] **Submit via Google Form**  
  - Ensure submission is completed before **March 16, 11:59 PM IST**.  
