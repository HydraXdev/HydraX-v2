# BITTEN Landing Page & Email Capture System - Complete Deployment Guide

## 🚀 Overview

This guide covers the deployment of the complete landing page and email capture system for Press Pass, including:
- High-converting landing page with email capture
- Press Pass claim and activation system
- A/B testing framework
- Analytics tracking
- Conversion optimization dashboard
- Automated email campaigns
- Seamless onboarding integration

## 📁 System Components

### 1. **Landing Page** (`/landing/index_v2.html`)
- Responsive design with urgency messaging
- Real-time spot counter
- Email capture form with validation
- Social proof with live metrics
- A/B testing integration

### 2. **Press Pass Manager** (`src/bitten_core/press_pass_manager.py`)
- Handles Press Pass claims and limits
- Email campaign management
- Conversion tracking
- Weekly limit enforcement (200 passes)
- Daily urgency counter

### 3. **Analytics Tracker** (`src/bitten_core/analytics_tracker.py`)
- Real-time event tracking
- Funnel analysis
- Integration with GA4, Facebook Pixel
- Custom metrics dashboard

### 4. **A/B Testing Framework** (`src/bitten_core/ab_testing_framework.py`)
- Experiment management
- Statistical significance testing
- Variant assignment
- Performance tracking

### 5. **Onboarding System** (`src/bitten_core/onboarding_system.py`)
- Multi-stage onboarding flow
- Progress tracking
- Automated actions
- Stuck user detection

### 6. **Conversion Dashboard** (`src/bitten_core/conversion_dashboard.py`)
- Real-time metrics
- Funnel visualization
- A/B test results
- Hourly trends

## 🛠️ Installation

### 1. Install Dependencies

```bash
cd /root/HydraX-v2

# Install Python dependencies
pip install -r requirements.txt

# Additional dependencies for analytics
pip install scipy numpy
```

### 2. Database Setup

```bash
# Run migrations
psql -U bitten_app -d bitten_production < migrations/email_capture_tables.sql
psql -U bitten_app -d bitten_production < migrations/press_pass_tables.sql
```

### 3. Redis Setup

Ensure Redis is running on ports:
- 6379 (default) - General cache
- 6379 db=1 - Press Pass manager
- 6379 db=2 - Rate limiting
- 6379 db=3 - Analytics
- 6379 db=4 - A/B testing
- 6379 db=5 - Onboarding

## ⚙️ Configuration

### 1. Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://bitten_app:password@localhost/bitten_production

# Email Service
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@joinbitten.com

# Analytics
GA_MEASUREMENT_ID=G-XXXXXXXXXX
GA_API_SECRET=your-secret
FB_PIXEL_ID=1234567890
FB_ACCESS_TOKEN=your-token
MIXPANEL_TOKEN=your-token

# Admin
ADMIN_API_KEY=your-secure-admin-key

# Flask
FLASK_SECRET_KEY=your-secret-key
```

### 2. Update Web App

The web app has been updated to serve the new landing page and include all API endpoints.

### 3. Analytics Setup

Replace placeholder IDs in `landing/index_v2.html`:
- Line 23: Replace `GA_MEASUREMENT_ID` with your Google Analytics ID
- Line 38: Replace `FB_PIXEL_ID` with your Facebook Pixel ID

## 🚦 Starting the System

### 1. Start Web Server

```bash
cd /root/HydraX-v2
python -m src.bitten_core.web_app
```

Or with production server:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 src.bitten_core.web_app:app
```

### 2. Start Background Tasks

```bash
# Press Pass expiry checker (run as cron job)
*/30 * * * * cd /root/HydraX-v2 && python -c "from src.bitten_core.press_pass_manager import press_pass_manager; press_pass_manager.check_expiring_passes()"

# Daily analytics aggregation
0 1 * * * cd /root/HydraX-v2 && python -c "from src.bitten_core.analytics_tracker import analytics_tracker; analytics_tracker._flush_events()"
```

### 3. Test the System

```bash
cd /root/HydraX-v2
python test_landing_email_system.py
```

## 📊 A/B Tests Configuration

Current experiments:

### 1. **Press Pass CTA Button** (`press_pass_cta`)
- Control: "ACTIVATE MY PRESS PASS NOW"
- Variant 1: "CLAIM YOUR FREE ACCESS"

### 2. **Urgency Messaging** (`urgency_messaging`)
- Control: "7 SPOTS LEFT"
- Time-based: "5 SPOTS LEFT TODAY"
- Countdown: "3 SPOTS REMAINING"

### 3. **Email Subject Lines** (`email_subject_lines`)
- Control: "🎯 Your BITTEN Press Pass is Ready!"
- Urgency: "⏰ Activate Your Press Pass Before It Expires"

## 📧 Email Campaign Setup

### Email Templates Location
- `/templates/emails/press_pass_welcome.html`
- `/templates/emails/press_pass_day1.html`
- `/templates/emails/press_pass_day3.html`
- `/templates/emails/press_pass_day6.html`
- `/templates/emails/press_pass_day7.html`

### Email Schedule
- **Day 0**: Welcome email (immediate)
- **Day 1**: Quick start guide
- **Day 3**: Performance showcase
- **Day 6**: Urgency reminder
- **Day 7**: Final warning

## 🔗 Integration Points

### 1. Telegram Bot Integration

When user clicks activation link:
```python
# In your Telegram bot handler
if message.text.startswith('/start pp_'):
    claim_token = message.text.split('pp_')[1]
    
    # Activate Press Pass
    response = requests.post(
        'http://localhost:5000/api/press-pass/activate',
        json={
            'claim_token': claim_token,
            'telegram_id': message.from_user.id
        }
    )
```

### 2. Onboarding Flow

```python
# Progress user through onboarding
from src.bitten_core.onboarding_system import onboarding_manager, OnboardingStage

# After Press Pass activation
onboarding_manager.progress_user(
    email,
    OnboardingStage.TELEGRAM_CONNECTED,
    telegram_id=telegram_id
)
```

### 3. Conversion Tracking

```python
# Track tier upgrade
from src.bitten_core.analytics_tracker import track_event

track_event('tier_upgrade', {
    'from_tier': 'press_pass',
    'to_tier': 'NIBBLER',
    'value': 39.00
})
```

## 📈 Monitoring

### 1. Access Dashboard
- URL: `http://your-domain.com/conversion-dashboard`
- Requires admin authentication

### 2. Key Metrics to Monitor
- **Conversion Rate**: Email → Press Pass → Paid Tier
- **Activation Rate**: Press Pass claimed → Activated
- **Time to Convert**: Average hours from claim to payment
- **A/B Test Performance**: Variant conversion rates
- **Funnel Drop-off**: Where users abandon

### 3. Alerts to Set Up
- Daily Press Pass limit approaching (< 5 remaining)
- Weekly limit reached
- Conversion rate drops below threshold
- High bounce rate on landing page

## 🚨 Troubleshooting

### Common Issues

1. **Email not sending**
   - Check SMTP credentials
   - Verify FROM_EMAIL is authorized
   - Check spam folder

2. **Redis connection errors**
   - Ensure Redis is running: `redis-cli ping`
   - Check Redis memory: `redis-cli info memory`

3. **Database connection issues**
   - Verify DATABASE_URL
   - Check PostgreSQL is running
   - Ensure migrations are applied

4. **Analytics not tracking**
   - Verify GA/FB credentials
   - Check browser console for errors
   - Ensure tracking blockers are disabled

## 🔐 Security Considerations

1. **Rate Limiting**
   - 3 claims per IP per hour
   - 2 claims per email per day

2. **Input Validation**
   - Email format validation
   - Name sanitization
   - SQL injection prevention

3. **Token Security**
   - SHA256 hashed tokens
   - 7-day expiration
   - One-time activation

## 📝 Next Steps

1. **Set up production analytics**
   - Create GA4 property
   - Install Facebook Pixel
   - Configure Mixpanel (optional)

2. **Configure email service**
   - Set up SendGrid/Mailgun
   - Create email templates
   - Set up tracking domains

3. **Optimize conversion**
   - Monitor A/B test results
   - Adjust urgency messaging
   - Test new variants

4. **Scale infrastructure**
   - Add Redis persistence
   - Set up database replicas
   - Configure CDN for assets

## 🎯 Success Metrics

Target metrics for first 30 days:
- **Email Capture Rate**: > 25%
- **Press Pass Activation**: > 60%
- **Conversion to Paid**: > 15%
- **Average Time to Convert**: < 4 days
- **Email Open Rate**: > 40%
- **Email Click Rate**: > 20%

## 🆘 Support

For issues or questions:
1. Check logs: `/root/HydraX-v2/logs/`
2. Run diagnostics: `python test_landing_email_system.py`
3. Monitor dashboard: `/conversion-dashboard`

---

**Remember**: The system is designed for high conversion through urgency, social proof, and seamless onboarding. Monitor metrics closely and optimize based on data!