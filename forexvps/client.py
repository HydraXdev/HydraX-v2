"""
ForexVPS API Client
Replaces Docker/Wine container communication with network API calls
"""
import asyncio
import aiohttp
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import json

from config.settings import FOREXVPS_CONFIG

logger = logging.getLogger(__name__)

class ForexVPSClient:
    """ForexVPS API client for trade execution and account management"""
    
    def __init__(self):
        self.base_url = FOREXVPS_CONFIG["base_url"]
        self.headers = FOREXVPS_CONFIG["headers"]
        self.timeout = FOREXVPS_CONFIG["timeout"]
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def execute_trade(self, user_id: str, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute trade via ForexVPS API
        Replaces: docker exec mt5_user_{user_id} + fire.txt
        """
        start_time = time.time()
        request_id = f"TRADE_{user_id}_{int(time.time())}"
        
        payload = {
            "request_id": request_id,
            "user_id": user_id,
            "action": "execute_trade",
            "trade_data": {
                "symbol": trade_data.get("symbol"),
                "direction": trade_data.get("direction"),
                "volume": trade_data.get("volume", trade_data.get("lot", 0.01)),
                "stop_loss": trade_data.get("stop_loss", trade_data.get("sl")),
                "take_profit": trade_data.get("take_profit", trade_data.get("tp")),
                "comment": trade_data.get("comment", f"BITTEN_{request_id}")
            }
        }
        
        try:
            logger.info(f"Executing trade for user {user_id}: {trade_data['symbol']} {trade_data['direction']}")
            
            async with self.session.post(
                f"{self.base_url}/execute_trade",
                json=payload
            ) as response:
                response_time = int((time.time() - start_time) * 1000)
                response_data = await response.json()
                
                if response.status == 200:
                    logger.info(f"Trade executed successfully for user {user_id}: {response_data}")
                    return {
                        "status": "success",
                        "request_id": request_id,
                        "response_time_ms": response_time,
                        "trade_result": response_data,
                        "broker_ticket": response_data.get("ticket"),
                        "execution_price": response_data.get("execution_price"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"Trade execution failed for user {user_id}: {response.status} - {response_data}")
                    return {
                        "status": "error",
                        "request_id": request_id,
                        "response_time_ms": response_time,
                        "error_code": response.status,
                        "error_message": response_data.get("error", "Unknown error"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except asyncio.TimeoutError:
            logger.error(f"Trade execution timeout for user {user_id}")
            return {
                "status": "error",
                "request_id": request_id,
                "error_code": "TIMEOUT",
                "error_message": "ForexVPS API timeout",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Trade execution error for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "request_id": request_id,
                "error_code": "API_ERROR",
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_account_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get account information via ForexVPS API
        Replaces: Reading MT5 account files from container
        """
        try:
            async with self.session.get(
                f"{self.base_url}/account_info",
                params={"user_id": user_id}
            ) as response:
                if response.status == 200:
                    account_data = await response.json()
                    return {
                        "status": "success",
                        "account": account_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    error_data = await response.json()
                    return {
                        "status": "error",
                        "error_code": response.status,
                        "error_message": error_data.get("error", "Failed to get account info"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            logger.error(f"Account info error for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "error_code": "API_ERROR",
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register user with ForexVPS
        Replaces: Container creation and credential injection
        """
        try:
            payload = {
                "user_id": user_data.get("telegram_id"),
                "credentials": {
                    "login": user_data.get("mt5_login"),
                    "password": user_data.get("mt5_password"),
                    "server": user_data.get("mt5_server")
                },
                "tier": user_data.get("tier", "NIBBLER")
            }
            
            async with self.session.post(
                f"{self.base_url}/register_user",
                json=payload
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    logger.info(f"User registered successfully: {user_data.get('telegram_id')}")
                    return {
                        "status": "success",
                        "vps_account_id": response_data.get("account_id"),
                        "terminal_status": response_data.get("terminal_status"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"User registration failed: {response.status} - {response_data}")
                    return {
                        "status": "error",
                        "error_code": response.status,
                        "error_message": response_data.get("error", "Registration failed"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            logger.error(f"User registration error: {str(e)}")
            return {
                "status": "error",
                "error_code": "API_ERROR",
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close_position(self, user_id: str, symbol: str, ticket: str = None) -> Dict[str, Any]:
        """
        Close position via ForexVPS API
        Replaces: fire.txt close commands
        """
        try:
            payload = {
                "user_id": user_id,
                "action": "close_position",
                "symbol": symbol,
                "ticket": ticket
            }
            
            async with self.session.post(
                f"{self.base_url}/close_position",
                json=payload
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    logger.info(f"Position closed successfully for user {user_id}: {symbol}")
                    return {
                        "status": "success",
                        "closed_ticket": response_data.get("ticket"),
                        "close_price": response_data.get("close_price"),
                        "profit_loss": response_data.get("profit"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "error_code": response.status,
                        "error_message": response_data.get("error", "Failed to close position"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            logger.error(f"Close position error for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "error_code": "API_ERROR",
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ForexVPS API health"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    return {
                        "status": "healthy",
                        "api_status": health_data.get("status"),
                        "response_time": health_data.get("response_time"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error_code": response.status,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Utility functions for backward compatibility
async def execute_trade_forexvps(user_id: str, trade_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute trade via ForexVPS - replaces file-based communication"""
    async with ForexVPSClient() as client:
        return await client.execute_trade(user_id, trade_data)

async def get_account_info_forexvps(user_id: str) -> Dict[str, Any]:
    """Get account info via ForexVPS - replaces container file reading"""
    async with ForexVPSClient() as client:
        return await client.get_account_info(user_id)

async def register_user_forexvps(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Register user with ForexVPS - replaces container creation"""
    async with ForexVPSClient() as client:
        return await client.register_user(user_data)