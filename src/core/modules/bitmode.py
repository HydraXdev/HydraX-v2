# bitmode.py
# BITTEN Bit Mode - Binary Decision Confirmation System
# Psychological trigger for control/uncertainty interplay

import sys
import os

# Add bitten_core to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'bitten_core'))

from uncertainty_control_system import UncertaintyControlSystem, ControlMode, BitModeDecision
from typing import Dict, Any, Optional

class BitMode:
    """
    Binary decision confirmation system for psychological control manipulation
    
    Forces users into YES/NO choices to create decision anxiety and engagement
    """
    
    def __init__(self):
        self.uncertainty_system = UncertaintyControlSystem()
        self.active = False
        self.pending_confirmation = None
        
    def activate(self, user_id: int = None) -> Dict[str, Any]:
        """Activate Bit Mode for binary decision making"""
        result = self.uncertainty_system.set_control_mode(ControlMode.BIT_MODE, user_id)
        self.active = True
        
        return {
            'success': True,
            'message': "🤖 BIT MODE ACTIVATED\n\nBit will now require YES/NO confirmation for all trading decisions.\nThis ensures precision but demands decisiveness.",
            'psychological_note': result['response'],
            'mode': 'bit_mode'
        }
    
    def deactivate(self, user_id: int = None) -> Dict[str, Any]:
        """Deactivate Bit Mode and return to full control"""
        result = self.uncertainty_system.set_control_mode(ControlMode.FULL_CONTROL, user_id)
        self.active = False
        self.pending_confirmation = None
        
        return {
            'success': True,
            'message': "🎯 FULL CONTROL RESTORED\n\nBit will execute decisions automatically.\nYou have resumed complete command authority.",
            'psychological_note': result['response'],
            'mode': 'full_control'
        }
    
    def request_confirmation(self, context: str, trade_data: Dict[str, Any]) -> BitModeDecision:
        """Request binary confirmation for trading decision"""
        if not self.active:
            return None
        
        # Generate context-specific question
        decision = self.uncertainty_system.activate_bit_mode(context, self._generate_question(context, trade_data))
        self.pending_confirmation = decision
        
        return decision
    
    def process_confirmation(self, decision_id: str, choice: bool, user_id: int = None) -> Dict[str, Any]:
        """Process user's YES/NO confirmation"""
        result = self.uncertainty_system.process_bit_decision(decision_id, choice, user_id)
        
        if result['success']:
            self.pending_confirmation = None
            
            # Generate Bit's response based on choice and consequences
            bit_response = self._generate_bit_response(choice, result)
            result['bit_response'] = bit_response
        
        return result
    
    def _generate_question(self, context: str, trade_data: Dict[str, Any]) -> str:
        """Generate appropriate confirmation question"""
        symbol = trade_data.get('symbol', 'UNKNOWN')
        direction = trade_data.get('direction', 'UNKNOWN')
        
        questions = {
            'trade_entry': [
                f"🎯 {symbol} {direction} signal detected. Execute trade?",
                f"🔥 Bit sees {symbol} opportunity. Fire now?",
                f"⚡ {symbol} entry conditions met. Proceed with {direction}?",
                f"🎪 {symbol} {direction} setup confirmed. Your command?"
            ],
            'trade_exit': [
                f"💰 {symbol} target approaching. Close position?",
                f"⏰ {symbol} exit signal triggered. Take profit?",
                f"🛡️ {symbol} risk increasing. Exit now?",
                f"🎯 {symbol} completion detected. Secure gains?"
            ],
            'risk_adjustment': [
                f"⚠️ {symbol} volatility spike. Reduce position?",
                f"🚨 {symbol} risk threshold reached. Scale down?",
                f"🛑 {symbol} showing danger signs. Adjust exposure?",
                f"⚡ {symbol} conditions changed. Modify risk?"
            ]
        }
        
        import secrets
        context_questions = questions.get(context, questions['trade_entry'])
        return secrets.choice(context_questions)
    
    def _generate_bit_response(self, choice: bool, result: Dict[str, Any]) -> str:
        """Generate Bit's psychological response to user choice"""
        if choice:  # YES
            positive_responses = [
                "🎯 **CONFIRMED.** Bit executes with precision.",
                "⚡ **DECISIVENESS NOTED.** Bit approves your resolve.",
                "🔥 **COMMAND ACKNOWLEDGED.** Bit strikes without hesitation.",
                "💪 **BOLD CHOICE.** Bit respects your conviction.",
                "🎪 **EXCELLENT.** Bit admires your decisiveness."
            ]
            import secrets
            return secrets.choice(positive_responses)
        else:  # NO
            negative_responses = [
                "🛑 **HALT CONFIRMED.** Bit questions your timing.",
                "⏸️ **RESTRAINT NOTED.** Bit wonders about missed opportunity.",
                "🤔 **HESITATION DETECTED.** Bit analyzes your caution.",
                "⚠️ **DENIED.** Bit stores this hesitation pattern.",
                "🎭 **INTERESTING.** Bit notes your risk aversion."
            ]
            import secrets
            return secrets.choice(negative_responses)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Bit Mode status"""
        status = {
            'active': self.active,
            'pending_confirmation': self.pending_confirmation is not None,
            'system_status': self.uncertainty_system.get_system_status()
        }
        
        if self.pending_confirmation:
            status['pending_decision'] = {
                'id': self.pending_confirmation.decision_id,
                'question': self.pending_confirmation.question,
                'context': self.pending_confirmation.context,
                'timestamp': self.pending_confirmation.timestamp.isoformat() if self.pending_confirmation.timestamp else None
            }
        
        return status

def run_bitmode():
    """Legacy function for backwards compatibility"""
    bit_mode = BitMode()
    print("🤖 BITTEN Bit Mode: Binary decision system initialized.")
    print("Use activate() to enable YES/NO confirmation mode.")
    print("Psychological control interplay ready.")
    return bit_mode

if __name__ == "__main__":
    bit_mode = run_bitmode()
    
    # Demo mode
    print("\n--- BIT MODE DEMO ---")
    print("Activating Bit Mode...")
    result = bit_mode.activate()
    print(f"Result: {result['message']}")
    
    # Simulate trade confirmation request
    print("\nSimulating trade confirmation...")
    trade_data = {'symbol': 'EURUSD', 'direction': 'BUY'}
    decision = bit_mode.request_confirmation('trade_entry', trade_data)
    
    if decision:
        print(f"Decision ID: {decision.decision_id}")
        print(f"Question: {decision.question}")
        print(f"Context: {decision.context}")
        
        # Simulate user choice (YES)
        print("\nSimulating YES response...")
        confirmation_result = bit_mode.process_confirmation(decision.decision_id, True)
        print(f"Bit Response: {confirmation_result.get('bit_response', 'No response')}")
    
    print("\nBit Mode demo complete.")
