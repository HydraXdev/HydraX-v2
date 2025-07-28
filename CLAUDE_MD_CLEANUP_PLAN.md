# CLAUDE.md Cleanup Plan

## Current Issues with CLAUDE.md:
1. **Too Long**: 3,977 lines, 151KB - overwhelming for AI assistants
2. **Duplicate Sections**: Multiple overviews, repeated information
3. **Session Logs**: Contains outdated "CRITICAL UPDATE" sections from past work
4. **Outdated Info**: Wrong pricing, old credentials mentioned
5. **Poor Organization**: 492 headers with no clear hierarchy

## Proposed Solution:

### 1. Archive Current CLAUDE.md
```bash
mv CLAUDE.md CLAUDE_ARCHIVE_2025_07_11.md
```

### 2. Use New Clean Version
```bash
mv CLAUDE_CLEAN.md CLAUDE.md
```

### 3. New Structure (Clean Version):
- **Executive Summary** - Quick overview
- **System Architecture** - What BITTEN is
- **Tier System & Pricing** - Clear pricing table
- **Fire Modes** - How execution works
- **Signal System** - Types and thresholds
- **Safety Systems** - Risk management
- **XP & Gamification** - User progression
- **Current Status** - What's working/pending
- **Quick Start** - For developers
- **Support & Documentation** - Where to find help

### 4. What Was Removed:
- All "CRITICAL UPDATE" sections (moved to archive)
- Session completion logs
- Duplicate content
- Implementation details (those belong in handover.md)
- Old pricing references
- Exposed credentials

### 5. What Was Updated:
- Pricing: as  standalone
- Tier names: Using actual names only
- TCS thresholds: Both at 87%
- Fire modes: Clear explanation
- Current status: Accurate as of July 11

### 6. Benefits:
- **10x smaller**: From 151KB to ~15KB
- **Clear hierarchy**: Logical flow of information
- **No duplicates**: Each topic covered once
- **Current info**: All pricing and features updated
- **AI-friendly**: Easy to parse and understand

## Recommendation:
Replace the current CLAUDE.md with CLAUDE_CLEAN.md. The old version can be archived for reference but shouldn't be the primary documentation going forward.