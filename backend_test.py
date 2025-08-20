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
        self.created_resources = {
            'users': [],
            'leagues': [],
            'seasons': [],
            'matches': []
        }

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None, params: Dict[str, Any] = None) -> tuple[bool, Dict[Any, Any]]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
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
                    if isinstance(response_data, dict) and 'id' in response_data:
                        print(f"   Created resource ID: {response_data['id']}")
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

    def test_api_health(self):
        """Test API health check"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        return success

    def test_create_user(self, name: str, email: str, rating: float = 4.0):
        """Test user creation"""
        user_data = {
            "name": name,
            "email": email,
            "phone": "+1234567890",
            "rating_level": rating
        }
        
        success, response = self.run_test(
            f"Create User - {name}",
            "POST",
            "users",
            200,
            data=user_data
        )
        
        if success and 'id' in response:
            self.created_resources['users'].append(response)
            return response['id']
        return None

    def test_get_users(self):
        """Test getting all users"""
        success, response = self.run_test(
            "Get All Users",
            "GET",
            "users",
            200
        )
        return success, response

    def test_get_user_by_id(self, user_id: str):
        """Test getting user by ID"""
        success, response = self.run_test(
            f"Get User by ID - {user_id}",
            "GET",
            f"users/{user_id}",
            200
        )
        return success, response

    def test_create_league(self, name: str, region: str, level: str, format: str = "Doubles"):
        """Test league creation"""
        league_data = {
            "name": name,
            "region": region,
            "level": level,
            "format": format,
            "surface": "Hard Court",
            "rules_md": "Standard league rules apply"
        }
        
        success, response = self.run_test(
            f"Create League - {name}",
            "POST",
            "leagues",
            200,
            data=league_data
        )
        
        if success and 'id' in response:
            self.created_resources['leagues'].append(response)
            return response['id']
        return None

    def test_get_leagues(self):
        """Test getting all leagues"""
        success, response = self.run_test(
            "Get All Leagues",
            "GET",
            "leagues",
            200
        )
        return success, response

    def test_create_season(self, league_id: str, name: str):
        """Test season creation"""
        start_date = date.today()
        end_date = start_date + timedelta(weeks=9)
        
        season_data = {
            "league_id": league_id,
            "name": name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "weeks": 9,
            "max_players": 36
        }
        
        success, response = self.run_test(
            f"Create Season - {name}",
            "POST",
            "seasons",
            200,
            data=season_data
        )
        
        if success and 'id' in response:
            self.created_resources['seasons'].append(response)
            return response['id']
        return None

    def test_get_seasons(self):
        """Test getting all seasons"""
        success, response = self.run_test(
            "Get All Seasons",
            "GET",
            "seasons",
            200
        )
        return success, response

    def test_join_season(self, season_id: str, user_id: str):
        """Test joining a season"""
        success, response = self.run_test(
            f"Join Season - User {user_id}",
            "POST",
            f"seasons/{season_id}/join?user_id={user_id}",
            200
        )
        return success, response

    def test_get_season_players(self, season_id: str):
        """Test getting season players"""
        success, response = self.run_test(
            f"Get Season Players - {season_id}",
            "GET",
            f"seasons/{season_id}/players",
            200
        )
        return success, response

    def test_set_availability(self, season_id: str, user_id: str, week_number: int, status: str = "Yes"):
        """Test setting player availability"""
        availability_data = {
            "season_id": season_id,
            "week_number": week_number,
            "status": status,
            "note": "Available for matches"
        }
        
        success, response = self.run_test(
            f"Set Availability - User {user_id}, Week {week_number}",
            "POST",
            f"availability?user_id={user_id}",
            200,
            data=availability_data
        )
        return success, response

    def test_get_week_availability(self, season_id: str, week_number: int):
        """Test getting week availability"""
        success, response = self.run_test(
            f"Get Week Availability - Season {season_id}, Week {week_number}",
            "GET",
            f"seasons/{season_id}/availability/{week_number}",
            200
        )
        return success, response

    def test_generate_matches(self, season_id: str, week_number: int):
        """Test generating matches for a week"""
        success, response = self.run_test(
            f"Generate Matches - Season {season_id}, Week {week_number}",
            "POST",
            f"seasons/{season_id}/generate-matches/{week_number}",
            200
        )
        
        if success and 'matches' in response:
            self.created_resources['matches'].extend(response['matches'])
        return success, response

    def test_get_matches(self, season_id: str, week_number: int = None):
        """Test getting matches"""
        endpoint = f"seasons/{season_id}/matches"
        params = {"week_number": week_number} if week_number else None
        
        success, response = self.run_test(
            f"Get Matches - Season {season_id}" + (f", Week {week_number}" if week_number else ""),
            "GET",
            endpoint,
            200,
            params=params
        )
        return success, response

    def test_submit_scores(self, match_id: str, scores: list):
        """Test submitting match scores"""
        success, response = self.run_test(
            f"Submit Scores - Match {match_id}",
            "POST",
            f"matches/{match_id}/submit-scores",
            200,
            data={"scores": scores, "submitted_by": "test_user"}
        )
        return success, response

    def test_get_standings(self, season_id: str):
        """Test getting season standings"""
        success, response = self.run_test(
            f"Get Standings - Season {season_id}",
            "GET",
            f"seasons/{season_id}/standings",
            200
        )
        return success, response

    def run_complete_workflow_test(self):
        """Test the complete user journey"""
        print("\n" + "="*60)
        print("🚀 STARTING COMPLETE WORKFLOW TEST")
        print("="*60)

        # 1. Test API Health
        if not self.test_api_health():
            print("❌ API Health check failed, stopping tests")
            return False

        # 2. Create test users
        print("\n📝 Creating test users...")
        user1_id = self.test_create_user("Alice Johnson", "alice@example.com", 4.2)
        user2_id = self.test_create_user("Bob Smith", "bob@example.com", 3.8)
        user3_id = self.test_create_user("Carol Davis", "carol@example.com", 4.0)
        user4_id = self.test_create_user("David Wilson", "david@example.com", 4.1)

        if not all([user1_id, user2_id, user3_id, user4_id]):
            print("❌ Failed to create required users")
            return False

        # 3. Test getting users
        self.test_get_users()
        self.test_get_user_by_id(user1_id)

        # 4. Create a league
        print("\n🏆 Creating test league...")
        league_id = self.test_create_league(
            "Downtown Tennis League", 
            "San Francisco", 
            "Intermediate (3.5-4.0)"
        )
        
        if not league_id:
            print("❌ Failed to create league")
            return False

        # 5. Test getting leagues
        self.test_get_leagues()

        # 6. Create a season
        print("\n📅 Creating test season...")
        season_id = self.test_create_season(league_id, "Spring 2024 Season")
        
        if not season_id:
            print("❌ Failed to create season")
            return False

        # 7. Test getting seasons
        self.test_get_seasons()

        # 8. Join season with all users
        print("\n👥 Joining season with users...")
        for user_id in [user1_id, user2_id, user3_id, user4_id]:
            self.test_join_season(season_id, user_id)

        # 9. Test getting season players
        self.test_get_season_players(season_id)

        # 10. Set availability for all users for week 1
        print("\n📋 Setting availability for week 1...")
        for user_id in [user1_id, user2_id, user3_id, user4_id]:
            self.test_set_availability(season_id, user_id, 1, "Yes")

        # 11. Test getting week availability
        self.test_get_week_availability(season_id, 1)

        # 12. Generate matches for week 1
        print("\n⚡ Generating matches for week 1...")
        success, matches_response = self.test_generate_matches(season_id, 1)
        
        if not success or not matches_response.get('matches'):
            print("❌ Failed to generate matches")
            return False

        # 13. Get matches
        success, matches_data = self.test_get_matches(season_id, 1)
        
        if not success or not matches_data:
            print("❌ Failed to get matches")
            return False

        # 14. Submit scores for the first match
        print("\n🎾 Submitting scores...")
        if matches_data and len(matches_data) > 0:
            match = matches_data[0]
            match_id = match['id']
            
            if 'sets' in match and len(match['sets']) > 0:
                scores = []
                for set_data in match['sets']:
                    scores.append({
                        "set_id": set_data['id'],
                        "score_a": 6,
                        "score_b": 4
                    })
                
                self.test_submit_scores(match_id, scores)

        # 15. Get updated standings
        print("\n🏅 Getting final standings...")
        self.test_get_standings(season_id)

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