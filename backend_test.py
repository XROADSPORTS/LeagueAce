import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class NetlyAPITester:
    def __init__(self, base_url="https://netly-sports.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.league_manager_id = None
        self.player_id = None
        self.main_season_id = None
        self.format_tier_id = None
        self.skill_tier_id = None
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
            "name": "Test League Manager",
            "email": f"manager_{datetime.now().strftime('%H%M%S')}@test.com",
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
            "name": "Test Player",
            "email": f"player_{datetime.now().strftime('%H%M%S')}@test.com",
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

    def test_create_main_season(self):
        """Test creating a main season (League Manager only)"""
        if not self.league_manager_id:
            print("❌ Skipping - No League Manager ID available")
            return False

        season_data = {
            "name": "Test Season 14",
            "description": "Test season for API validation",
            "start_date": "2024-09-01",
            "end_date": "2024-12-31"
        }
        
        success, response = self.run_test(
            "Create Main Season",
            "POST",
            f"main-seasons",
            200,
            data=season_data,
            params={"created_by": self.league_manager_id}
        )
        
        if success and 'id' in response:
            self.main_season_id = response['id']
            print(f"   Created Main Season ID: {self.main_season_id}")
        
        return success

    def test_get_main_seasons(self):
        """Test getting all main seasons"""
        return self.run_test("Get All Main Seasons", "GET", "main-seasons", 200)

    def test_get_user_main_seasons(self):
        """Test getting user's main seasons"""
        if not self.league_manager_id:
            print("❌ Skipping - No League Manager ID available")
            return False
            
        return self.run_test(
            "Get User Main Seasons",
            "GET",
            f"users/{self.league_manager_id}/main-seasons",
            200
        )

    def test_create_format_tier(self):
        """Test creating a format tier"""
        if not self.main_season_id:
            print("❌ Skipping - No Main Season ID available")
            return False

        format_data = {
            "main_season_id": self.main_season_id,
            "name": "Singles",
            "description": "Singles format for test season"
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
        """Test getting format tiers for a main season"""
        if not self.main_season_id:
            print("❌ Skipping - No Main Season ID available")
            return False
            
        return self.run_test(
            "Get Format Tiers",
            "GET",
            f"main-seasons/{self.main_season_id}/format-tiers",
            200
        )

    def test_create_skill_tier(self):
        """Test creating a skill tier"""
        if not self.format_tier_id:
            print("❌ Skipping - No Format Tier ID available")
            return False

        skill_data = {
            "format_tier_id": self.format_tier_id,
            "name": "4.0",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 36,
            "region": "Test Region",
            "surface": "Hard Court"
        }
        
        success, response = self.run_test(
            "Create Skill Tier",
            "POST",
            "skill-tiers",
            200,
            data=skill_data
        )
        
        if success and 'id' in response:
            self.skill_tier_id = response['id']
            self.join_code = response.get('join_code')
            print(f"   Created Skill Tier ID: {self.skill_tier_id}")
            print(f"   Generated Join Code: {self.join_code}")
        
        return success

    def test_get_skill_tiers(self):
        """Test getting skill tiers for a format tier"""
        if not self.format_tier_id:
            print("❌ Skipping - No Format Tier ID available")
            return False
            
        return self.run_test(
            "Get Skill Tiers",
            "GET",
            f"format-tiers/{self.format_tier_id}/skill-tiers",
            200
        )

    def test_get_skill_tier_by_id(self):
        """Test getting a specific skill tier"""
        if not self.skill_tier_id:
            print("❌ Skipping - No Skill Tier ID available")
            return False
            
        return self.run_test(
            "Get Skill Tier by ID",
            "GET",
            f"skill-tiers/{self.skill_tier_id}",
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

    def test_get_user_joined_tiers(self):
        """Test getting user's joined tiers"""
        if not self.player_id:
            print("❌ Skipping - No Player ID available")
            return False
            
        return self.run_test(
            "Get User Joined Tiers",
            "GET",
            f"users/{self.player_id}/joined-tiers",
            200
        )

    def test_get_user_standings(self):
        """Test getting user's standings"""
        if not self.player_id:
            print("❌ Skipping - No Player ID available")
            return False
            
        return self.run_test(
            "Get User Standings",
            "GET",
            f"users/{self.player_id}/standings",
            200
        )

    def test_get_skill_tier_players(self):
        """Test getting players in a skill tier"""
        if not self.skill_tier_id:
            print("❌ Skipping - No Skill Tier ID available")
            return False
            
        return self.run_test(
            "Get Skill Tier Players",
            "GET",
            f"skill-tiers/{self.skill_tier_id}/players",
            200
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

    def test_unauthorized_season_creation(self):
        """Test that players cannot create seasons"""
        if not self.player_id:
            print("❌ Skipping - No Player ID available")
            return False

        season_data = {
            "name": "Unauthorized Season",
            "description": "This should fail",
            "start_date": "2024-09-01",
            "end_date": "2024-12-31"
        }
        
        # This should return 403 for unauthorized access
        return self.run_test(
            "Unauthorized Season Creation",
            "POST",
            f"main-seasons",
            403,
            data=season_data,
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