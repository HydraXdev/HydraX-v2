# module_tracker.py
# BITTEN Module Trigger Tracking - Source Transparency

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class ModuleType(Enum):
    ARCADE = "arcade"
    SNIPER = "sniper"
    ENHANCEMENT = "enhancement"
    MANUAL = "manual"
    SPECIAL = "special"

@dataclass
class DetectionModule:
    """Detection module metadata"""
    name: str
    type: ModuleType
    strategy: str
    icon: str
    description: str
    success_rate: float = 0.0
    total_signals: int = 0

class ModuleTriggerSystem:
    """
    Tracks which detection module found each signal
    Provides transparency and performance tracking
    """
    
    def __init__(self):
        # Initialize all detection modules
        self.modules = {
            # Arcade modules
            "DAWN_RAID_SCANNER": DetectionModule(
                name="DAWN_RAID_SCANNER",
                type=ModuleType.ARCADE,
                strategy="London Breakout",
                icon="🌅",
                description="Detects range breakouts during London open"
            ),
            "WALL_DEFENDER_SCANNER": DetectionModule(
                name="WALL_DEFENDER_SCANNER",
                type=ModuleType.ARCADE,
                strategy="S/R Bounce",
                icon="🏰",
                description="Identifies key level rejections"
            ),
            "ROCKET_RIDE_SCANNER": DetectionModule(
                name="ROCKET_RIDE_SCANNER",
                type=ModuleType.ARCADE,
                strategy="Momentum Continuation",
                icon="🚀",
                description="Catches pullbacks in strong trends"
            ),
            "RUBBER_BAND_SCANNER": DetectionModule(
                name="RUBBER_BAND_SCANNER",
                type=ModuleType.ARCADE,
                strategy="Mean Reversion",
                icon="🎯",
                description="Fades extreme deviations"
            ),
            
            # Sniper modules (classified)
            "LIQUIDITY_HUNTER": DetectionModule(
                name="LIQUIDITY_HUNTER",
                type=ModuleType.SNIPER,
                strategy="CLASSIFIED",
                icon="🎯",
                description="[REDACTED]"
            ),
            "TOKYO_TRAP_DETECTOR": DetectionModule(
                name="TOKYO_TRAP_DETECTOR",
                type=ModuleType.SNIPER,
                strategy="CLASSIFIED",
                icon="🎯",
                description="[REDACTED]"
            ),
            "NEWS_FADE_ENGINE": DetectionModule(
                name="NEWS_FADE_ENGINE",
                type=ModuleType.SNIPER,
                strategy="CLASSIFIED",
                icon="🎯",
                description="[REDACTED]"
            ),
            "PIVOT_MAGNET_SCANNER": DetectionModule(
                name="PIVOT_MAGNET_SCANNER",
                type=ModuleType.SNIPER,
                strategy="CLASSIFIED",
                icon="🎯",
                description="[REDACTED]"
            ),
            
            # Enhancement modules
            "SHADOW_SPOTTER": DetectionModule(
                name="SHADOW_SPOTTER",
                type=ModuleType.ENHANCEMENT,
                strategy="Confluence Detector",
                icon="👻",
                description="Adds shadow index confidence scoring"
            ),
            "VOLUME_PROFILER": DetectionModule(
                name="VOLUME_PROFILER",
                type=ModuleType.ENHANCEMENT,
                strategy="Volume Analysis",
                icon="📊",
                description="Analyzes volume patterns for confirmation"
            ),
            
            # Special modules
            "MIDNIGHT_HAMMER_DETECTOR": DetectionModule(
                name="MIDNIGHT_HAMMER_DETECTOR",
                type=ModuleType.SPECIAL,
                strategy="Community Event",
                icon="🔨",
                description="Ultra-rare perfect storm detector"
            ),
            "ALPHA_OVERRIDE": DetectionModule(
                name="ALPHA_OVERRIDE",
                type=ModuleType.MANUAL,
                strategy="Manual Force",
                icon="🔥",
                description="User-initiated signal override"
            )
        }
        
        # Performance tracking
        self.module_performance: Dict[str, Dict] = {}
        self.signal_history: List[Dict] = []
    
    def enhance_signal_with_source(self, signal: Dict, module_name: str) -> Dict:
        """
        Adds source tracking to signal
        
        Enhances trust by showing which system detected the opportunity
        """
        
        module = self.modules.get(module_name)
        if not module:
            # Unknown module
            module = DetectionModule(
                name=module_name,
                type=ModuleType.MANUAL,
                strategy="Unknown",
                icon="❓",
                description="Unregistered detection module"
            )
        
        # Add module metadata to signal
        signal['triggered_by'] = module_name
        signal['module_type'] = module.type.value
        signal['module_icon'] = module.icon
        
        # Build display string based on type
        if module.type == ModuleType.SNIPER:
            # Never reveal sniper strategy names
            signal['source_display'] = f"{module.icon} SNIPER: [CLASSIFIED]"
            signal['module_description'] = "Elite signal detection system"
        else:
            signal['source_display'] = f"{module.icon} {module.strategy}"
            signal['module_description'] = module.description
        
        # Add performance hint if available
        perf = self.module_performance.get(module_name, {})
        if perf.get('success_rate', 0) > 0:
            signal['module_success_rate'] = perf['success_rate']
        
        # Log for tracking
        self._log_signal_detection(module_name, signal)
        
        return signal
    
    def _log_signal_detection(self, module_name: str, signal: Dict):
        """Log signal detection for performance tracking"""
        
        log_entry = {
            'timestamp': datetime.now(),
            'module': module_name,
            'symbol': signal.get('symbol'),
            'tcs': signal.get('tcs_score'),
            'signal_id': signal.get('signal_id')
        }
        
        self.signal_history.append(log_entry)
        
        # Update module stats
        if module_name not in self.module_performance:
            self.module_performance[module_name] = {
                'total_signals': 0,
                'successful_signals': 0,
                'total_pips': 0,
                'success_rate': 0
            }
        
        self.module_performance[module_name]['total_signals'] += 1
    
    def update_signal_result(self, signal_id: str, result: str, pips: float):
        """Update module performance based on trade result"""
        
        # Find the signal in history
        signal_log = None
        for log in self.signal_history:
            if log['signal_id'] == signal_id:
                signal_log = log
                break
        
        if not signal_log:
            return
        
        module_name = signal_log['module']
        perf = self.module_performance.get(module_name, {})
        
        if result == 'win':
            perf['successful_signals'] = perf.get('successful_signals', 0) + 1
            perf['total_pips'] = perf.get('total_pips', 0) + pips
        
        # Update success rate
        total = perf.get('total_signals', 1)
        wins = perf.get('successful_signals', 0)
        perf['success_rate'] = (wins / total) * 100 if total > 0 else 0
        
        self.module_performance[module_name] = perf
    
    def get_module_stats(self) -> Dict[str, Dict]:
        """Get performance stats for all modules"""
        
        stats = {}
        
        for module_name, module in self.modules.items():
            perf = self.module_performance.get(module_name, {})
            
            stats[module_name] = {
                'type': module.type.value,
                'strategy': module.strategy,
                'icon': module.icon,
                'total_signals': perf.get('total_signals', 0),
                'success_rate': round(perf.get('success_rate', 0), 1),
                'total_pips': perf.get('total_pips', 0),
                'active': perf.get('total_signals', 0) > 0
            }
        
        return stats
    
    def format_module_display(self, module_name: str) -> str:
        """Format module info for user display"""
        
        module = self.modules.get(module_name)
        if not module:
            return "❓ Unknown Module"
        
        perf = self.module_performance.get(module_name, {})
        
        if module.type == ModuleType.SNIPER:
            # Classified display
            return f"""🎯 **SNIPER MODULE**
Strategy: [CLASSIFIED]
Success Rate: {perf.get('success_rate', 'N/A')}%
Status: ACTIVE"""
        
        else:
            # Full transparency for arcade
            return f"""{module.icon} **{module.strategy.upper()}**
Module: {module_name}
Description: {module.description}
Success Rate: {perf.get('success_rate', 0):.1f}%
Total Signals: {perf.get('total_signals', 0)}
Total Pips: {perf.get('total_pips', 0):.0f}"""
    
    def get_top_performers(self, limit: int = 5) -> List[Dict]:
        """Get top performing modules"""
        
        performers = []
        
        for module_name, perf in self.module_performance.items():
            if perf.get('total_signals', 0) >= 10:  # Min signals for ranking
                performers.append({
                    'module': module_name,
                    'type': self.modules[module_name].type.value,
                    'icon': self.modules[module_name].icon,
                    'success_rate': perf.get('success_rate', 0),
                    'total_pips': perf.get('total_pips', 0)
                })
        
        # Sort by success rate
        performers.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return performers[:limit]