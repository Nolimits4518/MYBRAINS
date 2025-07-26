#!/usr/bin/env python3
"""
Final comprehensive test for Enhanced Universal Trading Platform Connector
Validates all key enhanced endpoints mentioned in the review request
"""

import requests
import json

def test_enhanced_endpoints():
    """Test all enhanced endpoints"""
    base_url = "https://e43dbe7c-0788-4a57-a112-34fe20a53a1b.preview.emergentagent.com"
    headers = {'Content-Type': 'application/json'}
    
    print("🚀 Final Enhanced Universal Trading Platform Connector Test")
    print("=" * 70)
    
    results = []
    
    # 1. Test TradeLocker platform analysis
    print("\n1️⃣ Testing TradeLocker Platform Analysis...")
    try:
        response = requests.post(f"{base_url}/api/platform/analyze", 
                               json={"platform_name": "TradeLocker", "login_url": "https://platform.tradelocker.com/login"},
                               headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            login_fields = data.get("data", {}).get("login_fields", [])
            
            if len(login_fields) >= 3:
                field_types = [field.get("type", "") for field in login_fields]
                field_names = [field.get("name", "").lower() for field in login_fields]
                
                has_email = any("email" in name or "user" in name for name in field_names)
                has_password = "password" in field_types
                has_server = any("server" in name for name in field_names) or "select" in field_types
                
                if has_email and has_password and has_server:
                    print("✅ TradeLocker Analysis: PASSED - Detected 3 fields (email, password, server)")
                    results.append(("TradeLocker Analysis", True))
                else:
                    print("❌ TradeLocker Analysis: FAILED - Missing required field types")
                    results.append(("TradeLocker Analysis", False))
            else:
                print(f"❌ TradeLocker Analysis: FAILED - Only found {len(login_fields)} fields, expected 3+")
                results.append(("TradeLocker Analysis", False))
        else:
            print(f"❌ TradeLocker Analysis: FAILED - Status {response.status_code}")
            results.append(("TradeLocker Analysis", False))
    except Exception as e:
        print(f"❌ TradeLocker Analysis: FAILED - Exception: {e}")
        results.append(("TradeLocker Analysis", False))
    
    # 2. Test saving credentials with server field
    print("\n2️⃣ Testing Enhanced Credentials Saving...")
    try:
        credentials_data = {
            "platform_id": "tradelocker_final_test",
            "username": "test@example.com",
            "password": "testpass123",
            "server": "demo",
            "additional_fields": {"account_type": "demo"},
            "enable_2fa": False
        }
        
        response = requests.post(f"{base_url}/api/platform/save-credentials", 
                               json=credentials_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            platform_id = data.get("platform_id", "")
            if platform_id:
                print("✅ Enhanced Credentials Save: PASSED - Platform saved with server field")
                results.append(("Enhanced Credentials Save", True))
                saved_platform_id = platform_id
            else:
                print("❌ Enhanced Credentials Save: FAILED - No platform_id returned")
                results.append(("Enhanced Credentials Save", False))
                saved_platform_id = None
        else:
            print(f"❌ Enhanced Credentials Save: FAILED - Status {response.status_code}")
            results.append(("Enhanced Credentials Save", False))
            saved_platform_id = None
    except Exception as e:
        print(f"❌ Enhanced Credentials Save: FAILED - Exception: {e}")
        results.append(("Enhanced Credentials Save", False))
        saved_platform_id = None
    
    # 3. Test platform connection
    if saved_platform_id:
        print(f"\n3️⃣ Testing Platform Connection...")
        try:
            response = requests.post(f"{base_url}/api/platform/connect/{saved_platform_id}", 
                                   headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "connected" in data:
                    print("✅ Platform Connection: PASSED - API responds with connection status")
                    results.append(("Platform Connection", True))
                else:
                    print("❌ Platform Connection: FAILED - Missing 'connected' field")
                    results.append(("Platform Connection", False))
            else:
                print(f"❌ Platform Connection: FAILED - Status {response.status_code}")
                results.append(("Platform Connection", False))
        except Exception as e:
            print(f"❌ Platform Connection: FAILED - Exception: {e}")
            results.append(("Platform Connection", False))
    
    # 4. Test position closing
    print(f"\n4️⃣ Testing Position Closing...")
    try:
        close_data = {
            "platform_id": saved_platform_id or "test_platform",
            "position_symbol": "EURUSD"
        }
        
        response = requests.post(f"{base_url}/api/platform/close-position", 
                               json=close_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            close_result = data.get("data", {})
            if "order_id" in close_result and "timestamp" in close_result:
                print("✅ Position Closing: PASSED - API returns proper close result structure")
                results.append(("Position Closing", True))
            else:
                print("❌ Position Closing: FAILED - Missing required fields in close result")
                results.append(("Position Closing", False))
        else:
            print(f"❌ Position Closing: FAILED - Status {response.status_code}")
            results.append(("Position Closing", False))
    except Exception as e:
        print(f"❌ Position Closing: FAILED - Exception: {e}")
        results.append(("Position Closing", False))
    
    # 5. Test 2FA setup generation
    print(f"\n5️⃣ Testing Enhanced 2FA Setup...")
    try:
        response = requests.post(f"{base_url}/api/2fa/generate-setup?account_name=TradeLocker&issuer=TradingBot", 
                               headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            setup_data = data.get("data", {})
            required_fields = ["secret", "qr_code", "backup_codes", "manual_entry"]
            
            if all(field in setup_data for field in required_fields):
                qr_code = setup_data.get("qr_code", "")
                if qr_code.startswith("data:image/png;base64,"):
                    print("✅ Enhanced 2FA Setup: PASSED - Complete 2FA setup with QR code")
                    results.append(("Enhanced 2FA Setup", True))
                else:
                    print("❌ Enhanced 2FA Setup: FAILED - Invalid QR code format")
                    results.append(("Enhanced 2FA Setup", False))
            else:
                print("❌ Enhanced 2FA Setup: FAILED - Missing required 2FA fields")
                results.append(("Enhanced 2FA Setup", False))
        else:
            print(f"❌ Enhanced 2FA Setup: FAILED - Status {response.status_code}")
            results.append(("Enhanced 2FA Setup", False))
    except Exception as e:
        print(f"❌ Enhanced 2FA Setup: FAILED - Exception: {e}")
        results.append(("Enhanced 2FA Setup", False))
    
    # 6. Test platform list
    print(f"\n6️⃣ Testing Platform List...")
    try:
        response = requests.get(f"{base_url}/api/platform/list", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            platforms = data.get("data", [])
            count = data.get("count", 0)
            
            if count > 0 and isinstance(platforms, list):
                print(f"✅ Platform List: PASSED - Found {count} platforms")
                results.append(("Platform List", True))
            else:
                print("❌ Platform List: FAILED - No platforms or invalid structure")
                results.append(("Platform List", False))
        else:
            print(f"❌ Platform List: FAILED - Status {response.status_code}")
            results.append(("Platform List", False))
    except Exception as e:
        print(f"❌ Platform List: FAILED - Exception: {e}")
        results.append(("Platform List", False))
    
    # Print final results
    print("\n" + "=" * 70)
    print("📊 FINAL ENHANCED PLATFORM CONNECTOR TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"✅ Tests Passed: {passed}")
    print(f"❌ Tests Failed: {total - passed}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    print("\n📋 DETAILED RESULTS:")
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    # Critical assessment
    critical_tests = ["TradeLocker Analysis", "Enhanced Credentials Save", "Platform Connection", "Position Closing"]
    critical_passed = sum(1 for test_name, success in results if test_name in critical_tests and success)
    critical_total = sum(1 for test_name, _ in results if test_name in critical_tests)
    
    print(f"\n🎯 CRITICAL FEATURES: {critical_passed}/{critical_total} ({(critical_passed/critical_total)*100:.0f}%)")
    
    if critical_passed == critical_total:
        print("✅ All critical enhanced features are working correctly!")
    else:
        print("⚠️  Some critical enhanced features have issues")
    
    return passed == total

if __name__ == "__main__":
    test_enhanced_endpoints()