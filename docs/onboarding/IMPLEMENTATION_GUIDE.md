# BITTEN Onboarding Implementation Guide

## Overview
This guide outlines how to implement the "Ground Zero" onboarding flow for new BITTEN users.

## Architecture

### 1. State Machine Pattern
```python
class OnboardingState(Enum):
    FIRST_CONTACT = "first_contact"
    MARKET_WARFARE_INTRO = "market_warfare_intro"
    KNOWLEDGE_SOURCE = "knowledge_source"
    TRAINING_SETUP = "training_setup"
    FIRST_MISSION = "first_mission"
    PATH_FORWARD = "path_forward"
    THEATER_SELECTION = "theater_selection"
    OATH_OF_ENLISTMENT = "oath_of_enlistment"
    SECURE_LINK = "secure_link"
    CALLSIGN_CREATION = "callsign_creation"
    OPERATIONAL_INTERFACE = "operational_interface"
    CORE_MANEUVERS = "core_maneuvers"
    FIELD_MANUAL = "field_manual"
    PERSONAL_RECORD = "personal_record"
    COMPLETE = "complete"
```

### 2. Core Components

#### OnboardingOrchestrator
- Manages state transitions
- Tracks user progress
- Handles resumable sessions
- Integrates with persona system

#### OnboardingDialogue
- Stores all Sergeant Nexus dialogue
- Maintains character voice consistency
- Supports dynamic user name insertion

#### OnboardingHandlers
- Processes user responses
- Validates inputs
- Manages account creation flow
- Handles errors gracefully

### 3. Integration Points

#### With Telegram Bot
```python
@bot.message_handler(commands=['start'])
async def start_onboarding(message):
    user_id = message.from_user.id
    orchestrator = OnboardingOrchestrator(user_id)
    await orchestrator.begin_onboarding(message)
```

#### With Persona System
```python
# Use existing personas for voice overlays
nexus = persona_orchestrator.nexus
drill = persona_orchestrator.drill
doc = persona_orchestrator.doc
```

## Implementation Steps

### Phase 1: Core Structure
1. Create onboarding module structure
2. Define state machine and transitions
3. Implement base orchestrator class

### Phase 2: Dialogue System
1. Extract all dialogue into configuration
2. Create dialogue renderer with variable substitution
3. Add character voice markers

### Phase 3: User Interaction
1. Build response handlers for each state
2. Add input validation
3. Implement progress persistence

### Phase 4: Account Integration
1. Create secure broker connection flow
2. Implement credential encryption
3. Add verification steps

### Phase 5: Personalization
1. Callsign generation and validation
2. User profile creation
3. Stats tracking initialization

## Security Considerations

### Credential Handling
- Never store primary broker credentials
- Encrypt trading passwords at rest
- Use secure communication channels
- Implement session timeouts

### Input Validation
- Sanitize all user inputs
- Validate email formats
- Check callsign uniqueness
- Prevent injection attacks

## UI/UX Guidelines

### Telegram Formatting
```python
# Bold for emphasis
"*Sergeant Nexus:* Listen close, recruit..."

# Code blocks for buttons
"```\n[YES] → Continue\n[NO] → Exit\n```"

# Inline keyboards for choices
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("YES", callback_data="experience_yes")],
    [InlineKeyboardButton("NO", callback_data="experience_no")]
])
```

### Progress Indicators
- Show current phase number
- Estimate time remaining
- Allow skip/back navigation
- Save progress automatically

## Testing Strategy

### Unit Tests
- Test each state transition
- Validate dialogue rendering
- Check error handling
- Verify data persistence

### Integration Tests
- Full flow walkthrough
- Resume from each state
- Error recovery scenarios
- Performance under load

### User Testing
- A/B test dialogue variations
- Measure completion rates
- Gather feedback on clarity
- Optimize conversion funnel

## Metrics to Track

### Engagement Metrics
- Start-to-completion rate
- Drop-off points by phase
- Time spent per phase
- Return user percentage

### Conversion Metrics
- Demo account creation rate
- Live account upgrade rate
- First trade execution rate
- 30-day retention rate

## Deployment Checklist

1. [ ] All dialogue reviewed and approved
2. [ ] State machine thoroughly tested
3. [ ] Security audit completed
4. [ ] Error messages user-friendly
5. [ ] Analytics tracking verified
6. [ ] Rollback plan prepared
7. [ ] Support team briefed
8. [ ] Documentation updated

## Future Enhancements

### Adaptive Onboarding
- Adjust pace based on user responses
- Skip sections for experienced users
- Add tooltips for complex concepts
- Personalize examples to user region

### Gamification Elements
- Achievement badges for completion
- Progress bar visualization
- Bonus XP for fast completion
- Leaderboard for top recruits

### Multi-Channel Support
- Web interface version
- Mobile app adaptation
- Email drip campaign
- SMS reminders

---

*"Every operative's journey begins with a single step. Make it count."*
— Sergeant Nexus