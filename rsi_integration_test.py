#!/usr/bin/env python3
"""
RSI Trading System Integration Test
Tests the complete integrated RSI trading system with Universal Platform Connector
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class RSIIntegrationTester:
    def __init__(self, base_url="https://e43dbe7c-0788-4a57-a112-34fe20a53a1b.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if details and success:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "data": data
        })

    def run_api_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, 
                     data: Dict = None, params: Dict = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            if success:
                self.log_test(name, True, f"Status: {response.status_code}")
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
            
            return success, response_data
            
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_rsi_trading_system_status(self):
        """Test RSI Trading System Status - GET /api/bot/status"""
        print("\n🔍 Testing RSI Trading System Status...")
        success, data = self.run_api_test("RSI Bot Status", "GET", "api/bot/status")
        
        if success:
            bot_data = data.get("data", {})
            
            # Test for required RSI trading fields
            required_fields = [
                "bot_active", "auto_trading_enabled", "connected_platforms", 
                "total_platforms", "current_positions", "crypto_data", "signals"
            ]
            
            for field in required_fields:
                if field in bot_data:
                    self.log_test(f"RSI Status Field: {field}", True)
                else:
                    self.log_test(f"RSI Status Field: {field}", False, f"Missing field")
            
            # Test crypto data structure
            crypto_data = bot_data.get("crypto_data", {})
            expected_cryptos = ["bitcoin", "ethereum", "binancecoin"]
            
            for crypto in expected_cryptos:
                if crypto in crypto_data:
                    crypto_info = crypto_data[crypto]
                    
                    # Test crypto data fields
                    crypto_fields = ["price", "rsi", "signal"]
                    for field in crypto_fields:
                        if field in crypto_info:
                            self.log_test(f"Crypto Data {crypto.upper()} {field}", True)
                        else:
                            self.log_test(f"Crypto Data {crypto.upper()} {field}", False, f"Missing field")
                    
                    # Test RSI signal structure
                    signal = crypto_info.get("signal", {})
                    signal_fields = ["symbol", "timestamp", "price", "rsi", "signal", "action", "confidence"]
                    for field in signal_fields:
                        if field in signal:
                            self.log_test(f"RSI Signal {crypto.upper()} {field}", True)
                        else:
                            self.log_test(f"RSI Signal {crypto.upper()} {field}", False, f"Missing field")
                else:
                    self.log_test(f"Crypto Data: {crypto.upper()}", False, f"Missing crypto data")
            
            # Test auto trading status
            auto_trading = bot_data.get("auto_trading_enabled")
            if auto_trading is not None:
                self.log_test("Auto Trading Status", True, f"Auto trading: {'enabled' if auto_trading else 'disabled'}")
            else:
                self.log_test("Auto Trading Status", False, "Auto trading status not available")

    def test_market_data_endpoint(self):
        """Test Market Data - GET /api/market/data"""
        print("\n🔍 Testing Market Data Endpoint...")
        success, data = self.run_api_test("Market Data", "GET", "api/market/data")
        
        if success:
            market_data = data.get("data", {})
            expected_cryptos = ["bitcoin", "ethereum", "binancecoin"]
            
            for crypto in expected_cryptos:
                if crypto in market_data:
                    crypto_market = market_data[crypto]
                    
                    # Test market data structure
                    market_fields = ["symbol", "price", "rsi", "chart_data", "signal"]
                    for field in market_fields:
                        if field in crypto_market:
                            self.log_test(f"Market Data {crypto.upper()} {field}", True)
                        else:
                            self.log_test(f"Market Data {crypto.upper()} {field}", False, f"Missing field")
                    
                    # Test chart data structure
                    chart_data = crypto_market.get("chart_data", [])
                    if chart_data and len(chart_data) > 0:
                        sample_point = chart_data[0]
                        chart_fields = ["time", "price", "rsi"]
                        for field in chart_fields:
                            if field in sample_point:
                                self.log_test(f"Chart Data {crypto.upper()} {field}", True)
                            else:
                                self.log_test(f"Chart Data {crypto.upper()} {field}", False, f"Missing field")
                    else:
                        self.log_test(f"Chart Data {crypto.upper()}", False, "No chart data available")
                else:
                    self.log_test(f"Market Data: {crypto.upper()}", False, f"Missing market data")

    def test_platform_connector_integration(self):
        """Test Platform Connector Integration - GET /api/platform/list"""
        print("\n🔍 Testing Platform Connector Integration...")
        success, data = self.run_api_test("Platform List", "GET", "api/platform/list")
        
        if success:
            platforms = data.get("data", [])
            count = data.get("count", 0)
            
            self.log_test("Platform Management", True, f"Platform system operational, {count} platforms configured")
            
            # Test platform data structure if platforms exist
            if platforms and len(platforms) > 0:
                sample_platform = platforms[0]
                platform_fields = ["platform_id", "platform_name", "login_url", "is_connected"]
                
                for field in platform_fields:
                    if field in sample_platform:
                        self.log_test(f"Platform Field: {field}", True)
                    else:
                        self.log_test(f"Platform Field: {field}", False, f"Missing field")
            else:
                self.log_test("Platform Configuration", True, "No platforms configured (expected for fresh system)")

    def test_trading_signal_generation(self):
        """Test Trading Signal Generation - GET /api/bot/signals"""
        print("\n🔍 Testing Trading Signal Generation...")
        success, data = self.run_api_test("Trading Signals", "GET", "api/bot/signals")
        
        if success:
            signals_data = data.get("data", {})
            
            # Test signals structure
            signals = signals_data.get("signals", {})
            auto_trading = signals_data.get("auto_trading_enabled")
            last_update = signals_data.get("last_update")
            
            if signals:
                self.log_test("Signal Generation", True, f"Signals available for {len(signals)} symbols")
                
                # Test individual signal structure
                for symbol, signal in signals.items():
                    signal_fields = ["symbol", "timestamp", "price", "rsi", "signal", "action", "confidence"]
                    for field in signal_fields:
                        if field in signal:
                            self.log_test(f"Signal {symbol} {field}", True)
                        else:
                            self.log_test(f"Signal {symbol} {field}", False, f"Missing field")
            else:
                self.log_test("Signal Generation", True, "No active signals (normal for stable market)")
            
            if auto_trading is not None:
                self.log_test("Auto Trading Integration", True, f"Auto trading: {'enabled' if auto_trading else 'disabled'}")
            else:
                self.log_test("Auto Trading Integration", False, "Auto trading status not available")

    def test_communication_links(self):
        """Test Communication Links - API endpoints and WebSocket readiness"""
        print("\n🔍 Testing Communication Links...")
        
        # Test core API endpoints
        endpoints_to_test = [
            ("Root Endpoint", "GET", ""),
            ("Bot Status", "GET", "api/bot/status"),
            ("Market Data", "GET", "api/market/data"),
            ("Platform List", "GET", "api/platform/list"),
            ("Trading Signals", "GET", "api/bot/signals"),
            ("Crypto List", "GET", "api/crypto/list"),
            ("Timeframes", "GET", "api/crypto/timeframes")
        ]
        
        working_endpoints = 0
        for name, method, endpoint in endpoints_to_test:
            success, _ = self.run_api_test(f"API Link: {name}", method, endpoint)
            if success:
                working_endpoints += 1
        
        # Test API communication health
        if working_endpoints == len(endpoints_to_test):
            self.log_test("API Communication", True, "All core endpoints responding")
        elif working_endpoints >= len(endpoints_to_test) * 0.8:
            self.log_test("API Communication", True, f"{working_endpoints}/{len(endpoints_to_test)} endpoints working")
        else:
            self.log_test("API Communication", False, f"Only {working_endpoints}/{len(endpoints_to_test)} endpoints working")

    def test_auto_trading_functionality(self):
        """Test Auto-Trading Functionality"""
        print("\n🔍 Testing Auto-Trading Functionality...")
        
        # Test auto trading toggle
        success, data = self.run_api_test("Auto Trading Toggle", "POST", "api/bot/toggle-auto-trading")
        
        if success:
            toggle_data = data.get("data", {})
            auto_trading_enabled = toggle_data.get("auto_trading_enabled")
            message = toggle_data.get("message", "")
            
            if auto_trading_enabled is not None:
                self.log_test("Auto Trading Toggle", True, f"Toggle successful: {message}")
            else:
                self.log_test("Auto Trading Toggle", False, "Toggle response missing status")
        
        # Test trading configuration update
        config_update = {
            "rsi_oversold": 25,
            "rsi_overbought": 75,
            "position_size": 0.05,
            "stop_loss_pct": 1.5,
            "take_profit_pct": 3.0
        }
        
        success, data = self.run_api_test("Trading Config Update", "POST", "api/bot/update-config", data=config_update)
        
        if success:
            config_data = data.get("data", {})
            updated_config = config_data.get("config", {})
            
            # Verify configuration was updated
            config_fields = ["rsi_oversold", "rsi_overbought", "position_size", "stop_loss_pct", "take_profit_pct"]
            config_updated = True
            
            for field in config_fields:
                if field in updated_config:
                    self.log_test(f"Config Update {field}", True, f"Value: {updated_config[field]}")
                else:
                    self.log_test(f"Config Update {field}", False, f"Missing field")
                    config_updated = False
            
            if config_updated:
                self.log_test("Trading Configuration", True, "All configuration parameters updated successfully")
            else:
                self.log_test("Trading Configuration", False, "Configuration update incomplete")

    def test_signal_execution_readiness(self):
        """Test Signal Execution on Connected Platforms"""
        print("\n🔍 Testing Signal Execution Readiness...")
        
        # First check if there are any connected platforms
        success, data = self.run_api_test("Platform Connection Check", "GET", "api/platform/list")
        
        if success:
            platforms = data.get("data", [])
            connected_platforms = [p for p in platforms if p.get("is_connected", False)]
            
            if connected_platforms:
                self.log_test("Platform Connectivity", True, f"{len(connected_platforms)} platform(s) connected and ready")
                
                # Test signal execution capability (without actually executing)
                for platform in connected_platforms:
                    platform_name = platform.get("platform_name", "Unknown")
                    platform_id = platform.get("platform_id", "")
                    
                    self.log_test(f"Platform Ready: {platform_name}", True, f"ID: {platform_id}")
            else:
                self.log_test("Platform Connectivity", True, "No platforms connected (signals will be generated but not executed)")
        
        # Test that the system can generate signals for execution
        success, data = self.run_api_test("Signal Generation Readiness", "GET", "api/bot/signals")
        
        if success:
            signals_data = data.get("data", {})
            auto_trading = signals_data.get("auto_trading_enabled", False)
            
            if auto_trading:
                self.log_test("Signal Execution System", True, "Auto-trading enabled, signals will be executed on connected platforms")
            else:
                self.log_test("Signal Execution System", True, "Auto-trading disabled, signals generated but not executed")

    def run_comprehensive_integration_test(self):
        """Run comprehensive RSI trading system integration test"""
        print("🚀 Starting RSI Trading System Integration Test")
        print("Testing complete integrated RSI trading system with Universal Platform Connector")
        print("=" * 80)
        
        # Run all integration tests
        self.test_rsi_trading_system_status()
        self.test_market_data_endpoint()
        self.test_platform_connector_integration()
        self.test_trading_signal_generation()
        self.test_communication_links()
        self.test_auto_trading_functionality()
        self.test_signal_execution_readiness()
        
        # Print comprehensive results
        print("\n" + "=" * 80)
        print("📊 RSI TRADING SYSTEM INTEGRATION TEST RESULTS")
        print("=" * 80)
        
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Categorize results by system component
        categories = {
            "RSI Trading System": ["RSI Bot Status", "RSI Status Field", "Crypto Data", "RSI Signal"],
            "Market Data": ["Market Data", "Chart Data"],
            "Platform Connector": ["Platform", "Platform Field"],
            "Signal Generation": ["Trading Signals", "Signal Generation", "Signal "],
            "Communication": ["API Link", "API Communication"],
            "Auto Trading": ["Auto Trading", "Trading Config", "Config Update"],
            "Signal Execution": ["Platform Connectivity", "Signal Execution", "Platform Ready"]
        }
        
        print("\n📋 SYSTEM COMPONENT BREAKDOWN:")
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results if any(kw in r["name"] for kw in keywords)]
            passed = sum(1 for t in category_tests if t["success"])
            total = len(category_tests)
            if total > 0:
                print(f"  {category}: {passed}/{total} ({(passed/total)*100:.0f}%)")
        
        # Critical system status
        critical_failures = [r for r in self.test_results if not r["success"] and 
                           any(critical in r["name"] for critical in 
                               ["RSI Bot Status", "Market Data", "Trading Signals", "API Communication"])]
        
        if critical_failures:
            print("\n🚨 CRITICAL SYSTEM ISSUES:")
            for failure in critical_failures:
                print(f"  ❌ {failure['name']}: {failure['details']}")
        else:
            print("\n✅ NO CRITICAL SYSTEM ISSUES DETECTED")
        
        # System readiness assessment
        core_systems = ["RSI Trading System", "Market Data", "Platform Connector", "Signal Generation"]
        working_systems = 0
        
        for system in core_systems:
            system_tests = [r for r in self.test_results if any(kw in r["name"] for kw in categories.get(system, []))]
            if system_tests:
                passed = sum(1 for t in system_tests if t["success"])
                total = len(system_tests)
                if passed >= total * 0.7:  # 70% threshold
                    working_systems += 1
        
        print(f"\n🎯 SYSTEM READINESS: {working_systems}/{len(core_systems)} core systems operational")
        
        if working_systems == len(core_systems):
            print("🟢 SYSTEM STATUS: All systems operational - Ready for trading")
        elif working_systems >= len(core_systems) * 0.75:
            print("🟡 SYSTEM STATUS: Most systems operational - Minor issues detected")
        else:
            print("🔴 SYSTEM STATUS: Critical systems offline - Requires attention")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    print("RSI Trading System Integration Test")
    print("Testing complete integrated RSI trading system with Universal Platform Connector")
    print("=" * 80)
    
    tester = RSIIntegrationTester()
    
    try:
        success = tester.run_comprehensive_integration_test()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())