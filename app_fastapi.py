"""
BITTEN FastAPI Application
Production-Ready Async Server with ForexVPS Integration
Replaces Flask webapp_server_optimized.py
"""
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import time
from typing import Dict, Any, Optional, List
import redis
import aioredis
from sqlalchemy.orm import Session

# BITTEN imports
from config.settings import settings, validate_settings
from database.models import get_db, User, Signal, Mission, create_tables
from security.auth import (
    get_current_user, require_tier, check_rate_limit, 
    TelegramAuth, validate_input, auth_manager
)
from forexvps.client import ForexVPSClient, execute_trade_forexvps
from logging.logger import (
    app_logger, forexvps_logger, security_logger, performance_logger,
    setup_logging
)

# Initialize logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="BITTEN Trading System",
    description="ForexVPS-Integrated Trading Platform",
    version="6.2.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Templates
templates = Jinja2Templates(directory="templates")

# Redis connection
redis_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global redis_client
    
    app_logger.info("🚀 Starting BITTEN FastAPI application")
    
    # Validate settings
    try:
        validate_settings()
        app_logger.info("✅ Settings validation passed")
    except ValueError as e:
        app_logger.critical(f"❌ Settings validation failed: {e}")
        raise
    
    # Create database tables
    try:
        create_tables()
        app_logger.info("✅ Database tables created/verified")
    except Exception as e:
        app_logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Initialize Redis
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        app_logger.info("✅ Redis connection established")
    except Exception as e:
        app_logger.warning(f"⚠️ Redis connection failed: {e}")
        redis_client = None
    
    app_logger.info("🎯 BITTEN FastAPI application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_client
    
    app_logger.info("🛑 Shutting down BITTEN FastAPI application")
    
    if redis_client:
        await redis_client.close()
        app_logger.info("✅ Redis connection closed")
    
    app_logger.info("✅ BITTEN FastAPI application shutdown complete")

# Middleware for request logging and performance monitoring
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log requests and monitor performance"""
    start_time = time.time()
    
    # Generate request ID
    request_id = f"req_{int(time.time()*1000)}"
    
    # Log request start
    app_logger.info(
        f"Request started: {request.method} {request.url.path}",
        request_id=request_id
    )
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log completion
        app_logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"({response.status_code}) in {response_time:.3f}s",
            request_id=request_id
        )
        
        # Performance monitoring
        performance_logger.log_request_time(
            endpoint=f"{request.method} {request.url.path}",
            response_time=response_time
        )
        
        return response
        
    except Exception as e:
        response_time = time.time() - start_time
        app_logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"in {response_time:.3f}s - {str(e)}",
            request_id=request_id
        )
        raise

# Health Check Endpoints
@app.get("/health")
async def health_check():
    """System health check"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # Check database
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
        db.close()
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    if redis_client:
        try:
            await redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["services"]["redis"] = "not configured"
    
    # Check ForexVPS
    try:
        async with ForexVPSClient() as client:
            forexvps_health = await client.health_check()
            health_status["services"]["forexvps"] = forexvps_health["status"]
    except Exception as e:
        health_status["services"]["forexvps"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/health/detailed")
async def detailed_health_check(current_user: User = Depends(require_tier("COMMANDER"))):
    """Detailed health check for admins"""
    # Implementation for detailed health metrics
    return {
        "status": "healthy",
        "details": "Admin health check implementation"
    }

# Authentication Endpoints
@app.post("/auth/login")
async def login(telegram_id: str, username: str = None):
    """Authenticate user and return JWT token"""
    try:
        # Validate input
        telegram_id = validate_input(telegram_id, 20)
        
        # Get or create user
        db = next(get_db())
        user = get_user_by_telegram_id(db, telegram_id)
        
        if not user:
            # Create new user
            from database.models import create_user
            user = create_user(db, telegram_id, username)
            app_logger.info(f"New user created: {telegram_id}")
        
        # Generate token
        token = auth_manager.create_access_token({
            "telegram_id": user.telegram_id,
            "username": user.username,
            "tier": user.tier
        })
        
        # Log authentication
        security_logger.log_authentication(user.telegram_id, True)
        
        db.close()
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "tier": user.tier,
                "xp_points": user.xp_points
            }
        }
        
    except Exception as e:
        app_logger.error(f"Login failed for {telegram_id}: {str(e)}")
        security_logger.log_authentication(telegram_id, False)
        raise HTTPException(status_code=400, detail="Authentication failed")

# Signal Management Endpoints
@app.post("/api/signals")
async def receive_signal(
    signal_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_tier("SCOUT"))
):
    """Receive signal from VENOM engine"""
    try:
        # Validate signal data
        required_fields = ["signal_id", "symbol", "direction", "confidence"]
        for field in required_fields:
            if field not in signal_data:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")
        
        # Store signal in database
        db = next(get_db())
        from database.models import create_signal
        
        signal = create_signal(db, signal_data)
        app_logger.info(f"Signal received: {signal.signal_id}")
        
        # Process signal in background
        background_tasks.add_task(process_signal_background, signal.id)
        
        db.close()
        
        return {
            "status": "success",
            "signal_id": signal.signal_id,
            "message": "Signal received and processing"
        }
        
    except Exception as e:
        app_logger.error(f"Signal processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Signal processing failed")

async def process_signal_background(signal_id: str):
    """Process signal in background"""
    # Implementation for signal processing
    app_logger.info(f"Processing signal {signal_id} in background")

# Trading Endpoints
@app.post("/api/fire")
async def execute_trade(
    trade_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute trade via ForexVPS"""
    try:
        # Rate limiting
        check_rate_limit(current_user.telegram_id)
        
        # Validate trade request
        required_fields = ["mission_id", "symbol", "direction"]
        for field in required_fields:
            if field not in trade_request:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")
        
        # Execute trade via ForexVPS
        forexvps_result = await execute_trade_forexvps(
            user_id=current_user.telegram_id,
            trade_data=trade_request
        )
        
        # Log trade execution
        forexvps_logger.log_trade_execution(
            user_id=current_user.telegram_id,
            symbol=trade_request["symbol"],
            direction=trade_request["direction"],
            result=forexvps_result
        )
        
        # Store trade in database
        from database.models import Trade
        trade = Trade(
            trade_id=f"TRADE_{current_user.telegram_id}_{int(time.time())}",
            user_id=current_user.id,
            symbol=trade_request["symbol"],
            direction=trade_request["direction"],
            status="executed" if forexvps_result.get("status") == "success" else "failed",
            forexvps_response=forexvps_result
        )
        
        db.add(trade)
        db.commit()
        
        return {
            "status": forexvps_result.get("status"),
            "trade_id": trade.trade_id,
            "execution_result": forexvps_result
        }
        
    except Exception as e:
        app_logger.error(f"Trade execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Trade execution failed")

# User Management Endpoints
@app.get("/api/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    return {
        "telegram_id": current_user.telegram_id,
        "username": current_user.username,
        "tier": current_user.tier,
        "xp_points": current_user.xp_points,
        "rank": current_user.rank,
        "created_at": current_user.created_at,
        "is_active": current_user.is_active
    }

@app.get("/api/user/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user trading statistics"""
    # Get user trades
    trades = db.query(Trade).filter(Trade.user_id == current_user.id).all()
    
    # Calculate statistics
    total_trades = len(trades)
    successful_trades = len([t for t in trades if t.status == "executed"])
    win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
    
    return {
        "total_trades": total_trades,
        "successful_trades": successful_trades,
        "win_rate": round(win_rate, 2),
        "xp_points": current_user.xp_points,
        "tier": current_user.tier,
        "rank": current_user.rank
    }

# War Room Endpoint (Enhanced from webapp_server_optimized.py)
@app.get("/me", response_class=HTMLResponse)
async def war_room(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """War Room - Military-themed user dashboard"""
    # Get user statistics
    user_stats = {
        "telegram_id": current_user.telegram_id,
        "tier": current_user.tier,
        "xp_points": current_user.xp_points,
        "rank": current_user.rank
    }
    
    return templates.TemplateResponse(
        "war_room.html",
        {
            "request": request,
            "user": user_stats,
            "title": "War Room - Command Center"
        }
    )

# Admin Endpoints
@app.get("/admin/system-status")
async def system_status(current_user: User = Depends(require_tier("COMMANDER"))):
    """System status for administrators"""
    return {
        "status": "operational",
        "version": "6.2.0",
        "architecture": "ForexVPS",
        "message": "System running on FastAPI with ForexVPS integration"
    }

# Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    app_logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "http_error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    app_logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "server_error"}
    )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "BITTEN Trading System API",
        "version": "6.2.0",
        "architecture": "ForexVPS-Integrated",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "docs": "/docs" if settings.DEBUG else "disabled",
            "auth": "/auth/login",
            "signals": "/api/signals",
            "trading": "/api/fire",
            "war_room": "/me"
        }
    }

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "app_fastapi:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=1 if settings.DEBUG else settings.WORKERS,
        reload=settings.DEBUG,
        log_level="info"
    )