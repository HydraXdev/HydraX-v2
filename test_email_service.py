#!/usr/bin/env python3
"""
Test script for BITTEN Email Service
Tests email configuration and sends test emails
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bitten_core.email_service import create_email_service, EmailService
from bitten_core.press_pass_email_automation import PressPassEmailAutomation


def test_smtp_connection():
    """Test SMTP connection"""
    print("\n=== Testing SMTP Connection ===")
    
    # Check for required environment variables
    required_vars = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following in your .env file:")
        print("SMTP_HOST=smtp.gmail.com")
        print("SMTP_PORT=587")
        print("SMTP_USERNAME=your-email@gmail.com")
        print("SMTP_PASSWORD=your-app-password")
        return False
    
    try:
        email_service = create_email_service("smtp")
        print("✅ SMTP configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ SMTP configuration error: {str(e)}")
        return False


def test_sendgrid_connection():
    """Test SendGrid connection"""
    print("\n=== Testing SendGrid Connection ===")
    
    if not os.getenv("SENDGRID_API_KEY"):
        print("⚠️  SendGrid API key not configured")
        return False
    
    try:
        email_service = create_email_service("sendgrid")
        print("✅ SendGrid configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ SendGrid configuration error: {str(e)}")
        return False


def test_ses_connection():
    """Test AWS SES connection"""
    print("\n=== Testing AWS SES Connection ===")
    
    if not os.getenv("AWS_REGION"):
        print("⚠️  AWS SES not configured")
        return False
    
    try:
        email_service = create_email_service("ses")
        print("✅ AWS SES configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ AWS SES configuration error: {str(e)}")
        return False


def send_test_email(provider: str, test_email: str):
    """Send a test email"""
    print(f"\n=== Sending Test Email via {provider.upper()} ===")
    
    try:
        email_service = create_email_service(provider)
        
        # Test HTML content
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #ff6b6b;">BITTEN Email Service Test</h1>
            <p>This is a test email from the BITTEN trading system.</p>
            <p><strong>Provider:</strong> {provider}</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <hr>
            <p style="color: #666;">If you received this email, your email service is configured correctly!</p>
        </body>
        </html>
        """.format(
            provider=provider.upper(),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Send email
        success = email_service.send_email(
            to_email=test_email,
            subject=f"BITTEN Test Email - {provider.upper()}",
            html_content=html_content,
            text_content="This is a test email from BITTEN trading system."
        )
        
        if success:
            print(f"✅ Test email sent successfully to {test_email}")
        else:
            print(f"❌ Failed to send test email")
        
        return success
        
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        return False


def test_template_email(test_email: str):
    """Test template-based email"""
    print("\n=== Testing Template Email ===")
    
    try:
        # Check if template exists
        template_path = "templates/emails/press_pass_welcome.html"
        if not os.path.exists(template_path):
            print(f"⚠️  Template not found: {template_path}")
            print("Creating sample template...")
            
            # Create template directory
            os.makedirs("templates/emails", exist_ok=True)
            
            # Create sample template
            with open(template_path, "w") as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome to BITTEN Press Pass</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px;">
        <h1 style="color: #ff6b6b; text-align: center;">🎖️ Your BITTEN Press Pass is ACTIVE!</h1>
        
        <p>Hey {{ username }}!</p>
        
        <p>Your Press Pass is now active and you have <strong>{{ days_remaining }} days</strong> to make the most of it!</p>
        
        <div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3>Your Press Pass Benefits:</h3>
            <ul>
                <li>✅ Access to ALL trading signals</li>
                <li>✅ Priority alert delivery</li>
                <li>✅ Exclusive Midnight Hammer access</li>
                <li>✅ 30 days of unlimited trades</li>
            </ul>
        </div>
        
        <p style="text-align: center;">
            <a href="{{ telegram_link }}" style="display: inline-block; padding: 12px 30px; background-color: #ff6b6b; color: white; text-decoration: none; border-radius: 5px;">
                Start Trading Now
            </a>
        </p>
        
        <p style="color: #666; font-size: 12px; text-align: center; margin-top: 30px;">
            BITTEN Trading | Your Press Pass expires on {{ expiry_date }}
        </p>
    </div>
</body>
</html>
                """)
            print("✅ Sample template created")
        
        # Test email automation
        automation = PressPassEmailAutomation()
        
        # Create test data
        template_data = {
            "username": "TestUser",
            "days_remaining": 30,
            "expiry_date": "December 31, 2024",
            "telegram_link": "https://t.me/BITTENbot"
        }
        
        # Send template email
        success = automation.email_service.send_template_email(
            to_email=test_email,
            template_name="press_pass_welcome.html",
            template_data=template_data,
            subject="🎖️ Your BITTEN Press Pass is ACTIVE!"
        )
        
        if success:
            print(f"✅ Template email sent successfully to {test_email}")
        else:
            print("❌ Failed to send template email")
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing template email: {str(e)}")
        return False


def main():
    """Main test function"""
    print("=== BITTEN Email Service Test ===")
    print("This script will test your email service configuration")
    
    # Get test email address
    test_email = input("\nEnter your email address for testing: ").strip()
    
    if not test_email or "@" not in test_email:
        print("❌ Invalid email address")
        return
    
    # Check which provider to use
    provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()
    print(f"\nConfigured email provider: {provider}")
    
    # Test connections
    if provider == "smtp":
        if test_smtp_connection():
            send_test_email("smtp", test_email)
    elif provider == "sendgrid":
        if test_sendgrid_connection():
            send_test_email("sendgrid", test_email)
    elif provider == "ses":
        if test_ses_connection():
            send_test_email("ses", test_email)
    else:
        print(f"❌ Unknown email provider: {provider}")
        return
    
    # Test template email
    test_template_email(test_email)
    
    print("\n=== Email Service Test Complete ===")
    
    # Show configuration guide
    print("\n📋 Email Service Configuration Guide:")
    print("\n1. Add these to your .env file:")
    print("   EMAIL_PROVIDER=smtp  # Options: smtp, sendgrid, ses")
    print("   EMAIL_FROM=noreply@bitten.trading")
    print("   EMAIL_FROM_NAME=BITTEN Trading")
    print("\n2. For SMTP (Gmail example):")
    print("   SMTP_HOST=smtp.gmail.com")
    print("   SMTP_PORT=587")
    print("   SMTP_USERNAME=your-email@gmail.com")
    print("   SMTP_PASSWORD=your-app-password")
    print("   SMTP_USE_TLS=true")
    print("\n3. For SendGrid:")
    print("   SENDGRID_API_KEY=your-sendgrid-api-key")
    print("\n4. For AWS SES:")
    print("   AWS_REGION=us-east-1")
    print("   (Requires AWS credentials configured)")


if __name__ == "__main__":
    main()