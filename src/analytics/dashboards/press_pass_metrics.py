"""
Press Pass Analytics Dashboard Queries

Provides comprehensive SQL queries and data aggregation functions
for monitoring Press Pass conversion metrics and KPIs.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class PressPassMetricsDashboard:
    """Analytics dashboard for Press Pass conversion metrics"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    # ==========================================
    # CORE CONVERSION METRICS
    # ==========================================
    
    async def get_conversion_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get full conversion funnel metrics for Press Pass
        
        Returns:
            - Landing page views
            - Press Pass claims (conversions)
            - Demo account activations
            - First trade completions
            - Tier upgrades
            - Retention rates
        """
        query = """
        WITH funnel_stages AS (
            -- Stage 1: Landing page views (from analytics events)
            SELECT COUNT(DISTINCT session_id) as landing_views
            FROM analytics_events
            WHERE event_name = 'page_view'
                AND page_path = '/press-pass'
                AND created_at BETWEEN %s AND %s
        ),
        press_pass_claims AS (
            -- Stage 2: Press Pass activations
            SELECT 
                COUNT(DISTINCT user_id) as total_claims,
                COUNT(DISTINCT CASE 
                    WHEN metadata->>'source' = 'organic' THEN user_id 
                END) as organic_claims,
                COUNT(DISTINCT CASE 
                    WHEN metadata->>'source' = 'paid' THEN user_id 
                END) as paid_claims
            FROM user_subscriptions
            WHERE plan_id = (SELECT plan_id FROM subscription_plans WHERE tier = 'PRESS_PASS')
                AND created_at BETWEEN %s AND %s
        ),
        demo_activations AS (
            -- Stage 3: Demo account activations
            SELECT COUNT(DISTINCT user_id) as demo_activated
            FROM users
            WHERE tier = 'PRESS_PASS'
                AND mt5_connected = TRUE
                AND created_at BETWEEN %s AND %s
        ),
        first_trades AS (
            -- Stage 4: First trade completion
            SELECT COUNT(DISTINCT user_id) as completed_first_trade
            FROM trades
            WHERE trade_id IN (
                SELECT MIN(trade_id) 
                FROM trades 
                GROUP BY user_id
            )
            AND created_at BETWEEN %s AND %s
        ),
        tier_upgrades AS (
            -- Stage 5: Upgrades from Press Pass
            SELECT 
                COUNT(DISTINCT user_id) as total_upgrades,
                SUM(CASE WHEN new_tier = 'NIBBLER' THEN 1 ELSE 0 END) as to_nibbler,
                SUM(CASE WHEN new_tier = 'FANG' THEN 1 ELSE 0 END) as to_fang,
                SUM(CASE WHEN new_tier = 'COMMANDER' THEN 1 ELSE 0 END) as to_commander,
                SUM(CASE WHEN new_tier = '' THEN 1 ELSE 0 END) as to_apex
            FROM (
                SELECT 
                    user_id,
                    tier as new_tier,
                    LAG(tier) OVER (PARTITION BY user_id ORDER BY created_at) as prev_tier
                FROM user_subscription_history
            ) tier_changes
            WHERE prev_tier = 'PRESS_PASS'
                AND new_tier != 'PRESS_PASS'
                AND created_at BETWEEN %s AND %s
        )
        SELECT 
            f.landing_views,
            p.total_claims,
            p.organic_claims,
            p.paid_claims,
            d.demo_activated,
            t.completed_first_trade,
            u.total_upgrades,
            u.to_nibbler,
            u.to_fang,
            u.to_commander,
            u.to_apex,
            -- Conversion rates
            ROUND(p.total_claims::numeric / NULLIF(f.landing_views, 0) * 100, 2) as landing_to_claim_rate,
            ROUND(d.demo_activated::numeric / NULLIF(p.total_claims, 0) * 100, 2) as claim_to_demo_rate,
            ROUND(t.completed_first_trade::numeric / NULLIF(d.demo_activated, 0) * 100, 2) as demo_to_trade_rate,
            ROUND(u.total_upgrades::numeric / NULLIF(p.total_claims, 0) * 100, 2) as claim_to_upgrade_rate
        FROM funnel_stages f
        CROSS JOIN press_pass_claims p
        CROSS JOIN demo_activations d
        CROSS JOIN first_trades t
        CROSS JOIN tier_upgrades u;
        """
        
        params = [start_date, end_date] * 5
        result = await self.db.fetch_one(query, params)
        
        return {
            'funnel': {
                'landing_views': result['landing_views'],
                'claims': {
                    'total': result['total_claims'],
                    'organic': result['organic_claims'],
                    'paid': result['paid_claims']
                },
                'demo_activated': result['demo_activated'],
                'first_trade': result['completed_first_trade'],
                'upgrades': {
                    'total': result['total_upgrades'],
                    'by_tier': {
                        'nibbler': result['to_nibbler'],
                        'fang': result['to_fang'],
                        'commander': result['to_commander'],
                        'apex': result['to_apex']
                    }
                }
            },
            'conversion_rates': {
                'landing_to_claim': float(result['landing_to_claim_rate'] or 0),
                'claim_to_demo': float(result['claim_to_demo_rate'] or 0),
                'demo_to_trade': float(result['demo_to_trade_rate'] or 0),
                'claim_to_upgrade': float(result['claim_to_upgrade_rate'] or 0)
            }
        }
    
    async def get_xp_reset_metrics(self, date: datetime) -> Dict[str, Any]:
        """
        Get XP reset metrics for midnight GMT
        
        Returns:
            - Total users affected
            - Total XP reset
            - Average XP per user
            - Distribution by tier
        """
        query = """
        WITH daily_xp AS (
            SELECT 
                u.user_id,
                u.tier,
                up.total_xp,
                -- Calculate XP earned today
                COALESCE(SUM(x.amount), 0) as xp_earned_today
            FROM users u
            JOIN user_profiles up ON u.user_id = up.user_id
            LEFT JOIN xp_transactions x ON u.user_id = x.user_id
                AND DATE(x.created_at) = DATE(%s)
            WHERE u.tier = 'PRESS_PASS'
                AND u.subscription_status = 'ACTIVE'
            GROUP BY u.user_id, u.tier, up.total_xp
        )
        SELECT 
            COUNT(*) as total_users,
            SUM(xp_earned_today) as total_xp_reset,
            ROUND(AVG(xp_earned_today), 2) as avg_xp_per_user,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY xp_earned_today) as median_xp,
            MAX(xp_earned_today) as max_xp_earned,
            COUNT(CASE WHEN xp_earned_today > 0 THEN 1 END) as active_users,
            COUNT(CASE WHEN xp_earned_today = 0 THEN 1 END) as inactive_users
        FROM daily_xp;
        """
        
        result = await self.db.fetch_one(query, [date])
        
        return {
            'reset_date': date.isoformat(),
            'metrics': {
                'total_users': result['total_users'],
                'total_xp_reset': result['total_xp_reset'],
                'avg_xp_per_user': float(result['avg_xp_per_user'] or 0),
                'median_xp': float(result['median_xp'] or 0),
                'max_xp_earned': result['max_xp_earned'],
                'active_users': result['active_users'],
                'inactive_users': result['inactive_users'],
                'activity_rate': round(result['active_users'] / max(result['total_users'], 1) * 100, 2)
            }
        }
    
    async def get_activation_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get detailed activation metrics for Press Pass users
        
        Returns:
            - Time to first trade
            - Activation rate by cohort
            - Feature adoption rates
        """
        query = """
        WITH user_cohorts AS (
            SELECT 
                u.user_id,
                u.created_at,
                DATE_TRUNC('day', u.created_at) as cohort_date,
                up.onboarding_completed,
                up.profile_completed,
                MIN(t.created_at) as first_trade_at,
                COUNT(DISTINCT t.trade_id) as total_trades
            FROM users u
            JOIN user_profiles up ON u.user_id = up.user_id
            LEFT JOIN trades t ON u.user_id = t.user_id
            WHERE u.tier = 'PRESS_PASS'
                AND u.created_at BETWEEN %s AND %s
            GROUP BY u.user_id, u.created_at, up.onboarding_completed, up.profile_completed
        )
        SELECT 
            cohort_date,
            COUNT(*) as cohort_size,
            COUNT(CASE WHEN first_trade_at IS NOT NULL THEN 1 END) as activated_users,
            COUNT(CASE WHEN onboarding_completed THEN 1 END) as completed_onboarding,
            COUNT(CASE WHEN profile_completed THEN 1 END) as completed_profile,
            -- Time to activation metrics
            AVG(EXTRACT(EPOCH FROM (first_trade_at - created_at))/3600) as avg_hours_to_first_trade,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (first_trade_at - created_at))/3600
            ) as median_hours_to_first_trade,
            -- Activation rates
            ROUND(COUNT(CASE WHEN first_trade_at IS NOT NULL THEN 1 END)::numeric / 
                  NULLIF(COUNT(*), 0) * 100, 2) as activation_rate,
            -- Average trades per activated user
            AVG(CASE WHEN total_trades > 0 THEN total_trades END) as avg_trades_per_active_user
        FROM user_cohorts
        GROUP BY cohort_date
        ORDER BY cohort_date DESC;
        """
        
        results = await self.db.fetch_all(query, [start_date, end_date])
        
        cohorts = []
        for row in results:
            cohorts.append({
                'date': row['cohort_date'].isoformat(),
                'size': row['cohort_size'],
                'activated': row['activated_users'],
                'completed_onboarding': row['completed_onboarding'],
                'completed_profile': row['completed_profile'],
                'activation_rate': float(row['activation_rate'] or 0),
                'avg_hours_to_activate': float(row['avg_hours_to_first_trade'] or 0),
                'median_hours_to_activate': float(row['median_hours_to_first_trade'] or 0),
                'avg_trades_per_user': float(row['avg_trades_per_active_user'] or 0)
            })
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'cohorts': cohorts,
            'summary': {
                'total_users': sum(c['size'] for c in cohorts),
                'total_activated': sum(c['activated'] for c in cohorts),
                'overall_activation_rate': round(
                    sum(c['activated'] for c in cohorts) / 
                    max(sum(c['size'] for c in cohorts), 1) * 100, 2
                )
            }
        }
    
    async def get_retention_metrics(self, cohort_date: datetime) -> Dict[str, Any]:
        """
        Get retention metrics for a specific Press Pass cohort
        
        Returns:
            - D1, D3, D7, D14, D30 retention
            - Activity retention (trades)
            - Upgrade retention
        """
        query = """
        WITH cohort_users AS (
            SELECT user_id, created_at
            FROM users
            WHERE tier = 'PRESS_PASS'
                AND DATE(created_at) = DATE(%s)
        ),
        retention_data AS (
            SELECT 
                cu.user_id,
                cu.created_at,
                -- Login retention
                MAX(CASE WHEN l.login_date = cu.created_at::date + 1 THEN 1 ELSE 0 END) as d1_login,
                MAX(CASE WHEN l.login_date = cu.created_at::date + 3 THEN 1 ELSE 0 END) as d3_login,
                MAX(CASE WHEN l.login_date = cu.created_at::date + 7 THEN 1 ELSE 0 END) as d7_login,
                MAX(CASE WHEN l.login_date = cu.created_at::date + 14 THEN 1 ELSE 0 END) as d14_login,
                MAX(CASE WHEN l.login_date = cu.created_at::date + 30 THEN 1 ELSE 0 END) as d30_login,
                -- Trade activity retention
                MAX(CASE WHEN t.trade_date = cu.created_at::date + 1 THEN 1 ELSE 0 END) as d1_trade,
                MAX(CASE WHEN t.trade_date = cu.created_at::date + 3 THEN 1 ELSE 0 END) as d3_trade,
                MAX(CASE WHEN t.trade_date = cu.created_at::date + 7 THEN 1 ELSE 0 END) as d7_trade,
                MAX(CASE WHEN t.trade_date = cu.created_at::date + 14 THEN 1 ELSE 0 END) as d14_trade,
                MAX(CASE WHEN t.trade_date = cu.created_at::date + 30 THEN 1 ELSE 0 END) as d30_trade,
                -- Upgrade status
                MAX(CASE WHEN u.tier != 'PRESS_PASS' THEN 1 ELSE 0 END) as upgraded
            FROM cohort_users cu
            LEFT JOIN (
                SELECT user_id, DATE(created_at) as login_date
                FROM user_login_history
            ) l ON cu.user_id = l.user_id
            LEFT JOIN (
                SELECT user_id, DATE(created_at) as trade_date
                FROM trades
            ) t ON cu.user_id = t.user_id
            LEFT JOIN users u ON cu.user_id = u.user_id
            GROUP BY cu.user_id, cu.created_at
        )
        SELECT 
            COUNT(*) as cohort_size,
            -- Login retention rates
            ROUND(AVG(d1_login) * 100, 2) as d1_login_retention,
            ROUND(AVG(d3_login) * 100, 2) as d3_login_retention,
            ROUND(AVG(d7_login) * 100, 2) as d7_login_retention,
            ROUND(AVG(d14_login) * 100, 2) as d14_login_retention,
            ROUND(AVG(d30_login) * 100, 2) as d30_login_retention,
            -- Trade retention rates
            ROUND(AVG(d1_trade) * 100, 2) as d1_trade_retention,
            ROUND(AVG(d3_trade) * 100, 2) as d3_trade_retention,
            ROUND(AVG(d7_trade) * 100, 2) as d7_trade_retention,
            ROUND(AVG(d14_trade) * 100, 2) as d14_trade_retention,
            ROUND(AVG(d30_trade) * 100, 2) as d30_trade_retention,
            -- Upgrade rate
            ROUND(AVG(upgraded) * 100, 2) as upgrade_rate
        FROM retention_data;
        """
        
        result = await self.db.fetch_one(query, [cohort_date])
        
        return {
            'cohort_date': cohort_date.isoformat(),
            'cohort_size': result['cohort_size'],
            'retention': {
                'login': {
                    'D1': float(result['d1_login_retention'] or 0),
                    'D3': float(result['d3_login_retention'] or 0),
                    'D7': float(result['d7_login_retention'] or 0),
                    'D14': float(result['d14_login_retention'] or 0),
                    'D30': float(result['d30_login_retention'] or 0)
                },
                'trade_activity': {
                    'D1': float(result['d1_trade_retention'] or 0),
                    'D3': float(result['d3_trade_retention'] or 0),
                    'D7': float(result['d7_trade_retention'] or 0),
                    'D14': float(result['d14_trade_retention'] or 0),
                    'D30': float(result['d30_trade_retention'] or 0)
                }
            },
            'upgrade_rate': float(result['upgrade_rate'] or 0)
        }
    
    async def get_revenue_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get revenue metrics from Press Pass conversions
        
        Returns:
            - Total revenue from upgrades
            - LTV by cohort
            - Revenue by upgrade tier
        """
        query = """
        WITH press_pass_users AS (
            SELECT 
                u.user_id,
                u.created_at as press_pass_start,
                MIN(CASE WHEN u.tier != 'PRESS_PASS' THEN ush.created_at END) as upgrade_date,
                MIN(CASE WHEN u.tier != 'PRESS_PASS' THEN u.tier END) as upgrade_tier
            FROM users u
            LEFT JOIN user_subscription_history ush ON u.user_id = ush.user_id
            WHERE u.created_at BETWEEN %s AND %s
                AND EXISTS (
                    SELECT 1 FROM user_subscription_history 
                    WHERE user_id = u.user_id AND tier = 'PRESS_PASS'
                )
            GROUP BY u.user_id, u.created_at
        ),
        revenue_data AS (
            SELECT 
                ppu.user_id,
                ppu.press_pass_start,
                ppu.upgrade_date,
                ppu.upgrade_tier,
                COALESCE(SUM(pt.amount), 0) as total_revenue,
                COUNT(DISTINCT pt.transaction_id) as transaction_count,
                MAX(pt.created_at) as last_payment_date
            FROM press_pass_users ppu
            LEFT JOIN payment_transactions pt ON ppu.user_id = pt.user_id
                AND pt.status = 'completed'
                AND pt.created_at >= ppu.upgrade_date
            GROUP BY ppu.user_id, ppu.press_pass_start, ppu.upgrade_date, ppu.upgrade_tier
        )
        SELECT 
            COUNT(DISTINCT user_id) as total_users,
            COUNT(DISTINCT CASE WHEN upgrade_date IS NOT NULL THEN user_id END) as upgraded_users,
            SUM(total_revenue) as total_revenue,
            AVG(CASE WHEN total_revenue > 0 THEN total_revenue END) as avg_revenue_per_paying_user,
            -- Revenue by tier
            SUM(CASE WHEN upgrade_tier = 'NIBBLER' THEN total_revenue ELSE 0 END) as nibbler_revenue,
            SUM(CASE WHEN upgrade_tier = 'FANG' THEN total_revenue ELSE 0 END) as fang_revenue,
            SUM(CASE WHEN upgrade_tier = 'COMMANDER' THEN total_revenue ELSE 0 END) as commander_revenue,
            SUM(CASE WHEN upgrade_tier = '' THEN total_revenue ELSE 0 END) as apex_revenue,
            -- Time to upgrade
            AVG(EXTRACT(EPOCH FROM (upgrade_date - press_pass_start))/86400) as avg_days_to_upgrade,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (upgrade_date - press_pass_start))/86400
            ) as median_days_to_upgrade
        FROM revenue_data;
        """
        
        result = await self.db.fetch_one(query, [start_date, end_date])
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'users': {
                'total': result['total_users'],
                'upgraded': result['upgraded_users'],
                'conversion_rate': round(
                    result['upgraded_users'] / max(result['total_users'], 1) * 100, 2
                )
            },
            'revenue': {
                'total': float(result['total_revenue'] or 0),
                'avg_per_paying_user': float(result['avg_revenue_per_paying_user'] or 0),
                'by_tier': {
                    'nibbler': float(result['nibbler_revenue'] or 0),
                    'fang': float(result['fang_revenue'] or 0),
                    'commander': float(result['commander_revenue'] or 0),
                    'apex': float(result['apex_revenue'] or 0)
                }
            },
            'time_to_upgrade': {
                'avg_days': float(result['avg_days_to_upgrade'] or 0),
                'median_days': float(result['median_days_to_upgrade'] or 0)
            }
        }
    
    async def get_churn_metrics(self, date: datetime) -> Dict[str, Any]:
        """
        Get churn metrics for Press Pass users
        
        Returns:
            - Daily/weekly/monthly churn rates
            - Churn by engagement level
            - Win-back potential
        """
        query = """
        WITH press_pass_activity AS (
            SELECT 
                u.user_id,
                u.created_at,
                u.subscription_expires_at,
                up.last_trade_at,
                u.last_login_at,
                COUNT(DISTINCT t.trade_id) as total_trades,
                COUNT(DISTINCT DATE(t.created_at)) as trading_days,
                MAX(t.created_at) as last_trade_date,
                -- Engagement scoring
                CASE 
                    WHEN COUNT(DISTINCT t.trade_id) >= 10 AND 
                         COUNT(DISTINCT DATE(t.created_at)) >= 5 THEN 'high'
                    WHEN COUNT(DISTINCT t.trade_id) >= 3 THEN 'medium'
                    WHEN COUNT(DISTINCT t.trade_id) >= 1 THEN 'low'
                    ELSE 'inactive'
                END as engagement_level
            FROM users u
            JOIN user_profiles up ON u.user_id = up.user_id
            LEFT JOIN trades t ON u.user_id = t.user_id
                AND t.created_at >= u.created_at
            WHERE u.tier = 'PRESS_PASS'
                AND u.created_at <= %s - INTERVAL '30 days'
            GROUP BY u.user_id, u.created_at, u.subscription_expires_at, 
                     up.last_trade_at, u.last_login_at
        ),
        churn_analysis AS (
            SELECT 
                user_id,
                created_at,
                subscription_expires_at,
                engagement_level,
                -- Churn indicators
                CASE WHEN last_login_at < %s - INTERVAL '7 days' THEN 1 ELSE 0 END as churned_7d,
                CASE WHEN last_login_at < %s - INTERVAL '14 days' THEN 1 ELSE 0 END as churned_14d,
                CASE WHEN last_login_at < %s - INTERVAL '30 days' THEN 1 ELSE 0 END as churned_30d,
                CASE WHEN subscription_expires_at < %s THEN 1 ELSE 0 END as expired,
                -- Days since last activity
                EXTRACT(DAY FROM %s - last_login_at) as days_inactive,
                EXTRACT(DAY FROM %s - last_trade_date) as days_since_last_trade
            FROM press_pass_activity
        )
        SELECT 
            COUNT(*) as total_users,
            -- Churn rates
            ROUND(AVG(churned_7d) * 100, 2) as churn_rate_7d,
            ROUND(AVG(churned_14d) * 100, 2) as churn_rate_14d,
            ROUND(AVG(churned_30d) * 100, 2) as churn_rate_30d,
            ROUND(AVG(expired) * 100, 2) as expiry_rate,
            -- Churn by engagement
            COUNT(CASE WHEN engagement_level = 'high' AND churned_7d = 1 THEN 1 END) as high_engagement_churned,
            COUNT(CASE WHEN engagement_level = 'medium' AND churned_7d = 1 THEN 1 END) as medium_engagement_churned,
            COUNT(CASE WHEN engagement_level = 'low' AND churned_7d = 1 THEN 1 END) as low_engagement_churned,
            COUNT(CASE WHEN engagement_level = 'inactive' AND churned_7d = 1 THEN 1 END) as inactive_churned,
            -- Win-back potential
            COUNT(CASE WHEN churned_7d = 1 AND engagement_level IN ('high', 'medium') THEN 1 END) as high_value_churned,
            AVG(days_inactive) as avg_days_inactive,
            AVG(days_since_last_trade) as avg_days_since_trade
        FROM churn_analysis;
        """
        
        params = [date] * 7
        result = await self.db.fetch_one(query, params)
        
        return {
            'date': date.isoformat(),
            'total_users': result['total_users'],
            'churn_rates': {
                '7_day': float(result['churn_rate_7d'] or 0),
                '14_day': float(result['churn_rate_14d'] or 0),
                '30_day': float(result['churn_rate_30d'] or 0),
                'expired': float(result['expiry_rate'] or 0)
            },
            'churn_by_engagement': {
                'high': result['high_engagement_churned'],
                'medium': result['medium_engagement_churned'],
                'low': result['low_engagement_churned'],
                'inactive': result['inactive_churned']
            },
            'win_back_potential': {
                'high_value_churned': result['high_value_churned'],
                'avg_days_inactive': float(result['avg_days_inactive'] or 0),
                'avg_days_since_trade': float(result['avg_days_since_trade'] or 0)
            }
        }