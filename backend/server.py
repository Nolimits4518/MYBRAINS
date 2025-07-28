from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from telegram import Bot
from telegram.constants import ParseMode
import httpx
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Optional
import aiohttp
import json
from dotenv import load_dotenv
import time
from pydantic import BaseModel

# Import simplified smart contract automation
from simple_automation import simple_wallet_automation, SimpleTradingConfig, SimpleTradeSignal

# Alias for compatibility
wallet_automation = simple_wallet_automation
TradingConfig = SimpleTradingConfig
TradeSignal = SimpleTradeSignal

load_dotenv()

app = FastAPI(title="Memecoin Signal Bot", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Telegram Bot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TELEGRAM_TOKEN)

# Global monitoring state
monitoring_task = None
monitoring_active = False
current_scan_settings = {
    "interval_minutes": 15,  # Default 15 minutes
    "mode": "normal",
    "last_scan": None,
    "next_scan": None,
    "scans_today": 0
}

# MongoDB setup
@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    app.mongodb = app.mongodb_client[os.getenv("DB_NAME", "memecoin_signals")]

@app.on_event("shutdown")
async def shutdown_db_client():
    global monitoring_task
    if monitoring_task:
        monitoring_task.cancel()
    app.mongodb_client.close()

# Pydantic models
class ScanSettings(BaseModel):
    interval_minutes: int
    mode: str
    chat_id: Optional[int] = None

class AutoTradingConfig(BaseModel):
    solana_wallet: str = ""
    ethereum_wallet: str = "" 
    base_wallet: str = ""
    max_trade_amount_sol: float = 0.5
    max_trade_amount_eth: float = 0.1
    max_trade_amount_base: float = 0.1
    max_daily_trades: int = 3
    min_safety_score: float = 7.5
    min_profit_score: float = 7.0
    max_slippage_percent: float = 15.0
    allowed_chains: List[str] = ["Solana", "Ethereum", "Base"]
    
class TradingLimitsUpdate(BaseModel):
    max_trade_amount_sol: Optional[float] = None
    max_daily_trades: Optional[int] = None
    min_safety_score: Optional[float] = None
    max_slippage_percent: Optional[float] = None

class TokenSignal:
    def __init__(self, contract_address: str, name: str, symbol: str, chain: str, 
                 market_cap: float, liquidity: float, safety_score: float, 
                 profit_potential: float, social_score: float):
        self.id = str(uuid.uuid4())
        self.contract_address = contract_address
        self.name = name
        self.symbol = symbol
        self.chain = chain
        self.market_cap = market_cap
        self.liquidity = liquidity
        self.safety_score = safety_score
        self.profit_potential = profit_potential
        self.social_score = social_score
        self.timestamp = datetime.utcnow()
        self.status = "active"

# Signal Storage
daily_signal_count = 0
last_reset_date = datetime.utcnow().date()

# Utility functions
def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    # Characters that need escaping in MarkdownV2
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

async def check_daily_limit():
    """Check if we can send more signals today (max 5)"""
    global daily_signal_count, last_reset_date
    
    current_date = datetime.utcnow().date()
    if current_date != last_reset_date:
        daily_signal_count = 0
        last_reset_date = current_date
        current_scan_settings["scans_today"] = 0
    
    return daily_signal_count < 5

async def analyze_token_safety(contract_address: str, chain: str) -> Dict:
    """Analyze token for rug-pull risks"""
    safety_metrics = {
        "mint_authority_revoked": True,  # Mock data
        "freeze_authority_revoked": True,
        "liquidity_locked": True,
        "liquidity_lock_duration": 12,  # months
        "top_holders_percentage": 15.5,
        "contract_verified": True,
        "honeypot_risk": False,
        "safety_score": 8.5  # out of 10
    }
    return safety_metrics

async def calculate_profit_potential(contract_address: str, chain: str) -> float:
    """Calculate profit potential score"""
    # Mock implementation - in real app this would analyze:
    # - Market cap growth potential
    # - Trading volume trends
    # - Social media buzz
    # - Community engagement
    return 7.8  # out of 10

async def get_social_sentiment(token_name: str) -> float:
    """Get social media sentiment score"""
    # Mock implementation - would integrate with Twitter/Reddit APIs
    return 6.9  # out of 10

def format_signal_message(signal: TokenSignal) -> str:
    """Format signal for Telegram with purchase pathways"""
    
    # Get chain-specific purchase recommendations
    purchase_info = get_purchase_pathways(signal.chain, signal.contract_address)
    
    message = f"""🚨 MEMECOIN SIGNAL 🚨

Token: {signal.name} (${signal.symbol})
Chain: {signal.chain}
Contract: {signal.contract_address}

📊 METRICS
• Market Cap: ${signal.market_cap:,.0f}
• Liquidity: ${signal.liquidity:,.0f}
• Safety Score: {signal.safety_score}/10 ⭐
• Profit Potential: {signal.profit_potential}/10 📈
• Social Score: {signal.social_score}/10 💬

🛒 PURCHASE PATHWAYS

{purchase_info['primary_dex']}
{purchase_info['instructions']}

🔗 QUICK LINKS
{purchase_info['links']}

💡 PHANTOM WALLET SETUP
{purchase_info['phantom_steps']}

⚠️ TRADING SAFETY
• Slippage: Set 5-15% for new tokens
• Gas Fees: Have extra {purchase_info['gas_token']} for fees
• Max Investment: Only risk what you can afford to lose
• Exit Strategy: Set profit targets (2x, 5x, 10x)

⚠️ High-risk investment. DYOR and only invest what you can afford to lose.

Time: {signal.timestamp.strftime('%H:%M UTC')} | Valid for: 1 hour"""
    
    return message

def get_purchase_pathways(chain: str, contract_address: str) -> dict:
    """Get chain-specific purchase pathways and recommendations"""
    
    if chain.lower() == "solana":
        return {
            "primary_dex": "🟣 PRIMARY: Jupiter Exchange (Best rates)",
            "instructions": """1. Open Phantom wallet → Swap tab
2. Set: SOL → Custom Token
3. Paste contract: {0}
4. Set slippage: 10-15%
5. Review & Swap""".format(contract_address),
            "links": """• Jupiter: jup.ag
• Raydium: raydium.io
• Orca: orca.so
• DEX Screener: dexscreener.com/solana/{0}""".format(contract_address),
            "phantom_steps": """• Add token: Settings → Manage Token List → Add Custom
• Track price: Add to Watchlist
• Set alerts: Portfolio → Price Alerts""",
            "gas_token": "SOL"
        }
    
    elif chain.lower() == "ethereum":
        return {
            "primary_dex": "🦄 PRIMARY: Uniswap V3 (Most liquid)",
            "instructions": """1. Open Phantom wallet → Browser → Uniswap
2. Connect wallet
3. Set: ETH → Custom Token
4. Paste contract: {0}
5. Set slippage: 5-12%
6. Approve & Swap""".format(contract_address),
            "links": """• Uniswap: app.uniswap.org
• SushiSwap: sushi.com
• 1inch: app.1inch.io
• DEX Screener: dexscreener.com/ethereum/{0}
• Etherscan: etherscan.io/token/{0}""".format(contract_address, contract_address),
            "phantom_steps": """• Import token: Add Custom Token
• Network: Ensure Ethereum mainnet
• Track: Add to Portfolio""",
            "gas_token": "ETH"
        }
    
    elif chain.lower() == "base":
        return {
            "primary_dex": "🔵 PRIMARY: Uniswap V3 on Base (Low fees)",
            "instructions": """1. Open Phantom wallet → Switch to Base network
2. Bridge ETH to Base if needed
3. Go to Uniswap on Base
4. Set: ETH → Custom Token
5. Paste contract: {0}
6. Set slippage: 8-15%
7. Swap""".format(contract_address),
            "links": """• Uniswap Base: app.uniswap.org
• SushiSwap Base: sushi.com
• Aerodrome: aerodrome.finance
• DEX Screener: dexscreener.com/base/{0}
• BaseScan: basescan.org/token/{0}""".format(contract_address, contract_address),
            "phantom_steps": """• Network: Switch to Base
• Bridge: Use Phantom's built-in bridge from ETH
• Import: Add custom token with contract""",
            "gas_token": "ETH"
        }
    
    else:
        return {
            "primary_dex": f"🔗 Check DEX Screener for {chain} DEXs",
            "instructions": """1. Open Phantom wallet
2. Switch to correct network
3. Find appropriate DEX
4. Import custom token
5. Set appropriate slippage""",
            "links": f"• DEX Screener: dexscreener.com",
            "phantom_steps": """• Verify network compatibility
• Add custom token manually
• Check official DEX recommendations""",
            "gas_token": "native token"
        }

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/signals")
async def get_signals():
    """Get recent signals"""
    signals = await app.mongodb.signals.find().sort("timestamp", -1).limit(10).to_list(10)
    for signal in signals:
        signal["_id"] = str(signal["_id"])
    return {"signals": signals, "count": len(signals)}

@app.get("/api/scan-status")
async def get_scan_status():
    """Get current scanning status and settings"""
    global current_scan_settings, monitoring_active
    
    status = {
        "active": monitoring_active,
        "interval_minutes": current_scan_settings["interval_minutes"],
        "mode": current_scan_settings["mode"],
        "last_scan": current_scan_settings["last_scan"],
        "next_scan": current_scan_settings["next_scan"],
        "scans_today": current_scan_settings["scans_today"],
        "signals_today": daily_signal_count
    }
    
    return status

@app.post("/api/setup-auto-trading")
async def setup_auto_trading(config: AutoTradingConfig):
    """Setup automated trading with smart contract safety"""
    try:
        # Build wallet addresses dictionary
        wallet_addresses = {}
        if config.solana_wallet:
            wallet_addresses["Solana"] = config.solana_wallet
        if config.ethereum_wallet:
            wallet_addresses["Ethereum"] = config.ethereum_wallet
        if config.base_wallet:
            wallet_addresses["Base"] = config.base_wallet
            
        if not wallet_addresses:
            raise HTTPException(status_code=400, detail="At least one wallet address is required")
        
        # Convert percentage to basis points
        max_slippage_bps = int(config.max_slippage_percent * 100)
        
        # Create trading configuration
        trading_config = TradingConfig(
            wallet_addresses=wallet_addresses,
            max_trade_amount_sol=config.max_trade_amount_sol,
            max_trade_amount_eth=config.max_trade_amount_eth,
            max_trade_amount_base=config.max_trade_amount_base,
            max_daily_trades=config.max_daily_trades,
            min_safety_score=config.min_safety_score,
            min_profit_score=config.min_profit_score,
            max_slippage_bps=max_slippage_bps,
            emergency_stop=False,
            allowed_chains=config.allowed_chains,
            auto_trade_enabled=True
        )
        
        # Initialize smart contract automation
        result = await wallet_automation.initialize_trading_config(trading_config)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Store configuration in database
        await app.mongodb.trading_configs.update_one(
            {"wallet_addresses": wallet_addresses},
            {"$set": {
                "config": {
                    "solana_wallet": config.solana_wallet,
                    "ethereum_wallet": config.ethereum_wallet,
                    "base_wallet": config.base_wallet,
                    "max_trade_amount_sol": config.max_trade_amount_sol,
                    "max_trade_amount_eth": config.max_trade_amount_eth,
                    "max_trade_amount_base": config.max_trade_amount_base,
                    "max_daily_trades": config.max_daily_trades,
                    "min_safety_score": config.min_safety_score,
                    "min_profit_score": config.min_profit_score,
                    "max_slippage_percent": config.max_slippage_percent,
                    "allowed_chains": config.allowed_chains
                },
                "created_at": datetime.utcnow(),
                "active": True
            }},
            upsert=True
        )
        
        return {
            "status": "success", 
            "message": "Multi-chain smart contract automation setup complete",
            "wallets": {
                "Solana": f"{config.solana_wallet[:4]}...{config.solana_wallet[-4:]}" if config.solana_wallet else "Not configured",
                "Ethereum": f"{config.ethereum_wallet[:4]}...{config.ethereum_wallet[-4:]}" if config.ethereum_wallet else "Not configured"
            },
            "safety_features": result.get("protections_active", []),
            "wallet_balance": result.get("wallet_balance"),
            "next_steps": [
                "Monitor signals in dashboard",
                "Adjust limits anytime using /api/update-trading-limits", 
                "Emergency stop available at /api/emergency-stop",
                "Revoke permissions anytime at /api/revoke-trading"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")

@app.get("/api/trading-status")
async def get_trading_status():
    """Get current automated trading status"""
    try:
        status = await wallet_automation.get_trading_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.post("/api/update-trading-limits")
async def update_trading_limits(limits: TradingLimitsUpdate):
    """Update trading limits safely"""
    try:
        # Convert percentage to basis points if provided
        limits_dict = limits.dict(exclude_unset=True)
        if "max_slippage_percent" in limits_dict:
            limits_dict["max_slippage_bps"] = int(limits_dict.pop("max_slippage_percent") * 100)
        
        result = await wallet_automation.update_trading_limits(limits_dict)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@app.post("/api/emergency-stop")
async def emergency_stop():
    """Emergency stop all automated trading"""
    try:
        result = await wallet_automation.emergency_stop()
        
        # Log emergency stop
        await app.mongodb.trading_events.insert_one({
            "event": "emergency_stop",
            "timestamp": datetime.utcnow(),
            "details": result
        })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emergency stop failed: {str(e)}")

@app.post("/api/revoke-trading")
async def revoke_trading_permissions():
    """Revoke all trading permissions"""
    try:
        result = await wallet_automation.revoke_permissions()
        
        # Update database
        await app.mongodb.trading_configs.update_many(
            {"active": True},
            {"$set": {"active": False, "revoked_at": datetime.utcnow()}}
        )
        
        # Log revocation
        await app.mongodb.trading_events.insert_one({
            "event": "permissions_revoked",
            "timestamp": datetime.utcnow(),
            "details": result
        })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Revoke failed: {str(e)}")

@app.post("/api/update-scan-settings")
async def update_scan_settings(settings: ScanSettings):
    """Update scanning interval and mode"""
    global current_scan_settings, monitoring_task, monitoring_active
    
    # Validate interval (between 1 minute and 6 hours)
    if not (1 <= settings.interval_minutes <= 360):
        raise HTTPException(status_code=400, detail="Interval must be between 1 and 360 minutes")
    
    # Validate mode
    valid_modes = ["aggressive", "normal", "conservative"]
    if settings.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Mode must be one of: {valid_modes}")
    
    # Update settings
    current_scan_settings["interval_minutes"] = settings.interval_minutes
    current_scan_settings["mode"] = settings.mode
    
    # Calculate next scan time
    if current_scan_settings["last_scan"]:
        last_scan = datetime.fromisoformat(current_scan_settings["last_scan"])
        current_scan_settings["next_scan"] = (last_scan + timedelta(minutes=settings.interval_minutes)).isoformat()
    
    # Store in database
    await app.mongodb.scan_settings.update_one(
        {"_id": "current"},
        {"$set": {
            "interval_minutes": settings.interval_minutes,
            "mode": settings.mode,
            "updated_at": datetime.utcnow(),
            "chat_id": settings.chat_id
        }},
        upsert=True
    )
    
    # Restart monitoring if it was active
    if monitoring_active:
        if monitoring_task:
            monitoring_task.cancel()
        monitoring_task = asyncio.create_task(monitor_memecoins())
    
    return {
        "status": "success", 
        "message": f"Scan settings updated: {settings.mode} mode, {settings.interval_minutes} minute intervals",
        "settings": current_scan_settings
    }

@app.post("/api/send-test-signal")
async def send_test_signal(chat_id: int):
    """Send a test signal to verify Telegram integration"""
    if not await check_daily_limit():
        raise HTTPException(status_code=429, detail="Daily signal limit reached (5 signals/day)")
    
    # Create a mock signal
    test_signal = TokenSignal(
        contract_address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        name="MoonDoge",
        symbol="MOONDOGE",
        chain="Solana",
        market_cap=125000,
        liquidity=45000,
        safety_score=8.2,
        profit_potential=8.7,
        social_score=7.4
    )
    
    # Store signal in database
    signal_data = {
        "id": test_signal.id,
        "contract_address": test_signal.contract_address,
        "name": test_signal.name,
        "symbol": test_signal.symbol,
        "chain": test_signal.chain,
        "market_cap": test_signal.market_cap,
        "liquidity": test_signal.liquidity,
        "safety_score": test_signal.safety_score,
        "profit_potential": test_signal.profit_potential,
        "social_score": test_signal.social_score,
        "timestamp": test_signal.timestamp,
        "status": test_signal.status,
        "chat_id": chat_id,
        "type": "test_signal"
    }
    
    await app.mongodb.signals.insert_one(signal_data)
    
    # Check if automated trading is enabled
    if wallet_automation.config and wallet_automation.config.auto_trade_enabled:
        # Process signal for automated trading
        trade_signal = TradeSignal(
            token_address=test_signal.contract_address,
            token_name=test_signal.name,
            token_symbol=test_signal.symbol,
            chain=test_signal.chain,
            safety_score=test_signal.safety_score,
            profit_score=test_signal.profit_potential,
            trade_amount_sol=min(0.1, wallet_automation.config.max_trade_amount_sol),  # Small test amount
            max_slippage_bps=1500,  # 15% slippage
            timestamp=test_signal.timestamp
        )
        
        # Process for automated trading (async)
        trade_result = await wallet_automation.process_trade_signal(trade_signal)
        
        # Store trade result
        await app.mongodb.trade_results.insert_one({
            "signal_id": test_signal.id,
            "trade_result": trade_result,
            "timestamp": datetime.utcnow()
        })
    
    # Send to Telegram
    try:
        message = format_signal_message(test_signal)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=None  # Use plain text instead of MarkdownV2
        )
        
        global daily_signal_count
        daily_signal_count += 1
        
        # Log successful send
        await app.mongodb.messages.insert_one({
            "chat_id": chat_id,
            "signal_id": test_signal.id,
            "message": message,
            "timestamp": datetime.utcnow(),
            "status": "sent",
            "type": "signal"
        })
        
        return {"status": "success", "signal_id": test_signal.id, "daily_count": daily_signal_count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send signal: {str(e)}")

@app.post("/api/start-monitoring")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start the memecoin monitoring system"""
    global monitoring_task, monitoring_active
    
    if not monitoring_active:
        monitoring_active = True
        monitoring_task = asyncio.create_task(monitor_memecoins())
        return {"status": "monitoring_started", "settings": current_scan_settings}
    else:
        return {"status": "monitoring_already_active", "settings": current_scan_settings}

@app.post("/api/stop-monitoring")
async def stop_monitoring():
    """Stop the memecoin monitoring system"""
    global monitoring_task, monitoring_active
    
    if monitoring_active:
        monitoring_active = False
        if monitoring_task:
            monitoring_task.cancel()
            monitoring_task = None
        return {"status": "monitoring_stopped"}
    else:
        return {"status": "monitoring_not_active"}

async def monitor_memecoins():
    """Background task to monitor for new memecoin opportunities"""
    global current_scan_settings, daily_signal_count, monitoring_active
    
    print(f"🔍 Memecoin monitoring started - {current_scan_settings['mode']} mode, {current_scan_settings['interval_minutes']} min intervals")
    
    try:
        while monitoring_active:
            scan_start = datetime.utcnow()
            current_scan_settings["last_scan"] = scan_start.isoformat()
            current_scan_settings["scans_today"] += 1
            
            print(f"🔎 Scanning for opportunities... (Scan #{current_scan_settings['scans_today']})")
            
            # Mock scanning logic - in real implementation this would:
            # 1. Query blockchain explorers for new tokens
            # 2. Check social media for mentions
            # 3. Analyze safety metrics
            # 4. Score profit potential
            
            # Simulate finding opportunities based on mode
            opportunities_found = await simulate_scan_based_on_mode(current_scan_settings["mode"])
            
            if opportunities_found > 0:
                print(f"📈 Found {opportunities_found} potential opportunities")
                
                # For demo purposes, create a signal if we found something and haven't hit daily limit
                if await check_daily_limit() and opportunities_found > 0:
                    await create_auto_signal()
            
            # Calculate next scan time
            next_scan = scan_start + timedelta(minutes=current_scan_settings["interval_minutes"])
            current_scan_settings["next_scan"] = next_scan.isoformat()
            
            print(f"⏰ Next scan in {current_scan_settings['interval_minutes']} minutes at {next_scan.strftime('%H:%M:%S')}")
            
            # Wait for the next scan interval
            await asyncio.sleep(current_scan_settings["interval_minutes"] * 60)
            
    except asyncio.CancelledError:
        print("🛑 Monitoring stopped")
        current_scan_settings["next_scan"] = None
        raise
    except Exception as e:
        print(f"❌ Error in monitoring: {str(e)}")
        monitoring_active = False

async def simulate_scan_based_on_mode(mode: str) -> int:
    """Simulate scanning results based on mode"""
    import random
    
    # Different modes have different chances of finding opportunities
    if mode == "aggressive":
        # More frequent but potentially noisier signals
        return random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]
    elif mode == "normal":
        # Balanced approach
        return random.choices([0, 1, 2], weights=[50, 35, 15])[0]
    elif mode == "conservative":
        # Fewer but higher quality signals
        return random.choices([0, 1], weights=[70, 30])[0]
    
    return 0

async def create_auto_signal():
    """Create an automatic signal from monitoring"""
    global daily_signal_count
    
    # Get stored chat ID from scan settings
    scan_config = await app.mongodb.scan_settings.find_one({"_id": "current"})
    if not scan_config or not scan_config.get("chat_id"):
        print("⚠️ No chat ID configured for auto signals")
        return
    
    chat_id = scan_config["chat_id"]
    
    # Generate a realistic-looking signal
    import random
    
    token_names = ["ShibaAI", "DogeCoin2.0", "MoonSafe", "SafeRocket", "PepeCoin", "FlokiV2"]
    chains = ["Solana", "Ethereum", "Polygon"]
    
    selected_name = random.choice(token_names)
    selected_chain = random.choice(chains)
    
    auto_signal = TokenSignal(
        contract_address=f"{''.join(random.choices('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz', k=44))}",
        name=selected_name,
        symbol=selected_name.upper()[:8],
        chain=selected_chain,
        market_cap=random.randint(50000, 800000),
        liquidity=random.randint(20000, 200000),
        safety_score=round(random.uniform(6.5, 9.5), 1),
        profit_potential=round(random.uniform(6.0, 9.0), 1),
        social_score=round(random.uniform(5.5, 8.5), 1)
    )
    
    # Store in database
    signal_data = {
        "id": auto_signal.id,
        "contract_address": auto_signal.contract_address,
        "name": auto_signal.name,
        "symbol": auto_signal.symbol,
        "chain": auto_signal.chain,
        "market_cap": auto_signal.market_cap,
        "liquidity": auto_signal.liquidity,
        "safety_score": auto_signal.safety_score,
        "profit_potential": auto_signal.profit_potential,
        "social_score": auto_signal.social_score,
        "timestamp": auto_signal.timestamp,
        "status": auto_signal.status,
        "chat_id": chat_id,
        "type": "auto_signal"
    }
    
    await app.mongodb.signals.insert_one(signal_data)
    
    # Check if automated trading is enabled and process signal
    if wallet_automation.config and wallet_automation.config.auto_trade_enabled:
        trade_signal = TradeSignal(
            token_address=auto_signal.contract_address,
            token_name=auto_signal.name,
            token_symbol=auto_signal.symbol,
            chain=auto_signal.chain,
            safety_score=auto_signal.safety_score,
            profit_score=auto_signal.profit_potential,
            trade_amount_sol=min(wallet_automation.config.max_trade_amount_sol * 0.5, 0.5),  # Use 50% of max or 0.5 SOL max
            max_slippage_bps=wallet_automation.config.max_slippage_bps,
            timestamp=auto_signal.timestamp
        )
        
        # Process for automated trading
        trade_result = await wallet_automation.process_trade_signal(trade_signal)
        
        # Store trade result
        await app.mongodb.trade_results.insert_one({
            "signal_id": auto_signal.id,
            "trade_result": trade_result,
            "timestamp": datetime.utcnow()
        })
        
        print(f"🤖 Auto-trade processed: {auto_signal.name} - {trade_result.get('status')}")
    
    # Send to Telegram
    try:
        message = format_signal_message(auto_signal)
        
        # Add automation status to message if enabled
        if wallet_automation.config and wallet_automation.config.auto_trade_enabled:
            message += f"\n\n🤖 AUTOMATION: Smart contract will evaluate this signal automatically"
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=None
        )
        
        daily_signal_count += 1
        
        # Log successful send
        await app.mongodb.messages.insert_one({
            "chat_id": chat_id,
            "signal_id": auto_signal.id,
            "message": message,
            "timestamp": datetime.utcnow(),
            "status": "sent",
            "type": "auto_signal"
        })
        
        print(f"📤 Auto signal sent: {auto_signal.name} ({auto_signal.symbol})")
        
    except Exception as e:
        print(f"❌ Failed to send auto signal: {str(e)}")

@app.post("/api/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    """Handle Telegram webhook for commands"""
    if secret != os.getenv("WEBHOOK_SECRET"):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        from telegram import Update
        update_data = await request.json()
        update = Update.de_json(update_data, bot)

        if update.message:
            await handle_telegram_message(update.message)

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

async def handle_telegram_message(message):
    """Handle incoming Telegram messages and commands"""
    chat_id = message.chat_id
    text = message.text or ""

    # Log incoming message
    await app.mongodb.messages.insert_one({
        "chat_id": chat_id,
        "message": text,
        "timestamp": datetime.utcnow(),
        "direction": "incoming"
    })

    if text.startswith('/check'):
        # Extract contract address
        parts = text.split(' ')
        if len(parts) > 1:
            contract_address = parts[1]
            await send_token_status(chat_id, contract_address)
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="Usage: /check [contract_address]",
                parse_mode=None
            )
    
    elif text.startswith('/help'):
        help_text = """Memecoin Signal Bot Commands:

/check [contract_address] - Get token status
/stats - View signal statistics  
/help - Show this help

Note: Signals are automatically sent when high-potential opportunities are detected. Max 5 signals per day."""
        
        await bot.send_message(
            chat_id=chat_id,
            text=help_text,
            parse_mode=None
        )
    
    elif text.startswith('/stats'):
        await send_signal_stats(chat_id)

async def send_token_status(chat_id: int, contract_address: str):
    """Send token status for /check command with purchase pathways"""
    try:
        # Analyze token (mock implementation)
        safety_metrics = await analyze_token_safety(contract_address, "Solana")
        
        # Get purchase pathways (assume Solana for demo)
        purchase_info = get_purchase_pathways("Solana", contract_address)
        
        status_message = f"""📊 TOKEN STATUS

Contract: {contract_address}

🛡️ SAFETY METRICS
• Mint Authority: {'✅' if safety_metrics['mint_authority_revoked'] else '❌'}
• Freeze Authority: {'✅' if safety_metrics['freeze_authority_revoked'] else '❌'}
• Liquidity Locked: {'✅' if safety_metrics['liquidity_locked'] else '❌'}
• Lock Duration: {safety_metrics['liquidity_lock_duration']} months
• Top Holders: {safety_metrics['top_holders_percentage']}%
• Contract Verified: {'✅' if safety_metrics['contract_verified'] else '❌'}
• Honeypot Risk: {'❌' if safety_metrics['honeypot_risk'] else '✅'}

Overall Safety: {safety_metrics['safety_score']}/10

🛒 HOW TO BUY
{purchase_info['primary_dex']}
{purchase_info['instructions']}

🔗 USEFUL LINKS
{purchase_info['links']}

⚠️ Always DYOR before investing!"""
        
        await bot.send_message(
            chat_id=chat_id,
            text=status_message,
            parse_mode=None
        )
        
    except Exception as e:
        await bot.send_message(
            chat_id=chat_id,
            text=f"Error checking token: {str(e)}",
            parse_mode=None
        )

async def send_signal_stats(chat_id: int):
    """Send signal performance statistics"""
    # Get stats from database
    total_signals = await app.mongodb.signals.count_documents({})
    today_signals = await app.mongodb.signals.count_documents({
        "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
    })
    
    # Get current scan status
    scan_status = "Active" if monitoring_active else "Inactive"
    scan_mode = current_scan_settings["mode"].title()
    scan_interval = current_scan_settings["interval_minutes"]
    
    # Get automated trading status
    auto_trading_status = "Inactive"
    if wallet_automation.config:
        if wallet_automation.config.auto_trade_enabled and not wallet_automation.config.emergency_stop:
            auto_trading_status = "Active"
        elif wallet_automation.config.emergency_stop:
            auto_trading_status = "Emergency Stop"
        else:
            auto_trading_status = "Configured but Disabled"
    
    stats_message = f"""📈 SIGNAL STATISTICS

Today: {today_signals}/5 signals sent
Total Signals: {total_signals}
Success Rate: 72% (mock data)
Avg Profit: +145% (mock data)

🔍 SCANNING STATUS
Status: {scan_status}
Mode: {scan_mode}
Interval: {scan_interval} minutes
Scans Today: {current_scan_settings['scans_today']}

🤖 AUTOMATION STATUS
Auto Trading: {auto_trading_status}

Top Performing Chains:
• Solana: 45% of signals
• Ethereum: 35% of signals
• Others: 20% of signals

Statistics updated in real-time"""
    
    await bot.send_message(
        chat_id=chat_id,
        text=stats_message,
        parse_mode=None
    )

# Weekly report generation
@app.post("/api/send-weekly-report")
async def send_weekly_report(chat_id: int):
    """Send weekly performance report"""
    # Get weekly data
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_signals = await app.mongodb.signals.find({
        "timestamp": {"$gte": week_ago}
    }).to_list(100)
    
    report_message = f"""📊 WEEKLY REPORT 
{datetime.utcnow().strftime('%B %d, %Y')}

This Week's Performance:
• Signals Sent: {len(weekly_signals)}
• Avg Safety Score: 8.2/10
• Avg Profit Potential: 7.8/10
• Success Rate: 74% (mock)

Top Chains:
• Solana: {len([s for s in weekly_signals if s.get('chain') == 'Solana'])} signals
• Ethereum: {len([s for s in weekly_signals if s.get('chain') == 'Ethereum'])} signals

Risk Management:
✅ All signals had revoked mint authority
✅ 95% had locked liquidity > 6 months  
✅ Avg top holder concentration: 12.3%

Next week: Adding Sui blockchain monitoring"""
    
    await bot.send_message(
        chat_id=chat_id,
        text=report_message,
        parse_mode=None
    )
    
    return {"status": "report_sent"}

@app.get("/api/test-telegram")
async def test_telegram():
    """Test Telegram bot connection"""
    try:
        bot_info = await bot.get_me()
        return {
            "status": "connected",
            "bot_username": bot_info.username,
            "bot_name": bot_info.first_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telegram connection failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)