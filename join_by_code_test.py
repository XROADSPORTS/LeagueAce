import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class JoinByCodeTester:
    def __init__(self, base_url="https://doubles-master.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.manager_id = None
        self.league_id = None
        self.format_tier_id = None
        self.rating_tier_id = None
        self.join_code = None
        self.player_id = None
        self.out_of_range_player_id = None

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None, params: Dict[str, Any] = None) -> tuple[bool, Dict[Any, Any]]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
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

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) > 0:
                        print(f"   Response keys: {list(response_data.keys())}")
                    elif response_data is None:
                        print(f"   Response data is None")
                    else:
                        print(f"   Response data: {response_data}")
                    return True, response_data
                except Exception as e:
                    print(f"   JSON parse error: {e}")
                    print(f"   Raw response: {response.text}")
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

    def test_step_1_create_manager_and_league_structure(self):
        """Step 1: Create manager user, league, format tier (Doubles), and rating tier with min_rating 3.5 and max_rating 4.5"""
        print("\n🎾 STEP 1: Creating Manager and League Structure")
        
        # Create League Manager user
        manager_data = {
            "provider": "Google",
            "token": "mock_google_token_manager",
            "email": f"league.manager_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "name": "League Manager",
            "provider_id": "google_manager_123",
            "role": "League Manager"
        }
        
        success, response = self.run_test(
            "Create League Manager User",
            "POST",
            "auth/social-login",
            200,
            data=manager_data
        )
        
        if not success or not response or 'id' not in response:
            print("❌ Failed to create League Manager")
            return False
        
        self.manager_id = response['id']
        print(f"   ✅ Created League Manager ID: {self.manager_id}")
        
        # Create League (Tennis)
        league_data = {
            "name": "Tennis League",
            "sport_type": "Tennis",
            "description": "Tennis league for join-by-code testing"
        }
        
        success, response = self.run_test(
            "Create Tennis League",
            "POST",
            "leagues",
            200,
            data=league_data,
            params={"created_by": self.manager_id}
        )
        
        if not success or not response or 'id' not in response:
            print("❌ Failed to create Tennis League")
            return False
        
        self.league_id = response['id']
        print(f"   ✅ Created League ID: {self.league_id}")
        
        # Create Format Tier (Doubles)
        format_data = {
            "league_id": self.league_id,
            "name": "Doubles",
            "format_type": "Doubles",
            "description": "Doubles format for join-by-code testing"
        }
        
        success, response = self.run_test(
            "Create Doubles Format Tier",
            "POST",
            "format-tiers",
            200,
            data=format_data
        )
        
        if not success or not response or 'id' not in response:
            print("❌ Failed to create Doubles Format Tier")
            return False
        
        self.format_tier_id = response['id']
        print(f"   ✅ Created Format Tier ID: {self.format_tier_id}")
        
        # Create Rating Tier with min_rating 3.5 and max_rating 4.5
        rating_data = {
            "format_tier_id": self.format_tier_id,
            "name": "4.0 Level",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 36,
            "competition_system": "Team League Format",
            "playoff_spots": 8,
            "region": "General",
            "surface": "Hard Court"
        }
        
        success, response = self.run_test(
            "Create Rating Tier (3.5-4.5)",
            "POST",
            "rating-tiers",
            200,
            data=rating_data
        )
        
        if not success or not response or 'id' not in response:
            print("❌ Failed to create Rating Tier")
            return False
        
        self.rating_tier_id = response['id']
        self.join_code = response.get('join_code')
        print(f"   ✅ Created Rating Tier ID: {self.rating_tier_id}")
        print(f"   ✅ Generated Join Code: {self.join_code}")
        
        return True

    def test_step_2_create_player_with_rating_and_sports(self):
        """Step 2: Create player user with rating 4.0 and add Tennis to sports preferences"""
        print("\n🎾 STEP 2: Creating Player with Rating and Sports Preferences")
        
        # Create Player user with rating_level 4.0 (within range)
        player_data = {
            "provider": "Google",
            "token": "mock_google_token_player",
            "email": f"tennis.player_{datetime.now().strftime('%H%M%S')}@gmail.com",
            "name": "Tennis Player",
            "provider_id": "google_player_123",
            "role": "Player",
            "rating_level": 4.0
        }
        
        success, response = self.run_test(
            "Create Player User (rating 4.0)",
            "POST",
            "auth/social-login",
            200,
            data=player_data
        )
        
        if not success or not response or 'id' not in response:
            print("❌ Failed to create Player")
            return False
        
        self.player_id = response['id']
        print(f"   ✅ Created Player ID: {self.player_id}")
        print(f"   ✅ Player Rating: {response.get('rating_level')}")
        
        # Update sports preferences to include Tennis
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
        
        if not success:
            print("❌ Failed to update sports preferences")
            return False
        
        print(f"   ✅ Updated Sports Preferences: {response.get('sports_preferences')}")
        
        return True

    def test_step_3_preview_join_code(self):
        """Step 3: Preview code using GET /api/rating-tiers/by-code/{join_code}"""
        print("\n🎾 STEP 3: Preview Join Code")
        
        if not self.join_code:
            print("❌ No join code available")
            return False
        
        success, response = self.run_test(
            "Preview Join Code",
            "GET",
            f"rating-tiers/by-code/{self.join_code}",
            200
        )
        
        if not success:
            print("❌ Failed to preview join code")
            return False
        
        print(f"   ✅ Tier Name: {response.get('name')}")
        print(f"   ✅ League Name: {response.get('league_name')}")
        print(f"   ✅ Min Rating: {response.get('min_rating')}")
        print(f"   ✅ Max Rating: {response.get('max_rating')}")
        
        # Verify expected values
        if (response.get('league_name') == 'Tennis League' and
            response.get('min_rating') == 3.5 and
            response.get('max_rating') == 4.5):
            print("   ✅ Preview data matches expected values")
            return True
        else:
            print("   ❌ Preview data doesn't match expected values")
            return False

    def test_step_4_join_tier_by_code(self):
        """Step 4: Join tier using POST /api/join-by-code/{player_id}"""
        print("\n🎾 STEP 4: Join Tier by Code")
        
        if not self.player_id or not self.join_code:
            print("❌ Missing player ID or join code")
            return False
        
        join_data = {
            "join_code": self.join_code
        }
        
        success, response = self.run_test(
            "Join Tier by Code",
            "POST",
            f"join-by-code/{self.player_id}",
            200,
            data=join_data
        )
        
        if not success:
            print("❌ Failed to join tier by code")
            return False
        
        print(f"   ✅ Membership ID: {response.get('id')}")
        print(f"   ✅ Rating Tier ID: {response.get('rating_tier_id')}")
        print(f"   ✅ User ID: {response.get('user_id')}")
        print(f"   ✅ Status: {response.get('status')}")
        
        # Verify TierMembership structure
        if (response.get('rating_tier_id') == self.rating_tier_id and
            response.get('user_id') == self.player_id and
            response.get('status') == 'Active'):
            print("   ✅ TierMembership created correctly")
            return True
        else:
            print("   ❌ TierMembership structure incorrect")
            return False

    def test_step_5_verify_dashboard_list(self):
        """Step 5: Verify dashboard list using GET /api/users/{player_id}/joined-tiers?sport_type=Tennis"""
        print("\n🎾 STEP 5: Verify Dashboard List")
        
        if not self.player_id:
            print("❌ Missing player ID")
            return False
        
        success, response = self.run_test(
            "Get Joined Tiers for Tennis",
            "GET",
            f"users/{self.player_id}/joined-tiers",
            200,
            params={"sport_type": "Tennis"}
        )
        
        if not success:
            print("❌ Failed to get joined tiers")
            return False
        
        if not isinstance(response, list):
            print("❌ Response is not a list")
            return False
        
        print(f"   ✅ Number of joined tiers: {len(response)}")
        
        if len(response) == 0:
            print("   ❌ No joined tiers found")
            return False
        
        # Check the first tier
        tier = response[0]
        print(f"   ✅ Tier Name: {tier.get('name')}")
        print(f"   ✅ League Name: {tier.get('league_name')}")
        print(f"   ✅ Sport Type: {tier.get('sport_type')}")
        print(f"   ✅ Min Rating: {tier.get('min_rating')}")
        print(f"   ✅ Max Rating: {tier.get('max_rating')}")
        print(f"   ✅ Status: {tier.get('status')}")
        
        # Verify expected values
        if (tier.get('league_name') == 'Tennis League' and
            tier.get('sport_type') == 'Tennis' and
            tier.get('status') == 'Active' and
            tier.get('id') == self.rating_tier_id):
            print("   ✅ Dashboard list contains correct tier information")
            return True
        else:
            print("   ❌ Dashboard list data doesn't match expected values")
            return False

    def test_step_6_negative_cases(self):
        """Step 6: Test negative cases - duplicate join and out-of-range rating"""
        print("\n🎾 STEP 6: Testing Negative Cases")
        
        # Test 6a: Try joining again (should return 400 Already joined)
        if self.player_id and self.join_code:
            join_data = {
                "join_code": self.join_code
            }
            
            success, response = self.run_test(
                "Try Joining Again (Should Fail)",
                "POST",
                f"join-by-code/{self.player_id}",
                400,
                data=join_data
            )
            
            if success:
                print("   ✅ Correctly returned 400 for duplicate join")
                print(f"   ✅ Error message: {response.get('detail')}")
                if "Already joined" in str(response.get('detail', '')):
                    print("   ✅ Error message indicates already joined")
                else:
                    print("   ⚠️  Error message doesn't mention 'already joined'")
            else:
                print("   ❌ Should have returned 400 for duplicate join")
                return False
        
        # Test 6b: Create player with rating 5.5 (out of range) and try to join
        out_of_range_player_data = {
            "provider": "Google",
            "token": "mock_google_token_out_of_range",
            "email": f"out.of.range.player_{datetime.now().strftime('%H%M%S')}@gmail.com",
            "name": "Out of Range Player",
            "provider_id": "google_out_of_range_123",
            "role": "Player",
            "rating_level": 5.5
        }
        
        success, response = self.run_test(
            "Create Out-of-Range Player (rating 5.5)",
            "POST",
            "auth/social-login",
            200,
            data=out_of_range_player_data
        )
        
        if not success or not response or 'id' not in response:
            print("   ❌ Failed to create out-of-range player")
            return False
        
        self.out_of_range_player_id = response['id']
        print(f"   ✅ Created Out-of-Range Player ID: {self.out_of_range_player_id}")
        print(f"   ✅ Player Rating: {response.get('rating_level')}")
        
        # Try to join with out-of-range rating (should return 400)
        if self.out_of_range_player_id and self.join_code:
            join_data = {
                "join_code": self.join_code
            }
            
            success, response = self.run_test(
                "Try Joining with Out-of-Range Rating (Should Fail)",
                "POST",
                f"join-by-code/{self.out_of_range_player_id}",
                400,
                data=join_data
            )
            
            if success:
                print("   ✅ Correctly returned 400 for out-of-range rating")
                print(f"   ✅ Error message: {response.get('detail')}")
                error_msg = str(response.get('detail', ''))
                if "outside this tier range" in error_msg and "5.5" in error_msg and "3.5-4.5" in error_msg:
                    print("   ✅ Error message correctly indicates rating range issue")
                else:
                    print("   ⚠️  Error message doesn't clearly indicate rating range issue")
            else:
                print("   ❌ Should have returned 400 for out-of-range rating")
                return False
        
        return True

    def run_all_tests(self):
        """Run all join-by-code flow tests"""
        print("🎾 STARTING JOIN-BY-CODE FLOW END-TO-END TESTING")
        print("=" * 60)
        
        # Step 1: Create manager and league structure
        if not self.test_step_1_create_manager_and_league_structure():
            print("\n❌ STEP 1 FAILED - Cannot continue")
            return False
        
        # Step 2: Create player with rating and sports preferences
        if not self.test_step_2_create_player_with_rating_and_sports():
            print("\n❌ STEP 2 FAILED - Cannot continue")
            return False
        
        # Step 3: Preview join code
        if not self.test_step_3_preview_join_code():
            print("\n❌ STEP 3 FAILED - Cannot continue")
            return False
        
        # Step 4: Join tier by code
        if not self.test_step_4_join_tier_by_code():
            print("\n❌ STEP 4 FAILED - Cannot continue")
            return False
        
        # Step 5: Verify dashboard list
        if not self.test_step_5_verify_dashboard_list():
            print("\n❌ STEP 5 FAILED - Cannot continue")
            return False
        
        # Step 6: Test negative cases
        if not self.test_step_6_negative_cases():
            print("\n❌ STEP 6 FAILED")
            return False
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 JOIN-BY-CODE FLOW TESTING COMPLETE")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! Join-by-code flow is working perfectly!")
            return True
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} tests failed. Please review the issues above.")
            return False

if __name__ == "__main__":
    tester = JoinByCodeTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)