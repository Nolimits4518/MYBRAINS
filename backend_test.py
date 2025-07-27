#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Memecoin Signal Bot
Tests all API endpoints using the public URL from frontend configuration
"""

import requests
import sys
import json
from datetime import datetime
import time

class MemecoinBotTester:
    def __init__(self, base_url="https://1a6455d7-ff24-4dd0-be65-098d1fb4b385.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "timestamp" in data:
                    self.log_test("Health Check", True, f"Status: {data['status']}")
                    return True
                else:
                    self.log_test("Health Check", False, "Missing required fields in response")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_telegram_connection(self):
        """Test /api/test-telegram endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/test-telegram", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "connected" and "bot_username" in data:
                    self.log_test("Telegram Connection", True, f"Bot: @{data['bot_username']}")
                    return True
                else:
                    self.log_test("Telegram Connection", False, "Invalid response format")
                    return False
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "Unknown error")
                except:
                    pass
                self.log_test("Telegram Connection", False, f"HTTP {response.status_code}: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Telegram Connection", False, f"Exception: {str(e)}")
            return False

    def test_signals_endpoint(self):
        """Test /api/signals endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/signals", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "signals" in data and "count" in data:
                    signal_count = data["count"]
                    self.log_test("Fetch Signals", True, f"Retrieved {signal_count} signals")
                    return True, data["signals"]
                else:
                    self.log_test("Fetch Signals", False, "Missing required fields in response")
                    return False, []
            else:
                self.log_test("Fetch Signals", False, f"HTTP {response.status_code}")
                return False, []
                
        except Exception as e:
            self.log_test("Fetch Signals", False, f"Exception: {str(e)}")
            return False, []

    def test_send_test_signal(self, chat_id="123456789"):
        """Test /api/send-test-signal endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/api/send-test-signal",
                params={"chat_id": chat_id},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "signal_id" in data:
                    self.log_test("Send Test Signal", True, f"Signal ID: {data['signal_id']}")
                    return True, data["signal_id"]
                else:
                    self.log_test("Send Test Signal", False, "Invalid response format")
                    return False, None
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "Unknown error")
                except:
                    pass
                self.log_test("Send Test Signal", False, f"HTTP {response.status_code}: {error_detail}")
                return False, None
                
        except Exception as e:
            self.log_test("Send Test Signal", False, f"Exception: {str(e)}")
            return False, None

    def test_start_monitoring(self):
        """Test /api/start-monitoring endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/api/start-monitoring",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "monitoring_started":
                    self.log_test("Start Monitoring", True, "Monitoring started successfully")
                    return True
                else:
                    self.log_test("Start Monitoring", False, "Invalid response format")
                    return False
            else:
                self.log_test("Start Monitoring", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Start Monitoring", False, f"Exception: {str(e)}")
            return False

    def test_weekly_report(self, chat_id="123456789"):
        """Test /api/send-weekly-report endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/api/send-weekly-report",
                params={"chat_id": chat_id},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "report_sent":
                    self.log_test("Send Weekly Report", True, "Report sent successfully")
                    return True
                else:
                    self.log_test("Send Weekly Report", False, "Invalid response format")
                    return False
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "Unknown error")
                except:
                    pass
                self.log_test("Send Weekly Report", False, f"HTTP {response.status_code}: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Send Weekly Report", False, f"Exception: {str(e)}")
            return False

    def test_database_integration(self):
        """Test database integration by checking if signals persist"""
        print("\n🔍 Testing Database Integration...")
        
        # First, get initial signal count
        success, initial_signals = self.test_signals_endpoint()
        if not success:
            return False
            
        initial_count = len(initial_signals)
        print(f"Initial signal count: {initial_count}")
        
        # Send a test signal
        success, signal_id = self.test_send_test_signal()
        if not success:
            return False
            
        # Wait a moment for database write
        time.sleep(2)
        
        # Check if signal count increased
        success, new_signals = self.test_signals_endpoint()
        if not success:
            return False
            
        new_count = len(new_signals)
        print(f"New signal count: {new_count}")
        
        if new_count > initial_count:
            self.log_test("Database Persistence", True, f"Signal count increased from {initial_count} to {new_count}")
            return True
        else:
            self.log_test("Database Persistence", False, "Signal count did not increase after sending test signal")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Memecoin Signal Bot Backend Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test basic endpoints
        print("\n📡 Testing Basic API Endpoints...")
        self.test_health_endpoint()
        self.test_telegram_connection()
        self.test_signals_endpoint()
        
        # Test functionality endpoints
        print("\n🤖 Testing Bot Functionality...")
        self.test_send_test_signal()
        self.test_start_monitoring()
        self.test_weekly_report()
        
        # Test database integration
        self.test_database_integration()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        # Return success status
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = MemecoinBotTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())