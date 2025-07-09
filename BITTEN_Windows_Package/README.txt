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
