import requests
import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

class ReviewRequestTester:
    def __init__(self, base_url="https://doubles-master.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_users = []
        self.tier_id = None
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

    def setup_environment(self):
        """Setup test environment"""
        print("\n🔧 Setting up test environment...")
        
        # Create 4 test users
        for i in range(4):
            user_data = {
                "name": f"Test Player {chr(65 + i)}",
                "email": f"test.player{chr(65 + i).lower()}_{datetime.now().strftime('%H%M%S')}@test.com",
                "phone": f"+1-555-040{i + 1}",
                "rating_level": 4.0
            }
            
            success, response = self.run_test(
                f"Create Test Player {chr(65 + i)}",
                "POST",
                "users",
                200,
                data=user_data
            )
            
            if success and 'id' in response:
                self.test_users.append(response['id'])
        
        if len(self.test_users) < 4:
            print("❌ Failed to create enough test users")
            return False
        
        # Generate tier ID
        import uuid
        self.tier_id = str(uuid.uuid4())
        
        # Configure tier
        config_data = {
            "season_name": "Review Test Season",
            "season_length": 6,
            "minimize_repeat_partners": True,
            "track_first_match_badge": True,
            "track_finished_badge": True,
            "subgroup_labels": ["Test Group"],
            "subgroup_size": 4
        }
        
        success, response = self.run_test(
            "Configure RR Tier",
            "POST",
            f"rr/tiers/{self.tier_id}/configure",
            200,
            data=config_data
        )
        
        if not success:
            return False
        
        # Generate subgroups
        subgroup_data = {
            "player_ids": self.test_users
        }
        
        success, response = self.run_test(
            "Generate Subgroups",
            "POST",
            f"rr/tiers/{self.tier_id}/subgroups/generate",
            200,
            data=subgroup_data
        )
        
        if not success:
            return False
        
        # Schedule matches
        schedule_data = {
            "player_ids": self.test_users
        }
        
        success, response = self.run_test(
            "Schedule Matches",
            "POST",
            f"rr/tiers/{self.tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if success and 'schedule_quality' in response:
            print(f"   ✅ Schedule quality field present: {response.get('schedule_quality')}")
        
        return success

    def get_match_id(self):
        """Get a match ID for testing"""
        success, response = self.run_test(
            "Get Weeks for Match ID",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": self.test_users[0], "tier_id": self.tier_id}
        )
        
        if success and response.get('weeks'):
            for week in response['weeks']:
                if week.get('matches'):
                    self.match_id = week['matches'][0]['id']
                    print(f"   Using Match ID: {self.match_id}")
                    return True
        return False

    def test_toss_endpoint(self):
        """Test 1: POST /api/rr/matches/{mid}/toss persists toss and prevents duplicates"""
        print("\n🎯 TEST 1: RR TOSS ENDPOINT")
        
        if not self.match_id and not self.get_match_id():
            print("❌ No match available for toss testing")
            return False
        
        # Test toss
        toss_data = {
            "actor_user_id": self.test_users[0],
            "choice": "serve"
        }
        
        success1, response1 = self.run_test(
            "RR Match Toss",
            "POST",
            f"rr/matches/{self.match_id}/toss",
            200,
            data=toss_data
        )
        
        toss_persisted = False
        if success1:
            print(f"   Toss Winner: {response1.get('winner_user_id')}")
            print(f"   Toss Choice: {response1.get('choice')}")
            toss_persisted = True
        
        # Test duplicate prevention
        success2, response2 = self.run_test(
            "Duplicate Toss (Should Fail)",
            "POST",
            f"rr/matches/{self.match_id}/toss",
            400,
            data=toss_data
        )
        
        duplicate_prevented = success2
        if success2:
            print("   ✅ Duplicate toss correctly prevented")
        
        return toss_persisted and duplicate_prevented

    def test_partner_override(self):
        """Test 2: Partner override with 3 valid sets returns pending_confirmations, then 4 confirms lead to locked"""
        print("\n🎯 TEST 2: PARTNER OVERRIDE FLOW")
        
        if not self.match_id:
            print("❌ No match ID available")
            return False
        
        # Create partner override with 3 valid sets
        players = self.test_users
        override_data = {
            "actor_user_id": players[0],
            "sets": [
                [[players[0], players[1]], [players[2], players[3]]],
                [[players[0], players[2]], [players[1], players[3]]],
                [[players[0], players[3]], [players[1], players[2]]]
            ]
        }
        
        success1, response1 = self.run_test(
            "Partner Override Proposal",
            "POST",
            f"rr/matches/{self.match_id}/partner-override",
            200,
            data=override_data
        )
        
        pending_status = False
        if success1 and response1.get('status') == 'pending_confirmations':
            print("   ✅ Partner override returns pending_confirmations")
            pending_status = True
        
        # Test 4 confirmations
        confirmations_count = 0
        final_status = None
        
        for i, player_id in enumerate(players):
            confirm_data = {"user_id": player_id}
            
            success_confirm, response_confirm = self.run_test(
                f"Confirm Override Player {i+1}",
                "POST",
                f"rr/matches/{self.match_id}/partner-override/confirm",
                200,
                data=confirm_data
            )
            
            if success_confirm:
                confirmations_count += 1
                final_status = response_confirm.get('status')
                confirmations = response_confirm.get('confirmations', 0)
                print(f"   Player {i+1}: Status={final_status}, Confirmations={confirmations}")
        
        locked_status = (final_status == 'locked' and confirmations_count == 4)
        if locked_status:
            print("   ✅ All 4 confirmations lead to status=locked")
        
        return pending_status and locked_status

    def test_invalid_override(self):
        """Test 3: Invalid override sets (missing players) returns 400"""
        print("\n🎯 TEST 3: INVALID OVERRIDE VALIDATION")
        
        if not self.match_id:
            print("❌ No match ID available")
            return False
        
        # Create new match for clean test
        if not self.get_match_id():
            print("❌ Could not get new match ID")
            return False
        
        # Invalid override - missing players
        players = self.test_users
        invalid_data = {
            "actor_user_id": players[0],
            "sets": [
                [[players[0], players[1]], [players[2]]],  # Missing one player
                [[players[0]], [players[1], players[2]]],  # Missing one player  
                [[players[0], players[1]], [players[2]]]   # Missing one player
            ]
        }
        
        success, response = self.run_test(
            "Invalid Override (Missing Players)",
            "POST",
            f"rr/matches/{self.match_id}/partner-override",
            400,
            data=invalid_data
        )
        
        if success:
            print("   ✅ Invalid override correctly returns 400")
            return True
        else:
            print("   ❌ Should have returned 400 for invalid override")
            return False

    def test_scheduler_quality(self):
        """Test 4: Scheduler response includes schedule_quality"""
        print("\n🎯 TEST 4: SCHEDULER QUALITY FIELD")
        
        # Create new tier for clean test
        import uuid
        test_tier_id = str(uuid.uuid4())
        
        # Configure
        config_data = {
            "season_name": "Quality Test",
            "season_length": 4,
            "minimize_repeat_partners": True,
            "subgroup_labels": ["Quality Group"],
            "subgroup_size": 4
        }
        
        success1, response1 = self.run_test(
            "Configure Tier for Quality Test",
            "POST",
            f"rr/tiers/{test_tier_id}/configure",
            200,
            data=config_data
        )
        
        if not success1:
            return False
        
        # Schedule and check for quality field
        schedule_data = {
            "player_ids": self.test_users
        }
        
        success2, response2 = self.run_test(
            "Schedule with Quality Check",
            "POST",
            f"rr/tiers/{test_tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if success2 and 'schedule_quality' in response2:
            quality = response2.get('schedule_quality')
            print(f"   ✅ Schedule quality field present: {quality}")
            print(f"   Feasibility Score: {response2.get('feasibility_score')}")
            return True
        else:
            print("   ❌ Schedule quality field missing")
            return False

    def test_rr_flows(self):
        """Test 5: RR flows (availability, submit/approve scorecard, standings) still work"""
        print("\n🎯 TEST 5: RR FLOWS STILL WORK")
        
        # Test availability
        avail_data = {
            "user_id": self.test_users[0],
            "windows": ["Mon AM", "Wed PM", "Fri Evening"]
        }
        
        success1, response1 = self.run_test(
            "Set Availability",
            "PUT",
            "rr/availability",
            200,
            data=avail_data
        )
        
        success2, response2 = self.run_test(
            "Get Availability",
            "GET",
            "rr/availability",
            200,
            params={"user_id": self.test_users[0]}
        )
        
        availability_works = success1 and success2
        if availability_works:
            print("   ✅ Availability endpoints working")
        
        # Test scorecard flow
        if not self.match_id and not self.get_match_id():
            print("   ❌ No match for scorecard test")
            return availability_works
        
        # Submit scorecard
        scorecard_data = {
            "sets": [
                {
                    "team1_games": 6,
                    "team2_games": 4,
                    "winners": [self.test_users[0], self.test_users[1]],
                    "losers": [self.test_users[2], self.test_users[3]]
                },
                {
                    "team1_games": 6,
                    "team2_games": 3,
                    "winners": [self.test_users[0], self.test_users[1]],
                    "losers": [self.test_users[2], self.test_users[3]]
                },
                {
                    "team1_games": 6,
                    "team2_games": 2,
                    "winners": [self.test_users[0], self.test_users[1]],
                    "losers": [self.test_users[2], self.test_users[3]]
                }
            ],
            "submitted_by_user_id": self.test_users[0]
        }
        
        success3, response3 = self.run_test(
            "Submit Scorecard",
            "POST",
            f"rr/matches/{self.match_id}/submit-scorecard",
            200,
            data=scorecard_data
        )
        
        # Approve scorecard
        approve_data = {
            "approved_by_user_id": self.test_users[1]
        }
        
        success4, response4 = self.run_test(
            "Approve Scorecard",
            "POST",
            f"rr/matches/{self.match_id}/approve-scorecard",
            200,
            data=approve_data
        )
        
        scorecard_works = success3 and success4
        if scorecard_works:
            print("   ✅ Scorecard submit/approve working")
        
        # Test standings
        success5, response5 = self.run_test(
            "Get Standings",
            "GET",
            "rr/standings",
            200,
            params={"tier_id": self.tier_id}
        )
        
        standings_works = success5
        if success5:
            rows = response5.get('rows', [])
            print(f"   ✅ Standings working - {len(rows)} rows")
            if rows:
                first_row = rows[0]
                print(f"   First place pct_game_win: {first_row.get('pct_game_win')}")
        
        return availability_works and scorecard_works and standings_works

    def run_review_tests(self):
        """Run all review request tests"""
        print("🚀 REVIEW REQUEST TESTING")
        print("=" * 60)
        print("Testing specific items from review request:")
        print("1) POST /api/rr/matches/{mid}/toss persists toss and prevents duplicates")
        print("2) Partner override: 3 valid sets → pending_confirmations, 4 confirms → locked")
        print("3) Invalid override sets (missing players) returns 400")
        print("4) Scheduler response includes schedule_quality")
        print("5) RR flows (availability, submit/approve scorecard, standings) still work")
        print("=" * 60)
        
        # Setup
        if not self.setup_environment():
            print("❌ Failed to setup environment")
            return False
        
        # Run tests
        results = []
        results.append(self.test_toss_endpoint())
        results.append(self.test_partner_override())
        results.append(self.test_invalid_override())
        results.append(self.test_scheduler_quality())
        results.append(self.test_rr_flows())
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 REVIEW REQUEST TEST SUMMARY")
        print("=" * 60)
        
        test_names = [
            "RR Toss Endpoint (persist + prevent duplicates)",
            "Partner Override Flow (3 sets → pending → 4 confirms → locked)",
            "Invalid Override Validation (missing players → 400)",
            "Scheduler Quality Field Present",
            "RR Flows Still Work (availability, scorecard, standings)"
        ]
        
        passed = sum(results)
        total = len(results)
        
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{i+1}. {name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        print(f"API Tests: {self.tests_passed}/{self.tests_run} passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        return passed == total

if __name__ == "__main__":
    tester = ReviewRequestTester()
    success = tester.run_review_tests()
    sys.exit(0 if success else 1)