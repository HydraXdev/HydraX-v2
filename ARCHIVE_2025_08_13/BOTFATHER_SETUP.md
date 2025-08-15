# 🤖 BotFather WebApp Configuration

## Quick Setup to Remove "Open Link" Confirmation

### Step 1: Open BotFather
1. Open Telegram
2. Search for `@BotFather`
3. Start a conversation

### Step 2: Configure Your Bot
Send these commands in order:

```
/mybots
```
Select: **BittenCommander** (or your bot name)

```
Bot Settings
```

```
Configure Mini App
```

### Step 3: Set WebApp URL
When prompted, send:
```
https://joinbitten.com/hud
```

### Step 4: Set Mini App Name (Optional)
When prompted for a name, send:
```
BITTEN Mission Intel
```

### Step 5: Done!
That's it! Your bot is now configured.

## Test It
Run this command to send a test signal:
```bash
python3 SEND_DIRECT_SIGNAL.py
```

The webapp should now open directly without any confirmation dialog!

## Troubleshooting

### Still Getting Confirmation?
1. Make sure you set the EXACT URL: `https://joinbitten.com/hud`
2. Try clearing Telegram cache (Settings → Data and Storage → Clear Cache)
3. Restart Telegram app

### WebApp Not Loading?
1. Check if webapp server is running: `ps aux | grep webapp_server`
2. Check nginx is running: `systemctl status nginx`
3. Test the URL directly: `curl -I https://joinbitten.com/hud`

### Need to Change URL Later?
Just repeat the process - BotFather will let you update the Mini App URL anytime.