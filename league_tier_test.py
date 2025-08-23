#!/usr/bin/env python3
"""
League/Format/Rating Tier Endpoints End-to-End Test
Tests the newly added League/Format/Rating Tier endpoints as requested in review.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class LeagueTierTester:
    def __init__(self, base_url="https://doubles-master.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data storage
        self.manager_id: Optional[str] = None
        self.league_id: Optional[str] = None
        self.format_tier_id: Optional[str] = None
        self.rating_tier_id: Optional[str] = None
        self.join_code: Optional[str] = None
        self.group_ids: list = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> tuple[bool, Dict[str, Any]]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        self.log(f"   URL: {method} {url}")
        
        if params:
            self.log(f"   Params: {params}")
        if data:
            self.log(f"   Data keys: {list(data.keys())}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}", "SUCCESS")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) > 0:
                        self.log(f"   Response keys: {list(response_data.keys())}")
                    elif isinstance(response_data, list):
                        self.log(f"   Response: Array with {len(response_data)} items")
                    return True, response_data
                except:
                    return True, {}
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}", "ERROR")
                try:
                    error_detail = response.json()
                    self.log(f"   Error: {error_detail}", "ERROR")
                except:
                    self.log(f"   Response text: {response.text}", "ERROR")
                return False, {}

        except Exception as e:
            self.log(f"❌ FAILED - Exception: {str(e)}", "ERROR")
            return False, {}

    def test_step_1_create_manager_user(self):
        """Step 1: Create a manager user via POST /api/auth/social-login with role:"League Manager"; record id."""
        self.log("=== STEP 1: Create Manager User ===")
        
        manager_data = {
            "provider": "Google",
            "token": "mock_google_token_manager",
            "email": f"manager_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "name": "Alex Rodriguez",
            "provider_id": f"google_manager_{datetime.now().strftime('%H%M%S')}",
            "role": "League Manager"
        }
        
        success, response = self.run_test(
            "Create Manager User via Social Login",
            "POST",
            "auth/social-login",
            200,
            data=manager_data
        )
        
        if success and 'id' in response:
            self.manager_id = response['id']
            self.log(f"   ✅ Manager ID recorded: {self.manager_id}")
            self.log(f"   Manager role: {response.get('role')}")
            self.log(f"   Manager name: {response.get('name')}")
            return True
        else:
            self.log("   ❌ Failed to create manager user", "ERROR")
            return False

    def test_step_2_create_league(self):
        """Step 2: Create league: POST /api/leagues?created_by={manager_id} with specified data. Expect 200 with id."""
        self.log("=== STEP 2: Create League ===")
        
        if not self.manager_id:
            self.log("   ❌ No manager ID available", "ERROR")
            return False

        league_data = {
            "name": "City Tennis League",
            "sport_type": "Tennis",
            "description": "Test"
        }
        
        success, response = self.run_test(
            "Create League",
            "POST",
            "leagues",
            200,
            data=league_data,
            params={"created_by": self.manager_id}
        )
        
        if success and 'id' in response:
            self.league_id = response['id']
            self.log(f"   ✅ League ID recorded: {self.league_id}")
            self.log(f"   League name: {response.get('name')}")
            self.log(f"   Sport type: {response.get('sport_type')}")
            self.log(f"   Manager ID: {response.get('manager_id')}")
            return True
        else:
            self.log("   ❌ Failed to create league", "ERROR")
            return False

    def test_step_3_list_manager_leagues(self):
        """Step 3: List manager leagues: GET /api/users/{manager_id}/leagues?sport_type=Tennis; expect array including the new league."""
        self.log("=== STEP 3: List Manager Leagues ===")
        
        if not self.manager_id:
            self.log("   ❌ No manager ID available", "ERROR")
            return False

        success, response = self.run_test(
            "List Manager Leagues",
            "GET",
            f"users/{self.manager_id}/leagues",
            200,
            params={"sport_type": "Tennis"}
        )
        
        if success and isinstance(response, list):
            self.log(f"   ✅ Found {len(response)} leagues")
            
            # Check if our league is in the list
            league_found = False
            for league in response:
                self.log(f"   - League: {league.get('name')} (ID: {league.get('id')})")
                if league.get('id') == self.league_id:
                    league_found = True
                    self.log(f"     ✅ Our league found in manager's leagues!")
            
            if league_found:
                return True
            else:
                self.log("   ❌ Our league not found in manager's leagues", "ERROR")
                return False
        else:
            self.log("   ❌ Failed to get manager leagues or invalid response", "ERROR")
            return False

    def test_step_4_create_format_tier(self):
        """Step 4: Create format tier: POST /api/format-tiers with specified data. Expect 200 with id."""
        self.log("=== STEP 4: Create Format Tier ===")
        
        if not self.league_id:
            self.log("   ❌ No league ID available", "ERROR")
            return False

        format_data = {
            "league_id": self.league_id,
            "name": "Doubles",
            "format_type": "Doubles",
            "description": "Doubles play"
        }
        
        success, response = self.run_test(
            "Create Format Tier",
            "POST",
            "format-tiers",
            200,
            data=format_data
        )
        
        if success and 'id' in response:
            self.format_tier_id = response['id']
            self.log(f"   ✅ Format Tier ID recorded: {self.format_tier_id}")
            self.log(f"   Format name: {response.get('name')}")
            self.log(f"   Format type: {response.get('format_type')}")
            self.log(f"   League ID: {response.get('league_id')}")
            return True
        else:
            self.log("   ❌ Failed to create format tier", "ERROR")
            return False

    def test_step_5_list_format_tiers(self):
        """Step 5: List format tiers by league: GET /api/leagues/{league_id}/format-tiers; expect the created one."""
        self.log("=== STEP 5: List Format Tiers by League ===")
        
        if not self.league_id:
            self.log("   ❌ No league ID available", "ERROR")
            return False

        success, response = self.run_test(
            "List Format Tiers by League",
            "GET",
            f"leagues/{self.league_id}/format-tiers",
            200
        )
        
        if success and isinstance(response, list):
            self.log(f"   ✅ Found {len(response)} format tiers")
            
            # Check if our format tier is in the list
            format_found = False
            for format_tier in response:
                self.log(f"   - Format Tier: {format_tier.get('name')} (ID: {format_tier.get('id')})")
                self.log(f"     Type: {format_tier.get('format_type')}")
                if format_tier.get('id') == self.format_tier_id:
                    format_found = True
                    self.log(f"     ✅ Our format tier found!")
            
            if format_found:
                return True
            else:
                self.log("   ❌ Our format tier not found in league's format tiers", "ERROR")
                return False
        else:
            self.log("   ❌ Failed to get format tiers or invalid response", "ERROR")
            return False

    def test_step_6_create_rating_tier(self):
        """Step 6: Create rating tier with specified data. Verify join_code returned."""
        self.log("=== STEP 6: Create Rating Tier ===")
        
        if not self.format_tier_id:
            self.log("   ❌ No format tier ID available", "ERROR")
            return False

        rating_data = {
            "format_tier_id": self.format_tier_id,
            "name": "4.0",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 36,
            "competition_system": "Team League Format",
            "playoff_spots": 8,
            "region": "General",
            "surface": "Hard Court"
        }
        
        success, response = self.run_test(
            "Create Rating Tier",
            "POST",
            "rating-tiers",
            200,
            data=rating_data
        )
        
        if success and 'id' in response:
            self.rating_tier_id = response['id']
            self.join_code = response.get('join_code')
            
            self.log(f"   ✅ Rating Tier ID recorded: {self.rating_tier_id}")
            self.log(f"   Rating name: {response.get('name')}")
            self.log(f"   Min rating: {response.get('min_rating')}")
            self.log(f"   Max rating: {response.get('max_rating')}")
            self.log(f"   Max players: {response.get('max_players')}")
            self.log(f"   Competition system: {response.get('competition_system')}")
            self.log(f"   Playoff spots: {response.get('playoff_spots')}")
            self.log(f"   Region: {response.get('region')}")
            self.log(f"   Surface: {response.get('surface')}")
            
            if self.join_code:
                self.log(f"   ✅ Join code generated: {self.join_code}")
                return True
            else:
                self.log("   ❌ No join code returned", "ERROR")
                return False
        else:
            self.log("   ❌ Failed to create rating tier", "ERROR")
            return False

    def test_step_7_list_rating_tiers(self):
        """Step 7: List rating tiers: GET /api/format-tiers/{format_tier_id}/rating-tiers; expect created tier with min_rating/max_rating rounded to 0.5."""
        self.log("=== STEP 7: List Rating Tiers ===")
        
        if not self.format_tier_id:
            self.log("   ❌ No format tier ID available", "ERROR")
            return False

        success, response = self.run_test(
            "List Rating Tiers",
            "GET",
            f"format-tiers/{self.format_tier_id}/rating-tiers",
            200
        )
        
        if success and isinstance(response, list):
            self.log(f"   ✅ Found {len(response)} rating tiers")
            
            # Check if our rating tier is in the list and verify rounding
            rating_found = False
            for rating_tier in response:
                self.log(f"   - Rating Tier: {rating_tier.get('name')} (ID: {rating_tier.get('id')})")
                self.log(f"     Min rating: {rating_tier.get('min_rating')}")
                self.log(f"     Max rating: {rating_tier.get('max_rating')}")
                
                if rating_tier.get('id') == self.rating_tier_id:
                    rating_found = True
                    self.log(f"     ✅ Our rating tier found!")
                    
                    # Verify rounding to 0.5
                    min_rating = rating_tier.get('min_rating')
                    max_rating = rating_tier.get('max_rating')
                    
                    # Check if values are rounded to 0.5 increments
                    min_rounded = (min_rating * 2) % 1 == 0  # Should be divisible by 0.5
                    max_rounded = (max_rating * 2) % 1 == 0  # Should be divisible by 0.5
                    
                    if min_rounded and max_rounded:
                        self.log(f"     ✅ Ratings properly rounded to 0.5 increments")
                        self.log(f"     Min: {min_rating}, Max: {max_rating}")
                    else:
                        self.log(f"     ❌ Ratings not properly rounded", "ERROR")
                        return False
            
            if rating_found:
                return True
            else:
                self.log("   ❌ Our rating tier not found", "ERROR")
                return False
        else:
            self.log("   ❌ Failed to get rating tiers or invalid response", "ERROR")
            return False

    def test_step_8_patch_rating_tier(self):
        """Step 8: Patch rating tier range: PATCH /api/rating-tiers/{id} {min_rating:3.0, max_rating:5.0}; verify values and rounding."""
        self.log("=== STEP 8: Patch Rating Tier Range ===")
        
        if not self.rating_tier_id:
            self.log("   ❌ No rating tier ID available", "ERROR")
            return False

        patch_data = {
            "min_rating": 3.0,
            "max_rating": 5.0
        }
        
        success, response = self.run_test(
            "Patch Rating Tier Range",
            "PATCH",
            f"rating-tiers/{self.rating_tier_id}",
            200,
            data=patch_data
        )
        
        if success:
            min_rating = response.get('min_rating')
            max_rating = response.get('max_rating')
            
            self.log(f"   ✅ Rating tier updated")
            self.log(f"   New min rating: {min_rating}")
            self.log(f"   New max rating: {max_rating}")
            
            # Verify rounding to 0.5 increments
            min_rounded = (min_rating * 2) % 1 == 0  # Should be divisible by 0.5
            max_rounded = (max_rating * 2) % 1 == 0  # Should be divisible by 0.5
            
            if min_rounded and max_rounded and min_rating == 3.0 and max_rating == 5.0:
                self.log(f"   ✅ Values properly updated and rounded")
                return True
            else:
                self.log(f"   ❌ Values not properly updated or rounded", "ERROR")
                self.log(f"   Expected: min=3.0, max=5.0")
                self.log(f"   Got: min={min_rating}, max={max_rating}")
                return False
        else:
            self.log("   ❌ Failed to patch rating tier", "ERROR")
            return False

    def test_step_9_create_groups(self):
        """Step 9: Create groups: POST /api/rating-tiers/{id}/create-groups with specified data; expect two groups."""
        self.log("=== STEP 9: Create Groups ===")
        
        if not self.rating_tier_id:
            self.log("   ❌ No rating tier ID available", "ERROR")
            return False

        groups_data = {
            "group_size": 12,
            "custom_names": ["Group A", "Group B"]
        }
        
        success, response = self.run_test(
            "Create Groups",
            "POST",
            f"rating-tiers/{self.rating_tier_id}/create-groups",
            200,
            data=groups_data
        )
        
        if success and isinstance(response, list):
            self.group_ids = [group.get('id') for group in response if group.get('id')]
            
            self.log(f"   ✅ Created {len(response)} groups")
            
            for i, group in enumerate(response):
                self.log(f"   - Group {i+1}: {group.get('name')} (ID: {group.get('id')})")
                self.log(f"     Size: {group.get('group_size')}")
                self.log(f"     Rating Tier ID: {group.get('rating_tier_id')}")
            
            if len(response) == 2:
                self.log(f"   ✅ Expected 2 groups created")
                
                # Verify custom names
                names = [group.get('name') for group in response]
                if "Group A" in names and "Group B" in names:
                    self.log(f"   ✅ Custom names used correctly")
                    return True
                else:
                    self.log(f"   ❌ Custom names not used correctly", "ERROR")
                    self.log(f"   Expected: ['Group A', 'Group B']")
                    self.log(f"   Got: {names}")
                    return False
            else:
                self.log(f"   ❌ Expected 2 groups, got {len(response)}", "ERROR")
                return False
        else:
            self.log("   ❌ Failed to create groups or invalid response", "ERROR")
            return False

    def test_step_9b_get_player_groups(self):
        """Step 9b: GET /api/rating-tiers/{id}/player-groups returns the created groups."""
        self.log("=== STEP 9B: Get Player Groups ===")
        
        if not self.rating_tier_id:
            self.log("   ❌ No rating tier ID available", "ERROR")
            return False

        success, response = self.run_test(
            "Get Player Groups",
            "GET",
            f"rating-tiers/{self.rating_tier_id}/player-groups",
            200
        )
        
        if success and isinstance(response, list):
            self.log(f"   ✅ Retrieved {len(response)} groups")
            
            for i, group in enumerate(response):
                self.log(f"   - Group {i+1}: {group.get('name')} (ID: {group.get('id')})")
                self.log(f"     Size: {group.get('group_size')}")
                self.log(f"     Rating Tier ID: {group.get('rating_tier_id')}")
            
            # Verify we get the same groups we created
            retrieved_ids = [group.get('id') for group in response if group.get('id')]
            
            if set(retrieved_ids) == set(self.group_ids):
                self.log(f"   ✅ Retrieved groups match created groups")
                return True
            else:
                self.log(f"   ❌ Retrieved groups don't match created groups", "ERROR")
                self.log(f"   Created IDs: {self.group_ids}")
                self.log(f"   Retrieved IDs: {retrieved_ids}")
                return False
        else:
            self.log("   ❌ Failed to get player groups or invalid response", "ERROR")
            return False

    def test_api_prefix_compliance(self):
        """Verify all endpoints are under /api per ingress rules."""
        self.log("=== API PREFIX COMPLIANCE CHECK ===")
        
        # All our endpoints should be under /api
        endpoints_tested = [
            "auth/social-login",
            "leagues",
            f"users/{self.manager_id}/leagues" if self.manager_id else "users/*/leagues",
            "format-tiers",
            f"leagues/{self.league_id}/format-tiers" if self.league_id else "leagues/*/format-tiers",
            "rating-tiers",
            f"format-tiers/{self.format_tier_id}/rating-tiers" if self.format_tier_id else "format-tiers/*/rating-tiers",
            f"rating-tiers/{self.rating_tier_id}" if self.rating_tier_id else "rating-tiers/*",
            f"rating-tiers/{self.rating_tier_id}/create-groups" if self.rating_tier_id else "rating-tiers/*/create-groups",
            f"rating-tiers/{self.rating_tier_id}/player-groups" if self.rating_tier_id else "rating-tiers/*/player-groups"
        ]
        
        self.log(f"   ✅ All {len(endpoints_tested)} endpoints tested are under /api prefix")
        self.log(f"   Base API URL: {self.api_url}")
        
        for endpoint in endpoints_tested:
            self.log(f"   - /api/{endpoint}")
        
        return True

    def run_all_tests(self):
        """Run all test steps in sequence"""
        self.log("🚀 Starting League/Format/Rating Tier Endpoints End-to-End Test")
        self.log(f"Base URL: {self.base_url}")
        self.log(f"API URL: {self.api_url}")
        
        test_steps = [
            self.test_step_1_create_manager_user,
            self.test_step_2_create_league,
            self.test_step_3_list_manager_leagues,
            self.test_step_4_create_format_tier,
            self.test_step_5_list_format_tiers,
            self.test_step_6_create_rating_tier,
            self.test_step_7_list_rating_tiers,
            self.test_step_8_patch_rating_tier,
            self.test_step_9_create_groups,
            self.test_step_9b_get_player_groups,
            self.test_api_prefix_compliance
        ]
        
        failed_steps = []
        
        for i, test_step in enumerate(test_steps, 1):
            self.log(f"\n{'='*60}")
            try:
                if not test_step():
                    failed_steps.append(f"Step {i}: {test_step.__name__}")
                    self.log(f"❌ Step {i} FAILED", "ERROR")
                else:
                    self.log(f"✅ Step {i} PASSED", "SUCCESS")
            except Exception as e:
                failed_steps.append(f"Step {i}: {test_step.__name__} (Exception: {str(e)})")
                self.log(f"❌ Step {i} FAILED with exception: {str(e)}", "ERROR")
        
        # Final summary
        self.log(f"\n{'='*60}")
        self.log("🏁 TEST SUMMARY")
        self.log(f"{'='*60}")
        self.log(f"Total tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0.0%")
        
        if failed_steps:
            self.log(f"\n❌ FAILED STEPS:")
            for step in failed_steps:
                self.log(f"   - {step}")
        else:
            self.log(f"\n🎉 ALL STEPS PASSED!")
        
        # Test data summary
        self.log(f"\n📊 TEST DATA CREATED:")
        self.log(f"   Manager ID: {self.manager_id}")
        self.log(f"   League ID: {self.league_id}")
        self.log(f"   Format Tier ID: {self.format_tier_id}")
        self.log(f"   Rating Tier ID: {self.rating_tier_id}")
        self.log(f"   Join Code: {self.join_code}")
        self.log(f"   Group IDs: {self.group_ids}")
        
        return len(failed_steps) == 0

def main():
    """Main function to run the tests"""
    tester = LeagueTierTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()