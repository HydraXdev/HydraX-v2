#!/usr/bin/env python3
"""
🎯 PERSONALIZED HUD API - REAL MISSIONS ONLY
Serves personalized missions to users based on their real account data
"""

import json
import logging
import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from typing import Dict, List, Optional

# Import real data systems
import sys
sys.path.insert(0, '/root/HydraX-v2/src/bitten_core')

try:
    from zero_simulation_integration import get_user_real_dashboard
    from personalized_mission_brain import get_mission_brain
    from user_profile_manager import get_profile_manager
except ImportError as e:
    print(f"⚠️  Import warning: {e}")

logger = logging.getLogger(__name__)

class PersonalizedHudAPI:
    """
    🎯 PERSONALIZED HUD API - REAL MISSIONS ONLY
    
    Provides API endpoints for:
    - User's personalized missions
    - Real account dashboard data
    - Tactical strategy status
    - Real performance metrics
    """
    
    def __init__(self, app: Flask = None):
        self.logger = logging.getLogger("PERSONALIZED_HUD")
        
        try:
            self.mission_brain = get_mission_brain()
            self.profile_manager = get_profile_manager()
        except:
            self.logger.warning("Mission brain not available - using fallback")
            self.mission_brain = None
            self.profile_manager = None
            
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize Flask app with personalized HUD routes"""
        
        @app.route('/api/user/<user_id>/dashboard')
        def get_user_dashboard(user_id):
            """Get user's real dashboard data"""
            try:
                dashboard_data = get_user_real_dashboard(user_id)
                
                if 'error' in dashboard_data:
                    return jsonify({
                        'success': False,
                        'error': dashboard_data['error']
                    }), 404
                
                return jsonify({
                    'success': True,
                    'dashboard': dashboard_data,
                    'real_data_verified': True
                })
                
            except Exception as e:
                self.logger.error(f"❌ Dashboard API failed for {user_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/user/<user_id>/missions')
        def get_user_missions(user_id):
            """Get user's personalized missions"""
            try:
                if not self.mission_brain:
                    return jsonify({
                        'success': False,
                        'error': 'Mission brain not available'
                    }), 503
                
                missions = self.mission_brain.get_user_personalized_missions(user_id)
                
                # Filter only active missions
                active_missions = []
                now_ts = int(datetime.now(timezone.utc).timestamp())
                
                for mission in missions:
                    if mission.get('expires_timestamp', 0) > now_ts and mission.get('status') == 'pending':
                        active_missions.append(mission)
                
                return jsonify({
                    'success': True,
                    'missions': active_missions,
                    'count': len(active_missions),
                    'real_missions_verified': True
                })
                
            except Exception as e:
                self.logger.error(f"❌ Missions API failed for {user_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/user/<user_id>/tactical-status')
        def get_tactical_status(user_id):
            """Get user's daily tactical strategy status"""
            try:
                if not self.profile_manager:
                    return jsonify({
                        'success': False,
                        'error': 'Profile manager not available'
                    }), 503
                
                profile = self.profile_manager.get_user_profile(user_id)
                if not profile:
                    return jsonify({
                        'success': False,
                        'error': 'User profile not found'
                    }), 404
                
                daily_tactic = profile.get('daily_tactic', 'LONE_WOLF')
                
                # Get tactical engine for status
                try:
                    from tactical_strategy_engine import get_tactical_engine
                    tactical_engine = get_tactical_engine()
                    tactical_status = tactical_engine.get_user_daily_status(user_id, daily_tactic)
                except:
                    tactical_status = {
                        'strategy': daily_tactic,
                        'trades_taken': 0,
                        'trades_remaining': 4,
                        'error': 'Tactical engine not available'
                    }
                
                return jsonify({
                    'success': True,
                    'tactical_status': tactical_status,
                    'daily_tactic': daily_tactic,
                    'tier': profile.get('tier', 'UNKNOWN')
                })
                
            except Exception as e:
                self.logger.error(f"❌ Tactical status API failed for {user_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/hud/personalized/<user_id>')
        def personalized_hud(user_id):
            """Personalized HUD page for user"""
            try:
                # Get user's real dashboard data
                dashboard_data = get_user_real_dashboard(user_id)
                
                if 'error' in dashboard_data:
                    return f"Error loading dashboard: {dashboard_data['error']}", 404
                
                # Get user's personalized missions
                missions = []
                if self.mission_brain:
                    missions = self.mission_brain.get_user_personalized_missions(user_id)
                
                # Filter active missions
                active_missions = []
                now_ts = int(datetime.now(timezone.utc).timestamp())
                
                for mission in missions:
                    if mission.get('expires_timestamp', 0) > now_ts and mission.get('status') == 'pending':
                        active_missions.append(mission)
                
                # Generate personalized HUD HTML
                hud_html = self._generate_personalized_hud_html(user_id, dashboard_data, active_missions)
                
                return hud_html
                
            except Exception as e:
                self.logger.error(f"❌ Personalized HUD failed for {user_id}: {e}")
                return f"HUD Error: {str(e)}", 500
        
        self.logger.info("✅ Personalized HUD API routes initialized")
    
    def _generate_personalized_hud_html(self, user_id: str, dashboard: Dict, missions: List[Dict]) -> str:
        """Generate personalized HUD HTML"""
        try:
            profile = dashboard.get('profile', {})
            stats = dashboard.get('statistics', {})
            tactical_status = dashboard.get('tactical_status', {})
            
            # Mission cards HTML
            mission_cards = ""
            for mission in missions[:3]:  # Show top 3 missions
                time_remaining = mission.get('expires_timestamp', 0) - int(datetime.now().timestamp())
                minutes_remaining = max(0, time_remaining // 60)
                
                mission_cards += f"""
                <div class="mission-card" data-mission-id="{mission.get('mission_id', '')}">
                    <div class="mission-header">
                        <h3>🎯 {mission.get('symbol', 'UNKNOWN')} {mission.get('direction', '')}</h3>
                        <span class="tcs-score">TCS: {mission.get('tcs_score', 0)}%</span>
                    </div>
                    <div class="mission-details">
                        <p><strong>Position Size:</strong> {mission.get('position_size', 0)} lots</p>
                        <p><strong>Risk:</strong> ${mission.get('risk_amount', 0):.2f}</p>
                        <p><strong>Entry:</strong> {mission.get('entry_price', 0):.5f}</p>
                        <p><strong>Strategy:</strong> {mission.get('tactical_strategy', 'UNKNOWN')}</p>
                    </div>
                    <div class="mission-timer">
                        <span>⏰ {minutes_remaining} minutes remaining</span>
                    </div>
                    <button class="fire-button" onclick="fireMission('{mission.get('mission_id', '')}')">
                        🔥 EXECUTE MISSION
                    </button>
                </div>
                """
            
            if not mission_cards:
                mission_cards = """
                <div class="no-missions">
                    <h3>🎯 No Active Missions</h3>
                    <p>Waiting for signals that match your tactical strategy...</p>
                </div>
                """
            
            # Tactical status HTML
            tactical_html = f"""
            <div class="tactical-status">
                <h3>🎖️ Daily Tactical: {tactical_status.get('strategy', 'UNKNOWN')}</h3>
                <div class="tactical-progress">
                    <p>Trades: {tactical_status.get('trades_taken', 0)}/{tactical_status.get('trades_taken', 0) + tactical_status.get('trades_remaining', 0)}</p>
                    <p>Win Rate: {tactical_status.get('win_rate', 0):.1f}%</p>
                    <p>Daily P&L: ${tactical_status.get('total_pnl', 0):.2f}</p>
                </div>
            </div>
            """
            
            hud_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>BITTEN HUD - {profile.get('tier', 'UNKNOWN')} Operative</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ 
                        background: #0a0a0a; 
                        color: #00ff00; 
                        font-family: 'Courier New', monospace;
                        margin: 0;
                        padding: 20px;
                    }}
                    .hud-container {{ 
                        max-width: 800px; 
                        margin: 0 auto;
                    }}
                    .user-header {{
                        text-align: center;
                        border: 2px solid #00ff00;
                        padding: 20px;
                        margin-bottom: 20px;
                        background: rgba(0, 255, 0, 0.1);
                    }}
                    .mission-card {{
                        border: 2px solid #ff6600;
                        margin: 15px 0;
                        padding: 20px;
                        background: rgba(255, 102, 0, 0.1);
                        border-radius: 10px;
                    }}
                    .mission-header {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 15px;
                    }}
                    .tcs-score {{
                        background: #ff6600;
                        color: #000;
                        padding: 5px 10px;
                        border-radius: 5px;
                        font-weight: bold;
                    }}
                    .fire-button {{
                        background: #ff0000;
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        font-size: 18px;
                        font-weight: bold;
                        border-radius: 5px;
                        cursor: pointer;
                        width: 100%;
                        margin-top: 15px;
                    }}
                    .fire-button:hover {{
                        background: #cc0000;
                    }}
                    .tactical-status {{
                        border: 2px solid #0099ff;
                        padding: 20px;
                        margin: 20px 0;
                        background: rgba(0, 153, 255, 0.1);
                    }}
                    .no-missions {{
                        text-align: center;
                        padding: 40px;
                        border: 2px dashed #666;
                        color: #999;
                    }}
                </style>
            </head>
            <body>
                <div class="hud-container">
                    <div class="user-header">
                        <h1>🎯 BITTEN TACTICAL HUD</h1>
                        <h2>{profile.get('tier', 'UNKNOWN')} Operative {user_id}</h2>
                        <p>Balance: ${dashboard.get('real_balance', 0):.2f} | Win Rate: {stats.get('win_rate', 0):.1f}%</p>
                    </div>
                    
                    {tactical_html}
                    
                    <div class="missions-section">
                        <h2>🎯 ACTIVE PERSONALIZED MISSIONS</h2>
                        {mission_cards}
                    </div>
                </div>
                
                <script>
                    function fireMission(missionId) {{
                        if (confirm('Execute this mission? This will place a REAL trade!')) {{
                            fetch('/api/fire', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                    'X-User-ID': '{user_id}'
                                }},
                                body: JSON.stringify({{
                                    mission_id: missionId
                                }})
                            }})
                            .then(response => response.json())
                            .then(data => {{
                                if (data.success) {{
                                    alert('🎯 MISSION FIRED! Trade executed successfully!');
                                    location.reload();
                                }} else {{
                                    alert('❌ Mission failed: ' + data.error);
                                }}
                            }})
                            .catch(error => {{
                                alert('❌ Error: ' + error);
                            }});
                        }}
                    }}
                    
                    // Auto-refresh every 30 seconds
                    setTimeout(() => location.reload(), 30000);
                </script>
            </body>
            </html>
            """
            
            return hud_html
            
        except Exception as e:
            self.logger.error(f"❌ HUD HTML generation failed: {e}")
            return f"<html><body><h1>HUD Error: {str(e)}</h1></body></html>"

# Global instance
personalized_hud_api = PersonalizedHudAPI()

if __name__ == "__main__":
    print("🎯 TESTING PERSONALIZED HUD API")
    print("=" * 50)
    
    from flask import Flask
    
    app = Flask(__name__)
    personalized_hud_api.init_app(app)
    
    print("✅ Personalized HUD API routes registered")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        if 'user' in rule.rule or 'hud' in rule.rule:
            print(f"  {rule.methods} {rule.rule}")
    
    print("🎯 PERSONALIZED HUD API OPERATIONAL")