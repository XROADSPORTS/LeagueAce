#!/usr/bin/env python3
"""
Round Robin Sample Schedules Test
Creates sample schedules for both QA tiers and returns all created player IDs and scheduling metadata.
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

class RRSampleSchedulesTest:
    def __init__(self, base_url="https://teamace.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # QA Tier IDs from review request
        self.qa_doubles_tier_id = "82830a8f-6f02-48ac-99fc-dbc445f4385a"
        self.qa_doubles_join_code = "4EE4BJ"
        self.qa_singles_tier_id = "dbaf7ed9-b507-4983-bd92-44c561e912ee"
        self.qa_singles_join_code = "ENSXQG"
        
        # Results storage
        self.doubles_results = {}
        self.singles_results = {}
        self.created_players = []

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

    def create_player(self, name: str, email: str, rating: float) -> str:
        """Create a player via social login"""
        player_data = {
            "provider": "google",
            "token": "fake_token",
            "email": email,
            "name": name,
            "provider_id": f"google_{uuid.uuid4()}",
            "role": "Player",
            "rating_level": rating
        }
        
        success, response = self.run_test(
            f"Create Player {name}",
            "POST",
            "auth/social-login",
            200,
            data=player_data
        )
        
        if success and 'id' in response:
            player_id = response['id']
            print(f"   Created Player ID: {player_id}")
            self.created_players.append({
                "id": player_id,
                "name": name,
                "email": email,
                "rating": rating
            })
            return player_id
        return None

    def patch_player_sports(self, player_id: str) -> bool:
        """PATCH player sports to Tennis"""
        sports_data = {
            "sports_preferences": ["Tennis"]
        }
        
        success, response = self.run_test(
            f"PATCH Player Sports {player_id}",
            "PATCH",
            f"users/{player_id}/sports",
            200,
            data=sports_data
        )
        return success

    def join_by_code(self, player_id: str, join_code: str) -> bool:
        """Join tier by code"""
        join_data = {
            "join_code": join_code
        }
        
        success, response = self.run_test(
            f"Join by code {join_code}",
            "POST",
            f"join-by-code/{player_id}",
            200,
            data=join_data
        )
        return success

    def configure_rr_tier(self, tier_id: str, season_length: int = 3) -> str:
        """Configure RR tier"""
        config_data = {
            "season_length": season_length,
            "track_first_match_badge": True,
            "track_finished_badge": True
        }
        
        success, response = self.run_test(
            f"Configure RR Tier {tier_id}",
            "POST",
            f"rr/tiers/{tier_id}/configure",
            200,
            data=config_data
        )
        
        if success and 'config' in response:
            config_id = response['config'].get('id')
            print(f"   RR Config ID: {config_id}")
            return config_id
        return None

    def schedule_rr_tier(self, tier_id: str, player_ids: List[str]) -> Dict[str, Any]:
        """Schedule RR tier"""
        schedule_data = {
            "player_ids": player_ids
        }
        
        success, response = self.run_test(
            f"Schedule RR Tier {tier_id}",
            "POST",
            f"rr/tiers/{tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if success:
            return response
        return {}

    def get_schedule_meta(self, tier_id: str) -> Dict[str, Any]:
        """Get schedule metadata"""
        success, response = self.run_test(
            f"Get Schedule Meta {tier_id}",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": tier_id}
        )
        
        if success:
            return response
        return {}

    def get_rr_weeks(self, player_id: str, tier_id: str) -> Dict[str, Any]:
        """Get RR weeks for player"""
        success, response = self.run_test(
            f"Get RR Weeks for Player {player_id}",
            "GET",
            "rr/weeks",
            200,
            params={"player_id": player_id, "tier_id": tier_id}
        )
        
        if success:
            return response
        return {}

    def propose_slot_for_match(self, match_id: str, proposed_by_user_id: str) -> List[str]:
        """Propose a slot for a match"""
        future_datetime = (datetime.now() + timedelta(days=7)).isoformat()
        
        slot_data = {
            "slots": [{
                "start": future_datetime,
                "venue_name": "QA Court"
            }],
            "proposed_by_user_id": proposed_by_user_id
        }
        
        success, response = self.run_test(
            f"Propose Slot for Match {match_id}",
            "POST",
            f"rr/matches/{match_id}/propose-slots",
            200,
            data=slot_data
        )
        
        if success and 'created' in response:
            return response['created']
        return []

    def get_tier_members(self, tier_id: str) -> List[Dict[str, Any]]:
        """Get existing members of a tier"""
        success, response = self.run_test(
            f"Get Tier Members {tier_id}",
            "GET",
            f"rating-tiers/{tier_id}/members",
            200
        )
        
        if success and isinstance(response, list):
            return response
        return []

    def test_qa_doubles_workflow(self):
        """Test QA 4.0 Doubles workflow"""
        print("\n" + "="*60)
        print("🎾 TESTING QA 4.0 DOUBLES WORKFLOW")
        print("="*60)
        
        # Get existing members first
        existing_members = self.get_tier_members(self.qa_doubles_tier_id)
        existing_player_ids = [member['user_id'] for member in existing_members]
        print(f"   Found {len(existing_members)} existing members")
        
        # Create 3 new players (ratings within 3.5–4.5)
        new_players = []
        for i in range(3):
            rating = 3.5 + (i * 0.5)  # 3.5, 4.0, 4.5
            player_id = self.create_player(
                f"QA Doubles Player {i+1}",
                f"qa.doubles.player{i+1}@gmail.com",
                rating
            )
            if player_id:
                # PATCH sports to Tennis
                self.patch_player_sports(player_id)
                # Join by code
                self.join_by_code(player_id, self.qa_doubles_join_code)
                new_players.append(player_id)
        
        # Total players should be existing + new
        all_player_ids = existing_player_ids + new_players
        print(f"   Total players for scheduling: {len(all_player_ids)}")
        
        # Configure RR
        rr_config_id = self.configure_rr_tier(self.qa_doubles_tier_id, season_length=3)
        
        # Schedule RR
        schedule_result = self.schedule_rr_tier(self.qa_doubles_tier_id, all_player_ids)
        
        # Get schedule meta
        schedule_meta = self.get_schedule_meta(self.qa_doubles_tier_id)
        
        # Get weeks for first player to find matches
        if all_player_ids:
            weeks_data = self.get_rr_weeks(all_player_ids[0], self.qa_doubles_tier_id)
            
            # Find first match and propose a slot
            example_match_id = None
            example_proposed_slot_ids = []
            
            if 'weeks' in weeks_data and weeks_data['weeks']:
                for week in weeks_data['weeks']:
                    if 'matches' in week and week['matches']:
                        example_match_id = week['matches'][0]['id']
                        example_proposed_slot_ids = self.propose_slot_for_match(
                            example_match_id, 
                            all_player_ids[0]
                        )
                        break
        
        # Store results
        self.doubles_results = {
            "player_ids": all_player_ids,
            "new_player_ids": new_players,
            "rr_config_id": rr_config_id,
            "weeks_count": schedule_result.get('weeks', 0),
            "feasibility_score": schedule_result.get('feasibility_score', 0),
            "schedule_quality": schedule_result.get('schedule_quality', 0),
            "example_match_id": example_match_id,
            "example_proposed_slot_ids": example_proposed_slot_ids,
            "schedule_meta": schedule_meta
        }
        
        return len(new_players) == 3

    def test_qa_singles_workflow(self):
        """Test QA 4.5 Singles workflow"""
        print("\n" + "="*60)
        print("🎾 TESTING QA 4.5 SINGLES WORKFLOW")
        print("="*60)
        
        # Get existing members (should be 2)
        existing_members = self.get_tier_members(self.qa_singles_tier_id)
        existing_player_ids = [member['user_id'] for member in existing_members]
        print(f"   Found {len(existing_members)} existing members")
        
        # Create 2 more players (ratings within 4.5–5.0)
        new_players = []
        for i in range(2):
            rating = 4.5 + (i * 0.25)  # 4.5, 4.75
            player_id = self.create_player(
                f"QA Singles Player {i+1}",
                f"qa.singles.player{i+1}@gmail.com",
                rating
            )
            if player_id:
                # PATCH sports to Tennis
                self.patch_player_sports(player_id)
                # Join by code
                self.join_by_code(player_id, self.qa_singles_join_code)
                new_players.append(player_id)
        
        # Total players should be 4
        all_player_ids = existing_player_ids + new_players
        print(f"   Total players for scheduling: {len(all_player_ids)}")
        
        # Configure RR
        rr_config_id = self.configure_rr_tier(self.qa_singles_tier_id, season_length=3)
        
        # Schedule RR
        schedule_result = self.schedule_rr_tier(self.qa_singles_tier_id, all_player_ids)
        
        # Get schedule meta
        schedule_meta = self.get_schedule_meta(self.qa_singles_tier_id)
        
        # Get weeks for first player to find matches
        if all_player_ids:
            weeks_data = self.get_rr_weeks(all_player_ids[0], self.qa_singles_tier_id)
            
            # Find first match and propose a slot
            example_match_id = None
            example_proposed_slot_ids = []
            
            if 'weeks' in weeks_data and weeks_data['weeks']:
                for week in weeks_data['weeks']:
                    if 'matches' in week and week['matches']:
                        example_match_id = week['matches'][0]['id']
                        example_proposed_slot_ids = self.propose_slot_for_match(
                            example_match_id, 
                            all_player_ids[0]
                        )
                        break
        
        # Store results
        self.singles_results = {
            "player_ids": all_player_ids,
            "new_player_ids": new_players,
            "rr_config_id": rr_config_id,
            "weeks_count": schedule_result.get('weeks', 0),
            "feasibility_score": schedule_result.get('feasibility_score', 0),
            "schedule_quality": schedule_result.get('schedule_quality', 0),
            "example_match_id": example_match_id,
            "example_proposed_slot_ids": example_proposed_slot_ids,
            "schedule_meta": schedule_meta
        }
        
        return len(new_players) == 2

    def generate_final_summary(self):
        """Generate the final JSON summary"""
        print("\n" + "="*60)
        print("📋 FINAL SUMMARY")
        print("="*60)
        
        summary = {
            "doubles": {
                "player_ids": self.doubles_results.get('player_ids', []),
                "new_player_ids": self.doubles_results.get('new_player_ids', []),
                "rr_config_id": self.doubles_results.get('rr_config_id'),
                "weeks_count": self.doubles_results.get('weeks_count', 0),
                "feasibility_score": self.doubles_results.get('feasibility_score', 0),
                "schedule_quality": self.doubles_results.get('schedule_quality', 0),
                "example_match_id": self.doubles_results.get('example_match_id'),
                "example_proposed_slot_ids": self.doubles_results.get('example_proposed_slot_ids', [])
            },
            "singles": {
                "player_ids": self.singles_results.get('player_ids', []),
                "new_player_ids": self.singles_results.get('new_player_ids', []),
                "rr_config_id": self.singles_results.get('rr_config_id'),
                "weeks_count": self.singles_results.get('weeks_count', 0),
                "feasibility_score": self.singles_results.get('feasibility_score', 0),
                "schedule_quality": self.singles_results.get('schedule_quality', 0),
                "example_match_id": self.singles_results.get('example_match_id'),
                "example_proposed_slot_ids": self.singles_results.get('example_proposed_slot_ids', [])
            },
            "test_urls": {
                "doubles_rr_schedule_meta_url": f"{self.api_url}/rr/schedule-meta?tier_id={self.qa_doubles_tier_id}",
                "singles_rr_schedule_meta_url": f"{self.api_url}/rr/schedule-meta?tier_id={self.qa_singles_tier_id}",
                "rr_weeks_urls": []
            }
        }
        
        # Add RR weeks URLs for each created player
        for player in self.created_players:
            for tier_name, tier_id in [("doubles", self.qa_doubles_tier_id), ("singles", self.qa_singles_tier_id)]:
                summary["test_urls"]["rr_weeks_urls"].append({
                    "player_name": player["name"],
                    "tier": tier_name,
                    "url": f"{self.api_url}/rr/weeks?player_id={player['id']}&tier_id={tier_id}"
                })
        
        print(json.dumps(summary, indent=2))
        return summary

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Round Robin Sample Schedules Test")
        print(f"   Base URL: {self.base_url}")
        
        try:
            # Test QA Doubles workflow
            doubles_success = self.test_qa_doubles_workflow()
            
            # Test QA Singles workflow  
            singles_success = self.test_qa_singles_workflow()
            
            # Generate final summary
            summary = self.generate_final_summary()
            
            # Print test results
            print(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
            
            if doubles_success and singles_success:
                print("✅ All workflows completed successfully!")
                return True, summary
            else:
                print("❌ Some workflows failed")
                return False, summary
                
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
            return False, {}

if __name__ == "__main__":
    tester = RRSampleSchedulesTest()
    success, summary = tester.run_all_tests()
    
    if success:
        print("\n🎉 Round Robin Sample Schedules Test completed successfully!")
    else:
        print("\n💥 Round Robin Sample Schedules Test failed!")
    
    exit(0 if success else 1)