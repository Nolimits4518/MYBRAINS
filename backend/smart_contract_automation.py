"""
Smart Contract Trading Automation for Phantom Wallet
Safe trading automation using Solana programs without exposing private keys
"""

import asyncio
import json
import base58
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from solana.publickey import PublicKey
from spl.token.instructions import get_associated_token_address
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradingConfig:
    """Configuration for automated trading"""
    wallet_address: str
    max_trade_amount_sol: float
    max_daily_trades: int
    min_safety_score: float
    min_profit_score: float
    max_slippage_bps: int  # basis points (100 bps = 1%)
    emergency_stop: bool
    allowed_chains: List[str]
    auto_trade_enabled: bool

@dataclass
class TradeSignal:
    """Trade signal data structure"""
    token_address: str
    token_name: str
    token_symbol: str
    chain: str
    safety_score: float
    profit_score: float
    trade_amount_sol: float
    max_slippage_bps: int
    timestamp: datetime

class PhantomWalletAutomation:
    """Safe automation for Phantom wallet using smart contract patterns"""
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.client = AsyncClient(rpc_url)
        self.config: Optional[TradingConfig] = None
        self.daily_trades = 0
        self.last_reset_date = datetime.utcnow().date()
        self.active_positions = {}
        
    async def initialize_trading_config(self, config: TradingConfig) -> Dict:
        """Initialize safe trading configuration"""
        try:
            # Validate wallet address
            try:
                wallet_pubkey = PublicKey(config.wallet_address)
            except Exception:
                return {"error": "Invalid wallet address format"}
            
            # Check wallet balance
            balance_response = await self.client.get_balance(wallet_pubkey)
            balance_sol = balance_response.value / 1e9
            
            if balance_sol < config.max_trade_amount_sol:
                return {
                    "error": f"Insufficient balance. Current: {balance_sol:.2f} SOL, Required: {config.max_trade_amount_sol} SOL"
                }
            
            # Store configuration
            self.config = config
            
            # Create safety contract state (simulated)
            safety_state = {
                "wallet_address": config.wallet_address,
                "max_trade_amount": config.max_trade_amount_sol,
                "daily_limit": config.max_daily_trades,
                "safety_threshold": config.min_safety_score,
                "emergency_stop": config.emergency_stop,
                "created_at": datetime.utcnow().isoformat(),
                "permissions_granted": True
            }
            
            return {
                "status": "success",
                "message": f"Smart contract automation initialized for wallet {config.wallet_address[:4]}...{config.wallet_address[-4:]}",
                "safety_state": safety_state,
                "wallet_balance": f"{balance_sol:.2f} SOL",
                "protections_active": [
                    f"Max trade: {config.max_trade_amount_sol} SOL",
                    f"Daily limit: {config.max_daily_trades} trades",
                    f"Min safety score: {config.min_safety_score}/10",
                    f"Max slippage: {config.max_slippage_bps/100}%",
                    "Emergency stop available",
                    "Revoke permissions anytime"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error initializing trading config: {str(e)}")
            return {"error": f"Configuration failed: {str(e)}"}
    
    async def process_trade_signal(self, signal: TradeSignal) -> Dict:
        """Process incoming trade signal with safety checks"""
        if not self.config or not self.config.auto_trade_enabled:
            return {"status": "skipped", "reason": "Auto-trading not enabled"}
        
        # Reset daily counter if new day
        current_date = datetime.utcnow().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.last_reset_date = current_date
        
        # Safety checks
        safety_checks = await self._run_safety_checks(signal)
        if not safety_checks["passed"]:
            return {
                "status": "rejected",
                "reason": safety_checks["reason"],
                "signal": signal.token_symbol
            }
        
        # Execute trade
        try:
            trade_result = await self._execute_safe_trade(signal)
            if trade_result["status"] == "success":
                self.daily_trades += 1
                self.active_positions[signal.token_address] = {
                    "symbol": signal.token_symbol,
                    "entry_time": signal.timestamp,
                    "entry_amount": signal.trade_amount_sol,
                    "safety_score": signal.safety_score
                }
            
            return trade_result
            
        except Exception as e:
            logger.error(f"Trade execution error: {str(e)}")
            return {"status": "error", "reason": f"Execution failed: {str(e)}"}
    
    async def _run_safety_checks(self, signal: TradeSignal) -> Dict:
        """Comprehensive safety checks before trade execution"""
        
        # Check emergency stop
        if self.config.emergency_stop:
            return {"passed": False, "reason": "Emergency stop is active"}
        
        # Check daily trade limit
        if self.daily_trades >= self.config.max_daily_trades:
            return {"passed": False, "reason": f"Daily trade limit reached ({self.config.max_daily_trades})"}
        
        # Check trade amount limit
        if signal.trade_amount_sol > self.config.max_trade_amount_sol:
            return {"passed": False, "reason": f"Trade amount exceeds limit ({self.config.max_trade_amount_sol} SOL)"}
        
        # Check safety score threshold
        if signal.safety_score < self.config.min_safety_score:
            return {"passed": False, "reason": f"Safety score too low ({signal.safety_score} < {self.config.min_safety_score})"}
        
        # Check profit score threshold
        if signal.profit_score < self.config.min_profit_score:
            return {"passed": False, "reason": f"Profit score too low ({signal.profit_score} < {self.config.min_profit_score})"}
        
        # Check chain allowlist
        if signal.chain.lower() not in [chain.lower() for chain in self.config.allowed_chains]:
            return {"passed": False, "reason": f"Chain {signal.chain} not in allowed list"}
        
        # Check slippage limits
        if signal.max_slippage_bps > self.config.max_slippage_bps:
            return {"passed": False, "reason": f"Slippage too high ({signal.max_slippage_bps/100}% > {self.config.max_slippage_bps/100}%)"}
        
        # Check wallet balance
        try:
            wallet_pubkey = PublicKey(self.config.wallet_address)
            balance_response = await self.client.get_balance(wallet_pubkey)
            balance_sol = balance_response.value / 1e9
            
            if balance_sol < signal.trade_amount_sol + 0.01:  # 0.01 SOL for fees
                return {"passed": False, "reason": f"Insufficient balance for trade + fees"}
                
        except Exception as e:
            return {"passed": False, "reason": f"Balance check failed: {str(e)}"}
        
        # All checks passed
        return {"passed": True, "reason": "All safety checks passed"}
    
    async def _execute_safe_trade(self, signal: TradeSignal) -> Dict:
        """Execute trade through Jupiter API with safety measures"""
        try:
            # Get Jupiter quote
            quote_response = await self._get_jupiter_quote(
                input_mint="So11111111111111111111111111111111111111112",  # SOL
                output_mint=signal.token_address,
                amount=int(signal.trade_amount_sol * 1e9),  # Convert SOL to lamports
                slippage_bps=signal.max_slippage_bps
            )
            
            if not quote_response:
                return {"status": "error", "reason": "Failed to get Jupiter quote"}
            
            # Get swap transaction
            swap_transaction = await self._get_jupiter_swap_transaction(
                quote_response, 
                self.config.wallet_address
            )
            
            if not swap_transaction:
                return {"status": "error", "reason": "Failed to create swap transaction"}
            
            # For security, we return the transaction for manual signing
            # In production, this would integrate with Phantom's transaction approval
            return {
                "status": "success",
                "message": f"Trade prepared for {signal.token_symbol}",
                "trade_details": {
                    "token": f"{signal.token_name} ({signal.token_symbol})",
                    "amount_sol": signal.trade_amount_sol,
                    "safety_score": signal.safety_score,
                    "profit_score": signal.profit_score,
                    "max_slippage": f"{signal.max_slippage_bps/100}%",
                    "timestamp": signal.timestamp.isoformat()
                },
                "transaction_ready": True,
                "requires_wallet_approval": True,
                "jupiter_quote": quote_response
            }
            
        except Exception as e:
            logger.error(f"Trade execution error: {str(e)}")
            return {"status": "error", "reason": f"Trade preparation failed: {str(e)}"}
    
    async def _get_jupiter_quote(self, input_mint: str, output_mint: str, 
                               amount: int, slippage_bps: int) -> Optional[Dict]:
        """Get quote from Jupiter API"""
        try:
            url = "https://quote-api.jup.ag/v6/quote"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps,
                "onlyDirectRoutes": "false",
                "asLegacyTransaction": "false"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Jupiter quote failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Jupiter quote error: {str(e)}")
            return None
    
    async def _get_jupiter_swap_transaction(self, quote: Dict, wallet_address: str) -> Optional[Dict]:
        """Get swap transaction from Jupiter API"""
        try:
            url = "https://quote-api.jup.ag/v6/swap"
            payload = {
                "quoteResponse": quote,
                "userPublicKey": wallet_address,
                "wrapAndUnwrapSol": True,
                "useSharedAccounts": True,
                "feeAccount": None
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Jupiter swap transaction failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Jupiter swap transaction error: {str(e)}")
            return None
    
    async def emergency_stop(self) -> Dict:
        """Emergency stop all automated trading"""
        if self.config:
            self.config.emergency_stop = True
            self.config.auto_trade_enabled = False
            
            return {
                "status": "emergency_stop_activated",
                "message": "All automated trading has been stopped",
                "timestamp": datetime.utcnow().isoformat(),
                "active_positions": len(self.active_positions)
            }
        
        return {"error": "No active trading configuration"}
    
    async def revoke_permissions(self) -> Dict:
        """Revoke all trading permissions"""
        self.config = None
        self.active_positions.clear()
        self.daily_trades = 0
        
        return {
            "status": "permissions_revoked",
            "message": "All trading permissions have been revoked",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_trading_status(self) -> Dict:
        """Get current trading status and statistics"""
        if not self.config:
            return {"error": "No trading configuration active"}
        
        try:
            # Get current wallet balance
            wallet_pubkey = PublicKey(self.config.wallet_address)
            balance_response = await self.client.get_balance(wallet_pubkey)
            balance_sol = balance_response.value / 1e9
            
            return {
                "status": "active" if self.config.auto_trade_enabled and not self.config.emergency_stop else "inactive",
                "wallet_balance": f"{balance_sol:.2f} SOL",
                "daily_trades": f"{self.daily_trades}/{self.config.max_daily_trades}",
                "active_positions": len(self.active_positions),
                "safety_settings": {
                    "max_trade_amount": f"{self.config.max_trade_amount_sol} SOL",
                    "min_safety_score": self.config.min_safety_score,
                    "min_profit_score": self.config.min_profit_score,
                    "max_slippage": f"{self.config.max_slippage_bps/100}%"
                },
                "emergency_stop": self.config.emergency_stop,
                "permissions_active": True
            }
            
        except Exception as e:
            return {"error": f"Status check failed: {str(e)}"}
    
    async def update_trading_limits(self, new_limits: Dict) -> Dict:
        """Update trading limits safely"""
        if not self.config:
            return {"error": "No trading configuration active"}
        
        try:
            # Validate new limits
            if "max_trade_amount_sol" in new_limits:
                if new_limits["max_trade_amount_sol"] <= 0 or new_limits["max_trade_amount_sol"] > 10:
                    return {"error": "Max trade amount must be between 0 and 10 SOL"}
                self.config.max_trade_amount_sol = new_limits["max_trade_amount_sol"]
            
            if "max_daily_trades" in new_limits:
                if new_limits["max_daily_trades"] <= 0 or new_limits["max_daily_trades"] > 20:
                    return {"error": "Daily trade limit must be between 1 and 20"}
                self.config.max_daily_trades = new_limits["max_daily_trades"]
            
            if "min_safety_score" in new_limits:
                if new_limits["min_safety_score"] < 5.0 or new_limits["min_safety_score"] > 10.0:
                    return {"error": "Safety score must be between 5.0 and 10.0"}
                self.config.min_safety_score = new_limits["min_safety_score"]
            
            if "max_slippage_bps" in new_limits:
                if new_limits["max_slippage_bps"] < 100 or new_limits["max_slippage_bps"] > 2000:  # 1% to 20%
                    return {"error": "Slippage must be between 1% and 20%"}
                self.config.max_slippage_bps = new_limits["max_slippage_bps"]
            
            return {
                "status": "success",
                "message": "Trading limits updated successfully",
                "updated_limits": new_limits,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to update limits: {str(e)}"}

# Global automation instance
wallet_automation = PhantomWalletAutomation()