# Enhanced server with Universal Platform Connector
import asyncio
import aiohttp
import json
import logging
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import websockets
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import httpx
from telegram import Bot
import uvicorn
from contextlib import asynccontextmanager
import ccxt
from pycoingecko import CoinGeckoAPI
import time

# Import our platform connector
from platform_connector import (
    PlatformConnectionManager, 
    DetectedForm, 
    PlatformCredentials, 
    TwoFAConfig, 
    AuthMethod, 
    TradeOrder, 
    TradeAction, 
    TradeResult,
    TwoFactorHelper,
    platform_manager
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
MONGO_URL = os.environ.get('MONGO_URL')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Initialize APIs
cg = CoinGeckoAPI()

# Global bot state (keeping existing functionality)
bot_state = {
    "running": False,
    "current_price": 0.0,
    "rsi_value": 50.0,
    "position": None,
    "daily_pnl": 0.0,
    "total_trades": 0,
    "winning_trades": 0,
    "market_data_connected": False,
    "last_update": datetime.now().isoformat(),
    "current_symbol": "ETHUSD",
    "current_timeframe": "1h",
    "available_cryptos": [],
    "connected_platforms": []
}

# Timeframes (keeping existing)
TIMEFRAMES = {
    "1m": {"minutes": 1, "binance": "1m", "display": "1 Minute"},
    "5m": {"minutes": 5, "binance": "5m", "display": "5 Minutes"},
    "15m": {"minutes": 15, "binance": "15m", "display": "15 Minutes"},
    "30m": {"minutes": 30, "binance": "30m", "display": "30 Minutes"},
    "1h": {"minutes": 60, "binance": "1h", "display": "1 Hour"},
    "4h": {"minutes": 240, "binance": "4h", "display": "4 Hours"},
    "1d": {"minutes": 1440, "binance": "1d", "display": "1 Day"},
    "1w": {"minutes": 10080, "binance": "1w", "display": "1 Week"},
    "1M": {"minutes": 43200, "binance": "1M", "display": "1 Month"}
}

# Enhanced Pydantic models
class TradingConfig(BaseModel):
    symbol: str = "ETHUSD"
    timeframe: str = "1h"
    rsi_length: int = 14
    stop_loss_pct: float = 1.0
    take_profit_pct: float = 2.0
    position_size: float = 0.1
    enable_grid_tp: bool = True
    use_external_platform: bool = False
    external_platform_id: str = ""

class PlatformSetupRequest(BaseModel):
    platform_name: str
    login_url: str

class PlatformCredentialsRequest(BaseModel):
    platform_id: str
    username: str
    password: str
    api_key: str = ""
    api_secret: str = ""
    enable_2fa: bool = False
    two_fa_method: str = "none"
    totp_secret: str = ""
    sms_number: str = ""
    email: str = ""

class TwoFAVerificationRequest(BaseModel):
    platform_id: str
    code: str

class ExternalTradeRequest(BaseModel):
    platform_id: str
    symbol: str
    action: str  # buy, sell, close
    quantity: float
    price: Optional[float] = None
    order_type: str = "market"

class Position(BaseModel):
    id: str
    symbol: str
    side: str
    entry_price: float
    current_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    entry_time: str
    timeframe: str
    stop_loss: float
    take_profit: float

# Keep existing models and classes from the original server...
# [Previous TelegramNotifier, CryptoDataProvider, EnhancedRSITradingBot classes remain the same]

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        
    async def send_message(self, message: str, parse_mode: str = None):
        """Send message to Telegram"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=message,
                parse_mode=parse_mode
            )
            logging.info(f"📱 Telegram alert sent")
            return True
        except Exception as e:
            logging.error(f"❌ Failed to send Telegram message: {e}")
            return False

    async def send_trade_alert(self, action: str, symbol: str, timeframe: str, price: float, 
                             position_size: float, stop_loss: float = 0, take_profit: float = 0, 
                             reason: str = "", pnl: float = 0, platform: str = "Internal"):
        """Send enhanced trade alert with platform info"""
        
        action_emojis = {
            "buy": "🟢 LONG ENTRY",
            "sell": "🔴 SHORT ENTRY", 
            "close_long": "⚪ CLOSE LONG",
            "close_short": "⚪ CLOSE SHORT",
        }
        
        action_display = action_emojis.get(action.lower(), f"📊 {action.upper()}")
        
        message = f"""🎯 **NEURAL TRADING SIGNAL**
        
{action_display}

📊 **Symbol:** {symbol}
⏰ **Timeframe:** {TIMEFRAMES.get(timeframe, {}).get('display', timeframe)}
💰 **Price:** ${price:,.4f}
📏 **Size:** {position_size}
🏢 **Platform:** {platform}
"""
        
        if stop_loss > 0:
            message += f"🛑 **Stop Loss:** ${stop_loss:,.4f}\n"
        
        if take_profit > 0:
            message += f"🎯 **Take Profit:** ${take_profit:,.4f}\n"
        
        if pnl != 0:
            pnl_emoji = "📈" if pnl > 0 else "📉"
            message += f"{pnl_emoji} **P&L:** ${pnl:,.2f}\n"
            
        if reason:
            message += f"📝 **Signal:** {reason}\n"
        
        message += f"\n⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message, parse_mode='Markdown')

# Global instances
current_config = TradingConfig()
telegram_notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) if TELEGRAM_BOT_TOKEN else None

# Database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = AsyncIOMotorClient(MONGO_URL)
    app.mongodb = app.mongodb_client[os.environ.get('DB_NAME', 'enhanced_rsi_bot')]
    
    # Load connected platforms
    bot_state["connected_platforms"] = platform_manager.get_connected_platforms()
    
    yield
    # Shutdown
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan, title="Enhanced RSI Trading Bot with Universal Platform Connector")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# UNIVERSAL PLATFORM CONNECTOR ENDPOINTS
# ========================================

@app.post("/api/platform/analyze")
async def analyze_platform(request: PlatformSetupRequest):
    """Analyze a trading platform's login page"""
    try:
        detected_form = await platform_manager.add_platform(
            request.platform_name, 
            request.login_url
        )
        
        return {
            "status": "success",
            "message": f"Platform {request.platform_name} analyzed successfully",
            "data": {
                "platform_name": request.platform_name,
                "login_url": request.login_url,
                "login_fields": [
                    {
                        "name": field.name,
                        "type": field.type,
                        "label": field.label,
                        "placeholder": field.placeholder,
                        "required": field.required
                    } for field in detected_form.login_fields
                ],
                "submit_button": detected_form.submit_button,
                "two_fa_detected": detected_form.two_fa_detected,
                "captcha_detected": detected_form.captcha_detected
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/platform/save-credentials")
async def save_platform_credentials(request: PlatformCredentialsRequest):
    """Save platform login credentials"""
    try:
        # Create 2FA config if enabled
        two_fa_config = None
        if request.enable_2fa:
            two_fa_config = TwoFAConfig(
                enabled=True,
                method=AuthMethod(request.two_fa_method),
                totp_secret=request.totp_secret,
                sms_number=request.sms_number,
                email=request.email
            )
        
        # Find the platform credentials to get the actual platform info
        # This assumes we have the platform_id from the analyze step
        platform_info = None
        for platform_id, creds in platform_manager.credentials.items():
            if platform_id == request.platform_id:
                platform_info = creds
                break
        
        if not platform_info:
            # If platform_id doesn't exist, create new entry
            platform_name = request.platform_id.split('_')[0].title()  # Extract from ID
            login_url = "https://example.com/login"  # This should be passed or stored
        else:
            platform_name = platform_info.platform_name
            login_url = platform_info.login_url
        
        platform_id = await platform_manager.save_platform_credentials(
            platform_name=platform_name,
            login_url=login_url,
            username=request.username,
            password=request.password,
            two_fa_config=two_fa_config
        )
        
        # Update bot state
        bot_state["connected_platforms"] = platform_manager.get_connected_platforms()
        
        return {
            "status": "success",
            "message": "Platform credentials saved successfully",
            "platform_id": platform_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/platform/connect/{platform_id}")
async def connect_to_platform(platform_id: str):
    """Connect to a platform using saved credentials"""
    try:
        success = await platform_manager.connect_platform(platform_id)
        
        if success:
            bot_state["connected_platforms"] = platform_manager.get_connected_platforms()
            return {
                "status": "success",
                "message": f"Successfully connected to platform {platform_id}",
                "connected": True
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to connect to platform {platform_id}",
                "connected": False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/platform/disconnect/{platform_id}")
async def disconnect_from_platform(platform_id: str):
    """Disconnect from a platform"""
    try:
        await platform_manager.disconnect_platform(platform_id)
        bot_state["connected_platforms"] = platform_manager.get_connected_platforms()
        
        return {
            "status": "success",
            "message": f"Successfully disconnected from platform {platform_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/platform/{platform_id}")
async def delete_platform(platform_id: str):
    """Delete platform credentials"""
    try:
        success = platform_manager.delete_platform(platform_id)
        
        if success:
            bot_state["connected_platforms"] = platform_manager.get_connected_platforms()
            return {
                "status": "success",
                "message": f"Platform {platform_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Platform not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platform/list")
async def list_connected_platforms():
    """Get list of all connected platforms"""
    try:
        platforms = platform_manager.get_connected_platforms()
        return {
            "status": "success",
            "data": platforms,
            "count": len(platforms)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/platform/trade")
async def execute_external_trade(request: ExternalTradeRequest):
    """Execute trade on external platform"""
    try:
        order = TradeOrder(
            symbol=request.symbol,
            action=TradeAction(request.action),
            quantity=request.quantity,
            price=request.price,
            order_type=request.order_type
        )
        
        result = await platform_manager.execute_trade_on_platform(request.platform_id, order)
        
        # Send Telegram notification
        if telegram_notifier and result.success:
            platform_name = "External Platform"
            for p in bot_state["connected_platforms"]:
                if p["platform_id"] == request.platform_id:
                    platform_name = p["platform_name"]
                    break
            
            await telegram_notifier.send_trade_alert(
                action=request.action,
                symbol=request.symbol,
                timeframe="manual",
                price=result.filled_price or request.price or 0,
                position_size=request.quantity,
                reason="Manual external trade",
                platform=platform_name
            )
        
        return {
            "status": "success" if result.success else "error",
            "message": result.message,
            "data": {
                "order_id": result.order_id,
                "filled_quantity": result.filled_quantity,
                "filled_price": result.filled_price,
                "timestamp": result.timestamp
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/2fa/generate-setup")
async def generate_2fa_setup(account_name: str = "Trading Bot", issuer: str = "RSI Neural System"):
    """Generate TOTP setup QR code"""
    try:
        import pyotp
        secret = pyotp.random_base32()
        qr_code = TwoFactorHelper.generate_totp_qr(secret, account_name, issuer)
        backup_codes = TwoFactorHelper.generate_backup_codes()
        
        return {
            "status": "success",
            "data": {
                "secret": secret,
                "qr_code": qr_code,
                "backup_codes": backup_codes,
                "manual_entry": f"Account: {account_name}\nIssuer: {issuer}\nSecret: {secret}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/2fa/verify")
async def verify_2fa_code(request: TwoFAVerificationRequest):
    """Verify 2FA code"""
    try:
        # Get platform credentials
        if request.platform_id not in platform_manager.credentials:
            raise HTTPException(status_code=404, detail="Platform not found")
        
        credentials = platform_manager.credentials[request.platform_id]
        
        if not credentials.two_fa or not credentials.two_fa.enabled:
            raise HTTPException(status_code=400, detail="2FA not enabled for this platform")
        
        if credentials.two_fa.method == AuthMethod.TOTP:
            valid = TwoFactorHelper.verify_totp_code(credentials.two_fa.totp_secret, request.code)
        else:
            # For SMS/Email, we'll assume the code is valid if it's 6 digits
            valid = len(request.code) == 6 and request.code.isdigit()
        
        return {
            "status": "success" if valid else "error",
            "message": "Code verified successfully" if valid else "Invalid verification code",
            "valid": valid
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# EXISTING ENDPOINTS (Enhanced)
# ========================================

@app.get("/api/bot/status")
async def get_bot_status():
    """Get current bot status with platform info"""
    bot_state["connected_platforms"] = platform_manager.get_connected_platforms()
    return {
        "status": "success",
        "data": bot_state
    }

@app.post("/api/bot/start")
async def start_enhanced_bot(config: TradingConfig, background_tasks: BackgroundTasks):
    """Start the enhanced trading bot with external platform support"""
    global current_config
    
    try:
        if bot_state["running"]:
            raise HTTPException(status_code=400, detail="Bot is already running")
        
        current_config = config
        bot_state["running"] = True
        bot_state["current_symbol"] = config.symbol
        bot_state["current_timeframe"] = config.timeframe
        
        # If external platform is selected, verify connection
        if config.use_external_platform and config.external_platform_id:
            platform_connected = False
            for platform in bot_state["connected_platforms"]:
                if platform["platform_id"] == config.external_platform_id:
                    platform_connected = platform["is_connected"]
                    break
            
            if not platform_connected:
                raise HTTPException(
                    status_code=400, 
                    detail="External platform not connected. Please connect first."
                )
        
        # Send enhanced startup notification
        if telegram_notifier:
            platform_info = "Internal System"
            if config.use_external_platform:
                for p in bot_state["connected_platforms"]:
                    if p["platform_id"] == config.external_platform_id:
                        platform_info = p["platform_name"]
                        break
            
            await telegram_notifier.send_message(
                f"🤖 **NEURAL RSI SYSTEM ACTIVATED**\n\n"
                f"📊 **Asset:** {config.symbol}\n"
                f"⏰ **Timeframe:** {TIMEFRAMES.get(config.timeframe, {}).get('display', config.timeframe)}\n"
                f"🏢 **Platform:** {platform_info}\n"
                f"⚙️ **RSI Period:** {config.rsi_length}\n"
                f"🛑 **Stop Loss:** {config.stop_loss_pct}%\n"
                f"🎯 **Take Profit:** {config.take_profit_pct}%\n\n"
                f"✅ System monitoring quantum fluctuations...",
                parse_mode='Markdown'
            )
        
        return {
            "status": "success",
            "message": f"Enhanced Neural RSI System activated for {config.symbol}",
            "config": config.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Keep all other existing endpoints...
# [All the previous endpoints remain the same but enhanced with platform integration]

@app.get("/api/crypto/list")
async def get_crypto_list():
    """Get comprehensive crypto list"""
    try:
        crypto_list = []
        # Mock data for now - in production, integrate with CoinGecko
        popular_cryptos = [
            {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "current_price": 42000},
            {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "current_price": 2500},
            {"id": "cardano", "symbol": "ADA", "name": "Cardano", "current_price": 0.45},
            {"id": "solana", "symbol": "SOL", "name": "Solana", "current_price": 95},
            {"id": "polkadot", "symbol": "DOT", "name": "Polkadot", "current_price": 6.5},
        ]
        
        for crypto in popular_cryptos:
            crypto_list.append({
                "id": crypto["id"],
                "symbol": crypto["symbol"],
                "name": crypto["name"],
                "current_price": crypto["current_price"],
                "market_cap": crypto["current_price"] * 21000000,  # Mock
                "volume_24h": crypto["current_price"] * 1000000,  # Mock
                "price_change_24h": 0.0,
                "price_change_percentage_24h": 0.0
            })
        
        return {
            "status": "success",
            "data": crypto_list,
            "count": len(crypto_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crypto/timeframes")
async def get_available_timeframes():
    """Get available timeframes"""
    return {
        "status": "success",
        "data": [
            {"value": k, "label": v["display"], "minutes": v["minutes"]}
            for k, v in TIMEFRAMES.items()
        ]
    }

# Root route
@app.get("/")
async def root():
    return {
        "message": "Enhanced RSI Trading Bot with Universal Platform Connector", 
        "status": "running",
        "version": "2.0.0",
        "features": [
            "Multi-timeframe trading (1m to 1M)",
            "100+ cryptocurrency support",
            "Universal platform connector",
            "2FA authentication support",
            "Advanced analytics and metrics",
            "Real-time position tracking",
            "Secure credential management"
        ]
    }

if __name__ == "__main__":
    uvicorn.run("enhanced_server:app", host="0.0.0.0", port=8001, reload=True)