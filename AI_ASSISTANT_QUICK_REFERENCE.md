# 🤖 AI Assistant Quick Reference Guide

**For Future AI Assistance on HydraX-v2 BITTEN System**

---

## 🎯 **CRITICAL: ALWAYS READ THESE FIRST**

### **📋 PRIMARY SOURCES OF TRUTH**
1. **CLAUDE.md** - Current system status and development log
2. **TECHNICAL_DOCS_INDEX.md** - Navigation to all technical specifications
3. **BITTEN_TECHNICAL_SPECIFICATION.md** - Master system specification
4. **config/trading_pairs.yml** - Current trading configuration (v3.0.0)

### **🔧 CURRENT SYSTEM STATE (July 9, 2025)**
- **Trading Pairs**: 10 active pairs (EURUSD, GBPUSD, USDJPY, USDCAD, GBPJPY, AUDUSD, NZDUSD, EURGBP, USDCHF, EURJPY)
- **Self-Optimizing Engine**: 65 signals/day target, 70-78% TCS range, 85%+ win rate
- **Tier System**: Press Pass (free) → NIBBLER ($39) → FANG ($89) → COMMANDER ($139) → APEX ($188)
- **Status**: Production ready, awaiting MT5 farm connection

---

## 📁 **TECHNICAL DOCUMENTATION STRUCTURE**

### **For System Architecture Questions**
- **Read**: `BITTEN_SYSTEM_ARCHITECTURE.md`
- **Covers**: Technology stack, database design, API endpoints, security

### **For Trading Logic Questions**
- **Read**: `TRADING_ENGINE_TECHNICAL_SPECIFICATION.md`
- **Covers**: TCS system, self-optimization, predictive detection, fire modes

### **For User Management Questions**
- **Read**: `docs/USER_MANAGEMENT_TIER_SYSTEM_SPECIFICATIONS.md`
- **Covers**: Tier system, authentication, subscriptions, achievements

### **For Integration Questions**
- **Read**: `BITTEN_INTEGRATION_SPECIFICATIONS.md`
- **Covers**: MT5 farm, Telegram bot, WebApp, external APIs

### **For Deployment Questions**
- **Read**: `DEPLOYMENT_OPERATIONS_SPECIFICATIONS.md`
- **Covers**: Infrastructure, deployment, monitoring, security

---

## 🚨 **CRITICAL SYSTEM PARAMETERS**

### **Trading Configuration (LOCKED)**
```yaml
# From config/trading_pairs.yml v3.0.0
total_active_pairs: 10
target_signals_per_day: 65
min_tcs_threshold: 70.0
max_tcs_threshold: 78.0
target_win_rate: 85%
self_optimizing: true
```

### **Tier Limits (FINAL)**
```yaml
PRESS_PASS: {shots: 1, tcs: 60%, price: $0, duration: 7_days, weekly_limit: 200, xp_resets_nightly: true}
NIBBLER: {shots: 6, tcs: 70%, price: $39}
FANG: {shots: 10, tcs: 85%, price: $89}
COMMANDER: {shots: 20, tcs: 90%, price: $139}
APEX: {shots: unlimited, tcs: 91%, price: $188}
```

### **Infrastructure**
- **Linux Server**: 134.199.204.67 (main system)
- **Windows MT5 Farm**: 3.145.84.187 (needs connection)
- **Database**: PostgreSQL + SQLite for optimization
- **WebApp**: https://joinbitten.com (port 8888)

---

## 🔄 **BEFORE MAKING ANY CHANGES**

### **Step 1: Identify System Component**
- **Trading Logic**: Use trading engine specifications
- **User Features**: Use user management specifications
- **System Architecture**: Use system architecture specifications
- **Deployment**: Use deployment specifications

### **Step 2: Check Current Implementation**
- **Read relevant specification document**
- **Check config files for current parameters**
- **Review CLAUDE.md for recent changes**
- **Verify with actual file contents**

### **Step 3: Implement Changes**
- **Update code/config as needed**
- **Update relevant specification document**
- **Update CLAUDE.md if major change**
- **Test thoroughly**

---

## 🎯 **COMMON QUESTIONS & ANSWERS**

### **Q: How many trading pairs are active?**
**A**: 10 active pairs (see config/trading_pairs.yml), 2 reserve pairs (AUDJPY, GBPCHF)

### **Q: What's the current TCS system?**
**A**: Self-optimizing 70-78% range, targets 65 signals/day, 85%+ win rate

### **Q: What are the tier prices?**
**A**: Press Pass (free) → NIBBLER ($39) → FANG ($89) → COMMANDER ($139) → APEX ($188)

### **Q: Where is the MT5 integration?**
**A**: Windows server 3.145.84.187, needs manual connection, see deployment specs

### **Q: What's the system architecture?**
**A**: Multi-server (Linux + Windows), self-optimizing engine, read system architecture doc

---

## 🛡️ **CRITICAL RULES**

### **❌ NEVER DO**
- Change trading pairs without updating config/trading_pairs.yml
- Modify tier pricing without updating user management specs
- Deploy without reading deployment specifications
- Ignore the technical documentation

### **✅ ALWAYS DO**
- Read relevant specification document first
- Check CLAUDE.md for current system status
- Update documentation when making changes
- Test changes thoroughly
- Follow the established architecture

---

## 📊 **SYSTEM STATUS INDICATORS**

### **✅ Production Ready**
- Self-optimizing TCS engine
- 10-pair trading configuration
- Complete tier system
- Technical documentation
- Security systems

### **🔄 Pending**
- MT5 farm connection
- Live signal generation
- Performance validation
- User testing

### **📋 Future**
- Mobile app
- Advanced analytics
- Social features expansion
- API marketplace

---

## 🚀 **QUICK COMMANDS FOR COMMON TASKS**

### **Check System Status**
```bash
# Check running services
ps aux | grep python | grep -E "(webapp|bitten|mt5)"

# Check configuration
cat /root/HydraX-v2/config/trading_pairs.yml

# Check database
python3 -c "import sqlite3; print('DB exists')"
```

### **Update Documentation**
```bash
# Edit relevant specification
nano /root/HydraX-v2/TRADING_ENGINE_TECHNICAL_SPECIFICATION.md

# Update index
nano /root/HydraX-v2/TECHNICAL_DOCS_INDEX.md

# Update CLAUDE.md if major change
nano /root/HydraX-v2/CLAUDE.md
```

---

## 📞 **ESCALATION PATH**

### **For Technical Issues**
1. **Check**: Relevant specification document
2. **Verify**: Current system configuration
3. **Review**: CLAUDE.md for recent changes
4. **Test**: In development environment first
5. **Deploy**: With proper monitoring

### **For System Changes**
1. **Plan**: Read affected specification documents
2. **Design**: Follow established architecture patterns
3. **Implement**: Update code and configurations
4. **Document**: Update relevant specifications
5. **Test**: Comprehensive testing before deployment

---

**Remember: The technical documentation system is the single source of truth. Always consult the relevant specification documents before making any changes to the BITTEN system.**

---

*This guide ensures consistent AI assistance and prevents configuration drift across the entire BITTEN platform.*