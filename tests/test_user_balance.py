#!/usr/bin/env python3
from real_time_balance_system import get_user_balance_safe

# Test both user IDs
for user_id in ["843859", "7176191872"]:
    balance = get_user_balance_safe(user_id)
    print(f"User {user_id}: ${balance.balance} ({balance.server}) - Live: {balance.is_live}")