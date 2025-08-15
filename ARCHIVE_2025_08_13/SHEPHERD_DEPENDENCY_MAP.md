# 🗺️ BITTEN Dependency Map
*Based on Shepherd Full Audit*

## System Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
├─────────────────────────────────────────────────────────────┤
│  Telegram Bot  │  WebApp (HUD)  │  API Endpoints           │
└────────┬───────┴────────┬────────┴──────────┬──────────────┘
         │                │                    │
         ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    ROUTING LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  Command Router │  Signal Router  │  Fire Mode Router       │
└────────┬───────┴────────┬────────┴──────────┬──────────────┘
         │                │                    │
         ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC                             │
├─────────────────────────────────────────────────────────────┤
│  Signal Engine  │  Trade Manager  │  Risk Controller        │
│  XP System      │  Auth System    │  Notification Engine    │
└────────┬───────┴────────┬────────┴──────────┬──────────────┘
         │                │                    │
         ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
├─────────────────────────────────────────────────────────────┤
│  Database       │  Cache          │  External APIs          │
│  File Storage   │  Session Store  │  MT5 Bridge             │
└─────────────────────────────────────────────────────────────┘
```

## Critical Dependency Chains

### 1. Signal Generation → Trade Execution
```
Market Data (MT5) 
    ↓
Signal Engine (TCS Calculation)
    ↓
Signal Classification (RAPID/SNIPER)
    ↓
Signal Alert System
    ↓
Telegram Notification
    ↓
WebApp HUD Display
    ↓
User Action (Execute)
    ↓
Fire Mode Validation
    ↓
Trade Execution (MT5)
    ↓
Risk Management Checks
    ↓
Position Tracking
    ↓
XP Award System
```

### 2. User Command → System Response
```
Telegram Command
    ↓
Command Handler
    ↓
Authentication Check
    ↓
Tier/Rank Validation
    ↓
Business Logic
    ↓
Database Operation
    ↓
Response Generation
    ↓
Telegram Reply
```

### 3. Risk Management Flow
```
Trade Request
    ↓
Position Size Check
    ↓
Daily Loss Check
    ↓
Risk Profile Validation
    ↓
Emergency Stop Check
    ↓
Execute/Reject Decision
    ↓
Audit Trail
```

## Component Statistics

### By Trigger Type:
- **Direct Call**: 3,980 (65%) - Internal function calls
- **User Action**: 829 (14%) - User-initiated events
- **Signal**: 783 (13%) - Trading signal triggers
- **Command**: 332 (5%) - Telegram commands
- **Webhook**: 213 (3%) - HTTP endpoints
- **Event**: 210 (3%) - System events
- **Scheduled**: 34 (1%) - Cron jobs

### By Flag Type:
- **External API**: 3,543 - Components making external calls
- **Writes DB**: 1,256 - Database write operations
- **Critical**: 985 - Critical system operations
- **Security**: 403 - Authentication/encryption
- **Financial**: 164 - Payment/subscription handling

## High-Risk Dependencies

### 1. Single Points of Failure
- **BittenCore**: Central controller (143 connections)
- **MT5 Bridge**: Trading execution gateway
- **Database Connection**: Data persistence

### 2. Circular Dependencies Detected
- Signal System ↔ XP System
- Trade Manager ↔ Risk Controller
- Notification Engine ↔ User Manager

### 3. External Dependencies
- **Telegram API**: User interface
- **MT5 API**: Trade execution
- **Stripe API**: Payments
- **ForexFactory API**: News events

## Security Considerations

### Authentication Chain
```
User → Telegram ID → Database Lookup → Tier Check → Access Grant
```

### Critical Operations Protection
- Emergency stops: Multi-layer validation
- Trade execution: 5-step verification
- Payment processing: Stripe webhook validation

## Optimization Opportunities

### 1. Connection Reduction
- Implement event bus for decoupling
- Use dependency injection
- Create service facades

### 2. Performance Improvements
- Cache frequently accessed data
- Batch database operations
- Implement connection pooling

### 3. Code Organization
- Consolidate duplicate validators
- Extract common utilities
- Standardize error handling

## Recommended Refactoring Priority

### High Priority (Tier 1 & 2 components)
1. Signal generation pipeline
2. Trade execution path
3. Risk management system

### Medium Priority (Tier 3 & 4)
1. XP calculation logic
2. Notification delivery
3. WebApp integration

### Low Priority (Tier 5 & General)
1. Educational content
2. Squad features
3. Utility functions

---

*This dependency map helps identify critical paths and potential bottlenecks in the BITTEN system architecture.*