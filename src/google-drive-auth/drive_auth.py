from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scopes and supported MIME types
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]
SUPPORTED_MIME_TYPES = [
    'application/vnd.google-apps.document',
    'application/pdf',
    'application/vnd.google-apps.spreadsheet'
]

def main():
    # Run local server for OAuth login
    flow = InstalledAppFlow.from_client_secrets_file('src/google-drive-auth/credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Build the Drive API client
    service = build('drive', 'v3', credentials=creds)

    files = list_supported_files(service, SUPPORTED_MIME_TYPES)
    selected_files = select_files(files)
    print("You selected the following files:")
    for name, file_id, mime in selected_files:
        print(f"Name: {name}")

def list_supported_files(service, supported_mimes):
    results = service.files().list(
        pageSize=100,
        fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    supported_files = [
        (item['name'], item['id'], item['mimeType'])
        for item in items if item['mimeType'] in supported_mimes
    ]

    return supported_files

def select_files(files):
    print("Supported files:")
    for idx, (name, _, _) in enumerate(files):
        print(f"{idx+1}. {name}")

    chosen_indices = input("Pick files by numbers (comma-separated): ")
    chosen_indices = [int(i)-1 for i in chosen_indices.split(',')]
    return [files[i] for i in chosen_indices]



if __name__ == '__main__':
    main()
