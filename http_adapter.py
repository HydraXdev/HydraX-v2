#!/usr/bin/env python3
"""
HydraSocket HTTP Fallback Adapter v1.0
Accepts HTTP POST requests and forwards to local TCP sockets
For EA WebRequest() fallback when TCP sockets are blocked
"""

import asyncio
import os
import socket

import uvicorn
from fastapi import FastAPI, Request, Response

# Configuration
ROUTER_HOST = "127.0.0.1"
EVT_PORT = int(os.getenv("HY_EVT_PORT", "5559"))
MET_PORT = int(os.getenv("HY_MET_PORT", "6000"))
HTTP_PORT = int(os.getenv("HY_HTTP_PORT", "8088"))

app = FastAPI(title="HydraSocket HTTP Adapter")


async def forward_lines(port: int, raw: bytes):
    """Forward JSONL lines to TCP socket"""
    try:
        lines = raw.decode("utf-8", "ignore").splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple TCP connect-per-line (quick & reliable)
            try:
                reader, writer = await asyncio.open_connection(ROUTER_HOST, port)
                writer.write((line + "\n").encode("utf-8"))
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                print(f"[HTTP Adapter] Forward error to {ROUTER_HOST}:{port} - {e}")
                # Silently swallow - rely on EA retry
    except Exception as e:
        print(f"[HTTP Adapter] Decode error - {e}")


@app.post("/events")
async def post_events(req: Request):
    """Accept event stream from EA WebRequest"""
    raw = await req.body()
    await forward_lines(EVT_PORT, raw)
    return Response(content="ok\n", media_type="text/plain")


@app.post("/metrics")
async def post_metrics(req: Request):
    """Accept metrics stream from EA WebRequest"""
    raw = await req.body()
    await forward_lines(MET_PORT, raw)
    return Response(content="ok\n", media_type="text/plain")


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "adapter": "http_fallback", "version": "1.0"}


if __name__ == "__main__":
    print(f"[HydraSocket HTTP Adapter] Starting on port {HTTP_PORT}")
    print(f"  POST /events   → tcp://{ROUTER_HOST}:{EVT_PORT}")
    print(f"  POST /metrics  → tcp://{ROUTER_HOST}:{MET_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT, log_level="info")
