#!/bin/bash
# Package BITTEN for Windows deployment

echo "📦 Creating BITTEN Windows deployment package"
echo "==========================================="

# Create package directory
PACKAGE_DIR="/root/HydraX-v2/BITTEN_Windows_Package"
mkdir -p "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/EA"
mkdir -p "$PACKAGE_DIR/Scripts"
mkdir -p "$PACKAGE_DIR/API"
mkdir -p "$PACKAGE_DIR/Docs"

# Copy EA files
echo "📋 Copying EA files..."
cp /root/HydraX-v2/src/bridge/BITTENBridge_v3_ENHANCED.mq5 "$PACKAGE_DIR/EA/"

# Copy Python files
echo "🐍 Copying Python API files..."
cp /root/HydraX-v2/src/bitten_core/mt5_enhanced_adapter.py "$PACKAGE_DIR/API/"
cp /root/HydraX-v2/src/bitten_core/live_data_filter.py "$PACKAGE_DIR/API/"

# Copy setup scripts
echo "📜 Copying setup scripts..."
cp /root/HydraX-v2/setup_mt5_windows.ps1 "$PACKAGE_DIR/Scripts/"

# Copy documentation
echo "📚 Copying documentation..."
cp /root/HydraX-v2/WINDOWS_MT5_SETUP.md "$PACKAGE_DIR/Docs/"
cp /root/HydraX-v2/docs/MT5_ENHANCED_FEATURES.md "$PACKAGE_DIR/Docs/"

# Create main setup script
cat << 'SETUP' > "$PACKAGE_DIR/SETUP.ps1"
# BITTEN Windows Quick Setup
Write-Host "🚀 BITTEN MT5 Windows Setup" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green

# Run the main setup script
.\Scripts\setup_mt5_windows.ps1

Write-Host "`n✅ Initial setup complete!" -ForegroundColor Green
Write-Host "Please see Docs\WINDOWS_MT5_SETUP.md for detailed instructions" -ForegroundColor Yellow
SETUP

# Create README
cat << 'README' > "$PACKAGE_DIR/README.txt"
BITTEN MT5 Windows Deployment Package
=====================================

This package contains everything needed to set up a BITTEN MT5 trading farm on Windows.

Contents:
- EA/             : Enhanced MT5 Expert Advisor
- Scripts/        : PowerShell setup scripts  
- API/            : Python API server files
- Docs/           : Complete documentation

Quick Start:
1. Copy this entire folder to C:\BITTEN on your Windows machine
2. Open PowerShell as Administrator
3. Navigate to C:\BITTEN
4. Run: .\SETUP.ps1

For detailed instructions, see Docs\WINDOWS_MT5_SETUP.md

Requirements:
- Windows Server 2019/2022 or Windows 10/11
- Python 3.8 or higher
- Administrator access
- MT5 broker account credentials

Support:
- Check documentation in Docs folder
- Review logs in C:\BITTEN\Logs
- Test API at http://localhost:8001/health
README

# Create a zip file
echo ""
echo "📦 Creating zip package..."
cd /root/HydraX-v2
zip -r BITTEN_Windows_Package.zip BITTEN_Windows_Package/

echo ""
echo "✅ Package created successfully!"
echo ""
echo "📋 Package location: /root/HydraX-v2/BITTEN_Windows_Package.zip"
echo ""
echo "Transfer options:"
echo "1. SCP to Windows: scp BITTEN_Windows_Package.zip user@windows-server:C:\\Users\\Administrator\\Desktop\\"
echo "2. Upload to S3: aws s3 cp BITTEN_Windows_Package.zip s3://your-bucket/"
echo "3. Use RDP and download directly"
echo ""
echo "The package contains:"
echo "- Enhanced EA with two-way communication"
echo "- Python API server for farm management"
echo "- Complete PowerShell setup scripts"
echo "- Detailed documentation"
echo ""
echo "Once on Windows, extract and run SETUP.ps1 as Administrator!"