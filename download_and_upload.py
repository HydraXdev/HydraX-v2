#!/usr/bin/env python3
"""
Download BITTEN report and upload to Google Drive
Run this script on your local computer with browser access
"""

import requests
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def download_report():
    """Download the PDF report from the server"""
    url = "http://134.199.204.67:8889/BITTEN_GAME_RULES_BACKTEST_REPORT.pdf"
    local_filename = "BITTEN_Game_Rules_Backtest_Report.pdf"
    
    print(f"📥 Downloading report from {url}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded successfully: {local_filename}")
        print(f"📄 File size: {os.path.getsize(local_filename):,} bytes")
        return local_filename
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def upload_to_drive(file_path):
    """Upload the file to Google Drive"""
    
    try:
        print("🔐 Authenticating with Google Drive...")
        
        # Create GoogleAuth instance
        gauth = GoogleAuth()
        
        # Try to load saved credentials
        gauth.LoadCredentialsFile("credentials.json")
        
        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()
        
        # Save the current credentials to a file
        gauth.SaveCredentialsFile("credentials.json")
        
        drive = GoogleDrive(gauth)
        print("✅ Connected to Google Drive")
        
        # Target folder ID from your URL
        folder_id = "1cm8CYKhvfnm-CV4PlCXQ99J5TFR1V8M6"
        
        # Create file metadata
        file_metadata = {
            'title': 'BITTEN_Game_Rules_Backtest_Report.pdf',
            'parents': [{'id': folder_id}]
        }
        
        print("📤 Creating file in Google Drive...")
        file = drive.CreateFile(file_metadata)
        file.SetContentFile(file_path)
        
        print("🚀 Uploading...")
        file.Upload()
        
        print("✅ Upload successful!")
        print(f"🔗 File URL: https://drive.google.com/file/d/{file['id']}/view")
        print(f"📁 Folder URL: https://drive.google.com/drive/folders/{folder_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def main():
    print("🎯 BITTEN Report Download & Upload Tool")
    print("=" * 50)
    print("📋 This script will:")
    print("1. Download the PDF report from the BITTEN server")
    print("2. Upload it to your Google Drive folder")
    print()
    
    # Download the report
    local_file = download_report()
    if not local_file:
        print("❌ Download failed, cannot proceed")
        return
    
    # Upload to Google Drive
    success = upload_to_drive(local_file)
    
    if success:
        print("\n🎉 SUCCESS!")
        print("Your BITTEN Game Rules Backtesting Report is now in Google Drive")
        
        # Clean up local file
        try:
            os.remove(local_file)
            print(f"🧹 Cleaned up local file: {local_file}")
        except:
            pass
    else:
        print(f"\n❌ Upload failed, but file saved locally: {local_file}")

if __name__ == "__main__":
    main()