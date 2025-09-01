#!/usr/bin/env python3
import json
import glob
import os
from datetime import datetime

class GateFilter:
    def __init__(self):
        self.gates = self.load_latest_gates()
    
    def load_latest_gates(self):
        gate_files = glob.glob("/root/elite_guard/active_gates_*.json")
        if not gate_files:
            return {}
        
        latest_file = max(gate_files, key=os.path.getmtime)
        with open(latest_file, 'r') as f:
            data = json.load(f)
            return data.get('gates', {})
    
    def filter_signal(self, signal):
        signal_key = f"{signal['symbol']}_{signal['pattern']}_{signal['session']}"
        
        if signal_key not in self.gates:
            return False
        
        gate = self.gates[signal_key]
        if gate.get('disabled', False):
            return False
        
        passes = (
            signal.get('quality', 0) >= gate.get('quality', 0.85) and
            signal.get('confidence', 0) >= gate.get('confidence', 0.90) and
            signal.get('rr', 0) >= gate.get('rr', 1.2)
        )
        
        return passes

if __name__ == "__main__":
    filter = GateFilter()
    print(f"Loaded {len(filter.gates)} gates")
