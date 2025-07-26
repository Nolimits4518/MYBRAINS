#!/usr/bin/env python3
"""
RSI Trading Bot Backend API Test Suite
Tests all backend endpoints and functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

class RSITradingBotTester:
    def __init__(self, base_url="https://eb4be883-8e6c-40a1-977f-51245952b0cc.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details and success:
            print(f"   ℹ️  {details}")

    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Message: {data.get('message', 'N/A')}, Status: {data.get('status', 'N/A')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Root Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("Root Endpoint", False, str(e))
            return False

    def test_bot_status(self):
        """Test bot status endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/bot/status")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success' and 'data' in data:
                    bot_data = data['data']
                    details = f"Running: {bot_data.get('running')}, Price: ${bot_data.get('current_price', 0):.2f}, RSI: {bot_data.get('rsi_value', 0):.1f}"
                else:
                    success = False
                    details = "Invalid response structure"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Bot Status", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Bot Status", False, str(e))
            return False, {}

    def test_bot_config_get(self):
        """Test get bot configuration"""
        try:
            response = self.session.get(f"{self.base_url}/api/bot/config")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success' and 'data' in data:
                    config = data['data']
                    details = f"Symbol: {config.get('symbol')}, RSI Length: {config.get('rsi_length')}, Stop Loss: {config.get('stop_loss_pct')}%"
                else:
                    success = False
                    details = "Invalid response structure"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Get Bot Config", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Get Bot Config", False, str(e))
            return False, {}

    def test_bot_config_update(self):
        """Test update bot configuration"""
        try:
            test_config = {
                "symbol": "ETHUSD",
                "rsi_length": 14,
                "stop_loss_pct": 1.5,
                "take_profit_pct": 2.5,
                "position_size": 0.1,
                "enable_grid_tp": True
            }
            
            response = self.session.post(f"{self.base_url}/api/bot/config", json=test_config)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success':
                    details = f"Config updated successfully"
                else:
                    success = False
                    details = "Invalid response structure"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Update Bot Config", success, details)
            return success
            
        except Exception as e:
            self.log_test("Update Bot Config", False, str(e))
            return False

    def test_telegram_integration(self):
        """Test Telegram integration - CRITICAL TEST"""
        try:
            response = self.session.post(f"{self.base_url}/api/telegram/test")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success':
                    details = "Telegram test message sent successfully!"
                else:
                    success = False
                    details = f"Telegram test failed: {data.get('message', 'Unknown error')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Telegram Integration (CRITICAL)", success, details)
            return success
            
        except Exception as e:
            self.log_test("Telegram Integration (CRITICAL)", False, str(e))
            return False

    def test_bot_start(self):
        """Test starting the bot"""
        try:
            config = {
                "symbol": "ETHUSD",
                "rsi_length": 14,
                "stop_loss_pct": 1.0,
                "take_profit_pct": 2.0,
                "position_size": 0.1,
                "enable_grid_tp": True
            }
            
            response = self.session.post(f"{self.base_url}/api/bot/start", json=config)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success':
                    details = "Bot started successfully"
                else:
                    success = False
                    details = f"Start failed: {data.get('message', 'Unknown error')}"
            else:
                # Check if bot is already running
                if response.status_code == 400:
                    error_data = response.json()
                    if "already running" in error_data.get('detail', '').lower():
                        success = True
                        details = "Bot already running (expected behavior)"
                    else:
                        details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown')}"
                else:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Start Bot", success, details)
            return success
            
        except Exception as e:
            self.log_test("Start Bot", False, str(e))
            return False

    def test_bot_stop(self):
        """Test stopping the bot"""
        try:
            response = self.session.post(f"{self.base_url}/api/bot/stop")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success':
                    details = "Bot stopped successfully"
                else:
                    success = False
                    details = f"Stop failed: {data.get('message', 'Unknown error')}"
            else:
                # Check if bot is not running
                if response.status_code == 400:
                    error_data = response.json()
                    if "not running" in error_data.get('detail', '').lower():
                        success = True
                        details = "Bot not running (expected behavior)"
                    else:
                        details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown')}"
                else:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Stop Bot", success, details)
            return success
            
        except Exception as e:
            self.log_test("Stop Bot", False, str(e))
            return False

    def test_trades_history(self):
        """Test trades history endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/trades/history")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success' and 'data' in data:
                    trades = data['data']
                    details = f"Retrieved {len(trades)} trades from history"
                else:
                    success = False
                    details = "Invalid response structure"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Trades History", success, details)
            return success
            
        except Exception as e:
            self.log_test("Trades History", False, str(e))
            return False

    def test_market_price(self):
        """Test market price endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/market/price/ETHUSD")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success' and 'data' in data:
                    price_data = data['data']
                    details = f"Symbol: {price_data.get('symbol')}, Price: ${price_data.get('price', 0):.2f}"
                else:
                    success = False
                    details = "Invalid response structure"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Market Price", success, details)
            return success
            
        except Exception as e:
            self.log_test("Market Price", False, str(e))
            return False

    def test_save_trade(self):
        """Test saving a trade"""
        try:
            test_trade = {
                "action": "buy",
                "symbol": "ETHUSD",
                "price": 2500.0,
                "timestamp": datetime.now().isoformat(),
                "reason": "Test trade for API validation"
            }
            
            response = self.session.post(f"{self.base_url}/api/trades/save", json=test_trade)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if data.get('status') == 'success':
                    details = f"Trade saved with ID: {data.get('trade_id', 'N/A')}"
                else:
                    success = False
                    details = "Invalid response structure"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Save Trade", success, details)
            return success
            
        except Exception as e:
            self.log_test("Save Trade", False, str(e))
            return False

    def run_full_test_suite(self):
        """Run all tests in sequence"""
        print("🚀 Starting RSI Trading Bot Backend Test Suite")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        print("\n📡 BASIC CONNECTIVITY TESTS")
        print("-" * 30)
        self.test_root_endpoint()
        
        # Bot status and configuration tests
        print("\n🤖 BOT STATUS & CONFIGURATION TESTS")
        print("-" * 40)
        status_success, status_data = self.test_bot_status()
        config_get_success, config_data = self.test_bot_config_get()
        self.test_bot_config_update()
        
        # Critical Telegram integration test
        print("\n📱 TELEGRAM INTEGRATION TEST (CRITICAL)")
        print("-" * 45)
        telegram_success = self.test_telegram_integration()
        
        # Bot control tests
        print("\n⚡ BOT CONTROL TESTS")
        print("-" * 25)
        
        # First ensure bot is stopped
        self.test_bot_stop()
        time.sleep(1)
        
        # Test starting the bot
        start_success = self.test_bot_start()
        time.sleep(2)  # Give bot time to start
        
        # Check status after start
        if start_success:
            print("   ℹ️  Checking bot status after start...")
            status_success_after_start, status_data_after_start = self.test_bot_status()
            if status_success_after_start:
                running = status_data_after_start.get('data', {}).get('running', False)
                print(f"   ℹ️  Bot running status: {running}")
        
        # Test stopping the bot
        self.test_bot_stop()
        
        # Market data and trading tests
        print("\n📊 MARKET DATA & TRADING TESTS")
        print("-" * 35)
        self.test_market_price()
        self.test_trades_history()
        self.test_save_trade()
        
        # Final results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Critical issues check
        critical_issues = []
        if not telegram_success:
            critical_issues.append("❌ CRITICAL: Telegram integration failed")
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   {issue}")
        else:
            print("\n✅ No critical issues found!")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = RSITradingBotTester()
    
    try:
        success = tester.run_full_test_suite()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())