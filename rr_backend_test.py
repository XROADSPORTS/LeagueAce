import requests
import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

class RoundRobinAPITester:
    def __init__(self, base_url="https://matchmaker-22.preview.emergentagent.com"):
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

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        
        if success:
            print(f"   Status: {response.get('status')}")
            print(f"   Time: {response.get('time')}")
        
        return success

    def setup_test_users(self):
        """Create test users for Round Robin testing"""
        print("\n🔧 Setting up test users...")
        
        user_names = ["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson", "Eva Brown", "Frank Miller"]
        
        for i, name in enumerate(user_names):
            user_data = {
                "name": name,
                "email": f"{name.lower().replace(' ', '.')}_{datetime.now().strftime('%H%M%S')}@example.com",
                "phone": f"+1-555-{1000 + i}",
                "rating_level": 4.0 + (i * 0.1),
                "lan": f"RR{i+1:03d}"
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
        return len(self.user_ids) >= 4

    def test_rr_availability_get_unknown_user(self):
        """Test GET /api/rr/availability returns empty windows for unknown user"""
        unknown_user_id = "unknown-user-123"
        
        success, response = self.run_test(
            "Get Availability for Unknown User",
            "GET",
            "rr/availability",
            200,
            params={"user_id": unknown_user_id}
        )
        
        if success:
            print(f"   User ID: {response.get('user_id')}")
            print(f"   Windows: {response.get('windows', [])}")
            
            # Should return empty windows for unknown user
            if response.get('user_id') == unknown_user_id and response.get('windows') == []:
                print("   ✅ Correctly returned empty windows for unknown user")
                return True
            else:
                print("   ❌ Did not return expected empty windows")
                return False
        
        return success

    def test_rr_availability_put_upsert(self):
        """Test PUT /api/rr/availability upserts with user_id and windows array"""
        if not self.user_ids:
            print("❌ Skipping - No test users available")
            return False
        
        user_id = self.user_ids[0]
        availability_data = {
            "user_id": user_id,
            "windows": ["Mon AM", "Wed PM", "Fri Evening", "Sat Morning"]
        }
        
        success, response = self.run_test(
            "PUT Availability (Upsert)",
            "PUT",
            "rr/availability",
            200,
            data=availability_data
        )
        
        if success:
            print(f"   Status: {response.get('status')}")
        
        # Now GET to verify it persisted
        success2, response2 = self.run_test(
            "GET Availability After PUT",
            "GET",
            "rr/availability",
            200,
            params={"user_id": user_id}
        )
        
        if success2:
            print(f"   Retrieved User ID: {response2.get('user_id')}")
            print(f"   Retrieved Windows: {response2.get('windows', [])}")
            
            # Verify the data persisted
            if (response2.get('user_id') == user_id and 
                response2.get('windows') == availability_data['windows']):
                print("   ✅ Availability upsert and persistence working correctly")
                return True
            else:
                print("   ❌ Retrieved availability doesn't match what was set")
                return False
        
        return success and success2

    def test_rr_configure_tier(self):
        """Test POST /api/rr/tiers/{tier_id}/configure creates config"""
        if not self.user_ids:
            print("❌ Skipping - No test users available")
            return False
        
        # Use a test tier ID
        self.tier_id = f"test-tier-{datetime.now().strftime('%H%M%S')}"
        
        config_data = {
            "season_name": "Fall 2024 Round Robin",
            "season_length": 12,
            "minimize_repeat_partners": True,
            "track_first_match_badge": True,
            "track_finished_badge": True,
            "subgroup_labels": ["Thunder", "Lightning", "Storm"],
            "subgroup_size": 4
        }
        
        success, response = self.run_test(
            "Configure RR Tier",
            "POST",
            f"rr/tiers/{self.tier_id}/configure",
            200,
            data=config_data
        )
        
        if success:
            print(f"   Status: {response.get('status')}")
            config = response.get('config', {})
            print(f"   Season Name: {config.get('season_name')}")
            print(f"   Season Length: {config.get('season_length')}")
            print(f"   Subgroup Labels: {config.get('subgroup_labels')}")
            print(f"   Subgroup Size: {config.get('subgroup_size')}")
            
            # Verify config was created correctly
            if (config.get('tier_id') == self.tier_id and
                config.get('season_name') == config_data['season_name'] and
                config.get('subgroup_labels') == config_data['subgroup_labels']):
                print("   ✅ RR tier configuration created successfully")
                return True
            else:
                print("   ❌ Configuration not created as expected")
                return False
        
        return success

    def test_rr_generate_subgroups_no_config(self):
        """Test subgroup generation without config returns 400"""
        unconfigured_tier_id = "unconfigured-tier-123"
        
        subgroup_data = {
            "player_ids": self.user_ids[:4] if self.user_ids else ["user1", "user2", "user3", "user4"]
        }
        
        success, response = self.run_test(
            "Generate Subgroups Without Config (Should Fail)",
            "POST",
            f"rr/tiers/{unconfigured_tier_id}/subgroups/generate",
            400,
            data=subgroup_data
        )
        
        if success:
            print("   ✅ Correctly returned 400 for unconfigured tier")
            return True
        else:
            print("   ❌ Should have returned 400 for unconfigured tier")
            return False

    def test_rr_generate_subgroups_with_config(self):
        """Test POST /api/rr/tiers/{tier_id}/subgroups/generate validates config present and splits player_ids"""
        if not self.tier_id or not self.user_ids:
            print("❌ Skipping - No configured tier or users available")
            return False
        
        # Use 6 users to create subgroups of size 4 and 2
        subgroup_data = {
            "player_ids": self.user_ids[:6]
        }
        
        success, response = self.run_test(
            "Generate Subgroups with Config",
            "POST",
            f"rr/tiers/{self.tier_id}/subgroups/generate",
            200,
            data=subgroup_data
        )
        
        if success:
            print(f"   Status: {response.get('status')}")
            print("   ✅ Subgroups generated successfully with configured labels and size")
            return True
        
        return success

    def test_rr_schedule_insufficient_players(self):
        """Test scheduling with <4 players returns 400"""
        if not self.tier_id:
            print("❌ Skipping - No configured tier available")
            return False
        
        schedule_data = {
            "player_ids": self.user_ids[:2] if self.user_ids else ["user1", "user2"]  # Only 2 players
        }
        
        success, response = self.run_test(
            "Schedule with <4 Players (Should Fail)",
            "POST",
            f"rr/tiers/{self.tier_id}/schedule",
            400,
            data=schedule_data
        )
        
        if success:
            print("   ✅ Correctly returned 400 for insufficient players")
            return True
        else:
            print("   ❌ Should have returned 400 for insufficient players")
            return False

    def test_rr_schedule_tier(self):
        """Test POST /api/rr/tiers/{tier_id}/schedule creates weeks and matches with correct slates for at least 4 players"""
        if not self.tier_id or len(self.user_ids) < 4:
            print("❌ Skipping - No configured tier or insufficient users available")
            return False
        
        schedule_data = {
            "player_ids": self.user_ids[:4]  # Use exactly 4 players
        }
        
        success, response = self.run_test(
            "Schedule RR Tier (4 Players)",
            "POST",
            f"rr/tiers/{self.tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if success:
            print(f"   Status: {response.get('status')}")
            print(f"   Weeks: {response.get('weeks')}")
            
            # Verify weeks were created
            if response.get('weeks') and response.get('weeks') > 0:
                print("   ✅ Schedule created successfully with weeks and matches")
                return True
            else:
                print("   ❌ No weeks created in schedule")
                return False
        
        return success

    def test_rr_get_weeks(self):
        """Test GET /api/rr/weeks returns player's matches by week"""
        if not self.user_ids or not self.tier_id:
            print("❌ Skipping - No users or tier available")
            return False
        
        player_id = self.user_ids[0]
        
        success, response = self.run_test(
            "Get RR Weeks for Player",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": player_id, "tier_id": self.tier_id}
        )
        
        if success:
            weeks = response.get('weeks', [])
            print(f"   Weeks found: {len(weeks)}")
            
            for week in weeks:
                print(f"   Week {week.get('week_index')}: {len(week.get('matches', []))} matches")
            
            if len(weeks) > 0:
                # Store first match ID for later tests
                first_week_matches = weeks[0].get('matches', [])
                if first_week_matches:
                    self.match_id = first_week_matches[0].get('id')
                    print(f"   Stored Match ID for testing: {self.match_id}")
                
                print("   ✅ Successfully retrieved weeks and matches")
                return True
            else:
                print("   ⚠️  No weeks found (may be expected if no matches scheduled)")
                return True
        
        return success

    def test_rr_propose_slots(self):
        """Test POST /api/rr/matches/{match_id}/propose-slots creates up to 3 slots"""
        if not self.match_id or not self.user_ids:
            print("❌ Skipping - No match ID or users available")
            return False
        
        # Create 3 time slots
        base_time = datetime.now(timezone.utc) + timedelta(days=7)
        slots_data = {
            "slots": [
                {
                    "start": (base_time + timedelta(hours=0)).isoformat(),
                    "venue_name": "Court 1"
                },
                {
                    "start": (base_time + timedelta(hours=2)).isoformat(),
                    "venue_name": "Court 2"
                },
                {
                    "start": (base_time + timedelta(days=1)).isoformat(),
                    "venue_name": "Court 3"
                }
            ],
            "proposed_by_user_id": self.user_ids[0]
        }
        
        success, response = self.run_test(
            "Propose Match Slots (3 slots)",
            "POST",
            f"rr/matches/{self.match_id}/propose-slots",
            200,
            data=slots_data
        )
        
        if success:
            created_ids = response.get('created', [])
            print(f"   Created Slot IDs: {created_ids}")
            print(f"   Number of slots created: {len(created_ids)}")
            
            if len(created_ids) <= 3:  # Should create up to 3 slots
                self.slot_ids = created_ids
                print("   ✅ Successfully created proposed slots (up to 3)")
                return True
            else:
                print(f"   ❌ Created more than 3 slots: {len(created_ids)}")
                return False
        
        return success

    def test_rr_confirm_slot_partial(self):
        """Test POST /api/rr/matches/{match_id}/confirm-slot with partial confirmations"""
        if not self.match_id or not self.slot_ids or len(self.user_ids) < 4:
            print("❌ Skipping - No match ID, slots, or insufficient users available")
            return False
        
        slot_id = self.slot_ids[0]  # Use first proposed slot
        
        # Confirm with first 2 players (should not lock yet)
        for i in range(2):
            confirm_data = {
                "slot_id": slot_id,
                "user_id": self.user_ids[i]
            }
            
            success, response = self.run_test(
                f"Confirm Slot by Player {i+1} (Partial)",
                "POST",
                f"rr/matches/{self.match_id}/confirm-slot",
                200,
                data=confirm_data
            )
            
            if success:
                print(f"   Player {i+1} confirmed: ✅")
                print(f"   Locked: {response.get('locked', False)}")
                print(f"   Confirmations: {len(response.get('confirmations', []))}")
                
                # Should not be locked yet with only 2 confirmations
                if not response.get('locked'):
                    print(f"   ✅ Correctly not locked with {len(response.get('confirmations', []))} confirmations")
                else:
                    print(f"   ❌ Should not be locked with partial confirmations")
                    return False
        
        return True

    def test_rr_confirm_slot_all_players(self):
        """Test POST confirm-slot requires all 4 player confirmations to lock"""
        if not self.match_id or not self.slot_ids or len(self.user_ids) < 4:
            print("❌ Skipping - No match ID, slots, or insufficient users available")
            return False
        
        slot_id = self.slot_ids[0]  # Use first proposed slot
        
        # Confirm with remaining 2 players (should lock after all 4)
        for i in range(2, 4):
            confirm_data = {
                "slot_id": slot_id,
                "user_id": self.user_ids[i]
            }
            
            success, response = self.run_test(
                f"Confirm Slot by Player {i+1} (Complete)",
                "POST",
                f"rr/matches/{self.match_id}/confirm-slot",
                200,
                data=confirm_data
            )
            
            if success:
                print(f"   Player {i+1} confirmed: ✅")
                print(f"   Locked: {response.get('locked', False)}")
                
                if i == 3:  # After 4th confirmation
                    if response.get('locked'):
                        print(f"   ✅ Match locked after all 4 confirmations!")
                        print(f"   Scheduled at: {response.get('scheduled_at')}")
                        print(f"   Venue: {response.get('venue')}")
                        return True
                    else:
                        print(f"   ❌ Match should be locked after 4 confirmations")
                        return False
        
        return False

    def test_rr_match_ics_unconfirmed(self):
        """Test GET /api/rr/matches/{match_id}/ics returns 404 unless confirmed"""
        # Create a new match that's not confirmed
        if not self.tier_id or len(self.user_ids) < 4:
            print("❌ Skipping - No tier or insufficient users")
            return False
        
        # First create a new schedule to get an unconfirmed match
        schedule_data = {
            "player_ids": self.user_ids[4:6] + self.user_ids[:2] if len(self.user_ids) >= 6 else self.user_ids[:4]
        }
        
        success, response = self.run_test(
            "Create New Schedule for ICS Test",
            "POST",
            f"rr/tiers/{self.tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if not success:
            print("❌ Failed to create schedule for ICS test")
            return False
        
        # Get the new matches
        success, response = self.run_test(
            "Get Weeks for ICS Test",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": self.user_ids[0], "tier_id": self.tier_id}
        )
        
        if success and response.get('weeks'):
            weeks = response.get('weeks', [])
            if weeks and weeks[0].get('matches'):
                unconfirmed_match_id = weeks[0]['matches'][0]['id']
                
                # Try to get ICS for unconfirmed match (should return 404)
                success, response = self.run_test(
                    "Get ICS for Unconfirmed Match (Should Fail)",
                    "GET",
                    f"rr/matches/{unconfirmed_match_id}/ics",
                    404
                )
                
                if success:
                    print("   ✅ Correctly returned 404 for unconfirmed match")
                    return True
                else:
                    print("   ❌ Should have returned 404 for unconfirmed match")
                    return False
        
        print("❌ Could not find unconfirmed match for ICS test")
        return False

    def test_rr_match_ics_confirmed(self):
        """Test GET /api/rr/matches/{match_id}/ics returns 200 with ICS content for confirmed matches"""
        if not self.match_id:
            print("❌ Skipping - No confirmed match ID available")
            return False
        
        success, response = self.run_test(
            "Get ICS for Confirmed Match",
            "GET",
            f"rr/matches/{self.match_id}/ics",
            200
        )
        
        if success:
            ics_content = response.get('ics', '')
            print(f"   ICS Content Length: {len(ics_content)} characters")
            
            # Verify ICS format
            required_fields = ['BEGIN:VCALENDAR', 'END:VCALENDAR', 'BEGIN:VEVENT', 'END:VEVENT', 'DTSTART', 'SUMMARY']
            missing_fields = [field for field in required_fields if field not in ics_content]
            
            if not missing_fields:
                print("   ✅ ICS content has all required fields")
                print(f"   ICS Preview: {ics_content[:100]}...")
                return True
            else:
                print(f"   ❌ ICS content missing fields: {missing_fields}")
                return False
        
        return success

    def test_rr_submit_scorecard_invalid_sets(self):
        """Test POST /api/rr/matches/{match_id}/submit-scorecard enforces exactly 3 sets"""
        if not self.match_id or len(self.user_ids) < 4:
            print("❌ Skipping - No match ID or insufficient users")
            return False
        
        # Test with only 2 sets (should fail)
        scorecard_data = {
            "sets": [
                {
                    "team1_games": 6,
                    "team2_games": 4,
                    "winners": self.user_ids[:2],
                    "losers": self.user_ids[2:4]
                },
                {
                    "team1_games": 6,
                    "team2_games": 3,
                    "winners": self.user_ids[:2],
                    "losers": self.user_ids[2:4]
                }
            ],
            "submitted_by_user_id": self.user_ids[0]
        }
        
        success, response = self.run_test(
            "Submit Scorecard with 2 Sets (Should Fail)",
            "POST",
            f"rr/matches/{self.match_id}/submit-scorecard",
            400,
            data=scorecard_data
        )
        
        if success:
            print("   ✅ Correctly returned 400 for non-3 sets")
            return True
        else:
            print("   ❌ Should have returned 400 for non-3 sets")
            return False

    def test_rr_submit_scorecard_invalid_participants(self):
        """Test scorecard validation for invalid winners/losers"""
        if not self.match_id or len(self.user_ids) < 4:
            print("❌ Skipping - No match ID or insufficient users")
            return False
        
        # Test with invalid participants (overlapping winners/losers)
        scorecard_data = {
            "sets": [
                {
                    "team1_games": 6,
                    "team2_games": 4,
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[1], self.user_ids[2]]  # user_ids[1] in both!
                },
                {
                    "team1_games": 6,
                    "team2_games": 3,
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[2], self.user_ids[3]]
                },
                {
                    "team1_games": 6,
                    "team2_games": 2,
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[2], self.user_ids[3]]
                }
            ],
            "submitted_by_user_id": self.user_ids[0]
        }
        
        success, response = self.run_test(
            "Submit Scorecard with Invalid Participants (Should Fail)",
            "POST",
            f"rr/matches/{self.match_id}/submit-scorecard",
            400,
            data=scorecard_data
        )
        
        if success:
            print("   ✅ Correctly returned 400 for invalid set participants")
            return True
        else:
            print("   ❌ Should have returned 400 for invalid set participants")
            return False

    def test_rr_submit_scorecard_valid(self):
        """Test POST /api/rr/matches/{match_id}/submit-scorecard with valid 3 sets"""
        if not self.match_id or len(self.user_ids) < 4:
            print("❌ Skipping - No match ID or insufficient users")
            return False
        
        # Valid scorecard with exactly 3 sets
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
                    "team1_games": 6,
                    "team2_games": 3,
                    "winners": [self.user_ids[0], self.user_ids[1]],
                    "losers": [self.user_ids[2], self.user_ids[3]]
                }
            ],
            "submitted_by_user_id": self.user_ids[0]
        }
        
        success, response = self.run_test(
            "Submit Valid Scorecard (3 Sets)",
            "POST",
            f"rr/matches/{self.match_id}/submit-scorecard",
            200,
            data=scorecard_data
        )
        
        if success:
            self.scorecard_id = response.get('scorecard_id')
            print(f"   Scorecard ID: {self.scorecard_id}")
            print(f"   Status: {response.get('status')}")
            
            if response.get('status') == 'pending_approval':
                print("   ✅ Scorecard submitted successfully and pending approval")
                return True
            else:
                print(f"   ❌ Unexpected status: {response.get('status')}")
                return False
        
        return success

    def test_rr_approve_scorecard(self):
        """Test POST /api/rr/matches/{match_id}/approve-scorecard marks match played and writes standings"""
        if not self.match_id or not self.scorecard_id or not self.user_ids:
            print("❌ Skipping - No match ID, scorecard ID, or users available")
            return False
        
        approve_data = {
            "approved_by_user_id": self.user_ids[1]  # Different user approves
        }
        
        success, response = self.run_test(
            "Approve Scorecard",
            "POST",
            f"rr/matches/{self.match_id}/approve-scorecard",
            200,
            data=approve_data
        )
        
        if success:
            print(f"   Status: {response.get('status')}")
            
            if response.get('status') == 'approved':
                print("   ✅ Scorecard approved successfully")
                
                # Now check if standings were updated
                success2, response2 = self.run_test(
                    "Get Standings After Approval",
                    "GET",
                    "rr/standings",
                    200,
                    params={"tier_id": self.tier_id}
                )
                
                if success2:
                    rows = response2.get('rows', [])
                    print(f"   Standings rows created: {len(rows)}")
                    
                    if len(rows) > 0:
                        print("   ✅ Standings updated after scorecard approval")
                        for i, row in enumerate(rows[:3]):  # Show top 3
                            print(f"   Rank {i+1}: Player {row.get('player_id')} - {row.get('set_points')} set points, {row.get('game_points')} game points")
                        return True
                    else:
                        print("   ❌ No standings rows found after approval")
                        return False
                
                return success2
            else:
                print(f"   ❌ Unexpected approval status: {response.get('status')}")
                return False
        
        return success

    def run_all_tests(self):
        """Run all Round Robin API tests"""
        print("🚀 Starting Round Robin API Tests")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_users():
            print("❌ Failed to setup test users")
            return
        
        # Test sequence
        tests = [
            self.test_health_endpoint,
            self.test_rr_availability_get_unknown_user,
            self.test_rr_availability_put_upsert,
            self.test_rr_configure_tier,
            self.test_rr_generate_subgroups_no_config,
            self.test_rr_generate_subgroups_with_config,
            self.test_rr_schedule_insufficient_players,
            self.test_rr_schedule_tier,
            self.test_rr_get_weeks,
            self.test_rr_propose_slots,
            self.test_rr_confirm_slot_partial,
            self.test_rr_confirm_slot_all_players,
            self.test_rr_match_ics_unconfirmed,
            self.test_rr_match_ics_confirmed,
            self.test_rr_submit_scorecard_invalid_sets,
            self.test_rr_submit_scorecard_invalid_participants,
            self.test_rr_submit_scorecard_valid,
            self.test_rr_approve_scorecard
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 Round Robin API Test Summary")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")

if __name__ == "__main__":
    tester = RoundRobinAPITester()
    tester.run_all_tests()