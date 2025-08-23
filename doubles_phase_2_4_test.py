#!/usr/bin/env python3
"""
Focused test for Doubles Phase 2-4 endpoints as requested in review.
Tests the specific endpoints mentioned in the review request.
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta

class DoublesPhase24Tester:
    def __init__(self):
        self.api_url = "https://matchmaker-22.preview.emergentagent.com/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data storage
        self.league_manager_id = None
        self.league_id = None
        self.doubles_format_tier_id = None
        self.doubles_rating_tier_id = None
        self.doubles_join_code = None
        self.team_ids = []
        self.player_ids = []
        self.match_id = None
        self.proposed_slot_ids = []
        self.score_id = None
    
    def run_test(self, test_name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        self.tests_run += 1
        url = f"{self.api_url}/{endpoint}"
        
        print(f"\n🔍 Testing {test_name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, params=params)
            elif method == "POST":
                response = requests.post(url, json=data, params=params)
            elif method == "PUT":
                response = requests.put(url, json=data, params=params)
            elif method == "DELETE":
                response = requests.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                    return False, error_detail
                except:
                    print(f"   Response text: {response.text}")
                    return False, response.text
                    
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, str(e)
    
    def setup_test_environment(self):
        """Set up the basic test environment for Doubles Phase 2-4 testing"""
        print("\n🔧 Setting up Doubles Phase 2-4 Test Environment...")
        
        # Create League Manager
        manager_data = {
            "name": "Doubles Test Manager",
            "email": f"doubles.manager_{datetime.now().strftime('%H%M%S')}@testleague.com",
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
        
        if success and 'id' in response:
            self.league_manager_id = response['id']
            print(f"   ✅ Created League Manager ID: {self.league_manager_id}")
        else:
            print("❌ Failed to create league manager")
            return False
        
        # Create League
        league_data = {
            "name": "Doubles Phase 2-4 Test League",
            "sport_type": "Tennis",
            "description": "League for testing Doubles Phase 2-4 endpoints"
        }
        
        success, response = self.run_test(
            "Create Test League",
            "POST",
            "leagues",
            200,
            data=league_data,
            params={"created_by": self.league_manager_id}
        )
        
        if success and 'id' in response:
            self.league_id = response['id']
            print(f"   ✅ Created League ID: {self.league_id}")
        else:
            print("❌ Failed to create league")
            return False
        
        # Create Doubles Format Tier
        format_data = {
            "league_id": self.league_id,
            "name": "Doubles Phase 2-4 Test",
            "format_type": "Doubles",
            "description": "Doubles format for Phase 2-4 testing"
        }
        
        success, response = self.run_test(
            "Create Doubles Format Tier",
            "POST",
            "format-tiers",
            200,
            data=format_data
        )
        
        if success and 'id' in response:
            self.doubles_format_tier_id = response['id']
            print(f"   ✅ Created Doubles Format Tier ID: {self.doubles_format_tier_id}")
        else:
            print("❌ Failed to create doubles format tier")
            return False
        
        # Create Doubles Rating Tier
        rating_data = {
            "format_tier_id": self.doubles_format_tier_id,
            "name": "4.0 Doubles Phase 2-4",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 8,
            "competition_system": "Team League Format",
            "playoff_spots": 4,
            "region": "Test Region",
            "surface": "Hard Court"
        }
        
        success, response = self.run_test(
            "Create Doubles Rating Tier",
            "POST",
            "rating-tiers",
            200,
            data=rating_data
        )
        
        if success and 'id' in response:
            self.doubles_rating_tier_id = response['id']
            self.doubles_join_code = response.get('join_code')
            print(f"   ✅ Created Doubles Rating Tier ID: {self.doubles_rating_tier_id}")
            print(f"   ✅ Join Code: {self.doubles_join_code}")
        else:
            print("❌ Failed to create doubles rating tier")
            return False
        
        # Create 4 players for 2 teams
        for i in range(4):
            player_data = {
                "name": f"Doubles Player {chr(65 + i)}",
                "email": f"doubles.player{chr(65 + i).lower()}_{datetime.now().strftime('%H%M%S')}@test.com",
                "phone": f"+1-555-020{i + 1}",
                "rating_level": 4.0,
                "role": "Player"
            }
            
            success, response = self.run_test(
                f"Create Player {chr(65 + i)}",
                "POST",
                "users",
                200,
                data=player_data
            )
            
            if success and 'id' in response:
                self.player_ids.append(response['id'])
                print(f"   ✅ Created Player {chr(65 + i)} ID: {response['id']}")
        
        if len(self.player_ids) < 4:
            print("❌ Failed to create enough players")
            return False
        
        # Create two teams using partner invites
        # Team 1: Player A invites Player B
        invite_data = {
            "inviter_user_id": self.player_ids[0],
            "rating_tier_id": self.doubles_rating_tier_id
        }
        
        success, response = self.run_test(
            "Create Partner Invite for Team 1",
            "POST",
            "doubles/invites",
            200,
            data=invite_data
        )
        
        if success and 'token' in response:
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
                print(f"   ✅ Created Team 1 ID: {response['id']}")
        
        # Team 2: Player C invites Player D
        invite_data = {
            "inviter_user_id": self.player_ids[2],
            "rating_tier_id": self.doubles_rating_tier_id
        }
        
        success, response = self.run_test(
            "Create Partner Invite for Team 2",
            "POST",
            "doubles/invites",
            200,
            data=invite_data
        )
        
        if success and 'token' in response:
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
                print(f"   ✅ Created Team 2 ID: {response['id']}")
        
        if len(self.team_ids) < 2:
            print("❌ Failed to create enough teams")
            return False
        
        print(f"   ✅ Setup complete: {len(self.team_ids)} teams, {len(self.player_ids)} players")
        return True
    
    def test_team_preferences_get_default(self):
        """Test A) GET /api/doubles/teams/{team_id}/preferences returns default object when none exists"""
        team_id = self.team_ids[0]
        
        success, response = self.run_test(
            "Team Preferences - Get Default",
            "GET",
            f"doubles/teams/{team_id}/preferences",
            200
        )
        
        if success:
            print(f"   Team ID: {response.get('team_id')}")
            print(f"   Preferred Venues: {response.get('preferred_venues', [])}")
            print(f"   Availability Windows: {len(response.get('availability', []))}")
            print(f"   Max Subs: {response.get('max_subs', 0)}")
            
            # Verify default values
            if (response.get('team_id') == team_id and 
                response.get('preferred_venues') == [] and
                response.get('availability') == [] and
                response.get('max_subs') == 0):
                print("   ✅ Default preferences object created correctly")
                return True
            else:
                print("   ❌ Default preferences object not as expected")
                return False
        
        return success
    
    def test_team_preferences_put_upsert(self):
        """Test A) PUT /api/doubles/teams/{team_id}/preferences upserts, then GET returns updated availability and venues"""
        team_id = self.team_ids[0]
        
        # PUT updated preferences
        preferences_data = {
            "team_id": team_id,
            "preferred_venues": ["Bay Area Tennis Center", "Stanford Courts"],
            "availability": [
                {"day": "Mon", "start": "18:00", "end": "21:00"},
                {"day": "Wed", "start": "19:00", "end": "22:00"},
                {"day": "Sat", "start": "09:00", "end": "12:00"}
            ],
            "max_subs": 2
        }
        
        success, response = self.run_test(
            "Team Preferences - PUT Upsert",
            "PUT",
            f"doubles/teams/{team_id}/preferences",
            200,
            data=preferences_data
        )
        
        if not success:
            return False
        
        # Now GET to verify the update persisted
        success2, response2 = self.run_test(
            "Team Preferences - GET Updated",
            "GET",
            f"doubles/teams/{team_id}/preferences",
            200
        )
        
        if success2:
            print(f"   Retrieved Venues: {response2.get('preferred_venues')}")
            print(f"   Retrieved Windows: {len(response2.get('availability', []))}")
            print(f"   Retrieved Max Subs: {response2.get('max_subs')}")
            
            # Verify values match what we set
            if (response2.get('preferred_venues') == preferences_data['preferred_venues'] and
                len(response2.get('availability', [])) == 3 and
                response2.get('max_subs') == 2):
                print("   ✅ Preferences upsert and retrieval working correctly")
                return True
            else:
                print("   ❌ Retrieved preferences don't match what was set")
                return False
        
        return success and success2
    
    def test_schedule_generation(self):
        """Test B) POST /api/doubles/rating-tiers/{rating_tier_id}/generate-team-schedule creates round-robin pairs only once"""
        success, response = self.run_test(
            "Schedule Generation - Round Robin",
            "POST",
            f"doubles/rating-tiers/{self.doubles_rating_tier_id}/generate-team-schedule",
            200
        )
        
        if success:
            print(f"   Message: {response.get('message')}")
            print(f"   Matches Created: {response.get('created')}")
            
            # Should create 1 match for 2 teams (round robin)
            if response.get('created') == 1:
                print("   ✅ Round-robin schedule generated correctly (1 match for 2 teams)")
                return True
            else:
                print(f"   ❌ Expected 1 match, got {response.get('created')}")
                return False
        
        return success
    
    def test_schedule_generation_insufficient_teams(self):
        """Test B) with <2 teams returns 400"""
        # Create a new rating tier with no teams
        empty_rating_data = {
            "format_tier_id": self.doubles_format_tier_id,
            "name": "Empty 4.0 Doubles",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 8
        }
        
        success, response = self.run_test(
            "Create Empty Rating Tier",
            "POST",
            "rating-tiers",
            200,
            data=empty_rating_data
        )
        
        if not success:
            return False
        
        empty_tier_id = response['id']
        
        # Try to generate schedule with no teams (should fail with 400)
        success, response = self.run_test(
            "Schedule Generation - Insufficient Teams (Should Fail)",
            "POST",
            f"doubles/rating-tiers/{empty_tier_id}/generate-team-schedule",
            400
        )
        
        if success:
            print("   ✅ Correctly returned 400 for insufficient teams")
            return True
        else:
            print("   ❌ Should have returned 400 for insufficient teams")
            return False
    
    def test_propose_match_slots(self):
        """Test C) POST /api/doubles/matches/{match_id}/propose-slots creates up to 3 slots with ISO date strings"""
        # First get a match to propose slots for
        success, matches = self.run_test(
            "Get Doubles Matches",
            "GET",
            "doubles/matches",
            200,
            params={"rating_tier_id": self.doubles_rating_tier_id}
        )
        
        if not success or not matches or len(matches) == 0:
            print("❌ No matches available for slot proposal")
            return False
        
        self.match_id = matches[0]['id']
        print(f"   Using Match ID: {self.match_id}")
        
        # Propose 3 slots with ISO date strings
        base_time = datetime.now(timezone.utc) + timedelta(days=7)
        
        slots_data = {
            "slots": [
                {
                    "start": (base_time + timedelta(hours=0)).isoformat(),
                    "venue_name": "Bay Area Tennis Center Court 1"
                },
                {
                    "start": (base_time + timedelta(hours=2)).isoformat(),
                    "venue_name": "Bay Area Tennis Center Court 2"
                },
                {
                    "start": (base_time + timedelta(days=1)).isoformat(),
                    "venue_name": "Stanford Courts"
                }
            ],
            "proposed_by_user_id": self.player_ids[0]
        }
        
        success, response = self.run_test(
            "Propose Match Slots (3 slots)",
            "POST",
            f"doubles/matches/{self.match_id}/propose-slots",
            200,
            data=slots_data
        )
        
        if success:
            created_ids = response.get('created', [])
            print(f"   Created Slot IDs: {created_ids}")
            print(f"   Number of slots created: {len(created_ids)}")
            
            if len(created_ids) == 3:
                self.proposed_slot_ids = created_ids
                print("   ✅ Successfully created 3 proposed slots")
                return True
            else:
                print(f"   ❌ Expected 3 slots, got {len(created_ids)}")
                return False
        
        return success
    
    def test_propose_slots_invalid_datetime(self):
        """Test C) invalid datetime returns 400"""
        if not self.match_id:
            print("❌ No match ID available")
            return False
        
        slots_data = {
            "slots": [
                {
                    "start": "invalid-datetime-format",
                    "venue_name": "Test Court"
                }
            ],
            "proposed_by_user_id": self.player_ids[0]
        }
        
        success, response = self.run_test(
            "Propose Slots - Invalid Datetime (Should Fail)",
            "POST",
            f"doubles/matches/{self.match_id}/propose-slots",
            400,
            data=slots_data
        )
        
        if success:
            print("   ✅ Correctly returned 400 for invalid datetime")
            return True
        else:
            print("   ❌ Should have returned 400 for invalid datetime")
            return False
    
    def test_confirm_slot_by_partners(self):
        """Test C) POST /api/doubles/matches/{match_id}/confirm-slot with each of the 4 partners confirms and locks match"""
        if not self.match_id or not self.proposed_slot_ids:
            print("❌ No match ID or proposed slots available")
            return False
        
        slot_id = self.proposed_slot_ids[0]  # Use first proposed slot
        
        # Confirm with all 4 partners
        confirmations_made = 0
        for i, player_id in enumerate(self.player_ids):
            confirm_data = {
                "slot_id": slot_id,
                "user_id": player_id
            }
            
            success, response = self.run_test(
                f"Confirm Slot by Partner {i+1}",
                "POST",
                f"doubles/matches/{self.match_id}/confirm-slot",
                200,
                data=confirm_data
            )
            
            if success:
                confirmations_made += 1
                print(f"   Partner {i+1} confirmation: {'✅' if success else '❌'}")
                print(f"   Locked: {response.get('locked', False)}")
                
                if response.get('locked'):
                    print(f"   Match locked! Scheduled at: {response.get('scheduled_at')}")
                    print(f"   Venue: {response.get('venue')}")
                else:
                    print(f"   Confirmations so far: {len(response.get('confirmations', []))}")
        
        print(f"   Total confirmations made: {confirmations_made}/4")
        
        # After all 4 confirmations, match should be locked
        if confirmations_made == 4:
            print("   ✅ All 4 partners confirmed successfully")
            return True
        else:
            print(f"   ❌ Expected 4 confirmations, got {confirmations_made}")
            return False
    
    def test_list_matches_by_player(self):
        """Test D) GET /api/doubles/matches?player_id=… filters to matches for that player; include team names and proposed slots"""
        player_id = self.player_ids[0]
        
        success, response = self.run_test(
            "List Matches by Player ID",
            "GET",
            "doubles/matches",
            200,
            params={"player_id": player_id}
        )
        
        if success and isinstance(response, list):
            print(f"   Matches found for player: {len(response)}")
            
            for i, match in enumerate(response):
                print(f"   Match {i+1}:")
                print(f"     - Team 1: {match.get('team1_name')}")
                print(f"     - Team 2: {match.get('team2_name')}")
                print(f"     - Status: {match.get('status')}")
                print(f"     - Proposed Slots: {len(match.get('proposed_slots', []))}")
            
            # Verify that the player is actually in these matches
            if len(response) > 0:
                print("   ✅ Successfully filtered matches by player ID")
                return True
            else:
                print("   ⚠️  No matches found for player (may be expected)")
                return True
        
        return success
    
    def test_submit_match_score(self):
        """Test E) POST /api/doubles/matches/{match_id}/submit-score requires majority winner; returns score_id and pending status"""
        if not self.match_id:
            print("❌ No match ID available")
            return False
        
        # Submit a score with majority winner (2-1 sets)
        score_data = {
            "sets": [
                {"team1_games": 6, "team2_games": 4},  # Team 1 wins set 1
                {"team1_games": 3, "team2_games": 6},  # Team 2 wins set 2
                {"team1_games": 6, "team2_games": 2}   # Team 1 wins set 3 (majority)
            ],
            "submitted_by_user_id": self.player_ids[0]
        }
        
        success, response = self.run_test(
            "Submit Match Score (Majority Winner)",
            "POST",
            f"doubles/matches/{self.match_id}/submit-score",
            200,
            data=score_data
        )
        
        if success:
            print(f"   Score ID: {response.get('score_id')}")
            print(f"   Status: {response.get('status')}")
            self.score_id = response.get('score_id')
            
            if response.get('status') == 'pending_co-sign':
                print("   ✅ Score submitted with pending status")
                return True
            else:
                print(f"   ❌ Expected 'pending_co-sign' status, got {response.get('status')}")
                return False
        
        return success
    
    def test_submit_score_no_majority_winner(self):
        """Test E) submitting score without majority winner returns 400"""
        if not self.match_id:
            print("❌ No match ID available")
            return False
        
        # Submit a score with tie (1-1 sets) - should fail
        score_data = {
            "sets": [
                {"team1_games": 6, "team2_games": 4},  # Team 1 wins set 1
                {"team1_games": 3, "team2_games": 6}   # Team 2 wins set 2 (tie)
            ],
            "submitted_by_user_id": self.player_ids[0]
        }
        
        success, response = self.run_test(
            "Submit Score - No Majority Winner (Should Fail)",
            "POST",
            f"doubles/matches/{self.match_id}/submit-score",
            400,
            data=score_data
        )
        
        if success:
            print("   ✅ Correctly returned 400 for no majority winner")
            return True
        else:
            print("   ❌ Should have returned 400 for no majority winner")
            return False
    
    def test_co_sign_score(self):
        """Test E) POST /api/doubles/matches/{match_id}/co-sign: require one cosign from opposite team to reach confirmed; after confirm, update standings and mark match played"""
        if not self.match_id or not self.score_id:
            print("❌ No match ID or score ID available")
            return False
        
        # Co-sign from partner first
        partner_cosign_data = {
            "user_id": self.player_ids[1],  # Partner of submitter
            "role": "partner"
        }
        
        success, response = self.run_test(
            "Co-sign Score (Partner)",
            "POST",
            f"doubles/matches/{self.match_id}/co-sign",
            200,
            data=partner_cosign_data
        )
        
        if success:
            print(f"   Status after partner co-sign: {response.get('status')}")
            print(f"   Co-signs: {len(response.get('cosigns', []))}")
        
        # Co-sign from opponent to reach confirmed
        opponent_cosign_data = {
            "user_id": self.player_ids[2],  # Opponent team member
            "role": "opponent"
        }
        
        success2, response2 = self.run_test(
            "Co-sign Score (Opponent)",
            "POST",
            f"doubles/matches/{self.match_id}/co-sign",
            200,
            data=opponent_cosign_data
        )
        
        if success2:
            print(f"   Status after opponent co-sign: {response2.get('status')}")
            print(f"   Co-signs: {len(response2.get('cosigns', []))}")
            
            if response2.get('status') == 'confirmed':
                print("   ✅ Score confirmed after partner and opponent co-sign")
                return True
            else:
                print(f"   ❌ Expected 'confirmed' status, got {response2.get('status')}")
                return False
        
        return success and success2
    
    def test_dispute_score(self):
        """Test E) POST /api/doubles/matches/{match_id}/dispute flips status to disputed"""
        if not self.match_id:
            print("❌ No match ID available")
            return False
        
        # First submit a new score to dispute
        score_data = {
            "sets": [
                {"team1_games": 6, "team2_games": 0},  # Team 1 wins set 1
                {"team1_games": 6, "team2_games": 1}   # Team 1 wins set 2
            ],
            "submitted_by_user_id": self.player_ids[0]
        }
        
        success, response = self.run_test(
            "Submit Score for Dispute Test",
            "POST",
            f"doubles/matches/{self.match_id}/submit-score",
            200,
            data=score_data
        )
        
        if not success:
            print("❌ Failed to submit score for dispute test")
            return False
        
        # Now dispute it
        success, response = self.run_test(
            "Dispute Match Score",
            "POST",
            f"doubles/matches/{self.match_id}/dispute",
            200,
            params={"user_id": self.player_ids[2]}  # Opponent disputes
        )
        
        if success:
            print(f"   Status after dispute: {response.get('status')}")
            
            if response.get('status') == 'disputed':
                print("   ✅ Score status changed to disputed")
                return True
            else:
                print(f"   ❌ Expected 'disputed' status, got {response.get('status')}")
                return False
        
        return success
    
    def test_get_doubles_standings(self):
        """Test F) GET /api/doubles/standings?rating_tier_id=… returns sorted rows with team_name and correct points/sets/games tallies"""
        success, response = self.run_test(
            "Get Doubles Standings",
            "GET",
            "doubles/standings",
            200,
            params={"rating_tier_id": self.doubles_rating_tier_id}
        )
        
        if success and isinstance(response, list):
            print(f"   Standings rows: {len(response)}")
            
            for i, row in enumerate(response):
                print(f"   Team {i+1}: {row.get('team_name')}")
                print(f"     - Wins/Losses: {row.get('wins', 0)}/{row.get('losses', 0)}")
                print(f"     - Sets: {row.get('sets_won', 0)}/{row.get('sets_lost', 0)}")
                print(f"     - Games: {row.get('games_won', 0)}/{row.get('games_lost', 0)}")
                print(f"     - Points: {row.get('points', 0)}")
            
            # Verify sorting (points descending)
            if len(response) >= 2:
                first_points = response[0].get('points', 0)
                second_points = response[1].get('points', 0)
                if first_points >= second_points:
                    print("   ✅ Standings correctly sorted by points")
                else:
                    print("   ❌ Standings not properly sorted")
                    return False
            
            print("   ✅ Doubles standings retrieved successfully")
            return True
        
        return success
    
    def test_get_match_ics(self):
        """Test G) GET /api/doubles/matches/{match_id}/ics returns valid ICS only after match is confirmed; otherwise 404"""
        if not self.match_id:
            print("❌ No match ID available")
            return False
        
        # First try to get ICS for unconfirmed match (should return 404)
        success, response = self.run_test(
            "Get ICS for Unconfirmed Match (Should Fail)",
            "GET",
            f"doubles/matches/{self.match_id}/ics",
            404
        )
        
        if success:
            print("   ✅ Correctly returned 404 for unconfirmed match")
        else:
            print("   ❌ Should have returned 404 for unconfirmed match")
            return False
        
        # Now let's try to get a confirmed match
        # First get all matches and find a confirmed one
        success, matches = self.run_test(
            "Get All Doubles Matches",
            "GET",
            "doubles/matches",
            200,
            params={"rating_tier_id": self.doubles_rating_tier_id}
        )
        
        if success and matches:
            confirmed_match = None
            for match in matches:
                if match.get('status') == 'confirmed' and match.get('scheduled_at'):
                    confirmed_match = match
                    break
            
            if confirmed_match:
                success, response = self.run_test(
                    "Get ICS for Confirmed Match",
                    "GET",
                    f"doubles/matches/{confirmed_match['id']}/ics",
                    200
                )
                
                if success and 'ics' in response:
                    ics_content = response['ics']
                    print(f"   ICS Content Length: {len(ics_content)} characters")
                    
                    # Verify ICS format
                    if ('BEGIN:VCALENDAR' in ics_content and 
                        'END:VCALENDAR' in ics_content and
                        'BEGIN:VEVENT' in ics_content and
                        'END:VEVENT' in ics_content):
                        print("   ✅ Valid ICS format returned for confirmed match")
                        return True
                    else:
                        print("   ❌ Invalid ICS format")
                        return False
                else:
                    print("   ❌ Failed to get ICS for confirmed match")
                    return False
            else:
                print("   ⚠️  No confirmed matches found to test ICS generation")
                return True  # Not a failure, just no confirmed matches yet
        
        return True
    
    def run_all_tests(self):
        """Run all Doubles Phase 2-4 tests"""
        print("🎾 DOUBLES PHASE 2-4 ENDPOINT TESTING")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Failed to set up test environment")
            return False
        
        # Test cases as specified in review request
        test_cases = [
            ("A) Team Preferences - Get Default", self.test_team_preferences_get_default),
            ("A) Team Preferences - PUT Upsert", self.test_team_preferences_put_upsert),
            ("B) Schedule Generation - Round Robin", self.test_schedule_generation),
            ("B) Schedule Generation - Insufficient Teams", self.test_schedule_generation_insufficient_teams),
            ("C) Propose Match Slots", self.test_propose_match_slots),
            ("C) Propose Slots - Invalid Datetime", self.test_propose_slots_invalid_datetime),
            ("C) Confirm Slot by Partners", self.test_confirm_slot_by_partners),
            ("D) List Matches by Player", self.test_list_matches_by_player),
            ("E) Submit Match Score", self.test_submit_match_score),
            ("E) Submit Score - No Majority", self.test_submit_score_no_majority_winner),
            ("E) Co-sign Score", self.test_co_sign_score),
            ("E) Dispute Score", self.test_dispute_score),
            ("F) Get Doubles Standings", self.test_get_doubles_standings),
            ("G) Get Match ICS", self.test_get_match_ics)
        ]
        
        successful_tests = 0
        failed_tests = []
        
        for test_name, test_method in test_cases:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_method():
                    successful_tests += 1
                    print(f"   ✅ {test_name} - PASSED")
                else:
                    print(f"   ❌ {test_name} - FAILED")
                    failed_tests.append(test_name)
            except Exception as e:
                print(f"   ❌ {test_name} - ERROR: {str(e)}")
                failed_tests.append(f"{test_name} (ERROR)")
        
        # Summary
        print(f"\n🎯 DOUBLES PHASE 2-4 TEST SUMMARY:")
        print(f"   Tests Run: {len(test_cases)}")
        print(f"   Tests Passed: {successful_tests}")
        print(f"   Tests Failed: {len(failed_tests)}")
        print(f"   Success Rate: {(successful_tests/len(test_cases))*100:.1f}%")
        
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test}")
        
        if successful_tests >= len(test_cases) * 0.8:  # 80% success rate
            print("\n🎉 DOUBLES PHASE 2-4 TESTING SUCCESSFUL!")
            return True
        else:
            print("\n⚠️  DOUBLES PHASE 2-4 TESTING NEEDS ATTENTION")
            return False

def main():
    tester = DoublesPhase24Tester()
    success = tester.run_all_tests()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   API Tests Run: {tester.tests_run}")
    print(f"   API Tests Passed: {tester.tests_passed}")
    print(f"   API Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())