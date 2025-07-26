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
from fastapi import FastAPI, HTTPException, BackgroundTasks
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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
MONGO_URL = os.environ.get('MONGO_URL')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Initialize APIs
cg = CoinGeckoAPI()

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
    "last_update": datetime.now().isoformat(),
    "current_symbol": "ETHUSD",
    "current_timeframe": "1h",
    "available_cryptos": []
}

# Timeframe options
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

# Pydantic models
class TradingConfig(BaseModel):
    symbol: str = "ETHUSD"
    timeframe: str = "1h"
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
    pnl_pct: float
    entry_time: str
    timeframe: str
    stop_loss: float
    take_profit: float

class TradeMetrics(BaseModel):
    symbol: str
    timeframe: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    average_profit: float
    average_loss: float
    max_drawdown: float
    sharpe_ratio: float

class CryptoSymbol(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: float
    market_cap: int
    volume_24h: float
    price_change_24h: float
    price_change_percentage_24h: float

class OHLCV(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    rsi: Optional[float] = None

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
    historical_data: List[OHLCV] = None
    trade_history: List[Dict] = None

    def __post_init__(self):
        if self.dot_colors is None:
            self.dot_colors = []
        if self.historical_data is None:
            self.historical_data = []
        if self.trade_history is None:
            self.trade_history = []

# Global instances
current_config = TradingConfig()
trade_state = TradeState()

class CryptoDataProvider:
    def __init__(self):
        self.exchange = ccxt.binance()
        
    async def fetch_crypto_list(self) -> List[CryptoSymbol]:
        """Fetch comprehensive crypto list from CoinGecko"""
        try:
            coins = cg.get_coins_markets(vs_currency='usd', per_page=100, page=1, 
                                       sparkline=False, price_change_percentage='24h')
            
            crypto_list = []
            for coin in coins:
                crypto_list.append(CryptoSymbol(
                    id=coin['id'],
                    symbol=coin['symbol'].upper(),
                    name=coin['name'],
                    current_price=coin['current_price'] or 0,
                    market_cap=coin['market_cap'] or 0,
                    volume_24h=coin['total_volume'] or 0,
                    price_change_24h=coin['price_change_24h'] or 0,
                    price_change_percentage_24h=coin['price_change_percentage_24h'] or 0
                ))
            
            bot_state["available_cryptos"] = [c.dict() for c in crypto_list]
            return crypto_list
            
        except Exception as e:
            logging.error(f"Error fetching crypto list: {e}")
            return []
    
    async def fetch_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Fetch OHLCV data for given symbol and timeframe"""
        try:
            # Convert symbol format for Binance (ETHUSD -> ETH/USDT)
            binance_symbol = self.convert_symbol_format(symbol)
            binance_timeframe = TIMEFRAMES.get(timeframe, {}).get("binance", "1h")
            
            # Fetch data from Binance
            ohlcv = self.exchange.fetch_ohlcv(binance_symbol, binance_timeframe, limit=limit)
            
            result = []
            for candle in ohlcv:
                result.append(OHLCV(
                    timestamp=candle[0],
                    open=candle[1],
                    high=candle[2],
                    low=candle[3],
                    close=candle[4],
                    volume=candle[5]
                ))
            
            # Calculate RSI for the data
            closes = [candle.close for candle in result]
            rsi_values = self.calculate_rsi_series(closes, 14)
            
            for i, rsi in enumerate(rsi_values):
                if i < len(result):
                    result[i].rsi = rsi
            
            return result
            
        except Exception as e:
            logging.error(f"Error fetching OHLCV data: {e}")
            return []
    
    def convert_symbol_format(self, symbol: str) -> str:
        """Convert symbol format for different exchanges"""
        symbol_mapping = {
            "ETHUSD": "ETH/USDT",
            "BTCUSD": "BTC/USDT",
            "ADAUSD": "ADA/USDT",
            "SOLUSD": "SOL/USDT",
            "DOTUSD": "DOT/USDT",
            "LINKUSD": "LINK/USDT",
            "LTCUSD": "LTC/USDT",
            "XRPUSD": "XRP/USDT",
        }
        
        return symbol_mapping.get(symbol.upper(), f"{symbol.replace('USD', '')}/USDT")
    
    def calculate_rsi_series(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate RSI for a series of prices"""
        if len(prices) < period + 1:
            return [50.0] * len(prices)
        
        deltas = []
        for i in range(1, len(prices)):
            deltas.append(prices[i] - prices[i-1])
        
        rsi_values = []
        
        for i in range(len(prices)):
            if i < period:
                rsi_values.append(50.0)
            else:
                recent_deltas = deltas[i-period:i]
                gains = [d if d > 0 else 0 for d in recent_deltas]
                losses = [-d if d < 0 else 0 for d in recent_deltas]
                
                avg_gain = sum(gains) / period
                avg_loss = sum(losses) / period
                
                if avg_loss == 0:
                    rsi = 100.0
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                
                rsi_values.append(rsi)
        
        return rsi_values

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
                             reason: str = "", pnl: float = 0):
        """Send formatted trade alert with enhanced metrics"""
        
        action_emojis = {
            "buy": "🟢 LONG ENTRY",
            "sell": "🔴 SHORT ENTRY", 
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
⏰ **Timeframe:** {TIMEFRAMES.get(timeframe, {}).get('display', timeframe)}
💰 **Price:** ${price:,.4f}
📏 **Position Size:** {position_size}
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

class EnhancedRSITradingBot:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.crypto_provider = CryptoDataProvider()
        self.telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) if TELEGRAM_BOT_TOKEN else None
        self.running = False
        
    async def start_trading(self):
        """Start the enhanced trading bot with timeframe support"""
        try:
            self.running = True
            bot_state["running"] = True
            bot_state["current_symbol"] = self.config.symbol
            bot_state["current_timeframe"] = self.config.timeframe
            
            if self.telegram:
                await self.telegram.send_message(
                    f"🤖 **Enhanced RSI Trading Bot Started**\n\n"
                    f"📊 **Symbol:** {self.config.symbol}\n"
                    f"⏰ **Timeframe:** {TIMEFRAMES.get(self.config.timeframe, {}).get('display', self.config.timeframe)}\n"
                    f"⚙️ **RSI Period:** {self.config.rsi_length}\n"
                    f"🛑 **Stop Loss:** {self.config.stop_loss_pct}%\n"
                    f"🎯 **Take Profit:** {self.config.take_profit_pct}%\n\n"
                    f"✅ Bot is now monitoring {TIMEFRAMES.get(self.config.timeframe, {}).get('display', self.config.timeframe)} timeframe...",
                    parse_mode='Markdown'
                )
            
            logging.info(f"🚀 Enhanced RSI Trading Bot started for {self.config.symbol} on {self.config.timeframe}")
            
            # Start data monitoring loop
            await self.monitor_market_data()
            
        except Exception as e:
            logging.error(f"❌ Failed to start enhanced bot: {e}")
    
    async def monitor_market_data(self):
        """Monitor market data with selected timeframe"""
        while self.running:
            try:
                # Fetch latest OHLCV data
                ohlcv_data = await self.crypto_provider.fetch_ohlcv_data(
                    self.config.symbol, 
                    self.config.timeframe, 
                    limit=50
                )
                
                if ohlcv_data:
                    latest_candle = ohlcv_data[-1]
                    bot_state["current_price"] = latest_candle.close
                    bot_state["rsi_value"] = latest_candle.rsi or 50.0
                    bot_state["last_update"] = datetime.now().isoformat()
                    bot_state["market_data_connected"] = True
                    
                    # Store historical data
                    trade_state.historical_data = ohlcv_data
                    
                    # Check for trading signals
                    await self.check_trading_signals(ohlcv_data)
                    
                    # Update position P&L if in trade
                    if bot_state["position"]:
                        await self.update_position_pnl(latest_candle.close)
                
                # Wait based on timeframe
                wait_time = min(TIMEFRAMES.get(self.config.timeframe, {}).get("minutes", 60) * 60, 300)  # Max 5 minutes
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logging.error(f"❌ Error monitoring market data: {e}")
                bot_state["market_data_connected"] = False
                await asyncio.sleep(60)
    
    async def check_trading_signals(self, ohlcv_data: List[OHLCV]):
        """Enhanced signal detection with timeframe consideration"""
        if len(ohlcv_data) < self.config.rsi_length + 2:
            return
        
        current_rsi = ohlcv_data[-1].rsi
        prev_rsi = ohlcv_data[-2].rsi
        current_price = ohlcv_data[-1].close
        
        if current_rsi is None or prev_rsi is None:
            return
        
        # Enhanced signal logic based on timeframe
        if not trade_state.is_buy_active and not trade_state.is_sell_active:
            # Buy signal: RSI crosses above 30 from oversold
            if prev_rsi <= 30 and current_rsi > 30:
                await self.execute_trade_signal("buy", current_price, "RSI Exit Oversold")
            
            # Sell signal: RSI crosses below 70 from overbought  
            elif prev_rsi >= 70 and current_rsi < 70:
                await self.execute_trade_signal("sell", current_price, "RSI Exit Overbought")
            
            # Additional signals for shorter timeframes
            elif self.config.timeframe in ["1m", "5m", "15m"]:
                # Quick scalping signals
                if prev_rsi <= 40 and current_rsi > 50:
                    await self.execute_trade_signal("buy", current_price, "Quick Bull Signal")
                elif prev_rsi >= 60 and current_rsi < 50:
                    await self.execute_trade_signal("sell", current_price, "Quick Bear Signal")
    
    async def execute_trade_signal(self, signal_type: str, price: float, reason: str):
        """Execute enhanced trade signal with metrics tracking"""
        try:
            trade_id = f"{signal_type}_{int(time.time())}"
            
            if signal_type == "buy":
                trade_state.entry_price = price
                trade_state.is_buy_active = True
                trade_state.is_sell_active = False
                stop_loss = price * (1 - self.config.stop_loss_pct / 100)
                take_profit = price * (1 + self.config.take_profit_pct / 100)
                
                position = Position(
                    id=trade_id,
                    symbol=self.config.symbol,
                    side="LONG",
                    entry_price=price,
                    current_price=price,
                    quantity=self.config.position_size,
                    pnl=0.0,
                    pnl_pct=0.0,
                    entry_time=datetime.now().isoformat(),
                    timeframe=self.config.timeframe,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                bot_state["position"] = position.dict()
                
            elif signal_type == "sell":
                trade_state.entry_price = price
                trade_state.is_buy_active = False
                trade_state.is_sell_active = True
                stop_loss = price * (1 + self.config.stop_loss_pct / 100)
                take_profit = price * (1 - self.config.take_profit_pct / 100)
                
                position = Position(
                    id=trade_id,
                    symbol=self.config.symbol,
                    side="SHORT",
                    entry_price=price,
                    current_price=price,
                    quantity=self.config.position_size,
                    pnl=0.0,
                    pnl_pct=0.0,
                    entry_time=datetime.now().isoformat(),
                    timeframe=self.config.timeframe,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                bot_state["position"] = position.dict()
            
            # Send enhanced Telegram alert
            if self.telegram:
                await self.telegram.send_trade_alert(
                    action=signal_type,
                    symbol=self.config.symbol,
                    timeframe=self.config.timeframe,
                    price=price,
                    position_size=self.config.position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=reason
                )
            
            trade_state.total_trades_today += 1
            bot_state["total_trades"] = trade_state.total_trades_today
            
            # Store trade in history
            trade_record = {
                "id": trade_id,
                "timestamp": datetime.now().isoformat(),
                "action": signal_type,
                "symbol": self.config.symbol,
                "timeframe": self.config.timeframe,
                "price": price,
                "quantity": self.config.position_size,
                "reason": reason
            }
            trade_state.trade_history.append(trade_record)
            
            logging.info(f"✅ {signal_type.upper()} signal executed at ${price:,.4f} on {self.config.timeframe}")
            
        except Exception as e:
            logging.error(f"❌ Failed to execute {signal_type} signal: {e}")
    
    async def update_position_pnl(self, current_price: float):
        """Update position P&L with enhanced metrics"""
        if not bot_state["position"]:
            return
        
        position = bot_state["position"]
        entry_price = position["entry_price"]
        quantity = position["quantity"]
        side = position["side"]
        
        if side == "LONG":
            pnl = (current_price - entry_price) * quantity
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            pnl = (entry_price - current_price) * quantity
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Update position
        bot_state["position"]["current_price"] = current_price
        bot_state["position"]["pnl"] = pnl
        bot_state["position"]["pnl_pct"] = pnl_pct
        bot_state["daily_pnl"] = pnl
        trade_state.daily_pnl = pnl
        
        # Check for stop loss or take profit
        if side == "LONG":
            if current_price <= position["stop_loss"]:
                await self.close_position("stop_loss", current_price)
            elif current_price >= position["take_profit"]:
                await self.close_position("take_profit", current_price)
        else:  # SHORT
            if current_price >= position["stop_loss"]:
                await self.close_position("stop_loss", current_price)
            elif current_price <= position["take_profit"]:
                await self.close_position("take_profit", current_price)
    
    async def close_position(self, reason: str, current_price: float):
        """Close position with detailed tracking"""
        if not bot_state["position"]:
            return
        
        position = bot_state["position"]
        final_pnl = position["pnl"]
        
        # Update trade statistics
        if final_pnl > 0:
            trade_state.winning_trades += 1
        
        # Send closing alert
        if self.telegram:
            close_action = "close_long" if position["side"] == "LONG" else "close_short"
            await self.telegram.send_trade_alert(
                action=close_action,
                symbol=self.config.symbol,
                timeframe=self.config.timeframe,
                price=current_price,
                position_size=position["quantity"],
                reason=f"Position closed: {reason}",
                pnl=final_pnl
            )
        
        # Reset position
        bot_state["position"] = None
        trade_state.is_buy_active = False
        trade_state.is_sell_active = False
        trade_state.entry_price = None
        
        logging.info(f"✅ Position closed due to {reason} at ${current_price:,.4f}, P&L: ${final_pnl:,.2f}")
    
    def stop_trading(self):
        """Stop the trading bot"""
        self.running = False
        bot_state["running"] = False

# Global bot instance
enhanced_bot = None
crypto_provider = CryptoDataProvider()

# Database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = AsyncIOMotorClient(MONGO_URL)
    app.mongodb = app.mongodb_client[os.environ.get('DB_NAME', 'enhanced_rsi_bot')]
    
    # Load crypto data on startup
    await crypto_provider.fetch_crypto_list()
    
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
    """Get current bot status with enhanced metrics"""
    return {
        "status": "success",
        "data": bot_state
    }

@app.get("/api/crypto/list")
async def get_crypto_list():
    """Get comprehensive crypto list"""
    try:
        crypto_list = await crypto_provider.fetch_crypto_list()
        return {
            "status": "success",
            "data": [crypto.dict() for crypto in crypto_list],
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

@app.get("/api/market/ohlcv/{symbol}")
async def get_ohlcv_data(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Get OHLCV data for symbol and timeframe"""
    try:
        ohlcv_data = await crypto_provider.fetch_ohlcv_data(symbol, timeframe, limit)
        return {
            "status": "success",
            "data": [candle.dict() for candle in ohlcv_data],
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(ohlcv_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot/start")
async def start_enhanced_bot(config: TradingConfig, background_tasks: BackgroundTasks):
    """Start the enhanced trading bot"""
    global enhanced_bot, current_config
    
    try:
        if bot_state["running"]:
            raise HTTPException(status_code=400, detail="Bot is already running")
        
        current_config = config
        enhanced_bot = EnhancedRSITradingBot(config)
        
        # Start bot in background
        background_tasks.add_task(enhanced_bot.start_trading)
        
        return {
            "status": "success",
            "message": f"Enhanced trading bot started for {config.symbol} on {config.timeframe}",
            "config": config.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot/stop")
async def stop_enhanced_bot():
    """Stop the enhanced trading bot"""
    global enhanced_bot
    
    try:
        if not bot_state["running"]:
            raise HTTPException(status_code=400, detail="Bot is not running")
        
        if enhanced_bot:
            enhanced_bot.stop_trading()
        
        bot_state["running"] = False
        bot_state["position"] = None
        
        return {
            "status": "success",
            "message": "Enhanced trading bot stopped successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/metrics/{symbol}")
async def get_trading_metrics(symbol: str, timeframe: str = "1h"):
    """Get comprehensive trading metrics"""
    try:
        # Calculate metrics from trade history
        trades = trade_state.trade_history
        symbol_trades = [t for t in trades if t["symbol"] == symbol and t.get("timeframe") == timeframe]
        
        if not symbol_trades:
            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "average_profit": 0.0,
                    "average_loss": 0.0
                }
            }
        
        total_trades = len(symbol_trades)
        winning_trades = trade_state.winning_trades
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        metrics = {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_pnl": trade_state.daily_pnl,
            "average_profit": trade_state.daily_pnl / winning_trades if winning_trades > 0 else 0,
            "average_loss": 0  # Will be calculated from actual trade history
        }
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/chart-data/{symbol}")
async def get_chart_data(symbol: str, timeframe: str = "1h"):
    """Get chart data with position overlays"""
    try:
        ohlcv_data = await crypto_provider.fetch_ohlcv_data(symbol, timeframe, 200)
        
        # Add position markers
        chart_data = []
        for candle in ohlcv_data:
            data_point = candle.dict()
            
            # Add position markers if trades exist at this timestamp
            trades_at_time = [
                t for t in trade_state.trade_history 
                if abs(int(datetime.fromisoformat(t["timestamp"]).timestamp() * 1000) - candle.timestamp) < 60000
            ]
            
            if trades_at_time:
                data_point["trades"] = trades_at_time
            
            chart_data.append(data_point)
        
        return {
            "status": "success",
            "data": chart_data,
            "symbol": symbol,
            "timeframe": timeframe,
            "current_position": bot_state["position"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telegram/test")
async def test_telegram():
    """Test Telegram connection with enhanced diagnostics"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            raise HTTPException(status_code=400, detail="Telegram token not configured")
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        try:
            bot_info = await bot.get_me()
            logging.info(f"Bot info: {bot_info.username} - {bot_info.first_name}")
            
            telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            success = await telegram.send_message(
                f"🧪 **Enhanced RSI Bot Test**\n\n"
                f"✅ Multi-timeframe trading ready\n"
                f"📊 {len(bot_state.get('available_cryptos', []))} cryptocurrencies available\n"
                f"⏰ {len(TIMEFRAMES)} timeframes supported\n\n"
                f"Bot connection working perfectly!",
                parse_mode='Markdown'
            )
            
            if success:
                return {
                    "status": "success", 
                    "message": "Enhanced Telegram test message sent successfully",
                    "bot_info": {
                        "username": bot_info.username,
                        "name": bot_info.first_name,
                        "features": ["Multi-timeframe", "100+ Cryptocurrencies", "Advanced Analytics"]
                    }
                }
            else:
                return {
                    "status": "error", 
                    "message": f"Failed to send message to chat {TELEGRAM_CHAT_ID}",
                    "troubleshooting": [
                        f"Bot @{bot_info.username} is working correctly",
                        f"Issue: Cannot send message to chat ID {TELEGRAM_CHAT_ID}",
                        "Solution: Start a chat with the bot first",
                        f"Steps: Find @{bot_info.username} on Telegram → Send /start → Try again"
                    ]
                }
        except Exception as chat_error:
            bot_info = await bot.get_me()
            return {
                "status": "error", 
                "message": f"Chat error: {str(chat_error)}",
                "bot_info": {"username": bot_info.username, "working": True},
                "error_details": str(chat_error)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root route
@app.get("/")
async def root():
    return {
        "message": "Enhanced RSI Trading Bot API", 
        "status": "running",
        "features": [
            "Multi-timeframe trading (1m to 1M)",
            "100+ cryptocurrency support",
            "Advanced analytics and metrics",
            "Real-time position tracking",
            "Enhanced charting with overlays"
        ]
    }

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)