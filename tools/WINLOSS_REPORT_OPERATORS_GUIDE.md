# WINLOSS REPORT - Operator's Guide

## Quick Commands (Most Used)

```bash
# Last 24 hours rolling
python3 /root/HydraX-v2/tools/winloss_report.py last24h

# Today so far
python3 /root/HydraX-v2/tools/winloss_report.py today

# Yesterday full day
python3 /root/HydraX-v2/tools/winloss_report.py yesterday

# Last 7 days
python3 /root/HydraX-v2/tools/winloss_report.py last7d

# Custom date range
python3 /root/HydraX-v2/tools/winloss_report.py --from '2025-09-01' --to '2025-09-05'
```

## Using the Shell Script Alias

```bash
# Easier command using shell script
/root/HydraX-v2/tools/run_winloss_report.sh last24h
/root/HydraX-v2/tools/run_winloss_report.sh today
/root/HydraX-v2/tools/run_winloss_report.sh custom '2025-09-01' '2025-09-05'
```

## Report Format

The report ALWAYS returns these sections in order:

1. **Header**: Time range, total signals analyzed, timeout policy
2. **Table A - Confidence Bins**: 70-75, 75-80, 80-85, 85-90, 90-95, 95+
3. **Table B - Pattern Performance**: All patterns with N, Win%, Expectancy
4. **Table C - Session Performance**: ASIAN, LONDON, NY, OVERLAP
5. **Top/Bottom Performers**: Patterns with N≥20 sorted by expectancy
6. **Footnotes**: Policy explanations and exclusion counts

## Understanding the Metrics

- **N**: Number of signals
- **TP**: Take profit hits
- **SL**: Stop loss hits  
- **TO**: Timeouts (counted as losses by default)
- **Win%**: TP/(TP+SL+TO) percentage
- **Exp(R)**: Average achieved R:R (expectancy)
- **Med(min)**: Median time to outcome in minutes
- **Coverage%**: Percentage of total signals in this bin

## Database Tables Used

- `signals_all`: All generated signals (FIRED or DROPPED)
- `signal_outcomes_verified`: Broker outcomes for executed trades
- `signal_outcomes_shadow`: Shadow outcomes for non-executed trades
- `unified_outcomes`: SQL view combining broker and shadow results

## Timeout Policy

- **loss** (default): Timeouts count as losses in Win%
- **exclude**: Timeouts excluded from Win% calculation

```bash
# Change timeout policy
python3 /root/HydraX-v2/tools/winloss_report.py last24h --timeout_policy exclude
```

## Confidence Type

- **calibrated** (default): Use ML-calibrated confidence
- **raw**: Use original Elite Guard confidence

```bash
# Use raw confidence
python3 /root/HydraX-v2/tools/winloss_report.py last24h --bins raw
```

## Data Freshness

- Report reads live database
- Pending signals (not yet closed) are excluded
- Shadow outcomes finalize after timebox expires (typically 120 min)
- Broker outcomes always override shadow when available

## Troubleshooting

### No Data in Report
```bash
# Check if signals exist
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signals_all"

# Check if outcomes exist  
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signal_outcomes_verified"
sqlite3 /root/HydraX-v2/bitten.db "SELECT COUNT(*) FROM signal_outcomes_shadow"
```

### Missing Recent Signals
```bash
# Populate from existing signals table
python3 /root/HydraX-v2/tools/populate_signals_all.py
```

### Report Takes Too Long
```bash
# Check indexes exist
sqlite3 /root/HydraX-v2/bitten.db ".indexes signals_all"
```

## Daily Report Automation

A PM2 task runs the report at midnight UTC and saves to file:
```bash
# Check if running
pm2 status winloss_daily

# View daily reports
ls -la /root/HydraX-v2/reports/daily/
```

## Important Notes

1. **TIMEOUT as Loss**: We treat timeouts as losses in the standard report
2. **TRAIL/MANUAL**: Counted based on achieved_r (positive→TP, negative→SL)
3. **Unknown Session**: Means session wasn't tagged at signal generation
4. **Pending Exclusion**: Signals without outcomes yet are excluded from denominators

## Recovery Commands

If the report tool disappears, use these SQLite commands directly:

```sql
-- Confidence bins
SELECT 
    CASE
        WHEN calibrated_confidence >= 95 THEN '95+'
        WHEN calibrated_confidence >= 90 THEN '90-95'
        WHEN calibrated_confidence >= 85 THEN '85-90'
        WHEN calibrated_confidence >= 80 THEN '80-85'
        WHEN calibrated_confidence >= 75 THEN '75-80'
        WHEN calibrated_confidence >= 70 THEN '70-75'
    END as bin,
    COUNT(*) as N,
    SUM(CASE WHEN outcome='TP' THEN 1 ELSE 0 END) as TP,
    SUM(CASE WHEN outcome='SL' THEN 1 ELSE 0 END) as SL
FROM unified_outcomes
WHERE ts_fire > strftime('%s', 'now', '-24 hours')
GROUP BY bin;

-- Pattern performance
SELECT 
    pattern,
    COUNT(*) as N,
    AVG(CASE WHEN outcome='TP' THEN 100.0 ELSE 0 END) as win_pct,
    AVG(achieved_r) as expectancy
FROM unified_outcomes
WHERE ts_fire > strftime('%s', 'now', '-24 hours')
GROUP BY pattern;
```

## Contact

For issues or enhancements, check:
- Log file: `/var/log/winloss_report.log` (if configured)
- Source code: `/root/HydraX-v2/tools/winloss_report.py`
- Migration script: `/root/HydraX-v2/tools/populate_signals_all.py`