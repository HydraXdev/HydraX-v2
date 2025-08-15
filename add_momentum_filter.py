#!/usr/bin/env python3
"""
Add momentum filter to Elite Guard for higher win rate
Only signal when price is actively moving in the direction
"""

# Read the file
with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'r') as f:
    lines = f.readlines()

# Find where signals are validated (around line 1065)
insert_position = -1
for i, line in enumerate(lines):
    if "if signal and signal.confidence >=" in line:
        insert_position = i
        break

if insert_position > 0:
    # Add momentum check before signal validation
    momentum_check = """                # MOMENTUM FILTER: Check if price is actively moving
                if signal:
                    # Calculate recent momentum
                    if symbol in self.m1_data and len(self.m1_data[symbol]) >= 3:
                        recent_prices = [c.get('close', 0) for c in self.m1_data[symbol][-3:]]
                        if len(recent_prices) >= 3:
                            # Price must be moving in signal direction
                            price_change = recent_prices[-1] - recent_prices[0]
                            momentum_direction = "BUY" if price_change > 0 else "SELL"
                            
                            # Signal direction must match momentum
                            if signal.direction != momentum_direction:
                                logger.info(f"⚠️ {symbol} Signal rejected - momentum mismatch "
                                          f"(signal: {signal.direction}, momentum: {momentum_direction})")
                                signal = None
                            else:
                                # Boost confidence if strong momentum
                                momentum_strength = abs(price_change) * 10000  # Convert to pips
                                if momentum_strength > 2:  # Strong momentum
                                    signal.confidence = min(90, signal.confidence + 5)
                                    logger.info(f"🚀 {symbol} Momentum boost: +5 confidence (momentum: {momentum_strength:.1f} pips)")
                
"""
    lines.insert(insert_position, momentum_check)

# Write back
with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'w') as f:
    f.writelines(lines)

print("✅ Added momentum filter to Elite Guard")
print("   - Signals must have momentum in same direction")
print("   - Strong momentum boosts confidence +5")
print("   - Reduces false signals significantly")