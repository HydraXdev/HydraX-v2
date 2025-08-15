# MT5 Farm Setup Guide - 5 Master Templates

## 🎯 Overview: 5 Master MT5 Instances for Cloning

You need to set up these 5 master instances, each configured differently:

### 1. **Coinexx Live Master** (Production Trading)
- **Broker**: Coinexx
- **Account Type**: Live/Real
- **Purpose**: Real money trading for paid tiers
- **Clone Target**: 50-100 instances
- **Risk Settings**: Conservative (1-2% per trade)

### 2. **Forex.com Live Master** (Production Trading)  
- **Broker**: Forex.com
- **Account Type**: Live/Real
- **Purpose**: Alternative broker for risk distribution
- **Clone Target**: 50-100 instances
- **Risk Settings**: Conservative (1-2% per trade)

### 3. **Forex.com Demo Master** (Testing/Development)
- **Broker**: Forex.com
- **Account Type**: Demo
- **Purpose**: Testing strategies, new users trials
- **Clone Target**: 50-100 instances
- **Risk Settings**: Moderate (2-5% per trade)

### 4. **Coinexx Demo Master** (Testing/Development)
- **Broker**: Coinexx
- **Account Type**: Demo
- **Purpose**: Alternative demo environment
- **Clone Target**: 50-100 instances
- **Risk Settings**: Moderate (2-5% per trade)

### 5. **Generic Demo Master** (Press Pass - No Login)
- **Broker**: MetaQuotes Demo
- **Account Type**: Automatic Demo
- **Purpose**: Press Pass 7-day trials
- **Clone Target**: 100-200 instances
- **Risk Settings**: Aggressive (5-10% per trade)
- **Special**: No login required, auto-provisions demo account

## 📋 Setup Steps for Each Master

### Step 1: Install MT5 Terminals
```bash
# Suggested directory structure:
C:\MT5_Farm\Masters\
├── Coinexx_Live\
├── Forex_Live\
├── Forex_Demo\
├── Coinexx_Demo\
└── Generic_Demo\
```

### Step 2: Configure Each Master

#### For Broker-Specific Masters (1-4):
1. Install MT5 from broker's website
2. Login with appropriate credentials
3. File → Login to Trade Account
4. Save login credentials for cloning

#### For Generic Demo Master (5):
1. Install standard MT5 from metaquotes.net
2. File → Open Demo Account
3. Choose "MetaQuotes-Demo" server
4. Let it auto-create account
5. **DO NOT** save password (each clone gets new account)

### Step 3: EA Configuration per Master

Set different magic numbers and risk settings:

```
Coinexx Live:    Magic: 10001-10100, Risk: 1%
Forex Live:      Magic: 20001-20100, Risk: 1%
Forex Demo:      Magic: 30001-30100, Risk: 3%
Coinexx Demo:    Magic: 40001-40100, Risk: 3%
Generic Demo:    Magic: 50001-50200, Risk: 5%
```

### Step 4: Attach EA to Charts

For each master, open these pairs and attach EA:
1. EURUSD
2. GBPUSD
3. USDJPY
4. USDCAD
5. GBPJPY
6. AUDUSD
7. NZDUSD
8. EURGBP
9. USDCHF
10. EURJPY

### Step 5: Configure EA Settings

**Live Masters (Coinexx/Forex Live):**
- Risk per trade: 1%
- Max daily loss: 5%
- Enable all safety features
- Conservative mode ON

**Demo Masters (Coinexx/Forex Demo):**
- Risk per trade: 3%
- Max daily loss: 10%
- Standard safety features
- Normal mode

**Generic Demo (Press Pass):**
- Risk per trade: 5%
- Max daily loss: 20%
- Minimal restrictions
- Aggressive mode
- Auto-accept all trades

## 🔄 Cloning Process

Once masters are set up:

```powershell
# Example cloning script
$masters = @{
    "Coinexx_Live" = 67
    "Forex_Live" = 67
    "Forex_Demo" = 66
    "Coinexx_Demo" = 66
    "Generic_Demo" = 134
}

foreach ($master in $masters.Keys) {
    $count = $masters[$master]
    for ($i = 1; $i -le $count; $i++) {
        # Copy master to clone directory
        Copy-Item "C:\MT5_Farm\Masters\$master" "C:\MT5_Farm\Clones\${master}_$i" -Recurse
        
        # Modify config for unique instance
        # Update magic number
        # Update installation ID
    }
}
```

## 🎯 User Assignment Logic

```python
def assign_mt5_instance(user_tier, user_id):
    if user_tier == "PRESS_PASS":
        # Assign from Generic Demo pool
        return get_available_instance("Generic_Demo")
    
    elif user_tier in ["NIBBLER", "FANG"]:
        # Prefer demo, fallback to live with restrictions
        instance = get_available_instance("Forex_Demo")
        if not instance:
            instance = get_available_instance("Coinexx_Demo")
        return instance
    
    elif user_tier in ["COMMANDER"]:
        # Assign from live pools
        if user_id % 2 == 0:
            return get_available_instance("Forex_Live")
        else:
            return get_available_instance("Coinexx_Live")
```

## 📊 Resource Planning

**Total Instances**: 400 (5 masters × 80 average clones)

**Resource Requirements per Instance**:
- RAM: ~200MB
- CPU: ~1-2%
- Disk: ~500MB

**Total Server Requirements**:
- RAM: 80GB minimum
- CPU: 32+ cores recommended
- Disk: 200GB SSD
- Network: 1Gbps minimum

## 🔐 Security Considerations

1. **Live Masters**: 
   - Isolated network segment
   - Encrypted credentials
   - Read-only access for clones

2. **Demo Masters**:
   - Less restrictive
   - Can share network

3. **Generic Demo**:
   - Most permissive
   - Auto-cleanup after 7 days
   - No saved credentials

## ✅ Checklist

- [ ] Install 5 MT5 terminals in master directories
- [ ] Login to 4 broker accounts (skip Generic)
- [ ] Compile and attach EA to all charts
- [ ] Configure unique magic numbers
- [ ] Set appropriate risk levels
- [ ] Test one clone from each master
- [ ] Create cloning script
- [ ] Set up monitoring for all instances

Once these 5 masters are properly configured, you can clone them hundreds of times for your user base!