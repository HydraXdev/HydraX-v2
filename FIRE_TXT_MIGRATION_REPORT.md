# Fire.txt Migration Report

Generated: 2025-08-01T01:43:30.699214

## Summary

Total references found: 115

- Write operations: 4

- Read operations: 0

- Path references: 14

- Documentation: 53

- Comments: 10

- Other: 34


## Critical Migrations Required

These write operations need immediate migration to ZMQ:


### /root/HydraX-v2/zmq_fire_integration.py:109
```python
with open(fire_path, 'w') as f:
```
**Migration**: Replace with `execute_bitten_trade()` from zmq_bitten_controller


### /root/HydraX-v2/audit_fire_txt_references.py:178
```python
report.append("    with open(fire_path, 'w') as f:\n")
```
**Migration**: Replace with `execute_bitten_trade()` from zmq_bitten_controller


### /root/HydraX-v2/ZMQ_BRIDGE_DEPLOYMENT.md:123
```python
with open(f"/mt5/user_{user_id}/fire.txt", "w") as f:
```
**Migration**: Replace with `execute_bitten_trade()` from zmq_bitten_controller


### /root/HydraX-v2/src/toc/bridge_terminal_server.py:256
```python
with open(fire_file_path, 'w') as f:
```
**Migration**: Replace with `execute_bitten_trade()` from zmq_bitten_controller


## Read Operations to Remove

These read operations should be replaced with telemetry monitoring:


## Migration Strategy

1. **Phase 1**: Add ZMQ alongside fire.txt (dual-write)

2. **Phase 2**: Verify ZMQ working, monitor both channels

3. **Phase 3**: Stop reading fire.txt, only write for compatibility

4. **Phase 4**: Remove all fire.txt writes


## Feature Flag Implementation

```python

USE_ZMQ = os.getenv('USE_ZMQ', 'false').lower() == 'true'



if USE_ZMQ:

    from zmq_bitten_controller import execute_bitten_trade

    result = execute_bitten_trade(signal_data)

else:

    # Legacy fire.txt method

    with open(fire_path, 'w') as f:

        json.dump(signal_data, f)

```
