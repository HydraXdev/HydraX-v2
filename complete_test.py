import json
from datetime import datetime

# Read the test signal
with open('/root/HydraX-v2/truth_log.jsonl', 'r') as f:
    lines = f.readlines()
    for line in lines:
        if not line.strip() or line.strip() == '[]':
            continue
        signal = json.loads(line)
        if 'TEST_SIGNAL' in signal.get('signal_id', ''):
            print(f"Found test signal: {signal['signal_id']}")
            
            # Mark it as completed (TP hit) - USE THE GOOD DATA
            if signal.get('entry_price', 0) > 0:  # Use the signal with real prices
                signal['completed'] = True
                signal['outcome'] = 'win'
                signal['exit_price'] = signal['tp']
                signal['pips'] = 20
                signal['completed_at'] = datetime.now().isoformat()
                
                # Write completion
                with open('/root/HydraX-v2/truth_log.jsonl', 'a') as out:
                    out.write(json.dumps(signal) + '\n')
                
                print("✅ Signal marked as complete - WIN")
                print(f"Entry: {signal['entry_price']} → Exit: {signal['exit_price']}")
                print(f"Profit: +20 pips")
                break
            else:
                print(f"⚠️ Skipping corrupted signal (entry_price = 0)")