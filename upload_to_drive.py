#!/usr/bin/env python3
"""
Upload BITTEN Game Rules Backtesting Report to Google Drive
"""

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
import sys

def upload_report():
    """Upload the PDF report to Google Drive"""
    
    # Check if PDF exists
    pdf_path = '/root/HydraX-v2/BITTEN_GAME_RULES_BACKTEST_REPORT.pdf'
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF not found at {pdf_path}")
        return False
    
    try:
        print("🔐 Authenticating with Google Drive...")
        
        # Create settings.yaml for authentication
        settings_content = """
client_config_backend: service
client_config:
  client_id: your_client_id
  client_secret: your_client_secret

save_credentials: True
save_credentials_backend: file
save_credentials_file: credentials.json

get_refresh_token: True

oauth_scope:
  - https://www.googleapis.com/auth/drive.file
  - https://www.googleapis.com/auth/drive.install
"""
        
        # For command line authentication without browser
        gauth = GoogleAuth()
        
        # Try to load saved credentials
        gauth.LoadCredentialsFile("credentials.json")
        
        if gauth.credentials is None:
            # Authenticate if credentials don't exist
            print("📝 First time setup - need to authenticate...")
            print("⚠️  This requires a browser for Google OAuth...")
            print("💡 Alternative: Use service account for headless auth")
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh token if expired
            print("🔄 Refreshing expired token...")
            gauth.Refresh()
        else:
            # Initialize with saved credentials
            print("✅ Using saved credentials...")
            gauth.Authorize()
        
        # Save credentials for next run
        gauth.SaveCredentialsFile("credentials.json")
        
        # Create drive instance
        drive = GoogleDrive(gauth)
        print("✅ Connected to Google Drive")
        
        # Get the target folder ID from the URL
        folder_url = "https://drive.google.com/drive/folders/1cm8CYKhvfnm-CV4PlCXQ99J5TFR1V8M6"
        folder_id = "1cm8CYKhvfnm-CV4PlCXQ99J5TFR1V8M6"
        
        print(f"📁 Uploading to folder: {folder_id}")
        
        # Create file metadata
        file_metadata = {
            'title': 'BITTEN_Game_Rules_Backtest_Report.pdf',
            'parents': [{'id': folder_id}],
            'description': 'BITTEN Game Rules Backtesting Report - Complete validation of trading system mechanics and user protection systems'
        }
        
        # Create and upload file
        print("📤 Creating file object...")
        file = drive.CreateFile(file_metadata)
        
        print("📦 Setting content...")
        file.SetContentFile(pdf_path)
        
        print("🚀 Uploading...")
        file.Upload()
        
        print("✅ Upload successful!")
        print(f"📋 File ID: {file['id']}")
        print(f"🔗 File URL: https://drive.google.com/file/d/{file['id']}/view")
        print(f"📁 Folder URL: {folder_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        print("💡 Troubleshooting tips:")
        print("   1. Make sure you have access to the Google Drive folder")
        print("   2. Check your internet connection")
        print("   3. Try running the script with browser access")
        return False

def create_service_account_instructions():
    """Create instructions for service account setup"""
    instructions = """
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
"""
    
    with open('service_account_setup.md', 'w') as f:
        f.write(instructions)
    
    print("📖 Created service_account_setup.md with detailed instructions")

if __name__ == "__main__":
    print("🎯 BITTEN Game Rules Report Upload")
    print("=" * 50)
    
    # Check if running in headless environment
    if not os.environ.get('DISPLAY'):
        print("⚠️  Running in headless environment (no display)")
        print("💡 This may require service account authentication")
        create_service_account_instructions()
    
    success = upload_report()
    
    if success:
        print("\n🎉 MISSION ACCOMPLISHED!")
        print("Your BITTEN Game Rules Backtesting Report is now available in Google Drive")
    else:
        print("\n❌ Upload failed - see error messages above")
        sys.exit(1)