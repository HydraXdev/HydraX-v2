# BITTEN Stripe Integration Setup Guide

## Overview
BITTEN uses a 15-day free trial system with Stripe for subscription management. Users get full access for 15 days, with payment prompts starting on day 14.

## Setup Steps

### 1. Create Stripe Account
1. Go to https://stripe.com and sign up
2. Complete business verification
3. Enable **Test Mode** for development

### 2. Get API Keys
1. Go to Developers → API Keys
2. Copy your keys:
   - **Publishable key**: `pk_test_...` (for frontend)
   - **Secret key**: `sk_test_...` (for backend)

### 3. Set Environment Variables
Add to your `.env` file:
```bash
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### 4. Create Products and Prices
Run this script once to create your products in Stripe:

```python
import stripe
stripe.api_key = "sk_test_your_secret_key_here"

# Create products
products = {
    'NIBBLER': stripe.Product.create(
        name='BITTEN Nibbler',
        description='Entry tier - 6 trades/day, manual only'
    ),
    'FANG': stripe.Product.create(
        name='BITTEN Fang', 
        description='Advanced tier - 10 trades/day, sniper mode'
    ),
    'COMMANDER': stripe.Product.create(
        name='BITTEN Commander',
        description='Pro tier - 20 trades/day, full automation'
    ),
    'APEX': stripe.Product.create(
        name='BITTEN Apex',
        description='Elite tier - Unlimited trades, priority support'
    )
}

# Create prices (monthly and annual)
prices = {}
pricing = {
    'NIBBLER': {'monthly': 3900, 'annual': 31200},
    'FANG': {'monthly': 8900, 'annual': 71200},
    'COMMANDER': {'monthly': 13900, 'annual': 111200},
    'APEX': {'monthly': 18800, 'annual': 150400}
}

for tier, product in products.items():
    # Monthly price
    prices[f'{tier}_MONTHLY'] = stripe.Price.create(
        product=product.id,
        unit_amount=pricing[tier]['monthly'],
        currency='usd',
        recurring={'interval': 'month'},
        metadata={'tier': tier, 'billing': 'monthly'}
    )
    
    # Annual price
    prices[f'{tier}_ANNUAL'] = stripe.Price.create(
        product=product.id,
        unit_amount=pricing[tier]['annual'],
        currency='usd',
        recurring={'interval': 'year'},
        metadata={'tier': tier, 'billing': 'annual'}
    )

# Print price IDs to add to .env
for name, price in prices.items():
    print(f"STRIPE_PRICE_{name}={price.id}")
```

### 5. Configure Webhooks
1. Go to Developers → Webhooks
2. Add endpoint: `https://your-domain.com/stripe/webhook`
3. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `customer.subscription.trial_will_end`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the webhook signing secret

### 6. Configure Customer Portal
1. Go to Settings → Billing → Customer portal
2. Enable features:
   - ✅ Allow customers to update payment methods
   - ✅ Allow customers to cancel subscriptions
   - ✅ Allow customers to switch plans
3. Set cancellation policy: "Cancel at end of billing period"
4. Save settings

### 7. Set Trial Period
The 15-day trial is configured in code:
```python
subscription = stripe.Subscription.create(
    customer=customer_id,
    items=[{'price': price_id}],
    trial_period_days=15,  # 15-day free trial
    payment_behavior='default_incomplete'
)
```

### 8. Configure Grace Period
In Stripe Dashboard:
1. Go to Settings → Subscriptions and emails
2. Set "Retry schedule" to:
   - First retry: 1 day
   - Second retry: 3 days (this gives 2-day grace as requested)
   - Final action: Cancel subscription

## User Flow

### Day 1-13: Silent Trial
- User gets `/start` command
- Full access granted immediately
- NO payment mentions
- User explores and trades freely

### Day 14: First Payment Prompt
- Automated message sent via Telegram
- "Your trial ends tomorrow!"
- Show subscription options
- One-click payment link

### Day 15: Trial Ends
- If no payment: Features locked
- Only Subscribe button works
- 45-day data retention begins

### Payment Collection
When user clicks "Subscribe":
1. Create Stripe Checkout session
2. User enters card details
3. Subscription starts immediately
4. Features unlock instantly

### Subscription Management
- Auto-renewal enabled by default
- 2-day grace period for failed payments
- Users can cancel anytime (ends at period end)
- Portal link for self-service

## Testing

### Test Card Numbers
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Requires auth: `4000 0025 0000 3155`

### Test Scenarios
1. **New User Trial**
   - Start bot with `/start`
   - Verify 15-day access
   - Check day 14 reminder

2. **Trial Conversion**
   - Use test card to subscribe
   - Verify immediate access
   - Check Stripe dashboard

3. **Failed Payment**
   - Use decline card
   - Verify grace period
   - Test retry logic

4. **Cancellation**
   - Cancel via customer portal
   - Verify end-of-period access
   - Test reactivation

## Monitoring

### Key Metrics
- Trial-to-paid conversion rate
- Payment failure rate
- Churn rate by tier
- MRR growth

### Alerts to Set
- Failed payments > 10%
- Webhook failures
- Subscription cancellations spike
- Trial abandonments > 50%

## Security Notes
- Never log card details
- Use HTTPS for all endpoints
- Validate webhook signatures
- Store customer IDs only
- PCI compliance via Stripe

## Support Considerations
- Provide customer portal link in `/help`
- Clear refund policy (within 7 days)
- Document upgrade/downgrade behavior
- Handle currency conversions