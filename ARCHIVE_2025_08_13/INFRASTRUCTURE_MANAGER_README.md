# Infrastructure Manager - Singleton Pattern Implementation

## Overview

The Infrastructure Manager ensures that only one instance of each critical infrastructure component exists throughout the application lifecycle. This prevents multiple instantiations that could lead to resource conflicts, connection issues, and unpredictable behavior.

## Key Features

1. **Thread-Safe Singleton Pattern**: Uses locks to ensure thread-safe access
2. **Lazy Loading**: Components are only created when first requested
3. **Centralized Management**: All infrastructure components managed from one place
4. **Circuit Breaker Protection**: Prevents infinite recursion and cascade failures

## Usage

### Import the Infrastructure Manager

```python
from src.bitten_core.infrastructure_manager import (
    get_aws_mt5_bridge,
    get_bulletproof_mt5_infrastructure,
    get_infrastructure_status
)
```

### Get AWS MT5 Bridge Instance

```python
# This will always return the same instance
bridge = get_aws_mt5_bridge()

# Use the bridge
market_data = bridge.get_market_data("EURUSD")
```

### Get Bulletproof Infrastructure Instance

```python
# This will always return the same instance
infra = get_bulletproof_mt5_infrastructure()

# Use the infrastructure
data = infra.get_mt5_data_bulletproof("GBPUSD")
```

### Check Infrastructure Status

```python
status = get_infrastructure_status()
print(status)
# Output:
# {
#     'bulletproof_mt5': 'initialized',
#     'aws_mt5_bridge': 'initialized',
#     'bulletproof_details': {...},
#     'aws_bridge_connected': True
# }
```

## Implementation Details

### Files Modified

1. **`/root/HydraX-v2/src/bitten_core/infrastructure_manager.py`**
   - New file containing the singleton manager
   - Manages instances of BulletproofMT5Infrastructure and AWSMT5Bridge
   - Thread-safe implementation with locks

2. **`/root/HydraX-v2/aws_mt5_bridge.py`**
   - Updated to use infrastructure manager instead of creating its own instance
   - Removed class-level singleton pattern in favor of centralized management

3. **`/root/HydraX-v2/AUTHORIZED_SIGNAL_ENGINE.py`**
   - Updated to get AWS bridge instance from infrastructure manager
   - Ensures only one bridge instance exists across all signal engines

## Benefits

1. **Resource Efficiency**: Only one connection pool to AWS servers
2. **Consistency**: All components share the same infrastructure instances
3. **Easier Debugging**: Centralized logging and status reporting
4. **Thread Safety**: Multiple threads can safely access the same instances
5. **Circuit Breaker**: Prevents cascade failures and infinite recursion

## Circuit Breaker Protection

The infrastructure includes circuit breaker logic that:
- Opens after 3 consecutive failures
- Blocks attempts for 5 minutes when open
- Prevents infinite recursion with depth tracking
- Automatically resets after timeout period

## Testing

Run the test script to verify singleton behavior:

```bash
python3 test_infrastructure_manager.py
```

This will test:
- Singleton pattern correctness
- Thread-safe concurrent access
- Infrastructure status reporting
- Circuit breaker functionality

## Best Practices

1. Always use the convenience functions (`get_aws_mt5_bridge()`, etc.)
2. Never create instances directly with `new` or constructor calls
3. Check infrastructure status before critical operations
4. Handle exceptions gracefully - infrastructure may be unavailable
5. Monitor logs for circuit breaker trips and connection issues