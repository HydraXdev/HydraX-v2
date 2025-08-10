#!/usr/bin/env python3
"""
REAL DATA VALIDATION LAYER
Comprehensive validation to reject ANY synthetic/fake/demo data
CRITICAL: One fake price could cost thousands - Better offline than fake
"""

import re
import json
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import sys

# Add project root to path
sys.path.append('/root/HydraX-v2')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DATA_VALIDATOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/data_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ValidationResult(Enum):
    """Validation result types"""
    VALID_REAL = "valid_real"
    INVALID_FAKE = "invalid_fake"
    INVALID_DEMO = "invalid_demo"
    INVALID_SYNTHETIC = "invalid_synthetic"
    INVALID_STALE = "invalid_stale"
    INVALID_CORRUPTED = "invalid_corrupted"
    VALIDATION_ERROR = "validation_error"

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    result: ValidationResult
    confidence: float  # 0-100%
    reasons: List[str]
    warnings: List[str]
    data_hash: str
    timestamp: float
    source_verified: bool
    real_data_confirmed: bool

class FakeDataSignature:
    """Known signatures of fake/demo data"""
    
    # Demo account patterns
    DEMO_ACCOUNT_PATTERNS = [
        r'demo',
        r'test',
        r'simulation',
        r'sim',
        r'fake',
        r'mock',
        r'sandbox',
        r'MetaQuotes-Demo',
        r'Demo Server',
        r'[Dd]emo.*[Aa]ccount',
        r'Test.*[Aa]ccount',
        r'Practice.*[Aa]ccount'
    ]
    
    # Fake price patterns (too perfect/round numbers)
    FAKE_PRICE_PATTERNS = [
        r'1\.00000',  # Perfect 1.0
        r'1\.10000',  # Perfect 1.1
        r'1\.20000',  # Perfect 1.2
        r'\.00000$',  # Ends with 00000
        r'\.99999$',  # Ends with 99999
        r'\.12345',   # Sequential digits
        r'\.54321',   # Reverse sequential
    ]
    
    # Synthetic data indicators
    SYNTHETIC_INDICATORS = [
        'random',
        'generated',
        'simulated',
        'artificial',
        'mock',
        'placeholder',
        'dummy',
        'test_data',
        'sample',
        'example'
    ]
    
    # Blacklisted sources
    BLACKLISTED_SOURCES = [
        'random.random',
        'np.random',
        'math.random',
        'faker',
        'simulation',
        'mock_api',
        'test_server',
        'localhost',
        'demo_feed',
        'synthetic_feed'
    ]

class RealDataValidator:
    """
    Comprehensive real data validation system
    ZERO TOLERANCE for fake/synthetic/demo data
    """
    
    def __init__(self):
        self.validation_stats = {
            'total_validations': 0,
            'valid_real': 0,
            'invalid_fake': 0,
            'invalid_demo': 0,
            'invalid_synthetic': 0,
            'invalid_stale': 0,
            'invalid_corrupted': 0,
            'validation_errors': 0,
            'fake_data_blocked': 0,
            'start_time': time.time()
        }
        
        self.fake_signatures = FakeDataSignature()
        
        # Real source whitelist (must be verified real data sources)
        self.verified_real_sources = {
            'EA_CONFIRMATION',
            'TRUTH_TRACKER',
            'POSITION_TRACKER',
            'BROKER_API_OANDA',
            'BROKER_API_IC_MARKETS',
            'BROKER_API_IG',
            'BROKER_API_FXCM',
            'MARKET_DATA_RECEIVER',
            'ZMQ_TELEMETRY_BRIDGE'
        }
        
        # Broker API endpoints (real only)
        self.real_broker_apis = {
            'api-fxtrade.oanda.com',
            'api.icmarkets.com',
            'api.ig.com',
            'api-demo.fxcm.com'  # Note: FXCM demo API is their live endpoint
        }
        
        logger.info("🛡️ Real Data Validator initialized")
        logger.info("🚨 ZERO TOLERANCE for fake/synthetic data")
        
    def validate_data(self, data: Any, source: str = "UNKNOWN", context: str = "") -> ValidationReport:
        """
        Comprehensive data validation - STRICT REAL DATA ONLY
        """
        start_time = time.time()
        self.validation_stats['total_validations'] += 1
        
        try:
            # Convert to dict if possible
            if hasattr(data, '__dict__'):
                data_dict = data.__dict__
            elif isinstance(data, dict):
                data_dict = data
            else:
                data_dict = {'value': data}
                
            # Calculate data hash
            data_str = json.dumps(data_dict, sort_keys=True, default=str)
            data_hash = hashlib.md5(data_str.encode()).hexdigest()
            
            # Initialize validation report
            report = ValidationReport(
                result=ValidationResult.VALID_REAL,
                confidence=100.0,
                reasons=[],
                warnings=[],
                data_hash=data_hash,
                timestamp=start_time,
                source_verified=False,
                real_data_confirmed=False
            )
            
            # STEP 1: Source validation
            source_valid = self._validate_source(source, report)
            
            # STEP 2: Demo account detection
            demo_detected = self._detect_demo_data(data_dict, report)
            
            # STEP 3: Synthetic data detection
            synthetic_detected = self._detect_synthetic_data(data_dict, report)
            
            # STEP 4: Fake pattern detection
            fake_patterns = self._detect_fake_patterns(data_dict, report)
            
            # STEP 5: Timestamp validation
            timestamp_valid = self._validate_timestamps(data_dict, report)
            
            # STEP 6: Data integrity validation
            integrity_valid = self._validate_data_integrity(data_dict, report)
            
            # STEP 7: Price validation (if applicable)
            price_valid = self._validate_prices(data_dict, report)
            
            # FINAL DETERMINATION
            if demo_detected:
                report.result = ValidationResult.INVALID_DEMO
                report.confidence = 0.0
                self.validation_stats['invalid_demo'] += 1
                
            elif synthetic_detected:
                report.result = ValidationResult.INVALID_SYNTHETIC
                report.confidence = 0.0
                self.validation_stats['invalid_synthetic'] += 1
                
            elif fake_patterns:
                report.result = ValidationResult.INVALID_FAKE
                report.confidence = 0.0
                self.validation_stats['invalid_fake'] += 1
                
            elif not timestamp_valid:
                report.result = ValidationResult.INVALID_STALE
                report.confidence = 0.0
                self.validation_stats['invalid_stale'] += 1
                
            elif not integrity_valid:
                report.result = ValidationResult.INVALID_CORRUPTED
                report.confidence = 0.0
                self.validation_stats['invalid_corrupted'] += 1
                
            elif not (source_valid and price_valid):
                report.result = ValidationResult.INVALID_FAKE
                report.confidence = 0.0
                report.reasons.append("Failed validation checks")
                self.validation_stats['invalid_fake'] += 1
                
            else:
                # All validations passed
                report.result = ValidationResult.VALID_REAL
                report.source_verified = True
                report.real_data_confirmed = True
                self.validation_stats['valid_real'] += 1
                
            # Update blocked counter
            if report.result != ValidationResult.VALID_REAL:
                self.validation_stats['fake_data_blocked'] += 1
                
            # Log results
            self._log_validation_result(report, source, context)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Validation error: {str(e)}")
            self.validation_stats['validation_errors'] += 1
            
            return ValidationReport(
                result=ValidationResult.VALIDATION_ERROR,
                confidence=0.0,
                reasons=[f"Validation error: {str(e)}"],
                warnings=[],
                data_hash="ERROR",
                timestamp=start_time,
                source_verified=False,
                real_data_confirmed=False
            )
            
    def _validate_source(self, source: str, report: ValidationReport) -> bool:
        """Validate data source is from approved real sources"""
        try:
            # Check if source is in verified real sources
            if source in self.verified_real_sources:
                report.reasons.append(f"✅ Verified real source: {source}")
                return True
                
            # Check for URL sources (broker APIs)
            if any(api in source.lower() for api in self.real_broker_apis):
                report.reasons.append(f"✅ Real broker API source: {source}")
                return True
                
            # Check for blacklisted sources
            if any(blacklisted in source.lower() for blacklisted in self.fake_signatures.BLACKLISTED_SOURCES):
                report.reasons.append(f"❌ BLACKLISTED source: {source}")
                return False
                
            # Unknown source - be cautious
            report.warnings.append(f"⚠️ Unknown source: {source}")
            return False
            
        except Exception as e:
            report.reasons.append(f"❌ Source validation error: {str(e)}")
            return False
            
    def _detect_demo_data(self, data: Dict, report: ValidationReport) -> bool:
        """Detect demo/test account data"""
        try:
            # Convert all values to strings for pattern matching
            data_str = json.dumps(data, default=str).lower()
            
            # Check for demo patterns
            for pattern in self.fake_signatures.DEMO_ACCOUNT_PATTERNS:
                if re.search(pattern, data_str, re.IGNORECASE):
                    report.reasons.append(f"❌ DEMO DATA DETECTED: Pattern '{pattern}' found")
                    return True
                    
            # Check specific fields that often contain demo indicators
            demo_fields = ['account', 'server', 'broker', 'login', 'name', 'description']
            for field in demo_fields:
                if field in data:
                    value = str(data[field]).lower()
                    if any(demo in value for demo in ['demo', 'test', 'simulation', 'practice']):
                        report.reasons.append(f"❌ DEMO indicator in {field}: {value}")
                        return True
                        
            return False
            
        except Exception as e:
            report.reasons.append(f"❌ Demo detection error: {str(e)}")
            return True  # Err on side of caution
            
    def _detect_synthetic_data(self, data: Dict, report: ValidationReport) -> bool:
        """Detect artificially generated/synthetic data"""
        try:
            data_str = json.dumps(data, default=str).lower()
            
            # Check for synthetic indicators
            for indicator in self.fake_signatures.SYNTHETIC_INDICATORS:
                if indicator in data_str:
                    report.reasons.append(f"❌ SYNTHETIC DATA: '{indicator}' found")
                    return True
                    
            # Check for mathematical generation patterns
            if 'random' in data_str or 'generated' in data_str or 'math.' in data_str:
                report.reasons.append("❌ SYNTHETIC: Mathematical generation detected")
                return True
                
            # Check for placeholder values
            placeholder_values = ['placeholder', 'dummy', 'example', 'sample', 'test', 'null', 'undefined']
            for field, value in data.items():
                if str(value).lower() in placeholder_values:
                    report.reasons.append(f"❌ PLACEHOLDER value in {field}: {value}")
                    return True
                    
            return False
            
        except Exception as e:
            report.reasons.append(f"❌ Synthetic detection error: {str(e)}")
            return True  # Err on side of caution
            
    def _detect_fake_patterns(self, data: Dict, report: ValidationReport) -> bool:
        """Detect fake price/data patterns"""
        try:
            # Check price fields for fake patterns
            price_fields = ['price', 'bid', 'ask', 'open', 'high', 'low', 'close', 'entry_price', 'exit_price']
            
            for field in price_fields:
                if field in data:
                    price_str = str(data[field])
                    
                    # Check against fake price patterns
                    for pattern in self.fake_signatures.FAKE_PRICE_PATTERNS:
                        if re.search(pattern, price_str):
                            report.reasons.append(f"❌ FAKE PRICE pattern in {field}: {price_str}")
                            return True
                            
                    # Check for obviously fake prices
                    try:
                        price = float(price_str)
                        if price == 0.0 or price < 0:
                            report.reasons.append(f"❌ INVALID price in {field}: {price}")
                            return True
                        if price > 100000:  # Unreasonably high price
                            report.reasons.append(f"❌ UNREALISTIC price in {field}: {price}")
                            return True
                    except (ValueError, TypeError):
                        pass
                        
            return False
            
        except Exception as e:
            report.reasons.append(f"❌ Fake pattern detection error: {str(e)}")
            return True  # Err on side of caution
            
    def _validate_timestamps(self, data: Dict, report: ValidationReport) -> bool:
        """Validate timestamps are recent and realistic"""
        try:
            now = time.time()
            timestamp_fields = ['timestamp', 'time', 'created_at', 'updated_at', 'generated_at']
            
            for field in timestamp_fields:
                if field in data:
                    try:
                        ts = float(data[field])
                        
                        # Check if timestamp is too old (more than 1 hour)
                        age = now - ts
                        if age > 3600:  # 1 hour
                            report.warnings.append(f"⚠️ OLD timestamp in {field}: {age:.0f}s old")
                            
                        # Check if timestamp is too old (more than 24 hours) - FAIL
                        if age > 86400:  # 24 hours
                            report.reasons.append(f"❌ STALE timestamp in {field}: {age:.0f}s old")
                            return False
                            
                        # Check if timestamp is from the future
                        if ts > now + 60:  # More than 1 minute in future
                            report.reasons.append(f"❌ FUTURE timestamp in {field}: {ts}")
                            return False
                            
                    except (ValueError, TypeError):
                        report.warnings.append(f"⚠️ Invalid timestamp format in {field}: {data[field]}")
                        
            return True
            
        except Exception as e:
            report.reasons.append(f"❌ Timestamp validation error: {str(e)}")
            return False
            
    def _validate_data_integrity(self, data: Dict, report: ValidationReport) -> bool:
        """Validate data integrity and completeness"""
        try:
            # Check for obviously corrupted data
            if not data or len(data) == 0:
                report.reasons.append("❌ EMPTY data")
                return False
                
            # Check for required fields based on data type
            if 'signal_id' in data:
                # Signal data validation
                required = ['symbol', 'direction', 'entry_price']
                missing = [f for f in required if f not in data]
                if missing:
                    report.reasons.append(f"❌ Missing signal fields: {missing}")
                    return False
                    
            if 'ticket' in data:
                # Trade data validation
                required = ['symbol', 'result']
                missing = [f for f in required if f not in data]
                if missing:
                    report.reasons.append(f"❌ Missing trade fields: {missing}")
                    return False
                    
            # Check for data type consistency
            for field, value in data.items():
                if value is None:
                    report.warnings.append(f"⚠️ Null value in {field}")
                elif isinstance(value, str) and len(value) == 0:
                    report.warnings.append(f"⚠️ Empty string in {field}")
                    
            return True
            
        except Exception as e:
            report.reasons.append(f"❌ Integrity validation error: {str(e)}")
            return False
            
    def _validate_prices(self, data: Dict, report: ValidationReport) -> bool:
        """Validate price data is realistic"""
        try:
            price_fields = ['price', 'bid', 'ask', 'open', 'high', 'low', 'close']
            
            for field in price_fields:
                if field in data:
                    try:
                        price = float(data[field])
                        
                        # Basic price sanity checks
                        if price <= 0:
                            report.reasons.append(f"❌ Non-positive price in {field}: {price}")
                            return False
                            
                        if price > 1000000:  # Million+ prices are suspicious
                            report.reasons.append(f"❌ Unrealistic high price in {field}: {price}")
                            return False
                            
                        # Check for suspiciously round numbers
                        if price == round(price, 0) and price > 1:  # Whole numbers > 1 are suspicious for FX
                            report.warnings.append(f"⚠️ Round price in {field}: {price}")
                            
                    except (ValueError, TypeError):
                        report.reasons.append(f"❌ Invalid price format in {field}: {data[field]}")
                        return False
                        
            # Check bid/ask spread if both present
            if 'bid' in data and 'ask' in data:
                try:
                    bid = float(data['bid'])
                    ask = float(data['ask'])
                    spread = ask - bid
                    
                    if spread <= 0:
                        report.reasons.append(f"❌ Invalid spread: bid={bid}, ask={ask}")
                        return False
                        
                    if spread > bid * 0.1:  # Spread > 10% of bid is suspicious
                        report.reasons.append(f"❌ Unrealistic spread: {spread:.5f}")
                        return False
                        
                except (ValueError, TypeError):
                    report.reasons.append("❌ Invalid bid/ask format")
                    return False
                    
            return True
            
        except Exception as e:
            report.reasons.append(f"❌ Price validation error: {str(e)}")
            return False
            
    def _log_validation_result(self, report: ValidationReport, source: str, context: str):
        """Log validation results"""
        try:
            if report.result != ValidationResult.VALID_REAL:
                # Log all rejections
                logger.error(f"❌ DATA REJECTED: {report.result.value}")
                logger.error(f"❌ Source: {source} | Context: {context}")
                logger.error(f"❌ Reasons: {', '.join(report.reasons)}")
                
                # Log to separate rejection file
                rejection_entry = {
                    'timestamp': report.timestamp,
                    'datetime': datetime.now().isoformat(),
                    'result': report.result.value,
                    'source': source,
                    'context': context,
                    'reasons': report.reasons,
                    'warnings': report.warnings,
                    'data_hash': report.data_hash,
                    'confidence': report.confidence
                }
                
                with open('/root/HydraX-v2/logs/data_rejections.jsonl', 'a') as f:
                    f.write(json.dumps(rejection_entry) + '\n')
                    
            else:
                # Log successful validations (less verbose)
                logger.debug(f"✅ DATA VALIDATED: {source}")
                if report.warnings:
                    logger.warning(f"⚠️ Warnings: {', '.join(report.warnings)}")
                    
        except Exception as e:
            logger.error(f"❌ Error logging validation result: {str(e)}")
            
    def get_validation_stats(self) -> Dict:
        """Get comprehensive validation statistics"""
        total = self.validation_stats['total_validations']
        blocked = self.validation_stats['fake_data_blocked']
        
        return {
            **self.validation_stats,
            'rejection_rate': (blocked / total * 100) if total > 0 else 0,
            'validation_rate': ((total - blocked) / total * 100) if total > 0 else 0,
            'uptime_seconds': time.time() - self.validation_stats['start_time'],
            'fake_data_protection': True,
            'real_data_only': True
        }

# Global validator instance
_validator = None

def get_data_validator() -> RealDataValidator:
    """Get or create singleton validator"""
    global _validator
    if not _validator:
        _validator = RealDataValidator()
    return _validator

def validate_real_data(data: Any, source: str = "UNKNOWN", context: str = "") -> ValidationReport:
    """Convenience function for data validation"""
    validator = get_data_validator()
    return validator.validate_data(data, source, context)

def is_real_data(data: Any, source: str = "UNKNOWN") -> bool:
    """Quick check if data is real (not fake/demo/synthetic)"""
    report = validate_real_data(data, source)
    return report.result == ValidationResult.VALID_REAL

if __name__ == "__main__":
    # Test the validator
    validator = get_data_validator()
    
    logger.info("=" * 60)
    logger.info("🛡️ REAL DATA VALIDATION LAYER")
    logger.info("=" * 60)
    logger.info("🚨 ZERO TOLERANCE for fake/synthetic/demo data")
    logger.info("💰 Protecting real money with strict validation")
    logger.info("⚠️ Better to reject good data than accept fake data")
    logger.info("=" * 60)
    
    # Test cases
    test_cases = [
        # Real-looking data
        {
            'data': {'symbol': 'EURUSD', 'bid': 1.08234, 'ask': 1.08237, 'timestamp': time.time()},
            'source': 'BROKER_API_OANDA',
            'expected': ValidationResult.VALID_REAL
        },
        # Demo account data
        {
            'data': {'account': 'MetaQuotes-Demo', 'balance': 10000, 'timestamp': time.time()},
            'source': 'UNKNOWN',
            'expected': ValidationResult.INVALID_DEMO
        },
        # Fake price patterns
        {
            'data': {'symbol': 'EURUSD', 'price': 1.00000, 'timestamp': time.time()},
            'source': 'UNKNOWN',
            'expected': ValidationResult.INVALID_FAKE
        },
        # Synthetic data
        {
            'data': {'value': 'random_generated_data', 'source': 'simulation', 'timestamp': time.time()},
            'source': 'random.random',
            'expected': ValidationResult.INVALID_SYNTHETIC
        }
    ]
    
    logger.info("🧪 Running validation tests...")
    
    passed = 0
    for i, test in enumerate(test_cases, 1):
        result = validator.validate_data(test['data'], test['source'])
        expected = test['expected']
        
        if result.result == expected:
            logger.info(f"✅ Test {i}: PASS - {expected.value}")
            passed += 1
        else:
            logger.error(f"❌ Test {i}: FAIL - Expected {expected.value}, got {result.result.value}")
            
    logger.info(f"📊 Tests passed: {passed}/{len(test_cases)}")
    
    # Show final stats
    stats = validator.get_validation_stats()
    logger.info(f"📊 Validation Statistics:")
    logger.info(f"   Total validations: {stats['total_validations']}")
    logger.info(f"   Fake data blocked: {stats['fake_data_blocked']}")
    logger.info(f"   Rejection rate: {stats['rejection_rate']:.1f}%")