#!/usr/bin/env python3
"""
Event Bus Schema Guard - Contract Validation
Validates execution.outcome.v1 events against frozen schema
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


class SchemaViolationError(Exception):
    """Raised when an event violates the schema contract"""

    pass


class EventBusSchemaGuard:
    def __init__(self):
        self.setup_logging()

        # FROZEN SCHEMA v1 - Do not modify without version bump
        self.execution_outcome_v1_schema = {
            "required_fields": ["trade_id", "result", "symbol", "pnl_pips", "schema_version"],
            "optional_fields": [
                "signal_id",
                "fire_id",
                "direction",
                "entry_price",
                "exit_price",
                "duration_minutes",
                "pattern_type",
                "confidence",
                "source",
            ],
            "field_types": {
                "trade_id": str,
                "result": str,
                "symbol": str,
                "pnl_pips": (int, float),
                "schema_version": int,
                "signal_id": (str, type(None)),
                "fire_id": (str, type(None)),
                "direction": (str, type(None)),
                "entry_price": (int, float, type(None)),
                "exit_price": (int, float, type(None)),
                "duration_minutes": (int, float, type(None)),
                "pattern_type": (str, type(None)),
                "confidence": (int, float, type(None)),
                "source": (str, type(None)),
            },
            "field_constraints": {
                "result": ["WIN", "LOSS"],
                "schema_version": [1],
                "direction": ["BUY", "SELL", None],
                "confidence": lambda x: x is None or (0 <= x <= 100),
                "pnl_pips": lambda x: isinstance(x, (int, float)),
            },
        }

        # FROZEN SCHEMA v1 - execution.confirmation.v1
        self.execution_confirmation_v1_schema = {
            "required_fields": ["fire_id", "status", "schema_version"],
            "optional_fields": [
                "ticket",
                "price",
                "target_uuid",
                "symbol",
                "direction",
                "lot_size",
                "sl",
                "tp",
                "message",
                "error_code",
                "execution_time",
            ],
            "field_types": {
                "fire_id": str,
                "status": str,
                "schema_version": int,
                "ticket": (int, type(None)),
                "price": (int, float, type(None)),
                "target_uuid": (str, type(None)),
                "symbol": (str, type(None)),
                "direction": (str, type(None)),
                "lot_size": (int, float, type(None)),
                "sl": (int, float, type(None)),
                "tp": (int, float, type(None)),
                "message": (str, type(None)),
                "error_code": (str, int, type(None)),
                "execution_time": (int, float, type(None)),
            },
            "field_constraints": {
                "status": ["FILLED", "FAILED", "CLOSED", "REJECTED", "PENDING"],
                "schema_version": lambda x: x == 1,
                "ticket": lambda x: x is None or x >= 0,
                "price": lambda x: x is None or x > 0,
            },
        }

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [SCHEMA_GUARD] %(levelname)s: %(message)s")
        self.logger = logging.getLogger(__name__)

    def validate_execution_outcome_v1(self, event_data: Dict[str, Any]) -> List[str]:
        """
        Validate execution.outcome.v1 event against frozen schema
        Returns list of violations (empty list = valid)
        """
        violations = []
        schema = self.execution_outcome_v1_schema

        # Check required fields
        for field in schema["required_fields"]:
            if field not in event_data:
                violations.append(f"Missing required field: {field}")

        # Check for unknown fields
        allowed_fields = set(schema["required_fields"] + schema["optional_fields"])
        for field in event_data.keys():
            if field not in allowed_fields:
                violations.append(f"Unknown field not in schema v1: {field}")

        # Check field types
        for field, expected_types in schema["field_types"].items():
            if field in event_data:
                value = event_data[field]
                if not isinstance(value, expected_types):
                    violations.append(
                        f"Field {field} has wrong type: {type(value).__name__}, expected {expected_types}"
                    )

        # Check field constraints
        for field, constraint in schema["field_constraints"].items():
            if field in event_data:
                value = event_data[field]
                if callable(constraint):
                    if not constraint(value):
                        violations.append(f"Field {field} violates constraint: {value}")
                elif isinstance(constraint, list):
                    if value not in constraint:
                        violations.append(f"Field {field} not in allowed values {constraint}: {value}")

        # Additional business logic validations
        if "trade_id" in event_data:
            trade_id = event_data["trade_id"]
            if not trade_id or len(trade_id.strip()) == 0:
                violations.append("trade_id cannot be empty")
            if len(trade_id) > 255:
                violations.append("trade_id too long (>255 chars)")

        if "result" in event_data and "pnl_pips" in event_data:
            result = event_data["result"]
            pnl = event_data["pnl_pips"]

            # Basic sanity check: WIN should have positive pnl, LOSS should have negative
            if result == "WIN" and pnl < 0:
                violations.append("WIN result with negative pnl_pips - data inconsistency")
            elif result == "LOSS" and pnl > 0:
                violations.append("LOSS result with positive pnl_pips - data inconsistency")

        return violations

    def validate_execution_confirmation_v1(self, event_data: Dict[str, Any]) -> List[str]:
        """
        Validate execution.confirmation.v1 event against frozen schema
        Returns list of violations (empty list = valid)
        """
        violations = []
        schema = self.execution_confirmation_v1_schema

        # Check required fields
        for field in schema["required_fields"]:
            if field not in event_data:
                violations.append(f"Missing required field: {field}")

        # Check for unknown fields
        allowed_fields = set(schema["required_fields"] + schema["optional_fields"])
        for field in event_data.keys():
            if field not in allowed_fields:
                violations.append(f"Unknown field not in schema v1: {field}")

        # Check field types
        for field, expected_types in schema["field_types"].items():
            if field in event_data:
                value = event_data[field]
                if not isinstance(value, expected_types):
                    violations.append(
                        f"Field {field} has wrong type: {type(value).__name__}, expected {expected_types}"
                    )

        # Check field constraints
        for field, constraint in schema["field_constraints"].items():
            if field in event_data:
                value = event_data[field]
                if callable(constraint):
                    if not constraint(value):
                        violations.append(f"Field {field} violates constraint: {value}")
                elif isinstance(constraint, list):
                    if value not in constraint:
                        violations.append(f"Field {field} not in allowed values {constraint}: {value}")

        # Additional business logic validations
        if "status" in event_data and "ticket" in event_data:
            status = event_data["status"]
            ticket = event_data["ticket"]

            # FILLED status should have a ticket number
            if status == "FILLED" and (ticket is None or ticket <= 0):
                violations.append("FILLED status should have valid ticket number")

            # FAILED/REJECTED status should not have ticket
            if status in ["FAILED", "REJECTED"] and ticket and ticket > 0:
                violations.append("FAILED/REJECTED status should not have ticket number")

        return violations

    def validate_event(self, event_type: str, event_data: Dict[str, Any], strict: bool = True) -> bool:
        """
        Main validation entry point
        Returns True if valid, False if invalid
        Raises SchemaViolationError in strict mode
        """
        violations = []

        if event_type == "execution.outcome.v1":
            violations = self.validate_execution_outcome_v1(event_data)
        elif event_type == "execution.confirmation.v1":
            violations = self.validate_execution_confirmation_v1(event_data)
        else:
            violations = [f"Unknown event type: {event_type}"]

        if violations:
            violation_msg = f"Schema violations for {event_type}: {violations}"
            self.logger.error(violation_msg)

            if strict:
                raise SchemaViolationError(violation_msg)
            return False

        return True

    def create_dlq_event(self, event_type: str, event_data: Dict[str, Any], violations: List[str]) -> Dict[str, Any]:
        """Create a dead letter queue event for failed validation"""
        return {
            "dlq_event_type": "schema_violation",
            "original_event_type": event_type,
            "original_data": event_data,
            "violations": violations,
            "timestamp": datetime.now().isoformat(),
            "schema_version": 1,
        }

    def safe_emit_with_validation(self, event_type: str, event_data: Dict[str, Any], emit_func, dlq_func=None) -> bool:
        """
        Safely emit event with validation
        On validation failure, sends to DLQ instead of main stream
        """
        try:
            if self.validate_event(event_type, event_data, strict=False):
                # Valid - emit to main stream
                return emit_func(event_type, event_data)
            else:
                # Invalid - send to DLQ if available
                if dlq_func:
                    violations = []
                    if event_type == "execution.outcome.v1":
                        violations = self.validate_execution_outcome_v1(event_data)

                    dlq_event = self.create_dlq_event(event_type, event_data, violations)
                    dlq_func("schema_violation", dlq_event)

                self.logger.warning(f"Event sent to DLQ due to schema violations: {event_type}")
                return False

        except Exception as e:
            self.logger.error(f"Schema guard error: {e}")
            return False


# Contract test functions for CI
def test_execution_outcome_v1_valid():
    """Test valid execution.outcome.v1 event"""
    guard = EventBusSchemaGuard()

    valid_event = {
        "trade_id": "fire:TEST_123",
        "result": "WIN",
        "symbol": "EURUSD",
        "pnl_pips": 15.5,
        "schema_version": 1,
        "signal_id": "ELITE_TEST_123",
        "direction": "BUY",
        "confidence": 85.0,
    }

    assert guard.validate_event("execution.outcome.v1", valid_event) == True
    print("✅ Valid event test passed")


def test_execution_outcome_v1_invalid():
    """Test invalid execution.outcome.v1 event"""
    guard = EventBusSchemaGuard()

    invalid_event = {
        "trade_id": "",  # Empty trade_id
        "result": "MAYBE",  # Invalid result value
        "symbol": "EURUSD",
        "pnl_pips": "not_a_number",  # Wrong type
        "schema_version": 2,  # Wrong version
        "unknown_field": "should_fail",  # Unknown field
    }

    assert guard.validate_event("execution.outcome.v1", invalid_event, strict=False) == False
    print("✅ Invalid event test passed")


def test_business_logic_validation():
    """Test business logic constraints"""
    guard = EventBusSchemaGuard()

    inconsistent_event = {
        "trade_id": "fire:TEST_456",
        "result": "WIN",
        "symbol": "GBPUSD",
        "pnl_pips": -10.0,  # WIN with negative pips - should fail
        "schema_version": 1,
    }

    violations = guard.validate_execution_outcome_v1(inconsistent_event)
    assert len(violations) > 0
    assert any("data inconsistency" in v for v in violations)
    print("✅ Business logic validation test passed")


if __name__ == "__main__":
    # Run contract tests
    test_execution_outcome_v1_valid()
    test_execution_outcome_v1_invalid()
    test_business_logic_validation()
    print("🎉 All schema guard tests passed!")
