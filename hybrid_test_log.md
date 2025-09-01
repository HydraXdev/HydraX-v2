# USDJPY Hybrid Position Management Test Log

## Test Configuration
- **Date/Time Started**: [PENDING]
- **Symbol**: USDJPY
- **Lot Size**: 0.01
- **Risk**: 20 pips SL
- **Expected TP1**: +30 pips (1.5R)
- **Expected Partial**: 75% at TP1
- **Expected BE**: Entry + 2-3 pip offset
- **Expected Trail**: ATR×2 (≈15-20 pips)

## Test Results Table

| Ticket | Entry | SL | TP1 Target | Time to TP1 | Partial Closed? | BE Set Price | Trail Distance | Exit Reason | Net P/L (R) |
|--------|-------|----|-----------:|------------:|-----------------|--------------|---------------:|-------------|------------:|
| [PENDING] | - | - | - | - | - | - | - | - | - |

## Event Timeline

```
[ ] Trade opened at: 
[ ] Entry price: 
[ ] Initial SL: 
[ ] TP1 target calculated: 
[ ] TP1 reached at: 
[ ] Partial close executed: 
[ ] BE+offset modification: 
[ ] Trail started: 
[ ] Final exit at: 
[ ] Exit reason: 
```

## Validation Checklist

- [ ] ✅ No partials triggered before +1.5R (30 pips)
- [ ] ✅ Exactly 75% closed at +1.5R 
- [ ] ✅ SL moved to BE + offset (not exact entry)
- [ ] ✅ Trail only started after TP1 hit
- [ ] ✅ Remainder exited via trail or timeout

## Issues/Observations

_None yet_

## Rollback Command (if needed)
```bash
sed -i 's/^FEATURE_HYBRID_ENABLED.*/FEATURE_HYBRID_ENABLED = false/' config/rollout.toml
pm2 restart webapp
```