#!/bin/bash
# Quick setup script for BITTEN web application

echo "🚀 BITTEN Web Setup"
echo "=================="

# 1. Get Stripe price IDs
echo "📋 Step 1: Getting your Stripe price IDs..."
python3 get_stripe_prices.py

echo -e "\n📝 Step 2: Update your .env file with:"
echo "- The price IDs shown above"
echo "- Your webhook signing secret (after creating webhook)"

# 2. Install the service
echo -e "\n🔧 Step 3: To install as a service, run:"
echo "sudo cp bitten-web.service /etc/systemd/system/"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable bitten-web"
echo "sudo systemctl start bitten-web"

# 3. Set up nginx (optional)
echo -e "\n🌐 Step 4: For nginx setup, create /etc/nginx/sites-available/bitten:"
cat << 'EOF'
server {
    listen 80;
    server_name joinbitten.com www.joinbitten.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /stripe/webhook {
        proxy_pass http://localhost:5000/stripe/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Stripe-Signature $http_stripe_signature;
    }
}
EOF

echo -e "\n✅ Step 5: Set up Stripe webhook:"
echo "1. Go to https://dashboard.stripe.com/webhooks"
echo "2. Add endpoint: https://joinbitten.com/stripe/webhook"
echo "3. Select events:"
echo "   - customer.subscription.created"
echo "   - customer.subscription.updated"
echo "   - customer.subscription.deleted"
echo "   - invoice.payment_succeeded"
echo "   - invoice.payment_failed"
echo "4. Copy the signing secret to .env as STRIPE_WEBHOOK_SECRET"

echo -e "\n🎯 Step 6: Update your Telegram bot username in:"
echo "- /root/HydraX-v2/landing/index.html"
echo "- Replace 'your_bot_username' with your actual bot"

echo -e "\n📱 Step 7: Test everything:"
echo "1. Visit http://your-ip:5000 (or https://joinbitten.com if nginx is set up)"
echo "2. Click 'START TRIAL' - should open Telegram"
echo "3. Test webhook at https://dashboard.stripe.com/test/webhooks"

echo -e "\n✨ Done! Your landing page and Stripe integration are ready."