# BITTEN Demo Account Credentials

## 🔐 Master Demo Account (MetaQuotes)

**Account Number:** 100007013135
**Password:** \_5LgQaCw
**Server:** MetaQuotes-Demo
**Broker:** MetaQuotes Demo Server

## 📍 Location & Usage

**Container:** bitten-mt5-master (129.212.185.102)
**Purpose:** Master template for cloning user instances
**Status:** ACTIVE & CONFIGURED
**Magic Number:** 20250626

## 🎯 15 BITTEN Pairs Status

All 15 pairs configured and ready:

### Major Pairs (4)

- ✅ EURUSD
- ✅ GBPUSD
- ✅ USDJPY
- ✅ USDCAD

### Volatile Pairs (4)

- ✅ GBPJPY
- ✅ EURJPY
- ✅ AUDJPY
- ✅ GBPCHF

### Standard Pairs (4)

- ✅ AUDUSD
- ✅ NZDUSD
- ✅ USDCHF
- ✅ EURGBP

### Volatility Monsters (3)

- ✅ GBPNZD
- ✅ GBPAUD
- ✅ EURAUD

## 🔧 Technical Details

**Bridge Configuration:**

- Local Socket Bridge: 129.212.185.102:5557
- FireRouter: CONNECTED to local bridge
- Drop Folder: /root/.wine/drive_c/MT5Terminal/Files/BITTEN/
- Account Config: /root/.wine/drive_c/MT5Terminal/config/account.ini

## ⚠️ Security Notes

- This is a DEMO account for testing/master template
- No real money at risk
- Used for cloning user instances
- Password should be changed periodically
- Only use for BITTEN system development

## 🚀 Clone Instructions

To create user clone:

1. Copy master container: `docker commit bitten-mt5-master bitten-master-template`
2. Launch new instance with user credentials
3. Update account.ini with user's broker details
4. Start container with unique user ID

---

**Created:** July 18, 2025
**Last Updated:** July 18, 2025
**Status:** ACTIVE
