# BITTEN Bot Documentation

## Overview

BITTEN is the Telegram bot component of the HydraX v2 trading system, providing command and control capabilities through Telegram groups.

## Key Features

- **Elite Commands**: Full command set for advanced trading operations
- **Webhook Integration**: HTTPS webhook for real-time Telegram updates
- **Group Management**: Operates in Telegram group -1002581996861
- **Health Monitoring**: Built-in health check endpoint

## Documentation Structure

- `webhook-setup-victory.md` - Complete webhook implementation guide and 32-hour journey
- `commands.md` - Command reference (coming soon)
- `deployment.md` - Deployment procedures (coming soon)

## Quick Links

- **Live Bot Endpoint**: https://telegram1.joinbitten.com
- **Health Check**: https://telegram1.joinbitten.com/health
- **Server**: 134.199.204.67

## Core Files

- `/root/HydraX-v2/BITTEN_elite_commands_FULL.py` - Main bot implementation
- `/root/bitten/toc_core/telegram_router.py` - Webhook router (running instance)

## Current Status

✅ Bot is live and operational
✅ Webhook configured and receiving updates
✅ SSL certificate active
✅ Commands responding (/ping tested successfully)

## Recent Achievements

- July 4, 2025: Successfully deployed HTTPS webhook after eliminating Cloudflare tunnel issues
- Implemented nginx reverse proxy with Let's Encrypt SSL
- Established reliable bot infrastructure

See `webhook-setup-victory.md` for the complete implementation story.