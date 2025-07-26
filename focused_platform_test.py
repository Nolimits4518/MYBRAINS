#!/usr/bin/env python3
"""
Focused test for Enhanced Universal Trading Platform Connector
Tests the specific enhanced endpoints mentioned in the review request
"""

import requests
import sys
import json
import time
from datetime import datetime

class FocusedPlatformTester:
    def __init__(self, base_url="https://e43dbe7c-0788-4a57-a112-34fe20a53a1b.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
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
            "details": details
        })

    def run_api_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, 
                     data: dict = None, params: dict = None) -> tuple:
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

    def test_specific_enhanced_endpoints(self):
        """Test the specific enhanced endpoints mentioned in the review request"""
        print("🚀 Testing Enhanced Universal Trading Platform Connector Endpoints")
        print("=" * 80)
        
        # 1. POST /api/platform/analyze - Test with TradeLocker
        print("\n1️⃣ Testing POST /api/platform/analyze with TradeLocker...")
        analyze_data = {
            "platform_name": "TradeLocker",
            "login_url": "https://platform.tradelocker.com/login"
        }
        
        success, data = self.run_api_test("TradeLocker Analysis", "POST", "api/platform/analyze", data=analyze_data)
        
        if success:
            response_data = data.get("data", {})
            login_fields = response_data.get("login_fields", [])
            
            # Check if we detect 3 fields (email, password, server)
            if len(login_fields) >= 3:
                self.log_test("TradeLocker 3 Fields Detected", True, f"Found {len(login_fields)} fields")
                
                # Check for specific field types
                field_names = [field.get("name", "").lower() for field in login_fields]
                field_types = [field.get("type", "") for field in login_fields]
                
                has_email = any("email" in name or "user" in name for name in field_names)
                has_password = "password" in field_types
                has_server = any("server" in name for name in field_names) or "select" in field_types
                
                if has_email and has_password and has_server:
                    self.log_test("TradeLocker Required Fields", True, "Email, password, and server fields detected")
                else:
                    self.log_test("TradeLocker Required Fields", False, f"Missing fields - Email: {has_email}, Password: {has_password}, Server: {has_server}")
            else:
                self.log_test("TradeLocker 3 Fields Detected", False, f"Only found {len(login_fields)} fields, expected 3+")
        
        # 2. POST /api/platform/save-credentials - Test with server field
        print("\n2️⃣ Testing POST /api/platform/save-credentials with server field...")
        credentials_data = {
            "platform_id": "tradelocker_test",
            "username": "test@example.com",
            "password": "testpass123",
            "server": "demo",
            "additional_fields": {"account_type": "demo"},
            "enable_2fa": False
        }
        
        success, data = self.run_api_test("Save Credentials with Server", "POST", "api/platform/save-credentials", data=credentials_data)
        
        saved_platform_id = None
        if success:
            saved_platform_id = data.get("platform_id", "")
            if saved_platform_id:
                self.log_test("Credentials Saved Successfully", True, f"Platform ID: {saved_platform_id}")
            else:
                self.log_test("Credentials Saved Successfully", False, "No platform_id returned")
        
        # 3. POST /api/platform/connect/{platform_id} - Test connecting
        if saved_platform_id:
            print(f"\n3️⃣ Testing POST /api/platform/connect/{saved_platform_id}...")
            success, data = self.run_api_test("Platform Connection", "POST", f"api/platform/connect/{saved_platform_id}")
            
            if success:
                connected = data.get("connected", False)
                message = data.get("message", "")
                
                # Connection might fail due to invalid URL, but API should respond properly
                if "connected" in data:
                    self.log_test("Connection API Response", True, f"Response received: {message}")
                else:
                    self.log_test("Connection API Response", False, "Missing 'connected' field in response")
        
        # 4. GET /api/platform/interface/{platform_id} - Test getting interface analysis
        if saved_platform_id:
            print(f"\n4️⃣ Testing GET /api/platform/interface/{saved_platform_id}...")
            success, data = self.run_api_test("Interface Analysis Data", "GET", f"api/platform/interface/{saved_platform_id}")
            
            if success:
                interface_data = data.get("data", {})
                expected_fields = ["buy_elements", "sell_elements", "trading_inputs", "positions_table"]
                
                found_fields = sum(1 for field in expected_fields if field in interface_data)
                if found_fields > 0:
                    self.log_test("Interface Analysis Fields", True, f"Found {found_fields}/{len(expected_fields)} expected fields")
                else:
                    self.log_test("Interface Analysis Fields", False, "No expected interface fields found")
            else:
                # Interface analysis might fail if platform isn't connected, but API should handle it
                if data.get("status") == "error":
                    self.log_test("Interface Analysis Error Handling", True, "API properly handles interface analysis errors")
        
        # 5. POST /api/platform/analyze-interface - Test re-analyzing interface
        if saved_platform_id:
            print(f"\n5️⃣ Testing POST /api/platform/analyze-interface...")
            reanalyze_data = {"platform_id": saved_platform_id}
            success, data = self.run_api_test("Interface Re-analysis", "POST", "api/platform/analyze-interface", data=reanalyze_data)
            
            if success:
                analysis_data = data.get("data", {})
                if "interface_analysis" in analysis_data:
                    self.log_test("Interface Re-analysis Success", True, "Interface re-analysis completed")
                else:
                    self.log_test("Interface Re-analysis Success", False, "No interface_analysis in response")
            else:
                # Re-analysis might fail if platform isn't connected
                if data.get("status") == "error":
                    self.log_test("Interface Re-analysis Error Handling", True, "API properly handles re-analysis errors")
        
        # 6. POST /api/platform/trade - Test trade execution
        if saved_platform_id:
            print(f"\n6️⃣ Testing POST /api/platform/trade...")
            trade_data = {
                "platform_id": saved_platform_id,
                "symbol": "EURUSD",
                "action": "BUY",
                "quantity": 0.1,
                "price": 1.0950,
                "order_type": "LIMIT"
            }
            
            success, data = self.run_api_test("Trade Execution", "POST", "api/platform/trade", data=trade_data)
            
            if success:
                trade_result = data.get("data", {})
                expected_fields = ["order_id", "filled_quantity", "filled_price", "timestamp"]
                
                found_fields = sum(1 for field in expected_fields if field in trade_result)
                if found_fields > 0:
                    self.log_test("Trade Result Fields", True, f"Found {found_fields}/{len(expected_fields)} expected fields")
                else:
                    self.log_test("Trade Result Fields", False, "No expected trade result fields found")
            else:
                # Trade execution might fail if platform isn't connected
                if data.get("status") == "error":
                    self.log_test("Trade Execution Error Handling", True, "API properly handles trade execution errors")
        
        # 7. POST /api/platform/close-position - Test closing position
        if saved_platform_id:
            print(f"\n7️⃣ Testing POST /api/platform/close-position...")
            close_data = {
                "platform_id": saved_platform_id,
                "position_symbol": "EURUSD"
            }
            
            success, data = self.run_api_test("Position Closing", "POST", "api/platform/close-position", data=close_data)
            
            if success:
                close_result = data.get("data", {})
                expected_fields = ["order_id", "timestamp"]
                
                found_fields = sum(1 for field in expected_fields if field in close_result)
                if found_fields > 0:
                    self.log_test("Position Close Fields", True, f"Found {found_fields}/{len(expected_fields)} expected fields")
                else:
                    self.log_test("Position Close Fields", False, "No expected close result fields found")
            else:
                # Position closing might fail if platform isn't connected
                if data.get("status") == "error":
                    self.log_test("Position Close Error Handling", True, "API properly handles position close errors")
        
        # Print results
        print("\n" + "=" * 80)
        print("📊 FOCUSED ENHANCED PLATFORM CONNECTOR TEST RESULTS")
        print("=" * 80)
        
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Show critical failures
        critical_failures = [r for r in self.test_results if not r["success"] and 
                           any(critical in r["name"] for critical in 
                               ["TradeLocker Analysis", "Save Credentials", "Trade Execution", "Position Closing"])]
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES:")
            for failure in critical_failures:
                print(f"  ❌ {failure['name']}: {failure['details']}")
        else:
            print("\n✅ No critical issues found in core enhanced functionality")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = FocusedPlatformTester()
    
    try:
        success = tester.test_specific_enhanced_endpoints()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())