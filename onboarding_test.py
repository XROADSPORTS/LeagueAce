#!/usr/bin/env python3
"""
Backend Onboarding Endpoints Test Suite
Tests the new backend endpoints required for frontend onboarding:
1. POST /api/auth/social-login - creates or updates user; returns user with id, lan, role, sports_preferences
2. GET /api/users/{id}/notifications - returns empty list or notifications when created by rr_notify
3. PATCH /api/users/{id}/sports - persists sports preferences and returns updated user
4. GET /api/users/{id} - verify user retrieval works
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

class OnboardingAPITester:
    def __init__(self, base_url="https://teamace.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_users = []
        
    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Dict[Any, Any] = None, params: Dict[str, Any] = None) -> tuple[bool, Dict[Any, Any]]:
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
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

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

    def test_social_login_new_user(self):
        """Test POST /api/auth/social-login creates new user with all required fields"""
        timestamp = datetime.now().strftime('%H%M%S')
        social_data = {
            "provider": "Google",
            "token": f"mock_google_token_{timestamp}",
            "email": f"sarah.johnson_{timestamp}@gmail.com",
            "name": "Sarah Johnson",
            "provider_id": f"google_{timestamp}"
        }
        
        success, response = self.run_test(
            "Social Login - New User Creation",
            "POST",
            "auth/social-login",
            200,
            data=social_data
        )
        
        if success:
            # Verify all required fields are present
            required_fields = ['id', 'lan', 'role', 'sports_preferences']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False
            
            print(f"   ✅ User created with ID: {response['id']}")
            print(f"   ✅ LAN code: {response['lan']}")
            print(f"   ✅ Role: {response['role']}")
            print(f"   ✅ Sports preferences: {response['sports_preferences']}")
            print(f"   ✅ Email: {response['email']}")
            print(f"   ✅ Name: {response['name']}")
            
            # Store user for further testing
            self.created_users.append({
                'id': response['id'],
                'email': response['email'],
                'name': response['name'],
                'lan': response['lan']
            })
            
            # Verify default values
            if (response['role'] == 'Player' and 
                isinstance(response['sports_preferences'], list) and
                response['lan'].startswith('LAN-')):
                print("   ✅ Default values set correctly")
                return True
            else:
                print("   ❌ Default values not as expected")
                return False
        
        return success

    def test_social_login_existing_user(self):
        """Test POST /api/auth/social-login updates existing user"""
        if not self.created_users:
            print("❌ Skipping - No existing user available")
            return False
        
        existing_user = self.created_users[0]
        
        # Login with same email but different name
        social_data = {
            "provider": "Google",
            "token": "updated_token_123",
            "email": existing_user['email'],
            "name": "Sarah Johnson-Smith",  # Updated name
            "provider_id": "google_updated_123"
        }
        
        success, response = self.run_test(
            "Social Login - Existing User Update",
            "POST",
            "auth/social-login",
            200,
            data=social_data
        )
        
        if success:
            # Should return same user ID but updated name
            if (response['id'] == existing_user['id'] and 
                response['name'] == "Sarah Johnson-Smith" and
                response['email'] == existing_user['email']):
                print(f"   ✅ Existing user updated correctly")
                print(f"   ✅ Same ID: {response['id']}")
                print(f"   ✅ Updated name: {response['name']}")
                return True
            else:
                print("   ❌ Existing user not updated correctly")
                return False
        
        return success

    def test_get_user_by_id(self):
        """Test GET /api/users/{id} returns user data"""
        if not self.created_users:
            print("❌ Skipping - No user available")
            return False
        
        user = self.created_users[0]
        user_id = user['id']
        
        success, response = self.run_test(
            "Get User by ID",
            "GET",
            f"users/{user_id}",
            200
        )
        
        if success:
            # Verify user data matches
            if (response['id'] == user_id and 
                response['email'] == user['email']):
                print(f"   ✅ User retrieved correctly")
                print(f"   ✅ ID: {response['id']}")
                print(f"   ✅ Email: {response['email']}")
                print(f"   ✅ Name: {response['name']}")
                print(f"   ✅ LAN: {response['lan']}")
                return True
            else:
                print("   ❌ User data doesn't match")
                return False
        
        return success

    def test_get_user_notifications_empty(self):
        """Test GET /api/users/{id}/notifications returns empty list for new user"""
        if not self.created_users:
            print("❌ Skipping - No user available")
            return False
        
        user_id = self.created_users[0]['id']
        
        success, response = self.run_test(
            "Get User Notifications - Empty",
            "GET",
            f"users/{user_id}/notifications",
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Returned list with {len(response)} notifications")
                if len(response) == 0:
                    print("   ✅ Empty list for new user (expected)")
                else:
                    print("   ℹ️  User has existing notifications")
                return True
            else:
                print("   ❌ Response is not a list")
                return False
        
        return success

    def test_create_notification_and_retrieve(self):
        """Test creating a notification via rr_notify and retrieving it"""
        if not self.created_users:
            print("❌ Skipping - No user available")
            return False
        
        user_id = self.created_users[0]['id']
        
        # Create a notification by calling an endpoint that uses rr_notify
        # We'll use the RR availability endpoint which should trigger notifications
        availability_data = {
            "user_id": user_id,
            "windows": ["Mon AM", "Wed PM", "Sat Morning"]
        }
        
        success, response = self.run_test(
            "Set User Availability (triggers notification)",
            "PUT",
            "rr/availability",
            200,
            data=availability_data
        )
        
        if not success:
            print("   ⚠️  Could not create notification via availability endpoint")
            # This is not a failure of the notifications endpoint itself
            return True
        
        # Now check if notifications were created
        success, response = self.run_test(
            "Get User Notifications - After Activity",
            "GET",
            f"users/{user_id}/notifications",
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Retrieved {len(response)} notifications")
                for i, notification in enumerate(response):
                    if isinstance(notification, dict):
                        print(f"   Notification {i+1}:")
                        print(f"     - Message: {notification.get('message', 'No message')}")
                        print(f"     - Created: {notification.get('created_at', 'No timestamp')}")
                return True
            else:
                print("   ❌ Response is not a list")
                return False
        
        return success

    def test_update_sports_preferences(self):
        """Test PATCH /api/users/{id}/sports persists sports preferences"""
        if not self.created_users:
            print("❌ Skipping - No user available")
            return False
        
        user_id = self.created_users[0]['id']
        
        # Update sports preferences
        sports_data = {
            "sports_preferences": ["Tennis", "Pickleball", "Badminton"]
        }
        
        success, response = self.run_test(
            "Update Sports Preferences",
            "PATCH",
            f"users/{user_id}/sports",
            200,
            data=sports_data
        )
        
        if success:
            # Verify the response contains updated sports preferences
            if (response.get('sports_preferences') == sports_data['sports_preferences'] and
                response.get('id') == user_id):
                print(f"   ✅ Sports preferences updated successfully")
                print(f"   ✅ Updated preferences: {response['sports_preferences']}")
                return True
            else:
                print("   ❌ Sports preferences not updated correctly")
                return False
        
        return success

    def test_sports_preferences_persistence(self):
        """Test that sports preferences persist by retrieving user again"""
        if not self.created_users:
            print("❌ Skipping - No user available")
            return False
        
        user_id = self.created_users[0]['id']
        
        success, response = self.run_test(
            "Verify Sports Preferences Persistence",
            "GET",
            f"users/{user_id}",
            200
        )
        
        if success:
            expected_sports = ["Tennis", "Pickleball", "Badminton"]
            if response.get('sports_preferences') == expected_sports:
                print(f"   ✅ Sports preferences persisted correctly")
                print(f"   ✅ Persisted preferences: {response['sports_preferences']}")
                return True
            else:
                print(f"   ❌ Sports preferences not persisted")
                print(f"   Expected: {expected_sports}")
                print(f"   Got: {response.get('sports_preferences')}")
                return False
        
        return success

    def test_invalid_user_id_endpoints(self):
        """Test endpoints with invalid user IDs return 404"""
        invalid_user_id = str(uuid.uuid4())
        
        # Test GET /api/users/{invalid_id}
        success1, _ = self.run_test(
            "Get Invalid User ID",
            "GET",
            f"users/{invalid_user_id}",
            404
        )
        
        # Test GET /api/users/{invalid_id}/notifications
        success2, _ = self.run_test(
            "Get Notifications for Invalid User ID",
            "GET",
            f"users/{invalid_user_id}/notifications",
            200  # This might return empty list instead of 404
        )
        
        # Test PATCH /api/users/{invalid_id}/sports
        success3, _ = self.run_test(
            "Update Sports for Invalid User ID",
            "PATCH",
            f"users/{invalid_user_id}/sports",
            404,
            data={"sports_preferences": ["Tennis"]}
        )
        
        if success1 and success3:
            print("   ✅ Invalid user ID handling working correctly")
            return True
        else:
            print("   ❌ Invalid user ID handling not working correctly")
            return False

    def test_social_login_missing_fields(self):
        """Test social login with missing required fields"""
        # Missing email
        incomplete_data = {
            "provider": "Google",
            "token": "test_token",
            "name": "Test User",
            "provider_id": "google_123"
            # Missing email
        }
        
        success, _ = self.run_test(
            "Social Login - Missing Email",
            "POST",
            "auth/social-login",
            422,  # Validation error
            data=incomplete_data
        )
        
        return success

    def test_sports_preferences_invalid_data(self):
        """Test sports preferences update with invalid data"""
        if not self.created_users:
            print("❌ Skipping - No user available")
            return False
        
        user_id = self.created_users[0]['id']
        
        # Invalid data type (not a list)
        invalid_data = {
            "sports_preferences": "Tennis"  # Should be a list
        }
        
        success, _ = self.run_test(
            "Update Sports Preferences - Invalid Data",
            "PATCH",
            f"users/{user_id}/sports",
            422,  # Validation error
            data=invalid_data
        )
        
        return success

    def run_all_tests(self):
        """Run all onboarding endpoint tests"""
        print("🚀 Starting Backend Onboarding Endpoints Test Suite")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            self.test_social_login_new_user,
            self.test_social_login_existing_user,
            self.test_get_user_by_id,
            self.test_get_user_notifications_empty,
            self.test_create_notification_and_retrieve,
            self.test_update_sports_preferences,
            self.test_sports_preferences_persistence,
            
            # Error handling tests
            self.test_invalid_user_id_endpoints,
            self.test_social_login_missing_fields,
            self.test_sports_preferences_invalid_data,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
                self.tests_run += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - see details above")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = OnboardingAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)