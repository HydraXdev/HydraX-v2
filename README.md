# HydraX v2: Bit by Bit Edition

HydraX is an AI-powered trading bot system built for beginners, optimized for speed and scale.

This version includes:
- Bit Mode (safe auto-scalping)
- Commander Mode (high-risk compounding)
- Tactical Logic (modes: Auto, Semi, Sniper, Leroy)
- Telegram integration
- Future: Myfxbook API, MT5 support

More coming soon.

## Configuration

Create a `.env` file (see `core/modules/modules/modules/telegram_bot/.env.example`)
and set at least the following variables:

```
TELEGRAM_TOKEN=<your-telegram-bot-token>
TELEGRAM_CHAT_ID=<optional-chat-id>
```

`TELEGRAM_TOKEN` is used by `TEN_elite_commands_FULL.py` to send replies.
