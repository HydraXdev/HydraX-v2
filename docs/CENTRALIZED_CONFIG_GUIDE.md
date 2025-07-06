# BITTEN Centralized Trading Pairs Configuration

## 🎯 Overview

The new centralized configuration system provides a **single source of truth** for all trading pairs, eliminating scattered definitions across the codebase.

## 📁 Configuration Files

### 1. **Main Configuration**: `/config/trading_pairs.yml`
- **Single source of truth** for all trading pairs
- Contains specifications, TCS requirements, and categories
- Easy to modify and maintain

### 2. **Configuration Manager**: `/src/bitten_core/config_manager.py`
- Python interface to the YAML configuration
- Provides validation and convenience methods
- Handles compatibility with existing code

## 🔧 Quick Start

### Using the Configuration Manager

```python
from bitten_core.config_manager import get_trading_config

# Get the global configuration instance
config = get_trading_config()

# Get all supported pairs
all_pairs = config.get_supported_symbols()
print(f"Supported pairs: {all_pairs}")

# Check if a pair is supported
is_supported = config.is_supported_pair('GBPUSD')
print(f"GBPUSD supported: {is_supported}")

# Get TCS requirement for a pair
tcs_req = config.get_pair_tcs_requirement('AUDUSD')
print(f"AUDUSD TCS requirement: {tcs_req}")

# Validate TCS for a pair
is_valid, msg = config.validate_tcs_for_pair('AUDUSD', 90)
print(f"AUDUSD with 90% TCS: {is_valid} - {msg}")
```

### Current Configuration

**Core Pairs (5)**: Use standard tier TCS requirements
- GBPUSD, EURUSD, USDJPY, GBPJPY, USDCAD

**Extra Pairs (7)**: Require 85% minimum TCS for safety
- AUDUSD, NZDUSD, AUDJPY, EURJPY, EURGBP, GBPCHF, USDCHF

**No Metals**: XAUUSD and XAGUSD completely removed

## 🔄 Migration Status

### ✅ **Updated Files**:
1. **`config/trading_pairs.yml`** - New centralized configuration
2. **`src/bitten_core/config_manager.py`** - Configuration management class
3. **`src/bitten_core/fire_modes.py`** - Now loads TCS requirements from config
4. **`src/bitten_core/master_filter.py`** - Updated to pass pair parameter for TCS validation
5. **`config/mt5_bridge.json`** - Updated symbol mappings
6. **`src/bitten_core/heat_map_analytics.py`** - Removed metals, updated tracked pairs
7. **`src/bitten_core/risk_management.py`** - Added extra pairs, removed metals

### 🔄 **Partially Updated Files**:
1. **`src/bitten_core/fire_router.py`** - Contains hardcoded PAIRS dict (legacy compatibility)
2. **`src/bitten_core/arcade_filter.py`** - Uses hardcoded pairs list
3. **`src/bitten_core/sniper_filter.py`** - Uses hardcoded pairs list

## 🚀 Adding New Pairs

### Step 1: Update YAML Configuration
Edit `/config/trading_pairs.yml`:

```yaml
trading_pairs:
  extra_pairs:
    AUDCAD:  # New pair
      pip_value: 0.0001
      min_volume: 0.01
      max_volume: 100.0
      spread_limit: 3.5
      session_hours: 
        - "13:00-22:00"
      volatility_filter: true
      contract_size: 100000
      min_lot: 0.01
      max_lot: 100
      tcs_requirement: 85  # 85% minimum TCS
      category: "cross"
      description: "Australian Dollar vs Canadian Dollar"
```

### Step 2: Update MT5 Mappings (if needed)
Add to `mt5_mappings` section:

```yaml
mt5_mappings:
  AUDCAD: "AUDCAD"
```

### Step 3: Reload Configuration
```python
from bitten_core.config_manager import reload_trading_config
config = reload_trading_config()
```

## 🎛️ Configuration Sections

### Trading Pairs Structure
```yaml
trading_pairs:
  core_pairs:      # Standard tier TCS requirements
    SYMBOL:
      pip_value: 0.0001
      tcs_requirement: null
      # ... other specs
  
  extra_pairs:     # 85% minimum TCS
    SYMBOL:
      tcs_requirement: 85
      # ... other specs
```

### Strategy Assignments
```yaml
strategy_assignments:
  arcade_strategy:
    allowed_pairs: [GBPUSD, EURUSD, ...]
    min_tcs: 65
  
  sniper_strategy:
    allowed_pairs: [GBPUSD, EURUSD, ...]
    min_tcs: 75
```

### Session Definitions
```yaml
sessions:
  london:
    hours: "03:00-11:00"
    optimal_pairs: [GBPUSD, EURGBP, ...]
    bonus_multiplier: 1.2
```

## 🔍 Validation Methods

### Pair Validation
```python
# Check if pair is supported
is_supported = config.is_supported_pair('GBPUSD')

# Validate TCS requirements
is_valid, msg = config.validate_tcs_for_pair('AUDUSD', 85)

# Check strategy compatibility
is_valid, msg = config.validate_pair_for_strategy('GBPUSD', 'arcade_strategy')
```

### Get Pair Information
```python
# Get specific pair details
pair_spec = config.get_pair_spec('GBPUSD')
print(f"Pip value: {pair_spec.pip_value}")
print(f"TCS requirement: {pair_spec.tcs_requirement}")

# Get strategy-specific pairs
arcade_pairs = config.get_strategy_pairs('arcade_strategy')
```

## 📈 Benefits

### ✅ **Before (Scattered)**
- 7+ files to update for new pairs
- Inconsistent configurations
- Duplicate definitions
- Risk of errors

### ✅ **After (Centralized)**
- **Single file** to update: `trading_pairs.yml`
- **Consistent** specifications across all modules
- **Validation** built-in
- **Easy maintenance**

## 🧪 Testing

### Test Configuration Loading
```bash
python3 -c "
import yaml
config = yaml.safe_load(open('config/trading_pairs.yml'))
print('Core pairs:', list(config['trading_pairs']['core_pairs'].keys()))
print('Extra pairs:', list(config['trading_pairs']['extra_pairs'].keys()))
"
```

### Test Python Interface
```bash
python3 -c "
import sys; sys.path.append('src')
from bitten_core.config_manager import TradingPairsConfig
config = TradingPairsConfig()
print(f'Total pairs: {config.get_total_pairs_count()}')
print(f'AUDUSD TCS req: {config.get_pair_tcs_requirement(\"AUDUSD\")}')
"
```

## 🔧 Legacy Compatibility

The system provides backward compatibility methods:

```python
# Get pairs in old fire_router format
legacy_pairs = config.get_fire_router_pairs()

# Get TCS requirements in old format
legacy_tcs = config.get_pair_specific_tcs()

# Get risk management specs in old format
legacy_risk = config.get_risk_management_specs()
```

## 📝 Future Enhancements

1. **Dynamic Reloading**: Hot-reload configuration without restart
2. **Environment-Specific Configs**: Dev/staging/prod configurations
3. **Pair-Specific Strategies**: Different strategies per pair
4. **Advanced Validation**: Cross-validation with broker specifications
5. **API Integration**: Fetch pair specs from broker APIs

## 🚨 Important Notes

- **Always edit `trading_pairs.yml`** instead of hardcoded values
- **Restart the system** after configuration changes
- **Test thoroughly** after adding new pairs
- **Keep MT5 mappings** in sync with pair additions
- **Metals trading is disabled** (XAUUSD/XAGUSD removed)

## 🆘 Troubleshooting

### Configuration Not Loading
1. Check YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('config/trading_pairs.yml'))"`
2. Verify file path exists
3. Check file permissions

### Pair Not Recognized
1. Verify pair exists in `trading_pairs.yml`
2. Check spelling and case sensitivity
3. Restart the application

### TCS Validation Failing
1. Check `tcs_requirement` in configuration
2. Verify pair category (core vs extra)
3. Ensure TCS score meets minimum requirements

---

## 📞 Support

For questions about the centralized configuration system:
1. Check this documentation
2. Review `/config/trading_pairs.yml` for examples
3. Test with the provided Python scripts
4. Refer to `/src/bitten_core/config_manager.py` for advanced usage