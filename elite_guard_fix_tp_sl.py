#!/usr/bin/env python3
"""
Fix Elite Guard TP/SL for high win rate scalping
RAPID: 1:1.5 RR, must hit within 1 hour
SNIPER: 1:2 RR, must hit within 2 hours
"""

import sys

# Read the Elite Guard file
with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'r') as f:
    content = f.read()

# Find and replace the TP/SL calculation section
old_code = """            # Calculate levels
            pip_size = 0.01 if 'JPY' in pattern_signal.pair else 0.0001
            stop_distance = max(atr * sl_multiplier, 10 * pip_size)  # Minimum 10 pips
            stop_pips = int(stop_distance / pip_size)
            target_pips = int(stop_pips * tp_multiplier)"""

new_code = """            # SCALPING FIX: Tight TP/SL for 1-2 hour completion
            pip_size = 0.01 if 'JPY' in pattern_signal.pair else 0.0001
            
            # Determine if RAPID or SNIPER based on pattern confidence
            if pattern_signal.confidence >= 75:  # SNIPER patterns
                stop_pips = 8   # 8 pip stop loss
                target_pips = 16  # 16 pip take profit (1:2 RR)
                pattern_class = "SNIPER"
                expected_minutes = 120  # 2 hours max
            else:  # RAPID patterns  
                stop_pips = 6   # 6 pip stop loss
                target_pips = 9  # 9 pip take profit (1:1.5 RR)
                pattern_class = "RAPID"
                expected_minutes = 60  # 1 hour max
                
            stop_distance = stop_pips * pip_size
            
            # Override the multipliers to ensure correct RR
            tp_multiplier = target_pips / stop_pips"""

# Replace the code
content = content.replace(old_code, new_code)

# Also fix the minimum pip movement for pattern detection
content = content.replace(
    "if pip_movement > 3 and volume_surge > 1.3:",
    "if pip_movement > 1.5 and volume_surge > 1.2:"  # Lower threshold for faster signals
)

# Fix confidence thresholds to generate more signals
content = content.replace(
    "if signal and signal.confidence >= 65:",
    "if signal and signal.confidence >= 60:"  # Lower confidence threshold
)

# Add pattern class to signal output
old_signal_dict = """                'created_at': int(time.time()),
                'source': 'ELITE_GUARD',
                'version': '5.0'"""

new_signal_dict = """                'created_at': int(time.time()),
                'source': 'ELITE_GUARD',
                'version': '5.1_SCALP',
                'pattern_class': pattern_class,
                'expected_minutes': expected_minutes"""

content = content.replace(old_signal_dict, new_signal_dict)

# Write the fixed version
with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'w') as f:
    f.write(content)

print("✅ Elite Guard fixed with scalping TP/SL:")
print("   RAPID: 6p SL, 9p TP (1:1.5 RR) - 1 hour max")
print("   SNIPER: 8p SL, 16p TP (1:2 RR) - 2 hours max")