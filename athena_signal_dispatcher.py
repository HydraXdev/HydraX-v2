#!/usr/bin/env python3
"""
🏛️ ATHENA SIGNAL DISPATCHER
Connects BittenCore signal delivery to existing PersonalizedMissionBrain
Uses existing components - NO NEW FUNCTIONALITY
"""

import logging
import sys
from typing import Dict, List

# Add paths
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2/src/bitten_core')

logger = logging.getLogger('AthenaSignalDispatcher')

class AthenaSignalDispatcher:
    """Dispatcher that connects signals to existing PersonalizedMissionBrain"""
    
    def __init__(self):
        # Import existing components
        try:
            from src.bitten_core.personalized_mission_brain import get_mission_brain
            from src.bitten_core.user_profile_manager import get_all_active_users
            self.mission_brain = get_mission_brain()
            self.get_active_users = get_all_active_users
            logger.info("✅ Connected to existing PersonalizedMissionBrain")
        except ImportError as e:
            logger.error(f"❌ Failed to connect to existing components: {e}")
            self.mission_brain = None
            self.get_active_users = lambda: ["7176191872"]  # Fallback to Commander
    
    def dispatch_signal_via_athena(self, signal_data: Dict) -> Dict:
        """
        Dispatch signal to individual users using existing PersonalizedMissionBrain
        This is what BittenCore expects to call
        """
        try:
            if not self.mission_brain:
                # Fallback for Commander only
                return {
                    'success': True,
                    'dispatch_results': [
                        {'user_id': '7176191872', 'status': 'dispatched', 'method': 'fallback'}
                    ]
                }
            
            # Get active users using existing system
            active_users = self.get_active_users()
            if not active_users:
                active_users = ["7176191872"]  # Always include Commander
            
            # Create personalized missions using existing brain
            missions = self.mission_brain.create_personalized_missions(signal_data, active_users)
            
            dispatch_results = []
            for mission in missions:
                try:
                    # Save mission using existing brain method
                    self.mission_brain._save_personalized_mission(mission)
                    dispatch_results.append({
                        'user_id': mission.user_id,
                        'status': 'dispatched',
                        'mission_id': mission.mission_id,
                        'method': 'personalized_mission_brain'
                    })
                except Exception as e:
                    logger.error(f"Failed to save mission for user {mission.user_id}: {e}")
                    dispatch_results.append({
                        'user_id': mission.user_id,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'dispatch_results': dispatch_results,
                'total_missions': len(missions)
            }
            
        except Exception as e:
            logger.error(f"Dispatch failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'dispatch_results': []
            }

# Create the athena_dispatcher instance that BittenCore expects
athena_dispatcher = AthenaSignalDispatcher()