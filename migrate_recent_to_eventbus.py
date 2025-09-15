#!/usr/bin/env python3
"""
Migrate last 24 hours of tracking data to Event Bus
Only need recent data - old data is outdated/incorrect
"""

import json
import time
from datetime import datetime, timedelta

# Import Event Bus client directly
import sys
sys.path.append('/root/HydraX-v2')
from event_bus.event_bus import EventBusClient

def migrate_recent_outcomes():
    """Migrate only last 24 hours of outcomes to Event Bus"""
    
    # Create Event Bus client
    client = EventBusClient()
    
    cutoff_time = time.time() - (24 * 3600)  # 24 hours ago
    migrated_count = 0
    
    print("🔄 Migrating last 24 hours of outcomes to Event Bus...")
    
    # Read comprehensive tracking file
    try:
        with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    
                    # Skip if older than 24 hours
                    timestamp = data.get('timestamp', 0)
                    if timestamp < cutoff_time:
                        continue
                    
                    # Only migrate if has outcome (WIN/LOSS)
                    outcome = data.get('outcome')
                    if outcome not in ['WIN', 'LOSS']:
                        continue
                    
                    # Publish to Event Bus as signal_outcome event
                    event_data = {
                        'signal_id': data.get('signal_id'),
                        'outcome': outcome,
                        'pips_result': data.get('pips_result', 0),
                        'pattern': data.get('pattern_type'),
                        'confidence': data.get('confidence'),
                        'symbol': data.get('symbol'),
                        'direction': data.get('direction'),
                        'original_timestamp': timestamp
                    }
                    
                    client.publish(
                        event_type='signal_outcome_recorded',
                        source='migration_script',
                        data=event_data,
                        correlation_id=data.get('signal_id')
                    )
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Error migrating record: {e}")
                    continue
                    
    except FileNotFoundError:
        print("❌ comprehensive_tracking.jsonl not found")
        return
    
    print(f"✅ Migrated {migrated_count} outcomes from last 24 hours")
    print(f"📊 Cutoff: {datetime.fromtimestamp(cutoff_time).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Now: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    migrate_recent_outcomes()
    print("\n🎯 Migration complete! Run 'bitten-report' to see Event Bus data")