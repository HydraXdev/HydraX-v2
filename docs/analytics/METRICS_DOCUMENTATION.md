# Press Pass Analytics & Metrics Documentation

## Overview

This document provides comprehensive documentation of all metrics, KPIs, and analytics systems implemented for monitoring Press Pass conversion performance.

## Table of Contents

1. [Core Metrics](#core-metrics)
2. [Conversion Funnel Metrics](#conversion-funnel-metrics)
3. [Activation Metrics](#activation-metrics)
4. [Retention Metrics](#retention-metrics)
5. [Revenue Metrics](#revenue-metrics)
6. [System Health Metrics](#system-health-metrics)
7. [Real-time Monitoring](#real-time-monitoring)
8. [Alerting Thresholds](#alerting-thresholds)
9. [Reporting Schedule](#reporting-schedule)

## Core Metrics

### 1. Press Pass Conversion Rate
- **Definition**: Percentage of landing page visitors who claim a Press Pass
- **Formula**: `(Press Pass Claims / Landing Page Views) × 100`
- **Target**: 2.5-3.5%
- **Update Frequency**: Real-time
- **Alert Threshold**: < 0.5% (Critical), < 1.5% (Warning)

### 2. Daily Active Users (DAU)
- **Definition**: Unique Press Pass users who logged in within 24 hours
- **Formula**: `COUNT(DISTINCT user_id) WHERE last_login >= NOW() - 24h`
- **Target**: > 70% of active Press Pass holders
- **Update Frequency**: Every 5 minutes
- **Alert Threshold**: < 50% (Warning), < 30% (Critical)

### 3. XP Reset Metrics
- **Definition**: Daily XP reset statistics at midnight GMT
- **Tracked Values**:
  - Total users affected
  - Total XP reset
  - Average XP per user
  - Activity rate (users with XP > 0)
- **Update Frequency**: Daily at 00:00 GMT
- **Alert Threshold**: Reset failure count > 5

## Conversion Funnel Metrics

### Funnel Stages

1. **Landing Page Views**
   - Unique sessions on /press-pass page
   - Tracked via analytics events

2. **Press Pass Claims**
   - Users who successfully activate Press Pass
   - Split by source (organic/paid)

3. **Demo Account Activation**
   - Users who connect MT5 demo account
   - Time to activation tracked

4. **First Trade Completion**
   - Users who complete at least one trade
   - Average time to first trade: Target < 24 hours

5. **Tier Upgrade**
   - Users who upgrade from Press Pass to paid tier
   - Breakdown by target tier (Nibbler, Fang, Commander, Apex)

### Funnel Conversion Rates

| Stage Transition | Target Rate | Alert Threshold |
|-----------------|-------------|-----------------|
| Landing → Claim | 2.5-3.5% | < 1.5% |
| Claim → Demo | > 80% | < 60% |
| Demo → Trade | > 50% | < 30% |
| Trade → Upgrade | > 10% | < 5% |

## Activation Metrics

### Key Activation Indicators

1. **Time to First Trade**
   - **Definition**: Hours between Press Pass claim and first trade
   - **Target**: < 24 hours (median)
   - **Measurement**: Median and average tracked separately

2. **Onboarding Completion Rate**
   - **Definition**: Users who complete all onboarding steps
   - **Target**: > 90%
   - **Steps Tracked**:
     - Profile completion
     - Demo account setup
     - First trade tutorial
     - Strategy selection

3. **Feature Adoption**
   - **Tracked Features**:
     - Auto-trading activation
     - Risk management setup
     - Notification preferences
     - Community engagement

## Retention Metrics

### Cohort Retention Analysis

Retention measured at key intervals:
- **D1**: 24 hours after registration
- **D3**: 3 days after registration
- **D7**: 7 days after registration (key metric)
- **D14**: 14 days after registration
- **D30**: 30 days after registration

### Retention Targets

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| D1 Login | > 80% | < 60% |
| D7 Login | > 50% | < 35% |
| D30 Login | > 30% | < 20% |
| D7 Trade Activity | > 40% | < 25% |

### Churn Indicators

1. **7-Day Churn Rate**
   - Users inactive for 7+ days
   - Target: < 30%

2. **At-Risk Users**
   - No activity in 3-6 days
   - Trigger re-engagement campaigns

3. **Win-Back Potential**
   - High-engagement users who churned
   - Priority for targeted campaigns

## Revenue Metrics

### Revenue Tracking

1. **Total Revenue from Upgrades**
   - Sum of all payments from Press Pass upgrades
   - Tracked by payment method and tier

2. **Average Revenue Per User (ARPU)**
   - **Formula**: `Total Revenue / Upgraded Users`
   - Calculated for different time windows

3. **Customer Lifetime Value (CLV)**
   - Projected revenue per Press Pass user
   - Includes upgrade probability and retention

4. **Time to Upgrade**
   - Days between Press Pass claim and tier upgrade
   - **Target**: 7-14 days (median)

### Revenue by Tier

| Tier | Monthly Price | Avg. Upgrade Time | Conversion Rate |
|------|--------------|-------------------|-----------------|
| Nibbler | $39 | 7 days | 5% |
| Fang | $79 | 10 days | 3% |
| Commander | $159 | 14 days | 1.5% |
| Apex | $349 | 21 days | 0.5% |

## System Health Metrics

### Performance Indicators

1. **API Response Time**
   - Average response time for key endpoints
   - **Target**: < 200ms (p95)
   - **Alert**: > 1000ms

2. **Error Rate**
   - Percentage of failed requests
   - **Target**: < 1%
   - **Alert**: > 5%

3. **Database Performance**
   - Query execution time
   - Connection pool utilization
   - **Alert**: > 80% utilization

### Availability Metrics

1. **Uptime**
   - System availability percentage
   - **Target**: 99.9%

2. **Demo Account Provisioning Success**
   - Success rate for MT5 demo accounts
   - **Target**: > 99%

## Real-time Monitoring

### Dashboard Components

1. **Live Conversion Funnel**
   - Updates every 60 seconds
   - Shows current conversion rates

2. **Active User Counter**
   - Real-time count of online users
   - Geographic distribution

3. **Revenue Ticker**
   - Live revenue tracking
   - Comparison to daily target

4. **Alert Feed**
   - Real-time anomaly notifications
   - Severity-based prioritization

### Monitoring Infrastructure

- **Data Collection**: Event-based tracking via analytics API
- **Processing**: Stream processing for real-time aggregation
- **Storage**: Time-series database for historical data
- **Visualization**: Interactive dashboards with Plotly/Grafana

## Alerting Thresholds

### Critical Alerts (Immediate Action Required)

| Metric | Condition | Action |
|--------|-----------|---------|
| Conversion Rate | < 0.5% | Check tracking, landing page |
| XP Reset Failure | > 5 failures | Manual intervention required |
| System Error Rate | > 10% | Check system health, rollback |
| Database Connection | > 90% utilized | Scale database resources |

### Warning Alerts (Investigation Needed)

| Metric | Condition | Action |
|--------|-----------|---------|
| Activation Rate | < 30% | Review onboarding flow |
| D7 Retention | < 35% | Enhance engagement tactics |
| Churn Spike | > 50% increase | Analyze user feedback |
| Response Time | > 500ms | Optimize slow queries |

### Info Alerts (Monitoring Only)

- Unusual positive spikes (verify data accuracy)
- Scheduled maintenance windows
- A/B test deployments

## Reporting Schedule

### Daily Reports (1 AM GMT)

**Contents:**
- Previous day's funnel performance
- Conversion rate trends
- Activation metrics
- XP reset summary
- Top performing traffic sources
- Anomaly summary

**Distribution:**
- Email to stakeholders
- Slack summary to #analytics channel
- Dashboard update

### Weekly Reports (Monday 2 AM GMT)

**Contents:**
- Week-over-week comparisons
- Cohort retention analysis
- Revenue performance
- Detailed funnel breakdown
- A/B test results
- Strategic recommendations

**Distribution:**
- Comprehensive email report
- Executive summary presentation
- Team meeting agenda items

### Monthly Reports (1st of month)

**Contents:**
- Monthly KPI review
- Cohort LTV analysis
- Seasonal trend analysis
- Competitive benchmarking
- Strategic planning inputs

## Implementation Details

### Data Sources

1. **Primary Database** (PostgreSQL)
   - User data
   - Transaction records
   - Subscription information

2. **Analytics Events** (Event Stream)
   - Page views
   - User interactions
   - Conversion events

3. **Application Logs**
   - Error tracking
   - Performance metrics
   - System health

### Technology Stack

- **Database**: PostgreSQL with TimescaleDB extension
- **Stream Processing**: Apache Kafka / Redis Streams
- **Analytics Engine**: Custom Python analytics service
- **Visualization**: Plotly, Matplotlib, Grafana
- **Alerting**: Custom anomaly detection + PagerDuty integration
- **Reporting**: Automated Python scripts with Jinja2 templates

### Data Retention Policy

| Data Type | Retention Period | Aggregation |
|-----------|-----------------|-------------|
| Raw Events | 90 days | None |
| Hourly Metrics | 1 year | By hour |
| Daily Summaries | 2 years | By day |
| Monthly Reports | Indefinite | By month |

## Best Practices

### For Analysts

1. **Always verify anomalies** before escalating
2. **Consider seasonality** in trend analysis
3. **Cross-reference** multiple metrics for insights
4. **Document** any manual interventions

### For Developers

1. **Test tracking** before deploying changes
2. **Monitor performance** impact of new features
3. **Version** analytics events properly
4. **Maintain** backwards compatibility

### For Stakeholders

1. **Focus on trends** not single data points
2. **Set realistic targets** based on historical data
3. **Act on insights** from reports promptly
4. **Provide feedback** on report usefulness

## Appendix: SQL Query Examples

### Daily Conversion Funnel
```sql
WITH funnel AS (
    SELECT 
        COUNT(DISTINCT CASE WHEN event = 'page_view' THEN session_id END) as views,
        COUNT(DISTINCT CASE WHEN event = 'press_pass_claim' THEN user_id END) as claims,
        COUNT(DISTINCT CASE WHEN event = 'demo_activated' THEN user_id END) as activated,
        COUNT(DISTINCT CASE WHEN event = 'first_trade' THEN user_id END) as traded,
        COUNT(DISTINCT CASE WHEN event = 'tier_upgrade' THEN user_id END) as upgraded
    FROM analytics_events
    WHERE date = CURRENT_DATE
)
SELECT 
    *,
    ROUND(claims::numeric / NULLIF(views, 0) * 100, 2) as view_to_claim_rate,
    ROUND(activated::numeric / NULLIF(claims, 0) * 100, 2) as claim_to_active_rate,
    ROUND(traded::numeric / NULLIF(activated, 0) * 100, 2) as active_to_trade_rate,
    ROUND(upgraded::numeric / NULLIF(traded, 0) * 100, 2) as trade_to_upgrade_rate
FROM funnel;
```

### Cohort Retention Analysis
```sql
WITH cohorts AS (
    SELECT 
        DATE_TRUNC('day', created_at) as cohort_date,
        user_id,
        created_at
    FROM users
    WHERE tier = 'PRESS_PASS'
)
SELECT 
    cohort_date,
    COUNT(DISTINCT c.user_id) as cohort_size,
    COUNT(DISTINCT CASE WHEN l.login_date = c.cohort_date + 1 THEN c.user_id END) as d1_retained,
    COUNT(DISTINCT CASE WHEN l.login_date = c.cohort_date + 7 THEN c.user_id END) as d7_retained,
    COUNT(DISTINCT CASE WHEN l.login_date = c.cohort_date + 30 THEN c.user_id END) as d30_retained
FROM cohorts c
LEFT JOIN user_logins l ON c.user_id = l.user_id
GROUP BY cohort_date
ORDER BY cohort_date DESC;
```

---

*Last Updated: [Current Date]*
*Version: 1.0*
*Maintained by: Analytics Team*