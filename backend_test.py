import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class LeagueAceAPITester:
    def __init__(self, base_url="https://courtmaster-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.league_manager_id = None
        self.player_id = None
        self.league_id = None
        self.season_id = None
        self.format_tier_id = None
        self.rating_tier_id = None
        self.join_code = None

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

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_create_league_manager(self):
        """Create a League Manager user"""
        manager_data = {
            "name": "Alex Rodriguez",
            "email": f"alex.rodriguez_{datetime.now().strftime('%H%M%S')}@tennisclub.com",
            "phone": "+1-555-0101",
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
            print(f"   Created League Manager ID: {self.league_manager_id}")
        
        return success

    def test_create_player(self):
        """Create a Player user"""
        player_data = {
            "name": "Maria Santos",
            "email": f"maria.santos_{datetime.now().strftime('%H%M%S')}@gmail.com",
            "phone": "+1-555-0102",
            "rating_level": 4.0,
            "role": "Player"
        }
        
        success, response = self.run_test(
            "Create Player",
            "POST",
            "users",
            200,
            data=player_data
        )
        
        if success and 'id' in response:
            self.player_id = response['id']
            print(f"   Created Player ID: {self.player_id}")
        
        return success

    def test_get_users(self):
        """Test getting all users"""
        return self.run_test("Get All Users", "GET", "users", 200)

    def test_get_user_by_id(self):
        """Test getting user by ID"""
        if not self.league_manager_id:
            print("❌ Skipping - No League Manager ID available")
            return False
            
        return self.run_test(
            "Get User by ID",
            "GET",
            f"users/{self.league_manager_id}",
            200
        )

    def test_create_league(self):
        """Test creating a league (League Manager only)"""
        if not self.league_manager_id:
            print("❌ Skipping - No League Manager ID available")
            return False

        league_data = {
            "name": "Bay Area Tennis League",
            "sport_type": "Tennis",
            "description": "Premier tennis league for Bay Area players"
        }
        
        success, response = self.run_test(
            "Create League",
            "POST",
            f"leagues",
            200,
            data=league_data,
            params={"created_by": self.league_manager_id}
        )
        
        if success and 'id' in response:
            self.league_id = response['id']
            print(f"   Created League ID: {self.league_id}")
        
        return success

    def test_get_leagues(self):
        """Test getting all leagues"""
        return self.run_test("Get All Leagues", "GET", "leagues", 200)

    def test_get_user_leagues(self):
        """Test getting user's leagues"""
        if not self.league_manager_id:
            print("❌ Skipping - No League Manager ID available")
            return False
            
        return self.run_test(
            "Get User Leagues",
            "GET",
            f"users/{self.league_manager_id}/leagues",
            200
        )

    def test_create_season(self):
        """Test creating a season"""
        if not self.league_id:
            print("❌ Skipping - No League ID available")
            return False

        season_data = {
            "league_id": self.league_id,
            "name": "Fall 2024 Season",
            "start_date": "2024-09-01",
            "end_date": "2024-12-31"
        }
        
        success, response = self.run_test(
            "Create Season",
            "POST",
            "seasons",
            200,
            data=season_data
        )
        
        if success and 'id' in response:
            self.season_id = response['id']
            print(f"   Created Season ID: {self.season_id}")
        
        return success

    def test_get_league_seasons(self):
        """Test getting seasons for a league"""
        if not self.league_id:
            print("❌ Skipping - No League ID available")
            return False
            
        return self.run_test(
            "Get League Seasons",
            "GET",
            f"leagues/{self.league_id}/seasons",
            200
        )

    def test_create_format_tier(self):
        """Test creating a format tier (Singles/Doubles)"""
        if not self.season_id:
            print("❌ Skipping - No Season ID available")
            return False

        format_data = {
            "season_id": self.season_id,
            "name": "Singles Competition",
            "format_type": "Singles",
            "description": "Singles format for competitive play"
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
            print(f"   Created Format Tier ID: {self.format_tier_id}")
        
        return success

    def test_get_format_tiers(self):
        """Test getting format tiers for a season"""
        if not self.season_id:
            print("❌ Skipping - No Season ID available")
            return False
            
        return self.run_test(
            "Get Format Tiers",
            "GET",
            f"seasons/{self.season_id}/format-tiers",
            200
        )

    def test_create_rating_tier(self):
        """Test creating a rating tier (4.0, 4.5, 5.0)"""
        if not self.format_tier_id:
            print("❌ Skipping - No Format Tier ID available")
            return False

        rating_data = {
            "format_tier_id": self.format_tier_id,
            "name": "4.0 Level",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 36,
            "competition_system": "Team League Format",
            "playoff_spots": 8,
            "region": "Bay Area",
            "surface": "Hard Court",
            "rules_md": "Standard USTA rules apply"
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
            print(f"   Created Rating Tier ID: {self.rating_tier_id}")
            print(f"   Generated Join Code: {self.join_code}")
        
        return success

    def test_get_rating_tiers(self):
        """Test getting rating tiers for a format tier"""
        if not self.format_tier_id:
            print("❌ Skipping - No Format Tier ID available")
            return False
            
        return self.run_test(
            "Get Rating Tiers",
            "GET",
            f"format-tiers/{self.format_tier_id}/rating-tiers",
            200
        )

    def test_get_rating_tier_by_id(self):
        """Test getting a specific rating tier"""
        if not self.rating_tier_id:
            print("❌ Skipping - No Rating Tier ID available")
            return False
            
        return self.run_test(
            "Get Rating Tier by ID",
            "GET",
            f"rating-tiers/{self.rating_tier_id}",
            200
        )

    def test_join_by_code(self):
        """Test player joining by code"""
        if not self.player_id or not self.join_code:
            print("❌ Skipping - No Player ID or Join Code available")
            return False

        join_data = {
            "join_code": self.join_code
        }
        
        success, response = self.run_test(
            "Join by Code",
            "POST",
            f"join-by-code/{self.player_id}",
            200,
            data=join_data
        )
        
        if success:
            print(f"   Join Status: {response.get('status', 'Unknown')}")
            print(f"   Message: {response.get('message', 'No message')}")
        
        return success

    def test_create_player_groups(self):
        """Test creating player groups (Tier 4)"""
        if not self.rating_tier_id:
            print("❌ Skipping - No Rating Tier ID available")
            return False

        group_data = {
            "group_size": 12,
            "custom_names": ["Group Alpha", "Group Beta", "Group Gamma"]
        }
        
        success, response = self.run_test(
            "Create Player Groups",
            "POST",
            f"rating-tiers/{self.rating_tier_id}/create-groups",
            200,
            data=group_data
        )
        
        if success:
            print(f"   Groups Created: {response.get('message', 'Unknown')}")
        
        return success

    def test_get_rating_tier_groups(self):
        """Test getting groups for a rating tier"""
        if not self.rating_tier_id:
            print("❌ Skipping - No Rating Tier ID available")
            return False
            
        return self.run_test(
            "Get Rating Tier Groups",
            "GET",
            f"rating-tiers/{self.rating_tier_id}/groups",
            200
        )

    def test_social_login(self):
        """Test social login functionality"""
        social_data = {
            "provider": "Google",
            "token": "mock_google_token_123",
            "email": f"john.doe_{datetime.now().strftime('%H%M%S')}@gmail.com",
            "name": "John Doe",
            "provider_id": "google_123456789"
        }
        
        success, response = self.run_test(
            "Social Login (Google)",
            "POST",
            "auth/social-login",
            200,
            data=social_data
        )
        
        if success and 'id' in response:
            print(f"   Social Login User ID: {response['id']}")
        
        return success

    def test_update_sports_preferences(self):
        """Test updating user sports preferences"""
        if not self.player_id:
            print("❌ Skipping - No Player ID available")
            return False

        preferences_data = {
            "sports_preferences": ["Tennis", "Pickleball"]
        }
        
        return self.run_test(
            "Update Sports Preferences",
            "PATCH",
            f"users/{self.player_id}/sports",
            200,
            data=preferences_data
        )

    def test_update_profile_picture(self):
        """Test updating profile picture"""
        if not self.player_id:
            print("❌ Skipping - No Player ID available")
            return False

        picture_data = {
            "profile_picture": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        }
        
        return self.run_test(
            "Update Profile Picture",
            "PATCH",
            f"users/{self.player_id}/profile-picture",
            200,
            data=picture_data
        )

    def test_invalid_join_code(self):
        """Test joining with invalid code"""
        if not self.player_id:
            print("❌ Skipping - No Player ID available")
            return False

        join_data = {
            "join_code": "INVALID"
        }
        
        # This should return 404 for invalid code
        return self.run_test(
            "Join with Invalid Code",
            "POST",
            f"join-by-code/{self.player_id}",
            404,
            data=join_data
        )

    def test_unauthorized_league_creation(self):
        """Test that players cannot create leagues"""
        if not self.player_id:
            print("❌ Skipping - No Player ID available")
            return False

        league_data = {
            "name": "Unauthorized League",
            "sport_type": "Tennis",
            "description": "This should fail"
        }
        
        # This should return 403 for unauthorized access
        return self.run_test(
            "Unauthorized League Creation",
            "POST",
            f"leagues",
            403,
            data=league_data,
            params={"created_by": self.player_id}
        )

    def run_complete_workflow_test(self):
        """Test the complete 3-tier league workflow"""
        print("\n" + "="*60)
        print("🚀 STARTING NETLY 3-TIER LEAGUE WORKFLOW TEST")
        print("="*60)

        # Test sequence for new 3-tier structure
        test_methods = [
            ("Root API", self.test_root_endpoint),
            ("Create League Manager", self.test_create_league_manager),
            ("Create Player", self.test_create_player),
            ("Get All Users", self.test_get_users),
            ("Get User by ID", self.test_get_user_by_id),
            ("Create Main Season", self.test_create_main_season),
            ("Get All Main Seasons", self.test_get_main_seasons),
            ("Get User Main Seasons", self.test_get_user_main_seasons),
            ("Create Format Tier", self.test_create_format_tier),
            ("Get Format Tiers", self.test_get_format_tiers),
            ("Create Skill Tier", self.test_create_skill_tier),
            ("Get Skill Tiers", self.test_get_skill_tiers),
            ("Get Skill Tier by ID", self.test_get_skill_tier_by_id),
            ("Join by Code", self.test_join_by_code),
            ("Get User Joined Tiers", self.test_get_user_joined_tiers),
            ("Get User Standings", self.test_get_user_standings),
            ("Get Skill Tier Players", self.test_get_skill_tier_players),
            ("Invalid Join Code", self.test_invalid_join_code),
            ("Unauthorized Season Creation", self.test_unauthorized_season_creation)
        ]
        
        # Run all tests
        for test_name, test_method in test_methods:
            print(f"\n📋 Running: {test_name}")
            test_method()
        
        return True

def main():
    print("🎾 Netly API Testing Suite")
    print("=" * 50)
    
    tester = NetlyAPITester()
    
    # Run complete workflow test
    success = tester.run_complete_workflow_test()
    
    # Print final results
    print("\n" + "="*60)
    print("📊 FINAL TEST RESULTS")
    print("="*60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if success and tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())