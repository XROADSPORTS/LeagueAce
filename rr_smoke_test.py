#!/usr/bin/env python3
"""
Round Robin Smoke Test - Quick sanity check for specific endpoints
Based on review request: GET /api/rr/weeks, GET /api/rr/standings, GET /api/rr/availability
"""

import requests
import sys
import json
from datetime import datetime

class RRSmokeTest:
    def __init__(self, base_url="https://doubles-master.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, params=None) -> tuple[bool, dict]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        if params:
            print(f"   Params: {params}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            else:
                print(f"❌ Unsupported method: {method}")
                return False, {}

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) > 0:
                        print(f"   Response keys: {list(response_data.keys())}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_rr_weeks_with_dummy_params(self):
        """Test GET /api/rr/weeks with dummy player/tier returns 200 structure"""
        dummy_player_id = "dummy-player-123"
        dummy_tier_id = "dummy-tier-456"
        
        success, response = self.run_test(
            "RR Weeks with Dummy Player/Tier",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": dummy_player_id, "tier_id": dummy_tier_id}
        )
        
        if success:
            # Check response structure
            if 'weeks' in response and isinstance(response['weeks'], list):
                print(f"   ✅ Response has 'weeks' field as list with {len(response['weeks'])} items")
                return True
            else:
                print(f"   ❌ Response missing 'weeks' field or not a list")
                return False
        
        return success

    def test_rr_standings_for_tier(self):
        """Test GET /api/rr/standings for tier returns 200 and rows field"""
        dummy_tier_id = "dummy-tier-789"
        
        success, response = self.run_test(
            "RR Standings for Tier",
            "GET",
            "rr/standings",
            200,
            params={"tier_id": dummy_tier_id}
        )
        
        if success:
            # Check response structure
            if 'rows' in response and isinstance(response['rows'], list):
                print(f"   ✅ Response has 'rows' field as list with {len(response['rows'])} items")
                if 'top8' in response:
                    print(f"   ✅ Response also has 'top8' field")
                return True
            else:
                print(f"   ❌ Response missing 'rows' field or not a list")
                return False
        
        return success

    def test_rr_availability_without_record(self):
        """Test GET /api/rr/availability without record returns default"""
        dummy_user_id = "nonexistent-user-999"
        
        success, response = self.run_test(
            "RR Availability Without Record",
            "GET",
            "rr/availability",
            200,
            params={"user_id": dummy_user_id}
        )
        
        if success:
            # Check default response structure
            expected_keys = ['user_id', 'windows']
            if all(key in response for key in expected_keys):
                print(f"   ✅ Response has expected keys: {expected_keys}")
                if response.get('user_id') == dummy_user_id and response.get('windows') == []:
                    print(f"   ✅ Default values correct: user_id={dummy_user_id}, windows=[]")
                    return True
                else:
                    print(f"   ❌ Default values incorrect: {response}")
                    return False
            else:
                print(f"   ❌ Response missing expected keys: {response}")
                return False
        
        return success

    def run_smoke_tests(self):
        """Run all smoke tests"""
        print("🚀 Starting Round Robin Smoke Tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   API URL: {self.api_url}")
        
        tests = [
            self.test_rr_weeks_with_dummy_params,
            self.test_rr_standings_for_tier,
            self.test_rr_availability_without_record
        ]
        
        for test in tests:
            test()
        
        print(f"\n📊 Smoke Test Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("   🎉 All smoke tests passed!")
            return True
        else:
            print(f"   ⚠️  {self.tests_run - self.tests_passed} test(s) failed")
            return False

if __name__ == "__main__":
    tester = RRSmokeTest()
    success = tester.run_smoke_tests()
    sys.exit(0 if success else 1)