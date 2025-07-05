# BITTEN Onboarding State Machine Specification

## Overview
This document defines the state machine architecture for the BITTEN "Ground Zero" onboarding flow.

## State Definitions

```python
@dataclass
class OnboardingSession:
    user_id: str
    telegram_id: int
    current_state: str
    state_data: Dict[str, Any]
    started_at: datetime
    last_activity: datetime
    completed_states: List[str]
    user_responses: Dict[str, Any]
    
    # User data collected during onboarding
    has_experience: Optional[bool] = None
    first_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    selected_theater: Optional[str] = None
    accepted_terms: bool = False
    broker_account_id: Optional[str] = None
    callsign: Optional[str] = None
```

## State Flow Diagram

```
[START] 
    |
    v
[FIRST_CONTACT] -- Has experience? --> [YES/NO Response]
    |
    v
[MARKET_WARFARE_INTRO] -- Show demo --> [User executes prediction]
    |
    v
[KNOWLEDGE_SOURCE] -- Explain system --> [User confirms understanding]
    |
    v
[TRAINING_SETUP] -- Collect info --> [Basic Info -> Account Setup -> Allocation]
    |
    v
[FIRST_MISSION] -- Practice trade --> [User completes lesson]
    |
    v
[PATH_FORWARD] -- Show progress --> [User chooses to continue]
    |
    v
[THEATER_SELECTION] -- Choose account --> [Demo/Regulated/Offshore]
    |
    v
[OATH_OF_ENLISTMENT] -- Accept terms --> [User agrees to protocols]
    |
    v
[SECURE_LINK] -- Connect broker --> [User provides trading credentials]
    |
    v
[CALLSIGN_CREATION] -- Choose identity --> [User enters callsign]
    |
    v
[OPERATIONAL_INTERFACE] -- Show interface --> [Tour begins]
    |
    v
[CORE_MANEUVERS] -- Basic training --> [User practices commands]
    |
    v
[FIELD_MANUAL] -- Show resources --> [User explores menu]
    |
    v
[PERSONAL_RECORD] -- Show stats --> [User views profile]
    |
    v
[COMPLETE] -- Onboarding finished
```

## State Transition Rules

### FIRST_CONTACT
**Entry Actions:**
- Send Sergeant Nexus opening message
- Display YES/NO buttons

**Valid Transitions:**
- On YES/NO response → MARKET_WARFARE_INTRO
- On timeout (5 min) → Save state and pause
- On /skip → MARKET_WARFARE_INTRO (mark as skipped)

**Exit Actions:**
- Store has_experience flag
- Log response time

### MARKET_WARFARE_INTRO
**Entry Actions:**
- Display market explanation
- Show live chart animation
- Present "ENGAGE NOW" button

**Valid Transitions:**
- On ENGAGE click → Show success animation → KNOWLEDGE_SOURCE
- On timeout → Send reminder
- On /back → FIRST_CONTACT

**Exit Actions:**
- Log engagement success
- Store demo completion flag

### TRAINING_SETUP
**Entry Actions:**
- Display step indicator (1/4, 2/4, etc.)
- Show appropriate input fields

**Sub-states:**
1. BASIC_INFO
   - Collect: first_name, email, phone
   - Validate: email format, phone format
   
2. ACCOUNT_VERIFICATION
   - Display collected info for confirmation
   - Allow editing
   
3. CAPITAL_ALLOCATION
   - Show $50,000 allocation message
   - Display Doc's protective message
   
4. SETUP_COMPLETE
   - Show success confirmation
   - Display next steps

**Valid Transitions:**
- On valid input → Next sub-state
- On invalid input → Show error, retry
- On /back → Previous sub-state

### THEATER_SELECTION
**Entry Actions:**
- Display three account options
- Show detailed comparison

**Options:**
1. US_REGULATED_DEMO
   - $50,000 practice funds
   - No risk messaging
   
2. US_REGULATED_LIVE
   - Real money warnings
   - Security emphasis
   
3. OFFSHORE_UNREGULATED
   - Bitcoin only notice
   - Risk warnings

**Valid Transitions:**
- On selection → OATH_OF_ENLISTMENT
- On /info [option] → Show detailed info
- On /back → PATH_FORWARD

### CALLSIGN_CREATION
**Entry Actions:**
- Display callsign explanation
- Show example suggestions
- Present input field

**Validation Rules:**
- Length: 3-20 characters
- Pattern: Alphanumeric + underscore
- Uniqueness check
- No reserved words

**Valid Transitions:**
- On valid callsign → OPERATIONAL_INTERFACE
- On invalid → Show specific error
- On /suggest → Generate suggestions

## Session Management

### Persistence Strategy
```python
class OnboardingSessionManager:
    def save_session(self, session: OnboardingSession):
        # Save to database/cache
        # Key: f"onboarding:{session.user_id}"
        # TTL: 7 days
        
    def load_session(self, user_id: str) -> Optional[OnboardingSession]:
        # Load from database/cache
        # Check if expired
        # Return None if not found
        
    def resume_session(self, session: OnboardingSession):
        # Send appropriate message for current state
        # Include "Welcome back" messaging
        # Show progress indicator
```

### Timeout Handling
- Inactive for 5 minutes → Save state, send reminder
- Inactive for 1 hour → Send follow-up with resume link
- Inactive for 24 hours → Send final reminder
- Inactive for 7 days → Archive session

## Integration Points

### Telegram Bot Commands
```python
# During onboarding
/start - Begin or resume onboarding
/back - Go to previous step
/skip - Skip optional steps
/help - Get context-sensitive help
/pause - Save and pause onboarding
/status - Show onboarding progress

# Post-onboarding
/me - View personal record
/menu - Access field manual
/scan - Market reconnaissance
/engage - Execute trade
```

### Persona Integration
```python
# Use existing persona system
responses = persona_orchestrator.get_response(
    user_id=session.user_id,
    event_type=f"onboarding_{current_state}",
    context={
        "state_data": session.state_data,
        "user_responses": session.user_responses
    }
)
```

### Analytics Events
```python
# Track key metrics
track_event("onboarding_started", {
    "user_id": user_id,
    "source": source,
    "timestamp": timestamp
})

track_event("onboarding_state_completed", {
    "user_id": user_id,
    "state": state_name,
    "duration": duration,
    "attempts": attempts
})

track_event("onboarding_completed", {
    "user_id": user_id,
    "total_duration": duration,
    "theater_selected": theater,
    "callsign": callsign
})
```

## Error Handling

### Graceful Degradation
- Network errors → Save state, retry with exponential backoff
- Invalid input → Show specific error with examples
- System errors → Apologize, save state, notify support
- Rate limits → Show cooldown message

### Recovery Flows
```python
def handle_error(session: OnboardingSession, error: Exception):
    if isinstance(error, NetworkError):
        return "Connection issue detected. Your progress is saved. Try again in a moment."
    elif isinstance(error, ValidationError):
        return f"Invalid input: {error.message}. Example: {error.example}"
    elif isinstance(error, RateLimitError):
        return f"Slow down, recruit! Wait {error.cooldown} seconds."
    else:
        return "Tactical error encountered. Progress saved. Support notified."
```

## Success Metrics

### Completion Rate Tracking
- Overall completion rate
- Drop-off by state
- Time per state
- Error frequency by state

### A/B Testing Framework
```python
class OnboardingVariant:
    STANDARD = "standard"
    SHORTENED = "shortened"  # Fewer states
    GAMIFIED = "gamified"   # More game elements
    
def get_variant(user_id: str) -> OnboardingVariant:
    # Deterministic assignment based on user_id
    # Track performance by variant
```

---

*"Every mission begins with a plan. Execute with precision."*
— BITTEN Operations Manual