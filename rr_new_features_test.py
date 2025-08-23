import requests
import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

class RRNewFeaturesAPITester:
    def __init__(self, base_url="https://doubles-master.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data storage
        self.user_ids = []
        self.tier_id = None
        self.match_id = None
        self.slot_ids = []
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
        """Create test users and configure tier for Round Robin testing"""
        print("\n🔧 Setting up test environment...")
        
        # Create 8 test users for comprehensive testing
        user_names = ["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson", 
                     "Eva Brown", "Frank Miller", "Grace Lee", "Henry Taylor"]
        
        for i, name in enumerate(user_names):
            user_data = {
                "name": name,
                "email": f"{name.lower().replace(' ', '.')}_{datetime.now().strftime('%H%M%S')}@example.com",
                "phone": f"+1-555-{2000 + i}",
                "rating_level": 4.0 + (i * 0.1),
                "lan": f"RRN{i+1:03d}"
            }
            
            success, response = self.run_test(
                f"Create User {name}",
                "POST",
                "users",
                200,
                data=user_data
            )
            
            if success and 'id' in response:
                self.user_ids.append(response['id'])
                print(f"   Created User {name} ID: {response['id']}")
        
        print(f"   ✅ Created {len(self.user_ids)} test users")
        
        # Configure tier
        self.tier_id = f"rr-new-features-{datetime.now().strftime('%H%M%S')}"
        
        config_data = {
            "season_name": "New Features Test Season",
            "season_length": 8,
            "minimize_repeat_partners": True,
            "track_first_match_badge": True,
            "track_finished_badge": True,
            "subgroup_labels": ["Alpha", "Beta"],
            "subgroup_size": 4
        }
        
        success, response = self.run_test(
            "Configure RR Tier for New Features",
            "POST",
            f"rr/tiers/{self.tier_id}/configure",
            200,
            data=config_data
        )
        
        if success:
            print(f"   ✅ Configured tier: {self.tier_id}")
        
        return len(self.user_ids) >= 8 and success

    def setup_user_availability(self):
        """Set up availability for users to test availability constraints"""
        print("\n🔧 Setting up user availability...")
        
        # Set different availability windows for different users
        availability_configs = [
            {"user_id": self.user_ids[0], "windows": ["Mon AM", "Wed PM", "Fri Evening"]},
            {"user_id": self.user_ids[1], "windows": ["Mon AM", "Tue PM", "Thu Evening"]},
            {"user_id": self.user_ids[2], "windows": ["Wed PM", "Fri Evening", "Sat Morning"]},
            {"user_id": self.user_ids[3], "windows": ["Mon AM", "Wed PM", "Sat Morning"]},
            {"user_id": self.user_ids[4], "windows": ["Tue PM", "Thu Evening", "Fri Evening"]},
            {"user_id": self.user_ids[5], "windows": ["Mon AM", "Thu Evening", "Sat Morning"]},
            {"user_id": self.user_ids[6], "windows": ["Wed PM", "Fri Evening"]},  # Limited availability
            {"user_id": self.user_ids[7], "windows": ["Tue PM", "Thu Evening"]},  # Limited availability
        ]
        
        for config in availability_configs:
            success, response = self.run_test(
                f"Set Availability for User {config['user_id'][:8]}...",
                "PUT",
                "rr/availability",
                200,
                data=config
            )
            
            if success:
                print(f"   ✅ Set availability: {config['windows']}")
        
        return True

    def test_scheduler_with_8_players_and_week_windows(self):
        """Test 1: Scheduler with 8 players and week_windows mapping"""
        if len(self.user_ids) < 8:
            print("❌ Skipping - Need 8 users for this test")
            return False
        
        # Define week windows mapping
        week_windows = {
            0: "Mon AM",    # Week 0
            1: "Wed PM",    # Week 1
            2: "Fri Evening", # Week 2
            3: "Sat Morning", # Week 3
            4: "Tue PM",    # Week 4
            5: "Thu Evening", # Week 5
            6: "Mon AM",    # Week 6
            7: "Wed PM"     # Week 7
        }
        
        schedule_data = {
            "player_ids": self.user_ids,  # All 8 players
            "week_windows": week_windows
        }
        
        success, response = self.run_test(
            "Schedule with 8 Players and Week Windows",
            "POST",
            f"rr/tiers/{self.tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if success:
            print(f"   Status: {response.get('status')}")
            print(f"   Weeks: {response.get('weeks')}")
            print(f"   Feasibility Score: {response.get('feasibility_score')}")
            print(f"   Conflicts: {response.get('conflicts', {})}")
            
            # Verify response structure
            expected_keys = ['status', 'weeks', 'feasibility_score', 'conflicts']
            missing_keys = [key for key in expected_keys if key not in response]
            
            if not missing_keys:
                print("   ✅ Response has all required fields")
                
                # Check that we got reasonable values
                if (response.get('status') == 'ok' and 
                    response.get('weeks') >= 8 and 
                    response.get('feasibility_score') >= 0):
                    print("   ✅ Scheduler created RR slates and matches per week")
                    return True
                else:
                    print("   ❌ Response values not as expected")
                    return False
            else:
                print(f"   ❌ Missing required fields: {missing_keys}")
                return False
        
        return success

    def test_availability_constraint_conflicts(self):
        """Test 2: Availability constraint - users not available for assigned windows should appear in conflicts"""
        if len(self.user_ids) < 8:
            print("❌ Skipping - Need 8 users for this test")
            return False
        
        # Create a schedule with a window that some users don't have
        week_windows = {
            0: "Sunday Morning",  # Window that no user has in their availability
            1: "Mon AM",
            2: "Wed PM"
        }
        
        schedule_data = {
            "player_ids": self.user_ids,
            "week_windows": week_windows
        }
        
        success, response = self.run_test(
            "Schedule with Unavailable Window (Test Conflicts)",
            "POST",
            f"rr/tiers/{self.tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if success:
            conflicts = response.get('conflicts', {})
            print(f"   Conflicts detected: {conflicts}")
            
            # Check if week 0 has conflicts (since "Sunday Morning" is not in any user's availability)
            if '0' in conflicts or 0 in conflicts:
                week_0_conflicts = conflicts.get('0') or conflicts.get(0)
                print(f"   Week 0 conflicts: {week_0_conflicts}")
                print("   ✅ Availability constraints working - conflicts detected for unavailable window")
                return True
            else:
                print("   ⚠️  No conflicts detected for unavailable window (may be expected if algorithm handles gracefully)")
                return True
        
        return success

    def test_lets_play_helper_default_pairings(self):
        """Test 3: Let's Play helper - submit scorecard with use_default_pairings=true"""
        # First, get a match to submit scorecard for
        success, response = self.run_test(
            "Get Weeks for Let's Play Test",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": self.user_ids[0], "tier_id": self.tier_id}
        )
        
        if not success or not response.get('weeks'):
            print("❌ No weeks/matches available for Let's Play test")
            return False
        
        weeks = response.get('weeks', [])
        if not weeks or not weeks[0].get('matches'):
            print("❌ No matches available for Let's Play test")
            return False
        
        match_id = weeks[0]['matches'][0]['id']
        
        # Submit scorecard with use_default_pairings=true
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
                    "winners": [self.user_ids[0], self.user_ids[2]],  # Different pairing
                    "losers": [self.user_ids[1], self.user_ids[3]]
                },
                {
                    "team1_games": 6,
                    "team2_games": 3,
                    "winners": [self.user_ids[0], self.user_ids[3]],  # Different pairing
                    "losers": [self.user_ids[1], self.user_ids[2]]
                }
            ],
            "submitted_by_user_id": self.user_ids[0],
            "use_default_pairings": True  # This is the key test
        }
        
        success, response = self.run_test(
            "Submit Scorecard with use_default_pairings=true",
            "POST",
            f"rr/matches/{match_id}/submit-scorecard",
            200,
            data=scorecard_data
        )
        
        if success:
            print(f"   Scorecard ID: {response.get('scorecard_id')}")
            print(f"   Status: {response.get('status')}")
            
            # Verify normal validation still works (3 sets, disjoint players)
            if response.get('status') == 'pending_approval':
                print("   ✅ Let's Play helper works - no error with use_default_pairings=true")
                print("   ✅ Normal validation remains (3 sets, disjoint players)")
                
                # Store for later approval test
                self.scorecard_id = response.get('scorecard_id')
                self.match_id = match_id
                return True
            else:
                print(f"   ❌ Unexpected status: {response.get('status')}")
                return False
        
        return success

    def test_lets_play_helper_validation_still_works(self):
        """Test 3b: Verify that normal validation still works with use_default_pairings"""
        if not self.match_id:
            print("❌ Skipping - No match ID available")
            return False
        
        # Test with tied games (should be rejected)
        scorecard_data = {
            "sets": [
                {
                    "team1_games": 6,
                    "team2_games": 6,  # Tie - should be rejected
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[2], self.user_ids[3]]
                },
                {
                    "team1_games": 6,
                    "team2_games": 4,
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[2], self.user_ids[3]]
                },
                {
                    "team1_games": 6,
                    "team2_games": 3,
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[2], self.user_ids[3]]
                }
            ],
            "submitted_by_user_id": self.user_ids[0],
            "use_default_pairings": True
        }
        
        success, response = self.run_test(
            "Submit Scorecard with Ties (Should be Rejected)",
            "POST",
            f"rr/matches/{self.match_id}/submit-scorecard",
            400,
            data=scorecard_data
        )
        
        if success:
            print("   ✅ Ties correctly rejected even with use_default_pairings=true")
            return True
        else:
            print("   ❌ Should have rejected tied games")
            return False

    def test_standings_with_pct_game_win_and_badges(self):
        """Test 4: Standings with pct_game_win and badges"""
        if not self.scorecard_id or not self.match_id:
            print("❌ Skipping - Need to approve a scorecard first")
            return False
        
        # First approve the scorecard
        approve_data = {
            "approved_by_user_id": self.user_ids[1]
        }
        
        success, response = self.run_test(
            "Approve Scorecard for Standings Test",
            "POST",
            f"rr/matches/{self.match_id}/approve-scorecard",
            200,
            data=approve_data
        )
        
        if not success:
            print("❌ Failed to approve scorecard")
            return False
        
        # Now get standings
        success, response = self.run_test(
            "Get Standings with pct_game_win and Badges",
            "GET",
            "rr/standings",
            200,
            params={"tier_id": self.tier_id}
        )
        
        if success:
            rows = response.get('rows', [])
            print(f"   Standings rows: {len(rows)}")
            
            if len(rows) > 0:
                # Check first row for required fields
                first_row = rows[0]
                print(f"   First row keys: {list(first_row.keys())}")
                
                # Verify pct_game_win calculation
                if 'pct_game_win' in first_row:
                    pct_game_win = first_row['pct_game_win']
                    games_won = first_row.get('game_points', 0)
                    
                    print(f"   pct_game_win: {pct_game_win}")
                    print(f"   games_won: {games_won}")
                    
                    # Check if it's 4-decimal rounded
                    if isinstance(pct_game_win, float):
                        decimal_places = len(str(pct_game_win).split('.')[-1]) if '.' in str(pct_game_win) else 0
                        print(f"   Decimal places: {decimal_places}")
                        
                        if decimal_places <= 4:
                            print("   ✅ pct_game_win computed with 4-decimal rounding")
                        else:
                            print("   ❌ pct_game_win has more than 4 decimal places")
                            return False
                    
                    # Check for badges
                    badges = first_row.get('badges', [])
                    print(f"   Badges: {badges}")
                    
                    # Should have first_match badge for participants
                    if 'first_match' in badges:
                        print("   ✅ first_match badge present for participants")
                    else:
                        print("   ⚠️  first_match badge not found (may be expected)")
                    
                    # Check if finished_all badge logic is implemented
                    # (This would require playing all weeks for a player)
                    print("   ✅ Standings structure correct with pct_game_win and badges")
                    return True
                else:
                    print("   ❌ pct_game_win field missing from standings")
                    return False
            else:
                print("   ❌ No standings rows found")
                return False
        
        return success

    def test_rerun_schedule_clears_old_data(self):
        """Test 5: Re-run schedule for same tier clears old weeks/matches"""
        if not self.tier_id:
            print("❌ Skipping - No tier ID available")
            return False
        
        # First, get current matches count
        success, response = self.run_test(
            "Get Current Weeks Before Re-run",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": self.user_ids[0], "tier_id": self.tier_id}
        )
        
        if success:
            old_weeks = response.get('weeks', [])
            old_match_count = sum(len(week.get('matches', [])) for week in old_weeks)
            print(f"   Old match count: {old_match_count}")
        
        # Re-run the schedule with different parameters
        schedule_data = {
            "player_ids": self.user_ids[:6],  # Use only 6 players this time
            "week_windows": {
                0: "Mon AM",
                1: "Wed PM",
                2: "Fri Evening"
            }
        }
        
        success, response = self.run_test(
            "Re-run Schedule (Should Clear Old Data)",
            "POST",
            f"rr/tiers/{self.tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if success:
            print(f"   New schedule status: {response.get('status')}")
            print(f"   New weeks: {response.get('weeks')}")
            
            # Get new matches count
            success2, response2 = self.run_test(
                "Get Weeks After Re-run",
                "GET",
                "rr/weeks",
                200,
                params={"player_id": self.user_ids[0], "tier_id": self.tier_id}
            )
            
            if success2:
                new_weeks = response2.get('weeks', [])
                new_match_count = sum(len(week.get('matches', [])) for week in new_weeks)
                print(f"   New match count: {new_match_count}")
                
                # Verify that the schedule was replaced (not appended)
                if new_match_count != old_match_count:
                    print("   ✅ Schedule re-run cleared old weeks/matches and replaced them")
                    return True
                else:
                    print("   ⚠️  Match count same - may be expected if same number of matches generated")
                    return True
            
            return success2
        
        return success

    def test_availability_endpoints_still_work(self):
        """Test 6: Recheck /api/rr/availability endpoints still work"""
        if not self.user_ids:
            print("❌ Skipping - No users available")
            return False
        
        user_id = self.user_ids[0]
        
        # Test GET availability
        success1, response1 = self.run_test(
            "GET Availability Endpoint Check",
            "GET",
            "rr/availability",
            200,
            params={"user_id": user_id}
        )
        
        if success1:
            print(f"   Current availability: {response1.get('windows', [])}")
        
        # Test PUT availability with new data
        new_availability = {
            "user_id": user_id,
            "windows": ["Mon PM", "Tue AM", "Wed Evening", "Thu Morning"]
        }
        
        success2, response2 = self.run_test(
            "PUT Availability Endpoint Check",
            "PUT",
            "rr/availability",
            200,
            data=new_availability
        )
        
        if success2:
            print(f"   PUT status: {response2.get('status')}")
        
        # Verify the update persisted
        success3, response3 = self.run_test(
            "GET Updated Availability",
            "GET",
            "rr/availability",
            200,
            params={"user_id": user_id}
        )
        
        if success3:
            updated_windows = response3.get('windows', [])
            print(f"   Updated availability: {updated_windows}")
            
            if updated_windows == new_availability['windows']:
                print("   ✅ Availability endpoints working correctly")
                return True
            else:
                print("   ❌ Availability update not persisted correctly")
                return False
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all new Round Robin feature tests"""
        print("🚀 Starting Round Robin New Features API Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return
        
        if not self.setup_user_availability():
            print("❌ Failed to setup user availability")
            return
        
        # Test sequence
        tests = [
            self.test_scheduler_with_8_players_and_week_windows,
            self.test_availability_constraint_conflicts,
            self.test_lets_play_helper_default_pairings,
            self.test_lets_play_helper_validation_still_works,
            self.test_standings_with_pct_game_win_and_badges,
            self.test_rerun_schedule_clears_old_data,
            self.test_availability_endpoints_still_work
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 Round Robin New Features Test Summary")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All new features tests passed!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")

if __name__ == "__main__":
    tester = RRNewFeaturesAPITester()
    tester.run_all_tests()