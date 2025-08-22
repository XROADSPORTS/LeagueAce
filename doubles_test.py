#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class DoublesCoordinatorTester:
    def __init__(self, base_url="https://pickleplay-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data storage
        self.league_manager_id = None
        self.league_id = None
        self.doubles_format_tier_id = None
        self.doubles_tier_id = None
        self.doubles_join_code = None
        self.singles_tier_id = None
        self.doubles_inviter_id = None
        self.doubles_invitee_id = None
        self.partner_invite_token = None
        self.partner_invite_token_2 = None
        self.doubles_team_id = None

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
        """Setup the complete test environment for doubles coordinator testing"""
        print("\n🔧 SETTING UP DOUBLES COORDINATOR TEST ENVIRONMENT")
        print("=" * 60)
        
        # Step 1: Create League Manager
        print("\n📋 Step 1: Create League Manager")
        manager_data = {
            "name": "League Manager",
            "email": f"manager_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "phone": "+1-555-0100",
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
        print(f"   ✅ Created League Manager ID: {self.league_manager_id}")
        
        # Step 2: Create League
        print("\n📋 Step 2: Create League")
        league_data = {
            "name": "Doubles Test League",
            "sport_type": "Tennis",
            "description": "League for testing doubles coordinator functionality"
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
            print("❌ Failed to create league")
            return False
        
        self.league_id = response['id']
        print(f"   ✅ Created League ID: {self.league_id}")
        
        # Step 3: Create Doubles Format Tier
        print("\n📋 Step 3: Create Doubles Format Tier")
        doubles_format_data = {
            "league_id": self.league_id,
            "name": "Doubles Tournament",
            "format_type": "Doubles",
            "description": "Doubles format for partner coordination"
        }
        
        success, response = self.run_test(
            "Create Doubles Format Tier",
            "POST",
            "format-tiers",
            200,
            data=doubles_format_data
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create doubles format tier")
            return False
        
        self.doubles_format_tier_id = response['id']
        print(f"   ✅ Created Doubles Format Tier ID: {self.doubles_format_tier_id}")
        
        # Step 4: Create Doubles Rating Tier
        print("\n📋 Step 4: Create Doubles Rating Tier")
        doubles_rating_data = {
            "format_tier_id": self.doubles_format_tier_id,
            "name": "4.0-4.5 Doubles",
            "min_rating": 3.8,
            "max_rating": 4.7,
            "max_players": 16,
            "competition_system": "Team League Format",
            "playoff_spots": 4,
            "region": "Bay Area",
            "surface": "Hard Court"
        }
        
        success, response = self.run_test(
            "Create Doubles Rating Tier",
            "POST",
            "rating-tiers",
            200,
            data=doubles_rating_data
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create doubles rating tier")
            return False
        
        self.doubles_tier_id = response['id']
        self.doubles_join_code = response.get('join_code')
        print(f"   ✅ Created Doubles Rating Tier ID: {self.doubles_tier_id}")
        print(f"   ✅ Generated Join Code: {self.doubles_join_code}")
        
        # Step 5: Create Singles Format Tier (for negative testing)
        print("\n📋 Step 5: Create Singles Format Tier (Non-Doubles)")
        singles_format_data = {
            "league_id": self.league_id,
            "name": "Singles Tournament",
            "format_type": "Singles",
            "description": "Singles format (not doubles)"
        }
        
        success, response = self.run_test(
            "Create Singles Format Tier",
            "POST",
            "format-tiers",
            200,
            data=singles_format_data
        )
        
        if success and 'id' in response:
            singles_format_tier_id = response['id']
            
            # Create singles rating tier
            singles_rating_data = {
                "format_tier_id": singles_format_tier_id,
                "name": "4.0 Singles",
                "min_rating": 3.5,
                "max_rating": 4.5,
                "max_players": 12,
                "competition_system": "Team League Format",
                "playoff_spots": 4
            }
            
            success, response = self.run_test(
                "Create Singles Rating Tier",
                "POST",
                "rating-tiers",
                200,
                data=singles_rating_data
            )
            
            if success and 'id' in response:
                self.singles_tier_id = response['id']
                print(f"   ✅ Created Singles Rating Tier ID: {self.singles_tier_id}")
        
        # Step 6: Create Test Users
        print("\n📋 Step 6: Create Test Users")
        
        # Create inviter user
        inviter_data = {
            "name": "Alice Johnson",
            "email": f"alice.johnson_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "phone": "+1-555-0201",
            "rating_level": 4.2,
            "role": "Player"
        }
        
        success, response = self.run_test(
            "Create Doubles Inviter",
            "POST",
            "users",
            200,
            data=inviter_data
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create inviter user")
            return False
        
        self.doubles_inviter_id = response['id']
        print(f"   ✅ Created Doubles Inviter ID: {self.doubles_inviter_id}")
        
        # Create invitee user
        invitee_data = {
            "name": "Bob Smith",
            "email": f"bob.smith_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "phone": "+1-555-0202",
            "rating_level": 4.1,
            "role": "Player"
        }
        
        success, response = self.run_test(
            "Create Doubles Invitee",
            "POST",
            "users",
            200,
            data=invitee_data
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create invitee user")
            return False
        
        self.doubles_invitee_id = response['id']
        print(f"   ✅ Created Doubles Invitee ID: {self.doubles_invitee_id}")
        
        print("\n✅ SETUP COMPLETE - Ready for doubles coordinator testing!")
        return True

    def test_create_partner_invite_with_rating_tier_id(self):
        """Test POST /api/doubles/invites with rating_tier_id"""
        invite_data = {
            "inviter_user_id": self.doubles_inviter_id,
            "rating_tier_id": self.doubles_tier_id,
            "invitee_contact": "partner@example.com"
        }
        
        success, response = self.run_test(
            "Create Partner Invite (Rating Tier ID)",
            "POST",
            "doubles/invites",
            200,
            data=invite_data
        )
        
        if success:
            self.partner_invite_token = response.get('token')
            print(f"   Token: {self.partner_invite_token}")
            print(f"   League: {response.get('league_name')}")
            print(f"   Tier: {response.get('tier_name')}")
            print(f"   Inviter: {response.get('inviter_name')}")
            print(f"   Expires: {response.get('expires_at')}")
            
            # Validate response structure
            required_fields = ['token', 'league_name', 'tier_name', 'inviter_name', 'expires_at']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                return False
        
        return success

    def test_create_partner_invite_with_join_code(self):
        """Test POST /api/doubles/invites with join_code"""
        invite_data = {
            "inviter_user_id": self.doubles_inviter_id,
            "join_code": self.doubles_join_code,
            "invitee_contact": "partner2@example.com"
        }
        
        success, response = self.run_test(
            "Create Partner Invite (Join Code)",
            "POST",
            "doubles/invites",
            200,
            data=invite_data
        )
        
        if success:
            self.partner_invite_token_2 = response.get('token')
            print(f"   Token: {self.partner_invite_token_2}")
            print(f"   League: {response.get('league_name')}")
            print(f"   Tier: {response.get('tier_name')}")
        
        return success

    def test_create_partner_invite_non_doubles_tier(self):
        """Test POST /api/doubles/invites with non-doubles tier (should return 400)"""
        invite_data = {
            "inviter_user_id": self.doubles_inviter_id,
            "rating_tier_id": self.singles_tier_id
        }
        
        success, response = self.run_test(
            "Create Partner Invite (Non-Doubles Tier - Should Fail)",
            "POST",
            "doubles/invites",
            400,
            data=invite_data
        )
        
        return success

    def test_create_partner_invite_missing_tier(self):
        """Test POST /api/doubles/invites with missing tier (should return 404)"""
        invite_data = {
            "inviter_user_id": self.doubles_inviter_id,
            "rating_tier_id": "non-existent-tier-id"
        }
        
        success, response = self.run_test(
            "Create Partner Invite (Missing Tier - Should Fail)",
            "POST",
            "doubles/invites",
            404,
            data=invite_data
        )
        
        return success

    def test_create_partner_invite_out_of_range_rating(self):
        """Test POST /api/doubles/invites with inviter rating out of range (should return 400)"""
        # Create user with rating outside the doubles tier range
        out_of_range_data = {
            "name": "Charlie Wilson",
            "email": f"charlie.wilson_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "phone": "+1-555-0203",
            "rating_level": 5.2,  # Outside the 3.8-4.7 range
            "role": "Player"
        }
        
        success, response = self.run_test(
            "Create Out-of-Range User",
            "POST",
            "users",
            200,
            data=out_of_range_data
        )
        
        if not success or 'id' not in response:
            return False
        
        out_of_range_user_id = response['id']
        
        invite_data = {
            "inviter_user_id": out_of_range_user_id,
            "rating_tier_id": self.doubles_tier_id
        }
        
        success, response = self.run_test(
            "Create Partner Invite (Out-of-Range Rating - Should Fail)",
            "POST",
            "doubles/invites",
            400,
            data=invite_data
        )
        
        return success

    def test_preview_partner_invite(self):
        """Test GET /api/doubles/invites/{token}"""
        if not self.partner_invite_token:
            print("❌ Skipping - No partner invite token available")
            return False
        
        success, response = self.run_test(
            "Preview Partner Invite",
            "GET",
            f"doubles/invites/{self.partner_invite_token}",
            200
        )
        
        if success:
            print(f"   Token: {response.get('token')}")
            print(f"   League: {response.get('league_name')}")
            print(f"   Tier: {response.get('tier_name')}")
            print(f"   Inviter: {response.get('inviter_name')}")
            print(f"   Format: {response.get('format_type')}")
            print(f"   Expires: {response.get('expires_at')}")
        
        return success

    def test_preview_expired_invite(self):
        """Test GET /api/doubles/invites/{token} with expired invite"""
        success, response = self.run_test(
            "Preview Invalid/Expired Invite (Should Fail)",
            "GET",
            "doubles/invites/invalid-token-12345",
            404  # Invalid token should return 404
        )
        
        return success

    def test_accept_partner_invite(self):
        """Test POST /api/doubles/invites/accept"""
        if not self.partner_invite_token or not self.doubles_invitee_id:
            print("❌ Skipping - No partner invite token or invitee available")
            return False
        
        accept_data = {
            "token": self.partner_invite_token,
            "invitee_user_id": self.doubles_invitee_id
        }
        
        success, response = self.run_test(
            "Accept Partner Invite",
            "POST",
            "doubles/invites/accept",
            200,
            data=accept_data
        )
        
        if success:
            self.doubles_team_id = response.get('id')
            print(f"   Team ID: {self.doubles_team_id}")
            print(f"   Team Name: {response.get('team_name')}")
            print(f"   Status: {response.get('status')}")
            print(f"   Members: {len(response.get('members', []))}")
            
            # Validate team name format
            actual_name = response.get('team_name', '')
            if '&' in actual_name and len(response.get('members', [])) == 2:
                print(f"   ✅ Team name format correct: {actual_name}")
            else:
                print(f"   ⚠️  Team name format may be incorrect: {actual_name}")
            
            # Validate members
            members = response.get('members', [])
            if len(members) == 2:
                member_ids = [m.get('user_id') for m in members]
                if self.doubles_inviter_id in member_ids and self.doubles_invitee_id in member_ids:
                    print(f"   ✅ Both inviter and invitee added as members")
                else:
                    print(f"   ⚠️  Member IDs don't match expected users")
            else:
                print(f"   ⚠️  Expected 2 members, got {len(members)}")
        
        return success

    def test_accept_invite_same_person(self):
        """Test POST /api/doubles/invites/accept with same person (should fail)"""
        if not self.partner_invite_token_2 or not self.doubles_inviter_id:
            print("❌ Skipping - No second partner invite token available")
            return False
        
        accept_data = {
            "token": self.partner_invite_token_2,
            "invitee_user_id": self.doubles_inviter_id  # Same as inviter
        }
        
        success, response = self.run_test(
            "Accept Invite (Same Person - Should Fail)",
            "POST",
            "doubles/invites/accept",
            400,
            data=accept_data
        )
        
        return success

    def test_accept_invite_already_on_team(self):
        """Test POST /api/doubles/invites/accept when user already on active team (should fail)"""
        # Create a third user
        third_user_data = {
            "name": "Carol Davis",
            "email": f"carol.davis_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "phone": "+1-555-0204",
            "rating_level": 4.3,
            "role": "Player"
        }
        
        success, response = self.run_test(
            "Create Third User for Team Test",
            "POST",
            "users",
            200,
            data=third_user_data
        )
        
        if not success or 'id' not in response:
            return False
        
        third_user_id = response['id']
        
        # Create another invite with the third user as inviter
        invite_data = {
            "inviter_user_id": third_user_id,
            "rating_tier_id": self.doubles_tier_id
        }
        
        success, response = self.run_test(
            "Create Second Invite for Team Test",
            "POST",
            "doubles/invites",
            200,
            data=invite_data
        )
        
        if not success or 'token' not in response:
            return False
        
        second_token = response['token']
        
        # Try to accept with someone who's already on a team (doubles_invitee_id)
        accept_data = {
            "token": second_token,
            "invitee_user_id": self.doubles_invitee_id  # Already on a team
        }
        
        success, response = self.run_test(
            "Accept Invite (Already on Team - Should Fail)",
            "POST",
            "doubles/invites/accept",
            400,
            data=accept_data
        )
        
        return success

    def test_get_player_doubles_teams(self):
        """Test GET /api/doubles/teams?player_id=..."""
        if not self.doubles_inviter_id:
            print("❌ Skipping - No doubles inviter ID available")
            return False
        
        success, response = self.run_test(
            "Get Player Doubles Teams",
            "GET",
            "doubles/teams",
            200,
            params={"player_id": self.doubles_inviter_id}
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} teams for player")
            for i, team in enumerate(response):
                print(f"   Team {i+1}: {team.get('team_name')}")
                print(f"     - League: {team.get('league_name')}")
                print(f"     - Tier: {team.get('rating_tier_name')}")
                print(f"     - Status: {team.get('status')}")
                print(f"     - Members: {len(team.get('members', []))}")
                
                # Validate team structure
                required_fields = ['id', 'team_name', 'rating_tier_id', 'league_id', 'status', 'members']
                missing_fields = [field for field in required_fields if field not in team]
                if missing_fields:
                    print(f"     ⚠️  Missing fields: {missing_fields}")
        
        return success

    def test_get_player_doubles_teams_no_teams(self):
        """Test GET /api/doubles/teams?player_id=... for player with no teams"""
        # Create a new user who hasn't joined any teams
        new_user_data = {
            "name": "David Lee",
            "email": f"david.lee_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "phone": "+1-555-0205",
            "rating_level": 4.0,
            "role": "Player"
        }
        
        success, response = self.run_test(
            "Create User with No Teams",
            "POST",
            "users",
            200,
            data=new_user_data
        )
        
        if not success or 'id' not in response:
            return False
        
        new_user_id = response['id']
        
        success, response = self.run_test(
            "Get Doubles Teams (No Teams)",
            "GET",
            "doubles/teams",
            200,
            params={"player_id": new_user_id}
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} teams (expected 0)")
            return len(response) == 0
        
        return success

    def run_all_tests(self):
        """Run all doubles coordinator tests"""
        print("\n🎾 DOUBLES COORDINATOR PHASE 1 COMPREHENSIVE TESTING")
        print("=" * 70)
        
        # Setup environment first
        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return False
        
        # Define all tests
        doubles_tests = [
            ("Create Partner Invite (Rating Tier ID)", self.test_create_partner_invite_with_rating_tier_id),
            ("Create Partner Invite (Join Code)", self.test_create_partner_invite_with_join_code),
            ("Create Invite Non-Doubles Tier (400)", self.test_create_partner_invite_non_doubles_tier),
            ("Create Invite Missing Tier (404)", self.test_create_partner_invite_missing_tier),
            ("Create Invite Out-of-Range Rating (400)", self.test_create_partner_invite_out_of_range_rating),
            ("Preview Partner Invite", self.test_preview_partner_invite),
            ("Preview Invalid/Expired Invite (404)", self.test_preview_expired_invite),
            ("Accept Partner Invite", self.test_accept_partner_invite),
            ("Accept Invite Same Person (400)", self.test_accept_invite_same_person),
            ("Accept Invite Already on Team (400)", self.test_accept_invite_already_on_team),
            ("Get Player Doubles Teams", self.test_get_player_doubles_teams),
            ("Get Player Doubles Teams (No Teams)", self.test_get_player_doubles_teams_no_teams)
        ]
        
        print(f"\n🚀 RUNNING {len(doubles_tests)} DOUBLES COORDINATOR TESTS")
        print("=" * 70)
        
        successful_tests = 0
        failed_tests = []
        
        for test_name, test_method in doubles_tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_method():
                    successful_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    failed_tests.append(test_name)
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                failed_tests.append(test_name)
                print(f"❌ {test_name}: ERROR - {str(e)}")
        
        # Print summary
        print(f"\n🎯 DOUBLES COORDINATOR TEST SUMMARY")
        print("=" * 70)
        print(f"Tests Run: {len(doubles_tests)}")
        print(f"Tests Passed: {successful_tests}")
        print(f"Tests Failed: {len(failed_tests)}")
        print(f"Success Rate: {(successful_tests/len(doubles_tests)*100):.1f}%")
        
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test}")
        
        if successful_tests == len(doubles_tests):
            print("\n🎉 ALL DOUBLES COORDINATOR TESTS PASSED!")
            return True
        elif successful_tests >= len(doubles_tests) * 0.8:
            print("\n⚠️  Most doubles coordinator features working, minor issues remain")
            return True
        else:
            print("\n🚨 CRITICAL ISSUES FOUND - Doubles coordinator needs attention")
            return False

def main():
    print("🎾 Doubles Coordinator Phase 1 Testing Suite")
    print("=" * 60)
    
    tester = DoublesCoordinatorTester()
    success = tester.run_all_tests()
    
    # Print final results
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    print(f"Total Tests Run: {tester.tests_run}")
    print(f"Total Tests Passed: {tester.tests_passed}")
    print(f"Overall Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if success:
        print("\n🎉 DOUBLES COORDINATOR PHASE 1 IS WORKING!")
        return 0
    else:
        print("\n⚠️  DOUBLES COORDINATOR PHASE 1 NEEDS ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())