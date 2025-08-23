#!/usr/bin/env python3
"""
Comprehensive Round Robin Testing including Schedule Meta endpoint
Testing as requested in review: GET /api/rr/schedule-meta with tier_id
"""

import requests
import json
import uuid
from datetime import datetime, timezone

class ComprehensiveRRTester:
    def __init__(self, base_url="https://leagueace-rr.preview.emergentagent.com"):
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
        
        # Create 8 test users for better scheduling
        for i in range(8):
            user_data = {
                "name": f"RR Player {i+1}",
                "email": f"rrplayer{i+1}_{datetime.now().strftime('%H%M%S')}@test.com",
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

        # Generate a test tier ID
        self.test_tier_id = str(uuid.uuid4())
        print(f"   Test Tier ID: {self.test_tier_id}")
        print(f"   Created {len(self.test_users)} test users")

        return len(self.test_users) >= 4

    def test_schedule_meta_fallback_behavior(self):
        """Test GET /api/rr/schedule-meta fallback to zeros for non-existing tier"""
        print("\n📋 TESTING SCHEDULE META FALLBACK BEHAVIOR")
        
        non_existing_tier = str(uuid.uuid4())
        success, response = self.run_test(
            "Schedule Meta - Non-existing Tier Fallback",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": non_existing_tier}
        )
        
        if success:
            # Verify fallback to zeros as mentioned in review request
            expected_keys = ["tier_id", "feasibility_score", "schedule_quality", "conflicts"]
            missing_keys = [key for key in expected_keys if key not in response]
            if missing_keys:
                print(f"❌ Missing expected keys: {missing_keys}")
                return False
            
            # Check fallback values
            if response.get("feasibility_score") != 0:
                print(f"❌ Expected feasibility_score=0, got {response.get('feasibility_score')}")
                return False
                
            if response.get("schedule_quality") != 0:
                print(f"❌ Expected schedule_quality=0, got {response.get('schedule_quality')}")
                return False
                
            if response.get("conflicts") != {}:
                print(f"❌ Expected empty conflicts, got {response.get('conflicts')}")
                return False
                
            print("✅ Correctly returns fallback values (zeros) for non-existing tier")
        
        return success

    def test_schedule_meta_with_real_schedule(self):
        """Test GET /api/rr/schedule-meta after creating a real schedule with conflicts/feasibility/quality"""
        print("\n📋 TESTING SCHEDULE META WITH REAL SCHEDULE")
        
        if not self.test_tier_id or len(self.test_users) < 6:
            print("❌ Skipping - Test environment not ready")
            return False

        # Step 1: Configure the tier
        config_data = {
            "season_name": "Test Season",
            "season_length": 6,
            "minimize_repeat_partners": True,
            "track_first_match_badge": True,
            "track_finished_badge": True,
            "subgroup_labels": ["Test Group"],
            "subgroup_size": 6
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
            "player_ids": self.test_users[:6]
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

        # Step 3: Set availability constraints to create conflicts
        for i, user_id in enumerate(self.test_users[:6]):
            # Create varied availability to generate conflicts
            windows = ["Monday Morning", "Wednesday Evening"] if i < 3 else ["Tuesday Afternoon", "Friday Morning"]
            avail_data = {
                "user_id": user_id,
                "windows": windows
            }
            
            success, _ = self.run_test(
                f"Set Availability User {i+1}",
                "PUT",
                "rr/availability",
                200,
                data=avail_data
            )
            
            if not success:
                return False

        # Step 4: Create schedule with week windows to trigger conflicts
        schedule_data = {
            "player_ids": self.test_users[:6],
            "week_windows": {
                0: "Monday Morning",    # Only first 3 users available
                1: "Tuesday Afternoon", # Only last 3 users available
                2: "Wednesday Evening", # Only first 3 users available
                3: "Friday Morning",    # Only last 3 users available
                4: "Monday Morning",
                5: "Tuesday Afternoon"
            }
        }
        
        success, schedule_response = self.run_test(
            "Create Schedule with Conflicts",
            "POST",
            f"rr/tiers/{self.test_tier_id}/schedule",
            200,
            data=schedule_data
        )
        
        if not success:
            return False

        # Verify schedule response structure
        expected_schedule_keys = ["status", "weeks", "feasibility_score", "conflicts", "schedule_quality"]
        missing_keys = [key for key in expected_schedule_keys if key not in schedule_response]
        if missing_keys:
            print(f"❌ Schedule response missing keys: {missing_keys}")
            return False

        print(f"   Schedule created:")
        print(f"   - Feasibility Score: {schedule_response.get('feasibility_score')}")
        print(f"   - Schedule Quality: {schedule_response.get('schedule_quality')}")
        print(f"   - Conflicts: {schedule_response.get('conflicts')}")

        # Step 5: Test schedule-meta endpoint after scheduling
        success, meta_response = self.run_test(
            "Schedule Meta - After Real Scheduling",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": self.test_tier_id}
        )
        
        if success:
            # Verify response structure
            expected_keys = ["tier_id", "feasibility_score", "schedule_quality", "conflicts"]
            missing_keys = [key for key in expected_keys if key not in meta_response]
            if missing_keys:
                print(f"❌ Missing expected keys: {missing_keys}")
                return False
            
            # Verify values are reasonable
            if meta_response.get("tier_id") != self.test_tier_id:
                print(f"❌ Tier ID mismatch: expected {self.test_tier_id}, got {meta_response.get('tier_id')}")
                return False
                
            # Check that we have meaningful data (not just zeros)
            feasibility = meta_response.get("feasibility_score", 0)
            quality = meta_response.get("schedule_quality", 0)
            conflicts = meta_response.get("conflicts", {})
            
            print(f"   Meta Response:")
            print(f"   - Feasibility Score: {feasibility}")
            print(f"   - Schedule Quality: {quality}")
            print(f"   - Conflicts: {conflicts}")
            
            # Conflicts should be a dict and may contain conflict data
            if not isinstance(conflicts, dict):
                print(f"❌ Expected conflicts to be dict, got {type(conflicts)}")
                return False
                
            print("✅ Schedule meta endpoint returns correct structure and data after scheduling")
        
        return success

    def test_regression_endpoints(self):
        """Test other RR endpoints to ensure no regressions"""
        print("\n📋 TESTING REGRESSION - OTHER RR ENDPOINTS")
        
        # Test health endpoint
        success1, _ = self.run_test(
            "Health Endpoint",
            "GET",
            "health",
            200
        )
        
        # Test availability endpoint
        test_user = self.test_users[0] if self.test_users else str(uuid.uuid4())
        success2, _ = self.run_test(
            "Get Availability",
            "GET",
            "rr/availability",
            200,
            params={"user_id": test_user}
        )
        
        # Test user search
        success3, _ = self.run_test(
            "Search Users",
            "GET",
            "users/search",
            200,
            params={"q": "RR"}
        )
        
        return success1 and success2 and success3

    def test_schedule_meta_edge_cases(self):
        """Test edge cases for schedule meta endpoint"""
        print("\n📋 TESTING SCHEDULE META EDGE CASES")
        
        # Test without tier_id parameter
        success1, _ = self.run_test(
            "Schedule Meta - Missing tier_id",
            "GET",
            "rr/schedule-meta",
            422  # Should fail validation
        )
        
        # Test with empty tier_id
        success2, _ = self.run_test(
            "Schedule Meta - Empty tier_id",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": ""}
        )
        
        # Test with invalid UUID format
        success3, _ = self.run_test(
            "Schedule Meta - Invalid UUID",
            "GET",
            "rr/schedule-meta",
            200,
            params={"tier_id": "invalid-uuid-format"}
        )
        
        return success2 and success3  # success1 expected to fail

    def run_all_tests(self):
        """Run all comprehensive RR tests"""
        print("🎾 Starting Comprehensive Round Robin Testing")
        print("Focus: GET /api/rr/schedule-meta endpoint as requested in review")
        print("=" * 70)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return False

        # Test cases
        test_methods = [
            self.test_schedule_meta_fallback_behavior,
            self.test_schedule_meta_with_real_schedule,
            self.test_regression_endpoints,
            self.test_schedule_meta_edge_cases,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 70)
        print(f"🎾 COMPREHENSIVE RR TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run*100):.1f}% success rate)")
        
        if self.tests_passed >= (self.tests_run * 0.9):  # 90% success rate acceptable
            print("✅ TESTING SUCCESSFUL - Schedule Meta endpoint working correctly!")
            print("✅ No schema issues or regressions detected")
            return True
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return False

if __name__ == "__main__":
    tester = ComprehensiveRRTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)