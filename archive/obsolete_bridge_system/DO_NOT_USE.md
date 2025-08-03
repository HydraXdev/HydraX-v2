# ⚠️ OBSOLETE BRIDGE SYSTEM - DO NOT USE ⚠️

## CRITICAL WARNING
These files are from an obsolete bridge system that has been decommissioned.

## WHY ARCHIVED
- The bridge system was sending HTTP traffic to ZMQ ports
- Interfered with the modern ZMQ-based market data pipeline
- Used deprecated AWS bridge architecture
- No longer compatible with current BITTEN infrastructure

## FILES ARCHIVED
- bridge_fortress_daemon.py - Old monitoring daemon
- production_bridge_tunnel.py - HTTP-based bridge tunnel
- bridge_troll_*.py - Various bridge troll components
- bridge_troll.service - Systemd service (disabled)

## DO NOT
- ❌ Run any of these scripts
- ❌ Re-enable the systemd services
- ❌ Import from these modules
- ❌ Reference this architecture in new code

## CURRENT SYSTEM
The modern system uses:
- ZMQ-based communication (ports 5555-5557)
- Direct EA integration via ZMQ client
- No HTTP bridge layers
- No AWS dependencies

Date Archived: July 31, 2025
Reason: Obsolete and interfering with ZMQ infrastructure