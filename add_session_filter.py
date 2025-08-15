#!/usr/bin/env python3
"""
Add session filter - only trade during active sessions
"""

code_to_add = """
    def is_active_trading_session(self):
        \"\"\"Check if we're in an active trading session\"\"\"
        from datetime import datetime
        import pytz
        
        # Get current UTC time
        utc_now = datetime.now(pytz.UTC)
        hour = utc_now.hour
        
        # Define sessions (UTC times)
        # London: 07:00 - 16:00 UTC
        # New York: 12:00 - 21:00 UTC
        # Overlap: 12:00 - 16:00 UTC (BEST TIME)
        
        if 12 <= hour < 16:  # London/NY overlap - BEST
            return True, "OVERLAP", 1.1  # 10% confidence boost
        elif 7 <= hour < 12:  # London only
            return True, "LONDON", 1.05  # 5% confidence boost
        elif 16 <= hour < 21:  # NY only
            return True, "NEWYORK", 1.05  # 5% confidence boost
        else:  # Asian or dead zone
            return False, "INACTIVE", 1.0
"""

# Read the file
with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'r') as f:
    content = f.read()

# Add session check function after class definition
import_line = "import pytz"
if import_line not in content:
    # Add import at top
    content = content.replace("import time", "import time\nimport pytz")

# Find class definition and add method
class_pos = content.find("class EliteGuardWithCitadel:")
if class_pos > 0:
    # Find next method definition to insert before
    next_method = content.find("\n    def ", class_pos + 30)
    if next_method > 0:
        # Insert our method
        content = content[:next_method] + code_to_add + content[next_method:]

# Now add session check to signal generation
old_check = "if signal and signal.confidence >= 60:"
new_check = """# Check if we're in active trading session
                is_active, session_name, conf_multiplier = self.is_active_trading_session()
                if not is_active:
                    logger.info(f"⏰ {symbol} Signal skipped - inactive session ({session_name})")
                    signal = None
                elif signal:
                    # Boost confidence for good sessions
                    signal.confidence = int(signal.confidence * conf_multiplier)
                    logger.info(f"📍 {symbol} Session: {session_name} (confidence x{conf_multiplier})")
                
                if signal and signal.confidence >= 60:"""

content = content.replace(old_check, new_check)

# Write back
with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'w') as f:
    f.write(content)

print("✅ Added session filter:")
print("   - London/NY overlap: BEST time (12:00-16:00 UTC)")
print("   - London session: Good (07:00-12:00 UTC)")
print("   - NY session: Good (16:00-21:00 UTC)")
print("   - Other times: NO TRADING")