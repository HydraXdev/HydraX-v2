"""
Automated Report Generator for Press Pass Analytics

Generates daily and weekly reports with key metrics, insights,
and actionable recommendations.
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from decimal import Decimal
import json
from jinja2 import Template
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates automated reports for Press Pass performance"""
    
    def __init__(self, dashboard, email_service=None, slack_service=None):
        self.dashboard = dashboard
        self.email_service = email_service
        self.slack_service = slack_service
        
    async def generate_daily_report(self, report_date: date) -> Dict[str, Any]:
        """Generate comprehensive daily report"""
        logger.info(f"Generating daily report for {report_date}")
        
        # Calculate date ranges
        start_date = datetime.combine(report_date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        previous_start = start_date - timedelta(days=1)
        
        # Gather metrics
        metrics = await self._gather_daily_metrics(start_date, end_date, previous_start)
        
        # Generate insights
        insights = self._generate_daily_insights(metrics)
        
        # Create visualizations
        charts = await self._create_daily_charts(metrics)
        
        # Compile report
        report = {
            'type': 'daily',
            'date': report_date.isoformat(),
            'generated_at': datetime.utcnow().isoformat(),
            'metrics': metrics,
            'insights': insights,
            'charts': charts,
            'recommendations': self._generate_recommendations(metrics, insights)
        }
        
        # Send report
        await self._distribute_report(report)
        
        return report
    
    async def generate_weekly_report(self, week_end_date: date) -> Dict[str, Any]:
        """Generate comprehensive weekly report"""
        logger.info(f"Generating weekly report ending {week_end_date}")
        
        # Calculate date ranges
        end_date = datetime.combine(week_end_date, datetime.min.time()) + timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        previous_start = start_date - timedelta(days=7)
        previous_end = start_date
        
        # Gather metrics
        metrics = await self._gather_weekly_metrics(start_date, end_date, previous_start, previous_end)
        
        # Generate insights
        insights = self._generate_weekly_insights(metrics)
        
        # Create visualizations
        charts = await self._create_weekly_charts(metrics)
        
        # Compile report
        report = {
            'type': 'weekly',
            'week_ending': week_end_date.isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'generated_at': datetime.utcnow().isoformat(),
            'metrics': metrics,
            'insights': insights,
            'charts': charts,
            'trends': self._analyze_weekly_trends(metrics),
            'recommendations': self._generate_recommendations(metrics, insights)
        }
        
        # Send report
        await self._distribute_report(report)
        
        return report
    
    async def _gather_daily_metrics(self, start_date: datetime, end_date: datetime, 
                                   previous_start: datetime) -> Dict[str, Any]:
        """Gather all daily metrics"""
        
        # Current day metrics
        current_funnel = await self.dashboard.get_conversion_funnel(start_date, end_date)
        current_activation = await self.dashboard.get_activation_metrics(start_date, end_date)
        current_revenue = await self.dashboard.get_revenue_metrics(start_date, end_date)
        xp_reset = await self.dashboard.get_xp_reset_metrics(start_date.date())
        churn = await self.dashboard.get_churn_metrics(end_date)
        
        # Previous day metrics for comparison
        previous_funnel = await self.dashboard.get_conversion_funnel(previous_start, start_date)
        previous_activation = await self.dashboard.get_activation_metrics(previous_start, start_date)
        previous_revenue = await self.dashboard.get_revenue_metrics(previous_start, start_date)
        
        return {
            'current': {
                'funnel': current_funnel,
                'activation': current_activation,
                'revenue': current_revenue,
                'xp_reset': xp_reset,
                'churn': churn
            },
            'previous': {
                'funnel': previous_funnel,
                'activation': previous_activation,
                'revenue': previous_revenue
            },
            'changes': self._calculate_changes(
                current_funnel, previous_funnel,
                current_activation, previous_activation,
                current_revenue, previous_revenue
            )
        }
    
    async def _gather_weekly_metrics(self, start_date: datetime, end_date: datetime,
                                    previous_start: datetime, previous_end: datetime) -> Dict[str, Any]:
        """Gather all weekly metrics"""
        
        # Current week metrics
        current_funnel = await self.dashboard.get_conversion_funnel(start_date, end_date)
        current_activation = await self.dashboard.get_activation_metrics(start_date, end_date)
        current_revenue = await self.dashboard.get_revenue_metrics(start_date, end_date)
        
        # Previous week metrics
        previous_funnel = await self.dashboard.get_conversion_funnel(previous_start, previous_end)
        previous_activation = await self.dashboard.get_activation_metrics(previous_start, previous_end)
        previous_revenue = await self.dashboard.get_revenue_metrics(previous_start, previous_end)
        
        # Cohort retention (for users who started last week)
        cohort_date = previous_start.date()
        retention = await self.dashboard.get_retention_metrics(cohort_date)
        
        # Daily breakdown for the week
        daily_metrics = []
        for i in range(7):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_funnel = await self.dashboard.get_conversion_funnel(day_start, day_end)
            daily_metrics.append({
                'date': day_start.date().isoformat(),
                'conversions': day_funnel['funnel']['claims']['total'],
                'conversion_rate': day_funnel['conversion_rates']['landing_to_claim'],
                'activations': day_funnel['funnel']['demo_activated'],
                'upgrades': day_funnel['funnel']['upgrades']['total']
            })
        
        return {
            'current': {
                'funnel': current_funnel,
                'activation': current_activation,
                'revenue': current_revenue
            },
            'previous': {
                'funnel': previous_funnel,
                'activation': previous_activation,
                'revenue': previous_revenue
            },
            'retention': retention,
            'daily_breakdown': daily_metrics,
            'changes': self._calculate_changes(
                current_funnel, previous_funnel,
                current_activation, previous_activation,
                current_revenue, previous_revenue
            )
        }
    
    def _calculate_changes(self, current_funnel, previous_funnel, 
                          current_activation, previous_activation,
                          current_revenue, previous_revenue) -> Dict[str, Any]:
        """Calculate period-over-period changes"""
        
        def calc_change(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round((current - previous) / previous * 100, 2)
        
        return {
            'conversions': {
                'absolute': current_funnel['funnel']['claims']['total'] - 
                           previous_funnel['funnel']['claims']['total'],
                'percentage': calc_change(
                    current_funnel['funnel']['claims']['total'],
                    previous_funnel['funnel']['claims']['total']
                )
            },
            'conversion_rate': {
                'absolute': current_funnel['conversion_rates']['landing_to_claim'] - 
                           previous_funnel['conversion_rates']['landing_to_claim'],
                'percentage': calc_change(
                    current_funnel['conversion_rates']['landing_to_claim'],
                    previous_funnel['conversion_rates']['landing_to_claim']
                )
            },
            'activations': {
                'absolute': current_activation['summary']['total_activated'] - 
                           previous_activation['summary']['total_activated'],
                'percentage': calc_change(
                    current_activation['summary']['total_activated'],
                    previous_activation['summary']['total_activated']
                )
            },
            'revenue': {
                'absolute': current_revenue['revenue']['total'] - 
                           previous_revenue['revenue']['total'],
                'percentage': calc_change(
                    current_revenue['revenue']['total'],
                    previous_revenue['revenue']['total']
                )
            }
        }
    
    def _generate_daily_insights(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from daily metrics"""
        insights = []
        
        # Conversion rate insight
        current_rate = metrics['current']['funnel']['conversion_rates']['landing_to_claim']
        rate_change = metrics['changes']['conversion_rate']['percentage']
        
        if rate_change > 10:
            insights.append({
                'type': 'positive',
                'category': 'conversion',
                'message': f"Conversion rate increased by {rate_change}% to {current_rate}%",
                'priority': 'high'
            })
        elif rate_change < -10:
            insights.append({
                'type': 'negative',
                'category': 'conversion',
                'message': f"Conversion rate decreased by {abs(rate_change)}% to {current_rate}%",
                'priority': 'high',
                'action': "Review landing page performance and A/B test results"
            })
        
        # Activation insight
        activation_rate = metrics['current']['activation']['summary']['overall_activation_rate']
        if activation_rate < 20:
            insights.append({
                'type': 'warning',
                'category': 'activation',
                'message': f"Low activation rate: {activation_rate}% of new users completed first trade",
                'priority': 'high',
                'action': "Review onboarding flow and provide more guidance"
            })
        
        # XP Reset insight
        xp_metrics = metrics['current']['xp_reset']['metrics']
        if xp_metrics['activity_rate'] < 50:
            insights.append({
                'type': 'warning',
                'category': 'engagement',
                'message': f"Low daily activity: only {xp_metrics['activity_rate']}% of Press Pass users were active",
                'priority': 'medium',
                'action': "Send engagement emails to inactive users"
            })
        
        # Churn insight
        churn_rate = metrics['current']['churn']['churn_rates']['7_day']
        if churn_rate > 30:
            insights.append({
                'type': 'negative',
                'category': 'retention',
                'message': f"High 7-day churn rate: {churn_rate}%",
                'priority': 'high',
                'action': "Implement win-back campaign for at-risk users"
            })
        
        return insights
    
    def _generate_weekly_insights(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from weekly metrics"""
        insights = []
        
        # Weekly trend analysis
        daily_data = metrics['daily_breakdown']
        conversion_rates = [d['conversion_rate'] for d in daily_data]
        
        # Check for declining trend
        if all(conversion_rates[i] <= conversion_rates[i-1] for i in range(1, len(conversion_rates))):
            insights.append({
                'type': 'negative',
                'category': 'trend',
                'message': "Conversion rate declined consistently throughout the week",
                'priority': 'high',
                'action': "Urgent review needed - consider refreshing offers or messaging"
            })
        
        # Revenue per user insight
        total_revenue = metrics['current']['revenue']['revenue']['total']
        total_upgrades = metrics['current']['funnel']['funnel']['upgrades']['total']
        if total_upgrades > 0:
            revenue_per_upgrade = total_revenue / total_upgrades
            insights.append({
                'type': 'info',
                'category': 'revenue',
                'message': f"Average revenue per upgrade: ${revenue_per_upgrade:.2f}",
                'priority': 'medium'
            })
        
        # Retention insight
        retention = metrics['retention']
        d7_retention = retention['retention']['login']['D7']
        if d7_retention < 40:
            insights.append({
                'type': 'warning',
                'category': 'retention',
                'message': f"Low D7 retention: {d7_retention}% for last week's cohort",
                'priority': 'high',
                'action': "Strengthen day 3-7 engagement tactics"
            })
        
        # Best performing day
        best_day = max(daily_data, key=lambda x: x['conversions'])
        insights.append({
            'type': 'positive',
            'category': 'performance',
            'message': f"Best performing day: {best_day['date']} with {best_day['conversions']} conversions",
            'priority': 'low'
        })
        
        return insights
    
    async def _create_daily_charts(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Create visualizations for daily report"""
        charts = {}
        
        # Conversion funnel chart
        funnel_data = metrics['current']['funnel']['funnel']
        stages = ['Landing', 'Claimed', 'Demo Active', 'First Trade', 'Upgraded']
        values = [
            funnel_data['landing_views'],
            funnel_data['claims']['total'],
            funnel_data['demo_activated'],
            funnel_data['first_trade'],
            funnel_data['upgrades']['total']
        ]
        
        plt.figure(figsize=(10, 6))
        plt.bar(stages, values, color='#2E86AB')
        plt.title('Daily Conversion Funnel')
        plt.ylabel('Users')
        
        # Add conversion rates between stages
        for i in range(len(values)-1):
            if values[i] > 0:
                rate = (values[i+1] / values[i]) * 100
                plt.text(i+0.5, max(values)*0.9, f'{rate:.1f}%', ha='center')
        
        charts['funnel'] = self._chart_to_base64(plt)
        plt.close()
        
        # Hourly conversions heatmap (mock data for now)
        plt.figure(figsize=(12, 4))
        hours = list(range(24))
        conversions = [metrics['current']['funnel']['funnel']['claims']['total'] / 24] * 24
        
        plt.plot(hours, conversions, marker='o', color='#A23B72')
        plt.fill_between(hours, conversions, alpha=0.3, color='#A23B72')
        plt.title('Hourly Conversion Pattern')
        plt.xlabel('Hour (GMT)')
        plt.ylabel('Conversions')
        plt.grid(True, alpha=0.3)
        
        charts['hourly'] = self._chart_to_base64(plt)
        plt.close()
        
        return charts
    
    async def _create_weekly_charts(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Create visualizations for weekly report"""
        charts = {}
        
        # Daily trends chart
        daily_data = pd.DataFrame(metrics['daily_breakdown'])
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Conversions and conversion rate
        ax1.bar(daily_data['date'], daily_data['conversions'], alpha=0.7, color='#2E86AB', label='Conversions')
        ax1.set_ylabel('Conversions', color='#2E86AB')
        ax1.tick_params(axis='y', labelcolor='#2E86AB')
        
        ax1_twin = ax1.twinx()
        ax1_twin.plot(daily_data['date'], daily_data['conversion_rate'], 
                     color='#F18F01', marker='o', linewidth=2, label='Conversion Rate')
        ax1_twin.set_ylabel('Conversion Rate (%)', color='#F18F01')
        ax1_twin.tick_params(axis='y', labelcolor='#F18F01')
        
        ax1.set_title('Daily Conversions and Rate')
        ax1.grid(True, alpha=0.3)
        
        # Activations and upgrades
        ax2.bar(daily_data['date'], daily_data['activations'], 
               alpha=0.7, color='#C73E1D', label='Activations', width=0.4, align='edge')
        ax2.bar(daily_data['date'], daily_data['upgrades'], 
               alpha=0.7, color='#6A994E', label='Upgrades', width=-0.4, align='edge')
        
        ax2.set_ylabel('Count')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        charts['daily_trends'] = self._chart_to_base64(plt)
        plt.close()
        
        # Retention cohort chart
        retention = metrics['retention']['retention']
        
        plt.figure(figsize=(10, 6))
        
        days = ['D1', 'D3', 'D7', 'D14', 'D30']
        login_retention = [retention['login'][d] for d in days]
        trade_retention = [retention['trade_activity'][d] for d in days]
        
        x = range(len(days))
        width = 0.35
        
        plt.bar([i - width/2 for i in x], login_retention, width, 
               label='Login Retention', color='#2E86AB')
        plt.bar([i + width/2 for i in x], trade_retention, width, 
               label='Trade Activity', color='#A23B72')
        
        plt.xlabel('Days Since Registration')
        plt.ylabel('Retention Rate (%)')
        plt.title('Cohort Retention Analysis')
        plt.xticks(x, days)
        plt.legend()
        plt.grid(True, alpha=0.3, axis='y')
        
        charts['retention'] = self._chart_to_base64(plt)
        plt.close()
        
        # Revenue breakdown pie chart
        revenue_by_tier = metrics['current']['revenue']['revenue']['by_tier']
        
        plt.figure(figsize=(8, 8))
        
        tiers = list(revenue_by_tier.keys())
        values = list(revenue_by_tier.values())
        colors = ['#6A994E', '#A23B72', '#F18F01', '#C73E1D']
        
        plt.pie(values, labels=tiers, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Revenue by Upgrade Tier')
        
        charts['revenue_breakdown'] = self._chart_to_base64(plt)
        plt.close()
        
        return charts
    
    def _chart_to_base64(self, plt) -> str:
        """Convert matplotlib chart to base64 string"""
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()
        return image_base64
    
    def _analyze_weekly_trends(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze weekly trends"""
        daily_data = metrics['daily_breakdown']
        
        # Calculate trend directions
        conversion_trend = 'improving' if daily_data[-1]['conversion_rate'] > daily_data[0]['conversion_rate'] else 'declining'
        volume_trend = 'increasing' if daily_data[-1]['conversions'] > daily_data[0]['conversions'] else 'decreasing'
        
        # Find best and worst days
        best_day = max(daily_data, key=lambda x: x['conversion_rate'])
        worst_day = min(daily_data, key=lambda x: x['conversion_rate'])
        
        # Calculate volatility
        rates = [d['conversion_rate'] for d in daily_data]
        avg_rate = sum(rates) / len(rates)
        volatility = sum(abs(r - avg_rate) for r in rates) / len(rates)
        
        return {
            'conversion_trend': conversion_trend,
            'volume_trend': volume_trend,
            'best_day': best_day['date'],
            'worst_day': worst_day['date'],
            'volatility': round(volatility, 2),
            'consistency': 'stable' if volatility < 0.5 else 'volatile'
        }
    
    def _generate_recommendations(self, metrics: Dict[str, Any], insights: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on metrics and insights"""
        recommendations = []
        
        # Check for critical issues
        critical_insights = [i for i in insights if i.get('priority') == 'high' and i.get('type') in ['negative', 'warning']]
        
        if critical_insights:
            recommendations.append("URGENT: Address the following critical issues immediately:")
            for insight in critical_insights:
                if 'action' in insight:
                    recommendations.append(f"- {insight['action']}")
        
        # Conversion optimization
        if 'current' in metrics:
            conv_rate = metrics['current']['funnel']['conversion_rates']['landing_to_claim']
            if conv_rate < 2.0:
                recommendations.append("- Test more aggressive CTA copy and placement")
                recommendations.append("- Consider increasing urgency messaging (spots remaining)")
            
            # Activation optimization
            activation_rate = metrics['current']['activation']['summary']['overall_activation_rate']
            if activation_rate < 30:
                recommendations.append("- Simplify demo account setup process")
                recommendations.append("- Add interactive tutorial for first trade")
                recommendations.append("- Send immediate welcome email with quick-start guide")
        
        # Retention optimization
        if 'retention' in metrics:
            d7_retention = metrics['retention']['retention']['login']['D7']
            if d7_retention < 50:
                recommendations.append("- Implement daily challenge system for first week")
                recommendations.append("- Add push notifications for trading opportunities")
                recommendations.append("- Create exclusive Press Pass trader community")
        
        # Revenue optimization
        if 'current' in metrics and metrics['current']['funnel']['funnel']['upgrades']['total'] > 0:
            upgrade_rate = metrics['current']['funnel']['conversion_rates']['claim_to_upgrade']
            if upgrade_rate < 10:
                recommendations.append("- Highlight tier benefits more prominently")
                recommendations.append("- Offer limited-time upgrade discount at day 7")
                recommendations.append("- Show success stories from upgraded traders")
        
        return recommendations
    
    async def _distribute_report(self, report: Dict[str, Any]):
        """Distribute report via configured channels"""
        
        # Format report for distribution
        if report['type'] == 'daily':
            subject = f"Daily Press Pass Report - {report['date']}"
        else:
            subject = f"Weekly Press Pass Report - Week Ending {report['week_ending']}"
        
        # Send via email
        if self.email_service:
            await self._send_email_report(report, subject)
        
        # Send via Slack
        if self.slack_service:
            await self._send_slack_report(report, subject)
        
        # Save to database
        await self._save_report_to_db(report)
    
    async def _send_email_report(self, report: Dict[str, Any], subject: str):
        """Send report via email"""
        # This would integrate with your email service
        logger.info(f"Sending email report: {subject}")
    
    async def _send_slack_report(self, report: Dict[str, Any], subject: str):
        """Send report summary via Slack"""
        # This would integrate with your Slack service
        logger.info(f"Sending Slack report: {subject}")
    
    async def _save_report_to_db(self, report: Dict[str, Any]):
        """Save report to database for historical reference"""
        # This would save the report to your database
        logger.info(f"Saving report to database: {report['type']} - {report.get('date') or report.get('week_ending')}")

class ReportScheduler:
    """Schedules automated report generation"""
    
    def __init__(self, report_generator: ReportGenerator):
        self.generator = report_generator
        self.is_running = False
        
    async def start(self):
        """Start the report scheduler"""
        self.is_running = True
        
        # Schedule daily and weekly reports
        await asyncio.gather(
            self._schedule_daily_reports(),
            self._schedule_weekly_reports()
        )
    
    async def stop(self):
        """Stop the report scheduler"""
        self.is_running = False
    
    async def _schedule_daily_reports(self):
        """Run daily reports at 1 AM GMT"""
        while self.is_running:
            now = datetime.utcnow()
            
            # Calculate next 1 AM GMT
            next_run = now.replace(hour=1, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            
            # Wait until next run
            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            if self.is_running:
                # Generate report for previous day
                report_date = (now - timedelta(days=1)).date()
                try:
                    await self.generator.generate_daily_report(report_date)
                except Exception as e:
                    logger.error(f"Error generating daily report: {e}")
    
    async def _schedule_weekly_reports(self):
        """Run weekly reports on Mondays at 2 AM GMT"""
        while self.is_running:
            now = datetime.utcnow()
            
            # Calculate next Monday 2 AM GMT
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= 2:
                days_until_monday = 7
            
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            next_run += timedelta(days=days_until_monday)
            
            # Wait until next run
            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            if self.is_running:
                # Generate report for previous week
                week_end_date = (now - timedelta(days=1)).date()
                try:
                    await self.generator.generate_weekly_report(week_end_date)
                except Exception as e:
                    logger.error(f"Error generating weekly report: {e}")