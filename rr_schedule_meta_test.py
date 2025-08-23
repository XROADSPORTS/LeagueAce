#!/usr/bin/env python3
"""
Round Robin Schedule Meta Endpoint Testing
Testing GET /api/rr/schedule-meta endpoint as requested in review
"""

import requests
import json
import uuid
from datetime import datetime, timezone

class RRScheduleMetaTester:
    def __init__(self, base_url="https://teamace.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_tier_id = None
        self.test_users = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        if params:
            print(f"   Params: {params}")
        
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
        """Create test users and tier for testing"""
        print("\n🔧 Setting up test environment...")
        
        # Create test users
        for i in range(4):
            user_data = {
                "name": f"RR Test Player {i+1}",
                "email": f"rrtest{i+1}_{datetime.now().strftime('%H%M%S')}@test.com",
                "rating_level": 4.0 + (i * 0.1)
            }
            success, response = self.run_test(
                f"Create Test User {i+1}",
                "POST",
                "users",
                200,
                data=user_data
            )
            if success and 'id' in response:
                self.test_users.append(response['id'])
                print(f"   Created User {i+1} ID: {response['id']}")

        # Generate a test tier ID
        self.test_tier_id = str(uuid.uuid4())
        print(f"   Test Tier ID: {self.test_tier_id}")

        return len(self.test_users) >= 4

    def test_schedule_meta_non_existing_tier(self):
        """Test GET /api/rr/schedule-meta with non-existing tier (should return defaults)"""
        non_existing_tier = str(uuid.uuid4())
        success, response = self.run_test(
            "Schedule Meta - Non-existing Tier",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": non_existing_tier}
        )
        
        if success:
            # Verify fallback to zeros as mentioned in review request
            expected_keys = ["tier_id", "feasibility_score", "schedule_quality", "conflicts"]
            for key in expected_keys:
                if key not in response:
                    print(f"❌ Missing expected key: {key}")
                    return False
            
            if response.get("feasibility_score") != 0:
                print(f"❌ Expected feasibility_score=0, got {response.get('feasibility_score')}")
                return False
                
            if response.get("schedule_quality") != 0:
                print(f"❌ Expected schedule_quality=0, got {response.get('schedule_quality')}")
                return False
                
            if response.get("conflicts") != {}:
                print(f"❌ Expected empty conflicts, got {response.get('conflicts')}")
                return False
                
            print("✅ Correctly returns default values for non-existing tier")
        
        return success

    def test_schedule_meta_with_scheduling(self):
        """Test GET /api/rr/schedule-meta after creating a schedule"""
        if not self.test_tier_id or len(self.test_users) < 4:
            print("❌ Skipping - Test environment not ready")
            return False

        # Step 1: Configure the tier
        config_data = {
            "season_name": "Test Season",
            "season_length": 4,
            "minimize_repeat_partners": True,
            "track_first_match_badge": True,
            "track_finished_badge": True,
            "subgroup_labels": ["Test Group"],
            "subgroup_size": 4
        }
        
        success, _ = self.run_test(
            "Configure RR Tier",
            "POST",
            f"rr/tiers/{self.test_tier_id}/configure",
            200,
            data=config_data
        )
        
        if not success:
            return False

        # Step 2: Generate subgroups
        subgroup_data = {
            "player_ids": self.test_users[:4]
        }
        
        success, _ = self.run_test(
            "Generate Subgroups",
            "POST",
            f"rr/tiers/{self.test_tier_id}/subgroups/generate",
            200,
            data=subgroup_data
        )
        
        if not success:
            return False

        # Step 3: Create schedule
        schedule_data = {
            "player_ids": self.test_users[:4],
            "week_windows": {
                0: "Monday Morning",
                1: "Wednesday Evening"
            }
        }
        
        success, schedule_response = self.run_test(
            "Create Schedule",
            "POST",
            f"rr/tiers/{self.test_tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if not success:
            return False

        # Verify schedule response has required fields
        expected_schedule_keys = ["status", "weeks", "feasibility_score", "conflicts", "schedule_quality"]
        for key in expected_schedule_keys:
            if key not in schedule_response:
                print(f"❌ Schedule response missing key: {key}")
                return False

        print(f"   Schedule created with feasibility_score: {schedule_response.get('feasibility_score')}")
        print(f"   Schedule quality: {schedule_response.get('schedule_quality')}")

        # Step 4: Test schedule-meta endpoint after scheduling
        success, meta_response = self.run_test(
            "Schedule Meta - After Scheduling",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": self.test_tier_id}
        )
        
        if success:
            # Verify response structure
            expected_keys = ["tier_id", "feasibility_score", "schedule_quality", "conflicts"]
            for key in expected_keys:
                if key not in meta_response:
                    print(f"❌ Missing expected key: {key}")
                    return False
            
            # Verify values match what was created during scheduling
            if meta_response.get("tier_id") != self.test_tier_id:
                print(f"❌ Tier ID mismatch: expected {self.test_tier_id}, got {meta_response.get('tier_id')}")
                return False
                
            # Feasibility score should be > 0 since we created matches
            if meta_response.get("feasibility_score", 0) <= 0:
                print(f"❌ Expected feasibility_score > 0, got {meta_response.get('feasibility_score')}")
                return False
                
            # Schedule quality should be present (can be 0 or positive)
            if "schedule_quality" not in meta_response:
                print("❌ Missing schedule_quality field")
                return False
                
            # Conflicts should be a dict
            if not isinstance(meta_response.get("conflicts"), dict):
                print(f"❌ Expected conflicts to be dict, got {type(meta_response.get('conflicts'))}")
                return False
                
            print("✅ Schedule meta endpoint returns correct data after scheduling")
            print(f"   Feasibility Score: {meta_response.get('feasibility_score')}")
            print(f"   Schedule Quality: {meta_response.get('schedule_quality')}")
            print(f"   Conflicts: {meta_response.get('conflicts')}")
        
        return success

    def test_health_endpoint(self):
        """Test health endpoint to verify no regressions"""
        success, response = self.run_test(
            "Health Endpoint",
            "GET",
            "health",
            200
        )
        
        if success:
            if response.get("status") != "ok":
                print(f"❌ Expected status=ok, got {response.get('status')}")
                return False
            if "time" not in response:
                print("❌ Missing time field in health response")
                return False
            print("✅ Health endpoint working correctly")
        
        return success

    def run_all_tests(self):
        """Run all schedule meta tests"""
        print("🎾 Starting Round Robin Schedule Meta Endpoint Testing")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return False

        # Test cases
        test_methods = [
            self.test_health_endpoint,
            self.test_schedule_meta_non_existing_tier,
            self.test_schedule_meta_with_scheduling,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🎾 ROUND ROBIN SCHEDULE META TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run*100):.1f}% success rate)")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED - Schedule Meta endpoint working correctly!")
            return True
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return False

if __name__ == "__main__":
    tester = RRScheduleMetaTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)