# BITTEN Component Map
*Generated from Shepherd Index*

## Core System Architecture

### 🎯 Tier 1: Core Trading & Signals (41 components)
**Purpose**: The heart of BITTEN - signal generation, trade execution, and market analysis

**Key Components:**
- `SignalAlertSystem` - Manages signal generation and delivery
- `execute_trade` - Core trade execution logic
- `get_tcs_score` - Trade Confidence Score calculation
- `get_signals` - Signal retrieval and filtering
- `close_trade` - Trade closing logic

### 🛡️ Tier 2: Risk Management & Control (47 components)
**Purpose**: Safety systems, risk controls, and trade management

**Key Components:**
- `BittenCore` - Main system controller
- `EmergencyStopController` - Emergency shutdown system
- `RiskProfile` - User risk configuration
- `_move_to_breakeven` - Breakeven protection
- `_trail_stop` - Trailing stop implementation

### ⭐ Tier 3: User Features & XP (28 components)
**Purpose**: Gamification, achievements, and user progression

**Key Components:**
- `UserXPBalance` - XP tracking system
- `activate_parachute_exit` - Special exit features
- `award_xp` - XP distribution logic
- `_show_achievement_showcase` - Achievement display
- `_cmd_achievements` - Achievement commands

### 🔧 Tier 4: Support Systems (4 components)
**Purpose**: Infrastructure and support features

**Key Components:**
- `_notify` - Notification system
- `send_education_notification` - Educational alerts
- `_get_pending_notifications` - Notification queue

### 📚 Tier 5: Education & Social (13 components)
**Purpose**: Learning resources and community features

**Key Components:**
- `_cmd_learn` - Educational commands
- `_cmd_squad` - Squad/team features
- `_get_user_education_progress` - Progress tracking
- `_handle_education_callback` - Educational interactions

### 📦 Tier General: Infrastructure (171 components)
**Purpose**: Base classes, utilities, and system infrastructure

## Component Categories by Function

### 📡 Signal System
- Signal generation and analysis
- Trade Confidence Score (TCS) calculation
- Signal filtering by tier access
- Signal alert delivery via Telegram

### 🔫 Fire Modes System
- `SystemMode` - System-wide operating modes
- `TacticalMode` - Trading strategy modes
- Fire mode validators and routers
- Mode-specific trade execution

### 💼 Trade Management
- Position tracking and management
- Trade execution and validation
- Stop loss and take profit handling
- Breakeven and trailing stop logic

### 🤖 Telegram Bot Interface
- Command handlers (`_cmd_*` functions)
- Message routing and formatting
- WebApp integration for HUD
- User interaction handling

### 💰 XP & Gamification
- XP earning and tracking
- Achievement system
- Rank progression
- Battle pass features

### 🚨 Emergency & Risk Systems
- Emergency stop controls
- Daily loss limits
- Position size validation
- Risk profile management

### 🔔 Notification System
- Real-time alerts
- Batch notification handling
- Educational notifications
- System status updates

## Naming Conventions

- `_cmd_*` - Telegram command handlers
- `_handle_*` - Event handlers
- `send_*` - Message/notification senders
- `get_*` - Data retrievers
- `validate_*` - Validation functions
- `process_*` - Data processors
- `*Controller` - System controllers
- `*Manager` - Resource managers
- `*System` - Major subsystems

## File Organization

- `/src/bitten_core/` - Core BITTEN components
- `/src/telegram_bot/` - Telegram bot specific code
- `/src/order_flow/` - Market analysis components
- `/src/toc/` - Trading Operations Center
- `/config/` - Configuration files
- `/data/` - Data storage and caches