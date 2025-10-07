#!/bin/bash

# BITTEN UI - Vercel Deployment Script
# Deploys to production with real backend integration

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 BITTEN UI - Vercel Production Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if vercel is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not installed. Installing..."
    npm install -g vercel
fi

# Build locally first to catch errors
echo ""
echo "📦 Building locally to verify..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Fix errors before deploying."
    exit 1
fi

echo "✅ Local build successful"
echo ""

# Set environment variables
echo "🔧 Setting environment variables..."

vercel env add NEXT_PUBLIC_USE_MOCKS production << EOF
0
EOF

vercel env add NEXT_PUBLIC_BUS_URL production << EOF
ws://134.199.204.67:8888/socket.io
EOF

vercel env add NEXT_PUBLIC_BACKEND_URL production << EOF
http://134.199.204.67:8888
EOF

vercel env add NEXT_PUBLIC_API_FIRE production << EOF
/api/fire
EOF

vercel env add NEXT_PUBLIC_API_CLOSE_ALL production << EOF
/api/trades/close-all
EOF

vercel env add NEXT_PUBLIC_TELEGRAM_URL production << EOF
https://t.me/bittenops
EOF

echo "✅ Environment variables set"
echo ""

# Deploy to production
echo "🚀 Deploying to production..."
vercel --prod

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ DEPLOYMENT SUCCESSFUL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 Your app is live at the URL shown above"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Test /mission page"
    echo "  2. Test /status page"
    echo "  3. Verify WebSocket connection"
    echo "  4. Test fire endpoint"
    echo ""
else
    echo "❌ Deployment failed"
    exit 1
fi
