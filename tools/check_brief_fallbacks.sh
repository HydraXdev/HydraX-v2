#!/bin/bash
echo "=== BRIEF FALLBACK STATISTICS ==="
echo "Total fallback missions created:"
redis-cli GET bitten:brief_fallback_count || echo "0"
echo ""
echo "Signal IDs that needed fallback creation:"
redis-cli SMEMBERS bitten:brief_fallback_signals | head -n 10
echo ""
echo "Recent fallback count:"
echo "$(redis-cli SCARD bitten:brief_fallback_signals || echo 0) unique signals created on-demand"