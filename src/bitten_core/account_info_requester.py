#!/usr/bin/env python3
"""
Account Info Requester - Get account balance via MT5 EA handshake
Uses the 3-channel architecture: Data, Trade Commands, Trade Confirmations
"""

import os
import json
import time
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def get_user_account_info(user_id: str, timeout: float = 5.0) -> Dict:
    """
    Request account info via EA handshake - 3-channel architecture
    
    This sends a special ACCOUNT_INFO command to the EA and waits for
    the response containing balance, equity, and connection verification.
    
    Returns:
        Dict with account info or error details
    """
    return _ea_handshake_implementation(user_id, timeout)

# EA handshake implementation - NOW ACTIVE:
def _ea_handshake_implementation(user_id: str, timeout: float = 5.0) -> Dict:
    """
    Future implementation - EA handshake for account verification
    """
    mt5_files_path = "/root/HydraX-v2/mt5_files"
    os.makedirs(mt5_files_path, exist_ok=True)
    
    instruction_file = os.path.join(mt5_files_path, "bitten_instructions.txt")
    result_file = os.path.join(mt5_files_path, "bitten_results.txt")
    
    try:
        # Generate unique request ID
        request_id = f"ACCOUNT_INFO_{int(time.time() * 1000)}"
        
        # Create account info request command
        # Format: REQUEST_ID,ACCOUNT_INFO,USER_ID
        command = f"{request_id},ACCOUNT_INFO,{user_id}"
        
        # Write instruction file
        with open(instruction_file, 'w') as f:
            f.write(command)
        
        logger.info(f"EA handshake sent: {request_id}")
        
        # Wait for result with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r') as f:
                        content = f.read().strip()
                    
                    if content:
                        result = json.loads(content)
                        
                        # Check if this is our response
                        if result.get('id') == request_id:
                            # Delete result file
                            os.remove(result_file)
                            
                            # Return account info
                            account = result.get('account', {})
                            return {
                                'success': True,
                                'user_id': user_id,
                                'balance': float(account.get('balance', 0)),
                                'equity': float(account.get('equity', 0)),
                                'margin': float(account.get('margin', 0)),
                                'free_margin': float(account.get('free_margin', 0)),
                                'currency': account.get('currency', 'USD'),
                                'leverage': int(account.get('leverage', 500)),
                                'login': account.get('login', ''),
                                'broker': account.get('broker', ''),
                                'timestamp': result.get('timestamp', datetime.now().isoformat()),
                                'connected': True,
                                'handshake_verified': True
                            }
                
                except (json.JSONDecodeError, Exception) as e:
                    logger.error(f"Error parsing EA response: {e}")
            
            time.sleep(0.1)  # Brief sleep to avoid busy waiting
        
        # Timeout
        return {
            'success': False,
            'error': 'EA handshake timeout - no response from MT5 terminal',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'EA handshake error: {str(e)}',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }