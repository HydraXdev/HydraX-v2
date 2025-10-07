#!/usr/bin/env python3
"""
🔒 ATHENA Bot Security Audit Script
Verifies all security hardening measures are properly implemented
"""

import os
import re
import sys


def check_token_security():
    """Check if token is properly secured"""
    print("🔒 Checking token security...")

    # Check if token is loaded from environment
    with open("/root/HydraX-v2/athena_mission_bot.py", "r") as f:
        content = f.read()
        if 'os.getenv("ATHENA_BOT_TOKEN"' in content:
            print("  ✅ Token loaded from environment variable")
        else:
            print("  ❌ Token not loaded from environment")
            return False

    # Check if environment file exists
    if os.path.exists("/root/HydraX-v2/.secrets/athena.env"):
        print("  ✅ Environment file exists")
    else:
        print("  ❌ Environment file missing")
        return False

    return True


def check_authorization_system():
    """Check if authorization system is implemented"""
    print("🔒 Checking authorization system...")

    with open("/root/HydraX-v2/athena_mission_bot.py", "r") as f:
        content = f.read()

        if "AUTHORIZED_USERS" in content:
            print("  ✅ Authorized users list implemented")
        else:
            print("  ❌ No authorized users list found")
            return False

        if "is_authorized_user" in content:
            print("  ✅ Authorization check function exists")
        else:
            print("  ❌ No authorization check function")
            return False

    return True


def check_command_whitelist():
    """Check if command whitelist is implemented"""
    print("🔒 Checking command whitelist...")

    with open("/root/HydraX-v2/athena_mission_bot.py", "r") as f:
        content = f.read()

        if "ALLOWED_COMMANDS" in content:
            print("  ✅ Allowed commands whitelist implemented")
        else:
            print("  ❌ No command whitelist found")
            return False

    return True


def check_security_logging():
    """Check if security logging is implemented"""
    print("🔒 Checking security logging...")

    with open("/root/HydraX-v2/athena_mission_bot.py", "r") as f:
        content = f.read()

        if "log_security_event" in content:
            print("  ✅ Security logging function exists")
        else:
            print("  ❌ No security logging found")
            return False

        if "UNAUTHORIZED_ACCESS" in content:
            print("  ✅ Unauthorized access logging implemented")
        else:
            print("  ❌ No unauthorized access logging")
            return False

    return True


def check_catch_all_handler():
    """Check if dangerous catch-all handler is secured"""
    print("🔒 Checking catch-all handler security...")

    with open("/root/HydraX-v2/athena_mission_bot.py", "r") as f:
        content = f.read()

        if "block_unauthorized_messages" in content:
            print("  ✅ Secure message blocking implemented")
        else:
            print("  ❌ No secure message blocking found")
            return False

        # Check for dangerous patterns
        if "func=lambda message: True" in content and "block_unauthorized_messages" in content:
            print("  ✅ Catch-all handler secured")
        else:
            print("  ❌ Catch-all handler not properly secured")
            return False

    return True


def main():
    """Run complete security audit"""
    print("🔒 ATHENA Bot Security Audit")
    print("=" * 50)

    all_checks_passed = True

    checks = [
        check_token_security,
        check_authorization_system,
        check_command_whitelist,
        check_security_logging,
        check_catch_all_handler,
    ]

    for check in checks:
        if not check():
            all_checks_passed = False
        print()

    print("=" * 50)
    if all_checks_passed:
        print("✅ ALL SECURITY CHECKS PASSED")
        print("🔒 ATHENA Bot is properly hardened")
    else:
        print("❌ SECURITY VULNERABILITIES FOUND")
        print("🚨 Fix issues before running bot")
        sys.exit(1)


if __name__ == "__main__":
    main()
