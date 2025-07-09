# Press Pass XP Reset Test Report

**Generated**: 2025-07-08 01:01:12 UTC

## Summary
- **Total Tests**: 11
- **Passed**: 10 ✅
- **Failed**: 1 ❌
- **Success Rate**: 90.9%

## Test Results

### Midnight Reset Timing ❌ FAIL
**Description**: Error testing midnight reset timing
**Details**: 'NoneType' object has no attribute 'do'
**Time**: 2025-07-08T01:01:12.394283+00:00

### Warning Notifications ✅ PASS
**Description**: Warning notifications have correct content and timing
**Details**: 1-hour warning correct: True, 15-min warning correct: True
**Time**: 2025-07-08T01:01:12.394323+00:00

### Shadow Stats Preservation ✅ PASS
**Description**: Shadow stats correctly preserved and updated during reset
**Details**: All checks passed: True
**Time**: 2025-07-08T01:01:12.394336+00:00

### Regular Users Unaffected ✅ PASS
**Description**: Regular users' XP remained unchanged during Press Pass reset
**Details**: Press Pass reset: True, Regular unchanged: True
**Time**: 2025-07-08T01:01:12.394345+00:00

### XP Wipe Notification Amounts ✅ PASS
**Description**: XP wipe notifications show correctly formatted amounts
**Details**: Tested amounts: [12345, 67890, 100, 999999]
**Time**: 2025-07-08T01:01:12.394357+00:00

### Timezone Handling ✅ PASS
**Description**: Timezone handling is correct (all times in UTC)
**Details**: UTC timestamp: 2025-07-08T01:01:12.394361+00:00, Warning times correct: True
**Time**: 2025-07-08T01:01:12.394378+00:00

### Manual Reset Functionality ✅ PASS
**Description**: Manual reset works correctly for single user and all users
**Details**: Tests passed: single reset, others unchanged, all reset
**Time**: 2025-07-08T01:01:12.394385+00:00

### Scheduler Reliability ✅ PASS
**Description**: Scheduler can execute jobs reliably
**Details**: Test job executed successfully
**Time**: 2025-07-08T01:01:12.702254+00:00

### Data Persistence ✅ PASS
**Description**: Data persistence works correctly
**Details**: Data saved and loaded successfully
**Time**: 2025-07-08T01:01:12.703250+00:00

### Concurrent Operations Safety ✅ PASS
**Description**: Concurrent operations handled safely
**Details**: Operations order: ['reset', 'award'], Final XP: 100
**Time**: 2025-07-08T01:01:12.804931+00:00

### Edge Cases ✅ PASS
**Description**: All edge cases handled correctly
**Details**: Cases tested: ['Zero XP user', 'Large XP formatting', 'Timezone boundary', 'Multiple resets']
**Time**: 2025-07-08T01:01:12.805093+00:00

## Issues Found

- Midnight Reset Timing: Error testing midnight reset timing - 'NoneType' object has no attribute 'do'
