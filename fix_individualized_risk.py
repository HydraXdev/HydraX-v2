#!/usr/bin/env python3
"""
Fix individualized risk management and position sizing
"""

import json
import sqlite3

def add_risk_profiles_to_users():
    """Add individualized risk profiles to user registry"""
    try:
        with open('/root/HydraX-v2/user_registry.json', 'r') as f:
            registry = json.load(f)
        
        updated = 0
        for user_id, user_data in registry.items():
            if 'risk_profile' not in user_data:
                # Set default risk based on tier
                if 'COMMANDER' in user_data.get('tier', ''):
                    # Commander gets 2% default risk
                    user_data['risk_profile'] = {
                        'risk_percentage': 2.0,  # 2% per trade
                        'max_daily_risk': 10.0,  # 10% max daily
                        'max_concurrent_trades': 3,
                        'risk_mode': 'MODERATE'  # CONSERVATIVE, MODERATE, AGGRESSIVE
                    }
                elif user_data.get('tier') == 'PRO':
                    # Pro gets 1.5% default risk
                    user_data['risk_profile'] = {
                        'risk_percentage': 1.5,
                        'max_daily_risk': 7.5,
                        'max_concurrent_trades': 2,
                        'risk_mode': 'MODERATE'
                    }
                else:
                    # Nibbler/Base gets 1% default risk
                    user_data['risk_profile'] = {
                        'risk_percentage': 1.0,
                        'max_daily_risk': 5.0,
                        'max_concurrent_trades': 1,
                        'risk_mode': 'CONSERVATIVE'
                    }
                
                updated += 1
        
        # Save updated registry
        with open('/root/HydraX-v2/user_registry.json', 'w') as f:
            json.dump(registry, f, indent=2)
        
        print(f"✅ Added risk profiles to {updated} users")
        return registry
        
    except Exception as e:
        print(f"Error updating user registry: {e}")
        return {}

def calculate_position_size(balance, risk_percentage, sl_pips, symbol):
    """Calculate proper position size based on user's risk profile"""
    
    # Get pip value for symbol
    def get_pip_value(symbol, lot_size=1.0):
        """Get pip value for 1 standard lot"""
        symbol = symbol.upper()
        
        # Forex pairs
        if symbol.endswith('USD'):
            return 10.0  # $10 per pip for 1 standard lot
        elif symbol.startswith('USD'):
            # For USDJPY, USDCAD, etc - need exchange rate
            if symbol == 'USDJPY':
                return 10.0 / 150  # Approximate, should use live rate
            elif symbol == 'USDCAD':
                return 10.0 / 1.35  # Approximate
            else:
                return 8.0  # Conservative estimate
        elif 'JPY' in symbol:
            return 8.0  # Approximate for JPY crosses
        elif symbol.startswith('XAU'):
            return 10.0  # Gold
        else:
            return 10.0  # Default for other pairs
    
    # Calculate risk amount in dollars
    risk_amount = balance * (risk_percentage / 100)
    
    # Get pip value for the symbol
    pip_value_per_lot = get_pip_value(symbol)
    
    # Calculate position size
    # Formula: Risk Amount / (SL in pips × Pip Value per lot)
    if sl_pips > 0 and pip_value_per_lot > 0:
        position_size = risk_amount / (sl_pips * pip_value_per_lot)
    else:
        position_size = 0.01  # Minimum lot size as fallback
    
    # Round to 2 decimal places for broker compatibility
    position_size = round(position_size, 2)
    
    # Apply minimum and maximum constraints
    min_lot = 0.01
    max_lot = 10.0  # Broker maximum
    position_size = max(min_lot, min(position_size, max_lot))
    
    return position_size, risk_amount

def get_user_risk_profile(user_id):
    """Get user's risk profile from registry"""
    try:
        with open('/root/HydraX-v2/user_registry.json', 'r') as f:
            registry = json.load(f)
        
        if user_id in registry:
            user = registry[user_id]
            return user.get('risk_profile', {
                'risk_percentage': 1.0,  # Default 1%
                'max_daily_risk': 5.0,
                'max_concurrent_trades': 1,
                'risk_mode': 'CONSERVATIVE'
            })
        else:
            return {
                'risk_percentage': 1.0,
                'max_daily_risk': 5.0,
                'max_concurrent_trades': 1,
                'risk_mode': 'CONSERVATIVE'
            }
    except:
        return {
            'risk_percentage': 1.0,
            'max_daily_risk': 5.0,
            'max_concurrent_trades': 1,
            'risk_mode': 'CONSERVATIVE'
        }

def update_user_risk_settings(user_id, risk_percentage=None, risk_mode=None):
    """Update a user's risk settings"""
    try:
        with open('/root/HydraX-v2/user_registry.json', 'r') as f:
            registry = json.load(f)
        
        if user_id in registry:
            if 'risk_profile' not in registry[user_id]:
                registry[user_id]['risk_profile'] = {}
            
            if risk_percentage is not None:
                # Validate risk percentage (0.5% to 5% range)
                risk_percentage = max(0.5, min(5.0, risk_percentage))
                registry[user_id]['risk_profile']['risk_percentage'] = risk_percentage
                
                # Adjust daily max based on per-trade risk
                registry[user_id]['risk_profile']['max_daily_risk'] = risk_percentage * 5
            
            if risk_mode is not None and risk_mode in ['CONSERVATIVE', 'MODERATE', 'AGGRESSIVE']:
                registry[user_id]['risk_profile']['risk_mode'] = risk_mode
                
                # Adjust concurrent trades based on mode
                if risk_mode == 'CONSERVATIVE':
                    registry[user_id]['risk_profile']['max_concurrent_trades'] = 1
                elif risk_mode == 'MODERATE':
                    registry[user_id]['risk_profile']['max_concurrent_trades'] = 3
                else:  # AGGRESSIVE
                    registry[user_id]['risk_profile']['max_concurrent_trades'] = 5
            
            # Save updated registry
            with open('/root/HydraX-v2/user_registry.json', 'w') as f:
                json.dump(registry, f, indent=2)
            
            return True
        return False
    except Exception as e:
        print(f"Error updating user risk settings: {e}")
        return False

if __name__ == "__main__":
    print("Fixing individualized risk management...")
    
    # Add risk profiles to all users
    registry = add_risk_profiles_to_users()
    
    # Test with commander user
    user_id = "7176191872"
    risk_profile = get_user_risk_profile(user_id)
    print(f"\nUser {user_id} risk profile:")
    print(f"  Risk per trade: {risk_profile['risk_percentage']}%")
    print(f"  Max daily risk: {risk_profile['max_daily_risk']}%")
    print(f"  Max concurrent: {risk_profile['max_concurrent_trades']}")
    print(f"  Risk mode: {risk_profile['risk_mode']}")
    
    # Test position sizing
    balance = 978.85  # Current balance
    sl_pips = 20  # Example SL
    symbol = "EURUSD"
    
    position_size, risk_amount = calculate_position_size(
        balance, 
        risk_profile['risk_percentage'],
        sl_pips,
        symbol
    )
    
    print(f"\nPosition sizing example:")
    print(f"  Balance: ${balance:.2f}")
    print(f"  Risk: {risk_profile['risk_percentage']}% = ${risk_amount:.2f}")
    print(f"  SL: {sl_pips} pips")
    print(f"  Position size: {position_size:.2f} lots")
    
    # Calculate TP dollar amount (example with 2:1 RR)
    tp_dollars = risk_amount * 2  # 2:1 risk/reward
    print(f"  TP (2:1 RR): ${tp_dollars:.2f}")