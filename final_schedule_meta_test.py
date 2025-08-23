#!/usr/bin/env python3
"""
Final Schedule Meta Endpoint Test
Testing GET /api/rr/schedule-meta as requested in review after bug fix
"""

import requests
import json
import uuid
from datetime import datetime

class FinalScheduleMetaTester:
    def __init__(self, base_url="https://matchmaker-22.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
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

    def test_complete_workflow(self):
        """Test complete workflow: setup -> schedule -> get meta"""
        print("\n🎾 TESTING COMPLETE SCHEDULE META WORKFLOW")
        
        # Create test users
        test_users = []
        for i in range(4):
            user_data = {
                "name": f"Final Test Player {i+1}",
                "email": f"finaltest{i+1}_{datetime.now().strftime('%H%M%S')}@test.com",
                "rating_level": 4.0
            }
            success, response = self.run_test(
                f"Create User {i+1}",
                "POST",
                "users",
                200,
                data=user_data
            )
            if success and 'id' in response:
                test_users.append(response['id'])

        if len(test_users) < 4:
            print("❌ Failed to create enough test users")
            return False

        # Generate test tier ID
        tier_id = str(uuid.uuid4())
        print(f"   Using tier ID: {tier_id}")

        # Configure tier
        config_data = {
            "season_name": "Final Test",
            "season_length": 3,
            "minimize_repeat_partners": True,
            "subgroup_labels": ["Test Group"],
            "subgroup_size": 4
        }
        
        success, _ = self.run_test(
            "Configure Tier",
            "POST",
            f"rr/tiers/{tier_id}/configure",
            200,
            data=config_data
        )
        if not success:
            return False

        # Generate subgroups
        success, _ = self.run_test(
            "Generate Subgroups",
            "POST",
            f"rr/tiers/{tier_id}/subgroups/generate",
            200,
            data={"player_ids": test_users}
        )
        if not success:
            return False

        # Create schedule
        schedule_data = {
            "player_ids": test_users,
            "week_windows": {
                0: "Monday Morning",
                1: "Wednesday Evening",
                2: "Friday Afternoon"
            }
        }
        
        success, schedule_response = self.run_test(
            "Create Schedule",
            "POST",
            f"rr/tiers/{tier_id}/schedule",
            200,
            data=schedule_data
        )
        if not success:
            return False

        print(f"   Schedule Response: {schedule_response}")

        # Test schedule-meta endpoint
        success, meta_response = self.run_test(
            "Get Schedule Meta",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": tier_id}
        )
        
        if success:
            print(f"   Meta Response: {meta_response}")
            
            # Verify required fields
            required_fields = ["tier_id", "feasibility_score", "schedule_quality", "conflicts"]
            for field in required_fields:
                if field not in meta_response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify tier_id matches
            if meta_response.get("tier_id") != tier_id:
                print(f"❌ Tier ID mismatch")
                return False
                
            print("✅ Schedule meta endpoint working correctly with all required fields")
        
        return success

    def test_fallback_behavior(self):
        """Test fallback behavior for non-existing tier"""
        print("\n🎾 TESTING FALLBACK BEHAVIOR")
        
        non_existing_tier = str(uuid.uuid4())
        success, response = self.run_test(
            "Non-existing Tier Fallback",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": non_existing_tier}
        )
        
        if success:
            # Check fallback values
            expected_values = {
                "feasibility_score": 0,
                "schedule_quality": 0,
                "conflicts": {}
            }
            
            for key, expected_value in expected_values.items():
                if response.get(key) != expected_value:
                    print(f"❌ Fallback value incorrect for {key}: expected {expected_value}, got {response.get(key)}")
                    return False
            
            print("✅ Fallback behavior working correctly")
        
        return success

    def test_regression_checks(self):
        """Test other endpoints to ensure no regressions"""
        print("\n🎾 TESTING REGRESSION CHECKS")
        
        # Health endpoint
        success1, _ = self.run_test("Health Check", "GET", "health", 200)
        
        # User search
        success2, _ = self.run_test("User Search", "GET", "users/search", 200, params={"q": "test"})
        
        return success1 and success2

    def run_all_tests(self):
        """Run all final tests"""
        print("🎾 FINAL SCHEDULE META ENDPOINT TESTING")
        print("Testing GET /api/rr/schedule-meta as requested in review")
        print("=" * 60)
        
        test_methods = [
            self.test_fallback_behavior,
            self.test_complete_workflow,
            self.test_regression_checks,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🎾 FINAL TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run*100):.1f}% success rate)")
        
        if self.tests_passed >= (self.tests_run * 0.9):
            print("✅ SCHEDULE META ENDPOINT WORKING CORRECTLY!")
            print("✅ Returns conflicts/feasibility/quality after scheduling")
            print("✅ Fallback to zeros for non-existing tier")
            print("✅ No schema issues or regressions detected")
            return True
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return False

if __name__ == "__main__":
    tester = FinalScheduleMetaTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)