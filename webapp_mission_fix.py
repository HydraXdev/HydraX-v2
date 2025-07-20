#!/usr/bin/env python3
"""
Fixed WebApp Route for Mission Briefing Template
"""

import os
import json
from datetime import datetime
from flask import Flask, request, send_from_directory

app = Flask(__name__)

@app.route('/styles.css')
def serve_css():
    """Serve CSS file for FANG HUD"""
    return send_from_directory('/root/HydraX-v2/src/ui/fang_hud/', 'styles.css', mimetype='text/css')

@app.route('/fang_logic.js')
def serve_js():
    """Serve JS file for FANG HUD"""
    return send_from_directory('/root/HydraX-v2/src/ui/fang_hud/', 'fang_logic.js', mimetype='application/javascript')

@app.route('/test/<tier>')
def test_tier(tier):
    """Test different tier appearances"""
    template_path = '/root/HydraX-v2/mission_brief_simple.html'
    
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Mock data for testing
    template_content = template_content.replace('TIER: LOADING...', f'TIER: {tier.upper()}')
    template_content = template_content.replace('id="currentStreak">0</span>', f'id="currentStreak">{"5" if tier == "nibbler" else "12" if tier == "fang" else "28"}</span>')
    template_content = template_content.replace('id="winRate">0%</span>', f'id="winRate">{"58" if tier == "nibbler" else "68" if tier == "fang" else "78"}%</span>')
    template_content = template_content.replace('id="todayPnL">+0%</span>', f'id="todayPnL">+{"1.2" if tier == "nibbler" else "3.8" if tier == "fang" else "7.5"}%</span>')
    template_content = template_content.replace('id="symbol">LOADING...</span>', f'id="symbol">USDJPY</span>')
    template_content = template_content.replace('id="direction">--</span>', f'id="direction">BUY</span>')
    template_content = template_content.replace('id="tcsScore">--</div>', f'id="tcsScore">{"72" if tier == "nibbler" else "78" if tier == "fang" else "88"}</div>')
    template_content = template_content.replace('id="entryPrice">0.00000</div>', f'id="entryPrice">148.919</div>')
    template_content = template_content.replace('id="stopLoss">0.00000</div>', f'id="stopLoss">148.770</div>')
    template_content = template_content.replace('id="takeProfit">0.00000</div>', f'id="takeProfit">149.235</div>')
    template_content = template_content.replace('id="riskRatio">1:0</div>', f'id="riskRatio">1:2.1</div>')
    template_content = template_content.replace('Analyzing...', f'{"Good Signal Quality" if tier == "nibbler" else "High Confidence Signal" if tier == "fang" else "Elite Level Signal"}')
    
    return template_content

@app.route('/hud')
def mission_briefing():
    """Mission briefing interface using proper template"""
    try:
        mission_id = request.args.get('mission_id')
        if not mission_id:
            return "Missing mission_id parameter", 400
        
        # Load mission data
        mission_file = f"./missions/{mission_id}.json"
        if not os.path.exists(mission_file):
            return f"Mission {mission_id} not found", 404
        
        with open(mission_file, 'r') as f:
            mission_data = f.read()
        
        # Load mission data to determine tier
        mission_obj = json.loads(mission_data)
        user_tier = mission_obj.get('user', {}).get('tier', 'FANG')
        
        # Use the streamlined mission brief template for all tiers
        template_path = '/root/HydraX-v2/mission_brief_simple.html'
        
        # Load the streamlined mission brief template
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Inject real mission data into the template
        signal_data = mission_obj.get('signal', {})
        user_data = mission_obj.get('user', {})
        user_stats = user_data.get('stats', {})
        
        # Replace personal stats
        template_content = template_content.replace('TIER: LOADING...', f'TIER: {user_data.get("tier", "FANG")}')
        template_content = template_content.replace('id="currentStreak">0</span>', f'id="currentStreak">{user_stats.get("streak_days", "0")}</span>')
        template_content = template_content.replace('id="winRate">0%</span>', f'id="winRate">{user_stats.get("win_rate", "0")}%</span>')
        template_content = template_content.replace('id="todayPnL">+0%</span>', f'id="todayPnL">+{user_stats.get("last_7d_pips", "0")}%</span>')
        
        # Replace signal data
        template_content = template_content.replace('id="symbol">LOADING...</span>', f'id="symbol">{signal_data.get("symbol", "LOADING...")}</span>')
        template_content = template_content.replace('id="direction">--</span>', f'id="direction">{signal_data.get("direction", "--")}</span>')
        template_content = template_content.replace('id="tcsScore">--</div>', f'id="tcsScore">{signal_data.get("tcs_score", "--")}</div>')
        template_content = template_content.replace('id="entryPrice">0.00000</div>', f'id="entryPrice">{signal_data.get("entry_price", "0.00000")}</div>')
        template_content = template_content.replace('id="stopLoss">0.00000</div>', f'id="stopLoss">{signal_data.get("stop_loss", "0.00000")}</div>')
        template_content = template_content.replace('id="takeProfit">0.00000</div>', f'id="takeProfit">{signal_data.get("take_profit", "0.00000")}</div>')
        template_content = template_content.replace('id="riskRatio">1:0</div>', f'id="riskRatio">1:{signal_data.get("risk_reward_ratio", "0")}</div>')
        
        # Update confidence text based on TCS score
        tcs_score = signal_data.get('tcs_score', 0)
        if tcs_score >= 80:
            confidence_text = 'High Confidence Signal'
        elif tcs_score >= 70:
            confidence_text = 'Good Signal Quality'
        else:
            confidence_text = 'Moderate Confidence'
        template_content = template_content.replace('Analyzing...', confidence_text)
        
        return template_content
        
    except Exception as e:
        return f"Error loading mission: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889, debug=True)