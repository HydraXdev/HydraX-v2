# TCS++ and Stealth Protocol Test Suite

Comprehensive test suite for the TCS++ scoring engine and stealth protocol implementation.

## Test Structure

### Unit Tests

1. **test_tcs_plus_engine.py**
   - TCS++ scoring accuracy tests
   - Trade classification tests
   - Component function tests
   - Edge case handling
   - Performance benchmarks

2. **test_stealth_protocol_comprehensive.py**
   - Stealth protocol initialization
   - Entry delay functionality
   - Lot size jitter
   - TP/SL offset
   - Ghost skip logic
   - Volume cap management
   - Execution shuffle
   - Full stealth application

### Integration Tests

3. **integration/test_tcs_stealth_integration.py**
   - TCS++ and stealth protocol integration
   - Fire mode integration
   - Edge cases and boundaries
   - Performance under integrated load

### Performance Tests

4. **test_performance_benchmarks.py**
   - TCS++ performance benchmarks
   - Stealth protocol performance
   - Integrated system performance
   - Scalability tests
   - Latency percentiles

## Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Specific Test Suite
```bash
python tests/run_all_tests.py --suite test_tcs_plus_engine.py
```

### Run with Verbose Output
```bash
python tests/run_all_tests.py --verbose
```

### Validate Test Files
```bash
python tests/validate_tests.py
```

### Using pytest Directly
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_tcs_plus_engine.py -v

# Run specific test class
pytest tests/test_tcs_plus_engine.py::TestTCSScoringAccuracy -v

# Run specific test method
pytest tests/test_tcs_plus_engine.py::TestTCSScoringAccuracy::test_perfect_trade_conditions -v

# Run with coverage
pytest tests/ --cov=core --cov=src.bitten_core --cov-report=html
```

## Test Coverage

The test suite covers:

### TCS++ Engine
- ✓ Scoring accuracy with various market conditions
- ✓ Trade classification (Hammer, Shadow Strike, Scalp)
- ✓ All component scoring functions
- ✓ Edge cases and boundary conditions
- ✓ Performance benchmarks

### Stealth Protocol
- ✓ Entry delay randomization
- ✓ Lot size jitter
- ✓ TP/SL offset calculations
- ✓ Ghost skip functionality
- ✓ Volume cap enforcement
- ✓ Execution shuffle
- ✓ Different stealth levels

### Integration
- ✓ TCS score to stealth level mapping
- ✓ Fire mode compatibility
- ✓ Concurrent execution scenarios
- ✓ High-frequency trading scenarios
- ✓ Market maker scenarios
- ✓ Scalping scenarios

### Performance
- ✓ Single operation latency
- ✓ Batch processing throughput
- ✓ Concurrent load handling
- ✓ Memory efficiency
- ✓ CPU usage optimization
- ✓ Scalability testing

## Performance Requirements

### TCS++ Engine
- Single scoring: < 0.1ms average, < 1ms max
- Batch scoring: > 1000 operations/second
- Memory usage: < 100MB for 10,000 signals

### Stealth Protocol
- Single application: < 1ms average, < 10ms max
- Volume cap checks: > 10,000 operations/second
- Shuffle performance: Linear time complexity

### Integrated System
- Full pipeline: > 1000 signals/second
- Latency percentiles:
  - P50: < 1ms
  - P90: < 2ms
  - P95: < 5ms
  - P99: < 10ms

## Test Reports

Test reports are saved to `tests/reports/` with:
- Detailed JSON report: `test_report_YYYYMMDD_HHMMSS.json`
- Summary text file: `test_summary_YYYYMMDD_HHMMSS.txt`

## Dependencies

- pytest
- pytest-cov (optional, for coverage)
- psutil (for performance monitoring)

Install test dependencies:
```bash
pip install pytest pytest-cov psutil
```

## Continuous Integration

The test suite is designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    python tests/run_all_tests.py
```

Exit codes:
- 0: All tests passed
- 1: One or more tests failed