import requests
import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

class PhaseABackendTester:
    def __init__(self, base_url="https://doubles-master.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_users = {}  # Store created users by email
        self.tier_id = None
        
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

    def test_scope_a_1_new_user_google_league_manager(self):
        """Scope A.1: New user (Google) as League Manager"""
        social_data = {
            "provider": "Google",
            "token": "mock_google_token_manager",
            "email": "manager.user@gmail.com",
            "name": "Manager User",
            "provider_id": "g_1",
            "role": "League Manager"
        }
        
        success, response = self.run_test(
            "Social Login - New Google User as League Manager",
            "POST",
            "auth/social-login",
            200,
            data=social_data
        )
        
        if success:
            # Verify response contains expected fields
            expected_fields = ['id', 'lan', 'role', 'sports_preferences']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
            
            if response.get('role') != 'League Manager':
                print(f"   ❌ Expected role 'League Manager', got '{response.get('role')}'")
                return False
            
            if not isinstance(response.get('sports_preferences'), list):
                print(f"   ❌ sports_preferences should be array, got {type(response.get('sports_preferences'))}")
                return False
            
            print(f"   ✅ User ID: {response['id']}")
            print(f"   ✅ LAN: {response['lan']}")
            print(f"   ✅ Role: {response['role']}")
            print(f"   ✅ Sports Preferences: {response['sports_preferences']}")
            
            self.created_users['manager.user@gmail.com'] = response
            
            # Test GET /api/users/{id} returns role "League Manager"
            user_id = response['id']
            success2, user_response = self.run_test(
                "Get User by ID - Verify League Manager Role",
                "GET",
                f"users/{user_id}",
                200
            )
            
            if success2:
                if user_response.get('role') != 'League Manager':
                    print(f"   ❌ GET user role mismatch: expected 'League Manager', got '{user_response.get('role')}'")
                    return False
                print(f"   ✅ GET /api/users/{user_id} confirms role: {user_response.get('role')}")
            
            return success2
        
        return success

    def test_scope_a_2_escalate_player_to_manager(self):
        """Scope A.2: Escalate existing Player to League Manager"""
        # First create user as Player
        player_data = {
            "provider": "Google",
            "token": "mock_google_token_player",
            "email": "player.to.manager@gmail.com",
            "name": "Player To Manager",
            "provider_id": "g_2",
            "role": "Player"
        }
        
        success, response = self.run_test(
            "Social Login - Create User as Player",
            "POST",
            "auth/social-login",
            200,
            data=player_data
        )
        
        if not success:
            return False
        
        if response.get('role') != 'Player':
            print(f"   ❌ Initial role should be 'Player', got '{response.get('role')}'")
            return False
        
        user_id = response['id']
        print(f"   ✅ Created user as Player with ID: {user_id}")
        
        # Re-login same email with role "League Manager"
        manager_data = {
            "provider": "Google",
            "token": "mock_google_token_manager_escalate",
            "email": "player.to.manager@gmail.com",
            "name": "Player To Manager",
            "provider_id": "g_2",
            "role": "League Manager"
        }
        
        success2, response2 = self.run_test(
            "Social Login - Escalate to League Manager",
            "POST",
            "auth/social-login",
            200,
            data=manager_data
        )
        
        if success2:
            if response2.get('role') != 'League Manager':
                print(f"   ❌ Escalated role should be 'League Manager', got '{response2.get('role')}'")
                return False
            
            if response2.get('id') != user_id:
                print(f"   ❌ User ID should remain same after escalation: {user_id} vs {response2.get('id')}")
                return False
            
            print(f"   ✅ Role escalated to: {response2.get('role')}")
            
            # Verify GET /api/users/{id} reflects updated role
            success3, user_response = self.run_test(
                "Get User by ID - Verify Escalated Role",
                "GET",
                f"users/{user_id}",
                200
            )
            
            if success3:
                if user_response.get('role') != 'League Manager':
                    print(f"   ❌ GET user role after escalation: expected 'League Manager', got '{user_response.get('role')}'")
                    return False
                print(f"   ✅ GET /api/users/{user_id} confirms escalated role: {user_response.get('role')}")
            
            self.created_users['player.to.manager@gmail.com'] = response2
            return success3
        
        return success2

    def test_scope_a_3_missing_role_defaults_player(self):
        """Scope A.3: Missing role defaults to Player"""
        social_data = {
            "provider": "Google",
            "token": "mock_google_token_no_role",
            "email": "no.role@gmail.com",
            "name": "No Role User",
            "provider_id": "g_3"
            # Note: no "role" field provided
        }
        
        success, response = self.run_test(
            "Social Login - Missing Role Defaults to Player",
            "POST",
            "auth/social-login",
            200,
            data=social_data
        )
        
        if success:
            if response.get('role') != 'Player':
                print(f"   ❌ Default role should be 'Player', got '{response.get('role')}'")
                return False
            
            print(f"   ✅ Default role assigned: {response.get('role')}")
            self.created_users['no.role@gmail.com'] = response
        
        return success

    def test_scope_a_4_sports_prefs_patch_works(self):
        """Scope A.4: Sports prefs patch still works"""
        # Use one of the created users
        if not self.created_users:
            print("   ❌ No users available for sports preferences test")
            return False
        
        user_email = list(self.created_users.keys())[0]
        user_data = self.created_users[user_email]
        user_id = user_data['id']
        
        # PATCH sports preferences
        sports_data = {
            "sports_preferences": ["Tennis"]
        }
        
        success, response = self.run_test(
            "PATCH User Sports Preferences",
            "PATCH",
            f"users/{user_id}/sports",
            200,
            data=sports_data
        )
        
        if success:
            if response.get('sports_preferences') != ["Tennis"]:
                print(f"   ❌ Sports preferences not updated correctly: {response.get('sports_preferences')}")
                return False
            
            print(f"   ✅ Sports preferences updated: {response.get('sports_preferences')}")
            
            # GET to confirm field updated
            success2, user_response = self.run_test(
                "GET User - Confirm Sports Preferences Updated",
                "GET",
                f"users/{user_id}",
                200
            )
            
            if success2:
                if user_response.get('sports_preferences') != ["Tennis"]:
                    print(f"   ❌ GET sports preferences mismatch: {user_response.get('sports_preferences')}")
                    return False
                print(f"   ✅ GET confirms sports preferences: {user_response.get('sports_preferences')}")
            
            return success2
        
        return success

    def test_scope_a_5_manager_leagues_empty_graceful(self):
        """Scope A.5: Manager leagues endpoint handles empty gracefully"""
        # Use the League Manager user
        manager_user = None
        for email, user_data in self.created_users.items():
            if user_data.get('role') == 'League Manager':
                manager_user = user_data
                break
        
        if not manager_user:
            print("   ❌ No League Manager user available")
            return False
        
        user_id = manager_user['id']
        
        success, response = self.run_test(
            "GET Manager Leagues - Empty Graceful",
            "GET",
            f"users/{user_id}/leagues",
            200,
            params={"sport_type": "Tennis"}
        )
        
        if success:
            if not isinstance(response, list):
                print(f"   ❌ Response should be array, got {type(response)}")
                return False
            
            print(f"   ✅ Returned empty array gracefully: {response}")
        
        return success

    def test_scope_b_6_rr_availability_endpoints(self):
        """Scope B.6: RR availability endpoints reachable"""
        # Create a test user for availability testing
        if not self.created_users:
            print("   ❌ No users available for RR availability test")
            return False
        
        user_data = list(self.created_users.values())[0]
        user_id = user_data['id']
        
        # Create a dummy tier_id for testing
        self.tier_id = "test_tier_123"
        
        # PUT availability
        availability_data = {
            "user_id": user_id,
            "tier_id": self.tier_id,
            "availability": {"0": ["Sat 9-12"]}
        }
        
        success, response = self.run_test(
            "PUT RR Availability",
            "PUT",
            "rr/availability",
            200,
            data=availability_data
        )
        
        if success:
            print(f"   ✅ PUT availability successful")
            
            # GET availability
            success2, response2 = self.run_test(
                "GET RR Availability",
                "GET",
                "rr/availability",
                200,
                params={"user_id": user_id, "tier_id": self.tier_id}
            )
            
            if success2:
                print(f"   ✅ GET availability successful")
                print(f"   Response: {response2}")
                
                # Verify structure matches what we set
                if response2.get('user_id') == user_id:
                    print(f"   ✅ User ID matches: {response2.get('user_id')}")
                else:
                    print(f"   ❌ User ID mismatch: expected {user_id}, got {response2.get('user_id')}")
                    return False
            
            return success2
        
        return success

    def test_scope_b_7_rr_standings_empty_graceful(self):
        """Scope B.7: RR standings endpoint reachable (no data)"""
        # Use dummy tier_id
        tier_id = "empty_tier_456"
        
        success, response = self.run_test(
            "GET RR Standings - Empty Graceful",
            "GET",
            "rr/standings",
            200,
            params={"tier_id": tier_id}
        )
        
        if success:
            print(f"   ✅ Standings endpoint reachable")
            print(f"   Response structure: {list(response.keys()) if isinstance(response, dict) else type(response)}")
            
            # Should return empty/default structure without 500
            if isinstance(response, dict):
                if 'rows' in response:
                    print(f"   ✅ Contains 'rows' field: {len(response.get('rows', []))} rows")
                else:
                    print(f"   ⚠️  No 'rows' field in response")
            
            # The key is that it doesn't return 500 error
            print(f"   ✅ No 500 error - endpoint handles empty data gracefully")
        
        return success

    def run_all_tests(self):
        """Run all Phase A tests"""
        print("🚀 Starting Backend Phase A Tests - Role-aware Social Login & RR Stability")
        print("=" * 80)
        
        # Scope A: Auth/social-login role handling
        print("\n📋 SCOPE A: Auth/Social-Login Role Handling")
        print("-" * 50)
        
        tests = [
            self.test_scope_a_1_new_user_google_league_manager,
            self.test_scope_a_2_escalate_player_to_manager,
            self.test_scope_a_3_missing_role_defaults_player,
            self.test_scope_a_4_sports_prefs_patch_works,
            self.test_scope_a_5_manager_leagues_empty_graceful,
        ]
        
        scope_a_passed = 0
        for test in tests:
            if test():
                scope_a_passed += 1
        
        print(f"\n📊 Scope A Results: {scope_a_passed}/{len(tests)} tests passed")
        
        # Scope B: Regression spot-check RR core
        print("\n📋 SCOPE B: Regression Spot-check RR Core")
        print("-" * 50)
        
        rr_tests = [
            self.test_scope_b_6_rr_availability_endpoints,
            self.test_scope_b_7_rr_standings_empty_graceful,
        ]
        
        scope_b_passed = 0
        for test in rr_tests:
            if test():
                scope_b_passed += 1
        
        print(f"\n📊 Scope B Results: {scope_b_passed}/{len(rr_tests)} tests passed")
        
        # Final summary
        total_passed = scope_a_passed + scope_b_passed
        total_tests = len(tests) + len(rr_tests)
        
        print("\n" + "=" * 80)
        print(f"🎯 PHASE A BACKEND TESTING COMPLETE")
        print(f"📊 Overall Results: {total_passed}/{total_tests} tests passed ({(total_passed/total_tests)*100:.1f}%)")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"📝 Tests Run: {self.tests_run}")
        
        if total_passed == total_tests:
            print("🎉 ALL TESTS PASSED! Backend Phase A functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the detailed output above for issues.")
            
        return total_passed == total_tests

if __name__ == "__main__":
    tester = PhaseABackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)