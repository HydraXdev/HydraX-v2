# BITTEN Stripe Quick Setup Guide (Monthly Only)

## What You Need From Stripe

1. **API Keys**
   - ✅ You have: `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`
   - ❓ Still need: Webhook signing secret (`whsec_...`)

2. **Products & Prices**
   - Need to create 4 products (NIBBLER, FANG, COMMANDER)
   - Monthly prices only ($39, $79, $139, )

## Step 1: Create Products

Run this command:
```bash
python setup_stripe_products.py
```

This will:
- Create all 4 products in your Stripe account
- Set up monthly pricing
- Give you the price IDs to add to .env

## Step 2: Set Up Webhook

1. Go to: https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter your URL: `https://your-domain.com/stripe/webhook`
4. Select these events:
   - `customer.subscription.created`
   - `customer.subscription.updated` 
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the signing secret (starts with `whsec_`)

## Step 3: Update .env

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=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
STRIPE_WEBHOOK_SECRET=whsec_[YOUR_WEBHOOK_SECRET_HERE]

# Price IDs (from setup script)
STRIPE_PRICE_NIBBLER=price_[from_setup_script]
STRIPE_PRICE_FANG=price_[from_setup_script]
STRIPE_PRICE_COMMANDER=price_[from_setup_script]
STRIPE_PRICE_=price_[from_setup_script]
```

## Step 4: Configure Stripe Settings

1. **Payment Methods**
   - Dashboard → Settings → Payment methods
   - Enable: Card payments only

2. **Customer Portal**
   - Dashboard → Settings → Billing → Customer portal
   - Enable: Update payment methods
   - Enable: Cancel subscriptions
   - Disable: Switch plans (we handle this in-app)

3. **Retry Schedule** (for failed payments)
   - Dashboard → Settings → Subscriptions and emails
   - Set retry schedule:
     - First retry: 1 day
     - Second retry: 3 days
     - Final: Cancel subscription

4. **Email Notifications**
   - Keep defaults (payment receipts, etc.)

## Step 5: Add to Your Flask App

```python
from src.bitten_core.stripe_webhook_endpoint import register_stripe_webhook

# In your main app
register_stripe_webhook(app)
```

## How It Works

### User Flow:
1. **Day 1-13**: User uses bot freely, no payment mentions
2. **Day 14**: Bot sends ONE reminder about trial ending
3. **Day 15**: Trial expires, features lock
4. **Payment**: User clicks subscribe → Stripe Checkout → Auto-activation

### Subscription Features:
- ✅ Monthly billing only
- ✅ Cancel anytime
- ✅ 2-day grace period for failed payments
- ✅ Automatic tier upgrades/downgrades
- ✅ Proration handled by Stripe

### What Happens on Events:
- **Subscription Created**: User tier activates, features unlock
- **Payment Success**: Features stay unlocked
- **Payment Failed**: 2-day grace period starts
- **Subscription Cancelled**: Access until period end

## Testing

Use these test cards:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

## Next Steps

After setup:
1. Test with a real subscription
2. Monitor webhook logs
3. Set up monitoring alerts
4. Create customer support docs

## Common Issues

**Webhook not working?**
- Check endpoint URL is correct
- Verify signing secret in .env
- Check server logs for errors

**Products not creating?**
- Verify API key is live key
- Check Stripe account is activated
- Ensure no duplicate products exist

**Payments failing?**
- Check customer has valid payment method
- Verify price IDs are correct
- Check currency matches account