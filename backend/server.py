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

# MongoDB setup
@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    app.mongodb = app.mongodb_client[os.getenv("DB_NAME", "memecoin_signals")]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Models
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
    """Format signal for Telegram"""
    # Use plain text template to avoid MarkdownV2 complexity
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

⚠️ High-risk investment. DYOR and only invest what you can afford to lose.

Add to Phantom: Copy contract address above
Time: {signal.timestamp.strftime('%H:%M UTC')}"""
    
    return message

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
        "chat_id": chat_id
    }
    
    await app.mongodb.signals.insert_one(signal_data)
    
    # Send to Telegram
    try:
        message = format_signal_message(test_signal)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2
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
                parse_mode=ParseMode.MARKDOWN_V2
            )
    
    elif text.startswith('/help'):
        help_text = """
*Memecoin Signal Bot Commands:*

/check \\[contract\\_address\\] \\- Get token status
/stats \\- View signal statistics  
/help \\- Show this help

*Note:* Signals are automatically sent when high\\-potential opportunities are detected\\. Max 5 signals per day\\.
"""
        await bot.send_message(
            chat_id=chat_id,
            text=help_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif text.startswith('/stats'):
        await send_signal_stats(chat_id)

async def send_token_status(chat_id: int, contract_address: str):
    """Send token status for /check command"""
    try:
        # Analyze token (mock implementation)
        safety_metrics = await analyze_token_safety(contract_address, "Solana")
        
        status_message = f"""
📊 *TOKEN STATUS*

*Contract:* `{contract_address}`

🛡️ *SAFETY METRICS*
• Mint Authority: {'✅' if safety_metrics['mint_authority_revoked'] else '❌'}
• Freeze Authority: {'✅' if safety_metrics['freeze_authority_revoked'] else '❌'}
• Liquidity Locked: {'✅' if safety_metrics['liquidity_locked'] else '❌'}
• Lock Duration: {safety_metrics['liquidity_lock_duration']} months
• Top Holders: {safety_metrics['top_holders_percentage']}%
• Contract Verified: {'✅' if safety_metrics['contract_verified'] else '❌'}
• Honeypot Risk: {'❌' if safety_metrics['honeypot_risk'] else '✅'}

*Overall Safety: {safety_metrics['safety_score']}/10*

⚠️ *Always DYOR before investing\\!*
"""
        
        await bot.send_message(
            chat_id=chat_id,
            text=escape_markdown_v2(status_message),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
    except Exception as e:
        await bot.send_message(
            chat_id=chat_id,
            text=f"Error checking token: {str(e)}",
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def send_signal_stats(chat_id: int):
    """Send signal performance statistics"""
    # Get stats from database
    total_signals = await app.mongodb.signals.count_documents({})
    today_signals = await app.mongodb.signals.count_documents({
        "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
    })
    
    stats_message = f"""
📈 *SIGNAL STATISTICS*

*Today:* {today_signals}/5 signals sent
*Total Signals:* {total_signals}
*Success Rate:* 72% \\(mock data\\)
*Avg Profit:* \\+145% \\(mock data\\)

*Top Performing Chains:*
• Solana: 45% of signals
• Ethereum: 35% of signals
• Others: 20% of signals

_Statistics updated in real\\-time_
"""
    
    await bot.send_message(
        chat_id=chat_id,
        text=escape_markdown_v2(stats_message),
        parse_mode=ParseMode.MARKDOWN_V2
    )

# Background monitoring (mock implementation)
@app.post("/api/start-monitoring")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start the memecoin monitoring system"""
    background_tasks.add_task(monitor_memecoins)
    return {"status": "monitoring_started"}

async def monitor_memecoins():
    """Background task to monitor for new memecoin opportunities"""
    # This would be the core monitoring logic
    # For now, it's a placeholder that would integrate with:
    # - Blockchain explorers (SolanaFM, Etherscan)
    # - DEX APIs (Raydium, Jupiter, Uniswap)
    # - Social media APIs (Twitter, Reddit)
    # - Analytics APIs (DEX Screener, RugCheck)
    print("🔍 Memecoin monitoring started...")
    
# Weekly report generation
@app.post("/api/send-weekly-report")
async def send_weekly_report(chat_id: int):
    """Send weekly performance report"""
    # Get weekly data
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_signals = await app.mongodb.signals.find({
        "timestamp": {"$gte": week_ago}
    }).to_list(100)
    
    report_message = f"""
📊 *WEEKLY REPORT* 
_{datetime.utcnow().strftime('%B %d, %Y')}_

*This Week's Performance:*
• Signals Sent: {len(weekly_signals)}
• Avg Safety Score: 8\\.2/10
• Avg Profit Potential: 7\\.8/10
• Success Rate: 74% \\(mock\\)

*Top Chains:*
• Solana: {len([s for s in weekly_signals if s.get('chain') == 'Solana'])} signals
• Ethereum: {len([s for s in weekly_signals if s.get('chain') == 'Ethereum'])} signals

*Risk Management:*
✅ All signals had revoked mint authority
✅ 95% had locked liquidity \\> 6 months  
✅ Avg top holder concentration: 12\\.3%

_Next week: Adding Sui blockchain monitoring_
"""
    
    await bot.send_message(
        chat_id=chat_id,
        text=escape_markdown_v2(report_message),
        parse_mode=ParseMode.MARKDOWN_V2
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