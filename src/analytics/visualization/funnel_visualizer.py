"""
Conversion Funnel Visualization for Press Pass

Creates interactive and static visualizations of the Press Pass
conversion funnel with detailed breakdowns and insights.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.text import Text
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

class FunnelVisualizer:
    """Creates visualizations for Press Pass conversion funnel"""
    
    def __init__(self):
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#6A994E',
            'warning': '#F18F01',
            'danger': '#C73E1D',
            'info': '#7209B7',
            'light': '#F8F9FA',
            'dark': '#212529'
        }
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
    
    def create_funnel_chart(self, funnel_data: Dict[str, Any], 
                           title: str = "Press Pass Conversion Funnel") -> go.Figure:
        """Create interactive funnel chart using Plotly"""
        
        stages = ['Landing Page', 'Press Pass Claimed', 'Demo Activated', 
                 'First Trade', 'Tier Upgraded']
        
        values = [
            funnel_data['landing_views'],
            funnel_data['claims']['total'],
            funnel_data['demo_activated'],
            funnel_data['first_trade'],
            funnel_data['upgrades']['total']
        ]
        
        # Calculate conversion rates between stages
        rates = []
        for i in range(len(values)-1):
            if values[i] > 0:
                rate = (values[i+1] / values[i]) * 100
                rates.append(f"{rate:.1f}%")
            else:
                rates.append("0%")
        
        # Create funnel chart
        fig = go.Figure()
        
        fig.add_trace(go.Funnel(
            y=stages,
            x=values,
            textposition="inside",
            textinfo="value+percent initial",
            opacity=0.85,
            marker={
                "color": [self.colors['primary'], self.colors['secondary'], 
                         self.colors['success'], self.colors['warning'], 
                         self.colors['danger']],
                "line": {"width": 2, "color": "white"}
            },
            connector={"line": {"color": "gray", "width": 2}}
        ))
        
        # Add annotations for conversion rates
        for i, rate in enumerate(rates):
            fig.add_annotation(
                x=0.5,
                y=i + 0.5,
                text=f"→ {rate}",
                showarrow=False,
                font=dict(size=14, color="black"),
                xref="paper",
                yref="y"
            )
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            width=800,
            height=600,
            showlegend=False,
            plot_bgcolor='white',
            font=dict(size=12)
        )
        
        return fig
    
    def create_funnel_breakdown(self, funnel_data: Dict[str, Any]) -> go.Figure:
        """Create detailed breakdown of funnel by source"""
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Claims by Source', 'Upgrades by Tier', 
                          'Conversion Rates Over Time', 'User Journey Time'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "box"}]]
        )
        
        # 1. Claims by source pie chart
        claims = funnel_data['claims']
        fig.add_trace(
            go.Pie(
                labels=['Organic', 'Paid'],
                values=[claims['organic'], claims['paid']],
                marker_colors=[self.colors['success'], self.colors['info']],
                textinfo='label+percent',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # 2. Upgrades by tier bar chart
        upgrades = funnel_data['upgrades']['by_tier']
        fig.add_trace(
            go.Bar(
                x=list(upgrades.keys()),
                y=list(upgrades.values()),
                marker_color=[self.colors['primary'], self.colors['secondary'],
                             self.colors['warning'], self.colors['danger']],
                text=list(upgrades.values()),
                textposition='auto',
                showlegend=False
            ),
            row=1, col=2
        )
        
        # 3. Mock conversion rates over time (would use real data)
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        mock_rates = np.random.normal(2.5, 0.5, 30)
        mock_rates = np.maximum(mock_rates, 0.5)  # Ensure positive
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=mock_rates,
                mode='lines+markers',
                marker_color=self.colors['primary'],
                line=dict(width=2),
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 4. User journey time box plot (mock data)
        journey_times = {
            'Landing→Claim': np.random.exponential(5, 100),
            'Claim→Demo': np.random.exponential(30, 100),
            'Demo→Trade': np.random.exponential(120, 100),
            'Trade→Upgrade': np.random.exponential(480, 100)
        }
        
        for stage, times in journey_times.items():
            fig.add_trace(
                go.Box(
                    y=times / 60,  # Convert to hours
                    name=stage,
                    marker_color=self.colors['primary'],
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title="Press Pass Funnel Breakdown Analysis",
            height=800,
            showlegend=False,
            plot_bgcolor='white'
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Conversion Rate (%)", row=2, col=1)
        fig.update_xaxes(title_text="Stage Transition", row=2, col=2)
        fig.update_yaxes(title_text="Time (hours)", row=2, col=2)
        
        return fig
    
    def create_cohort_retention_heatmap(self, retention_data: List[Dict[str, Any]]) -> go.Figure:
        """Create cohort retention heatmap"""
        
        # Prepare data for heatmap
        cohorts = []
        days = ['D0', 'D1', 'D3', 'D7', 'D14', 'D30']
        
        for cohort in retention_data:
            cohort_retention = []
            for day in days:
                if day == 'D0':
                    cohort_retention.append(100)  # 100% on day 0
                else:
                    retention_value = cohort['retention']['login'].get(day, 0)
                    cohort_retention.append(retention_value)
            cohorts.append(cohort_retention)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=cohorts,
            x=days,
            y=[cohort['cohort_date'] for cohort in retention_data],
            colorscale='RdYlGn',
            text=[[f'{val:.1f}%' for val in row] for row in cohorts],
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Retention %")
        ))
        
        fig.update_layout(
            title="Press Pass Cohort Retention Analysis",
            xaxis_title="Days Since Registration",
            yaxis_title="Cohort Date",
            width=800,
            height=600,
            plot_bgcolor='white'
        )
        
        return fig
    
    def create_revenue_analysis(self, revenue_data: Dict[str, Any]) -> plt.Figure:
        """Create revenue analysis visualization"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Press Pass Revenue Analysis', fontsize=16)
        
        # 1. Revenue by tier
        tiers = list(revenue_data['revenue']['by_tier'].keys())
        revenues = list(revenue_data['revenue']['by_tier'].values())
        
        ax1.bar(tiers, revenues, color=[self.colors['primary'], self.colors['secondary'],
                                        self.colors['warning'], self.colors['danger']])
        ax1.set_title('Revenue by Upgrade Tier')
        ax1.set_ylabel('Revenue ($)')
        
        # Add value labels
        for i, v in enumerate(revenues):
            ax1.text(i, v + max(revenues)*0.01, f'${v:,.0f}', ha='center')
        
        # 2. Conversion to upgrade funnel
        stages = ['Press Pass\nUsers', 'Completed\nOnboarding', 'Made\nFirst Trade', 'Upgraded']
        values = [
            revenue_data['users']['total'],
            int(revenue_data['users']['total'] * 0.7),  # Mock data
            int(revenue_data['users']['total'] * 0.5),  # Mock data
            revenue_data['users']['upgraded']
        ]
        
        # Create funnel visualization
        y_positions = range(len(stages))
        max_width = 1.0
        
        for i, (stage, value) in enumerate(zip(stages, values)):
            width = (value / values[0]) * max_width
            left = (max_width - width) / 2
            
            rect = FancyBboxPatch(
                (left, i), width, 0.8,
                boxstyle="round,pad=0.02",
                facecolor=self.colors['primary'],
                alpha=0.7,
                edgecolor='black'
            )
            ax2.add_patch(rect)
            
            # Add text
            ax2.text(0.5, i + 0.4, f"{stage}\n{value:}", 
                    ha='center', va='center', fontsize=10, weight='bold')
            
            # Add conversion rate
            if i > 0:
                rate = (value / values[i-1]) * 100
                ax2.text(1.1, i, f"{rate:.1f}%", ha='left', va='center')
        
        ax2.set_xlim(-0.1, 1.3)
        ax2.set_ylim(-0.5, len(stages) - 0.5)
        ax2.set_title('Upgrade Conversion Funnel')
        ax2.axis('off')
        
        # 3. Average revenue per user over time
        days = range(1, 31)
        arpu = [revenue_data['revenue']['avg_per_paying_user'] * (1 - np.exp(-i/10)) for i in days]
        
        ax3.plot(days, arpu, marker='o', color=self.colors['success'], linewidth=2)
        ax3.fill_between(days, arpu, alpha=0.3, color=self.colors['success'])
        ax3.set_title('Average Revenue Per Paying User (30 days)')
        ax3.set_xlabel('Days Since Upgrade')
        ax3.set_ylabel('Cumulative Revenue ($)')
        ax3.grid(True, alpha=0.3)
        
        # 4. Time to upgrade distribution
        upgrade_times = np.random.gamma(revenue_data['time_to_upgrade']['avg_days'], 2, 1000)
        
        ax4.hist(upgrade_times, bins=30, color=self.colors['info'], alpha=0.7, edgecolor='black')
        ax4.axvline(revenue_data['time_to_upgrade']['avg_days'], 
                   color='red', linestyle='--', linewidth=2, label='Average')
        ax4.axvline(revenue_data['time_to_upgrade']['median_days'], 
                   color='green', linestyle='--', linewidth=2, label='Median')
        ax4.set_title('Time to Upgrade Distribution')
        ax4.set_xlabel('Days from Press Pass to Upgrade')
        ax4.set_ylabel('Number of Users')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_real_time_dashboard(self, metrics: Dict[str, Any]) -> go.Figure:
        """Create real-time monitoring dashboard"""
        
        # Create subplots with different types
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                'Current Conversion Rate', 'Active Users', 'Revenue Today',
                'Hourly Conversions', 'Activation Funnel', 'Alert Status',
                'XP Reset Progress', 'Churn Risk', 'System Health'
            ),
            specs=[
                [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                [{"type": "scatter"}, {"type": "funnel"}, {"type": "table"}],
                [{"type": "indicator"}, {"type": "gauge"}, {"type": "indicator"}]
            ],
            row_heights=[0.2, 0.5, 0.3]
        )
        
        # Row 1: KPI Indicators
        fig.add_trace(
            go.Indicator(
                mode="number+delta+gauge",
                value=metrics.get('conversion_rate', 2.5),
                delta={'reference': 2.0, 'relative': True},
                gauge={'axis': {'range': [0, 5]},
                      'bar': {'color': self.colors['success']},
                      'steps': [
                          {'range': [0, 1], 'color': self.colors['danger']},
                          {'range': [1, 2], 'color': self.colors['warning']},
                          {'range': [2, 5], 'color': self.colors['success']}
                      ],
                      'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': 2}},
                title={'text': "Conversion Rate %"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=metrics.get('active_users', 342),
                delta={'reference': 320},
                title={'text': "Active Users"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=metrics.get('revenue_today', 4532),
                delta={'reference': 4000, 'relative': True, 'valueformat': ".0%"},
                title={'text': "Revenue Today ($)"},
                number={'prefix': "$"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=1, col=3
        )
        
        # Row 2: Charts
        # Hourly conversions
        hours = list(range(24))
        conversions = metrics.get('hourly_conversions', [10 + np.random.randint(-5, 5) for _ in hours])
        
        fig.add_trace(
            go.Scatter(
                x=hours,
                y=conversions,
                mode='lines+markers',
                fill='tozeroy',
                marker_color=self.colors['primary'],
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Mini activation funnel
        fig.add_trace(
            go.Funnel(
                y=['Views', 'Claims', 'Active'],
                x=[1000, 25, 15],
                textinfo="value",
                marker_color=[self.colors['primary'], self.colors['secondary'], self.colors['success']],
                showlegend=False
            ),
            row=2, col=2
        )
        
        # Alert table
        alerts = metrics.get('recent_alerts', [])
        if alerts:
            fig.add_trace(
                go.Table(
                    header=dict(values=['Time', 'Alert', 'Severity'],
                               fill_color=self.colors['dark'],
                               font_color='white'),
                    cells=dict(values=[
                        [a['time'] for a in alerts],
                        [a['message'] for a in alerts],
                        [a['severity'] for a in alerts]
                    ],
                    fill_color=[['white', 'lightgray'] * len(alerts)],
                    font_color='black')
                ),
                row=2, col=3
            )
        
        # Row 3: Status Indicators
        # XP Reset Progress
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics.get('xp_reset_progress', 75),
                gauge={'axis': {'range': [0, 100]},
                      'bar': {'color': self.colors['info']}},
                title={'text': "XP Reset Progress %"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=3, col=1
        )
        
        # Churn Risk Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics.get('churn_risk', 25),
                gauge={'axis': {'range': [0, 100]},
                      'bar': {'color': self.colors['warning']},
                      'steps': [
                          {'range': [0, 30], 'color': "lightgreen"},
                          {'range': [30, 70], 'color': "yellow"},
                          {'range': [70, 100], 'color': "red"}
                      ]},
                title={'text': "Churn Risk %"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=3, col=2
        )
        
        # System Health
        fig.add_trace(
            go.Indicator(
                mode="number+gauge",
                value=metrics.get('system_health', 98),
                gauge={'axis': {'range': [0, 100]},
                      'bar': {'color': "green"}},
                title={'text': "System Health %"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=3, col=3
        )
        
        # Update layout
        fig.update_layout(
            title="Press Pass Real-Time Monitoring Dashboard",
            height=900,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa'
        )
        
        # Update axes
        fig.update_xaxes(title_text="Hour (GMT)", row=2, col=1)
        fig.update_yaxes(title_text="Conversions", row=2, col=1)
        
        return fig
    
    def export_dashboard_html(self, fig: go.Figure, filename: str):
        """Export interactive dashboard to HTML file"""
        fig.write_html(filename, include_plotlyjs='cdn')
        logger.info(f"Dashboard exported to {filename}")
    
    def create_comparison_chart(self, current_data: Dict[str, Any], 
                               previous_data: Dict[str, Any],
                               period: str = "Daily") -> go.Figure:
        """Create comparison chart between two periods"""
        
        metrics = ['Conversions', 'Activation Rate', 'Revenue', 'Churn Rate']
        current_values = [
            current_data['funnel']['claims']['total'],
            current_data['activation']['summary']['overall_activation_rate'],
            current_data['revenue']['revenue']['total'],
            current_data['churn']['churn_rates']['7_day']
        ]
        previous_values = [
            previous_data['funnel']['claims']['total'],
            previous_data['activation']['summary']['overall_activation_rate'],
            previous_data['revenue']['revenue']['total'],
            previous_data['churn']['churn_rates']['7_day']
        ]
        
        # Calculate percentage changes
        changes = []
        for curr, prev in zip(current_values, previous_values):
            if prev > 0:
                change = ((curr - prev) / prev) * 100
            else:
                change = 100 if curr > 0 else 0
            changes.append(change)
        
        # Create grouped bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name=f'Previous {period}',
            x=metrics,
            y=previous_values,
            marker_color=self.colors['secondary'],
            text=[f'{v:,.0f}' if i != 1 else f'{v:.1f}%' for i, v in enumerate(previous_values)],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name=f'Current {period}',
            x=metrics,
            y=current_values,
            marker_color=self.colors['primary'],
            text=[f'{v:,.0f}' if i != 1 else f'{v:.1f}%' for i, v in enumerate(current_values)],
            textposition='auto'
        ))
        
        # Add change annotations
        for i, (metric, change) in enumerate(zip(metrics, changes)):
            color = self.colors['success'] if change > 0 else self.colors['danger']
            symbol = '↑' if change > 0 else '↓'
            
            fig.add_annotation(
                x=i,
                y=max(current_values[i], previous_values[i]) * 1.1,
                text=f"{symbol} {abs(change):.1f}%",
                showarrow=False,
                font=dict(color=color, size=12, family="Arial Black")
            )
        
        fig.update_layout(
            title=f"{period} Performance Comparison",
            xaxis_title="Metrics",
            yaxis_title="Value",
            barmode='group',
            showlegend=True,
            plot_bgcolor='white',
            height=500
        )
        
        return fig