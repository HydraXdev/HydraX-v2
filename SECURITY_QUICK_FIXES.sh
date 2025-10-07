#!/bin/bash
# HydraX-v2 Security Quick Fixes
# Run these commands to fix critical security issues

echo "🔒 HydraX-v2 Security Quick Fixes"
echo "=================================="
echo ""

# 1. Flask Debug Mode
echo "1️⃣  Fixing Flask debug mode..."
find /root/HydraX-v2 -name "*.py" -type f -exec sed -i 's/debug=True/debug=False/g' {} \;
echo "   ✅ Flask debug mode disabled"
echo ""

# 2. Find subprocess shell=True issues
echo "2️⃣  Locating subprocess shell injection issues..."
grep -rn "shell=True" /root/HydraX-v2/*.py | head -10
echo "   ⚠️  Review these files and change to shell=False with argument lists"
echo ""

# 3. Find MD5 usage
echo "3️⃣  Locating MD5 hash usage..."
grep -rn "hashlib.md5" /root/HydraX-v2/*.py | head -10
echo "   ⚠️  Replace with hashlib.sha256()"
echo ""

# 4. Find bind to all interfaces
echo "4️⃣  Locating services bound to 0.0.0.0..."
grep -rn 'host="0.0.0.0"' /root/HydraX-v2/*.py
echo "   ⚠️  Change to host='127.0.0.1' or specific IP"
echo ""

# 5. Find SQL string construction
echo "5️⃣  Locating potential SQL injection..."
grep -rn "cursor.execute.*%.*" /root/HydraX-v2/*.py | head -10
echo "   ⚠️  Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id=?', (id,))"
echo ""

echo "📋 Full reports available at:"
echo "   - /root/HydraX-v2/SECURITY_AUDIT_REPORT.md"
echo "   - /root/HydraX-v2/SECURITY_FIXES_TODO.txt"
echo ""
echo "✅ Run this script again after fixes to verify"
