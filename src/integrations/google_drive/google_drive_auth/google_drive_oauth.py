"""
Google Drive OAuth authentication module.
Simple version - authenticates fresh each time.
"""
import os
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    # For testing without Google API libraries installed
    InstalledAppFlow = None
    build = None

# Define the scopes required for contribution analysis
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',  # Added for displayName
    'openid',
]


def google_drive_oauth(credentials_path: str = None) -> tuple:
    """
    Perform Google Drive OAuth authentication flow.
    """
    if credentials_path is None:
        # Default to module directory
        module_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(module_dir, 'credentials.json')
    
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Google Drive credentials file not found at {credentials_path}. "
            "Please download OAuth 2.0 credentials from Google Cloud Console."
        )
    
    print("\nGoogle Drive Login Starting...")
    print("Opening browser for authentication...")
    
    try:
        # Create OAuth flow and run it
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        
        print("Google Drive Authorized!")
        
        # Build and return services
        drive_service = build('drive', 'v3', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)
        return creds, drive_service, docs_service
    except Exception as e:
        print(f"Error during Google Drive authentication: {e}")
        return None, None, None


def get_user_email(creds):
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()
    return user_info["email"]


def get_user_info(creds):
    """Get both email and displayName from OAuth."""
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()
    
    # Try multiple fields for displayName
    display_name = (
        user_info.get("name") or  # Full name
        user_info.get("given_name") or  # First name
        (f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()) or  # Combined
        ""  # Fallback
    )

    return {
        "email": user_info.get("email", ""),
        "displayName": display_name,
    }


if __name__ == "__main__":
    creds, drive_service, docs_service = google_drive_oauth()
    if drive_service:
        user_email = get_user_email(creds)
        print("Successfully connected to Google Drive!")

