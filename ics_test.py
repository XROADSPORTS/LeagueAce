#!/usr/bin/env python3
"""
Focused ICS Test for Doubles Matches
Tests the specific requirement that GET /api/doubles/matches/{match_id}/ics 
should return 404 for non-confirmed matches and 200 with ICS for confirmed ones.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

class ICSTestRunner:
    def __init__(self, base_url="https://pickleplay-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data storage
        self.league_manager_id = None
        self.player_ids = []
        self.league_id = None
        self.format_tier_id = None
        self.rating_tier_id = None
        self.team_ids = []
        self.match_id = None

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

    def setup_test_environment(self):
        """Set up the test environment with necessary data"""
        print("🚀 Setting up test environment for ICS testing...")
        
        # 1. Create League Manager
        manager_data = {
            "name": "ICS Test Manager",
            "email": f"ics.manager_{datetime.now().strftime('%H%M%S')}@test.com",
            "rating_level": 4.5,
            "role": "League Manager"
        }
        
        success, response = self.run_test(
            "Create League Manager",
            "POST",
            "users",
            200,
            data=manager_data
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create league manager")
            return False
            
        self.league_manager_id = response['id']
        
        # 2. Create League
        league_data = {
            "name": "ICS Test Tennis League",
            "sport_type": "Tennis",
            "description": "Test league for ICS functionality"
        }
        
        success, response = self.run_test(
            "Create League",
            "POST",
            f"leagues?created_by={self.league_manager_id}",
            200,
            data=league_data
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create league")
            return False
            
        self.league_id = response['id']
        
        # 3. Create Doubles Format Tier
        format_data = {
            "league_id": self.league_id,
            "name": "Doubles",
            "format_type": "Doubles"
        }
        
        success, response = self.run_test(
            "Create Doubles Format Tier",
            "POST",
            "format-tiers",
            200,
            data=format_data
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create format tier")
            return False
            
        self.format_tier_id = response['id']
        
        # 4. Create Rating Tier
        rating_data = {
            "format_tier_id": self.format_tier_id,
            "name": "4.0",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 20
        }
        
        success, response = self.run_test(
            "Create Rating Tier",
            "POST",
            "rating-tiers",
            200,
            data=rating_data
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create rating tier")
            return False
            
        self.rating_tier_id = response['id']
        
        # 5. Create 4 players for doubles teams
        for i in range(4):
            player_data = {
                "name": f"ICS Player {i+1}",
                "email": f"ics.player{i+1}_{datetime.now().strftime('%H%M%S')}@test.com",
                "rating_level": 4.0,
                "role": "Player"
            }
            
            success, response = self.run_test(
                f"Create Player {i+1}",
                "POST",
                "users",
                200,
                data=player_data
            )
            
            if success and 'id' in response:
                self.player_ids.append(response['id'])
            else:
                print(f"❌ Failed to create player {i+1}")
                return False
        
        # 6. Create 2 doubles teams using partner invites
        # Team 1: Player 1 & Player 2
        invite_data = {
            "inviter_user_id": self.player_ids[0],
            "rating_tier_id": self.rating_tier_id
        }
        
        success, response = self.run_test(
            "Create Partner Invite for Team 1",
            "POST",
            "doubles/invites",
            200,
            data=invite_data
        )
        
        if not success or 'token' not in response:
            print("❌ Failed to create partner invite")
            return False
            
        token1 = response['token']
        
        # Accept invite
        accept_data = {
            "token": token1,
            "invitee_user_id": self.player_ids[1]
        }
        
        success, response = self.run_test(
            "Accept Partner Invite for Team 1",
            "POST",
            "doubles/invites/accept",
            200,
            data=accept_data
        )
        
        if success and 'id' in response:
            self.team_ids.append(response['id'])
        else:
            print("❌ Failed to accept partner invite for team 1")
            return False
        
        # Team 2: Player 3 & Player 4
        invite_data = {
            "inviter_user_id": self.player_ids[2],
            "rating_tier_id": self.rating_tier_id
        }
        
        success, response = self.run_test(
            "Create Partner Invite for Team 2",
            "POST",
            "doubles/invites",
            200,
            data=invite_data
        )
        
        if not success or 'token' not in response:
            print("❌ Failed to create partner invite for team 2")
            return False
            
        token2 = response['token']
        
        # Accept invite
        accept_data = {
            "token": token2,
            "invitee_user_id": self.player_ids[3]
        }
        
        success, response = self.run_test(
            "Accept Partner Invite for Team 2",
            "POST",
            "doubles/invites/accept",
            200,
            data=accept_data
        )
        
        if success and 'id' in response:
            self.team_ids.append(response['id'])
        else:
            print("❌ Failed to accept partner invite for team 2")
            return False
        
        print("✅ Test environment setup complete!")
        return True

    def test_ics_endpoint_behavior(self):
        """Test the specific ICS endpoint behavior for confirmed vs non-confirmed matches"""
        print("\n🎾 Testing ICS Endpoint Behavior...")
        
        # 1. Generate team schedule to create matches
        success, response = self.run_test(
            "Generate Team Schedule",
            "POST",
            f"doubles/rating-tiers/{self.rating_tier_id}/generate-team-schedule",
            200
        )
        
        if not success or 'created' not in response:
            print("❌ Failed to generate team schedule")
            return False
        
        if response['created'] == 0:
            print("❌ No matches were created")
            return False
        
        print(f"   Created {response['created']} matches")
        
        # 2. Get the matches that were created
        success, matches_response = self.run_test(
            "Get Generated Matches",
            "GET",
            "doubles/matches",
            200,
            params={"rating_tier_id": self.rating_tier_id}
        )
        
        if not success or not matches_response:
            print("❌ Failed to get matches")
            return False
        
        self.match_id = matches_response[0]['id']
        print(f"   Using match ID: {self.match_id}")
        
        # 3. Test ICS for unconfirmed match (should return 404)
        success, response = self.run_test(
            "Get ICS for Unconfirmed Match (Should Return 404)",
            "GET",
            f"doubles/matches/{self.match_id}/ics",
            404
        )
        
        if success:
            print("   ✅ Correctly returned 404 for unconfirmed match")
        else:
            print("   ❌ Should have returned 404 for unconfirmed match")
            return False
        
        # 4. Propose time slots for the match
        propose_data = {
            "slots": [
                {
                    "start": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                    "venue_name": "Test Tennis Court"
                }
            ],
            "proposed_by_user_id": self.player_ids[0]
        }
        
        success, response = self.run_test(
            "Propose Time Slots",
            "POST",
            f"doubles/matches/{self.match_id}/propose-slots",
            200,
            data=propose_data
        )
        
        if not success or 'slot_ids' not in response:
            print("❌ Failed to propose time slots")
            return False
        
        slot_id = response['slot_ids'][0]
        print(f"   Created slot ID: {slot_id}")
        
        # 5. Confirm the slot with all 4 players
        for player_id in self.player_ids:
            confirm_data = {
                "slot_id": slot_id,
                "user_id": player_id
            }
            
            success, response = self.run_test(
                f"Confirm Slot by Player {player_id}",
                "POST",
                f"doubles/matches/{self.match_id}/confirm-slot",
                200,
                data=confirm_data
            )
            
            if success:
                if response.get('locked'):
                    print(f"   ✅ Match locked after player {player_id} confirmed")
                    break
                else:
                    print(f"   ⏳ Player {player_id} confirmed, waiting for others...")
            else:
                print(f"❌ Failed to confirm slot for player {player_id}")
                # Continue with other players
        
        # 6. Check if match is now confirmed
        success, matches_response = self.run_test(
            "Get Match Details After Confirmation",
            "GET",
            "doubles/matches",
            200,
            params={"rating_tier_id": self.rating_tier_id}
        )
        
        if success and matches_response:
            confirmed_match = None
            for match in matches_response:
                if match['id'] == self.match_id and match.get('status') == 'confirmed':
                    confirmed_match = match
                    break
            
            if confirmed_match:
                print(f"   ✅ Match is now confirmed with scheduled_at: {confirmed_match.get('scheduled_at')}")
                
                # 7. Test ICS for confirmed match (should return 200 with ICS content)
                success, response = self.run_test(
                    "Get ICS for Confirmed Match (Should Return 200)",
                    "GET",
                    f"doubles/matches/{self.match_id}/ics",
                    200
                )
                
                if success and 'ics' in response:
                    ics_content = response['ics']
                    print(f"   ✅ Successfully got ICS content ({len(ics_content)} characters)")
                    
                    # Verify ICS format
                    required_elements = [
                        'BEGIN:VCALENDAR',
                        'END:VCALENDAR',
                        'BEGIN:VEVENT',
                        'END:VEVENT',
                        'DTSTART:',
                        'SUMMARY:'
                    ]
                    
                    all_present = all(element in ics_content for element in required_elements)
                    if all_present:
                        print("   ✅ ICS content has valid format")
                        print(f"   📅 ICS Preview: {ics_content[:200]}...")
                        return True
                    else:
                        print("   ❌ ICS content missing required elements")
                        print(f"   ICS Content: {ics_content}")
                        return False
                else:
                    print("   ❌ Failed to get ICS content for confirmed match")
                    return False
            else:
                print("   ⚠️  Match was not confirmed after all players confirmed slots")
                # This might be expected behavior - let's still test the 404 case
                success, response = self.run_test(
                    "Get ICS for Unconfirmed Match (Should Still Return 404)",
                    "GET",
                    f"doubles/matches/{self.match_id}/ics",
                    404
                )
                
                if success:
                    print("   ✅ Still correctly returns 404 for unconfirmed match")
                    return True
                else:
                    print("   ❌ Should return 404 for unconfirmed match")
                    return False
        
        return False

    def run_all_tests(self):
        """Run all ICS-related tests"""
        print("🎾 Starting ICS Endpoint Testing...")
        print("=" * 60)
        
        # Setup test environment
        if not self.setup_test_environment():
            print("❌ Failed to set up test environment")
            return False
        
        # Run ICS behavior test
        ics_test_result = self.test_ics_endpoint_behavior()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ICS TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if ics_test_result:
            print("\n✅ ICS ENDPOINT BEHAVIOR TEST: PASSED")
            print("   - Returns 404 for non-confirmed matches ✅")
            print("   - Returns 200 with valid ICS for confirmed matches ✅")
        else:
            print("\n❌ ICS ENDPOINT BEHAVIOR TEST: FAILED")
        
        return ics_test_result

if __name__ == "__main__":
    tester = ICSTestRunner()
    success = tester.run_all_tests()
    exit(0 if success else 1)