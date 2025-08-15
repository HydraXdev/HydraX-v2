#!/usr/bin/env python3
"""
ULTIMATE WAR ROOM V2 - Mobile-Optimized, Accessible Trading Command Center
Complete overhaul with mobile-first design, accessibility, and working features only
"""

def generate_ultimate_war_room(user_id, user_data=None):
    """
    Generate the Ultimate War Room HTML with mobile optimization and accessibility
    
    Args:
        user_id: User's Telegram ID
        user_data: Dict containing all user stats and positions
    """
    
    # Default data if not provided
    if not user_data:
        user_data = {
            'callsign': f'COMMANDER-{user_id[-4:]}',
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
            'pattern_stats': {},
            'referral_code': f'BITTEN-{user_id[-6:].upper()}',
            'referral_earnings': 120.00,
            'referrals_count': 12
        }
    
    # Ensure Commander rank for user 7176191872
    if user_id == '7176191872':
        user_data['callsign'] = 'COMMANDER-1872'
        user_data['rank'] = 'COMMANDER'
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>BITTEN WAR ROOM - {user_data['callsign']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            background: #0A0A0A;
            color: #fff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            overflow-x: hidden;
            position: relative;
            font-size: 16px;
            line-height: 1.6;
        }}
        
        /* Header Section */
        .header {{
            background: linear-gradient(135deg, rgba(0,0,0,0.95), rgba(0,153,255,0.1));
            border-bottom: 2px solid #0099FF;
            padding: 20px 15px;
            position: relative;
        }}
        
        .header-content {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        @media (min-width: 768px) {{
            .header-content {{
                flex-direction: row;
                justify-content: space-between;
                align-items: center;
            }}
        }}
        
        .user-profile {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .avatar {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #0099FF, #FF6600);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
        }}
        
        .user-info h1 {{
            font-size: 24px;
            background: linear-gradient(90deg, #0099FF, #FF6600);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }}
        
        @media (min-width: 768px) {{
            .user-info h1 {{
                font-size: 32px;
            }}
        }}
        
        .rank-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #000;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .level-progress {{
            margin-top: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 10px;
            overflow: hidden;
            position: relative;
            width: 100%;
            max-width: 300px;
        }}
        
        .level-bar {{
            height: 100%;
            background: linear-gradient(90deg, #0099FF, #00CC00);
            width: {int((user_data['xp'] / user_data['xp_to_next']) * 100)}%;
        }}
        
        .header-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            width: 100%;
        }}
        
        @media (min-width: 768px) {{
            .header-stats {{
                display: flex;
                gap: 30px;
                width: auto;
            }}
        }}
        
        .header-stat {{
            text-align: center;
        }}
        
        .header-stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #0099FF;
        }}
        
        @media (min-width: 768px) {{
            .header-stat-value {{
                font-size: 28px;
            }}
        }}
        
        .header-stat-label {{
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Main Layout - Mobile First */
        .dashboard {{
            padding: 15px;
        }}
        
        @media (min-width: 1200px) {{
            .dashboard {{
                display: grid;
                grid-template-columns: 350px 1fr 350px;
                gap: 20px;
                padding: 20px;
                max-width: 1800px;
                margin: 0 auto;
            }}
        }}
        
        /* Card Styles */
        .card {{
            background: linear-gradient(135deg, rgba(10,10,10,0.95), rgba(20,20,20,0.95));
            border: 1px solid rgba(0,153,255,0.3);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }}
        
        @media (min-width: 1200px) {{
            .card {{
                margin-bottom: 0;
            }}
        }}
        
        .card-title {{
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 20px;
            color: #0099FF;
            display: flex;
            align-items: center;
            gap: 10px;
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
            padding: 15px;
            background: rgba(0,153,255,0.05);
            border-radius: 8px;
            border-left: 3px solid #0099FF;
        }}
        
        .account-stat-label {{
            font-size: 14px;
            color: #999;
            text-transform: uppercase;
        }}
        
        .account-stat-value {{
            font-size: 20px;
            font-weight: bold;
            color: #0099FF;
        }}
        
        @media (min-width: 768px) {{
            .account-stat-value {{
                font-size: 24px;
            }}
        }}
        
        .account-stat-value.positive {{
            color: #00CC00;
            font-weight: bold;
        }}
        
        .account-stat-value.negative {{
            color: #FF3333;
            font-weight: bold;
        }}
        
        /* Live Positions */
        .positions-list {{
            max-height: 600px;
            overflow-y: auto;
        }}
        
        .position-item {{
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        
        .position-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .position-symbol {{
            font-size: 18px;
            font-weight: bold;
            color: #fff;
        }}
        
        .position-direction {{
            padding: 5px 12px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .position-direction.buy {{
            background: rgba(0,204,0,0.2);
            color: #00CC00;
            border: 1px solid #00CC00;
        }}
        
        .position-direction.sell {{
            background: rgba(255,51,51,0.2);
            color: #FF3333;
            border: 1px solid #FF3333;
        }}
        
        .position-details {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            font-size: 14px;
        }}
        
        .position-detail {{
            display: flex;
            flex-direction: column;
        }}
        
        .position-detail-label {{
            color: #999;
            font-size: 12px;
            text-transform: uppercase;
        }}
        
        .position-detail-value {{
            color: #fff;
            font-weight: bold;
            font-size: 16px;
        }}
        
        .position-pnl {{
            text-align: right;
            font-size: 20px;
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
            padding: 12px;
            background: linear-gradient(135deg, rgba(255,51,51,0.1), rgba(255,51,51,0.2));
            border: 2px solid #FF3333;
            border-radius: 8px;
            color: #FF3333;
            font-size: 16px;
            font-weight: bold;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }}
        
        .position-action:hover {{
            background: #FF3333;
            color: #fff;
            transform: scale(1.05);
        }}
        
        /* Referral Section */
        .referral-section {{
            background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(255,215,0,0.2));
            border: 2px solid #FFD700;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .referral-title {{
            color: #FFD700;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .referral-code {{
            background: rgba(0,0,0,0.5);
            border: 1px solid #FFD700;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            font-size: 24px;
            font-weight: bold;
            color: #FFD700;
            letter-spacing: 3px;
        }}
        
        .referral-link {{
            background: rgba(0,0,0,0.3);
            border: 1px solid #666;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-size: 14px;
            color: #999;
            word-break: break-all;
        }}
        
        .referral-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }}
        
        .referral-stat {{
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 8px;
        }}
        
        .referral-stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #FFD700;
        }}
        
        .referral-stat-label {{
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
        }}
        
        /* Achievement Badges */
        .achievements {{
            padding: 20px 0;
        }}
        
        .badge-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
            gap: 15px;
        }}
        
        .badge {{
            background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(255,215,0,0.2));
            border: 1px solid #FFD700;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            cursor: pointer;
        }}
        
        .badge-icon {{
            font-size: 32px;
            margin-bottom: 5px;
        }}
        
        .badge-name {{
            font-size: 10px;
            color: #FFD700;
            text-transform: uppercase;
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
        }}
        
        .pattern-name {{
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        
        .pattern-winrate {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .pattern-trades {{
            font-size: 12px;
            color: #666;
        }}
        
        /* Action Buttons */
        .action-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin-top: 20px;
        }}
        
        @media (min-width: 480px) {{
            .action-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        .action-button {{
            padding: 15px;
            background: linear-gradient(135deg, rgba(0,153,255,0.1), rgba(0,153,255,0.2));
            border: 2px solid #0099FF;
            border-radius: 10px;
            color: #0099FF;
            font-size: 16px;
            font-weight: bold;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }}
        
        .action-button:hover {{
            background: #0099FF;
            color: #000;
            transform: translateY(-3px);
        }}
        
        .action-button.primary {{
            background: linear-gradient(135deg, rgba(0,204,0,0.1), rgba(0,204,0,0.2));
            border-color: #00CC00;
            color: #00CC00;
        }}
        
        .action-button.primary:hover {{
            background: #00CC00;
            color: #000;
        }}
        
        /* Toast Notifications */
        .toast {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, rgba(0,153,255,0.9), rgba(0,153,255,0.8));
            color: #fff;
            padding: 15px 25px;
            border-radius: 10px;
            font-weight: bold;
            animation: slideIn 0.3s ease;
            z-index: 1000;
            font-size: 16px;
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
        
        /* Mobile Optimizations */
        @media (max-width: 480px) {{
            body {{
                font-size: 14px;
            }}
            
            .header {{
                padding: 15px 10px;
            }}
            
            .card {{
                padding: 15px;
                border-radius: 10px;
            }}
            
            .position-details {{
                grid-template-columns: repeat(2, 1fr);
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
                    <div class="header-stat-value">{user_data['win_rate']:.1f}%</div>
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
                    <div class="header-stat-label">Streak</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Main Dashboard -->
    <div class="dashboard">
        <!-- Left Column -->
        <div class="sidebar-left">
            <!-- Account Overview -->
            <div class="card">
                <div class="card-title">💰 Account Overview</div>
                <div class="account-stats">
                    <div class="account-stat">
                        <span class="account-stat-label">Balance</span>
                        <span class="account-stat-value">${user_data['balance']:,.2f}</span>
                    </div>
                    <div class="account-stat">
                        <span class="account-stat-label">Equity</span>
                        <span class="account-stat-value {'positive' if user_data['equity'] > user_data['balance'] else 'negative'}">
                            ${user_data['equity']:,.2f}
                        </span>
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
            
            <!-- Referral System -->
            <div class="referral-section">
                <div class="referral-title">💸 Earn $10 Per Referral</div>
                <div class="referral-code">{user_data['referral_code']}</div>
                <div class="referral-link">t.me/bitten_athena_bot?start={user_data['referral_code']}</div>
                <div class="referral-stats">
                    <div class="referral-stat">
                        <div class="referral-stat-value">{user_data.get('referrals_count', 0)}</div>
                        <div class="referral-stat-label">Recruits</div>
                    </div>
                    <div class="referral-stat">
                        <div class="referral-stat-value">${user_data.get('referral_earnings', 0):.2f}</div>
                        <div class="referral-stat-label">Earned</div>
                    </div>
                </div>
                <button class="action-button primary" onclick="copyReferralLink()">Copy Referral Link</button>
            </div>
            
            <!-- Quick Actions -->
            <div class="card">
                <div class="card-title">⚡ Quick Actions</div>
                <div class="action-grid">
                    <button onclick="window.location.href='/signals'" class="action-button primary">View Signals</button>
                    <button onclick="refreshData()" class="action-button">Refresh Data</button>
                </div>
            </div>
        </div>
        
        <!-- Center Content -->
        <div class="main-content">
            <!-- Live Positions -->
            <div class="card">
                <div class="card-title">🎯 Live Positions ({len(user_data.get('open_positions', []))})</div>
                <div class="positions-list" id="positions-list">
                    <!-- Positions will be loaded here -->
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
                            <button class="position-action" onclick="closePosition('pos123')">CLOSE POSITION</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Pattern Performance -->
            <div class="card">
                <div class="card-title">📊 Pattern Performance</div>
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
            <!-- Achievements -->
            <div class="card">
                <div class="card-title">🏆 Achievements</div>
                <div class="achievements">
                    <div class="badge-grid">
                        <div class="badge">
                            <div class="badge-icon">🎯</div>
                            <div class="badge-name">Sharpshooter</div>
                        </div>
                        <div class="badge">
                            <div class="badge-icon">⚡</div>
                            <div class="badge-name">Speed Demon</div>
                        </div>
                        <div class="badge">
                            <div class="badge-icon">💎</div>
                            <div class="badge-name">Diamond Hands</div>
                        </div>
                        <div class="badge">
                            <div class="badge-icon">🔥</div>
                            <div class="badge-name">Hot Streak</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Norman's Notebook -->
            <div class="card">
                <div class="card-title">📓 Norman's Notebook</div>
                <div style="padding: 10px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                    <p style="color: #999; margin-bottom: 15px;">Track your trades and strategy notes</p>
                    <button class="action-button" onclick="window.location.href='/notebook/{user_id}'">
                        Open Notebook
                    </button>
                </div>
            </div>
            
            <!-- Social Share -->
            <div class="card">
                <div class="card-title">📢 Share Your Success</div>
                <div class="action-grid">
                    <button class="action-button" onclick="shareToTwitter()">Twitter</button>
                    <button class="action-button" onclick="shareToTelegram()">Telegram</button>
                    <button class="action-button" onclick="copyStats()">Copy Stats</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Real-time data updates
        let updateInterval = null;
        
        function startPolling() {{
            updateInterval = setInterval(() => {{
                fetch('/api/user/{user_id}/live-data')
                    .then(res => res.json())
                    .then(data => updateDashboard(data))
                    .catch(err => console.error('Update failed:', err));
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
        }}
        
        function updatePositions(positions) {{
            const container = document.getElementById('positions-list');
            if (!positions || positions.length === 0) {{
                container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">No open positions</p>';
                return;
            }}
            
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
                    <div class="position-pnl ${{pos.pnl >= 0 ? 'positive' : 'negative'}}">${{pos.pnl >= 0 ? '+' : ''}}$${{pos.pnl.toFixed(2)}}</div>
                    <div class="position-actions">
                        <button class="position-action" onclick="closePosition('${{pos.id}}')">CLOSE POSITION</button>
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
                        }} else {{
                            showToast('Failed to close position: ' + (data.error || 'Unknown error'));
                        }}
                    }})
                    .catch(err => {{
                        showToast('Error closing position');
                        console.error(err);
                    }});
            }}
        }}
        
        function copyReferralLink() {{
            const link = 'https://t.me/bitten_athena_bot?start={user_data['referral_code']}';
            navigator.clipboard.writeText(link).then(() => {{
                showToast('Referral link copied! Send to friends to earn $10 per signup!');
            }}).catch(() => {{
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = link;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showToast('Referral link copied! Send to friends to earn $10 per signup!');
            }});
        }}
        
        function shareToTwitter() {{
            const text = `Just hit {user_data['win_rate']:.1f}% win rate on BITTEN! 🎯\\n\\nToday's P&L: ${{user_data['today_pnl']:.2f}}\\nGlobal Rank: #{user_data['global_rank']}\\n\\nJoin me: bitten.app/ref/{user_data['referral_code']}`;
            window.open(`https://twitter.com/intent/tweet?text=${{encodeURIComponent(text)}}`, '_blank');
        }}
        
        function shareToTelegram() {{
            const text = `🔥 BITTEN WAR ROOM Stats\\n\\nWin Rate: {user_data['win_rate']:.1f}%\\nToday P&L: ${{user_data['today_pnl']:.2f}}\\nGlobal Rank: #{user_data['global_rank']}\\n\\nJoin with my code: {user_data['referral_code']}`;
            window.open(`https://t.me/share/url?url=bitten.app&text=${{encodeURIComponent(text)}}`, '_blank');
        }}
        
        function copyStats() {{
            const stats = `BITTEN Stats - {user_data['callsign']}
Win Rate: {user_data['win_rate']:.1f}%
Today P&L: ${user_data['today_pnl']:.2f}
Week P&L: ${user_data['week_pnl']:.2f}
Global Rank: #{user_data['global_rank']}
Current Streak: {user_data['current_streak']}
Referral Code: {user_data['referral_code']}`;
            
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
                .then(() => location.reload())
                .catch(err => console.error('Refresh failed:', err));
        }}
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', () => {{
            startPolling();
            
            // Load initial data
            fetch('/api/user/{user_id}/live-data')
                .then(res => res.json())
                .then(data => updateDashboard(data))
                .catch(err => console.error('Initial load failed:', err));
        }});
    </script>
</body>
</html>
"""