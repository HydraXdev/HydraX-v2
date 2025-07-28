
def get_available_instance(master_type, tier):
    """Get an available MT5 instance for a user"""
    conn = sqlite3.connect('/root/HydraX-v2/data/mt5_instances.db')
    cursor = conn.cursor()
    
    # Find available instance
    cursor.execute("""
        SELECT instance_id, magic_number, port, directory_path 
        FROM mt5_instances 
        WHERE master_type = ? 
        AND assigned_user_id IS NULL 
        AND status = 'active'
        LIMIT 1
    """, (master_type,))
    
    instance = cursor.fetchone()
    conn.close()
    return instance

def assign_instance_to_user(user_id, tier):
    """Assign appropriate MT5 instance to user based on tier"""
    instance_map = {
        "PRESS_PASS": "Generic_Demo",
        "NIBBLER": "Forex_Demo",
        "FANG": "Forex_Demo",
        "COMMANDER": "Forex_Live": "Coinexx_Live"
    }
    
    master_type = instance_map.get(tier, "Forex_Demo")
    instance = get_available_instance(master_type, tier)
    
    if instance:
        # Update assignment
        conn = sqlite3.connect('/root/HydraX-v2/data/mt5_instances.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE mt5_instances 
            SET assigned_user_id = ?, assigned_tier = ?, last_active = CURRENT_TIMESTAMP
            WHERE instance_id = ?
        """, (user_id, tier, instance[0]))
        conn.commit()
        conn.close()
        
        return {
            "instance_id": instance[0],
            "magic_number": instance[1],
            "port": instance[2],
            "directory": instance[3]
        }
    return None
