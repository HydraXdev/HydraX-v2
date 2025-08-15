#!/usr/bin/env python3
"""
Add /positions command to Telegram bot
Shows users their live positions, P&L, and trade history
"""

def add_positions_command(bot):
    """Add /positions command to telegram bot"""
    
    @bot.message_handler(commands=['positions', 'trades', 'pnl'])
    def show_positions(message):
        """Show user's current positions and P&L"""
        
        user_id = str(message.from_user.id)
        
        try:
            from trade_history_tracker import TradeHistoryTracker
            tracker = TradeHistoryTracker()
            
            # Get positions and stats
            positions = tracker.get_user_positions(user_id)
            stats = tracker.get_user_statistics(user_id)
            
            # Format response
            response = ["📊 **YOUR TRADING DASHBOARD**\n"]
            
            # Overall stats
            response.append(f"**Overall Performance:**")
            response.append(f"• Win Rate: {stats['win_rate']:.1f}%")
            response.append(f"• Total P&L: {stats['total_pips']:.1f} pips")
            response.append(f"• Current Streak: {stats['current_streak']} wins")
            response.append(f"• Total Trades: {stats['total_trades']}\n")
            
            # Open positions
            if positions['open']:
                response.append("**📈 OPEN POSITIONS:**")
                for pos in positions['open']:
                    pnl_emoji = "🟢" if pos.get('current_pnl', 0) > 0 else "🔴"
                    response.append(f"""
{pnl_emoji} **{pos['symbol']}** {pos['direction']}
• Entry: {pos['entry_price']:.5f}
• Current: {pos.get('current_price', 0):.5f}
• P&L: {pos.get('current_pips', 0):.1f} pips (${pos.get('current_pnl', 0):.2f})
• SL: {pos['sl']:.5f} | TP: {pos['tp']:.5f}
""")
            else:
                response.append("**No open positions**\n")
            
            # Recent closed trades
            if positions['closed'][:3]:
                response.append("**📝 RECENT CLOSED:**")
                for pos in positions['closed'][:3]:
                    outcome_emoji = "✅" if pos['outcome'] == 'TP_HIT' else "❌"
                    response.append(f"""
{outcome_emoji} **{pos['symbol']}** {pos['direction']}
• Result: {pos.get('pips_result', 0):.1f} pips (${pos.get('final_pnl', 0):.2f})
• Outcome: {pos['outcome']}
""")
            
            # Quick actions
            response.append("\n**Quick Actions:**")
            response.append("🎯 /fire {signal_id} - Execute a signal")
            response.append("📊 /me - Full War Room dashboard")
            response.append("🔄 /positions - Refresh this view")
            
            bot.reply_to(message, "\n".join(response), parse_mode='Markdown')
            
        except Exception as e:
            bot.reply_to(message, f"Error loading positions: {e}")
    
    return bot

# Function to integrate with existing bot
def integrate_positions_command(bot_instance):
    """Integrate positions command with existing telegram bot"""
    return add_positions_command(bot_instance)