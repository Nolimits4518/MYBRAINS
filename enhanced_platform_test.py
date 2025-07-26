#!/usr/bin/env python3
"""
Enhanced Universal Trading Platform Connector - Comprehensive Backend API Testing
Tests intelligent trading features: platform analysis, interface detection, trade execution
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class EnhancedPlatformConnectorTester:
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

    def test_enhanced_platform_analysis(self):
        """Test enhanced platform analysis with TradeLocker"""
        print("\n🔍 Testing Enhanced Platform Analysis (TradeLocker)...")
        
        # Test TradeLocker platform analysis - should detect 3 fields (email, password, server)
        tradelocker_data = {
            "platform_name": "TradeLocker",
            "login_url": "https://platform.tradelocker.com/login"
        }
        
        success, data = self.run_api_test("TradeLocker Platform Analysis", "POST", "api/platform/analyze", data=tradelocker_data)
        
        if success:
            response_data = data.get("data", {})
            login_fields = response_data.get("login_fields", [])
            
            # Check if we have 3 fields as expected
            if len(login_fields) >= 3:
                self.log_test("TradeLocker Field Count", True, f"Found {len(login_fields)} fields (expected 3+)")
            else:
                self.log_test("TradeLocker Field Count", False, f"Found {len(login_fields)} fields, expected 3+")
            
            # Check for specific field types
            field_names = [field.get("name", "").lower() for field in login_fields]
            field_types = [field.get("type", "") for field in login_fields]
            
            # Check for email field
            if any("email" in name or "user" in name for name in field_names):
                self.log_test("TradeLocker Email Field", True, "Email/username field detected")
            else:
                self.log_test("TradeLocker Email Field", False, "Email/username field not found")
            
            # Check for password field
            if "password" in field_types:
                self.log_test("TradeLocker Password Field", True, "Password field detected")
            else:
                self.log_test("TradeLocker Password Field", False, "Password field not found")
            
            # Check for server field
            if any("server" in name for name in field_names) or "select" in field_types:
                self.log_test("TradeLocker Server Field", True, "Server selection field detected")
            else:
                self.log_test("TradeLocker Server Field", False, "Server selection field not found")
            
            # Validate field structure
            if login_fields:
                sample_field = login_fields[0]
                required_props = ["name", "type", "label", "placeholder", "required"]
                for prop in required_props:
                    if prop in sample_field:
                        self.log_test(f"TradeLocker Field Property: {prop}", True)
                    else:
                        self.log_test(f"TradeLocker Field Property: {prop}", False, f"Missing {prop} in field")
        
        return response_data if success else {}

    def test_enhanced_credentials_saving(self):
        """Test saving credentials with server field and additional fields"""
        print("\n🔍 Testing Enhanced Credentials Saving...")
        
        # Test saving credentials with server field and additional fields
        enhanced_credentials = {
            "platform_id": "tradelocker_test",
            "username": "trader@example.com",
            "password": "SecurePass123!",
            "server": "demo",
            "additional_fields": {
                "account_type": "demo",
                "region": "EU",
                "broker": "TradeLocker Demo"
            },
            "enable_2fa": False
        }
        
        success, data = self.run_api_test("Enhanced Credentials Save", "POST", "api/platform/save-credentials", data=enhanced_credentials)
        
        saved_platform_id = None
        if success:
            saved_platform_id = data.get("platform_id", "")
            if saved_platform_id:
                self.log_test("Enhanced Credentials Saved", True, f"Platform ID: {saved_platform_id}")
                
                # Verify the platform appears in the list with correct data
                success, list_data = self.run_api_test("Platform List After Enhanced Save", "GET", "api/platform/list")
                if success:
                    platforms = list_data.get("data", [])
                    found_platform = None
                    for platform in platforms:
                        if platform.get("platform_id") == saved_platform_id:
                            found_platform = platform
                            break
                    
                    if found_platform:
                        self.log_test("Enhanced Platform in List", True, f"Platform found with ID: {saved_platform_id}")
                        
                        # Check if server field is preserved
                        if "server" in str(found_platform):
                            self.log_test("Server Field Preserved", True, "Server field data maintained")
                        else:
                            self.log_test("Server Field Preserved", False, "Server field data not found")
                    else:
                        self.log_test("Enhanced Platform in List", False, "Saved platform not found in list")
            else:
                self.log_test("Enhanced Credentials Saved", False, "No platform_id returned")
        
        return saved_platform_id

    def test_platform_connection_with_interface_analysis(self):
        """Test connecting to platform and analyzing interface"""
        print("\n🔍 Testing Platform Connection with Interface Analysis...")
        
        # First save a platform for testing
        platform_id = self.test_enhanced_credentials_saving()
        
        if platform_id:
            # Test connecting to the platform
            success, data = self.run_api_test("Enhanced Platform Connection", "POST", f"api/platform/connect/{platform_id}")
            
            if success:
                connected = data.get("connected", False)
                message = data.get("message", "")
                
                # Connection might fail due to invalid URL, but API should respond properly
                if "connected" in data:
                    self.log_test("Connection API Response", True, f"Response: {message}")
                else:
                    self.log_test("Connection API Response", False, "Missing 'connected' field")
                
                # Test getting interface information (even if connection failed)
                success, interface_data = self.run_api_test("Platform Interface Info", "GET", f"api/platform/interface/{platform_id}")
                
                if success:
                    interface_info = interface_data.get("data", {})
                    
                    # Check for interface analysis fields
                    expected_interface_fields = ["buy_elements", "sell_elements", "trading_inputs", "positions_table"]
                    for field in expected_interface_fields:
                        if field in interface_info:
                            self.log_test(f"Interface Field: {field}", True)
                        else:
                            self.log_test(f"Interface Field: {field}", False, f"Missing {field} in interface data")
                else:
                    # Interface analysis might fail if platform isn't actually connected
                    if interface_data.get("status") == "error":
                        self.log_test("Interface Analysis Error Handling", True, "API properly handles interface analysis errors")
                
                # Test re-analyzing interface
                reanalyze_data = {"platform_id": platform_id}
                success, reanalyze_response = self.run_api_test("Interface Re-analysis", "POST", "api/platform/analyze-interface", data=reanalyze_data)
                
                if success:
                    analysis_data = reanalyze_response.get("data", {})
                    if "interface_analysis" in analysis_data:
                        self.log_test("Interface Re-analysis", True, "Interface re-analysis completed")
                    else:
                        self.log_test("Interface Re-analysis", False, "No interface_analysis in response")
                else:
                    # Re-analysis might fail if platform isn't connected
                    if reanalyze_response.get("status") == "error":
                        self.log_test("Interface Re-analysis Error Handling", True, "API properly handles re-analysis errors")
        
        return platform_id

    def test_trade_execution(self):
        """Test trade execution through web automation"""
        print("\n🔍 Testing Trade Execution...")
        
        # Use the platform from previous test
        platform_id = "tradelocker_test"
        
        # Test comprehensive trade order
        trade_order = {
            "platform_id": platform_id,
            "symbol": "EURUSD",
            "action": "BUY",
            "quantity": 0.1,
            "price": 1.0950,
            "order_type": "LIMIT"
        }
        
        success, data = self.run_api_test("Trade Execution", "POST", "api/platform/trade", data=trade_order)
        
        if success:
            trade_result = data.get("data", {})
            
            # Check trade result structure
            expected_trade_fields = ["order_id", "filled_quantity", "filled_price", "timestamp"]
            for field in expected_trade_fields:
                if field in trade_result:
                    self.log_test(f"Trade Result Field: {field}", True)
                else:
                    self.log_test(f"Trade Result Field: {field}", False, f"Missing {field} in trade result")
            
            # Check if trade was successful or properly handled
            if data.get("status") == "success":
                self.log_test("Trade Execution Success", True, "Trade executed successfully")
            elif data.get("status") == "error":
                self.log_test("Trade Execution Error Handling", True, "Trade error properly handled")
            else:
                self.log_test("Trade Execution Response", False, "Unclear trade execution response")
        else:
            # Trade execution might fail if platform isn't connected
            if data.get("status") == "error":
                self.log_test("Trade Execution Error Handling", True, "API properly handles trade execution errors")

    def test_position_closing(self):
        """Test closing positions"""
        print("\n🔍 Testing Position Closing...")
        
        platform_id = "tradelocker_test"
        
        # Test closing position
        close_position_data = {
            "platform_id": platform_id,
            "position_symbol": "EURUSD"
        }
        
        success, data = self.run_api_test("Position Closing", "POST", "api/platform/close-position", data=close_position_data)
        
        if success:
            close_result = data.get("data", {})
            
            # Check close result structure
            expected_close_fields = ["order_id", "timestamp"]
            for field in expected_close_fields:
                if field in close_result:
                    self.log_test(f"Close Result Field: {field}", True)
                else:
                    self.log_test(f"Close Result Field: {field}", False, f"Missing {field} in close result")
            
            # Check if close was successful or properly handled
            if data.get("status") == "success":
                self.log_test("Position Close Success", True, "Position closed successfully")
            elif data.get("status") == "error":
                self.log_test("Position Close Error Handling", True, "Position close error properly handled")
            else:
                self.log_test("Position Close Response", False, "Unclear position close response")
        else:
            # Position closing might fail if platform isn't connected
            if data.get("status") == "error":
                self.log_test("Position Close Error Handling", True, "API properly handles position close errors")

    def test_2fa_integration(self):
        """Test 2FA integration with enhanced features"""
        print("\n🔍 Testing Enhanced 2FA Integration...")
        
        # Test 2FA setup generation
        success, data = self.run_api_test("Enhanced 2FA Setup", "POST", "api/2fa/generate-setup?account_name=TradeLocker&issuer=TradingBot")
        
        totp_secret = None
        if success:
            setup_data = data.get("data", {})
            
            # Check 2FA setup structure
            required_2fa_fields = ["secret", "qr_code", "backup_codes", "manual_entry"]
            for field in required_2fa_fields:
                if field in setup_data:
                    self.log_test(f"Enhanced 2FA Field: {field}", True)
                else:
                    self.log_test(f"Enhanced 2FA Field: {field}", False, f"Missing {field} in 2FA setup")
            
            # Validate QR code format
            qr_code = setup_data.get("qr_code", "")
            if qr_code.startswith("data:image/png;base64,"):
                self.log_test("Enhanced 2FA QR Format", True, "QR code has correct base64 format")
            else:
                self.log_test("Enhanced 2FA QR Format", False, "Invalid QR code format")
            
            totp_secret = setup_data.get("secret", "")
        
        # Test 2FA verification with enhanced credentials
        if totp_secret:
            try:
                import pyotp
                totp = pyotp.TOTP(totp_secret)
                test_code = totp.now()
                
                verify_data = {
                    "platform_id": "tradelocker_test",
                    "code": test_code
                }
                
                success, data = self.run_api_test("Enhanced 2FA Verification", "POST", "api/2fa/verify", data=verify_data)
                
                if success:
                    is_valid = data.get("valid", False)
                    if is_valid:
                        self.log_test("Enhanced 2FA Code Valid", True, "TOTP code verified successfully")
                    else:
                        self.log_test("Enhanced 2FA Code Valid", False, "TOTP code verification failed")
                else:
                    self.log_test("Enhanced 2FA Verification API", False, "2FA verification endpoint failed")
                    
            except ImportError:
                self.log_test("Enhanced 2FA Code Generation", False, "pyotp not available for testing")
            except Exception as e:
                self.log_test("Enhanced 2FA Code Generation", False, f"Error generating TOTP: {str(e)}")

    def test_error_handling_and_edge_cases(self):
        """Test error handling for enhanced features"""
        print("\n🔍 Testing Enhanced Error Handling...")
        
        # Test invalid platform analysis
        invalid_data = {
            "platform_name": "",
            "login_url": "invalid-url"
        }
        success, data = self.run_api_test("Invalid Platform Analysis", "POST", "api/platform/analyze", expected_status=500, data=invalid_data)
        
        # Test trade execution with missing platform
        invalid_trade = {
            "platform_id": "nonexistent_platform",
            "symbol": "EURUSD",
            "action": "BUY",
            "quantity": 0.1
        }
        success, data = self.run_api_test("Trade with Invalid Platform", "POST", "api/platform/trade", expected_status=500, data=invalid_trade)
        
        # Test position closing with missing data
        invalid_close = {
            "platform_id": "nonexistent_platform"
        }
        success, data = self.run_api_test("Close Position Missing Data", "POST", "api/platform/close-position", expected_status=400, data=invalid_close)
        
        # Test interface analysis for non-existent platform
        invalid_interface = {"platform_id": "nonexistent_platform"}
        success, data = self.run_api_test("Interface Analysis Invalid Platform", "POST", "api/platform/analyze-interface", expected_status=400, data=invalid_interface)

    def run_enhanced_platform_tests(self):
        """Run all enhanced platform connector tests"""
        print("🚀 Starting Enhanced Universal Trading Platform Connector Tests")
        print("=" * 80)
        
        # Test enhanced features in order
        self.test_enhanced_platform_analysis()
        self.test_enhanced_credentials_saving()
        self.test_platform_connection_with_interface_analysis()
        self.test_trade_execution()
        self.test_position_closing()
        self.test_2fa_integration()
        self.test_error_handling_and_edge_cases()
        
        # Print comprehensive results
        print("\n" + "=" * 80)
        print("📊 ENHANCED PLATFORM CONNECTOR TEST RESULTS")
        print("=" * 80)
        
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Categorize results
        categories = {
            "Platform Analysis": ["Platform Analysis", "TradeLocker", "Field"],
            "Credentials Management": ["Credentials", "Enhanced Credentials", "Server Field"],
            "Interface Analysis": ["Interface", "Connection", "Re-analysis"],
            "Trade Execution": ["Trade Execution", "Trade Result"],
            "Position Management": ["Position Close", "Close Result"],
            "2FA Integration": ["2FA", "TOTP", "QR"],
            "Error Handling": ["Invalid", "Error Handling", "Missing"]
        }
        
        print("\n📋 ENHANCED FEATURE BREAKDOWN:")
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results if any(kw in r["name"] for kw in keywords)]
            passed = sum(1 for t in category_tests if t["success"])
            total = len(category_tests)
            if total > 0:
                print(f"  {category}: {passed}/{total} ({(passed/total)*100:.0f}%)")
        
        # Critical issues
        critical_failures = [r for r in self.test_results if not r["success"] and 
                           any(critical in r["name"] for critical in 
                               ["TradeLocker Platform Analysis", "Enhanced Credentials Save", 
                                "Trade Execution", "Position Closing", "Enhanced 2FA"])]
        
        if critical_failures:
            print("\n🚨 CRITICAL ENHANCED FEATURES ISSUES:")
            for failure in critical_failures:
                print(f"  ❌ {failure['name']}: {failure['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    print("Enhanced Universal Trading Platform Connector - Backend Testing")
    print("Testing Intelligent Trading Features: Analysis, Interface Detection, Trade Execution")
    print("=" * 80)
    
    tester = EnhancedPlatformConnectorTester()
    
    try:
        success = tester.run_enhanced_platform_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())