"""
BITTEN v2.0 API Server - Main Application
FastAPI REST API + WebSocket + Telegram Bot Integration
"""
import logging
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import time

# Add parent directory to path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.api_server.config import (
    API_HOST,
    API_PORT,
    DEBUG,
    TEMPLATE_DIR,
    STATIC_DIR,
    ALLOWED_ORIGINS
)
from services.api_server.models import HealthResponse
from services.api_server.rest import signals, fires, users, status, notebook, snapshot, candles, alerts
from services.api_server.websocket.signal_stream import signal_stream_manager
from services.api_server.websocket.position_stream import position_stream_manager
from services.api_server.tg_bot.bot import telegram_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting BITTEN v2.0 API Server...")

    # Start Telegram bot
    try:
        await telegram_bot.start()
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")

    # Start heartbeat task
    asyncio.create_task(signal_stream_manager.send_heartbeat())

    logger.info("BITTEN v2.0 API Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down BITTEN v2.0 API Server...")
    try:
        await telegram_bot.stop()
    except Exception as e:
        logger.error(f"Error stopping Telegram bot: {e}")

    logger.info("BITTEN v2.0 API Server stopped")


# Create FastAPI application
app = FastAPI(
    title="BITTEN v2.0 API",
    description="Bot-Integrated Tactical Trading Engine/Network API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware - ENABLED - Required for OPTIONS preflight handling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Don't send credentials
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers including Authorization
    expose_headers=["*"],  # Allow all headers to be exposed to client
)

# Mount static files and templates
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=int(time.time()),
        version="2.0.0",
        services={
            "api": "online",
            "websocket": "online",
            "telegram": "online" if telegram_bot.application else "offline",
            "database": "online"
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "BITTEN v2.0 API Server",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "signals": "/api/signals",
            "users": "/api/users",
            "websocket_signals": "/ws/signals",
            "websocket_positions": "/ws/positions",
            "war_room": "/me",
            "mission_briefing": "/brief",
            "connect": "/connect"
        }
    }


# ============================================================================
# REST API Routes
# ============================================================================

app.include_router(signals.router)
app.include_router(fires.router)
app.include_router(users.router)
app.include_router(status.router)
app.include_router(notebook.router)  # Norman's Notebook API
app.include_router(snapshot.router)  # Chart Snapshot API
app.include_router(candles.router)  # Historical Candles API
app.include_router(alerts.router)  # Alert Feed API


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """WebSocket endpoint for signal streaming"""
    await signal_stream_manager.connect(websocket)
    logger.info(f"New signal stream connection: {websocket.client}")

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_json({"type": "pong", "timestamp": int(time.time())})

    except WebSocketDisconnect:
        signal_stream_manager.disconnect(websocket)
        logger.info(f"Signal stream disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        signal_stream_manager.disconnect(websocket)


@app.websocket("/ws/positions/{user_id}")
async def websocket_positions(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for position streaming"""
    await position_stream_manager.connect(websocket, user_id)
    logger.info(f"New position stream connection for user {user_id}: {websocket.client}")

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_json({"type": "pong", "timestamp": int(time.time())})

    except WebSocketDisconnect:
        position_stream_manager.disconnect(websocket, user_id)
        logger.info(f"Position stream disconnected for user {user_id}: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        position_stream_manager.disconnect(websocket, user_id)


# ============================================================================
# HTML Page Routes
# ============================================================================

@app.get("/me", response_class=HTMLResponse)
async def war_room(request: Request):
    """War Room - User dashboard"""
    return templates.TemplateResponse(
        "war_room.html",
        {"request": request, "title": "War Room"}
    )


@app.get("/brief", response_class=HTMLResponse)
async def mission_briefing(request: Request):
    """Mission Briefing"""
    return templates.TemplateResponse(
        "mission_briefing.html",
        {"request": request, "title": "Mission Briefing"}
    )


@app.get("/connect", response_class=HTMLResponse)
async def connect_terminal(request: Request):
    """MT5 Connection Onboarding"""
    return templates.TemplateResponse(
        "connect.html",
        {"request": request, "title": "Connect MT5"}
    )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG,
        log_level="info"
    )
