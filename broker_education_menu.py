# \!/usr/bin/env python3
"""
Broker Education Menu - Explaining regulated vs offshore accounts
Part of the Intel Command Center education system
"""

BROKER_EDUCATION = {
    "main_menu": {
        "title": "🏦 BROKER INTELLIGENCE BRIEFING",
        "description": "Understanding your deployment options",
        "options": [
            {"id": "regulated", "label": "📋 Regulated Brokers (Forex.com)", "emoji": "🛡️"},
            {"id": "offshore", "label": "🌊 Offshore Brokers (Coinexx)", "emoji": "🚀"},
            {"id": "comparison", "label": "⚖️ Side-by-Side Comparison", "emoji": "📊"},
            {"id": "recommendations", "label": "🎯 Which Should I Choose?", "emoji": "💡"},
            {"id": "leverage", "label": "🔧 Understanding Leverage", "emoji": "📈"},
            {"id": "regulations", "label": "🏛️ Regulation Deep Dive", "emoji": "📚"},
        ],
    },
    "regulated": {
        "title": "🛡️ REGULATED BROKERS - FOREX.COM",
        "content": """
**THE SAFE HARBOR APPROACH**

Forex.com is regulated by the CFTC (Commodity Futures Trading Commission) and NFA (National Futures Association) in the United States.

**✅ ADVANTAGES:**
• **Trust & Security**: Your funds are segregated and protected
• **Legal Recourse**: You have regulatory protection if issues arise
• **Stability**: Less likely to disappear overnight
• **Transparency**: Required to report financials publicly
• **US Trader Friendly**: Fully compliant for US residents

**❌ LIMITATIONS:**
• **Max Leverage**: 50:1 (major pairs), 20:1 (minors)
• **FIFO Rule**: First In, First Out - can't cherry-pick positions to close
• **No Hedging**: Can't hold buy and sell on same pair simultaneously
• **Higher Minimums**: Often require larger deposits

**💰 COST STRUCTURE:**
• Spreads: Typically 1-2 pips on majors
• No commission on standard accounts
• Minimum deposit: $50-100

**🎯 BEST FOR:**
• New traders wanting safety
• US-based traders (required)
• Conservative approach
• Long-term investors
        """,
    },
    "offshore": {
        "title": "🚀 OFFSHORE BROKERS - COINEXX",
        "content": """
**THE HIGH-OCTANE OPTION**

Coinexx operates from St. Vincent and the Grenadines, outside major regulatory jurisdictions.

**✅ ADVANTAGES:**
• **High Leverage**: Up to 500:1 (10x more than regulated)
• **No FIFO**: Close any position you want
• **Hedging Allowed**: Hold opposing positions
• **Lower Minimums**: Start with as little as $10
• **More Freedom**: Fewer trading restrictions

**❌ RISKS:**
• **Less Protection**: Limited regulatory oversight
• **Trust Required**: Research broker reputation carefully
• **No SIPC/FDIC**: Funds not insured like US brokers
• **Potential Issues**: Withdrawal delays more common

**💰 COST STRUCTURE:**
• Tighter spreads: Often 0.1-0.8 pips
• Small commissions: $3-7 per lot
• Lower minimums: $10-25

**⚠️ RISK MANAGEMENT:**
With great leverage comes great responsibility:
• 500:1 means $100 controls $50,000
• 1% move = 500% gain/loss on margin
• BITTEN's 2% risk rule becomes CRITICAL

**🎯 BEST FOR:**
• Experienced traders
• Small account growth strategies
• Scalping (need tight spreads)
• Non-US traders
        """,
    },
    "comparison": {
        "title": "⚖️ REGULATED VS OFFSHORE COMPARISON",
        "content": """
**HEAD-TO-HEAD BREAKDOWN**

 < /dev/null |  Feature | Regulated (Forex.com) | Offshore (Coinexx) |
|---------|---------------------|-------------------|
| **Leverage** | 50:1 max | 500:1 max |
| **Minimum Deposit** | $50-100 | $10-25 |
| **Spreads** | 1-2 pips | 0.1-0.8 pips |
| **Commission** | None | $3-7/lot |
| **US Traders** | ✅ Allowed | ❌ Prohibited |
| **Fund Safety** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Trading Freedom** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **FIFO Rules** | ✅ Enforced | ❌ No |
| **Hedging** | ❌ Prohibited | ✅ Allowed |
| **Execution Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**📊 REAL EXAMPLE - $1,000 Account:**

*Regulated (50:1):*
• Max position: $50,000 (0.5 lots)
• 20 pip move = $100 (10% account)
• Safer but slower growth

*Offshore (500:1):*
• Max position: $500,000 (5 lots)
• 20 pip move = $1,000 (100% account)
• Higher risk, higher reward

**🎯 THE BITTEN APPROACH:**
Our 2% risk rule works with BOTH:
• Regulated: Smaller positions, steadier growth
• Offshore: Requires MORE discipline
        """,
    },
    "recommendations": {
        "title": "🎯 WHICH BROKER SHOULD I CHOOSE?",
        "content": """
**PERSONALIZED RECOMMENDATIONS**

**🆕 IF YOU'RE NEW TO TRADING:**
→ Start with REGULATED (Forex.com)
• Build skills with safety net
• Learn without blow-up risk
• Upgrade to offshore later

**🇺🇸 IF YOU'RE IN THE USA:**
→ REGULATED is your only option
• Legal requirement
• Still profitable with discipline
• Focus on skill over leverage

**💰 IF YOU HAVE <$500:**
→ Consider OFFSHORE (Coinexx)
• $100 can actually grow
• Tight spreads help small accounts
• BUT: Use BITTEN's safety features\!

**📈 IF YOU'RE EXPERIENCED:**
→ OFFSHORE offers more opportunity
• Leverage for scaling strategies
• Better spreads for scalping
• Hedging strategies available

**🛡️ IF YOU WANT PEACE OF MIND:**
→ REGULATED all the way
• Sleep better at night
• Your funds are protected
• Sustainable long-term approach

**🎮 THE BITTEN RECOMMENDATION:**
1. **Press Pass**: Generic Demo (instant start)
2. **First Month**: Regulated demo (learn safely)
3. **Month 2-3**: Small regulated live account
4. **Month 4+**: Consider offshore if ready

Remember: It's not about the broker, it's about YOUR discipline\!
        """,
    },
    "leverage": {
        "title": "🔧 UNDERSTANDING LEVERAGE",
        "content": """
**LEVERAGE: YOUR FORCE MULTIPLIER**

**What Is Leverage?**
Leverage lets you control large positions with small capital.
Think of it as a loan from your broker for each trade.

**THE MATH:**
• 50:1 = Control $50 for every $1
• 100:1 = Control $100 for every $1
• 500:1 = Control $500 for every $1

**REAL EXAMPLES:**

*No Leverage (1:1):*
• $1,000 account buys $1,000 of EUR/USD
• 100 pip move = $10 profit/loss (1%)

*50:1 Leverage (Regulated):*
• $1,000 controls $50,000 position
• 100 pip move = $500 profit/loss (50%)

*500:1 Leverage (Offshore):*
• $1,000 controls $500,000 position
• 100 pip move = $5,000 profit/loss (500%)

**⚠️ THE LEVERAGE TRAP:**
Higher leverage ≠ Higher profits
Higher leverage = Higher SPEED of win/loss

**🛡️ BITTEN'S PROTECTION:**
• 2% risk rule works at ANY leverage
• Auto-position sizing prevents overleverage
• Daily loss limits stop spiral

**GOLDEN RULES:**
1. Leverage amplifies emotions too
2. Start low, increase gradually
3. Never use full available leverage
4. Let BITTEN calculate position sizes
        """,
    },
    "regulations": {
        "title": "🏛️ REGULATION DEEP DIVE",
        "content": """
**UNDERSTANDING BROKER REGULATIONS**

**🇺🇸 US REGULATIONS (CFTC/NFA):**
• Strictest in the world
• Max 50:1 leverage
• No hedging allowed
• FIFO rule enforced
• Segregated client funds
• Regular audits required

**🇬🇧 UK REGULATIONS (FCA):**
• Max 30:1 leverage (retail)
• Negative balance protection
• Client money protection
• Stricter than US in some ways

**🇨🇾 CYPRUS (CySEC):**
• EU passport rights
• 30:1 leverage limit
• Popular for EU brokers
• Investor compensation fund

**🌊 OFFSHORE JURISDICTIONS:**

*St. Vincent (SVG):*
• Minimal regulations
• No leverage limits
• Popular for high-leverage brokers
• No investor protection

*Seychelles (FSA):*
• Light-touch regulation
• Some broker oversight
• No leverage restrictions

**❓ WHAT THIS MEANS FOR YOU:**

**Regulated = Safety Features:**
✅ Your money is segregated
✅ Regular audits happen
✅ Legal recourse exists
✅ Compensation schemes available
❌ Trading restrictions apply

**Offshore = Trading Freedom:**
✅ Higher leverage available
✅ More trading strategies
✅ Lower costs usually
✅ Easier account opening
❌ Higher counterparty risk

**🎯 THE SMART APPROACH:**
• Start regulated to learn safely
• Keep most funds in regulated accounts
• Use offshore for specific strategies
• Never put all eggs in one basket
        """,
    },
}


def format_broker_menu():
    """Format broker education for Telegram bot integration"""

    # Create callback data mapping
    callbacks = {}
    for key, data in BROKER_EDUCATION.items():
        if key == "main_menu":
            callbacks["broker_education"] = {
                "text": data["title"] + "\n" + data["description"],
                "buttons": [
                    [{"text": opt["emoji"] + " " + opt["label"], "callback_data": f"broker_{opt['id']}"}]
                    for opt in data["options"]
                ],
            }
        else:
            callbacks[f"broker_{key}"] = {
                "text": data["title"] + "\n" + data["content"],
                "buttons": [[{"text": "⬅️ Back to Broker Menu", "callback_data": "broker_education"}]],
            }

    return callbacks


if __name__ == "__main__":
    # Export for bot integration
    import json

    print("📚 Broker Education Menu Created")
    print("=" * 60)

    callbacks = format_broker_menu()

    # Save for bot integration
    with open("/root/HydraX-v2/data/broker_education_menu.json", "w") as f:
        json.dump(callbacks, f, indent=2)

    print("\n✅ Saved to: data/broker_education_menu.json")
    print("\n🔧 Integration:")
    print("Add to Intel Command Center under 'Field Manual' section")
    print("Callback: 'broker_education' opens the menu")

    # Show sample content
    print("\n📋 Sample Menu Structure:")
    print(json.dumps(list(BROKER_EDUCATION.keys()), indent=2))
