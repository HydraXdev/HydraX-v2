"""
WebApp Integration for NIBBLER Tactical Strategies
Provides API endpoints and UI components for tactical strategy management
"""

from flask import jsonify, request, render_template_string
from typing import Dict, Any
from .tactical_strategies import tactical_strategy_manager, TacticalStrategy
from .xp_economy import XPEconomy

class WebAppTacticalIntegration:
    """WebApp integration for tactical strategies"""
    
    def __init__(self, xp_economy: XPEconomy):
        self.xp_economy = xp_economy
        self.tactical_manager = tactical_strategy_manager
    
    def get_tactical_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get complete tactical dashboard data for user"""
        
        # Get user XP and unlocked strategies
        user_balance = self.xp_economy.get_user_balance(user_id)
        unlocked_strategies = self.tactical_manager.get_unlocked_strategies(user_balance.current_balance)
        
        # Get daily state
        daily_state = self.tactical_manager.get_daily_state(user_id)
        
        # Get strategy performance stats
        strategy_stats = {}
        for strategy in unlocked_strategies:
            strategy_stats[strategy.value] = self.tactical_manager.get_strategy_stats(user_id, strategy)
        
        # Get unlock progress
        unlock_status = self.xp_economy.get_tactical_unlock_status(user_id)
        
        return {
            "user_xp": user_balance.current_balance,
            "unlocked_strategies": [s.value for s in unlocked_strategies],
            "daily_state": {
                "selected_strategy": daily_state.selected_strategy.value if daily_state.selected_strategy else None,
                "shots_fired": daily_state.shots_fired,
                "wins_today": daily_state.wins_today,
                "losses_today": daily_state.losses_today,
                "daily_pnl": daily_state.daily_pnl,
                "locked_until": daily_state.locked_until.isoformat() if daily_state.locked_until else None,
                "max_shots": self.tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy].max_shots if daily_state.selected_strategy else 0
            },
            "strategy_stats": strategy_stats,
            "unlock_progress": unlock_status,
            "strategy_configs": {
                strategy.value: {
                    "display_name": config.display_name,
                    "description": config.description,
                    "max_shots": config.max_shots,
                    "daily_potential": config.daily_potential,
                    "psychology": config.psychology,
                    "unlock_xp": config.unlock_xp
                }
                for strategy, config in self.tactical_manager.TACTICAL_CONFIGS.items()
            }
        }
    
    def get_signal_display_data(self, user_id: str, all_signals: list) -> Dict[str, Any]:
        """Get signal display data with tactical filtering"""
        
        daily_state = self.tactical_manager.get_daily_state(user_id)
        
        if not daily_state.selected_strategy:
            return {
                "error": "No tactical strategy selected",
                "signals": [],
                "strategy_info": None
            }
        
        config = self.tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy]
        
        # Process each signal for tactical eligibility
        processed_signals = []
        for signal in all_signals:
            can_fire, reason, shot_info = self.tactical_manager.can_fire_shot(
                user_id,
                signal.get('tcs', 0),
                signal.get('direction', '')
            )
            
            processed_signals.append({
                "pair": signal.get('pair', ''),
                "direction": signal.get('direction', ''),
                "tcs": signal.get('tcs', 0),
                "entry_price": signal.get('entry_price', 0),
                "can_fire": can_fire,
                "fire_reason": reason,
                "shot_info": shot_info,
                "signal_id": signal.get('signal_id', '')
            })
        
        return {
            "strategy_info": {
                "name": config.display_name,
                "description": config.description,
                "shots_remaining": config.max_shots - daily_state.shots_fired,
                "total_shots": config.max_shots,
                "wins_today": daily_state.wins_today,
                "losses_today": daily_state.losses_today,
                "daily_pnl": daily_state.daily_pnl,
                "psychology": config.psychology
            },
            "signals": processed_signals,
            "stop_conditions": self.tactical_manager._check_stop_conditions(daily_state, config)
        }
    
    def execute_tactical_shot(self, user_id: str, signal_data: Dict, trade_result: str) -> Dict[str, Any]:
        """Execute a tactical shot and update state"""
        
        try:
            result = self.tactical_manager.fire_shot(user_id, signal_data, trade_result)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def select_daily_strategy_api(self, user_id: str, strategy_name: str) -> Dict[str, Any]:
        """API endpoint for strategy selection"""
        
        try:
            strategy = TacticalStrategy(strategy_name)
        except ValueError:
            return {"success": False, "error": "Invalid strategy"}
        
        user_balance = self.xp_economy.get_user_balance(user_id)
        success, message = self.tactical_manager.select_daily_strategy(
            user_id, strategy, user_balance.current_balance
        )
        
        return {
            "success": success,
            "message": message,
            "dashboard_data": self.get_tactical_dashboard_data(user_id) if success else None
        }

def get_tactical_dashboard_html() -> str:
    """Generate HTML for tactical dashboard component"""
    
    return """
    <div class="tactical-dashboard" id="tacticalDashboard">
        <!-- Strategy Selection Panel -->
        <div class="strategy-selection-panel" v-if="!dailyState.locked_until">
            <h3>🎯 Select Today's Tactical Strategy</h3>
            <div class="strategy-cards">
                <div v-for="strategy in unlockedStrategies" 
                     :key="strategy" 
                     class="strategy-card"
                     :class="{ 'selected': dailyState.selected_strategy === strategy }"
                     @click="selectStrategy(strategy)">
                    
                    <div class="strategy-header">
                        <h4>{{ strategyConfigs[strategy].display_name }}</h4>
                        <span class="unlock-badge" v-if="strategyConfigs[strategy].unlock_xp > 0">
                            {{ strategyConfigs[strategy].unlock_xp }} XP
                        </span>
                    </div>
                    
                    <p class="strategy-description">
                        {{ strategyConfigs[strategy].description }}
                    </p>
                    
                    <div class="strategy-stats">
                        <div class="stat-item">
                            <label>Max Shots:</label>
                            <span>{{ strategyConfigs[strategy].max_shots }}</span>
                        </div>
                        <div class="stat-item">
                            <label>Daily Potential:</label>
                            <span>{{ strategyConfigs[strategy].daily_potential }}</span>
                        </div>
                        <div class="stat-item" v-if="strategyStats[strategy]">
                            <label>Your Win Rate:</label>
                            <span>{{ strategyStats[strategy].win_rate.toFixed(1) }}%</span>
                        </div>
                    </div>
                    
                    <div class="strategy-psychology">
                        <em>"{{ strategyConfigs[strategy].psychology }}"</em>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Current Strategy Status -->
        <div class="current-strategy-panel" v-if="dailyState.selected_strategy">
            <h3>{{ strategyConfigs[dailyState.selected_strategy].display_name }} Active</h3>
            
            <div class="strategy-status">
                <div class="status-item">
                    <label>Shots Fired:</label>
                    <span class="shots-progress">
                        {{ dailyState.shots_fired }} / {{ dailyState.max_shots }}
                    </span>
                    <div class="progress-bar">
                        <div class="progress-fill" 
                             :style="{ width: (dailyState.shots_fired / dailyState.max_shots * 100) + '%' }">
                        </div>
                    </div>
                </div>
                
                <div class="status-item">
                    <label>Performance:</label>
                    <span class="performance-stats">
                        {{ dailyState.wins_today }}W - {{ dailyState.losses_today }}L
                    </span>
                </div>
                
                <div class="status-item">
                    <label>Daily P&L:</label>
                    <span class="pnl" :class="{ 'positive': dailyState.daily_pnl > 0, 'negative': dailyState.daily_pnl < 0 }">
                        {{ dailyState.daily_pnl > 0 ? '+' : '' }}{{ dailyState.daily_pnl.toFixed(2) }}%
                    </span>
                </div>
            </div>
            
            <div class="strategy-locked" v-if="dailyState.locked_until">
                <p>🔒 Strategy locked until midnight</p>
                <p class="lock-timer">{{ getLockTimeRemaining() }}</p>
            </div>
        </div>
        
        <!-- XP Progress Panel -->
        <div class="xp-progress-panel">
            <h4>🏆 Tactical Progression</h4>
            
            <div class="xp-current">
                <span class="xp-amount">{{ userXp.toLocaleString() }} XP</span>
                <span class="unlocked-count">{{ unlockProgress.unlocked_count }}/4 tactics unlocked</span>
            </div>
            
            <div class="next-unlock" v-if="unlockProgress.next_unlock">
                <label>Next Unlock:</label>
                <span class="next-strategy">{{ unlockProgress.next_unlock.display_name }}</span>
                <div class="xp-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" 
                             :style="{ width: unlockProgress.progress_percentage + '%' }">
                        </div>
                    </div>
                    <span class="progress-text">
                        {{ unlockProgress.next_unlock.xp_needed }} XP needed
                    </span>
                </div>
            </div>
        </div>
    </div>
    
    <style>
    .tactical-dashboard {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    
    .strategy-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    
    .strategy-card {
        border: 2px solid #333;
        border-radius: 10px;
        padding: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #1e1e1e, #2a2a2a);
    }
    
    .strategy-card:hover {
        border-color: #00ff88;
        transform: translateY(-2px);
    }
    
    .strategy-card.selected {
        border-color: #00ff88;
        background: linear-gradient(135deg, #1e3a1e, #2a4a2a);
    }
    
    .strategy-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .unlock-badge {
        background: #00ff88;
        color: black;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .strategy-stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 15px 0;
    }
    
    .stat-item {
        display: flex;
        justify-content: space-between;
    }
    
    .strategy-psychology {
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #444;
        font-style: italic;
        color: #aaa;
    }
    
    .current-strategy-panel {
        background: linear-gradient(135deg, #2a2a2a, #1e1e1e);
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .shots-progress {
        font-weight: bold;
        color: #00ff88;
    }
    
    .progress-bar {
        width: 100%;
        height: 8px;
        background: #333;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 5px;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #00ff88, #00cc66);
        transition: width 0.3s ease;
    }
    
    .pnl.positive {
        color: #00ff88;
    }
    
    .pnl.negative {
        color: #ff4444;
    }
    
    .strategy-locked {
        background: #444;
        border-radius: 5px;
        padding: 10px;
        margin-top: 15px;
        text-align: center;
    }
    
    .xp-progress-panel {
        background: linear-gradient(135deg, #1e1e3a, #2a2a4a);
        border-radius: 10px;
        padding: 20px;
    }
    
    .xp-current {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .xp-amount {
        font-size: 24px;
        font-weight: bold;
        color: #00ff88;
    }
    </style>
    """

def register_webapp_tactical_routes(app, xp_economy):
    """Register tactical strategy routes with Flask app"""
    
    integration = WebAppTacticalIntegration(xp_economy)
    
    @app.route('/api/tactical/dashboard/<user_id>')
    def get_tactical_dashboard(user_id):
        """Get tactical dashboard data"""
        try:
            data = integration.get_tactical_dashboard_data(user_id)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/tactical/select_strategy', methods=['POST'])
    def select_daily_strategy():
        """Select daily strategy"""
        try:
            data = request.json
            user_id = data.get('user_id')
            strategy = data.get('strategy')
            
            result = integration.select_daily_strategy_api(user_id, strategy)
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/tactical/signals/<user_id>')
    def get_tactical_signals(user_id):
        """Get signals with tactical filtering"""
        try:
            # This would get signals from your signal provider
            all_signals = []  # Replace with actual signal source
            
            data = integration.get_signal_display_data(user_id, all_signals)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/tactical/fire_shot', methods=['POST'])
    def fire_tactical_shot():
        """Execute a tactical shot"""
        try:
            data = request.json
            user_id = data.get('user_id')
            signal_data = data.get('signal_data')
            trade_result = data.get('trade_result')  # 'WIN' or 'LOSS'
            
            result = integration.execute_tactical_shot(user_id, signal_data, trade_result)
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500