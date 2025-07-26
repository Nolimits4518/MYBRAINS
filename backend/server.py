import asyncio
import aiohttp
import json
import logging
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import websockets
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import httpx
from telegram import Bot
import uvicorn
from contextlib import asynccontextmanager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
MONGO_URL = os.environ.get('MONGO_URL')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Global bot state
bot_state = {
    "running": False,
    "current_price": 0.0,
    "rsi_value": 50.0,
    "position": None,
    "daily_pnl": 0.0,
    "total_trades": 0,
    "winning_trades": 0,
    "market_data_connected": False,
    "last_update": datetime.now().isoformat()
}

# Pydantic models
class TradingConfig(BaseModel):
    symbol: str = "ETHUSD"
    rsi_length: int = 14
    stop_loss_pct: float = 1.0
    take_profit_pct: float = 2.0
    position_size: float = 0.1
    enable_grid_tp: bool = True

class Position(BaseModel):
    id: str
    symbol: str
    side: str
    entry_price: float
    current_price: float
    quantity: float
    pnl: float
    created_at: str

class TradeAlert(BaseModel):
    action: str
    symbol: str
    price: float
    timestamp: str
    reason: str

# Database models
@dataclass
class TradeState:
    entry_price: Optional[float] = None
    trade_count: int = 0
    candle_count_since_signal: int = 0
    is_buy_active: bool = False
    is_sell_active: bool = False
    grid_level: int = 0
    dot_colors: List[str] = None
    current_position_id: Optional[str] = None
    daily_pnl: float = 0.0
    total_trades_today: int = 0
    winning_trades: int = 0

    def __post_init__(self):
        if self.dot_colors is None:
            self.dot_colors = []

# Global instances
current_config = TradingConfig()
trade_state = TradeState()

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

    async def send_trade_alert(self, action: str, symbol: str, price: float, 
                             stop_loss: float = 0, take_profit: float = 0, 
                             reason: str = "", level: str = ""):
        """Send formatted trade alert"""
        
        action_emojis = {
            "buy": "🟢 LONG",
            "sell": "🔴 SHORT", 
            "close_long": "⚪ CLOSE LONG",
            "close_short": "⚪ CLOSE SHORT",
            "close_partial_33": "💰 PARTIAL CLOSE (33%)",
            "close_partial_50": "💰 PARTIAL CLOSE (50%)",
            "close_all": "💰 FULL CLOSE"
        }
        
        action_display = action_emojis.get(action.lower(), f"📊 {action.upper()}")
        
        message = f"""🎯 **RSI TRADING SIGNAL**
        
{action_display}

📊 **Symbol:** {symbol}
💰 **Price:** ${price:,.2f}
"""
        
        if stop_loss > 0:
            message += f"🛑 **Stop Loss:** ${stop_loss:,.2f}\n"
        
        if take_profit > 0:
            message += f"🎯 **Take Profit:** ${take_profit:,.2f}\n"
        
        if level:
            message += f"📊 **Level:** {level}\n"
            
        if reason:
            message += f"📝 **Reason:** {reason}\n"
        
        message += f"\n⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message, parse_mode='Markdown')

class MarketDataFeed:
    def __init__(self, symbol: str = "ETHUSD"):
        self.symbol = symbol
        self.running = False
        self.callbacks = []
        self.binance_symbol = self.convert_to_binance_format(symbol)
        
    def convert_to_binance_format(self, symbol: str) -> str:
        symbol_map = {
            "ETHUSD": "ethusdt",
            "BTCUSD": "btcusdt"
        }
        return symbol_map.get(symbol.upper(), "ethusdt")
        
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    async def start_feed(self):
        """Start market data feed with real Binance WebSocket"""
        self.running = True
        
        url = f"wss://stream.binance.com:9443/ws/{self.binance_symbol}@ticker"
        logging.info(f"🔄 Starting market data feed for {self.symbol}")
        
        while self.running:
            try:
                async with websockets.connect(url) as websocket:
                    logging.info(f"✅ Connected to Binance WebSocket for {self.symbol}")
                    bot_state["market_data_connected"] = True
                    
                    while self.running:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=30)
                            data = json.loads(message)
                            
                            price = float(data.get('c', 0))
                            if price > 0:
                                bot_state["current_price"] = price
                                bot_state["last_update"] = datetime.now().isoformat()
                                
                                for callback in self.callbacks:
                                    await callback(price)
                        
                        except asyncio.TimeoutError:
                            logging.warning("⚠️ WebSocket timeout - reconnecting...")
                            break
                        except websockets.exceptions.ConnectionClosed:
                            logging.warning("⚠️ WebSocket connection closed - reconnecting...")
                            break
                        except Exception as e:
                            logging.error(f"❌ WebSocket error: {e}")
                            await asyncio.sleep(5)
                            
            except Exception as e:
                logging.error(f"❌ Failed to connect to WebSocket: {e}")
                bot_state["market_data_connected"] = False
                # Fallback to simulated data
                await self.start_simulated_feed()
                await asyncio.sleep(10)
    
    async def start_simulated_feed(self):
        """Fallback simulated feed"""
        base_prices = {
            "ETHUSD": 2500.0,
            "BTCUSD": 42000.0
        }
        
        base_price = base_prices.get(self.symbol, 2500.0)
        
        for _ in range(10):  # Simulate 10 price updates
            if not self.running:
                break
                
            change_pct = np.random.normal(0, 0.002)
            base_price *= (1 + change_pct)
            
            if self.symbol == "ETHUSD":
                base_price = max(2000, min(4000, base_price))
            elif self.symbol == "BTCUSD":
                base_price = max(35000, min(50000, base_price))
            
            bot_state["current_price"] = base_price
            bot_state["last_update"] = datetime.now().isoformat()
            
            for callback in self.callbacks:
                await callback(base_price)
            
            await asyncio.sleep(2)
    
    def stop(self):
        self.running = False

class RSITradingBot:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.price_history = []
        self.rsi_history = []
        self.telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) if TELEGRAM_BOT_TOKEN else None
        self.market_feed = MarketDataFeed(config.symbol)
        self.market_feed.add_callback(self.on_price_update)
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def check_buy_signal(self, rsi_current: float, rsi_prev: float) -> bool:
        """Check for buy signal"""
        if len(trade_state.dot_colors) < 3:
            return False
        
        rsi_crossover_50 = rsi_prev <= 50 < rsi_current
        rsi_was_40_50 = 40 < rsi_prev < 50
        rsi_rising = rsi_current > rsi_prev
        third_last_green = trade_state.dot_colors[-3] == "green"
        
        return rsi_crossover_50 and rsi_was_40_50 and rsi_rising and third_last_green
    
    def check_sell_signal(self, rsi_current: float, rsi_prev: float) -> bool:
        """Check for sell signal"""
        rsi_crossunder_50 = rsi_prev >= 50 > rsi_current
        rsi_was_50_60 = 50 < rsi_prev < 60
        rsi_falling = rsi_current < rsi_prev
        
        return rsi_crossunder_50 and rsi_was_50_60 and rsi_falling
    
    async def execute_trade_signal(self, signal_type: str, price: float):
        """Execute trade signal"""
        try:
            if signal_type == "buy":
                trade_state.entry_price = price
                trade_state.is_buy_active = True
                trade_state.is_sell_active = False
                stop_loss = price * (1 - self.config.stop_loss_pct / 100)
                take_profit = price * (1 + self.config.take_profit_pct / 100)
                
                bot_state["position"] = {
                    "side": "LONG",
                    "entry_price": price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "quantity": self.config.position_size
                }
                
                if self.telegram:
                    await self.telegram.send_trade_alert(
                        action="buy",
                        symbol=self.config.symbol,
                        price=price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        reason="RSI bullish signal confirmed"
                    )
            
            elif signal_type == "sell":
                trade_state.entry_price = price
                trade_state.is_buy_active = False
                trade_state.is_sell_active = True
                stop_loss = price * (1 + self.config.stop_loss_pct / 100)
                take_profit = price * (1 - self.config.take_profit_pct / 100)
                
                bot_state["position"] = {
                    "side": "SHORT",
                    "entry_price": price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "quantity": self.config.position_size
                }
                
                if self.telegram:
                    await self.telegram.send_trade_alert(
                        action="sell",
                        symbol=self.config.symbol,
                        price=price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        reason="RSI bearish signal confirmed"
                    )
            
            trade_state.total_trades_today += 1
            bot_state["total_trades"] = trade_state.total_trades_today
            
            logging.info(f"✅ {signal_type.upper()} signal executed at ${price:,.2f}")
            
        except Exception as e:
            logging.error(f"❌ Failed to execute {signal_type} signal: {e}")
    
    async def on_price_update(self, price: float):
        """Handle new price data"""
        try:
            self.price_history.append(price)
            if len(self.price_history) > 200:
                self.price_history = self.price_history[-200:]
            
            if len(self.price_history) < self.config.rsi_length + 2:
                return
            
            # Calculate RSI
            rsi_current = self.calculate_rsi(self.price_history)
            rsi_prev = self.calculate_rsi(self.price_history[:-1])
            
            bot_state["rsi_value"] = rsi_current
            
            # Track RSI 50 crosses
            if rsi_prev <= 50 < rsi_current:
                trade_state.dot_colors.append("green")
            elif rsi_prev >= 50 > rsi_current:
                trade_state.dot_colors.append("red")
            
            if len(trade_state.dot_colors) > 10:
                trade_state.dot_colors = trade_state.dot_colors[-10:]
            
            # Check for entry signals (only if no position)
            if not trade_state.is_buy_active and not trade_state.is_sell_active:
                if self.check_buy_signal(rsi_current, rsi_prev):
                    await self.execute_trade_signal("buy", price)
                elif self.check_sell_signal(rsi_current, rsi_prev):
                    await self.execute_trade_signal("sell", price)
            
            # Update P&L for existing positions
            if bot_state["position"]:
                entry = bot_state["position"]["entry_price"]
                if bot_state["position"]["side"] == "LONG":
                    pnl = (price - entry) * bot_state["position"]["quantity"]
                else:
                    pnl = (entry - price) * bot_state["position"]["quantity"]
                
                bot_state["daily_pnl"] = pnl
                trade_state.daily_pnl = pnl
            
        except Exception as e:
            logging.error(f"❌ Error processing price update: {e}")
    
    async def start_trading(self):
        """Start the trading bot"""
        try:
            bot_state["running"] = True
            
            if self.telegram:
                await self.telegram.send_message(
                    "🤖 **RSI Trading Bot Started**\n\n"
                    f"📊 Symbol: {self.config.symbol}\n"
                    f"⚙️ RSI Period: {self.config.rsi_length}\n"
                    f"🛑 Stop Loss: {self.config.stop_loss_pct}%\n"
                    f"🎯 Take Profit: {self.config.take_profit_pct}%\n\n"
                    "✅ Bot is now monitoring the market...",
                    parse_mode='Markdown'
                )
            
            logging.info("🚀 RSI Trading Bot started successfully")
            
            # Start market data feed
            await self.market_feed.start_feed()
            
        except Exception as e:
            logging.error(f"❌ Failed to start bot: {e}")
    
    def stop_trading(self):
        """Stop the trading bot"""
        bot_state["running"] = False
        self.market_feed.stop()

# Global bot instance
trading_bot = None

# Database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = AsyncIOMotorClient(MONGO_URL)
    app.mongodb = app.mongodb_client[os.environ.get('DB_NAME', 'rsi_trading_bot')]
    yield
    # Shutdown
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/api/bot/status")
async def get_bot_status():
    """Get current bot status"""
    return {
        "status": "success",
        "data": bot_state
    }

@app.post("/api/bot/start")
async def start_bot(config: TradingConfig, background_tasks: BackgroundTasks):
    """Start the trading bot"""
    global trading_bot, current_config
    
    try:
        if bot_state["running"]:
            raise HTTPException(status_code=400, detail="Bot is already running")
        
        current_config = config
        trading_bot = RSITradingBot(config)
        
        # Start bot in background
        background_tasks.add_task(trading_bot.start_trading)
        
        return {
            "status": "success",
            "message": "Trading bot started successfully",
            "config": config.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot/stop")
async def stop_bot():
    """Stop the trading bot"""
    global trading_bot
    
    try:
        if not bot_state["running"]:
            raise HTTPException(status_code=400, detail="Bot is not running")
        
        if trading_bot:
            trading_bot.stop_trading()
        
        bot_state["running"] = False
        bot_state["position"] = None
        
        return {
            "status": "success",
            "message": "Trading bot stopped successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bot/config")
async def get_config():
    """Get current bot configuration"""
    return {
        "status": "success",
        "data": current_config.dict()
    }

@app.post("/api/bot/config")
async def update_config(config: TradingConfig):
    """Update bot configuration"""
    global current_config
    current_config = config
    
    return {
        "status": "success",
        "message": "Configuration updated successfully",
        "data": config.dict()
    }

@app.get("/api/trades/history")
async def get_trade_history():
    """Get trade history"""
    try:
        trades_collection = app.mongodb["trades"]
        trades = []
        async for trade in trades_collection.find().sort("timestamp", -1).limit(50):
            trade["_id"] = str(trade["_id"])
            trades.append(trade)
        
        return {
            "status": "success",
            "data": trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trades/save")
async def save_trade(trade: TradeAlert):
    """Save trade to database"""
    try:
        trades_collection = app.mongodb["trades"]
        trade_doc = trade.dict()
        trade_doc["timestamp"] = datetime.now().isoformat()
        
        result = await trades_collection.insert_one(trade_doc)
        
        return {
            "status": "success",
            "message": "Trade saved successfully",
            "trade_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/price/{symbol}")
async def get_market_price(symbol: str):
    """Get current market price"""
    try:
        # For now, return the current price from bot state
        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "price": bot_state["current_price"],
                "timestamp": bot_state["last_update"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telegram/test")
async def test_telegram():
    """Test Telegram connection"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            raise HTTPException(status_code=400, detail="Telegram token not configured")
        
        # First, test bot info
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        try:
            # Get bot information
            bot_info = await bot.get_me()
            logging.info(f"Bot info: {bot_info.username} - {bot_info.first_name}")
            
            # Try to send message
            telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            success = await telegram.send_message("🧪 **Telegram Test Message**\n\nBot connection is working correctly!", parse_mode='Markdown')
            
            if success:
                return {
                    "status": "success", 
                    "message": "Telegram test message sent successfully",
                    "bot_info": {
                        "username": bot_info.username,
                        "name": bot_info.first_name,
                        "chat_id": TELEGRAM_CHAT_ID
                    }
                }
            else:
                return {
                    "status": "error", 
                    "message": f"Failed to send message to chat {TELEGRAM_CHAT_ID}",
                    "bot_info": {
                        "username": bot_info.username,
                        "name": bot_info.first_name,
                        "working": True
                    },
                    "troubleshooting": [
                        f"Bot @{bot_info.username} is working correctly",
                        f"Issue: Cannot send message to chat ID {TELEGRAM_CHAT_ID}",
                        "Solution: Make sure you've started a chat with the bot first",
                        "Steps: 1) Find bot @{} on Telegram, 2) Send /start command, 3) Try test again".format(bot_info.username)
                    ]
                }
        except Exception as chat_error:
            # Bot token works but chat issue
            try:
                bot_info = await bot.get_me()
                return {
                    "status": "error", 
                    "message": f"Chat error: {str(chat_error)}",
                    "bot_info": {
                        "username": bot_info.username,
                        "name": bot_info.first_name,
                        "working": True
                    },
                    "chat_id": TELEGRAM_CHAT_ID,
                    "error_details": str(chat_error)
                }
            except Exception as bot_error:
                return {
                    "status": "error",
                    "message": f"Bot token error: {str(bot_error)}",
                    "token_provided": bool(TELEGRAM_BOT_TOKEN),
                    "chat_id": TELEGRAM_CHAT_ID
                }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root route
@app.get("/")
async def root():
    return {"message": "RSI Trading Bot API", "status": "running"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)