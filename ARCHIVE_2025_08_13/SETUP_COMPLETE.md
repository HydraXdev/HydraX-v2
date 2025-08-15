# 🚀 BITTEN WEBSITE IS LIVE!

## ✅ What's Running Now

1. **Landing Page**: http://134.199.204.67/
   - Military-themed design with all features
   - Links to your Telegram bot: @Bitten_Commander_bot
   - 7-day free trial call-to-action

2. **Compliance Pages**:
   - Terms: http://134.199.204.67/terms
   - Privacy: http://134.199.204.67/privacy
   - Refund Policy: http://134.199.204.67/refund

3. **Stripe Webhook**: http://134.199.204.67/stripe/webhook
   - Ready to receive Stripe events
   - Currently logs events (needs your secret key)

4. **Services Running**:
   - Flask web server on port 5000 (systemd service: bitten-web)
   - Nginx reverse proxy on port 80
   - Auto-starts on reboot

## 🔧 Next Steps to Complete Stripe

### 1. Get Your Stripe Details
You need:
- [ ] Secret API Key (starts with `sk_live_`)
- [ ] Webhook Signing Secret (starts with `whsec_`)
- [ ] Price IDs for each tier

### 2. Update .env File
```bash
nano /root/HydraX-v2/.env
```

Add your real values:
```
STRIPE_SECRET_KEY=sk_live_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
STRIPE_PRICE_NIBBLER=price_xxxxx
STRIPE_PRICE_FANG=price_xxxxx
STRIPE_PRICE_COMMANDER=price_xxxxx
STRIPE_PRICE_=price_xxxxx
```

### 3. Set Up Stripe Webhook
1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter: `http://134.199.204.67/stripe/webhook`
   (or `https://joinbitten.com/stripe/webhook` once you have SSL)
4. Select these events:
   - customer.subscription.created
   - customer.subscription.updated
   - customer.subscription.deleted
   - invoice.payment_succeeded
   - invoice.payment_failed
5. Copy the signing secret to .env

### 4. Get Price IDs
In Stripe Dashboard:
1. Go to Products
2. Find your 4 tiers
3. Click each product
4. Copy the price ID (starts with `price_`)

### 5. Domain Setup (Optional)
If you want joinbitten.com to work:
1. Point joinbitten.com DNS to 134.199.204.67
2. Install SSL certificate:
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d joinbitten.com -d www.joinbitten.com
   ```

## 📊 Monitoring

Check service status:
```bash
systemctl status bitten-web
```

View logs:
```bash
journalctl -u bitten-web -f
```

Restart service:
```bash
systemctl restart bitten-web
```

## 🎯 Test Your Site

1. Visit http://134.199.204.67/
2. Click "START 15-DAY FREE TRIAL"
3. Should open Telegram bot
4. Check webhook logs:
   ```bash
   tail -f /root/HydraX-v2/web.log
   ```

## 🔒 Security Notes

- Change FLASK_SECRET_KEY in .env to something random
- Set up SSL certificate for production
- Consider firewall rules for port 5000 (Flask)

Your landing page is LIVE and ready for customers! 🚀