# BITTEN Email Service Setup Guide

This guide covers the complete setup and configuration of the email service for BITTEN Press Pass campaigns.

## Overview

The BITTEN email service supports multiple providers and handles automated email campaigns for Press Pass users. It includes:

- Multi-provider support (SMTP, SendGrid, AWS SES)
- Automated Press Pass email campaigns
- Email tracking and analytics
- Template-based email system
- Scheduled email delivery
- Bounce and unsubscribe handling

## Email Service Architecture

```
┌─────────────────────┐     ┌──────────────────┐
│   Press Pass        │────▶│  Email Service   │
│   Activation        │     │                  │
└─────────────────────┘     └────────┬─────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Email Provider  │
                            ├─────────────────┤
                            │ • SMTP          │
                            │ • SendGrid      │
                            │ • AWS SES       │
                            └─────────────────┘
```

## 1. Environment Configuration

Add these variables to your `.env` file:

### General Email Settings
```bash
# Email Provider (smtp, sendgrid, or ses)
EMAIL_PROVIDER=smtp

# From Address
EMAIL_FROM=noreply@bitten.trading
EMAIL_FROM_NAME=BITTEN Trading
```

### SMTP Configuration (Gmail Example)
```bash
# SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_USE_TLS=true
```

### SendGrid Configuration
```bash
# SendGrid API Key
SENDGRID_API_KEY=SG.your-sendgrid-api-key
```

### AWS SES Configuration
```bash
# AWS Region
AWS_REGION=us-east-1
# Note: AWS credentials should be configured via AWS CLI or IAM role
```

## 2. Setting Up Email Providers

### Option A: SMTP (Recommended for Getting Started)

1. **Gmail Setup:**
   - Enable 2-factor authentication
   - Generate app-specific password:
     - Go to https://myaccount.google.com/apppasswords
     - Create new app password for "Mail"
     - Use this password in `SMTP_PASSWORD`

2. **Other SMTP Providers:**
   - **Outlook:** smtp.office365.com:587
   - **Yahoo:** smtp.mail.yahoo.com:587
   - **Custom:** Use your provider's SMTP settings

### Option B: SendGrid (Recommended for Production)

1. **Create SendGrid Account:**
   - Sign up at https://sendgrid.com
   - Verify your domain
   - Create API key with "Mail Send" permissions

2. **Configure Domain Authentication:**
   - Add SendGrid DNS records
   - Verify domain ownership
   - Enable click and open tracking

### Option C: AWS SES (For AWS Users)

1. **Setup SES:**
   - Verify domain in AWS SES console
   - Move out of sandbox mode
   - Configure IAM permissions

2. **Install AWS CLI:**
   ```bash
   pip install boto3
   aws configure
   ```

## 3. Database Setup

Run the email tracking migrations:

```bash
cd /opt/bitten/HydraX-v2
sqlite3 data/bitten_xp.db < migrations/email_tracking_tables.sql
```

## 4. Email Templates

Email templates are stored in `/templates/emails/`. Each campaign email has its own template:

- `press_pass_welcome.html` - Welcome email (Day 0)
- `press_pass_day1.html` - First trade prompt (Day 1)
- `press_pass_day3.html` - Midnight Hammer results (Day 3)
- `press_pass_day7.html` - Week 1 results (Day 7)
- `press_pass_day14.html` - Halfway reminder (Day 14)
- `press_pass_day21.html` - Week 3 results (Day 21)
- `press_pass_day25.html` - 5-day warning (Day 25)
- `press_pass_day28.html` - 48-hour warning (Day 28)
- `press_pass_day29.html` - Last day warning (Day 29)
- `press_pass_expired.html` - Expiration notice (Day 30)

### Template Variables

Templates use Jinja2 syntax with these available variables:

```python
{
    "username": "User's Telegram username",
    "email": "User's email address",
    "days_remaining": "Days left in Press Pass",
    "days_elapsed": "Days since activation",
    "total_profits": "Total profits made",
    "win_rate": "User's win rate percentage",
    "trades_count": "Total number of trades",
    "best_trade": "Best single trade profit",
    "account_growth": "Percentage account growth",
    "current_tier": "User's current tier",
    "next_tier": "Next available tier",
    "expiry_date": "Press Pass expiry date",
    "telegram_link": "Link to Telegram bot"
}
```

## 5. Testing Email Service

Run the test script to verify configuration:

```bash
cd /opt/bitten/HydraX-v2
python test_email_service.py
```

This will:
1. Test your email provider connection
2. Send a test email
3. Test template rendering
4. Verify all settings

## 6. Starting the Email Scheduler

### Development Mode
```bash
python src/bitten_core/email_scheduler.py
```

### Production Mode (Systemd)
```bash
# Copy service file
sudo cp scripts/bitten_email_scheduler.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable bitten_email_scheduler
sudo systemctl start bitten_email_scheduler

# Check status
sudo systemctl status bitten_email_scheduler
```

## 7. Email Campaign Flow

### Press Pass Activation Flow

1. User claims Press Pass
2. Welcome email sent immediately
3. Campaign emails scheduled based on activation date
4. Expiry reminders sent at 5, 2, and 1 day marks
5. Expiration email sent on day 30

### Email Scheduling

The scheduler runs these tasks:
- **Every minute:** Process email queue
- **Every 30 minutes:** Check for scheduled campaign emails
- **Every hour:** Update campaign statistics
- **Daily at 3 AM:** Clean up old data

## 8. Monitoring and Analytics

### View Email Statistics
```sql
-- Campaign performance
SELECT * FROM email_campaign_performance;

-- User engagement
SELECT * FROM user_email_engagement;

-- Daily stats
SELECT * FROM email_campaign_stats 
WHERE date >= date('now', '-7 days');
```

### Check Email Queue
```sql
-- Pending emails
SELECT * FROM email_queue 
WHERE status = 'pending' 
ORDER BY scheduled_for;

-- Failed emails
SELECT * FROM email_queue 
WHERE status = 'failed'
ORDER BY last_attempt_at DESC;
```

## 9. Troubleshooting

### Common Issues

1. **SMTP Authentication Failed**
   - Verify username and password
   - Check if 2FA is enabled (use app password)
   - Ensure "Less secure apps" is enabled (if applicable)

2. **Emails Not Sending**
   - Check email scheduler logs: `/var/log/bitten/email_scheduler.log`
   - Verify environment variables are set
   - Test with `test_email_service.py`

3. **Templates Not Found**
   - Ensure templates exist in `/templates/emails/`
   - Check file permissions
   - Verify template names match configuration

4. **Rate Limiting**
   - SMTP: Usually 500-1000 emails/day
   - SendGrid: Based on your plan
   - AWS SES: Start with 200/day, increases with reputation

### Debug Mode

Enable debug logging:
```python
# In email_service.py
logging.basicConfig(level=logging.DEBUG)
```

## 10. Best Practices

1. **Email Deliverability**
   - Use verified domains
   - Set up SPF, DKIM, and DMARC records
   - Monitor bounce rates
   - Handle unsubscribes properly

2. **Campaign Optimization**
   - A/B test subject lines
   - Monitor open rates (aim for >20%)
   - Track click-through rates
   - Optimize send times

3. **Security**
   - Never commit credentials to git
   - Use environment variables
   - Rotate API keys regularly
   - Monitor for suspicious activity

4. **Compliance**
   - Include unsubscribe links
   - Honor opt-out requests
   - Follow CAN-SPAM/GDPR rules
   - Keep records of consent

## 11. Integration with Press Pass System

The email service integrates automatically with the Press Pass system:

```python
# In press_pass activation
from bitten_core.press_pass_email_automation import get_email_automation

automation = get_email_automation()
automation.trigger_welcome_email(user_id, email, username)
```

## 12. Email Service API

### Sending Individual Emails
```python
from bitten_core.email_service import create_email_service

email_service = create_email_service()
email_service.send_email(
    to_email="user@example.com",
    subject="Test Email",
    html_content="<h1>Hello World</h1>",
    text_content="Hello World"
)
```

### Sending Template Emails
```python
email_service.send_template_email(
    to_email="user@example.com",
    template_name="press_pass_welcome.html",
    template_data={"username": "TestUser", "days_remaining": 30}
)
```

### Batch Emails
```python
recipients = [
    {"email": "user1@example.com", "data": {"username": "User1"}},
    {"email": "user2@example.com", "data": {"username": "User2"}}
]

email_service.send_batch_emails(
    recipients=recipients,
    template_name="announcement.html",
    default_data={"announcement": "New feature launched!"}
)
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in `/var/log/bitten/`
3. Test with `test_email_service.py`
4. Contact support with error logs