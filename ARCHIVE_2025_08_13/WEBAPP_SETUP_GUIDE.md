# Telegram WebApp Setup Guide

## Issue: "Button_type_invalid" Error

The error you're seeing occurs because the bot hasn't been properly configured in BotFather to support WebApps. Here's how to fix it:

## Step 1: Configure Bot in BotFather

1. **Open Telegram** and search for `@BotFather`
2. **Send `/mybots`** to BotFather
3. **Select your bot** from the list
4. **Choose "Bot Settings"**
5. **Select "Configure Mini App"**
6. **Set the Mini App URL** to: `https://joinbitten.com/hud`

## Step 2: Configure Menu Button (Optional but Recommended)

1. While in Bot Settings, select **"Configure Menu Button"**
2. **Set button text**: "🎯 Open BITTEN"
3. **Set Mini App URL**: `https://joinbitten.com/hud`

## Step 3: Verify WebApp Domain

Your webapp must be accessible via HTTPS. Test these URLs:
- ✅ https://joinbitten.com/hud
- ✅ https://joinbitten.com/test
- ✅ https://joinbitten.com/

## Step 4: Test the Setup

After configuring in BotFather, the WebApp buttons should work without the "Button_type_invalid" error.

## Key Requirements for WebApp Integration

### 1. HTTPS Only
- WebApps MUST use HTTPS
- No HTTP allowed
- Valid SSL certificate required

### 2. BotFather Configuration
- Main Mini App URL must be set
- Menu button should be configured
- Bot must be properly registered

### 3. WebApp JavaScript
Your webapp needs the Telegram WebApp script:
```html
<script src="https://telegram.org/js/telegram-web-app.js"></script>
```

### 4. Proper URL Structure
- Base URL: `https://joinbitten.com/hud`
- With data: `https://joinbitten.com/hud?data=...`
- Data must be URL-encoded JSON

## Testing Commands

Once configured, you can test with:

```bash
# Start the webapp server
python3 webapp_telegram_fixed.py &

# Test the webapp
curl https://joinbitten.com/test

# Send test signal
python3 send_signal_webapp_fixed.py
```

## Common Issues and Solutions

### 1. Button_type_invalid
**Cause**: Bot not configured in BotFather
**Solution**: Set Mini App URL in BotFather settings

### 2. WebApp doesn't open
**Cause**: HTTPS issues or invalid URL
**Solution**: Verify SSL certificate and URL accessibility

### 3. Confirmation dialog still appears
**Cause**: Incomplete BotFather setup
**Solution**: Set both Main Mini App and Menu Button

### 4. Data not passed correctly
**Cause**: JSON encoding issues
**Solution**: Use urllib.parse.quote for data encoding

## BotFather Commands Reference

```
/mybots - List your bots
/setmenubutton - Set menu button
/setdescription - Set bot description
/setuserpic - Set bot avatar
/setcommands - Set bot commands
```

## Next Steps

1. **Configure in BotFather** (most important)
2. **Test basic WebApp button**
3. **Test with data parameters**
4. **Verify no confirmation dialog**
5. **Deploy production signals**

## Production Deployment

Once working, you can:
- Send signals with embedded WebApp buttons
- Users click "🎯 VIEW INTEL" 
- WebApp opens directly in Telegram
- No confirmation dialogs
- Full signal intelligence displayed

## Support

If you continue to have issues after BotFather configuration:
1. Check bot token is correct
2. Verify webapp server is running
3. Test HTTPS accessibility
4. Ensure proper URL encoding