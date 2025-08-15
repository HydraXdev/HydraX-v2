#!/usr/bin/env python3
"""
ULTIMATE WAR ROOM - Gamified Trading Command Center
Complete overhaul with real-time data, live P&L, and social features
"""

def generate_ultimate_war_room(user_id, user_data=None):
    """
    Generate the Ultimate War Room HTML with gamification
    
    Args:
        user_id: User's Telegram ID
        user_data: Dict containing all user stats and positions
    """
    
    # Default data if not provided
    if not user_data:
        user_data = {
            'callsign': f'VIPER-{user_id[-4:]}',
            'rank': 'COMMANDER',
            'level': 42,
            'xp': 12450,
            'xp_to_next': 15000,
            'balance': 850.45,
            'equity': 892.33,
            'margin_used': 42.50,
            'free_margin': 849.83,
            'margin_level': 2099.60,
            'total_trades': 127,
            'win_rate': 48.5,
            'current_streak': 3,
            'best_streak': 12,
            'total_pnl': 4783.22,
            'today_pnl': 142.50,
            'week_pnl': 892.33,
            'month_pnl': 2341.15,
            'open_positions': [],
            'recent_trades': [],
            'achievements': [],
            'squad_size': 12,
            'global_rank': 247,
            'pattern_stats': {}
        }
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN WAR ROOM - {user_data['callsign']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            background: #000;
            color: #fff;
            font-family: 'Orbitron', 'Courier New', monospace;
            overflow-x: hidden;
            position: relative;
        }}
        
        /* Animated Background */
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(0, 217, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(255, 0, 128, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 20%, rgba(0, 255, 136, 0.1) 0%, transparent 50%);
            animation: backgroundPulse 20s ease-in-out infinite;
            z-index: -1;
        }}
        
        @keyframes backgroundPulse {{
            0%, 100% {{ opacity: 0.5; }}
            50% {{ opacity: 1; }}
        }}
        
        /* Header Section */
        .header {{
            background: linear-gradient(135deg, rgba(0,0,0,0.9), rgba(0,217,255,0.1));
            border-bottom: 2px solid #00D9FF;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }}
        
        .header::after {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0,217,255,0.3), transparent);
            animation: headerSweep 3s linear infinite;
        }}
        
        @keyframes headerSweep {{
            to {{ left: 100%; }}
        }}
        
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
            position: relative;
            z-index: 1;
        }}
        
        .user-profile {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .avatar {{
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #00D9FF, #FF0080);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            position: relative;
            animation: avatarRotate 10s linear infinite;
        }}
        
        @keyframes avatarRotate {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .avatar::before {{
            content: '';
            position: absolute;
            inset: -3px;
            background: conic-gradient(from 0deg, #00D9FF, #FF0080, #00FF88, #00D9FF);
            border-radius: 50%;
            z-index: -1;
            animation: avatarRotate 5s linear infinite reverse;
        }}
        
        .user-info h1 {{
            font-size: 28px;
            background: linear-gradient(90deg, #00D9FF, #FF0080);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 5px;
        }}
        
        .rank-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #000;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .level-progress {{
            margin-top: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            position: relative;
        }}
        
        .level-bar {{
            height: 100%;
            background: linear-gradient(90deg, #00D9FF, #00FF88);
            width: {int((user_data['xp'] / user_data['xp_to_next']) * 100)}%;
            position: relative;
            animation: levelPulse 2s ease-in-out infinite;
        }}
        
        @keyframes levelPulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}
        
        .header-stats {{
            display: flex;
            gap: 30px;
        }}
        
        .header-stat {{
            text-align: center;
        }}
        
        .header-stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #00D9FF;
        }}
        
        .header-stat-label {{
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Main Grid Layout */
        .dashboard {{
            display: grid;
            grid-template-columns: 300px 1fr 300px;
            gap: 20px;
            padding: 20px;
            max-width: 1800px;
            margin: 0 auto;
        }}
        
        @media (max-width: 1400px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Card Styles */
        .card {{
            background: linear-gradient(135deg, rgba(10,10,10,0.95), rgba(20,20,20,0.95));
            border: 1px solid rgba(0,217,255,0.3);
            border-radius: 15px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            border-color: #00D9FF;
            box-shadow: 0 10px 40px rgba(0,217,255,0.3);
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00D9FF, #FF0080, #00FF88);
            animation: cardTopBar 3s linear infinite;
        }}
        
        @keyframes cardTopBar {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        .card-title {{
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 20px;
            color: #00D9FF;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-title::before {{
            content: '▶';
            color: #FF0080;
            animation: titlePulse 1s ease-in-out infinite;
        }}
        
        @keyframes titlePulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        /* Account Overview */
        .account-stats {{
            display: grid;
            gap: 15px;
        }}
        
        .account-stat {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: rgba(0,217,255,0.05);
            border-radius: 8px;
            border-left: 3px solid #00D9FF;
        }}
        
        .account-stat-label {{
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }}
        
        .account-stat-value {{
            font-size: 18px;
            font-weight: bold;
            color: #00D9FF;
        }}
        
        .account-stat-value.positive {{
            color: #00FF88;
        }}
        
        .account-stat-value.negative {{
            color: #FF0044;
        }}
        
        /* Live Positions */
        .positions-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .position-item {{
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            position: relative;
            transition: all 0.3s ease;
        }}
        
        .position-item:hover {{
            background: rgba(0,217,255,0.1);
            border-color: #00D9FF;
        }}
        
        .position-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .position-symbol {{
            font-size: 16px;
            font-weight: bold;
            color: #fff;
        }}
        
        .position-direction {{
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .position-direction.buy {{
            background: rgba(0,255,136,0.2);
            color: #00FF88;
            border: 1px solid #00FF88;
        }}
        
        .position-direction.sell {{
            background: rgba(255,0,68,0.2);
            color: #FF0044;
            border: 1px solid #FF0044;
        }}
        
        .position-details {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            font-size: 12px;
        }}
        
        .position-detail {{
            display: flex;
            flex-direction: column;
        }}
        
        .position-detail-label {{
            color: #666;
            font-size: 10px;
            text-transform: uppercase;
        }}
        
        .position-detail-value {{
            color: #fff;
            font-weight: bold;
        }}
        
        .position-pnl {{
            text-align: right;
            font-size: 18px;
            font-weight: bold;
            margin-top: 10px;
        }}
        
        .position-actions {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }}
        
        .position-action {{
            flex: 1;
            padding: 8px;
            background: linear-gradient(135deg, rgba(0,217,255,0.1), rgba(0,217,255,0.2));
            border: 1px solid #00D9FF;
            border-radius: 5px;
            color: #00D9FF;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }}
        
        .position-action:hover {{
            background: #00D9FF;
            color: #000;
            transform: scale(1.05);
        }}
        
        .position-action.close {{
            background: linear-gradient(135deg, rgba(255,0,68,0.1), rgba(255,0,68,0.2));
            border-color: #FF0044;
            color: #FF0044;
        }}
        
        .position-action.close:hover {{
            background: #FF0044;
            color: #fff;
        }}
        
        /* Performance Chart */
        .chart-container {{
            height: 300px;
            position: relative;
            background: rgba(0,0,0,0.5);
            border-radius: 10px;
            padding: 20px;
        }}
        
        .chart-placeholder {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 14px;
        }}
        
        /* Pattern Performance */
        .pattern-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        
        .pattern-card {{
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .pattern-card:hover {{
            background: rgba(0,217,255,0.1);
            border-color: #00D9FF;
            transform: scale(1.05);
        }}
        
        .pattern-name {{
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        
        .pattern-winrate {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .pattern-trades {{
            font-size: 10px;
            color: #666;
        }}
        
        /* Action Buttons */
        .action-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }}
        
        .action-button {{
            padding: 15px;
            background: linear-gradient(135deg, rgba(0,217,255,0.1), rgba(0,217,255,0.2));
            border: 2px solid #00D9FF;
            border-radius: 10px;
            color: #00D9FF;
            font-weight: bold;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            text-decoration: none;
            display: block;
            position: relative;
            overflow: hidden;
        }}
        
        .action-button::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(0,217,255,0.5);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: all 0.5s ease;
        }}
        
        .action-button:hover::before {{
            width: 300px;
            height: 300px;
        }}
        
        .action-button:hover {{
            background: #00D9FF;
            color: #000;
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0,217,255,0.5);
        }}
        
        .action-button.primary {{
            background: linear-gradient(135deg, rgba(0,255,136,0.1), rgba(0,255,136,0.2));
            border-color: #00FF88;
            color: #00FF88;
        }}
        
        .action-button.primary:hover {{
            background: #00FF88;
            color: #000;
        }}
        
        /* Social Features */
        .social-share {{
            background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(255,215,0,0.2));
            border: 2px solid #FFD700;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            text-align: center;
        }}
        
        .share-title {{
            color: #FFD700;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .share-buttons {{
            display: flex;
            gap: 10px;
            justify-content: center;
        }}
        
        .share-button {{
            padding: 10px 20px;
            background: rgba(255,215,0,0.2);
            border: 1px solid #FFD700;
            border-radius: 5px;
            color: #FFD700;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .share-button:hover {{
            background: #FFD700;
            color: #000;
            transform: scale(1.1);
        }}
        
        /* Norman's Notebook Integration */
        .notebook-quick {{
            background: linear-gradient(135deg, rgba(0,255,65,0.1), rgba(0,255,65,0.2));
            border: 2px solid #00FF41;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .notebook-title {{
            color: #00FF41;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .notebook-entry {{
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(0,255,65,0.3);
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            font-size: 12px;
            color: #aaa;
        }}
        
        .notebook-add {{
            width: 100%;
            padding: 10px;
            background: rgba(0,255,65,0.1);
            border: 1px solid #00FF41;
            border-radius: 5px;
            color: #00FF41;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .notebook-add:hover {{
            background: #00FF41;
            color: #000;
        }}
        
        /* Loading States */
        .loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0,217,255,0.3);
            border-top-color: #00D9FF;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Toast Notifications */
        .toast {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, rgba(0,217,255,0.9), rgba(0,217,255,0.8));
            color: #fff;
            padding: 15px 25px;
            border-radius: 10px;
            font-weight: bold;
            animation: slideIn 0.3s ease;
            z-index: 1000;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateX(100%);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
    </style>
</head>
<body>
    <!-- Header Section -->
    <div class="header">
        <div class="header-content">
            <div class="user-profile">
                <div class="avatar">⚡</div>
                <div class="user-info">
                    <h1>{user_data['callsign']}</h1>
                    <span class="rank-badge">{user_data['rank']} • LVL {user_data['level']}</span>
                    <div class="level-progress">
                        <div class="level-bar"></div>
                    </div>
                </div>
            </div>
            <div class="header-stats">
                <div class="header-stat">
                    <div class="header-stat-value">{user_data['win_rate']}%</div>
                    <div class="header-stat-label">Win Rate</div>
                </div>
                <div class="header-stat">
                    <div class="header-stat-value">${user_data['today_pnl']:,.2f}</div>
                    <div class="header-stat-label">Today P&L</div>
                </div>
                <div class="header-stat">
                    <div class="header-stat-value">#{user_data['global_rank']}</div>
                    <div class="header-stat-label">Global Rank</div>
                </div>
                <div class="header-stat">
                    <div class="header-stat-value">{user_data['current_streak']}</div>
                    <div class="header-stat-label">Current Streak</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Main Dashboard -->
    <div class="dashboard">
        <!-- Left Sidebar -->
        <div class="sidebar-left">
            <!-- Account Overview -->
            <div class="card">
                <div class="card-title">Account Overview</div>
                <div class="account-stats">
                    <div class="account-stat">
                        <span class="account-stat-label">Balance</span>
                        <span class="account-stat-value">${user_data['balance']:,.2f}</span>
                    </div>
                    <div class="account-stat">
                        <span class="account-stat-label">Equity</span>
                        <span class="account-stat-value {'positive' if user_data['equity'] > user_data['balance'] else 'negative'}">${user_data['equity']:,.2f}</span>
                    </div>
                    <div class="account-stat">
                        <span class="account-stat-label">Free Margin</span>
                        <span class="account-stat-value">${user_data['free_margin']:,.2f}</span>
                    </div>
                    <div class="account-stat">
                        <span class="account-stat-label">Margin Level</span>
                        <span class="account-stat-value">{user_data['margin_level']:.1f}%</span>
                    </div>
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="card">
                <div class="card-title">Quick Actions</div>
                <div class="action-grid">
                    <a href="/signals" class="action-button primary">View Signals</a>
                    <a href="/notebook/{user_id}" class="action-button">Open Notebook</a>
                    <a href="#" onclick="refreshData()" class="action-button">Refresh Data</a>
                    <a href="#" onclick="showSettings()" class="action-button">Settings</a>
                </div>
            </div>
            
            <!-- Norman's Notebook Quick Access -->
            <div class="notebook-quick">
                <div class="notebook-title">📓 Norman's Notebook</div>
                <div class="notebook-entry">Last entry: "Great EURUSD setup today..."</div>
                <button class="notebook-add" onclick="openNotebook()">Add New Entry</button>
            </div>
        </div>
        
        <!-- Center Content -->
        <div class="main-content">
            <!-- Live Positions -->
            <div class="card">
                <div class="card-title">Live Positions ({len(user_data.get('open_positions', []))})</div>
                <div class="positions-list" id="positions-list">
                    <div class="position-item">
                        <div class="position-header">
                            <span class="position-symbol">EURUSD</span>
                            <span class="position-direction buy">BUY</span>
                        </div>
                        <div class="position-details">
                            <div class="position-detail">
                                <span class="position-detail-label">Entry</span>
                                <span class="position-detail-value">1.1650</span>
                            </div>
                            <div class="position-detail">
                                <span class="position-detail-label">Current</span>
                                <span class="position-detail-value">1.1672</span>
                            </div>
                            <div class="position-detail">
                                <span class="position-detail-label">Lots</span>
                                <span class="position-detail-value">0.01</span>
                            </div>
                        </div>
                        <div class="position-pnl positive">+$22.00</div>
                        <div class="position-actions">
                            <button class="position-action">Modify</button>
                            <button class="position-action close">Close</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Performance Chart -->
            <div class="card">
                <div class="card-title">Performance Chart</div>
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
            
            <!-- Pattern Performance -->
            <div class="card">
                <div class="card-title">Pattern Performance</div>
                <div class="pattern-grid">
                    <div class="pattern-card">
                        <div class="pattern-name">Liquidity Sweep</div>
                        <div class="pattern-winrate positive">52.3%</div>
                        <div class="pattern-trades">43 trades</div>
                    </div>
                    <div class="pattern-card">
                        <div class="pattern-name">VCB Breakout</div>
                        <div class="pattern-winrate positive">48.7%</div>
                        <div class="pattern-trades">38 trades</div>
                    </div>
                    <div class="pattern-card">
                        <div class="pattern-name">Order Block</div>
                        <div class="pattern-winrate positive">51.2%</div>
                        <div class="pattern-trades">41 trades</div>
                    </div>
                    <div class="pattern-card">
                        <div class="pattern-name">Sweep Return</div>
                        <div class="pattern-winrate negative">45.8%</div>
                        <div class="pattern-trades">24 trades</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Right Sidebar -->
        <div class="sidebar-right">
            <!-- Recent Trades -->
            <div class="card">
                <div class="card-title">Recent Trades</div>
                <div class="trades-list">
                    <!-- Trades will be populated here -->
                </div>
            </div>
            
            <!-- Social Share -->
            <div class="social-share">
                <div class="share-title">Share Your Success</div>
                <div class="share-buttons">
                    <button class="share-button" onclick="shareToTwitter()">Twitter</button>
                    <button class="share-button" onclick="shareToTelegram()">Telegram</button>
                    <button class="share-button" onclick="copyStats()">Copy Stats</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Real-time data updates
        let ws = null;
        let updateInterval = null;
        
        function connectWebSocket() {{
            // Connect to real-time data stream
            ws = new WebSocket('ws://localhost:8889/ws/user/{user_id}');
            
            ws.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                updateDashboard(data);
            }};
            
            ws.onerror = function(error) {{
                console.error('WebSocket error:', error);
                // Fallback to polling
                startPolling();
            }};
        }}
        
        function startPolling() {{
            updateInterval = setInterval(() => {{
                fetch('/api/user/{user_id}/live-data')
                    .then(res => res.json())
                    .then(data => updateDashboard(data));
            }}, 5000); // Update every 5 seconds
        }}
        
        function updateDashboard(data) {{
            // Update account stats
            if (data.account) {{
                document.querySelectorAll('.account-stat-value').forEach((el, i) => {{
                    const values = [data.account.balance, data.account.equity, data.account.free_margin, data.account.margin_level];
                    if (values[i] !== undefined) {{
                        el.textContent = typeof values[i] === 'number' ? 
                            (i === 3 ? values[i].toFixed(1) + '%' : '$' + values[i].toFixed(2)) : 
                            values[i];
                    }}
                }});
            }}
            
            // Update positions
            if (data.positions) {{
                updatePositions(data.positions);
            }}
            
            // Update P&L
            if (data.pnl) {{
                updatePnL(data.pnl);
            }}
        }}
        
        function updatePositions(positions) {{
            const container = document.getElementById('positions-list');
            container.innerHTML = positions.map(pos => `
                <div class="position-item">
                    <div class="position-header">
                        <span class="position-symbol">${{pos.symbol}}</span>
                        <span class="position-direction ${{pos.direction.toLowerCase()}}">${{pos.direction}}</span>
                    </div>
                    <div class="position-details">
                        <div class="position-detail">
                            <span class="position-detail-label">Entry</span>
                            <span class="position-detail-value">${{pos.entry.toFixed(5)}}</span>
                        </div>
                        <div class="position-detail">
                            <span class="position-detail-label">Current</span>
                            <span class="position-detail-value">${{pos.current.toFixed(5)}}</span>
                        </div>
                        <div class="position-detail">
                            <span class="position-detail-label">Lots</span>
                            <span class="position-detail-value">${{pos.lots}}</span>
                        </div>
                    </div>
                    <div class="position-pnl ${{pos.pnl >= 0 ? 'positive' : 'negative'}}">${{pos.pnl >= 0 ? '+' : ''}}${{pos.pnl.toFixed(2)}}</div>
                    <div class="position-actions">
                        <button class="position-action" onclick="modifyPosition('${{pos.id}}')">Modify</button>
                        <button class="position-action close" onclick="closePosition('${{pos.id}}')">Close</button>
                    </div>
                </div>
            `).join('');
        }}
        
        function closePosition(positionId) {{
            if (confirm('Close this position?')) {{
                fetch(`/api/position/${{positionId}}/close`, {{ method: 'POST' }})
                    .then(res => res.json())
                    .then(data => {{
                        if (data.success) {{
                            showToast('Position closed successfully');
                            refreshData();
                        }}
                    }});
            }}
        }}
        
        function shareToTwitter() {{
            const text = `Just hit {user_data['win_rate']}% win rate on BITTEN! 🎯\\n\\nToday's P&L: ${{user_data['today_pnl']:.2f}}\\nGlobal Rank: #{user_data['global_rank']}\\n\\nJoin me: bitten.app/ref/{user_id}`;
            window.open(`https://twitter.com/intent/tweet?text=${{encodeURIComponent(text)}}`, '_blank');
        }}
        
        function shareToTelegram() {{
            const text = `🔥 BITTEN WAR ROOM Stats\\n\\nWin Rate: {user_data['win_rate']}%\\nToday P&L: ${{user_data['today_pnl']:.2f}}\\nGlobal Rank: #{user_data['global_rank']}`;
            window.open(`https://t.me/share/url?url=bitten.app&text=${{encodeURIComponent(text)}}`, '_blank');
        }}
        
        function copyStats() {{
            const stats = `BITTEN Stats - {user_data['callsign']}
Win Rate: {user_data['win_rate']}%
Today P&L: ${user_data['today_pnl']:.2f}
Week P&L: ${user_data['week_pnl']:.2f}
Global Rank: #{user_data['global_rank']}
Current Streak: {user_data['current_streak']}`;
            
            navigator.clipboard.writeText(stats);
            showToast('Stats copied to clipboard!');
        }}
        
        function showToast(message) {{
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {{
                toast.remove();
            }}, 3000);
        }}
        
        function refreshData() {{
            fetch('/api/user/{user_id}/refresh', {{ method: 'POST' }})
                .then(() => location.reload());
        }}
        
        function openNotebook() {{
            window.open('/notebook/{user_id}', '_blank');
        }}
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', () => {{
            // Try WebSocket first
            connectWebSocket();
            
            // Initialize chart
            initPerformanceChart();
            
            // Add keyboard shortcuts
            document.addEventListener('keydown', (e) => {{
                if (e.ctrlKey && e.key === 'r') {{
                    e.preventDefault();
                    refreshData();
                }}
            }});
        }});
        
        function initPerformanceChart() {{
            // Placeholder for chart initialization
            // Would integrate with Chart.js or similar
            const canvas = document.getElementById('performanceChart');
            if (canvas) {{
                canvas.innerHTML = '<div class="chart-placeholder">Chart loading...</div>';
            }}
        }}
    </script>
</body>
</html>
"""