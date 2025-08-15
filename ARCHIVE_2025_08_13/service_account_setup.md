
🔧 GOOGLE DRIVE SERVICE ACCOUNT SETUP (For Headless Authentication)

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Google Drive API
4. Go to "Credentials" → "Create Credentials" → "Service Account"
5. Download the JSON key file
6. Share your Google Drive folder with the service account email
7. Update this script to use service account authentication

Example service account code:
```python
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth()
gauth.ServiceAuth()  # Uses service account
drive = GoogleDrive(gauth)
```
