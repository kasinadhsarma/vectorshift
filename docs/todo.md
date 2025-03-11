### ✅ **VectorShift Technical Assessment - To-Do List**  

#### **1️⃣ Setup the Project**  
- [x] **Install frontend dependencies**  
  - Navigate to the `/app` directory and run:  
    ```bash
    npm install
    npm run start
    ```
  - This ensures that all required frontend libraries are installed and the application runs correctly.

- [x] **Install backend dependencies and run the server**  
  - Navigate to the `/backend` directory and run:  
    ```bash
    uvicorn main:app --reload
    ```
  - This starts the FastAPI backend server to handle API requests.

- [ ] **Start Redis instance**  
  - Run the command:  
    ```bash
    redis-server
    ```
  - Redis is used for handling background tasks and caching.

#### **2️⃣ Implement HubSpot OAuth Integration**  
- [ ] **Modify `hubspot.py` to implement OAuth authentication**  
  - Complete the following functions in `backend/integrations/hubspot.py`:  
    - `authorize_hubspot` → Redirects users to HubSpot's OAuth consent screen.  
    - `oauth2callback_hubspot` → Handles the OAuth callback and retrieves access tokens.  
    - `get_hubspot_credentials` → Fetches stored credentials for authentication.  
  - Reference `airtable.py` and `notion.py` for implementation patterns.

- [ ] **Obtain client credentials from HubSpot**  
  - Sign up for a HubSpot developer account.
  - Create an app and get the **Client ID & Client Secret** for OAuth authentication.

- [ ] **Implement OAuth in frontend (`hubspot.js`)**  
  - Modify `frontend/src/integrations/hubspot.js` to enable user authentication via OAuth.
  - Ensure integration is similar to `airtable.js` and `notion.js`.

#### **3️⃣ Load HubSpot Items**  
- [ ] **Fetch and display HubSpot items**  
  - Implement `get_items_hubspot` in `backend/integrations/hubspot.py`.
  - Use the HubSpot API to retrieve data and convert it into `IntegrationItem` objects.
  - Verify that fetched data is correctly displayed.

#### **4️⃣ Final Testing & Debugging**  
- [ ] **Test OAuth authentication**  
  - Ensure users can successfully authenticate via HubSpot.

- [ ] **Verify API responses**  
  - Check that HubSpot data is being retrieved and displayed correctly.

- [ ] **Fix any bugs or issues**  
  - Debug errors and refine code for better performance.

#### **5️⃣ Prepare Submission**  
- [ ] **Zip completed code**  
  - Name the zip file as `YourName_Technical_Assessment.zip`.

- [ ] **Record a walkthrough video**  
  - Explain your implementation, code structure, and demonstrate functionality.
  - Save the file as `YourName_ScreenRecording.mp4`.

- [ ] **Submit via Google Form**  
  - Ensure submission is completed before **March 16, 11:59 PM IST**.

---  
Let me know if you need help with OAuth integration, API calls, or frontend setup! 🚀

