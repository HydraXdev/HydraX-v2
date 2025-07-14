#!/usr/bin/env python3
"""
BRIDGE TROLL AGENT - Military Grade Bridge Monitor & Technical Expert
Version: 1.0 FORTRESS
Status: ACTIVE DUTY

MISSION: Complete mastery and monitoring of BITTEN bridge infrastructure
SPECIALTY: Bridge architecture, fault diagnosis, and technical intelligence
CLEARANCE: FULL ACCESS to all bridge systems and diagnostics

The BRIDGE TROLL is the definitive technical authority on:
- Bridge file communication protocols
- MT5 terminal integration architecture  
- Signal flow pathways and bottlenecks
- Error patterns and resolution procedures
- Performance metrics and optimization

NEVER COMPROMISES. ALWAYS AVAILABLE. KNOWS EVERY BOLT AND WIRE.
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class BridgeStatus(Enum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"

@dataclass
class BridgeHealth:
    status: BridgeStatus
    response_time: float
    signal_files_count: int
    last_signal_time: Optional[datetime]
    error_count: int
    warnings: List[str]
    recommendations: List[str]

class BridgeTrollAgent:
    """
    BRIDGE TROLL AGENT - The Ultimate Bridge Technical Authority
    
    CORE COMPETENCIES:
    - Bridge infrastructure monitoring and diagnostics
    - MT5 terminal communication protocols
    - Signal file management and optimization
    - Real-time performance analysis
    - Emergency response and recovery procedures
    
    TECHNICAL KNOWLEDGE BASE:
    - Bridge Architecture: Windows MT5 Server (3.145.84.187) with bulletproof agents
    - Communication Protocol: HTTP POST to ports 5555-5557 with JSON payloads
    - File System: C:\\Users\\Administrator\\AppData\\Roaming\\MetaQuotes\\Terminal\\173477FF1060D99CE79296FC73108719\\MQL5\\Files\\BITTEN\\
    - Signal Format: JSON files with pattern *{SYMBOL}*.json
    - Command Types: CMD and PowerShell execution via bridge agents
    """
    
    def __init__(self):
        self.agent_name = "BRIDGE_TROLL"
        self.version = "1.0_FORTRESS"
        self.deployment_time = datetime.now()
        self.bridge_server = "3.145.84.187"
        self.bridge_ports = [5555, 5556, 5557]
        self.primary_port = 5555
        self.bridge_path = r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719\MQL5\Files\BITTEN\\"
        
        # Initialize military-grade logging
        self.setup_fortress_logging()
        
        # Bridge architecture knowledge base
        self.bridge_architecture = {
            "primary_server": "3.145.84.187",
            "agent_ports": [5555, 5556, 5557],
            "terminal_id": "173477FF1060D99CE79296FC73108719",
            "signal_directory": r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719\MQL5\Files\BITTEN\\",
            "communication_protocol": "HTTP_POST_JSON",
            "supported_commands": ["cmd", "powershell"],
            "signal_format": "JSON",
            "signal_pattern": "*{SYMBOL}*.json",
            "ea_configuration": {
                "master_type": "Generic_Demo",
                "risk_percent": 5.0,
                "max_daily_loss": 20.0,
                "magic_range": [50001, 50200],
                "supported_pairs": ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY", "AUDUSD", "NZDUSD", "EURGBP", "USDCHF", "EURJPY"]
            }
        }
        
        self.logger.info(f"🛡️ BRIDGE TROLL AGENT {self.version} DEPLOYED")
        self.logger.info(f"📡 MONITORING BRIDGE INFRASTRUCTURE: {self.bridge_server}")
        self.logger.info(f"🎯 MISSION: FORTRESS-LEVEL BRIDGE PROTECTION AND TECHNICAL INTELLIGENCE")
        
    def setup_fortress_logging(self):
        """Initialize military-grade logging system"""
        log_format = '%(asctime)s - BRIDGE_TROLL - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('/root/HydraX-v2/bridge_troll.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("BRIDGE_TROLL")
        
    def get_bridge_health(self) -> BridgeHealth:
        """
        FORTRESS-LEVEL BRIDGE HEALTH ASSESSMENT
        Returns comprehensive health status with military precision
        """
        start_time = time.time()
        warnings = []
        recommendations = []
        error_count = 0
        
        try:
            # Test primary bridge connection
            response = requests.get(f"http://{self.bridge_server}:{self.primary_port}/health", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                error_count += 1
                warnings.append(f"Bridge HTTP status: {response.status_code}")
                
        except requests.RequestException as e:
            error_count += 1
            warnings.append(f"Bridge connection failed: {str(e)}")
            response_time = time.time() - start_time
            
        # Count signal files
        signal_count, last_signal = self._count_signal_files()
        
        # Determine overall status
        if error_count == 0 and response_time < 1.0:
            status = BridgeStatus.OPERATIONAL
        elif error_count == 0 and response_time < 3.0:
            status = BridgeStatus.DEGRADED
            warnings.append(f"High response time: {response_time:.2f}s")
        elif error_count > 0:
            status = BridgeStatus.CRITICAL
        else:
            status = BridgeStatus.OFFLINE
            
        # Generate recommendations
        if response_time > 2.0:
            recommendations.append("Consider bridge server optimization")
        if signal_count == 0:
            recommendations.append("No signal files detected - verify EA status")
            
        return BridgeHealth(
            status=status,
            response_time=response_time,
            signal_files_count=signal_count,
            last_signal_time=last_signal,
            error_count=error_count,
            warnings=warnings,
            recommendations=recommendations
        )
        
    def _count_signal_files(self) -> Tuple[int, Optional[datetime]]:
        """Count signal files and get latest timestamp"""
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.primary_port}/execute",
                json={
                    "command": f'dir /B "{self.bridge_path}*.json"',
                    "type": "cmd"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('stdout'):
                    files = result['stdout'].strip().split('\n')
                    return len([f for f in files if f.strip()]), datetime.now()
                    
        except Exception as e:
            self.logger.error(f"Failed to count signal files: {e}")
            
        return 0, None
        
    def diagnose_signal_detection_failure(self, symbol: str) -> Dict:
        """
        COMPREHENSIVE SIGNAL DETECTION FAILURE ANALYSIS
        Military-grade diagnostic for signal detection issues
        """
        self.logger.info(f"🔍 INITIATING SIGNAL DETECTION DIAGNOSIS FOR {symbol}")
        
        diagnosis = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "root_cause": None,
            "resolution": None,
            "confidence": 0
        }
        
        # Test 1: Bridge connectivity
        diagnosis["tests"]["bridge_connectivity"] = self._test_bridge_connectivity()
        
        # Test 2: Directory access
        diagnosis["tests"]["directory_access"] = self._test_directory_access()
        
        # Test 3: File pattern matching
        diagnosis["tests"]["pattern_matching"] = self._test_pattern_matching(symbol)
        
        # Test 4: File content validation
        diagnosis["tests"]["file_validation"] = self._test_file_validation(symbol)
        
        # Test 5: Command execution environment
        diagnosis["tests"]["command_environment"] = self._test_command_environment()
        
        # Analyze results and determine root cause
        self._analyze_diagnosis(diagnosis)
        
        return diagnosis
        
    def _test_bridge_connectivity(self) -> Dict:
        """Test bridge server connectivity"""
        try:
            start_time = time.time()
            response = requests.get(f"http://{self.bridge_server}:{self.primary_port}/health", timeout=5)
            response_time = time.time() - start_time
            
            return {
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "response_time": response_time,
                "http_status": response.status_code,
                "details": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "error": str(e),
                "response_time": None
            }
            
    def _test_directory_access(self) -> Dict:
        """Test bridge directory access"""
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.primary_port}/execute",
                json={
                    "command": f'dir "{self.bridge_path}"',
                    "type": "cmd"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "PASS" if result.get('success') else "FAIL",
                    "returncode": result.get('returncode'),
                    "file_count": len(result.get('stdout', '').split('\n')) if result.get('stdout') else 0,
                    "raw_response": result
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "error": str(e)
            }
            
    def _test_pattern_matching(self, symbol: str) -> Dict:
        """Test file pattern matching for specific symbol"""
        tests = {}
        
        # Test different pattern approaches
        patterns = [
            f'dir /B "{self.bridge_path}*{symbol}*.json"',
            f'cd /D "{self.bridge_path}" && dir /B *{symbol}*.json',
            f'dir /B "{self.bridge_path}" | findstr {symbol}'
        ]
        
        for i, pattern in enumerate(patterns, 1):
            try:
                response = requests.post(
                    f"http://{self.bridge_server}:{self.primary_port}/execute",
                    json={"command": pattern, "type": "cmd"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    tests[f"pattern_{i}"] = {
                        "command": pattern,
                        "status": "PASS" if result.get('returncode') == 0 else "FAIL",
                        "returncode": result.get('returncode'),
                        "stdout": result.get('stdout', '').strip(),
                        "file_found": bool(result.get('stdout', '').strip())
                    }
            except Exception as e:
                tests[f"pattern_{i}"] = {
                    "command": pattern,
                    "status": "ERROR",
                    "error": str(e)
                }
                
        return tests
        
    def _test_file_validation(self, symbol: str) -> Dict:
        """Test file content validation"""
        # First try to find any files for the symbol
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.primary_port}/execute",
                json={
                    "command": f'cd /D "{self.bridge_path}" && dir /B *{symbol}*.json',
                    "type": "cmd"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('returncode') == 0 and result.get('stdout'):
                    files = [f.strip() for f in result['stdout'].strip().split('\n') if f.strip()]
                    if files:
                        # Test reading the first file
                        file_test = self._test_file_content(files[0])
                        return {
                            "files_found": files,
                            "file_count": len(files),
                            "content_test": file_test
                        }
                        
            return {
                "files_found": [],
                "file_count": 0,
                "content_test": None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "files_found": [],
                "file_count": 0
            }
            
    def _test_file_content(self, filename: str) -> Dict:
        """Test reading and parsing a specific file"""
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.primary_port}/execute",
                json={
                    "command": f'type "{self.bridge_path}{filename}"',
                    "type": "cmd"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('returncode') == 0 and result.get('stdout'):
                    content = result['stdout'].strip()
                    try:
                        parsed = json.loads(content)
                        return {
                            "status": "PASS",
                            "filename": filename,
                            "content_length": len(content),
                            "json_valid": True,
                            "parsed_data": parsed
                        }
                    except json.JSONDecodeError as e:
                        return {
                            "status": "FAIL",
                            "filename": filename,
                            "content_length": len(content),
                            "json_valid": False,
                            "json_error": str(e),
                            "raw_content": content[:200]
                        }
                        
        except Exception as e:
            return {
                "status": "ERROR",
                "filename": filename,
                "error": str(e)
            }
            
    def _test_command_environment(self) -> Dict:
        """Test command execution environment"""
        tests = {}
        
        env_commands = [
            ("working_dir", "cd"),
            ("system_time", "echo %date% %time%"),
            ("user_context", "whoami"),
            ("permissions", f'icacls "{self.bridge_path}"')
        ]
        
        for test_name, command in env_commands:
            try:
                response = requests.post(
                    f"http://{self.bridge_server}:{self.primary_port}/execute",
                    json={"command": command, "type": "cmd"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    tests[test_name] = {
                        "status": "PASS" if result.get('returncode') == 0 else "FAIL",
                        "output": result.get('stdout', '').strip()
                    }
            except Exception as e:
                tests[test_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
                
        return tests
        
    def _analyze_diagnosis(self, diagnosis: Dict):
        """Analyze diagnosis results and determine root cause"""
        tests = diagnosis["tests"]
        
        # Priority analysis based on test results
        if tests.get("bridge_connectivity", {}).get("status") != "PASS":
            diagnosis["root_cause"] = "BRIDGE_CONNECTIVITY_FAILURE"
            diagnosis["resolution"] = "Bridge server is unreachable. Check network connectivity and server status."
            diagnosis["confidence"] = 95
            
        elif tests.get("directory_access", {}).get("status") != "PASS":
            diagnosis["root_cause"] = "DIRECTORY_ACCESS_FAILURE"
            diagnosis["resolution"] = "Cannot access signal directory. Check path permissions and MT5 terminal status."
            diagnosis["confidence"] = 90
            
        elif not any(test.get("file_found", False) for test in tests.get("pattern_matching", {}).values()):
            diagnosis["root_cause"] = "NO_SIGNAL_FILES"
            diagnosis["resolution"] = "No signal files found for symbol. Verify EA is generating signals and file naming convention."
            diagnosis["confidence"] = 85
            
        elif tests.get("file_validation", {}).get("file_count", 0) > 0:
            content_test = tests.get("file_validation", {}).get("content_test", {})
            if content_test and not content_test.get("json_valid", True):
                diagnosis["root_cause"] = "INVALID_FILE_FORMAT"
                diagnosis["resolution"] = "Signal files exist but contain invalid JSON. Check EA signal generation format."
                diagnosis["confidence"] = 80
            else:
                diagnosis["root_cause"] = "PATTERN_MATCHING_ISSUE"
                diagnosis["resolution"] = "Files exist but pattern matching fails. Use alternative file detection method."
                diagnosis["confidence"] = 75
        else:
            diagnosis["root_cause"] = "UNKNOWN"
            diagnosis["resolution"] = "Unable to determine root cause. Manual investigation required."
            diagnosis["confidence"] = 30
            
    def get_bridge_architecture_report(self) -> Dict:
        """
        COMPREHENSIVE BRIDGE ARCHITECTURE INTELLIGENCE REPORT
        Complete technical documentation for troubleshooting
        """
        return {
            "agent_info": {
                "name": self.agent_name,
                "version": self.version,
                "deployment_time": self.deployment_time.isoformat(),
                "mission": "FORTRESS-LEVEL BRIDGE PROTECTION AND TECHNICAL INTELLIGENCE"
            },
            "bridge_architecture": self.bridge_architecture,
            "current_health": self.get_bridge_health().__dict__,
            "operational_parameters": {
                "primary_server": self.bridge_server,
                "primary_port": self.primary_port,
                "backup_ports": self.bridge_ports[1:],
                "signal_directory": self.bridge_path,
                "supported_symbols": self.bridge_architecture["ea_configuration"]["supported_pairs"],
                "communication_timeout": 10,
                "retry_attempts": 3
            },
            "troubleshooting_guide": {
                "signal_detection_failure": "Run diagnose_signal_detection_failure(symbol)",
                "bridge_connectivity": "Check get_bridge_health() status",
                "file_access_issues": "Verify MT5 terminal and EA status",
                "performance_degradation": "Monitor response_time in health checks"
            }
        }
        
    def monitor_continuous(self, interval: int = 30):
        """
        CONTINUOUS BRIDGE MONITORING MODE
        Military-grade 24/7 surveillance
        """
        self.logger.info(f"🛡️ INITIATING CONTINUOUS BRIDGE SURVEILLANCE (Interval: {interval}s)")
        
        while True:
            try:
                health = self.get_bridge_health()
                
                if health.status == BridgeStatus.OPERATIONAL:
                    self.logger.info(f"✅ BRIDGE STATUS: {health.status.value} (Response: {health.response_time:.2f}s)")
                elif health.status == BridgeStatus.DEGRADED:
                    self.logger.warning(f"⚠️ BRIDGE STATUS: {health.status.value} - {health.warnings}")
                else:
                    self.logger.error(f"🚨 BRIDGE STATUS: {health.status.value} - CRITICAL ISSUES DETECTED")
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("🛡️ BRIDGE TROLL SURVEILLANCE TERMINATED")
                break
            except Exception as e:
                self.logger.error(f"❌ SURVEILLANCE ERROR: {e}")
                time.sleep(10)

# Create global BRIDGE TROLL instance
BRIDGE_TROLL = BridgeTrollAgent()

def get_bridge_expert() -> BridgeTrollAgent:
    """Get the BRIDGE TROLL technical expert"""
    return BRIDGE_TROLL

if __name__ == "__main__":
    print("🛡️ BRIDGE TROLL AGENT - FORTRESS MODE ACTIVATED")
    print("=" * 60)
    
    # Display bridge architecture report
    report = BRIDGE_TROLL.get_bridge_architecture_report()
    print(json.dumps(report, indent=2, default=str))
    
    # Start continuous monitoring if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        BRIDGE_TROLL.monitor_continuous()