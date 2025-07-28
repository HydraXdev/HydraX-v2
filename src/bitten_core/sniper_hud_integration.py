# sniper_hud_integration.py
# Example integration showing how to use the Sniper HUD system

import asyncio
import time
from flask import Flask
from .telegram_router import TelegramRouter
from .signal_alerts import SignalAlert, SignalAlertSystem
from .hud_router import HUDRouter
from .user_profile import UserProfileManager

class SniperHUDIntegration:
    """Integration example for the complete Sniper HUD system"""
    
    def __init__(self, bot_token: str, webapp_domain: str):
        # Initialize Flask app
        self.app = Flask(__name__)
        
        # HUD WebApp URL
        self.hud_webapp_url = f"{webapp_domain}/sniper_hud/hud_interface.html"
        
        # Initialize components
        self.telegram_router = TelegramRouter(
            bitten_core=None,  # Your trading system
            hud_webapp_url=self.hud_webapp_url
        )
        
        self.signal_alert_system = SignalAlertSystem(
            bot_token=bot_token,
            hud_webapp_url=self.hud_webapp_url
        )
        
        self.hud_router = HUDRouter(
            app=self.app,
            bot_token=bot_token
        )
        
        self.profile_manager = UserProfileManager()
    
    async def send_trading_signal(self, symbol: str, direction: str, 
                                confidence: float, urgency: str,
                                entry_price: float, stop_loss: float, 
                                take_profit: float, strategy_info: Dict):
        """Send a trading signal to users"""
        
        # Create signal alert
        signal = SignalAlert(
            signal_id=f"SIG-{int(time.time())}",
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            urgency=urgency,
            timestamp=int(time.time()),
            expires_at=int(time.time()) + 300  # 5 minutes
        )
        
        # Add full signal data to HUD router
        signal_data = {
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'urgency': urgency,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'strategy': strategy_info
        }
        
        signal_id = self.hud_router.add_signal(signal_data)
        signal.signal_id = signal_id
        
        # Get target users based on tier
        target_users = self._get_eligible_users(urgency)
        
        # Send alerts
        results = await self.signal_alert_system.send_batch_alerts(
            signal, 
            target_users
        )
        
        print(f"Signal sent: {results['sent']} successful, "
              f"{results['failed']} failed, {results['tier_blocked']} tier-blocked")
        
        return signal_id
    
    def _get_eligible_users(self, urgency: str) -> List[Dict]:
        """Get users eligible for signal based on urgency"""
        # This would query your user database
        # For example:
        tier_requirements = {
            'MEDIUM': ['USER', 'AUTHORIZED', 'ELITE', 'ADMIN'],
            'HIGH': ['AUTHORIZED', 'ELITE', 'ADMIN'],
            'CRITICAL': ['ELITE', 'ADMIN']
        }
        
        eligible_tiers = tier_requirements.get(urgency, [])
        
        # Mock data - replace with actual database query
        users = [
            {'user_id': 123456, 'tier': 'ELITE'},
            {'user_id': 789012, 'tier': 'AUTHORIZED'},
            {'user_id': 345678, 'tier': 'USER'}]
        
        return [u for u in users if u['tier'] in eligible_tiers]
    
    def handle_telegram_command(self, update_data: Dict):
        """Handle incoming Telegram command"""
        # Parse update
        update = self.telegram_router.parse_telegram_update(update_data)
        if not update:
            return None
        
        # Process command
        result = self.telegram_router.process_command(update)
        
        # If result has reply_markup (WebApp buttons), send via bot API
        if result.data and 'reply_markup' in result.data:
            # Send message with markup via Telegram Bot API
            # This would use your bot's send_message method
            pass
        
        return result
    
    def run_webapp(self, host='0.0.0.0', port=5000):
        """Run the Flask webapp for HUD"""
        # Serve static files for HUD
        @self.app.route('/sniper_hud/<path:filename>')
        def serve_hud_files(filename):
            return send_from_directory('ui/sniper_hud', filename)
        
        # Start Flask app
        self.app.run(host=host, port=port)
    
    async def cleanup_expired_signals(self):
        """Periodic cleanup of expired signals"""
        while True:
            # Clean up HUD router signals
            hud_expired = self.hud_router.cleanup_expired_signals()
            
            # Clean up alert system signals
            alert_expired = await self.signal_alert_system.cleanup_expired_signals()
            
            print(f"Cleaned up {hud_expired + alert_expired} expired signals")
            
            # Run every minute
            await asyncio.sleep(60)

# Example usage
if __name__ == "__main__":
    # Initialize system
    integration = SniperHUDIntegration(
        bot_token="YOUR_BOT_TOKEN",
        webapp_domain="https://your-domain.com"
    )
    
    # Example: Send a signal
    async def send_example_signal():
        await integration.send_trading_signal(
            symbol="EURUSD",
            direction="BUY",
            confidence=0.85,
            urgency="HIGH",
            entry_price=1.0850,
            stop_loss=1.0830,
            take_profit=1.0890,
            strategy_info={
                'type': 'LONDON_BREAKOUT',
                'pattern': 'Bullish breakout',
                'timeframe': 'H1',
                'strength': 'Strong',
                'conditions': [
                    {'text': 'Above key resistance', 'favorable': True},
                    {'text': 'Strong momentum', 'favorable': True},
                    {'text': 'Volume confirmation', 'favorable': True}
                ]
            }
        )
    
    # Run example
    asyncio.run(send_example_signal())