# Core Module Tests
import pytest
from src.core.modules.bitmode import run_bitmode
from src.core.modules.commandermode import run_commander

def test_bitmode_initialization():
    """Test that bitmode initializes without errors"""
    # This would normally capture stdout and verify the message
    try:
        run_bitmode()
        assert True
    except Exception as e:
        pytest.fail(f"Bitmode failed to initialize: {e}")

def test_commander_initialization():
    """Test that commander mode initializes without errors"""
    try:
        run_commander()
        assert True
    except Exception as e:
        pytest.fail(f"Commander mode failed to initialize: {e}")

# TODO: Add more comprehensive tests for:
# - Trading logic
# - Risk management
# - API integrations
# - Error handling