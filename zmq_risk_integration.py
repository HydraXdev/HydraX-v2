#!/usr/bin/env python3
"""
ZMQ Risk Integration Module
Real-time risk monitoring and alerts based on telemetry
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger('ZMQRiskIntegration')

class ZMQRiskIntegration:
    """
    Real-time risk monitoring based on ZMQ telemetry stream
    """
    
    def __init__(self):
        self.risk_thresholds = {
            'margin_level_warning': 200,     # Warn below 200%
            'margin_level_critical': 150,    # Critical below 150%
            'margin_level_danger': 100,      # Immediate danger below 100%
            'drawdown_warning': 10,          # Warn at 10% drawdown
            'drawdown_critical': 20,         # Critical at 20% drawdown
            'position_limit_nibbler': 1,
            'position_limit_fang': 2,
            'position_limit_commander': 3,
            'position_limit_apex': 5
        }
        
        self.user_risk_state = {}  # Track risk state per user
        self.risk_alerts = defaultdict(list)  # History of risk alerts
        
    def analyze_telemetry_risk(self, telemetry: Dict, user_tier: str = 'nibbler') -> Dict:
        """
        Analyze telemetry for risk conditions
        
        Returns:
            Dict with risk_level, alerts, and recommendations
        """
        uuid = telemetry.get('uuid', '')
        
        # Initialize risk state if new user
        if uuid not in self.user_risk_state:
            self.user_risk_state[uuid] = {
                'peak_equity': telemetry.get('equity', 0),
                'initial_balance': telemetry.get('balance', 0),
                'last_alert_time': None,
                'alert_count': 0
            }
        
        state = self.user_risk_state[uuid]
        alerts = []
        risk_level = 'normal'
        
        # Update peak equity
        current_equity = telemetry.get('equity', 0)
        if current_equity > state['peak_equity']:
            state['peak_equity'] = current_equity
        
        # 1. Check margin level
        margin_level = telemetry.get('margin_level', 0)
        if margin_level > 0:  # Only check if positions are open
            if margin_level < self.risk_thresholds['margin_level_danger']:
                risk_level = 'danger'
                alerts.append({
                    'type': 'margin_call_imminent',
                    'message': f'⚠️ MARGIN CALL IMMINENT! Level: {margin_level:.1f}%',
                    'severity': 'danger',
                    'action': 'Close positions immediately'
                })
            elif margin_level < self.risk_thresholds['margin_level_critical']:
                risk_level = 'critical' if risk_level != 'danger' else risk_level
                alerts.append({
                    'type': 'margin_critical',
                    'message': f'🚨 Critical margin level: {margin_level:.1f}%',
                    'severity': 'critical',
                    'action': 'Reduce position size urgently'
                })
            elif margin_level < self.risk_thresholds['margin_level_warning']:
                risk_level = 'warning' if risk_level == 'normal' else risk_level
                alerts.append({
                    'type': 'margin_warning',
                    'message': f'⚠️ Low margin level: {margin_level:.1f}%',
                    'severity': 'warning',
                    'action': 'Monitor closely, avoid new positions'
                })
        
        # 2. Check drawdown
        if state['peak_equity'] > 0:
            drawdown_pct = ((state['peak_equity'] - current_equity) / state['peak_equity']) * 100
            
            if drawdown_pct > self.risk_thresholds['drawdown_critical']:
                risk_level = 'critical' if risk_level != 'danger' else risk_level
                alerts.append({
                    'type': 'drawdown_critical',
                    'message': f'📉 Critical drawdown: {drawdown_pct:.1f}%',
                    'severity': 'critical',
                    'action': 'Review strategy, consider pause'
                })
            elif drawdown_pct > self.risk_thresholds['drawdown_warning']:
                risk_level = 'warning' if risk_level == 'normal' else risk_level
                alerts.append({
                    'type': 'drawdown_warning',
                    'message': f'📊 Drawdown alert: {drawdown_pct:.1f}%',
                    'severity': 'warning',
                    'action': 'Tighten risk management'
                })
        
        # 3. Check position limits
        positions = telemetry.get('positions', 0)
        position_limit = self.risk_thresholds.get(f'position_limit_{user_tier}', 1)
        
        if positions > position_limit:
            alerts.append({
                'type': 'position_limit_exceeded',
                'message': f'🔒 Position limit exceeded: {positions}/{position_limit}',
                'severity': 'warning',
                'action': 'Close excess positions'
            })
        
        # 4. Check free margin
        free_margin = telemetry.get('free_margin', 0)
        if free_margin < 100 and positions > 0:
            alerts.append({
                'type': 'low_free_margin',
                'message': f'💰 Low free margin: ${free_margin:.2f}',
                'severity': 'warning',
                'action': 'No new positions available'
            })
        
        # Store alerts in history
        if alerts:
            self.risk_alerts[uuid].extend([{
                **alert,
                'timestamp': datetime.now().isoformat()
            } for alert in alerts])
            
            # Keep only last 100 alerts per user
            self.risk_alerts[uuid] = self.risk_alerts[uuid][-100:]
            
            # Update alert tracking
            state['last_alert_time'] = datetime.now()
            state['alert_count'] += len(alerts)
        
        return {
            'risk_level': risk_level,
            'alerts': alerts,
            'metrics': {
                'margin_level': margin_level,
                'drawdown_pct': drawdown_pct if state['peak_equity'] > 0 else 0,
                'positions': positions,
                'free_margin': free_margin
            },
            'recommendations': self._get_risk_recommendations(risk_level, alerts)
        }
        
    def _get_risk_recommendations(self, risk_level: str, alerts: List[Dict]) -> List[str]:
        """
        Generate risk management recommendations
        """
        recommendations = []
        
        if risk_level == 'danger':
            recommendations.extend([
                "🚨 IMMEDIATE ACTION REQUIRED",
                "Close all positions to avoid margin call",
                "Do not open new positions",
                "Contact support if needed"
            ])
        elif risk_level == 'critical':
            recommendations.extend([
                "Reduce position sizes immediately",
                "Set tight stop losses on all trades",
                "Avoid high-volatility pairs",
                "Consider taking profits on winning positions"
            ])
        elif risk_level == 'warning':
            recommendations.extend([
                "Monitor positions closely",
                "Use smaller position sizes",
                "Ensure stop losses are in place",
                "Review your risk management strategy"
            ])
        else:
            recommendations.extend([
                "Risk levels normal",
                "Continue following your trading plan",
                "Maintain disciplined position sizing"
            ])
        
        return recommendations
        
    def should_block_new_trades(self, telemetry: Dict, user_tier: str = 'nibbler') -> Tuple[bool, str]:
        """
        Determine if new trades should be blocked based on risk
        
        Returns:
            Tuple of (should_block, reason)
        """
        risk_analysis = self.analyze_telemetry_risk(telemetry, user_tier)
        
        # Block if risk level is critical or danger
        if risk_analysis['risk_level'] in ['critical', 'danger']:
            return True, f"Risk level too high: {risk_analysis['risk_level']}"
        
        # Block if margin level too low
        margin_level = telemetry.get('margin_level', 0)
        if margin_level > 0 and margin_level < 150:
            return True, f"Margin level too low: {margin_level:.1f}%"
        
        # Block if position limit exceeded
        positions = telemetry.get('positions', 0)
        position_limit = self.risk_thresholds.get(f'position_limit_{user_tier}', 1)
        if positions >= position_limit:
            return True, f"Position limit reached: {positions}/{position_limit}"
        
        # Block if free margin too low
        free_margin = telemetry.get('free_margin', 0)
        if free_margin < 50:
            return True, f"Insufficient free margin: ${free_margin:.2f}"
        
        return False, "Risk check passed"
        
    def get_user_risk_summary(self, uuid: str) -> Dict:
        """
        Get comprehensive risk summary for a user
        """
        if uuid not in self.user_risk_state:
            return {
                'risk_level': 'unknown',
                'alerts': [],
                'recommendations': ['No data available']
            }
        
        state = self.user_risk_state[uuid]
        recent_alerts = [a for a in self.risk_alerts[uuid] if 
                        datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=24)]
        
        return {
            'risk_state': state,
            'recent_alerts': recent_alerts,
            'alert_frequency': len(recent_alerts),
            'last_alert': state['last_alert_time'].isoformat() if state['last_alert_time'] else None
        }

# Integration functions

def monitor_risk_from_telemetry(telemetry_service, risk_integration: ZMQRiskIntegration):
    """
    Set up real-time risk monitoring from telemetry stream
    """
    def risk_callback(uuid: str, telemetry: Dict):
        # Analyze risk
        risk_analysis = risk_integration.analyze_telemetry_risk(telemetry)
        
        # Log alerts
        for alert in risk_analysis['alerts']:
            logger.warning(f"{alert['message']} (User: {uuid})")
        
        # Here you would send alerts to users
        # if risk_analysis['risk_level'] in ['critical', 'danger']:
        #     send_risk_alert(uuid, risk_analysis)
    
    telemetry_service.set_risk_callback(risk_callback)
    
def block_risky_trades(fire_router, telemetry_service, risk_integration: ZMQRiskIntegration):
    """
    Integration to block trades based on risk assessment
    """
    def pre_trade_risk_check(user_id: str, trade_request: Dict) -> Tuple[bool, str]:
        # Get latest telemetry
        telemetry = telemetry_service.get_user_telemetry(user_id)
        if not telemetry:
            return True, "No telemetry data available"
        
        # Check if trade should be blocked
        should_block, reason = risk_integration.should_block_new_trades(telemetry)
        
        if should_block:
            logger.warning(f"🚫 Trade blocked for {user_id}: {reason}")
        
        return not should_block, reason
    
    # This would integrate with fire_router
    # fire_router.add_pre_trade_check(pre_trade_risk_check)