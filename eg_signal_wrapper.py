#!/usr/bin/env python3
import json
import sys
import time
from datetime import datetime
from gate_filter import GateFilter

def process_signals():
    filter = GateFilter()
    input_file = "/root/HydraX-v2/optimized_tracking.jsonl"
    output_file = "/root/elite_guard/filtered_signals.jsonl"
    log_file = "/root/elite_guard/eg_signal_wrapper.log"
    
    processed_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    processed_ids.add(data.get('signal_id'))
                except:
                    pass
    
    while True:
        try:
            with open(input_file, 'r') as f:
                for line in f:
                    try:
                        signal = json.loads(line)
                        if signal.get('signal_id') in processed_ids:
                            continue
                        
                        if filter.filter_signal(signal):
                            output = {
                                "timestamp": datetime.utcnow().isoformat(),
                                "signal_id": signal.get('signal_id'),
                                "pair": signal.get('symbol'),
                                "pattern": signal.get('pattern'),
                                "session": signal.get('session'),
                                "quality": signal.get('quality'),
                                "confidence": signal.get('confidence'),
                                "original_rr": signal.get('rr'),
                                "adjusted_rr": signal.get('rr') * 1.1,
                                "filter_passed": True
                            }
                            
                            with open(output_file, 'a') as out:
                                out.write(json.dumps(output) + '\n')
                            
                            with open(log_file, 'a') as log:
                                log.write(f"[{datetime.utcnow()}] Filtered signal: {signal.get('signal_id')}\n")
                            
                            processed_ids.add(signal.get('signal_id'))
                    except:
                        pass
            
            time.sleep(5)
        except:
            time.sleep(10)

if __name__ == "__main__":
    import os
    process_signals()
