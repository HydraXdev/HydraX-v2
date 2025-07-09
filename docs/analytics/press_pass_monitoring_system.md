# Press Pass Monitoring System Documentation

## Overview

The Press Pass Monitoring System provides comprehensive analytics, real-time monitoring, automated reporting, and visualization capabilities for tracking Press Pass conversion metrics and optimizing user conversion from free tier to paid subscriptions.

## System Architecture

### Core Components

1. **Dashboard Queries** (`src/analytics/dashboards/press_pass_metrics.py`)
   - Comprehensive SQL queries for all key metrics
   - Conversion funnel analysis
   - Activation and retention metrics
   - Revenue tracking
   - Churn analysis

2. **Real-time Monitoring** (`src/analytics/monitoring/realtime_monitor.py`)
   - Continuous metric tracking
   - Threshold-based alerting
   - Redis-backed metric storage
   - System health monitoring

3. **Anomaly Detection** (`src/analytics/monitoring/anomaly_detector.py`)
   - Statistical anomaly detection
   - Multiple detection algorithms (Z-score, IQR, trend, seasonal)
   - Alert severity classification
   - Automated recommendations

4. **Report Generation** (`src/analytics/reporting/report_generator.py`)
   - Automated daily and weekly reports
   - Insight generation
   - Visual chart creation
   - Multi-channel distribution (email, Slack)

5. **Visualization** (`src/analytics/visualization/funnel_visualizer.py`)
   - Interactive funnel charts
   - Real-time dashboards
   - Cohort retention heatmaps
   - Revenue analysis visualizations

## Key Metrics and KPIs

### Conversion Metrics
- **Landing to Claim Rate**: Percentage of landing page visitors who claim Press Pass
- **Claim to Demo Rate**: Percentage of claimants who activate demo account
- **Demo to Trade Rate**: Percentage of demo users who complete first trade
- **Claim to Upgrade Rate**: Overall conversion from Press Pass to paid tier

### Activation Metrics
- **Time to First Trade**: Average hours from registration to first trade
- **Activation Rate by Cohort**: Daily cohort activation performance
- **Feature Adoption**: Onboarding completion, profile completion rates

### XP Reset Metrics
- **Daily Active Users**: Press Pass users earning XP
- **Total XP Reset**: Amount of XP reset at midnight GMT
- **Activity Rate**: Percentage of Press Pass users active daily

### Retention Metrics
- **D1, D3, D7, D14, D30 Retention**: Login and trade activity retention
- **Churn Rates**: 7-day, 14-day, 30-day churn rates
- **At-risk Users**: Users showing signs of churning

### Revenue Metrics
- **Total Revenue from Upgrades**: Revenue from Press Pass conversions
- **Average Revenue Per User (ARPU)**: Revenue per upgraded user
- **Revenue by Tier**: Breakdown by upgrade tier (Nibbler, Fang, Commander, Apex)
- **Time to Upgrade**: Average days from Press Pass to paid subscription

## Alert Thresholds

| Metric | Threshold | Severity | Description |
|--------|-----------|----------|-------------|
| Conversion Rate | < 0.5% | ERROR | Landing to claim conversion below threshold |
| Activation Rate | < 20% | WARNING | New user activation rate low |
| XP Reset Failures | > 5 | CRITICAL | Technical issues with nightly reset |
| Churn Rate Spike | > 50% increase | ERROR | Significant increase in churn |
| Upgrade Rate | < 5% | WARNING | Low conversion to paid tiers |
| Response Time | > 1000ms | WARNING | API performance degradation |
| Error Rate | > 5% | ERROR | High system error rate |

## Usage Examples

### 1. Initialize the Monitoring System

```python
from src.analytics.dashboards.press_pass_metrics import PressPassMetricsDashboard
from src.analytics.monitoring.realtime_monitor import RealtimeMonitor
from src.analytics.monitoring.anomaly_detector import AnomalyDetector, AlertManager
from src.analytics.reporting.report_generator import ReportGenerator, ReportScheduler
import redis
import asyncio

# Initialize components
db_connection = get_database_connection()  # Your database connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Create dashboard
dashboard = PressPassMetricsDashboard(db_connection)

# Set up real-time monitoring
monitor = RealtimeMonitor(db_connection, redis_client)

# Initialize anomaly detection
anomaly_detector = AnomalyDetector(sensitivity=2.5)
alert_manager = AlertManager(anomaly_detector)

# Set up automated reporting
report_generator = ReportGenerator(dashboard)
report_scheduler = ReportScheduler(report_generator)

# Start monitoring
async def start_monitoring():
    await asyncio.gather(
        monitor.start_monitoring(),
        report_scheduler.start()
    )

# Run the monitoring system
asyncio.run(start_monitoring())
```

### 2. Query Conversion Funnel Metrics

```python
from datetime import datetime, timedelta

# Get conversion funnel for last 7 days
start_date = datetime.utcnow() - timedelta(days=7)
end_date = datetime.utcnow()

funnel_metrics = await dashboard.get_conversion_funnel(start_date, end_date)

print(f"Conversion Rate: {funnel_metrics['conversion_rates']['landing_to_claim']}%")
print(f"Total Claims: {funnel_metrics['funnel']['claims']['total']}")
print(f"Upgrades: {funnel_metrics['funnel']['upgrades']['total']}")
```

### 3. Monitor XP Resets

```python
# Get XP reset metrics for today
today = datetime.utcnow().date()
xp_metrics = await dashboard.get_xp_reset_metrics(today)

print(f"Active Users: {xp_metrics['metrics']['active_users']}")
print(f"Total XP to Reset: {xp_metrics['metrics']['total_xp_reset']}")
print(f"Activity Rate: {xp_metrics['metrics']['activity_rate']}%")
```

### 4. Set Up Custom Alerts

```python
# Add custom alert handler
async def slack_alert_handler(alert):
    # Send alert to Slack
    await send_to_slack(f"🚨 {alert['title']}: {alert['message']}")

alert_manager.add_handler(slack_alert_handler)

# Add suppression rule to prevent alert spam
alert_manager.add_suppression_rule('press_pass_conversions', min_interval_minutes=30)

# Check metric and trigger alerts if needed
await alert_manager.check_and_alert('conversion_rate', 0.3, datetime.utcnow())
```

### 5. Generate Reports

```python
# Generate daily report manually
report_date = datetime.utcnow().date() - timedelta(days=1)
daily_report = await report_generator.generate_daily_report(report_date)

# Generate weekly report
week_end = datetime.utcnow().date() - timedelta(days=1)
weekly_report = await report_generator.generate_weekly_report(week_end)
```

### 6. Create Visualizations

```python
from src.analytics.visualization.funnel_visualizer import FunnelVisualizer

visualizer = FunnelVisualizer()

# Create funnel chart
funnel_data = funnel_metrics['funnel']
fig = visualizer.create_funnel_chart(funnel_data, title="Weekly Conversion Funnel")
visualizer.export_dashboard_html(fig, "weekly_funnel.html")

# Create real-time dashboard
current_metrics = await monitor.get_current_metrics()
dashboard_fig = visualizer.create_real_time_dashboard(current_metrics)
visualizer.export_dashboard_html(dashboard_fig, "realtime_dashboard.html")
```

## Automated Reporting Schedule

- **Daily Reports**: Generated at 1:00 AM GMT
  - Previous day's performance metrics
  - Key insights and anomalies
  - Conversion funnel visualization
  - Recommendations for optimization

- **Weekly Reports**: Generated Mondays at 2:00 AM GMT
  - Week-over-week performance comparison
  - Cohort retention analysis
  - Revenue breakdown
  - Trend analysis and forecasting

## Dashboard Access

### Real-time Dashboard URL
Access the real-time monitoring dashboard at: `/analytics/dashboard/press-pass`

### Key Dashboard Views
1. **Overview**: High-level KPIs and conversion funnel
2. **Activation**: New user activation and onboarding metrics
3. **Retention**: Cohort retention analysis and churn indicators
4. **Revenue**: Upgrade revenue and LTV analysis
5. **Alerts**: Recent anomalies and system alerts

## Best Practices

1. **Monitor Alert Fatigue**
   - Adjust thresholds based on actual performance
   - Use suppression rules to prevent spam
   - Focus on actionable alerts

2. **Regular Review Cycles**
   - Weekly review of conversion trends
   - Monthly deep-dive into cohort performance
   - Quarterly strategy adjustment based on data

3. **A/B Testing Integration**
   - Track conversion rate changes during tests
   - Use anomaly detection to identify test impacts
   - Document successful optimizations

4. **Data Quality**
   - Regular validation of tracking implementation
   - Monitor for data gaps or anomalies
   - Maintain data dictionary for metrics

## Troubleshooting

### Common Issues

1. **Missing Data in Reports**
   - Check database connectivity
   - Verify data pipeline is running
   - Check for tracking implementation issues

2. **False Positive Alerts**
   - Adjust sensitivity threshold
   - Add seasonal patterns to detection
   - Implement business hour filtering

3. **Performance Issues**
   - Optimize SQL queries with proper indexing
   - Implement query result caching
   - Use materialized views for complex aggregations

## Future Enhancements

1. **Machine Learning Integration**
   - Predictive churn modeling
   - Conversion probability scoring
   - Automated optimization recommendations

2. **Enhanced Visualizations**
   - User journey mapping
   - Predictive forecasting charts
   - Interactive cohort analysis

3. **Advanced Segmentation**
   - Behavioral clustering
   - Persona-based analysis
   - Geographic performance tracking

## Support

For questions or issues with the monitoring system:
- Technical Issues: #engineering-support
- Metric Questions: #data-analytics
- Alert Configuration: #ops-alerts

## Version History

- v1.0 (2025-01-08): Initial implementation
  - Core monitoring infrastructure
  - Basic alerting system
  - Daily/weekly reporting
  - Conversion funnel visualization