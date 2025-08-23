#!/usr/bin/env python3
"""
Manager Player List Testing - Specific Review Request
Tests the specific paths for Manager Player List functionality with join code J4YQDP
"""

import requests
import json
import sys
from datetime import datetime

class ManagerPlayerListTester:
    def __init__(self, base_url="https://teamace.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.format_tier_id = None
        self.rating_tier_id = None
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        
        if details:
            print(f"   {details}")
        print()
    
    def make_request(self, method: str, endpoint: str, data=None, params=None):
        """Make HTTP request and return response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            return response
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None
    
    def test_rating_tier_by_code_j4yqdp(self):
        """Test 1: GET /api/rating-tiers/by-code/J4YQDP"""
        print("🔍 Testing GET /api/rating-tiers/by-code/J4YQDP")
        
        response = self.make_request('GET', 'rating-tiers/by-code/J4YQDP')
        
        if response is None:
            self.log_test("GET /api/rating-tiers/by-code/J4YQDP", False, "Request failed")
            return False
        
        if response.status_code == 404:
            self.log_test("GET /api/rating-tiers/by-code/J4YQDP", True, 
                         f"Status: 404 - Join code J4YQDP not found (as reported)")
            print(f"   Response: {response.text}")
            return True
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.format_tier_id = data.get('format_tier_id')
                self.rating_tier_id = data.get('id')
                
                details = f"Status: 200 - Found tier\n"
                details += f"   Rating Tier ID: {self.rating_tier_id}\n"
                details += f"   Format Tier ID: {self.format_tier_id}\n"
                details += f"   League Name: {data.get('league_name')}\n"
                details += f"   Tier Name: {data.get('name')}\n"
                details += f"   Min Rating: {data.get('min_rating')}\n"
                details += f"   Max Rating: {data.get('max_rating')}\n"
                details += f"   Max Players: {data.get('max_players')}\n"
                details += f"   Competition System: {data.get('competition_system')}"
                
                self.log_test("GET /api/rating-tiers/by-code/J4YQDP", True, details)
                
                print("   EXACT RESPONSE:")
                print(f"   {json.dumps(data, indent=2)}")
                return True
                
            except Exception as e:
                self.log_test("GET /api/rating-tiers/by-code/J4YQDP", False, 
                             f"Status: 200 but failed to parse JSON: {str(e)}")
                return False
        else:
            self.log_test("GET /api/rating-tiers/by-code/J4YQDP", False, 
                         f"Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def test_rating_tier_members(self):
        """Test 2: GET /api/rating-tiers/{id}/members"""
        if not self.rating_tier_id:
            self.log_test("GET /api/rating-tiers/{id}/members", False, 
                         "Skipped - No rating_tier_id from previous test")
            return False
        
        print(f"🔍 Testing GET /api/rating-tiers/{self.rating_tier_id}/members")
        
        response = self.make_request('GET', f'rating-tiers/{self.rating_tier_id}/members')
        
        if response is None:
            self.log_test("GET /api/rating-tiers/{id}/members", False, "Request failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                details = f"Status: 200 - Members retrieved\n"
                details += f"   Total Members: {len(data)}\n"
                
                if len(data) > 0:
                    details += f"   Member Names:\n"
                    for i, member in enumerate(data):
                        name = member.get('name', 'Unknown')
                        email = member.get('email', 'No email')
                        rating = member.get('rating_level', 'No rating')
                        lan = member.get('lan', 'No LAN')
                        joined_at = member.get('joined_at', 'Unknown')
                        details += f"     {i+1}. {name} (Email: {email}, Rating: {rating}, LAN: {lan}, Joined: {joined_at})\n"
                else:
                    details += "   No members found in this tier"
                
                self.log_test("GET /api/rating-tiers/{id}/members", True, details)
                
                print("   EXACT RESPONSE:")
                print(f"   {json.dumps(data, indent=2)}")
                return True
                
            except Exception as e:
                self.log_test("GET /api/rating-tiers/{id}/members", False, 
                             f"Status: 200 but failed to parse JSON: {str(e)}")
                return False
        else:
            self.log_test("GET /api/rating-tiers/{id}/members", False, 
                         f"Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def test_format_tier_rating_tiers(self):
        """Test 3: GET /api/format-tiers/{format_tier_id}/rating-tiers"""
        if not self.format_tier_id:
            self.log_test("GET /api/format-tiers/{format_tier_id}/rating-tiers", False, 
                         "Skipped - No format_tier_id from previous test")
            return False
        
        print(f"🔍 Testing GET /api/format-tiers/{self.format_tier_id}/rating-tiers")
        
        response = self.make_request('GET', f'format-tiers/{self.format_tier_id}/rating-tiers')
        
        if response is None:
            self.log_test("GET /api/format-tiers/{format_tier_id}/rating-tiers", False, "Request failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                details = f"Status: 200 - Rating tiers retrieved\n"
                details += f"   Total Rating Tiers: {len(data)}\n"
                
                # Look for our specific tier
                target_tier = None
                for tier in data:
                    if tier.get('id') == self.rating_tier_id:
                        target_tier = tier
                        break
                
                if target_tier:
                    current_players = target_tier.get('current_players', 0)
                    details += f"   Target Tier Found:\n"
                    details += f"     - ID: {target_tier.get('id')}\n"
                    details += f"     - Name: {target_tier.get('name')}\n"
                    details += f"     - Current Players: {current_players}\n"
                    details += f"     - Max Players: {target_tier.get('max_players')}\n"
                    details += f"     - Join Code: {target_tier.get('join_code')}\n"
                    details += f"     - Competition System: {target_tier.get('competition_system')}\n"
                    
                    if current_players >= 1:
                        details += f"   ✅ VERIFIED: Tier has current_players >= 1 ({current_players})"
                    else:
                        details += f"   ❌ ISSUE: Tier has current_players < 1 ({current_players})"
                else:
                    details += f"   ❌ Target tier with ID {self.rating_tier_id} not found in format tier"
                
                # List all tiers for reference
                details += f"\n   All Rating Tiers in Format:\n"
                for i, tier in enumerate(data):
                    details += f"     {i+1}. {tier.get('name')} (ID: {tier.get('id')}, Players: {tier.get('current_players', 0)})\n"
                
                self.log_test("GET /api/format-tiers/{format_tier_id}/rating-tiers", True, details)
                
                print("   EXACT RESPONSE:")
                print(f"   {json.dumps(data, indent=2)}")
                return True
                
            except Exception as e:
                self.log_test("GET /api/format-tiers/{format_tier_id}/rating-tiers", False, 
                             f"Status: 200 but failed to parse JSON: {str(e)}")
                return False
        else:
            self.log_test("GET /api/format-tiers/{format_tier_id}/rating-tiers", False, 
                         f"Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 80)
        print("MANAGER PLAYER LIST TESTING - SPECIFIC REVIEW REQUEST")
        print("Testing paths for join code J4YQDP")
        print("=" * 80)
        print()
        
        # Test 1: Get tier by code J4YQDP
        test1_success = self.test_rating_tier_by_code_j4yqdp()
        
        # Test 2: Get members (only if Test 1 found the tier)
        test2_success = self.test_rating_tier_members()
        
        # Test 3: Verify tier in format tiers list (only if Test 1 found the tier)
        test3_success = self.test_format_tier_rating_tiers()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        print()
        
        if test1_success and self.rating_tier_id:
            print("✅ WORKFLOW VALIDATION:")
            print(f"   1. Join code J4YQDP {'found' if test1_success else 'not found'}")
            print(f"   2. Rating tier ID captured: {self.rating_tier_id}")
            print(f"   3. Format tier ID captured: {self.format_tier_id}")
            print(f"   4. Members endpoint {'accessible' if test2_success else 'not accessible'}")
            print(f"   5. Format tiers list {'accessible' if test3_success else 'not accessible'}")
        else:
            print("❌ WORKFLOW ISSUE:")
            print("   Join code J4YQDP was not found (404 response)")
            print("   This prevents testing of the member list functionality")
        
        print()
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ManagerPlayerListTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()