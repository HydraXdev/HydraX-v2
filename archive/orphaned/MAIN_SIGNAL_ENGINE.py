"""
BITTEN Main Signal Engine - v5.0 ONLY
This is the ONLY active signal engine in the system
All other engines have been archived for historical reference

TCS Range: 35-95 (Ultra-Aggressive Mode)
Pairs: 15 (including volatility monsters)
Target: 40+ signals/day @ 89% win rate
"""

from apex_v5_integration import v5IntegrationManager

# This is the ONLY signal engine that should be imported anywhere in the system
MainSignalEngine = v5IntegrationManager

print("✅ v5.0 Engine Active - Ultra-Aggressive Mode (TCS 35-95)")
print("⚠️  All conservative engines (87% TCS) have been archived")