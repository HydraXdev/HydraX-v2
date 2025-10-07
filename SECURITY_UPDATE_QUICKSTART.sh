#!/bin/bash
# SECURITY UPDATE QUICKSTART - HydraX-v2
# Generated: October 7, 2025
# Based on pip-audit results

set -e

echo "================================================================================"
echo "🔒 BITTEN SYSTEM - SECURITY UPDATE SCRIPT"
echo "================================================================================"
echo ""
echo "⚠️  CRITICAL: This is a LIVE TRADING SYSTEM"
echo "   → Only run during OFF-MARKET hours"
echo "   → Test in staging environment first if available"
echo ""

# Confirm before proceeding
read -p "Ready to proceed with security updates? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "📦 Step 1: Creating backup..."
pip freeze > /root/HydraX-v2/requirements_backup_$(date +%Y%m%d_%H%M%S).txt
echo "✅ Backup saved to: requirements_backup_$(date +%Y%m%d_%H%M%S).txt"

echo ""
echo "🔧 Step 2: Updating CRITICAL packages..."
pip install --upgrade \
  cryptography>=42.0.2 \
  twisted>=24.7.0rc1 \
  jwcrypto>=1.5.6 \
  pyjwt>=2.4.0 \
  pip>=23.3 \
  setuptools>=78.1.1

echo ""
echo "🔧 Step 3: Updating HIGH priority packages..."
pip install --upgrade \
  fastapi>=0.109.1 \
  starlette>=0.47.2 \
  aiohttp>=3.12.14 \
  oauthlib>=3.2.1 \
  babel>=2.9.1 \
  idna>=3.7 \
  python-multipart>=0.0.18 \
  configobj>=5.0.9 \
  wheel>=0.38.1

echo ""
echo "✅ Step 4: Verifying installation..."
pip check

echo ""
echo "🔍 Step 5: Checking PM2 processes..."
pm2 list

echo ""
echo "🌐 Step 6: Checking ZMQ ports..."
ss -tulpen | grep -E ":(5555|5556|5557|5558|5560|8888)" || echo "No ports bound (check if processes need restart)"

echo ""
echo "================================================================================"
echo "✅ SECURITY UPDATE COMPLETE"
echo "================================================================================"
echo ""
echo "📋 POST-UPDATE CHECKLIST:"
echo "   1. ✅ Check pm2 list - All processes running?"
echo "   2. ✅ Check ports - All ZMQ ports (5555-5560, 8888) bound?"
echo "   3. ✅ Test webapp - curl http://localhost:8888/healthz"
echo "   4. ✅ Test signal flow - Monitor logs for 15 minutes"
echo "   5. ✅ Verify EA connection - Check last_seen timestamp"
echo ""
echo "🔄 If issues occur, rollback with:"
echo "   pip install -r /root/HydraX-v2/requirements_backup_*.txt"
echo ""
echo "📊 Full audit report: /root/HydraX-v2/SECURITY_AUDIT_REPORT.md"
echo "================================================================================"
