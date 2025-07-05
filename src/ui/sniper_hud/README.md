# BITTEN WebApp: Sniper Mission Brief HUD

## PURPOSE
A futuristic WebApp interface for BITTEN users (Nibbler tier and above) to view mission briefs, real-time stats, encrypted sniper setups, and upgrade triggers in an immersive, AI war-room style HUD.

---

## STRUCTURE

### WebApp Modules
- `index.html`: Static HUD layout shell
- `style.css` (optional): Currently inline but can be modularized
- `app.js` (planned): JavaScript handling dynamic countdown, upgrade prompts, etc.

---

## FUTURE INTEGRATIONS

- **Tier Routing (Flask):**
  - Telegram `initData` sent to backend
  - Backend responds with user tier + mission data
  - WebApp dynamically reveals or locks elements

- **Logging (Optional):**
  - Button clicks
  - Upgrade views
  - XP calculations

- **Upgrade UX Triggers:**
  - Blocked fire
  - Tooltip reveals
  - Post-mission stats

---

## DEPLOYMENT PLAN

1. Host as static WebApp (e.g., Netlify, Cloudflare Pages)
2. Use Telegram WebApp button to open
3. Connect to Flask API for user data
4. Lock/unlock sniper data per tier

---

## STATUS (JULY 5)

✅ UI Mockup complete  
✅ Countdown logic live  
✅ Visual theme stable  
⏳ Backend auth + data  
⏳ Flask tier middleware  
⏳ Post-trade kill cards + XP feedback