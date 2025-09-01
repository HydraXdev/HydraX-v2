#!/usr/bin/env python3
"""
Real-Time Confidence Recalibrator for Elite Guard
Fixes overconfident 85%+ signals based on actual 32.4% performance
"""

import json
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidenceRecalibrator:
    def __init__(self):
        # Based on actual performance analysis from today's 670 signals
        self.performance_data = {
            "70-74": {"actual_win_rate": 37.4, "sample_size": 198},
            "75-79": {"actual_win_rate": 39.6, "sample_size": 154}, 
            "80-84": {"actual_win_rate": 43.4, "sample_size": 244},  # BEST PERFORMER
            "85+": {"actual_win_rate": 32.4, "sample_size": 74}     # WORST PERFORMER
        }
    
    def recalibrate_confidence(self, original_confidence: float) -> float:
        """
        Recalibrate confidence based on actual win rate performance
        Key insight: 80-84% is the sweet spot, 85%+ significantly overconfident
        """
        
        if original_confidence >= 85:
            # 85%+ severely overconfident (32.4% actual vs 85%+ claimed)
            # Map to realistic 30-35% range
            recalibrated = 30 + (original_confidence - 85) * 0.5
            recalibrated = min(35, max(30, recalibrated))
            
        elif original_confidence >= 80:
            # 80-84% is optimal range (43.4% actual)
            # Keep in 40-45% range (slight adjustment)
            recalibrated = 40 + (original_confidence - 80) * 1.25
            recalibrated = min(45, max(40, recalibrated))
            
        elif original_confidence >= 75:
            # 75-79% performs at 39.6%
            # Map to 35-40% range
            recalibrated = 35 + (original_confidence - 75) * 1.0
            recalibrated = min(40, max(35, recalibrated))
            
        elif original_confidence >= 70:
            # 70-74% performs at 37.4% 
            # Map to 32-37% range
            recalibrated = 32 + (original_confidence - 70) * 1.25
            recalibrated = min(37, max(32, recalibrated))
            
        else:
            # Below 70% - conservative mapping
            recalibrated = max(20, original_confidence * 0.5)
        
        return round(recalibrated, 1)
    
    def get_optimal_auto_fire_threshold(self) -> float:
        """Return optimal threshold for auto-fire based on performance data"""
        # 80-84% range has best performance at 43.4%
        # After recalibration, this becomes 40-45% range
        return 42.0  # Middle of the best performing recalibrated range
    
    def apply_batch_recalibration(self, signals: list) -> list:
        """Apply recalibration to a batch of signals"""
        recalibrated_signals = []
        
        for signal in signals:
            if 'confidence' in signal:
                original = signal['confidence']
                recalibrated = self.recalibrate_confidence(original)
                
                signal['original_confidence'] = original
                signal['confidence'] = recalibrated
                signal['recalibration_applied'] = True
                
                logger.debug(f"Recalibrated: {original}% → {recalibrated}%")
            
            recalibrated_signals.append(signal)
        
        return recalibrated_signals

def create_elite_guard_patch():
    """Create patch to integrate recalibration into Elite Guard"""
    
    patch_code = '''
# Add this to elite_guard_with_citadel.py after imports
from confidence_recalibrator import ConfidenceRecalibrator

class EliteGuardWithCitadel:
    def __init__(self):
        # ... existing init code ...
        self.confidence_recalibrator = ConfidenceRecalibrator()
    
    def calculate_dynamic_confidence(self, symbol: str, base_pattern_score: float, momentum: float, volume: float) -> float:
        """Calculate confidence with recalibration applied"""
        
        # Original confidence calculation (lines 474-547)
        confidence = 0
        
        # ... existing calculation code ...
        
        # Apply recalibration before returning
        raw_confidence = min(95, max(55, confidence))
        recalibrated_confidence = self.confidence_recalibrator.recalibrate_confidence(raw_confidence)
        
        print(f"  🔧 RECALIBRATED: {raw_confidence:.1f}% → {recalibrated_confidence:.1f}% (based on true performance)")
        
        return recalibrated_confidence
'''
    
    return patch_code

if __name__ == "__main__":
    recalibrator = ConfidenceRecalibrator()
    
    print("CONFIDENCE RECALIBRATION SYSTEM")
    print("==============================")
    print()
    print("Current Performance Analysis (670 signals):")
    for bucket, data in recalibrator.performance_data.items():
        print(f"  {bucket}%: {data['actual_win_rate']}% win rate ({data['sample_size']} signals)")
    
    print()
    print("Recalibration Examples:")
    test_confidences = [70, 75, 80, 85, 90, 95]
    for original in test_confidences:
        recalibrated = recalibrator.recalibrate_confidence(original)
        print(f"  {original}% → {recalibrated}% confidence")
    
    print()
    print(f"Optimal Auto-Fire Threshold: {recalibrator.get_optimal_auto_fire_threshold()}%")
    print()
    print("Integration patch created. Apply to Elite Guard for immediate effect.")