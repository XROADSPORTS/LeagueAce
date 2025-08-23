#!/usr/bin/env python3
"""
Focused test for the review request:
Validate that GET /api/rating-tiers/{rating_tier_id}/members returns the joined player 
immediately after POST /api/join-by-code/{user_id} within the same session.

Steps: create league/format/rating tier → create player → join by code → call members endpoint. 
Confirm non-empty array. Also check that status filter is 'Active' and ensure membership 
gets status Active when created. Report any latency or caching concerns.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class JoinByCodeMembersTest:
    def __init__(self, base_url="https://leagueace-rr.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data storage
        self.league_manager_id = None
        self.player_id = None
        self.league_id = None
        self.format_tier_id = None
        self.rating_tier_id = None
        self.join_code = None
        
    def log(self, message: str):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
        
    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Dict[Any, Any] = None, params: Dict[str, Any] = None) -> tuple[bool, Dict[Any, Any]]:
        """Run a single API test with timing"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        start_time = time.time()
        self.log(f"🔍 Testing {name}...")
        self.log(f"   URL: {method} {url}")
        
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

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ Passed - Status: {response.status_code} - Response Time: {response_time:.2f}ms")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) > 0:
                        self.log(f"   Response keys: {list(response_data.keys())}")
                    elif isinstance(response_data, list):
                        self.log(f"   Response array length: {len(response_data)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                self.log(f"❌ Failed - Expected {expected_status}, got {response.status_code} - Response Time: {response_time:.2f}ms")
                try:
                    error_detail = response.json()
                    self.log(f"   Error: {error_detail}")
                except:
                    self.log(f"   Response text: {response.text}")
                return False, {}

        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            self.log(f"❌ Failed - Error: {str(e)} - Response Time: {response_time:.2f}ms")
            return False, {}

    def setup_test_environment(self) -> bool:
        """Create the complete test environment: league → format tier → rating tier"""
        self.log("🏗️  Setting up test environment...")
        
        # Step 1: Create League Manager
        manager_data = {
            "provider": "Google",
            "token": "test_token_manager",
            "email": f"manager_{datetime.now().strftime('%H%M%S%f')}@testleague.com",
            "name": "Test League Manager",
            "provider_id": f"google_manager_{datetime.now().strftime('%H%M%S%f')}",
            "role": "League Manager",
            "rating_level": 4.5
        }
        
        success, response = self.run_test(
            "Create League Manager via Social Login",
            "POST",
            "auth/social-login",
            200,
            data=manager_data
        )
        
        if not success or 'id' not in response:
            self.log("❌ Failed to create League Manager")
            return False
            
        self.league_manager_id = response['id']
        self.log(f"   ✅ Created League Manager ID: {self.league_manager_id}")
        
        # Step 2: Create League
        league_data = {
            "name": "Test Tennis League",
            "sport_type": "Tennis",
            "description": "Test league for join-by-code members testing"
        }
        
        success, response = self.run_test(
            "Create League",
            "POST",
            "leagues",
            200,
            data=league_data,
            params={"created_by": self.league_manager_id}
        )
        
        if not success or 'id' not in response:
            self.log("❌ Failed to create League")
            return False
            
        self.league_id = response['id']
        self.log(f"   ✅ Created League ID: {self.league_id}")
        
        # Step 3: Create Format Tier (Singles)
        format_data = {
            "league_id": self.league_id,
            "name": "Singles Competition",
            "format_type": "Singles",
            "description": "Singles format for testing"
        }
        
        success, response = self.run_test(
            "Create Format Tier",
            "POST",
            "format-tiers",
            200,
            data=format_data
        )
        
        if not success or 'id' not in response:
            self.log("❌ Failed to create Format Tier")
            return False
            
        self.format_tier_id = response['id']
        self.log(f"   ✅ Created Format Tier ID: {self.format_tier_id}")
        
        # Step 4: Create Rating Tier with join code
        rating_data = {
            "format_tier_id": self.format_tier_id,
            "name": "4.0 Level",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 36,
            "competition_system": "Team League Format",
            "playoff_spots": 8,
            "region": "Test Region",
            "surface": "Hard Court"
        }
        
        success, response = self.run_test(
            "Create Rating Tier with Join Code",
            "POST",
            "rating-tiers",
            200,
            data=rating_data
        )
        
        if not success or 'id' not in response:
            self.log("❌ Failed to create Rating Tier")
            return False
            
        self.rating_tier_id = response['id']
        self.join_code = response.get('join_code')
        self.log(f"   ✅ Created Rating Tier ID: {self.rating_tier_id}")
        self.log(f"   ✅ Generated Join Code: {self.join_code}")
        
        if not self.join_code:
            self.log("❌ No join code generated")
            return False
            
        self.log("🏗️  Test environment setup complete!")
        return True
        
    def create_test_player(self) -> bool:
        """Create a test player with appropriate rating"""
        self.log("👤 Creating test player...")
        
        player_data = {
            "provider": "Google",
            "token": "test_token_player",
            "email": f"player_{datetime.now().strftime('%H%M%S%f')}@testplayer.com",
            "name": "Test Player",
            "provider_id": f"google_player_{datetime.now().strftime('%H%M%S%f')}",
            "role": "Player",
            "rating_level": 4.0  # Within the 3.5-4.5 range
        }
        
        success, response = self.run_test(
            "Create Player via Social Login",
            "POST",
            "auth/social-login",
            200,
            data=player_data
        )
        
        if not success or 'id' not in response:
            self.log("❌ Failed to create Player")
            return False
            
        self.player_id = response['id']
        self.log(f"   ✅ Created Player ID: {self.player_id}")
        self.log(f"   ✅ Player Rating: {response.get('rating_level', 'Unknown')}")
        
        # Update player sports preferences to include Tennis
        sports_data = {
            "sports_preferences": ["Tennis"]
        }
        
        success, response = self.run_test(
            "Update Player Sports Preferences",
            "PATCH",
            f"users/{self.player_id}/sports",
            200,
            data=sports_data
        )
        
        if success:
            self.log("   ✅ Updated player sports preferences to Tennis")
        else:
            self.log("   ⚠️  Failed to update sports preferences (may not be critical)")
            
        return True
        
    def test_members_endpoint_before_join(self) -> bool:
        """Test that members endpoint returns empty array before anyone joins"""
        self.log("📋 Testing members endpoint before any joins...")
        
        success, response = self.run_test(
            "Get Rating Tier Members (Before Join)",
            "GET",
            f"rating-tiers/{self.rating_tier_id}/members",
            200
        )
        
        if not success:
            return False
            
        if isinstance(response, list) and len(response) == 0:
            self.log("   ✅ Members endpoint returns empty array before joins")
            return True
        else:
            self.log(f"   ❌ Expected empty array, got: {response}")
            return False
            
    def test_join_by_code_and_immediate_members_check(self) -> bool:
        """Core test: Join by code and immediately check members endpoint"""
        self.log("🎯 CORE TEST: Join by code and immediate members check...")
        
        # Record time before join
        join_start_time = time.time()
        
        # Step 1: Join by code
        join_data = {
            "join_code": self.join_code
        }
        
        success, join_response = self.run_test(
            "Join Rating Tier by Code",
            "POST",
            f"join-by-code/{self.player_id}",
            200,
            data=join_data
        )
        
        join_end_time = time.time()
        join_duration = (join_end_time - join_start_time) * 1000
        
        if not success:
            self.log("❌ Failed to join by code")
            return False
            
        self.log(f"   ✅ Successfully joined by code - Duration: {join_duration:.2f}ms")
        self.log(f"   ✅ Join Response: {join_response}")
        
        # Verify join response contains expected fields
        if 'rating_tier_id' not in join_response:
            self.log("   ❌ Join response missing rating_tier_id")
            return False
            
        if join_response.get('rating_tier_id') != self.rating_tier_id:
            self.log(f"   ❌ Join response rating_tier_id mismatch: expected {self.rating_tier_id}, got {join_response.get('rating_tier_id')}")
            return False
            
        if join_response.get('status') != 'Active':
            self.log(f"   ❌ Join response status not Active: {join_response.get('status')}")
            return False
            
        self.log("   ✅ Join response contains correct rating_tier_id and Active status")
        
        # Step 2: IMMEDIATELY check members endpoint (no delay)
        members_start_time = time.time()
        
        success, members_response = self.run_test(
            "Get Rating Tier Members (Immediately After Join)",
            "GET",
            f"rating-tiers/{self.rating_tier_id}/members",
            200
        )
        
        members_end_time = time.time()
        members_duration = (members_end_time - members_start_time) * 1000
        total_duration = (members_end_time - join_start_time) * 1000
        
        if not success:
            self.log("❌ Failed to get members immediately after join")
            return False
            
        self.log(f"   ✅ Members endpoint responded - Duration: {members_duration:.2f}ms")
        self.log(f"   ✅ Total join-to-members duration: {total_duration:.2f}ms")
        
        # Step 3: Validate members response
        if not isinstance(members_response, list):
            self.log(f"   ❌ Members response is not an array: {type(members_response)}")
            return False
            
        if len(members_response) == 0:
            self.log("   ❌ Members array is empty - player not found immediately after join!")
            return False
            
        if len(members_response) != 1:
            self.log(f"   ⚠️  Expected 1 member, found {len(members_response)} members")
            
        # Step 4: Validate the member data
        member = members_response[0]
        self.log(f"   📋 Member data: {member}")
        
        # Check required fields
        required_fields = ['user_id', 'name', 'email', 'rating_level', 'joined_at']
        missing_fields = [field for field in required_fields if field not in member]
        
        if missing_fields:
            self.log(f"   ❌ Missing required fields in member data: {missing_fields}")
            return False
            
        # Validate member data matches our player
        if member.get('user_id') != self.player_id:
            self.log(f"   ❌ Member user_id mismatch: expected {self.player_id}, got {member.get('user_id')}")
            return False
            
        if member.get('name') != 'Test Player':
            self.log(f"   ❌ Member name mismatch: expected 'Test Player', got {member.get('name')}")
            return False
            
        if member.get('rating_level') != 4.0:
            self.log(f"   ❌ Member rating_level mismatch: expected 4.0, got {member.get('rating_level')}")
            return False
            
        # Check that joined_at is recent (within last 10 seconds)
        joined_at = member.get('joined_at')
        if joined_at:
            try:
                # Parse the joined_at timestamp
                if isinstance(joined_at, str):
                    # Handle ISO format
                    joined_time = datetime.fromisoformat(joined_at.replace('Z', '+00:00'))
                    time_diff = (datetime.now(joined_time.tzinfo) - joined_time).total_seconds()
                    if time_diff > 10:
                        self.log(f"   ⚠️  joined_at timestamp seems old: {time_diff:.2f} seconds ago")
                    else:
                        self.log(f"   ✅ joined_at timestamp is recent: {time_diff:.2f} seconds ago")
            except Exception as e:
                self.log(f"   ⚠️  Could not parse joined_at timestamp: {e}")
        
        self.log("   ✅ All member data validation passed!")
        
        # Step 5: Performance analysis
        if total_duration > 1000:  # More than 1 second
            self.log(f"   ⚠️  LATENCY CONCERN: Total duration {total_duration:.2f}ms exceeds 1 second")
        elif total_duration > 500:  # More than 500ms
            self.log(f"   ⚠️  PERFORMANCE NOTE: Total duration {total_duration:.2f}ms is above 500ms")
        else:
            self.log(f"   ✅ PERFORMANCE GOOD: Total duration {total_duration:.2f}ms is acceptable")
            
        return True
        
    def test_duplicate_join_prevention(self) -> bool:
        """Test that duplicate join attempts are properly handled"""
        self.log("🔒 Testing duplicate join prevention...")
        
        join_data = {
            "join_code": self.join_code
        }
        
        success, response = self.run_test(
            "Attempt Duplicate Join (Should Fail)",
            "POST",
            f"join-by-code/{self.player_id}",
            400,  # Should return 400 for duplicate
            data=join_data
        )
        
        if success:
            self.log("   ✅ Duplicate join correctly prevented with 400 status")
            self.log(f"   ✅ Error message: {response.get('detail', 'No detail provided')}")
            return True
        else:
            self.log("   ❌ Duplicate join was not prevented properly")
            return False
            
    def test_members_endpoint_consistency(self) -> bool:
        """Test that members endpoint returns consistent results on multiple calls"""
        self.log("🔄 Testing members endpoint consistency...")
        
        results = []
        for i in range(3):
            success, response = self.run_test(
                f"Get Members (Consistency Check {i+1})",
                "GET",
                f"rating-tiers/{self.rating_tier_id}/members",
                200
            )
            
            if not success:
                self.log(f"   ❌ Consistency check {i+1} failed")
                return False
                
            results.append(response)
            
        # Check that all results are identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 2):
            if result != first_result:
                self.log(f"   ❌ Inconsistent results between call 1 and call {i}")
                self.log(f"   First: {first_result}")
                self.log(f"   Call {i}: {result}")
                return False
                
        self.log("   ✅ All consistency checks returned identical results")
        return True
        
    def test_rating_tier_current_players_count(self) -> bool:
        """Test that rating tier current_players count is updated after join"""
        self.log("📊 Testing rating tier current_players count...")
        
        success, response = self.run_test(
            "Get Format Tier Rating Tiers (Check Count)",
            "GET",
            f"format-tiers/{self.format_tier_id}/rating-tiers",
            200
        )
        
        if not success:
            return False
            
        # Find our rating tier in the response
        our_tier = None
        for tier in response:
            if tier.get('id') == self.rating_tier_id:
                our_tier = tier
                break
                
        if not our_tier:
            self.log("   ❌ Could not find our rating tier in the response")
            return False
            
        current_players = our_tier.get('current_players', 0)
        if current_players == 1:
            self.log(f"   ✅ current_players count correctly updated to {current_players}")
            return True
        else:
            self.log(f"   ❌ current_players count incorrect: expected 1, got {current_players}")
            return False
            
    def run_all_tests(self) -> bool:
        """Run the complete test suite"""
        self.log("🚀 Starting Join-by-Code Members Test Suite")
        self.log("=" * 80)
        
        start_time = time.time()
        
        # Setup phase
        if not self.setup_test_environment():
            self.log("❌ Test environment setup failed")
            return False
            
        if not self.create_test_player():
            self.log("❌ Test player creation failed")
            return False
            
        # Pre-join validation
        if not self.test_members_endpoint_before_join():
            self.log("❌ Pre-join members endpoint test failed")
            return False
            
        # Core test
        if not self.test_join_by_code_and_immediate_members_check():
            self.log("❌ CORE TEST FAILED: Join-by-code immediate members check")
            return False
            
        # Additional validation tests
        if not self.test_duplicate_join_prevention():
            self.log("❌ Duplicate join prevention test failed")
            return False
            
        if not self.test_members_endpoint_consistency():
            self.log("❌ Members endpoint consistency test failed")
            return False
            
        if not self.test_rating_tier_current_players_count():
            self.log("❌ Rating tier current players count test failed")
            return False
            
        end_time = time.time()
        total_duration = (end_time - start_time) * 1000
        
        self.log("=" * 80)
        self.log("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        self.log(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        self.log(f"⏱️  Total Test Duration: {total_duration:.2f}ms")
        self.log("=" * 80)
        
        return True

def main():
    """Main test execution"""
    tester = JoinByCodeMembersTest()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n✅ JOIN-BY-CODE MEMBERS TEST SUITE PASSED")
            return 0
        else:
            print("\n❌ JOIN-BY-CODE MEMBERS TEST SUITE FAILED")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())