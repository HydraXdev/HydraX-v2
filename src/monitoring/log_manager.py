#!/usr/bin/env python3
"""
BITTEN Log Management System
Handles log rotation, cleanup, archival, and analysis for production environments.
"""

import os
import gzip
import shutil
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import subprocess
import asyncio
from dataclasses import dataclass, asdict
import threading
import time
from concurrent.futures import ThreadPoolExecutor

@dataclass
class LogMetrics:
    """Log metrics for analysis"""
    total_lines: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    file_size_mb: float
    oldest_entry: Optional[datetime]
    newest_entry: Optional[datetime]
    unique_users: int
    unique_actions: int
    avg_response_time: float

@dataclass
class LogFile:
    """Log file metadata"""
    path: Path
    size_mb: float
    created: datetime
    modified: datetime
    service: str
    log_type: str
    compressed: bool

class LogRotationManager:
    """Manages log rotation and cleanup"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_dir = Path(config.get('log_dir', '/var/log/bitten'))
        self.max_file_size = config.get('max_file_size_mb', 100) * 1024 * 1024
        self.max_files = config.get('max_files', 10)
        self.compress_after_days = config.get('compress_after_days', 1)
        self.delete_after_days = config.get('delete_after_days', 30)
        self.archive_dir = Path(config.get('archive_dir', '/var/log/bitten/archive'))
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger('log-manager')
        
    def rotate_logs(self) -> Dict[str, int]:
        """Rotate logs based on size and age"""
        results = {'rotated': 0, 'compressed': 0, 'archived': 0, 'deleted': 0}
        
        for log_file in self.log_dir.glob('*.log'):
            try:
                # Check if rotation is needed
                if self._needs_rotation(log_file):
                    self._rotate_file(log_file)
                    results['rotated'] += 1
                    
                # Check for compression
                if self._needs_compression(log_file):
                    self._compress_file(log_file)
                    results['compressed'] += 1
                    
                # Check for archival
                if self._needs_archival(log_file):
                    self._archive_file(log_file)
                    results['archived'] += 1
                    
                # Check for deletion
                if self._needs_deletion(log_file):
                    self._delete_file(log_file)
                    results['deleted'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing log file {log_file}: {e}")
        
        return results
    
    def _needs_rotation(self, log_file: Path) -> bool:
        """Check if log file needs rotation"""
        try:
            return log_file.stat().st_size > self.max_file_size
        except OSError:
            return False
    
    def _needs_compression(self, log_file: Path) -> bool:
        """Check if log file needs compression"""
        try:
            age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
            return age.days >= self.compress_after_days and not log_file.suffix == '.gz'
        except OSError:
            return False
    
    def _needs_archival(self, log_file: Path) -> bool:
        """Check if log file needs archival"""
        try:
            age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
            return age.days >= 7 and log_file.suffix == '.gz'
        except OSError:
            return False
    
    def _needs_deletion(self, log_file: Path) -> bool:
        """Check if log file needs deletion"""
        try:
            age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
            return age.days >= self.delete_after_days
        except OSError:
            return False
    
    def _rotate_file(self, log_file: Path):
        """Rotate a log file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rotated_name = f"{log_file.stem}_{timestamp}.log"
        rotated_path = log_file.parent / rotated_name
        
        # Move current log to rotated name
        shutil.move(log_file, rotated_path)
        
        # Create new empty log file
        log_file.touch()
        os.chmod(log_file, 0o644)
        
        self.logger.info(f"Rotated log file: {log_file} -> {rotated_path}")
    
    def _compress_file(self, log_file: Path):
        """Compress a log file"""
        compressed_path = log_file.with_suffix('.log.gz')
        
        with open(log_file, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        os.remove(log_file)
        self.logger.info(f"Compressed log file: {log_file} -> {compressed_path}")
    
    def _archive_file(self, log_file: Path):
        """Archive a log file"""
        # Create date-based subdirectory
        date_dir = self.archive_dir / datetime.now().strftime('%Y/%m')
        date_dir.mkdir(parents=True, exist_ok=True)
        
        archive_path = date_dir / log_file.name
        shutil.move(log_file, archive_path)
        
        self.logger.info(f"Archived log file: {log_file} -> {archive_path}")
    
    def _delete_file(self, log_file: Path):
        """Delete old log file"""
        os.remove(log_file)
        self.logger.info(f"Deleted old log file: {log_file}")
    
    def get_log_inventory(self) -> List[LogFile]:
        """Get inventory of all log files"""
        inventory = []
        
        for log_file in self.log_dir.rglob('*.log*'):
            try:
                stat = log_file.stat()
                size_mb = stat.st_size / (1024 * 1024)
                created = datetime.fromtimestamp(stat.st_ctime)
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                # Parse service and log type from filename
                parts = log_file.stem.split('_')
                service = parts[0] if parts else 'unknown'
                log_type = parts[1] if len(parts) > 1 else 'main'
                
                inventory.append(LogFile(
                    path=log_file,
                    size_mb=size_mb,
                    created=created,
                    modified=modified,
                    service=service,
                    log_type=log_type,
                    compressed=log_file.suffix == '.gz'
                ))
            except OSError:
                continue
        
        return inventory

class LogAnalyzer:
    """Analyzes log files for metrics and insights"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.logger = logging.getLogger('log-analyzer')
    
    def analyze_log_file(self, log_file: Path) -> LogMetrics:
        """Analyze a single log file"""
        metrics = LogMetrics(
            total_lines=0,
            error_count=0,
            warning_count=0,
            info_count=0,
            debug_count=0,
            file_size_mb=0,
            oldest_entry=None,
            newest_entry=None,
            unique_users=0,
            unique_actions=0,
            avg_response_time=0
        )
        
        try:
            # Get file size
            metrics.file_size_mb = log_file.stat().st_size / (1024 * 1024)
            
            # Open file (handle compressed files)
            if log_file.suffix == '.gz':
                open_func = gzip.open
                mode = 'rt'
            else:
                open_func = open
                mode = 'r'
            
            users = set()
            actions = set()
            response_times = []
            
            with open_func(log_file, mode, encoding='utf-8', errors='ignore') as f:
                for line in f:
                    metrics.total_lines += 1
                    
                    try:
                        # Parse JSON log entry
                        entry = json.loads(line.strip())
                        
                        # Count log levels
                        level = entry.get('level', '').upper()
                        if level == 'ERROR':
                            metrics.error_count += 1
                        elif level == 'WARNING':
                            metrics.warning_count += 1
                        elif level == 'INFO':
                            metrics.info_count += 1
                        elif level == 'DEBUG':
                            metrics.debug_count += 1
                        
                        # Track timestamps
                        timestamp_str = entry.get('timestamp')
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if metrics.oldest_entry is None or timestamp < metrics.oldest_entry:
                                metrics.oldest_entry = timestamp
                            if metrics.newest_entry is None or timestamp > metrics.newest_entry:
                                metrics.newest_entry = timestamp
                        
                        # Track unique users and actions
                        if 'user_id' in entry:
                            users.add(entry['user_id'])
                        if 'action' in entry:
                            actions.add(entry['action'])
                        
                        # Track response times
                        if 'duration_ms' in entry:
                            response_times.append(entry['duration_ms'])
                    
                    except (json.JSONDecodeError, ValueError):
                        # Skip non-JSON lines
                        continue
            
            metrics.unique_users = len(users)
            metrics.unique_actions = len(actions)
            metrics.avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
        except Exception as e:
            self.logger.error(f"Error analyzing log file {log_file}: {e}")
        
        return metrics
    
    def generate_daily_report(self, date: datetime) -> Dict[str, Any]:
        """Generate daily log analysis report"""
        report = {
            'date': date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'services': {},
            'summary': {
                'total_logs': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'total_size_mb': 0,
                'unique_users': set(),
                'unique_actions': set()
            }
        }
        
        # Find log files for the date
        date_pattern = date.strftime('%Y%m%d')
        log_files = list(self.log_dir.glob(f'*{date_pattern}*.log*'))
        
        for log_file in log_files:
            try:
                metrics = self.analyze_log_file(log_file)
                
                # Parse service name from filename
                service_name = log_file.stem.split('_')[0]
                
                if service_name not in report['services']:
                    report['services'][service_name] = {
                        'files': [],
                        'total_lines': 0,
                        'total_errors': 0,
                        'total_warnings': 0,
                        'total_size_mb': 0,
                        'avg_response_time': 0
                    }
                
                # Add file metrics
                report['services'][service_name]['files'].append({
                    'filename': log_file.name,
                    'metrics': asdict(metrics)
                })
                
                # Update service totals
                service_data = report['services'][service_name]
                service_data['total_lines'] += metrics.total_lines
                service_data['total_errors'] += metrics.error_count
                service_data['total_warnings'] += metrics.warning_count
                service_data['total_size_mb'] += metrics.file_size_mb
                
                # Update summary
                report['summary']['total_logs'] += metrics.total_lines
                report['summary']['total_errors'] += metrics.error_count
                report['summary']['total_warnings'] += metrics.warning_count
                report['summary']['total_size_mb'] += metrics.file_size_mb
                
            except Exception as e:
                self.logger.error(f"Error processing log file {log_file}: {e}")
        
        # Convert sets to counts
        report['summary']['unique_users'] = len(report['summary']['unique_users'])
        report['summary']['unique_actions'] = len(report['summary']['unique_actions'])
        
        return report

class LogManager:
    """Main log management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_dir = Path(config.get('log_dir', '/var/log/bitten'))
        self.rotation_manager = LogRotationManager(config)
        self.analyzer = LogAnalyzer(self.log_dir)
        self.logger = logging.getLogger('log-manager')
        
        # Background thread for periodic tasks
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def start(self):
        """Start log management background tasks"""
        self.running = True
        
        # Start rotation task
        self.executor.submit(self._rotation_task)
        
        # Start cleanup task
        self.executor.submit(self._cleanup_task)
        
        self.logger.info("Log management system started")
    
    def stop(self):
        """Stop log management background tasks"""
        self.running = False
        self.executor.shutdown(wait=True)
        self.logger.info("Log management system stopped")
    
    def _rotation_task(self):
        """Background task for log rotation"""
        while self.running:
            try:
                results = self.rotation_manager.rotate_logs()
                if any(results.values()):
                    self.logger.info(f"Log rotation completed: {results}")
                
                # Sleep for 1 hour
                time.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Error in rotation task: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def _cleanup_task(self):
        """Background task for log cleanup"""
        while self.running:
            try:
                # Clean up old files
                self._cleanup_old_files()
                
                # Generate daily report
                yesterday = datetime.now() - timedelta(days=1)
                report = self.analyzer.generate_daily_report(yesterday)
                
                # Save report
                report_file = self.log_dir / f"daily_report_{yesterday.strftime('%Y%m%d')}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                
                self.logger.info(f"Daily report generated: {report_file}")
                
                # Sleep for 24 hours (check once per day)
                time.sleep(86400)
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                time.sleep(3600)  # Wait 1 hour before retry
    
    def _cleanup_old_files(self):
        """Clean up old log files"""
        cutoff_date = datetime.now() - timedelta(days=self.config.get('delete_after_days', 30))
        
        for log_file in self.log_dir.rglob('*.log*'):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff_date:
                    os.remove(log_file)
                    self.logger.info(f"Deleted old log file: {log_file}")
            except OSError:
                continue
    
    def get_status(self) -> Dict[str, Any]:
        """Get log management status"""
        inventory = self.rotation_manager.get_log_inventory()
        
        return {
            'status': 'running' if self.running else 'stopped',
            'log_directory': str(self.log_dir),
            'total_files': len(inventory),
            'total_size_mb': sum(f.size_mb for f in inventory),
            'services': list(set(f.service for f in inventory)),
            'oldest_file': min(inventory, key=lambda f: f.created).created if inventory else None,
            'newest_file': max(inventory, key=lambda f: f.modified).modified if inventory else None
        }

# Global log manager instance
_log_manager = None

def get_log_manager(config: Optional[Dict[str, Any]] = None) -> LogManager:
    """Get global log manager instance"""
    global _log_manager
    if _log_manager is None:
        default_config = {
            'log_dir': '/var/log/bitten',
            'max_file_size_mb': 100,
            'max_files': 10,
            'compress_after_days': 1,
            'delete_after_days': 30,
            'archive_dir': '/var/log/bitten/archive'
        }
        _log_manager = LogManager(config or default_config)
    return _log_manager

# CLI for log management
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='BITTEN Log Management System')
    parser.add_argument('--rotate', action='store_true', help='Rotate logs now')
    parser.add_argument('--analyze', type=str, help='Analyze log file')
    parser.add_argument('--report', type=str, help='Generate daily report (YYYY-MM-DD)')
    parser.add_argument('--status', action='store_true', help='Show log management status')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create log manager
    log_manager = get_log_manager()
    
    if args.rotate:
        results = log_manager.rotation_manager.rotate_logs()
        print(f"Rotation completed: {results}")
    
    elif args.analyze:
        log_file = Path(args.analyze)
        if log_file.exists():
            metrics = log_manager.analyzer.analyze_log_file(log_file)
            print(json.dumps(asdict(metrics), indent=2, default=str))
        else:
            print(f"Log file not found: {log_file}")
    
    elif args.report:
        try:
            date = datetime.strptime(args.report, '%Y-%m-%d')
            report = log_manager.analyzer.generate_daily_report(date)
            print(json.dumps(report, indent=2, default=str))
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
    
    elif args.status:
        status = log_manager.get_status()
        print(json.dumps(status, indent=2, default=str))
    
    else:
        print("Use --help for usage information")