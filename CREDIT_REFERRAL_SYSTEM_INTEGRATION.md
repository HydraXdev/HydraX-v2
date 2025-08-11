# 🎯 BITTEN Credit Referral System - Integration Guide

## 📋 System Overview

The BITTEN Credit Referral System provides a complete $10 credit solution with:
- **Telegram Bot Commands**: `/recruit` and `/credits`
- **Automatic Stripe Integration**: Credit application to invoices
- **Gamification**: XP rewards, badges, and military progression
- **Admin Management**: Full admin API for credit oversight

## 🔧 Core Components

### 1. **Credit Referral System** (`credit_referral_system.py`)
- Database schema with SQLite storage
- Referral code generation and tracking
- Credit balance management
- Anti-abuse protection (self-referral, duplicates)

### 2. **Telegram Bot Commands** (`credit_referral_bot_commands.py`)
- `/recruit` - Generate and share referral links
- `/credits` - View credit balance and history
- Interactive inline keyboards
- Real-time statistics

### 3. **Stripe Integration** (`stripe_credit_manager.py`)
- Automatic credit application to invoices
- Payment confirmation handling
- Coupon-based credit system
- Customer metadata tracking

### 4. **Webhook Handler** (Updated `stripe_webhook_handler.py`)
- `invoice.created` - Apply credits before payment
- `payment_succeeded` - Confirm referral credits
- Integrated with existing webhook system

### 5. **Gamification System** (`referral_gamification_hooks.py`)
- Military rank progression (LONE_WOLF → BRIGADE_GENERAL)
- XP rewards and badge system
- Milestone achievements
- War room integration

### 6. **Admin API** (`credit_admin_api.py`)
- Credit management endpoints
- Top referrers leaderboard
- Manual credit application/revocation
- Export functionality

---

## 🚀 Quick Integration Steps

### Step 1: Bot Integration
Add to your main bot file (`bitten_production_bot.py`):

```python
from src.bitten_core.credit_referral_bot_commands import get_credit_referral_bot_commands

# Initialize
credit_commands = get_credit_referral_bot_commands()

# Add command handlers
@bot.message_handler(commands=['recruit'])
async def handle_recruit(message):
    await credit_commands.handle_recruit_command(message, None)

@bot.message_handler(commands=['credits'])
async def handle_credits(message):
    await credit_commands.handle_credits_command(message, None)

@bot.callback_query_handler(func=lambda call: True)
async def handle_callback(call):
    await credit_commands.handle_callback_query(call, None)
```

### Step 2: Webapp Integration
Add to your Flask app (`webapp_server_optimized.py`):

```python
from src.bitten_core.credit_admin_api import register_credit_admin_blueprint

# Register admin endpoints
register_credit_admin_blueprint(app)
```

### Step 3: Stripe Configuration
Ensure these webhooks are configured in Stripe:
- `invoice.created`
- `payment_intent.succeeded`
- Customer metadata includes `user_id` or `telegram_id`

### Step 4: Database Setup
The system auto-creates its database on first use:
- Location: `/root/HydraX-v2/data/credit_referrals.db`
- Tables: `referral_codes`, `referral_credits`, `user_credit_balances`, `gamification_rewards`

---

## 🧪 Testing

Run the comprehensive test suite:
```bash
cd /root/HydraX-v2
python3 test_credit_referral_system.py
```

**Test Coverage:**
- ✅ Basic referral flow (code generation → usage → payment → credit)
- ✅ Credit application to invoices
- ✅ Statistics and reporting
- ✅ Edge cases and error handling
- ✅ Complete integration test

---

## 📊 Usage Flow

### User Journey:
1. **User types `/recruit`** → Gets referral link `https://t.me/Bitten_Commander_bot?start=ABC123`
2. **Friend clicks link** → Registers with referral code
3. **Friend subscribes ($39+ tier)** → Makes first payment
4. **Stripe webhook triggers** → $10 credit applied to referrer
5. **Referrer's next bill** → Credit automatically deducted
6. **XP & badges earned** → Military progression unlocked

### Admin Features:
- View top recruiters: `GET /api/admin/credits/top-referrers`
- Manual credit adjustment: `POST /api/admin/credits/apply`
- Export all data: `GET /api/admin/credits/export`
- Force confirm payment: `POST /api/admin/credits/force-confirm`

---

## 🎮 Gamification Features

### Military Ranks:
- **FIRST_RECRUIT** (1): +100 XP, RECRUITER badge
- **SQUAD_BUILDER** (5): +500 XP, unlocks recruitment dashboard
- **PLATOON_LEADER** (10): +1000 XP, advanced analytics
- **COMPANY_COMMANDER** (25): +2500 XP, leaderboard features
- **BATTALION_COLONEL** (50): +5000 XP, custom campaigns
- **BRIGADE_GENERAL** (100+): +10000 XP, legendary status

### XP Rewards:
- Base referral: +50 XP
- Milestone bonuses: +100 to +10,000 XP
- Veteran multiplier: Up to 1.5x for high performers
- Credit milestones: +5 XP per $50 earned

---

## 🔒 Security Features

### Anti-Abuse:
- ✅ Self-referral prevention
- ✅ Duplicate referral blocking
- ✅ Payment confirmation required
- ✅ Credit application audit trail
- ✅ Admin authentication required

### Data Protection:
- SQLite database with proper indexing
- User ID anonymization in logs
- Secure admin token authentication
- Rate limiting on admin endpoints

---

## 📈 Admin Dashboard Metrics

### Key Stats Available:
```json
{
  "total_credits_issued": 1250.0,
  "total_referrals": 125,
  "pending_credits": 50.0,
  "top_referrers": [
    {"user_id": "123", "referrals": 15, "total_earned": 150.0}
  ]
}
```

### Monitoring Endpoints:
- System health: `/api/admin/credits/stats`
- User lookup: `/api/admin/credits/user/<user_id>`
- Transaction search: `/api/admin/credits/search?user_id=123`
- Pending credits: `/api/admin/credits/pending`

---

## 🚨 Integration Checklist

### Pre-Production:
- [ ] Bot commands integrated with main bot
- [ ] Stripe webhooks configured (`invoice.created`, `payment_intent.succeeded`)
- [ ] Customer metadata includes user/telegram ID
- [ ] Admin authentication token set (`X-Admin-Token`)
- [ ] Database permissions configured
- [ ] Test with real Stripe test mode

### Post-Launch:
- [ ] Monitor webhook delivery in Stripe dashboard
- [ ] Track credit application success rate
- [ ] Monitor gamification reward distribution
- [ ] Review admin dashboard metrics
- [ ] Set up automated backup of credit database

---

## 🔧 Configuration

### Environment Variables:
```bash
# Optional - defaults provided
CREDIT_REFERRAL_DB_PATH="/root/HydraX-v2/data/credit_referrals.db"
ADMIN_TOKEN="BITTEN_ADMIN_2025"  # Change for production
STRIPE_API_KEY="REDACTED"     # Your Stripe secret key
```

### Stripe Webhook URLs:
```
https://yourdomain.com/api/stripe/webhook
```

### Admin API Authentication:
```bash
curl -H "X-Admin-Token: BITTEN_ADMIN_2025" \
  https://yourdomain.com/api/admin/credits/stats
```

---

## 🎯 Success Metrics

After integration, you should see:
- **Referral codes generated** via `/recruit` command
- **Credits applied automatically** to user invoices
- **XP and badges awarded** for recruitment milestones
- **Admin dashboard populated** with referral statistics
- **$10 credit reduction** on subscriber invoices

---

## 🆘 Troubleshooting

### Common Issues:

**Credits not applying to invoices:**
- Check Stripe webhook delivery
- Verify customer metadata has `user_id`
- Check logs in webhook handler

**Referral codes not working:**
- Verify database permissions
- Check anti-abuse logic (self/duplicate referrals)
- Review bot command integration

**Gamification not triggering:**
- Check import path for gamification hooks
- Verify XP system integration
- Review reward processing logs

**Admin API not accessible:**
- Verify authentication token
- Check Flask blueprint registration
- Review endpoint URL paths

### Debug Commands:
```bash
# Check database structure
sqlite3 /root/HydraX-v2/data/credit_referrals.db ".schema"

# View recent referrals
sqlite3 /root/HydraX-v2/data/credit_referrals.db "SELECT * FROM referral_credits ORDER BY created_at DESC LIMIT 10"

# Test bot commands manually
python3 -c "
from src.bitten_core.credit_referral_system import get_credit_referral_system
system = get_credit_referral_system()
print(system.get_admin_stats())
"
```

---

## 🎉 Deployment Ready!

The BITTEN Credit Referral System is fully functional and ready for production deployment. All components are modular, tested, and integrated with your existing infrastructure.

**Key Achievement**: Complete $10 credit system that automatically rewards referrers when their recruits make their first payment, with full gamification and admin oversight.

**Next Steps**: Integrate bot commands, configure Stripe webhooks, and launch to your users!