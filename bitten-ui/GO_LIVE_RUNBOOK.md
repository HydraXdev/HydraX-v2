# BITTEN UI - GO LIVE RUNBOOK

**Version:** 1.0
**Date:** October 5, 2025
**Status:** Production Ready

---

## 🎯 Decision: Pick Your Launch Mode

### Option A: Real Data (Backend Ready) ✅ Recommended

- Backend event bus running
- REST endpoints `/api/fire` and `/api/trades/close-all` ready
- Go to **Section 1: Production Deployment**

### Option B: Public Demo (Backend Not Ready)

- No backend needed
- Shows realistic mock data
- Go to **Section 2: Demo Deployment**

---

## Section 1: Production Deployment (Real Data)

### Step 1: Pre-flight Checklist

Verify backend is ready:

```bash
# Test event bus connection
wscat -c ws://134.199.204.67:8888/socket.io

# Test fire endpoint
curl -i -X POST http://134.199.204.67:8888/api/fire \
  -H 'Content-Type: application/json' \
  -d '{"alertId":"test","entry":1.05,"sl":1.04,"tp":1.06,"riskUsd":100}'

# Test close-all endpoint
curl -i -X POST http://134.199.204.67:8888/api/trades/close-all \
  -H 'Content-Type: application/json' \
  -d '{"reason":"manual"}'
```

**Expected:**

- ✅ WebSocket connects and receives messages
- ✅ Fire endpoint returns 202 Accepted
- ✅ Close-all returns 202 Accepted

### Step 2: Configure Environment

Verify `.env.production`:

```bash
cat .env.production
```

Should show:

```
NEXT_PUBLIC_USE_MOCKS=0                    # Real data!
NEXT_PUBLIC_BUS_URL=ws://134.199.204.67:8888/socket.io
NEXT_PUBLIC_BACKEND_URL=http://134.199.204.67:8888
NEXT_PUBLIC_API_FIRE=/api/fire
NEXT_PUBLIC_API_CLOSE_ALL=/api/trades/close-all
```

### Step 3A: Deploy to Vercel (Fastest)

```bash
cd /root/HydraX-v2/bitten-ui
./deploy-vercel.sh
```

**What it does:**

1. Builds locally to catch errors
2. Sets all environment variables
3. Deploys to production
4. Returns live URL

**Time:** ~2-3 minutes

### Step 3B: Deploy via Docker (Self-hosted)

```bash
cd /root/HydraX-v2/bitten-ui
./deploy-docker.sh
```

**What it does:**

1. Builds optimized Docker image
2. Runs container on port 3000
3. Auto-restarts on failure

**Then configure NGINX:**

```nginx
server {
    listen 80;
    server_name ui.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Step 4: Smoke Tests

```bash
# Test deployed app
./smoke-tests.sh https://your-vercel-url.vercel.app

# Or for Docker
./smoke-tests.sh http://localhost:3000
```

**Must pass:**

- ✅ Homepage (200 OK)
- ✅ /mission (200 OK)
- ✅ /status (200 OK)
- ✅ WebSocket connectable

### Step 5: Manual Verification

Open in browser: `https://your-url.vercel.app/mission`

**Mission Brief Checklist:**

- [ ] See pattern name and confidence %
- [ ] Chart shows TP/Entry/SL markers
- [ ] Dossier shows risk/reward data
- [ ] Click "Execute Trade" → shows confirm modal
- [ ] Check "I acknowledge risk" → Confirm button enabled
- [ ] Click Confirm → redirects to /status
- [ ] See loading indicator → trade appears within 5s

**Status Board Checklist:**

- [ ] Header shows Operational/Secure beacons
- [ ] Balance and equity display correctly
- [ ] Open trades show with progress bars
- [ ] P/L updates in real-time
- [ ] Click "Alerts" → opens Telegram in new tab
- [ ] Click "Close All" → confirms → positions close

### Step 6: Mobile Check

Test on phone or DevTools mobile emulator:

- [ ] All buttons ≥ 44px tap targets
- [ ] No horizontal scroll
- [ ] Sticky header/footer work
- [ ] Safe areas respected
- [ ] Charts responsive

### Step 7: A11y Check

**Screen Reader Test:**

- [ ] Turn on VoiceOver/NVDA
- [ ] Navigate with Tab key
- [ ] All interactive elements announced
- [ ] Live regions announce changes

**Motion Preference:**

- [ ] Set `prefers-reduced-motion: reduce` in DevTools
- [ ] Animations disabled, UI still premium

---

## Section 2: Demo Deployment (Mock Data)

### Step 1: Enable Mock Mode

Edit `.env.production`:

```bash
NEXT_PUBLIC_USE_MOCKS=1
```

### Step 2: Deploy (Same as Production)

**Vercel:**

```bash
./deploy-vercel.sh
```

**Docker:**

```bash
./deploy-docker.sh
```

### Step 3: Verify Mock Events

Open `/mission` → should see:

- ✅ Mock user profile (VIPER_SIX, COMMANDER level)
- ✅ Mission alerts appear every 20-40s
- ✅ Execute → shows mock live trades on /status
- ✅ Trades update every 2-4s

**Demo is fully interactive without backend!**

---

## Section 3: Rollback Procedure

### Vercel Rollback

```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback <deployment-url>
```

### Docker Rollback

```bash
# Stop current
docker stop bitten-ui

# Run previous image
docker run -d --name bitten-ui -p 3000:3000 \
  --env-file .env.production \
  bitten-ui:previous-tag
```

---

## Section 4: Monitoring & Observability

### Client-Side Logs

All events tagged with `[EventBus]` or `[Fire API]`:

```javascript
// Browser console
[EventBus] Connected
[EventBus] Message: {"topic":"user.profile",...}
[Fire API] Success: op_abc123
```

### Server-Side Metrics (Optional)

UI sends heartbeat every 30s:

```bash
# Check logs for ui.heartbeat
grep "ui.heartbeat" /var/log/your-backend.log
```

Contains: `{ fps, memoryMb, latencyMs }`

---

## Section 5: Troubleshooting

### Issue: WebSocket Won't Connect

**Check:**

1. Backend running? `curl http://134.199.204.67:8888/healthz`
2. Firewall blocking? `telnet 134.199.204.67 8888`
3. CORS headers? Check browser DevTools Network tab

**Fix:**

```nginx
# NGINX config
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### Issue: Fire Endpoint 404

**Check:**

1. Endpoint exists? `curl -i http://134.199.204.67:8888/api/fire`
2. CORS headers? Check browser console

**Fix:** Verify `NEXT_PUBLIC_API_FIRE` env var

### Issue: Trades Not Updating

**Check:**

1. WebSocket connected? See `[EventBus] Connected` in console
2. Backend emitting deltas? Check server logs
3. Topic name correct? Should be `trades.delta`

---

## Section 6: Performance SLA

Monitor these metrics:

| Metric            | Target  | Critical |
| ----------------- | ------- | -------- |
| Page Load (FCP)   | < 1.5s  | < 3s     |
| WebSocket Latency | < 100ms | < 250ms  |
| Fire API Response | < 500ms | < 1s     |
| Delta Frequency   | 1-5s    | 10s max  |
| Memory Usage      | < 150MB | < 300MB  |
| CPU (idle)        | < 10%   | < 30%    |

---

## Section 7: Post-Launch Checklist

Within 24 hours:

- [ ] Monitor error rate (< 1%)
- [ ] Check WebSocket reconnect count
- [ ] Verify trade confirmations arriving
- [ ] Review user feedback
- [ ] Document any issues
- [ ] Plan next feature (War Room, Stats)

---

## Section 8: Emergency Contacts

**If live trading is affected:**

1. Set `NEXT_PUBLIC_USE_MOCKS=1` immediately
2. Redeploy to disable real trading
3. Investigate backend issue
4. Test fix in staging
5. Re-enable with `NEXT_PUBLIC_USE_MOCKS=0`

---

## Quick Reference Commands

```bash
# Build & verify locally
npm run build

# Deploy to Vercel
./deploy-vercel.sh

# Deploy via Docker
./deploy-docker.sh

# Run smoke tests
./smoke-tests.sh https://your-url.vercel.app

# View Docker logs
docker logs -f bitten-ui

# Rollback Vercel
vercel rollback <url>

# Toggle mock mode (emergency)
# Edit .env.production → NEXT_PUBLIC_USE_MOCKS=1
# Then redeploy
```

---

## Success Criteria ✅

**Go-live is successful when:**

- ✅ /mission and /status respond 200 OK
- ✅ WebSocket connects and receives messages
- ✅ Execute trade → 202 Accepted → position appears
- ✅ Close all → positions removed
- ✅ Mobile responsive (no scrolling issues)
- ✅ A11y: keyboard nav + screen reader friendly
- ✅ Error rate < 1% over 1 hour

---

**You're ready to go live. Good luck! 🚀**
