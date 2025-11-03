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
    'https://www.googleapis.com/auth/drive.metadata.readonly'
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
        
        # Build and return service
        service = build('drive', 'v3', credentials=creds)
        return creds, service
    except Exception as e:
        print(f"Error during Google Drive authentication: {e}")
        return None, None


if __name__ == "__main__":
    creds, service = google_drive_oauth()
    if service:
        print("Successfully connected to Google Drive!")

