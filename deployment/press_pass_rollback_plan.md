# Press Pass Deployment Rollback Plan

## Overview
This document outlines the rollback procedures for the Press Pass and TCS++ integration deployment.

## Pre-Deployment Backup Checklist
1. **Database Backup**
   - [ ] Backup current database state
   - [ ] Export Press Pass tier configurations
   - [ ] Save current user states and progress

2. **Code Backup**
   - [ ] Tag current production version in git
   - [ ] Backup current bot configuration
   - [ ] Save nginx configuration

3. **State Preservation**
   - [ ] Document current active Press Pass users
   - [ ] Save current tier metrics
   - [ ] Export TCS engine state

## Rollback Triggers
- Critical errors in Press Pass command execution
- Landing page payment flow failures
- Database corruption or data loss
- TCS engine calculation errors
- User authentication issues

## Rollback Procedures

### 1. Immediate Rollback (< 5 minutes)
```bash
# Stop bot service
systemctl stop hydrax-bot

# Restore previous code version
git checkout production-backup-[timestamp]

# Restart services
systemctl start hydrax-bot
systemctl restart nginx
```

### 2. Database Rollback
```bash
# Restore database from backup
psql -U postgres hydrax < /backups/hydrax-[timestamp].sql

# Verify data integrity
python3 /root/HydraX-v2/scripts/verify_database.py
```

### 3. Configuration Rollback
```bash
# Restore bot configuration
cp /backups/bot-config-[timestamp].json /root/HydraX-v2/config/bot_config.json

# Restore nginx configuration
cp /backups/nginx-[timestamp].conf /etc/nginx/sites-available/default
nginx -t && systemctl reload nginx
```

### 4. User State Recovery
```python
# Run user state recovery script
python3 /root/HydraX-v2/scripts/recover_user_states.py --backup-date [timestamp]
```

## Post-Rollback Verification
1. [ ] Verify bot responds to commands
2. [ ] Test basic Press Pass functionality
3. [ ] Check landing page loads correctly
4. [ ] Validate user data integrity
5. [ ] Monitor error logs for 30 minutes

## Communication Plan
1. Notify team via Telegram admin channel
2. Post status update in community channel
3. Document issues encountered
4. Schedule post-mortem meeting

## Emergency Contacts
- Lead Developer: @admin_handle
- DevOps: @devops_handle
- Database Admin: @db_admin_handle