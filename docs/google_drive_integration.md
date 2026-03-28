# Google Drive Integration

This project optionally supports Google Drive analysis through the Google Drive API.
All access is strictly consent-based and is not required for a project to be analyzed.

---

### For Course Evaluators (TAs) and Team Members

Google Drive integration **can be tested by course evaluators**.


To enable Google Drive integration during evaluation, follow these steps:

Create a Google Cloud Project
1. Go to: https://console.cloud.google.com 
2. Click Select a project -> New Project
3. Name it anything ( ex. Drive-API-Grading), Location can be left as "No organization"
4. Click Create

Enable the Google Drive API
1. Check you are in the project just created ( will say "you are working in [project_name] " )
   if project is a different one click and select apporpriate project
2. Go to navigation menu - > APIs & Services -> Enable APIs & services
3. Click " + Enable APIs and services"
4. Search for Google Drive API 
3. Click it -> Enable

Configure OAuth Consent Screen
1. Go to APIs & Services -> OAuth consent screen 
2. Click "Get Started"
3. Fill out:
      App name: (ex:"TestingTeam19")   
      User support email
4. Click "Next"
5. Select External, Click "Next"
6. Fill out email address for contact information, Click "Next"
7. Select "I agree to the Google API Services: User Data Policy. ", Click "Continue"
8. Click save

Add Yourself as a Test User
1. Go to APIs & Services -> OAuth consent screen
2. Find the "Test users" section
3. Click "+ Add users"
4. Enter your Google email address (the one you will use to authorize)
5. Click Save

> Note: While the app is in "Testing" mode, only emails listed as test users can authorize — even if you are the project owner. This applies to both the CLI and web OAuth flows.

Create OAuth Credentials (Desktop — for CLI analysis)
1. Go to APIs & Services -> Credentials
2. Click "+ Create Credentials" -> OAuth client ID
3. Choose **Desktop app**
4. Name it anything
5. Click "Create"
6. Click "Download JSON"
7. Rename it to "credentials.json"

Placing the Credentials file within the project
1. Place the file so its path is: `src/integrations/google_drive/google_drive_auth/credentials.json`
2. Verify the path is correct before running the application.

---

Create OAuth Credentials (Web — for API endpoints)
1. Go to APIs & Services -> Credentials
2. Click "+ Create Credentials" -> OAuth client ID
3. Choose **Web application**
4. Name it anything (e.g. "Capstone Web OAuth")
5. Under "Authorized redirect URIs", add: `http://localhost:8000/auth/google/callback`
6. Click "Create"
7. Copy the **Client ID** and **Client Secret**
8. Add them to your `.env` file:
   ```
   GOOGLE_CLIENT_ID=<your-client-id>
   GOOGLE_CLIENT_SECRET=<your-client-secret>
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
   ```

---

If credentials are not provided, the system will fall back to local-only analysis,
and all core functionality will remain available.

> Note: Google Drive OAuth requires the user’s email to be a Google account (e.g., Gmail).