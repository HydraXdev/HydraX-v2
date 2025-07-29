#!/usr/bin/env python3
"""
ML Retrain Manager - Automated model retraining system
Monitors truth_log.jsonl for new entries and triggers retraining when thresholds are met
"""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, Any
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLRetrainManager:
    """Manages automated ML model retraining based on new data"""
    
    def __init__(self, 
                 truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl",
                 model_path: str = "/root/HydraX-v2/model.pkl",
                 train_script_path: str = "/root/HydraX-v2/train_model.py",
                 status_path: str = "/root/HydraX-v2/ml_status.json"):
        
        self.truth_log_path = Path(truth_log_path)
        self.model_path = Path(model_path)
        self.train_script_path = Path(train_script_path)
        self.status_path = Path(status_path)
        
        # Retrain thresholds
        self.entry_threshold = 100  # New entries required for retrain
        self.time_threshold_days = 7  # Days since last retrain
        
        logger.info("ML Retrain Manager initialized")
    
    def load_status(self) -> Dict[str, Any]:
        """Load ML status from file"""
        try:
            if self.status_path.exists():
                with open(self.status_path, 'r') as f:
                    return json.load(f)
            else:
                # Initialize default status
                return {
                    "last_retrain": None,
                    "entry_count": 0,
                    "model_accuracy": 0.0,
                    "last_check_hash": "",
                    "total_retrains": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
        except Exception as e:
            logger.error(f"Error loading ML status: {e}")
            return {
                "last_retrain": None,
                "entry_count": 0,
                "model_accuracy": 0.0,
                "last_check_hash": "",
                "total_retrains": 0,
                "error": str(e)
            }
    
    def save_status(self, status: Dict[str, Any]) -> bool:
        """Save ML status to file"""
        try:
            # Ensure directory exists
            self.status_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add updated timestamp
            status['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Save with pretty formatting
            with open(self.status_path, 'w') as f:
                json.dump(status, f, indent=2, sort_keys=True)
            
            logger.info(f"ML status saved to {self.status_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving ML status: {e}")
            return False
    
    def get_truth_log_hash(self) -> str:
        """Get hash of truth log file for change detection"""
        try:
            if not self.truth_log_path.exists():
                return ""
            
            # Use file size + modification time for efficient change detection
            stat = self.truth_log_path.stat()
            hash_input = f"{stat.st_size}-{stat.st_mtime}"
            return hashlib.md5(hash_input.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Error getting truth log hash: {e}")
            return ""
    
    def count_new_entries(self, last_check_hash: str) -> int:
        """Count new entries in truth log since last check"""
        try:
            if not self.truth_log_path.exists():
                logger.warning(f"Truth log not found: {self.truth_log_path}")
                return 0
            
            current_hash = self.get_truth_log_hash()
            
            # If hash unchanged, no new entries
            if current_hash == last_check_hash:
                return 0
            
            # Count total entries (simple approach - count lines)
            entry_count = 0
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            json.loads(line)  # Validate JSON
                            entry_count += 1
                        except json.JSONDecodeError:
                            continue
            
            logger.info(f"Found {entry_count} total entries in truth log")
            return entry_count
            
        except Exception as e:
            logger.error(f"Error counting new entries: {e}")
            return 0
    
    def should_retrain(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Check if model should be retrained"""
        try:
            current_time = datetime.now(timezone.utc)
            current_hash = self.get_truth_log_hash()
            last_check_hash = status.get('last_check_hash', '')
            
            # Count current entries
            current_entry_count = self.count_new_entries('')
            last_entry_count = status.get('entry_count', 0)
            new_entries = max(0, current_entry_count - last_entry_count)
            
            # Check entry threshold
            entry_trigger = new_entries >= self.entry_threshold
            
            # Check time threshold
            time_trigger = False
            last_retrain = status.get('last_retrain')
            if last_retrain:
                try:
                    last_retrain_time = datetime.fromisoformat(last_retrain.replace('Z', '+00:00'))
                    days_since = (current_time - last_retrain_time).days
                    time_trigger = days_since >= self.time_threshold_days
                except (ValueError, TypeError):
                    time_trigger = True  # Invalid date, force retrain
            else:
                time_trigger = True  # Never retrained before
            
            # Determine if retrain needed
            should_retrain = entry_trigger or time_trigger
            
            reasons = []
            if entry_trigger:
                reasons.append(f"{new_entries} new entries (>={self.entry_threshold})")
            if time_trigger:
                if last_retrain:
                    reasons.append(f"{days_since} days since last retrain (>={self.time_threshold_days})")
                else:
                    reasons.append("No previous retrain found")
            
            result = {
                'should_retrain': should_retrain,
                'reasons': reasons,
                'new_entries': new_entries,
                'current_entry_count': current_entry_count,
                'current_hash': current_hash,
                'days_since_retrain': days_since if 'days_since' in locals() else 0
            }
            
            if should_retrain:
                logger.info(f"🔄 RETRAIN TRIGGERED: {', '.join(reasons)}")
            else:
                logger.info(f"📊 No retrain needed: {new_entries} new entries, {result['days_since_retrain']} days")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking retrain criteria: {e}")
            return {'should_retrain': False, 'error': str(e)}
    
    def run_training(self) -> Dict[str, Any]:
        """Execute train_model.py and capture results"""
        try:
            logger.info(f"🚀 Starting model training: {self.train_script_path}")
            
            # Check if training script exists
            if not self.train_script_path.exists():
                raise FileNotFoundError(f"Training script not found: {self.train_script_path}")
            
            # Run training script
            start_time = time.time()
            result = subprocess.run([
                'python3', str(self.train_script_path),
                '--truth-log', str(self.truth_log_path),
                '--model-path', str(self.model_path)
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            training_time = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ Training completed successfully in {training_time:.1f}s")
                
                # Try to extract accuracy from output
                accuracy = self.extract_accuracy_from_output(result.stdout)
                
                return {
                    'success': True,
                    'training_time': training_time,
                    'accuracy': accuracy,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                logger.error(f"❌ Training failed with return code {result.returncode}")
                return {
                    'success': False,
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'training_time': training_time
                }
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Training timed out after 10 minutes")
            return {'success': False, 'error': 'Training timeout'}
        except Exception as e:
            logger.error(f"❌ Training error: {e}")
            return {'success': False, 'error': str(e)}
    
    def extract_accuracy_from_output(self, output: str) -> float:
        """Extract model accuracy from training output"""
        try:
            # Look for common accuracy patterns in output
            import re
            
            # Pattern 1: CV Score: 0.681
            cv_match = re.search(r'CV Score:\s*([\d.]+)', output)
            if cv_match:
                return float(cv_match.group(1))
            
            # Pattern 2: Test score: 0.681
            test_match = re.search(r'[Tt]est\s+[Ss]core:\s*([\d.]+)', output)
            if test_match:
                return float(test_match.group(1))
            
            # Pattern 3: Accuracy: 68.1%
            acc_match = re.search(r'[Aa]ccuracy:\s*([\d.]+)%?', output)
            if acc_match:
                acc = float(acc_match.group(1))
                return acc / 100 if acc > 1 else acc
            
            # Pattern 4: Score: 0.681
            score_match = re.search(r'Score:\s*([\d.]+)', output)
            if score_match:
                return float(score_match.group(1))
            
            logger.warning("Could not extract accuracy from training output")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error extracting accuracy: {e}")
            return 0.0
    
    def update_status_after_retrain(self, status: Dict[str, Any], retrain_result: Dict[str, Any], 
                                  entry_count: int) -> Dict[str, Any]:
        """Update status after successful retrain"""
        current_time = datetime.now(timezone.utc)
        
        if retrain_result.get('success'):
            status.update({
                'last_retrain': current_time.isoformat(),
                'entry_count': entry_count,
                'model_accuracy': retrain_result.get('accuracy', 0.0),
                'last_check_hash': self.get_truth_log_hash(),
                'total_retrains': status.get('total_retrains', 0) + 1,
                'last_retrain_duration': retrain_result.get('training_time', 0),
                'last_retrain_success': True
            })
        else:
            status.update({
                'last_retrain_attempt': current_time.isoformat(),
                'last_retrain_success': False,
                'last_retrain_error': retrain_result.get('error', 'Unknown error')
            })
        
        return status
    
    def run_retrain_check(self) -> Dict[str, Any]:
        """Run complete retrain check and execute if needed"""
        logger.info("🔍 Checking retrain criteria...")
        
        try:
            # Load current status
            status = self.load_status()
            
            # Check if retrain is needed
            retrain_check = self.should_retrain(status)
            
            if not retrain_check.get('should_retrain', False):
                # Update hash even if no retrain needed
                status['last_check_hash'] = retrain_check.get('current_hash', '')
                status['last_check'] = datetime.now(timezone.utc).isoformat()
                self.save_status(status)
                return {
                    'retrain_performed': False,
                    'reason': 'Criteria not met',
                    'status': status
                }
            
            # Perform retrain
            logger.info("🔄 Starting model retrain...")
            retrain_result = self.run_training()
            
            # Update status
            entry_count = retrain_check.get('current_entry_count', 0)
            status = self.update_status_after_retrain(status, retrain_result, entry_count)
            
            # Save updated status
            self.save_status(status)
            
            if retrain_result.get('success'):
                logger.info(f"✅ Retrain completed - Accuracy: {status.get('model_accuracy', 0):.3f}")
            else:
                logger.error(f"❌ Retrain failed: {retrain_result.get('error', 'Unknown error')}")
            
            return {
                'retrain_performed': True,
                'success': retrain_result.get('success', False),
                'reasons': retrain_check.get('reasons', []),
                'new_entries': retrain_check.get('new_entries', 0),
                'accuracy': status.get('model_accuracy', 0.0),
                'status': status,
                'retrain_result': retrain_result
            }
            
        except Exception as e:
            logger.error(f"Error in retrain check: {e}")
            return {
                'retrain_performed': False,
                'error': str(e)
            }
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current ML training status summary"""
        try:
            status = self.load_status()
            current_entries = self.count_new_entries('')
            
            summary = {
                'model_exists': self.model_path.exists(),
                'truth_log_entries': current_entries,
                'last_retrain': status.get('last_retrain'),
                'model_accuracy': status.get('model_accuracy', 0.0),
                'total_retrains': status.get('total_retrains', 0),
                'entries_since_retrain': max(0, current_entries - status.get('entry_count', 0)),
                'days_since_retrain': 0
            }
            
            # Calculate days since retrain
            if status.get('last_retrain'):
                try:
                    last_retrain_time = datetime.fromisoformat(status['last_retrain'].replace('Z', '+00:00'))
                    summary['days_since_retrain'] = (datetime.now(timezone.utc) - last_retrain_time).days
                except:
                    pass
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting status summary: {e}")
            return {'error': str(e)}

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ML Retrain Manager')
    parser.add_argument('--check', action='store_true', help='Check retrain criteria and run if needed')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--force', action='store_true', help='Force retrain regardless of criteria')
    parser.add_argument('--loop', action='store_true', help='Run continuously every hour')
    parser.add_argument('--interval', type=int, default=3600, help='Loop interval in seconds (default: 3600)')
    
    args = parser.parse_args()
    
    try:
        manager = MLRetrainManager()
        
        if args.status:
            # Show status
            status = manager.get_status_summary()
            print("\n🤖 ML Retrain Manager Status:")
            print(f"   Model exists: {status.get('model_exists', False)}")
            print(f"   Truth log entries: {status.get('truth_log_entries', 0)}")
            print(f"   Last retrain: {status.get('last_retrain', 'Never')}")
            print(f"   Model accuracy: {status.get('model_accuracy', 0):.3f}")
            print(f"   Total retrains: {status.get('total_retrains', 0)}")
            print(f"   Entries since retrain: {status.get('entries_since_retrain', 0)}")
            print(f"   Days since retrain: {status.get('days_since_retrain', 0)}")
            
        elif args.force:
            # Force retrain
            print("🔄 Forcing model retrain...")
            retrain_result = manager.run_training()
            if retrain_result.get('success'):
                print(f"✅ Retrain completed - Accuracy: {retrain_result.get('accuracy', 0):.3f}")
            else:
                print(f"❌ Retrain failed: {retrain_result.get('error', 'Unknown error')}")
                
        elif args.loop:
            # Continuous monitoring
            logger.info(f"Starting continuous monitoring (every {args.interval}s)")
            while True:
                try:
                    result = manager.run_retrain_check()
                    if result.get('retrain_performed'):
                        if result.get('success'):
                            logger.info(f"✅ Retrain completed - Accuracy: {result.get('accuracy', 0):.3f}")
                        else:
                            logger.error("❌ Retrain failed")
                    
                    logger.info(f"Waiting {args.interval}s until next check...")
                    time.sleep(args.interval)
                    
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal - shutting down")
                    break
                    
        else:
            # Single check
            result = manager.run_retrain_check()
            
            if result.get('retrain_performed'):
                if result.get('success'):
                    print(f"\n✅ Retrain Completed:")
                    print(f"   Reasons: {', '.join(result.get('reasons', []))}")
                    print(f"   New entries: {result.get('new_entries', 0)}")
                    print(f"   Model accuracy: {result.get('accuracy', 0):.3f}")
                else:
                    print(f"\n❌ Retrain Failed:")
                    print(f"   Reasons: {', '.join(result.get('reasons', []))}")
                    print(f"   Error: {result.get('retrain_result', {}).get('error', 'Unknown')}")
            else:
                print(f"\n📊 No Retrain Needed:")
                print(f"   Reason: {result.get('reason', 'Unknown')}")
                
                status = result.get('status', {})
                print(f"   Current entries: {manager.count_new_entries('')}")
                print(f"   Last retrain: {status.get('last_retrain', 'Never')}")
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal - shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()