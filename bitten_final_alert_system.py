#!/usr/bin/env python3
"""
BITTEN FINAL ALERT SYSTEM - PRODUCTION READY
Complete with different button texts
"""

# FINAL ALERT FORMATS

def create_arcade_alert(tcs_score):
    """
    ARCADE alert format with MISSION BRIEF button
    """
    return {
        "text": f"🔫 RAPID ASSAULT [{tcs_score}%]\n🔥 STRIKE 💥",
        "button_text": "MISSION BRIEF",
        "signal_type": "ARCADE",
        "min_tier": "NIBBLER"
    }

def create_sniper_alert(tcs_score):
    """
    SNIPER alert format with VIEW INTEL button
    """
    return {
        "text": f"⚡ SNIPER OPS ⚡ [{tcs_score}%]\n🎖️ ELITE ACCESS",
        "button_text": "VIEW INTEL",
        "signal_type": "SNIPER",
        "min_tier": "FANG"
    }

# Example implementation
def format_telegram_alert(signal_data):
    """
    Format complete Telegram alert with inline button
    """
    tcs = int(signal_data['confidence'] * 100)
    
    # Determine signal type based on criteria
    if tcs >= 85 and signal_data.get('duration_minutes', 0) > 60:
        alert = create_sniper_alert(tcs)
    else:
        alert = create_arcade_alert(tcs)
    
    # Create inline keyboard
    keyboard = {
        "inline_keyboard": [[{
            "text": alert["button_text"],
            "web_app": {
                "url": f"https://joinbitten.com/mission?id={signal_data['signal_id']}"
            }
        }]]
    }
    
    return {
        "message": alert["text"],
        "keyboard": keyboard,
        "signal_type": alert["signal_type"],
        "min_tier": alert["min_tier"]
    }

# Summary
print("=== BITTEN FINAL ALERT SYSTEM ===\n")

print("ARCADE ALERTS:")
print("Text:   🔫 RAPID ASSAULT [XX%]")
print("        🔥 STRIKE 💥")
print("Button: [MISSION BRIEF]")
print("Access: All tiers\n")

print("SNIPER ALERTS:")
print("Text:   ⚡ SNIPER OPS ⚡ [XX%]")
print("        🎖️ ELITE ACCESS")
print("Button: [VIEW INTEL]")
print("Access: FANG+ only\n")

print("KEY DIFFERENCES:")
print("• ARCADE uses 'MISSION BRIEF' (sounds tactical)")
print("• SNIPER uses 'VIEW INTEL' (sounds elite/exclusive)")
print("• Visual differentiation clear")
print("• Access control at execution level")

print("\n✅ PRODUCTION READY!")