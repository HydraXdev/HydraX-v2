#!/usr/bin/env python3
"""
Quick Integration Script - Add Recruitment API to WebApp
Run this to automatically integrate recruitment endpoints into webapp_server_optimized.py
"""

import re
import shutil
from pathlib import Path

WEBAPP_FILE = Path("/root/HydraX-v2/webapp_server_optimized.py")
BACKUP_FILE = Path("/root/HydraX-v2/webapp_server_optimized.py.backup")

INTEGRATION_CODE = """
# ============================================================================
# FIREBASE RECRUITMENT SYSTEM INTEGRATION
# Added: October 12, 2025
# ============================================================================
from webapp_recruitment_handler import register_recruitment_routes

# Register recruitment API endpoints
# Provides: /api/recruitment/signup, /stats, /generate, /leaderboard
register_recruitment_routes(app)
print("✅ Recruitment API routes registered")
# ============================================================================
"""


def integrate_recruitment():
    """Add recruitment routes to webapp"""

    print("=" * 70)
    print("🔧 Integrating Firebase Recruitment API into WebApp")
    print("=" * 70)

    if not WEBAPP_FILE.exists():
        print(f"❌ ERROR: {WEBAPP_FILE} not found!")
        return False

    # Read current webapp
    print(f"\n📖 Reading {WEBAPP_FILE}...")
    content = WEBAPP_FILE.read_text()

    # Check if already integrated
    if "register_recruitment_routes" in content:
        print("⚠️  Recruitment routes already integrated!")
        return True

    # Create backup
    print(f"💾 Creating backup at {BACKUP_FILE}...")
    shutil.copy(WEBAPP_FILE, BACKUP_FILE)

    # Find insertion point (after Flask app creation)
    # Look for: app = Flask(__name__)
    pattern = r"(app\s*=\s*Flask\(__name__\).*?\n)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print("❌ ERROR: Could not find Flask app initialization!")
        return False

    # Insert integration code after app creation
    insertion_point = match.end()
    new_content = (
        content[:insertion_point] +
        "\n" + INTEGRATION_CODE + "\n" +
        content[insertion_point:]
    )

    # Write updated content
    print(f"✍️  Writing updated content to {WEBAPP_FILE}...")
    WEBAPP_FILE.write_text(new_content)

    print("\n✅ Integration complete!")
    print("\n📋 Next steps:")
    print("  1. Review changes: diff webapp_server_optimized.py webapp_server_optimized.py.backup")
    print("  2. Restart webapp: pm2 restart webapp")
    print("  3. Test endpoints: curl http://localhost:8888/api/recruitment/leaderboard")

    return True


def main():
    """Main execution"""
    success = integrate_recruitment()

    if success:
        print("\n🎯 Integration successful!")
        print(f"   Backup saved: {BACKUP_FILE}")
        print("\n🔍 To verify integration:")
        print("   grep -A 5 'register_recruitment_routes' webapp_server_optimized.py")
    else:
        print("\n❌ Integration failed!")
        print("   Manual integration required.")
        print("   See FIREBASE_RECRUITMENT_INTEGRATION.md for instructions.")


if __name__ == "__main__":
    main()
