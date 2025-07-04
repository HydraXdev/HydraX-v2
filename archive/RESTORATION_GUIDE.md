# HydraX v2 Cleanup & Restoration Guide

## Overview
This guide documents the comprehensive cleanup performed on July 4, 2025, and provides instructions for restoring any archived code if needed.

## Cleanup Summary

### 🗄️ Archive Branch Created
- **Branch**: `archive/pre-cleanup-20250704`
- **Purpose**: Complete snapshot of codebase before cleanup
- **Access**: `git checkout archive/pre-cleanup-20250704`

### 📁 Files Moved to Archive

#### Sensitive Files (`archive/sensitive_files/`)
- **`fire_trade.pynano`** - CRITICAL: Contains hardcoded SSH credentials and IP addresses
  - Original location: `/root/HydraX-v2/fire_trade.pynano`
  - Reason: Security risk - hardcoded credentials
  - ⚠️ **WARNING**: Do not restore to version control without removing sensitive data

#### Temporary Files (`archive/temp_files/`)
- **`nohup.out`** - Flask server logs (26KB)
  - Original location: `/root/HydraX-v2/nohup.out`
  - Reason: Build artifact, should not be in version control
  
- **`dev_log.txt`** - Development log file (1.1KB)
  - Original location: `/root/HydraX-v2/dev_log.txt`
  - Reason: Development artifact, added to .gitignore

### 🔄 Structure Reorganization

#### Old Structure → New Structure
```
OLD:
core/
├── hydrastrike_v3.5.py
├── TEN_elite_commands_FULL.py
└── modules/
    ├── bitmode.py
    └── modules/
        ├── commandermode.py
        └── modules/
            ├── tcs_scoring.py
            └── telegram_bot/
                ├── bot.py
                ├── requirements.txt
                └── .env.example

NEW:
src/
├── core/
│   ├── hydrastrike_v3.5.py
│   ├── TEN_elite_commands_FULL.py
│   └── modules/
│       ├── bitmode.py
│       ├── commandermode.py
│       └── tcs_scoring.py
├── telegram_bot/
│   ├── bot.py
│   ├── requirements.txt
│   └── .env.example
└── bridge/
    └── FileBridgeEA.mq5
```

#### Removed Directories
- `core/modules/modules/modules/` - Unnecessarily nested structure
- `"FileBridgeEA.mq5 → bridge/"` - Directory with unusual arrow characters

### 🔧 Syntax Fixes Applied
1. **`core/modules/bitmode.py`** - Fixed `e#` to `#` on line 1
2. **`core/modules/modules/commandermode.py`** - Fixed `e#` to `#` on line 1
3. **`core/modules/modules/modules/telegram_bot/bot.py`** - Fixed `f#` to `#` on line 1

### 📦 New Files Created
- `requirements.txt` - Main project dependencies
- `requirements-dev.txt` - Development dependencies
- `.env.example` - Environment configuration template
- `Makefile` - Development commands
- `src/__init__.py` - Package initialization files
- `tests/` - Test framework setup
- `.github/` - GitHub templates and workflows
- `docs/development.md` - Development guide

### 🔒 Security Improvements
- Enhanced `.gitignore` with security patterns
- Moved sensitive files to archive
- Added environment variable templates
- Implemented secret scanning in CI/CD

## Restoration Instructions

### 1. Accessing Archive Branch
```bash
# View available archive branches
git branch -a | grep archive

# Switch to archive branch
git checkout archive/pre-cleanup-20250704

# View original file structure
ls -la
```

### 2. Restoring Specific Files

#### Safe Files (No Security Risk)
```bash
# Switch to main branch
git checkout main

# Copy specific file from archive
git checkout archive/pre-cleanup-20250704 -- path/to/file.py

# Example: Restore development log
git checkout archive/pre-cleanup-20250704 -- dev_log.txt
```

#### Sensitive Files (⚠️ SECURITY RISK)
```bash
# Access sensitive files (DO NOT commit directly)
git checkout archive/pre-cleanup-20250704
cp fire_trade.pynano /tmp/fire_trade_backup.py

# Edit file to remove sensitive data
nano /tmp/fire_trade_backup.py
# Remove hardcoded credentials, IPs, passwords

# Switch back to main and copy cleaned version
git checkout main
cp /tmp/fire_trade_backup.py src/core/fire_trade.py
```

### 3. Restoring Directory Structure
```bash
# If you need the old nested structure:
git checkout archive/pre-cleanup-20250704
cp -r core/modules/modules/modules/ ./restored_nested_structure/
git checkout main
```

## File Inventory

### Files by Category

#### ✅ Preserved & Moved
- `BITTEN_elite_commands_FULL.py` → Root (Flask app)
- `fire_trade.py` → Root (Trade execution)
- `LICENSE` → Root
- `README.md` → Root (enhanced)
- `deploy_flask.sh` → Root
- `set_telegram_webhook.sh` → Root
- All core modules → `src/core/`
- Telegram bot → `src/telegram_bot/`
- MT5 bridge → `src/bridge/`
- Documentation → `docs/`

#### 🗄️ Archived
- `fire_trade.pynano` → `archive/sensitive_files/`
- `nohup.out` → `archive/temp_files/`
- `dev_log.txt` → `archive/temp_files/`

#### 🆕 Created
- `requirements.txt`
- `requirements-dev.txt`
- `.env.example`
- `Makefile`
- `tests/` directory
- `.github/` templates
- `docs/development.md`

### Security Audit Results

#### 🔴 Critical Issues Found
1. **Hardcoded SSH Credentials** in `fire_trade.pynano`
   - Username/password combinations
   - IP addresses
   - **Status**: Moved to archive, not in version control

#### 🟡 Minor Issues Fixed
1. **Log Files** in version control
   - `nohup.out` - 26KB of server logs
   - **Status**: Moved to archive, added to .gitignore

2. **Development Files** in version control
   - `dev_log.txt` - Development notes
   - **Status**: Moved to archive, added to .gitignore

## Emergency Restoration

### Full Rollback (if needed)
```bash
# Create backup of current state
git checkout main
git checkout -b backup-current-state

# Restore to pre-cleanup state
git checkout archive/pre-cleanup-20250704
git checkout -b restore-pre-cleanup

# Merge carefully, avoiding sensitive files
git checkout main
git merge restore-pre-cleanup --no-commit
git reset HEAD archive/sensitive_files/
git commit -m "Restore pre-cleanup state (excluding sensitive files)"
```

### Partial Restoration
```bash
# Restore specific functionality
git checkout main

# For trading logic:
git checkout archive/pre-cleanup-20250704 -- core/
# Clean up structure as needed

# For configuration:
git checkout archive/pre-cleanup-20250704 -- config/
```

## Contact & Support

### If You Need Help
1. **Check Archive Branch**: `git checkout archive/pre-cleanup-20250704`
2. **Review This Guide**: All changes are documented here
3. **Security First**: Never restore sensitive files without cleaning them

### Reporting Issues
If you find any missing functionality after cleanup:
1. Check the archive branch first
2. Document what's missing
3. Create an issue with details
4. Reference this restoration guide

## Future Cleanup Guidelines

### Before Major Cleanup
1. Create archive branch: `git checkout -b archive/pre-cleanup-$(date +%Y%m%d)`
2. Commit all changes: `git add -A && git commit`
3. Document what's being changed
4. Create restoration guide

### Security Checklist
- [ ] Scan for hardcoded credentials
- [ ] Check for sensitive URLs/IPs
- [ ] Review API keys and tokens
- [ ] Verify no production secrets in code
- [ ] Update .gitignore patterns

---

**Date**: July 4, 2025  
**Cleanup By**: Claude Code Assistant  
**Archive Branch**: `archive/pre-cleanup-20250704`  
**Status**: Complete ✅