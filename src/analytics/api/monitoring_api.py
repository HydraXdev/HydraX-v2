"""
API endpoints for Press Pass monitoring dashboard

Provides REST API access to monitoring metrics and reports.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
import logging
import redis
import json
import asyncpg

from src.analytics.dashboards.press_pass_metrics import PressPassMetricsDashboard
from src.analytics.monitoring.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

app = FastAPI(title="Press Pass Monitoring API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connections (initialized on startup)
db_pool = None
redis_client = None
dashboard = None
anomaly_detector = None

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global db_pool, redis_client, dashboard, anomaly_detector
    
    # Initialize database pool
    db_pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="bitten_user",
        password="your_password",
        database="bitten_db",
        min_size=5,
        max_size=10
    )
    
    # Initialize Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Initialize components
    dashboard = PressPassMetricsDashboard(db_pool)
    anomaly_detector = AnomalyDetector()
    
    logger.info("Monitoring API initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if db_pool:
        await db_pool.close()
    if redis_client:
        redis_client.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis
        redis_client.ping()
        
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/metrics/funnel")
async def get_funnel_metrics(
    start_date: Optional[date] = Query(None, description="Start date (defaults to 7 days ago)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)")
):
    """Get conversion funnel metrics"""
    if not start_date:
        start_date = date.today() - timedelta(days=7)
    if not end_date:
        end_date = date.today()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    try:
        metrics = await dashboard.get_conversion_funnel(start_datetime, end_datetime)
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error fetching funnel metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/metrics/activation")
async def get_activation_metrics(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date")
):
    """Get activation metrics"""
    if not start_date:
        start_date = date.today() - timedelta(days=7)
    if not end_date:
        end_date = date.today()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    try:
        metrics = await dashboard.get_activation_metrics(start_datetime, end_datetime)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching activation metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/metrics/retention")
async def get_retention_metrics(
    cohort_date: date = Query(..., description="Cohort date to analyze")
):
    """Get retention metrics for a specific cohort"""
    try:
        metrics = await dashboard.get_retention_metrics(cohort_date)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching retention metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/metrics/revenue")
async def get_revenue_metrics(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date")
):
    """Get revenue metrics"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    try:
        metrics = await dashboard.get_revenue_metrics(start_datetime, end_datetime)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching revenue metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/metrics/xp-reset")
async def get_xp_reset_metrics(
    date: Optional[date] = Query(None, description="Date to check (defaults to today)")
):
    """Get XP reset metrics"""
    if not date:
        date = date.today()
    
    try:
        metrics = await dashboard.get_xp_reset_metrics(date)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching XP reset metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/metrics/churn")
async def get_churn_metrics(
    date: Optional[date] = Query(None, description="Date to check (defaults to today)")
):
    """Get churn metrics"""
    if not date:
        date = date.today()
    
    check_datetime = datetime.combine(date, datetime.max.time())
    
    try:
        metrics = await dashboard.get_churn_metrics(check_datetime)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching churn metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/metrics/realtime")
async def get_realtime_metrics():
    """Get real-time metrics from Redis"""
    try:
        metrics = {}
        
        # Get all real-time metrics from Redis
        for key in redis_client.scan_iter("realtime:*"):
            metric_name = key.replace("realtime:", "")
            value = redis_client.get(key)
            if value:
                metrics[metric_name] = json.loads(value)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error fetching real-time metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/alerts/recent")
async def get_recent_alerts(
    hours: int = Query(24, description="Number of hours to look back")
):
    """Get recent alerts"""
    try:
        # Get alerts from Redis
        alerts = []
        raw_alerts = redis_client.lrange('alerts', 0, 100)
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        for alert_json in raw_alerts:
            alert = json.loads(alert_json)
            alert_time = datetime.fromisoformat(alert['timestamp'])
            if alert_time > cutoff:
                alerts.append(alert)
        
        return {
            "period_hours": hours,
            "total_alerts": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")

@app.get("/anomalies/summary")
async def get_anomaly_summary():
    """Get anomaly detection summary"""
    try:
        summary = anomaly_detector.get_anomaly_summary()
        return summary
    except Exception as e:
        logger.error(f"Error fetching anomaly summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch summary")

@app.post("/snapshot")
async def create_snapshot():
    """Create a snapshot of current metrics"""
    try:
        # Get all current metrics
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=1)
        
        snapshot = {
            "timestamp": end_date.isoformat(),
            "funnel": await dashboard.get_conversion_funnel(start_date, end_date),
            "activation": await dashboard.get_activation_metrics(start_date, end_date),
            "xp_reset": await dashboard.get_xp_reset_metrics(end_date.date()),
            "churn": await dashboard.get_churn_metrics(end_date)
        }
        
        # Store snapshot in Redis with 24 hour TTL
        snapshot_key = f"snapshot:{end_date.strftime('%Y%m%d_%H%M%S')}"
        redis_client.setex(snapshot_key, 86400, json.dumps(snapshot))
        
        return {
            "status": "success",
            "snapshot_key": snapshot_key,
            "timestamp": end_date.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        raise HTTPException(status_code=500, detail="Failed to create snapshot")

@app.get("/reports/available")
async def get_available_reports():
    """Get list of available reports"""
    try:
        # This would query your report storage
        # For now, return mock data
        return {
            "daily_reports": [
                {"date": "2025-01-07", "status": "available"},
                {"date": "2025-01-06", "status": "available"},
                {"date": "2025-01-05", "status": "available"}
            ],
            "weekly_reports": [
                {"week_ending": "2025-01-07", "status": "available"},
                {"week_ending": "2024-12-31", "status": "available"}
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reports")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)