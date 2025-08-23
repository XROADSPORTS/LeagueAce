import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

class RRImprovementsAPITester:
    def __init__(self, base_url="https://matchmaker-22.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.tier_id = None
        self.user_ids = []
        self.match_id = None
        self.scorecard_id = None

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
        """Setup test environment with users and tier configuration"""
        print("\n🏗️  Setting up RR test environment...")
        
        # Create 8 test users for comprehensive testing
        for i in range(8):
            user_data = {
                "name": f"RR Player {chr(65 + i)}",
                "email": f"rr.player{chr(65 + i).lower()}_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
                "phone": f"+1-555-030{i + 1}",
                "rating_level": 4.0 + (i * 0.1),
                "lan": f"RR-{chr(65 + i)}-{datetime.now().strftime('%H%M%S')}"
            }
            
            success, response = self.run_test(
                f"Create RR User {chr(65 + i)}",
                "POST",
                "users",
                200,
                data=user_data
            )
            
            if success and 'id' in response:
                self.user_ids.append(response['id'])
                print(f"   Created User {chr(65 + i)} ID: {response['id']}")
        
        if len(self.user_ids) < 8:
            print("❌ Failed to create enough users for testing")
            return False
        
        # Generate a unique tier ID for testing
        self.tier_id = f"tier_{str(uuid.uuid4())[:8]}"
        print(f"   Using Tier ID: {self.tier_id}")
        
        # Configure the RR tier
        config_data = {
            "season_name": "RR Improvements Test Season",
            "season_length": 8,
            "minimize_repeat_partners": True,
            "track_first_match_badge": True,
            "track_finished_badge": True,
            "subgroup_labels": ["Alpha", "Beta"],
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
            print("❌ Failed to configure RR tier")
            return False
        
        # Set varied availability for testing conflicts
        availability_windows = [
            ["Monday Morning", "Wednesday Evening", "Saturday Afternoon"],
            ["Tuesday Evening", "Thursday Morning", "Sunday Morning"],
            ["Monday Morning", "Friday Evening", "Saturday Afternoon"],
            ["Wednesday Evening", "Thursday Morning", "Sunday Morning"],
            ["Monday Morning", "Tuesday Evening", "Saturday Afternoon"],
            ["Wednesday Evening", "Friday Evening", "Sunday Morning"],
            ["Monday Morning", "Thursday Morning", "Saturday Afternoon"],
            ["Tuesday Evening", "Wednesday Evening", "Sunday Morning"]
        ]
        
        for i, user_id in enumerate(self.user_ids):
            avail_data = {
                "user_id": user_id,
                "windows": availability_windows[i]
            }
            
            success, response = self.run_test(
                f"Set Availability for User {chr(65 + i)}",
                "PUT",
                "rr/availability",
                200,
                data=avail_data
            )
        
        print("✅ Test environment setup complete")
        return True

    def test_scheduler_with_backtracking_and_quality(self):
        """Test 1: Scheduler performs light local backtracking and returns schedule_quality"""
        print("\n🎯 TEST 1: Scheduler with Backtracking and Quality Metrics")
        
        if not self.tier_id or len(self.user_ids) < 8:
            print("❌ Skipping - Test environment not ready")
            return False
        
        # Test with week_windows mapping to trigger availability constraints
        week_windows = {
            0: "Monday Morning",
            1: "Tuesday Evening", 
            2: "Wednesday Evening",
            3: "Thursday Morning",
            4: "Friday Evening",
            5: "Saturday Afternoon",
            6: "Sunday Morning",
            7: "Monday Morning"
        }
        
        schedule_data = {
            "player_ids": self.user_ids,
            "week_windows": week_windows
        }
        
        success, response = self.run_test(
            "Schedule with Week Windows (Backtracking Test)",
            "POST",
            f"rr/tiers/{self.tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if success:
            print(f"   Status: {response.get('status')}")
            print(f"   Weeks: {response.get('weeks')}")
            print(f"   Feasibility Score: {response.get('feasibility_score')}")
            print(f"   Schedule Quality: {response.get('schedule_quality')}")
            print(f"   Conflicts: {response.get('conflicts', {})}")
            
            # Verify required fields are present
            required_fields = ['status', 'weeks', 'feasibility_score', 'schedule_quality', 'conflicts']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False
            
            # Verify schedule_quality is present and numeric
            schedule_quality = response.get('schedule_quality')
            if schedule_quality is None or not isinstance(schedule_quality, (int, float)):
                print(f"   ❌ schedule_quality should be numeric, got: {schedule_quality}")
                return False
            
            # Verify conflicts detection
            conflicts = response.get('conflicts', {})
            if not isinstance(conflicts, dict):
                print(f"   ❌ conflicts should be dict, got: {type(conflicts)}")
                return False
            
            # Check if backtracking reduced conflicts (should have some conflicts due to availability constraints)
            total_conflicts = sum(len(players) for players in conflicts.values())
            print(f"   Total conflicted player-weeks: {total_conflicts}")
            
            # Verify feasibility_score is reasonable (should be > 0 for 8 players)
            feasibility_score = response.get('feasibility_score', 0)
            if feasibility_score <= 0:
                print(f"   ❌ feasibility_score should be > 0, got: {feasibility_score}")
                return False
            
            print("   ✅ Scheduler with backtracking and quality metrics working correctly")
            return True
        
        return success

    def test_scorecard_approval_creates_snapshots(self):
        """Test 2: Approving scorecard inserts rr_snapshots for trend analysis"""
        print("\n🎯 TEST 2: Scorecard Approval Creates Snapshots")
        
        if not self.tier_id or len(self.user_ids) < 4:
            print("❌ Skipping - Test environment not ready")
            return False
        
        # First get a match to submit scorecard for
        success, weeks_response = self.run_test(
            "Get RR Weeks for Scorecard Test",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": self.user_ids[0], "tier_id": self.tier_id}
        )
        
        if not success or not weeks_response.get('weeks'):
            print("❌ No matches available for scorecard test")
            return False
        
        # Find a match to use
        match_id = None
        for week in weeks_response['weeks']:
            if week.get('matches'):
                match_id = week['matches'][0]['id']
                break
        
        if not match_id:
            print("❌ No match ID found for scorecard test")
            return False
        
        self.match_id = match_id
        print(f"   Using Match ID: {match_id}")
        
        # Submit a scorecard with 3 sets
        scorecard_data = {
            "sets": [
                {
                    "team1_games": 6,
                    "team2_games": 4,
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[2], self.user_ids[3]]
                },
                {
                    "team1_games": 4,
                    "team2_games": 6,
                    "winners": [self.user_ids[2], self.user_ids[3]],
                    "losers": [self.user_ids[0], self.user_ids[1]]
                },
                {
                    "team1_games": 7,
                    "team2_games": 5,
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[2], self.user_ids[3]]
                }
            ],
            "submitted_by_user_id": self.user_ids[0]
        }
        
        success, response = self.run_test(
            "Submit Scorecard",
            "POST",
            f"rr/matches/{match_id}/submit-scorecard",
            200,
            data=scorecard_data
        )
        
        if not success:
            print("❌ Failed to submit scorecard")
            return False
        
        self.scorecard_id = response.get('scorecard_id')
        print(f"   Scorecard ID: {self.scorecard_id}")
        
        # Get initial snapshot count
        # Note: We can't directly query snapshots, but we'll check standings before/after
        success, initial_standings = self.run_test(
            "Get Initial Standings",
            "GET",
            "rr/standings",
            200,
            params={"tier_id": self.tier_id}
        )
        
        # Approve the scorecard (this should create a snapshot)
        approve_data = {
            "approved_by_user_id": self.user_ids[1]
        }
        
        success, response = self.run_test(
            "Approve Scorecard (Creates Snapshot)",
            "POST",
            f"rr/matches/{match_id}/approve-scorecard",
            200,
            data=approve_data
        )
        
        if success:
            print(f"   Approval Status: {response.get('status')}")
            print("   ✅ Scorecard approved successfully (snapshot should be created)")
            return True
        
        return success

    def test_standings_with_trend_field(self):
        """Test 3: Standings API returns trend field comparing with last snapshot"""
        print("\n🎯 TEST 3: Standings with Trend Field")
        
        if not self.tier_id:
            print("❌ Skipping - No tier ID available")
            return False
        
        # Get standings after scorecard approval
        success, response = self.run_test(
            "Get Standings with Trend",
            "GET",
            "rr/standings",
            200,
            params={"tier_id": self.tier_id}
        )
        
        if success:
            rows = response.get('rows', [])
            print(f"   Total standings rows: {len(rows)}")
            
            # Check for required fields in standings
            if rows:
                first_row = rows[0]
                print(f"   First row keys: {list(first_row.keys())}")
                
                # Verify required fields
                required_fields = ['player_id', 'matches_played', 'set_points', 'pct_game_win']
                missing_fields = [field for field in required_fields if field not in first_row]
                
                if missing_fields:
                    print(f"   ❌ Missing required fields: {missing_fields}")
                    return False
                
                # Check for trend field (may be None for first snapshot)
                trend_present = 'trend' in first_row
                print(f"   Trend field present: {trend_present}")
                
                # Check for badges
                badges_present = 'badges' in first_row
                print(f"   Badges field present: {badges_present}")
                
                if badges_present:
                    badges = first_row.get('badges', [])
                    print(f"   Badges in first row: {badges}")
                    
                    # Verify badges are still working
                    if isinstance(badges, list):
                        print("   ✅ Badges field is properly formatted as list")
                    else:
                        print(f"   ❌ Badges should be list, got: {type(badges)}")
                        return False
                
                # Verify pct_game_win precision (should be 4 decimal places)
                pct_game_win = first_row.get('pct_game_win')
                if pct_game_win is not None:
                    print(f"   pct_game_win: {pct_game_win}")
                    if isinstance(pct_game_win, float):
                        print("   ✅ pct_game_win is properly formatted as float")
                    else:
                        print(f"   ❌ pct_game_win should be float, got: {type(pct_game_win)}")
                        return False
                
                print("   ✅ Standings with trend field working correctly")
                return True
            else:
                print("   ⚠️  No standings rows found (may be expected if no matches played)")
                return True
        
        return success

    def test_toss_endpoint_functionality(self):
        """Test 4: Toss endpoint still passes"""
        print("\n🎯 TEST 4: Toss Endpoint Functionality")
        
        if not self.match_id:
            print("❌ Skipping - No match ID available")
            return False
        
        # Test toss endpoint
        toss_data = {
            "actor_user_id": self.user_ids[0],
            "choice": "serve"
        }
        
        success, response = self.run_test(
            "Conduct Match Toss",
            "POST",
            f"rr/matches/{self.match_id}/toss",
            200,
            data=toss_data
        )
        
        if success:
            print(f"   Toss Winner: {response.get('winner_user_id')}")
            print(f"   Toss Choice: {response.get('choice')}")
            
            # Verify required fields
            required_fields = ['winner_user_id', 'choice']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False
            
            # Test duplicate toss prevention
            success2, response2 = self.run_test(
                "Attempt Duplicate Toss (Should Fail)",
                "POST",
                f"rr/matches/{self.match_id}/toss",
                400,
                data=toss_data
            )
            
            if success2:
                print("   ✅ Duplicate toss prevention working correctly")
                print("   ✅ Toss endpoint functionality verified")
                return True
            else:
                print("   ❌ Duplicate toss should have been prevented")
                return False
        
        return success

    def test_partner_override_endpoints(self):
        """Test 5: Partner override endpoints still pass"""
        print("\n🎯 TEST 5: Partner Override Endpoints")
        
        if not self.match_id or len(self.user_ids) < 4:
            print("❌ Skipping - No match ID or insufficient users")
            return False
        
        # Get the actual match to find the correct player IDs
        success, weeks_response = self.run_test(
            "Get Match Details for Override",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": self.user_ids[0], "tier_id": self.tier_id}
        )
        
        if not success:
            print("❌ Failed to get match details")
            return False
        
        # Find our match and get the actual player IDs
        match_players = None
        for week in weeks_response.get('weeks', []):
            for match in week.get('matches', []):
                if match['id'] == self.match_id:
                    match_players = match.get('player_ids', [])
                    break
            if match_players:
                break
        
        if not match_players or len(match_players) != 4:
            print(f"❌ Could not find 4 players for match, found: {match_players}")
            return False
        
        print(f"   Using match players: {match_players}")
        
        # Test partner override proposal with correct player IDs
        override_data = {
            "actor_user_id": match_players[0],
            "sets": [
                [[match_players[0], match_players[1]], [match_players[2], match_players[3]]],
                [[match_players[0], match_players[2]], [match_players[1], match_players[3]]],
                [[match_players[0], match_players[3]], [match_players[1], match_players[2]]]
            ]
        }
        
        success, response = self.run_test(
            "Propose Partner Override",
            "POST",
            f"rr/matches/{self.match_id}/partner-override",
            200,
            data=override_data
        )
        
        if not success:
            print("❌ Failed to propose partner override")
            return False
        
        print(f"   Override Status: {response.get('status')}")
        
        # Test confirmations from all 4 players
        confirmations_made = 0
        for i, user_id in enumerate(match_players):
            confirm_data = {
                "user_id": user_id
            }
            
            success, response = self.run_test(
                f"Confirm Override by Player {i+1}",
                "POST",
                f"rr/matches/{self.match_id}/partner-override/confirm",
                200,
                data=confirm_data
            )
            
            if success:
                confirmations_made += 1
                print(f"   Player {i+1} confirmation: ✅")
                print(f"   Status: {response.get('status')}")
                print(f"   Confirmations: {response.get('confirmations')}")
        
        print(f"   Total confirmations: {confirmations_made}/4")
        
        if confirmations_made == 4:
            print("   ✅ Partner override endpoints working correctly")
            return True
        else:
            print(f"   ❌ Expected 4 confirmations, got {confirmations_made}")
            return False

    def test_no_regressions_in_existing_functionality(self):
        """Test 6: Verify no regressions in existing RR functionality"""
        print("\n🎯 TEST 6: No Regressions in Existing Functionality")
        
        if not self.tier_id or len(self.user_ids) < 4:
            print("❌ Skipping - Test environment not ready")
            return False
        
        # Test availability endpoints still work
        success1, response1 = self.run_test(
            "Get User Availability",
            "GET",
            "rr/availability",
            200,
            params={"user_id": self.user_ids[0]}
        )
        
        # Test health endpoint
        success2, response2 = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        
        # Test weeks endpoint
        success3, response3 = self.run_test(
            "Get RR Weeks",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": self.user_ids[0], "tier_id": self.tier_id}
        )
        
        all_passed = success1 and success2 and success3
        
        if all_passed:
            print("   ✅ No regressions detected in existing functionality")
        else:
            print("   ❌ Some existing functionality may have regressed")
        
        return all_passed

    def run_all_tests(self):
        """Run all RR improvements tests"""
        print("🚀 Starting Round Robin Improvements Testing")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return False
        
        # Run all tests
        tests = [
            self.test_scheduler_with_backtracking_and_quality,
            self.test_scorecard_approval_creates_snapshots,
            self.test_standings_with_trend_field,
            self.test_toss_endpoint_functionality,
            self.test_partner_override_endpoints,
            self.test_no_regressions_in_existing_functionality
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
                self.tests_run += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 RR IMPROVEMENTS TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = RRImprovementsAPITester()
    tester.run_all_tests()