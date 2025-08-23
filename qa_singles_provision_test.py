#!/usr/bin/env python3
"""
QA Singles Provision Test - Review Request Implementation
Provision an additional QA tier and players under the existing QA RR League.

Requirements:
1) Ensure league QA RR League exists (create if needed) under manager_id 79e8cbf0-ef27-49e9-9798-64aed67ea52a.
2) Create a Singles format tier: name='QA Round Robin Singles', format_type='Singles'.
3) Create a rating tier: name='QA 4.5 Singles', min_rating=4.5, max_rating=5.0, max_players=24, competition_system='Team League Format', playoff_spots=8, region='QA', surface='Hard'. Capture join_code and rating_tier_id.
4) Create two players at rating_level=4.5 (emails qa.singles1@leagueace.test, qa.singles2@leagueace.test), PATCH their sports to Tennis, and join them both to the new tier by code.
5) Return a compact JSON with: singles_format_tier_id, singles_rating_tier_id, join_code, player1_id, player2_id, and members_api_url.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class QASinglesProvisionTester:
    def __init__(self, base_url="https://teamace.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Required IDs from review request
        self.manager_id = "79e8cbf0-ef27-49e9-9798-64aed67ea52a"
        self.league_name = "QA RR League"
        
        # IDs to be created/captured
        self.league_id = None
        self.singles_format_tier_id = None
        self.singles_rating_tier_id = None
        self.join_code = None
        self.player1_id = None
        self.player2_id = None
        
        # Final result
        self.result_json = {}

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> tuple[bool, Dict[str, Any]]:
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

    def step_1_ensure_qa_league_exists(self):
        """Step 1: Ensure league QA RR League exists under manager_id 79e8cbf0-ef27-49e9-9798-64aed67ea52a"""
        print(f"\n🎯 STEP 1: Ensure QA RR League exists under manager {self.manager_id}")
        
        # First check if manager exists
        success, manager_response = self.run_test(
            "Verify Manager Exists",
            "GET",
            f"users/{self.manager_id}",
            200
        )
        
        if not success:
            print(f"❌ Manager {self.manager_id} not found")
            return False
        
        print(f"   ✅ Manager found: {manager_response.get('name', 'Unknown')}")
        
        # Check if QA RR League already exists for this manager
        success, leagues_response = self.run_test(
            "Get Manager's Leagues",
            "GET",
            f"users/{self.manager_id}/leagues",
            200,
            params={"sport_type": "Tennis"}
        )
        
        if success:
            existing_league = None
            for league in leagues_response:
                if league.get('name') == self.league_name:
                    existing_league = league
                    break
            
            if existing_league:
                self.league_id = existing_league['id']
                print(f"   ✅ QA RR League already exists: {self.league_id}")
                return True
        
        # Create QA RR League if it doesn't exist
        league_data = {
            "name": self.league_name,
            "sport_type": "Tennis",
            "description": "QA Round Robin League for testing"
        }
        
        success, response = self.run_test(
            "Create QA RR League",
            "POST",
            "leagues",
            200,
            data=league_data,
            params={"created_by": self.manager_id}
        )
        
        if success and 'id' in response:
            self.league_id = response['id']
            print(f"   ✅ Created QA RR League: {self.league_id}")
            return True
        
        return False

    def step_2_create_singles_format_tier(self):
        """Step 2: Create a Singles format tier: name='QA Round Robin Singles', format_type='Singles'"""
        print(f"\n🎯 STEP 2: Create Singles format tier")
        
        if not self.league_id:
            print("❌ No league ID available")
            return False
        
        format_data = {
            "league_id": self.league_id,
            "name": "QA Round Robin Singles",
            "format_type": "Singles",
            "description": "QA Singles format for round robin testing"
        }
        
        success, response = self.run_test(
            "Create QA Singles Format Tier",
            "POST",
            "format-tiers",
            200,
            data=format_data
        )
        
        if success and 'id' in response:
            self.singles_format_tier_id = response['id']
            print(f"   ✅ Created Singles Format Tier: {self.singles_format_tier_id}")
            print(f"   Format Type: {response.get('format_type')}")
            print(f"   Name: {response.get('name')}")
            return True
        
        return False

    def step_3_create_rating_tier(self):
        """Step 3: Create rating tier with specific requirements"""
        print(f"\n🎯 STEP 3: Create QA 4.5 Singles rating tier")
        
        if not self.singles_format_tier_id:
            print("❌ No singles format tier ID available")
            return False
        
        rating_data = {
            "format_tier_id": self.singles_format_tier_id,
            "name": "QA 4.5 Singles",
            "min_rating": 4.5,
            "max_rating": 5.0,
            "max_players": 24,
            "competition_system": "Team League Format",
            "playoff_spots": 8,
            "region": "QA",
            "surface": "Hard"
        }
        
        success, response = self.run_test(
            "Create QA 4.5 Singles Rating Tier",
            "POST",
            "rating-tiers",
            200,
            data=rating_data
        )
        
        if success and 'id' in response:
            self.singles_rating_tier_id = response['id']
            self.join_code = response.get('join_code')
            print(f"   ✅ Created Rating Tier: {self.singles_rating_tier_id}")
            print(f"   Join Code: {self.join_code}")
            print(f"   Min Rating: {response.get('min_rating')}")
            print(f"   Max Rating: {response.get('max_rating')}")
            print(f"   Max Players: {response.get('max_players')}")
            print(f"   Competition System: {response.get('competition_system')}")
            print(f"   Playoff Spots: {response.get('playoff_spots')}")
            print(f"   Region: {response.get('region')}")
            print(f"   Surface: {response.get('surface')}")
            return True
        
        return False

    def step_4_create_players_and_join(self):
        """Step 4: Create two players and join them to the tier"""
        print(f"\n🎯 STEP 4: Create players and join them to tier")
        
        if not self.join_code:
            print("❌ No join code available")
            return False
        
        # Create Player 1
        player1_data = {
            "provider": "Google",
            "token": "mock_token_qa_singles1",
            "email": "qa.singles1@gmail.com",
            "name": "QA Singles Player 1",
            "provider_id": "qa_singles1_provider_id",
            "role": "Player",
            "rating_level": 4.5
        }
        
        success, response = self.run_test(
            "Create QA Singles Player 1",
            "POST",
            "auth/social-login",
            200,
            data=player1_data
        )
        
        if success and 'id' in response:
            self.player1_id = response['id']
            print(f"   ✅ Created Player 1: {self.player1_id}")
            print(f"   Email: {response.get('email')}")
            print(f"   Rating: {response.get('rating_level')}")
        else:
            print("❌ Failed to create Player 1")
            return False
        
        # Create Player 2
        player2_data = {
            "provider": "Google",
            "token": "mock_token_qa_singles2",
            "email": "qa.singles2@gmail.com",
            "name": "QA Singles Player 2",
            "provider_id": "qa_singles2_provider_id",
            "role": "Player",
            "rating_level": 4.5
        }
        
        success, response = self.run_test(
            "Create QA Singles Player 2",
            "POST",
            "auth/social-login",
            200,
            data=player2_data
        )
        
        if success and 'id' in response:
            self.player2_id = response['id']
            print(f"   ✅ Created Player 2: {self.player2_id}")
            print(f"   Email: {response.get('email')}")
            print(f"   Rating: {response.get('rating_level')}")
        else:
            print("❌ Failed to create Player 2")
            return False
        
        # PATCH sports preferences for both players
        sports_data = {"sports_preferences": ["Tennis"]}
        
        success1, _ = self.run_test(
            "Update Player 1 Sports to Tennis",
            "PATCH",
            f"users/{self.player1_id}/sports",
            200,
            data=sports_data
        )
        
        success2, _ = self.run_test(
            "Update Player 2 Sports to Tennis",
            "PATCH",
            f"users/{self.player2_id}/sports",
            200,
            data=sports_data
        )
        
        if not (success1 and success2):
            print("❌ Failed to update sports preferences")
            return False
        
        print("   ✅ Updated sports preferences to Tennis for both players")
        
        # Join both players to the tier by code
        join_data = {"join_code": self.join_code}
        
        success1, response1 = self.run_test(
            "Player 1 Join by Code",
            "POST",
            f"join-by-code/{self.player1_id}",
            200,
            data=join_data
        )
        
        success2, response2 = self.run_test(
            "Player 2 Join by Code",
            "POST",
            f"join-by-code/{self.player2_id}",
            200,
            data=join_data
        )
        
        if success1 and success2:
            print("   ✅ Both players successfully joined the tier")
            print(f"   Player 1 Status: {response1.get('status', 'Active')}")
            print(f"   Player 2 Status: {response2.get('status', 'Active')}")
            return True
        else:
            print("❌ Failed to join players to tier")
            return False

    def step_5_verify_and_generate_result(self):
        """Step 5: Verify membership and generate final JSON result"""
        print(f"\n🎯 STEP 5: Verify membership and generate result JSON")
        
        if not self.singles_rating_tier_id:
            print("❌ No rating tier ID available")
            return False
        
        # Verify members are in the tier
        success, members_response = self.run_test(
            "Get Rating Tier Members",
            "GET",
            f"rating-tiers/{self.singles_rating_tier_id}/members",
            200
        )
        
        if success:
            print(f"   ✅ Members found: {len(members_response)}")
            for i, member in enumerate(members_response):
                print(f"   Member {i+1}: {member.get('name')} ({member.get('email')})")
        
        # Generate the compact JSON result as requested
        members_api_url = f"{self.api_url}/rating-tiers/{self.singles_rating_tier_id}/members"
        
        self.result_json = {
            "singles_format_tier_id": self.singles_format_tier_id,
            "singles_rating_tier_id": self.singles_rating_tier_id,
            "join_code": self.join_code,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "members_api_url": members_api_url
        }
        
        print(f"\n🎉 FINAL RESULT JSON:")
        print(json.dumps(self.result_json, indent=2))
        
        return True

    def run_full_provision_test(self):
        """Run the complete QA Singles provision workflow"""
        print("🚀 Starting QA Singles Provision Test")
        print("=" * 60)
        
        steps = [
            ("Ensure QA RR League exists", self.step_1_ensure_qa_league_exists),
            ("Create Singles format tier", self.step_2_create_singles_format_tier),
            ("Create QA 4.5 Singles rating tier", self.step_3_create_rating_tier),
            ("Create players and join tier", self.step_4_create_players_and_join),
            ("Verify and generate result", self.step_5_verify_and_generate_result)
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'='*20} {step_name} {'='*20}")
            if not step_func():
                print(f"\n❌ FAILED at step: {step_name}")
                self.print_summary()
                return False
        
        print(f"\n{'='*60}")
        print("🎉 QA SINGLES PROVISION COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}")
        
        self.print_summary()
        return True

    def print_summary(self):
        """Print test summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if self.result_json:
            print(f"\n📋 PROVISION RESULT:")
            print(json.dumps(self.result_json, indent=2))

def main():
    """Main execution function"""
    tester = QASinglesProvisionTester()
    
    try:
        success = tester.run_full_provision_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()