#!/usr/bin/env python3
"""
Mission Fire Integration - Connects mission briefings to TOC firing system
"""

import requests
import json
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MissionFireIntegration:
    """Handles firing missions through the TOC system"""
    
    def __init__(self, toc_url: str = "http://localhost:5000"):
        self.toc_url = toc_url
        self.session = requests.Session()
        self.session.timeout = 30
    
    def fire_mission(self, mission_briefing, user_id: str) -> Dict:
        """
        Fire a mission through the TOC system
        
        This converts a mission briefing back to signal format
        and sends it to TOC for RR calculation and execution
        """
        try:
            # Convert mission briefing back to signal format
            apex_signal = self._convert_mission_to_apex_signal(mission_briefing)
            
            # Prepare TOC fire request
            fire_request = {
                "user_id": user_id,
                "signal": apex_signal
            }
            
            logger.info(f"🔥 Firing mission {mission_briefing.mission_id} for user {user_id}")
            logger.info(f"📊 Signal: {apex_signal['symbol']} {apex_signal['direction']} TCS:{apex_signal['tcs']}")
            
            # Send to TOC for execution
            response = self.session.post(
                f"{self.toc_url}/fire",
                json=fire_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                logger.info(f"✅ Mission fired successfully: {result.get('message', 'Success')}")
                
                return {
                    'success': True,
                    'message': 'Mission fired successfully',
                    'mission_id': mission_briefing.mission_id,
                    'toc_response': result,
                    'signal_enhanced': result.get('signal_enhanced'),
                    'rr_calculation': result.get('rr_calculation')
                }
            else:
                error_msg = response.json().get('error', 'Unknown error') if response.text else 'Connection failed'
                logger.error(f"❌ Mission fire failed: {error_msg}")
                
                return {
                    'success': False,
                    'message': f'Fire failed: {error_msg}',
                    'mission_id': mission_briefing.mission_id,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ TOC connection error: {e}")
            return {
                'success': False,
                'message': f'TOC connection error: {str(e)}',
                'mission_id': mission_briefing.mission_id
            }
        except Exception as e:
            logger.error(f"❌ Mission fire error: {e}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'mission_id': mission_briefing.mission_id
            }
    
    def _convert_mission_to_apex_signal(self, mission_briefing) -> Dict:
        """Convert mission briefing back to signal format for TOC"""
        
        # Extract the core signal data from mission briefing
        signal = {
            'symbol': mission_briefing.symbol,
            'direction': mission_briefing.direction,
            'entry_price': mission_briefing.entry_price,
            'signal_type': mission_briefing.signal_class.value,
            'tcs': mission_briefing.tcs_score,
            'volume': mission_briefing.position_size,
            'comment': f"BITTEN Mission {mission_briefing.mission_id}",
            'pattern': mission_briefing.pattern_name,
            'timeframe': mission_briefing.timeframe,
            'session': mission_briefing.session,
            'mission_id': mission_briefing.mission_id,
            'timestamp': datetime.now().isoformat()
        }
        
        return signal
    
    def check_toc_health(self) -> Dict:
        """Check if TOC server is available"""
        try:
            response = self.session.get(f"{self.toc_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                return {
                    'available': True,
                    'status': health_data.get('status', 'unknown'),
                    'architecture': health_data.get('components', {}).get('architecture', 'unknown')
                }
            else:
                return {
                    'available': False,
                    'error': f'HTTP {response.status_code}'
                }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_user_clone_status(self, user_id: str) -> Dict:
        """Get user's clone status from TOC"""
        try:
            response = self.session.get(f"{self.toc_url}/status/{user_id}")
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}
    
    def assign_user_clone(self, user_id: str, broker_type: str = "demo") -> Dict:
        """Assign a clone to user if they don't have one"""
        try:
            request_data = {
                'user_id': user_id,
                'broker_type': broker_type
            }
            
            response = self.session.post(
                f"{self.toc_url}/assign-terminal",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get('error', 'Unknown error') if response.text else 'Connection failed'
                return {'error': error_msg}
                
        except Exception as e:
            return {'error': str(e)}

def create_mission_fire_integration(toc_url: str = "http://localhost:5000") -> MissionFireIntegration:
    """Factory function to create mission fire integration"""
    return MissionFireIntegration(toc_url)

# Example usage function
def fire_mission_example():
    """Example of how to fire a mission"""
    from mission_briefing_generator_active import v5MissionBriefingGenerator
    
    # Generate a sample mission
    generator = v5MissionBriefingGenerator()
    
    signal_data = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0900,
        'signal_type': 'RAPID_ASSAULT',
        'tcs': 75,
        'pattern': 'Pattern',
        'timeframe': 'M5',
        'session': 'LONDON'
    }
    
    user_data = {'tier': 'FANG'}
    account_data = {'balance': 10000.0}
    
    # Generate mission briefing
    briefing = generator.generate_v5_mission_briefing(signal_data, user_data, account_data)
    
    # Create fire integration
    fire_integration = create_mission_fire_integration()
    
    # Check TOC health
    health = fire_integration.check_toc_health()
    print(f"TOC Health: {health}")
    
    # Fire the mission
    if health.get('available'):
        result = fire_integration.fire_mission(briefing, "test_user")
        print(f"Fire Result: {result}")
    else:
        print("TOC not available")

if __name__ == "__main__":
    fire_mission_example()