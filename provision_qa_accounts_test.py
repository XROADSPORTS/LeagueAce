#!/usr/bin/env python3
"""
QA Account Provisioning Test
Provision test accounts that align with the frontend's built-in mock Google sign-in emails
so the user can log in via UI and see the QA data immediately.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class QAAccountProvisioner:
    def __init__(self, base_url="https://leagueace-rr.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Store IDs for the provisioning workflow
        self.manager_id = None
        self.player_id = None
        self.league_id = None
        self.format_tier_id = None
        self.rating_tier_id = None
        self.join_code = None

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict[Any, Any]] = None, params: Optional[Dict[str, Any]] = None) -> tuple[bool, Dict[Any, Any]]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Step {self.tests_run}: {name}...")
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
                print(f"✅ Success - Status: {response.status_code}")
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

    def provision_manager_user(self):
        """Step 1: Upsert Manager user via POST /api/auth/social-login"""
        manager_data = {
            "provider": "Google",
            "token": "mock",
            "email": "manager.user@gmail.com",
            "name": "Manager User",
            "provider_id": "google_mgr_ui",
            "role": "League Manager"
        }
        
        success, response = self.run_test(
            "Upsert Manager User (manager.user@gmail.com)",
            "POST",
            "auth/social-login",
            200,
            data=manager_data
        )
        
        if success and 'id' in response:
            self.manager_id = response['id']
            print(f"   ✅ Manager ID: {self.manager_id}")
            print(f"   Name: {response.get('name')}")
            print(f"   Role: {response.get('role')}")
            return True
        
        return False

    def provision_player_user(self):
        """Step 2: Upsert Player user via POST /api/auth/social-login"""
        player_data = {
            "provider": "Google",
            "token": "mock",
            "email": "sarah.johnson@gmail.com",
            "name": "Sarah Johnson",
            "provider_id": "google_sarah_ui",
            "role": "Player",
            "rating_level": 4.0
        }
        
        success, response = self.run_test(
            "Upsert Player User (sarah.johnson@gmail.com)",
            "POST",
            "auth/social-login",
            200,
            data=player_data
        )
        
        if success and 'id' in response:
            self.player_id = response['id']
            print(f"   ✅ Player ID: {self.player_id}")
            print(f"   Name: {response.get('name')}")
            print(f"   Rating: {response.get('rating_level')}")
            print(f"   Role: {response.get('role')}")
            
            # Update sports preferences
            sports_data = {
                "sports_preferences": ["Tennis"]
            }
            
            success2, response2 = self.run_test(
                "Update Player Sports Preferences",
                "PATCH",
                f"users/{self.player_id}/sports",
                200,
                data=sports_data
            )
            
            if success2:
                print(f"   ✅ Sports preferences updated: {response2.get('sports_preferences')}")
                return True
        
        return False

    def create_ui_focused_league(self):
        """Step 3: Create a UI-focused league under the new manager"""
        if not self.manager_id:
            print("❌ No manager ID available")
            return False

        league_data = {
            "name": "QA RR League (UI)",
            "sport_type": "Tennis",
            "description": "UI-aligned QA league"
        }
        
        success, response = self.run_test(
            "Create UI-focused League",
            "POST",
            "leagues",
            200,
            data=league_data,
            params={"created_by": self.manager_id}
        )
        
        if success and 'id' in response:
            self.league_id = response['id']
            print(f"   ✅ League ID: {self.league_id}")
            print(f"   League Name: {response.get('name')}")
            print(f"   Sport Type: {response.get('sport_type')}")
            return True
        
        return False

    def create_format_tier_doubles(self):
        """Step 4: Create format tier (Doubles)"""
        if not self.league_id:
            print("❌ No league ID available")
            return False

        format_data = {
            "league_id": self.league_id,
            "name": "QA Round Robin Doubles (UI)",
            "format_type": "Doubles",
            "description": "UI RR test"
        }
        
        success, response = self.run_test(
            "Create Format Tier (Doubles)",
            "POST",
            "format-tiers",
            200,
            data=format_data
        )
        
        if success and 'id' in response:
            self.format_tier_id = response['id']
            print(f"   ✅ Format Tier ID: {self.format_tier_id}")
            print(f"   Format Type: {response.get('format_type')}")
            print(f"   Name: {response.get('name')}")
            return True
        
        return False

    def create_rating_tier(self):
        """Step 5: Create rating tier"""
        if not self.format_tier_id:
            print("❌ No format tier ID available")
            return False

        rating_data = {
            "format_tier_id": self.format_tier_id,
            "name": "QA 4.0 (UI)",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 36,
            "competition_system": "Team League Format",
            "playoff_spots": 8,
            "region": "QA",
            "surface": "Hard"
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
            print(f"   ✅ Rating Tier ID: {self.rating_tier_id}")
            print(f"   Join Code: {self.join_code}")
            print(f"   Rating Range: {response.get('min_rating')}-{response.get('max_rating')}")
            print(f"   Max Players: {response.get('max_players')}")
            print(f"   Competition System: {response.get('competition_system')}")
            return True
        
        return False

    def join_sarah_via_code(self):
        """Step 6: Join Sarah via code"""
        if not self.player_id or not self.join_code:
            print("❌ No player ID or join code available")
            return False

        join_data = {
            "join_code": self.join_code
        }
        
        success, response = self.run_test(
            "Join Sarah via Code",
            "POST",
            f"join-by-code/{self.player_id}",
            200,
            data=join_data
        )
        
        if success:
            print(f"   ✅ Sarah joined successfully")
            print(f"   Status: {response.get('status')}")
            print(f"   Rating Tier ID: {response.get('rating_tier_id')}")
            return True
        
        return False

    def verify_members(self):
        """Step 7: Verify GET /api/rating-tiers/{rating_tier_id}/members returns Sarah"""
        if not self.rating_tier_id:
            print("❌ No rating tier ID available")
            return False

        success, response = self.run_test(
            "Verify Members List",
            "GET",
            f"rating-tiers/{self.rating_tier_id}/members",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Members found: {len(response)}")
            
            # Look for Sarah
            sarah_found = False
            for member in response:
                if member.get('email') == 'sarah.johnson@gmail.com':
                    sarah_found = True
                    print(f"   ✅ Sarah Johnson found:")
                    print(f"     - Name: {member.get('name')}")
                    print(f"     - Email: {member.get('email')}")
                    print(f"     - Rating: {member.get('rating_level')}")
                    print(f"     - LAN: {member.get('lan')}")
                    print(f"     - Joined: {member.get('joined_at')}")
                    break
            
            if sarah_found:
                print("   ✅ Sarah successfully found in members list")
                return True
            else:
                print("   ❌ Sarah not found in members list")
                return False
        
        return False

    def generate_summary(self):
        """Generate compact JSON summary"""
        members_api_url = f"{self.base_url}/api/rating-tiers/{self.rating_tier_id}/members" if self.rating_tier_id else None
        
        summary = {
            "manager_id": self.manager_id,
            "player_id": self.player_id,
            "league_id": self.league_id,
            "format_tier_id": self.format_tier_id,
            "rating_tier_id": self.rating_tier_id,
            "join_code": self.join_code,
            "members_api_url": members_api_url
        }
        
        return summary

    def run_full_provisioning(self):
        """Run the complete provisioning workflow"""
        print("🎾 QA ACCOUNT PROVISIONING - FRONTEND UI ALIGNMENT")
        print("=" * 60)
        print("Provisioning test accounts that align with frontend's built-in mock Google sign-in emails")
        print("This allows users to log in via UI and see QA data immediately.")
        print()

        # Execute all steps in sequence
        steps = [
            ("Provision Manager User", self.provision_manager_user),
            ("Provision Player User", self.provision_player_user),
            ("Create UI-focused League", self.create_ui_focused_league),
            ("Create Format Tier (Doubles)", self.create_format_tier_doubles),
            ("Create Rating Tier", self.create_rating_tier),
            ("Join Sarah via Code", self.join_sarah_via_code),
            ("Verify Members List", self.verify_members)
        ]

        all_success = True
        for step_name, step_func in steps:
            print(f"\n{'='*20} {step_name} {'='*20}")
            if not step_func():
                print(f"❌ FAILED: {step_name}")
                all_success = False
                break
            else:
                print(f"✅ COMPLETED: {step_name}")

        # Generate final summary
        print(f"\n{'='*60}")
        print("📊 PROVISIONING SUMMARY")
        print(f"{'='*60}")
        
        summary = self.generate_summary()
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print()
        
        if all_success:
            print("🎉 QA ACCOUNT PROVISIONING SUCCESSFUL!")
            print()
            print("📋 COMPACT JSON SUMMARY:")
            print(json.dumps(summary, indent=2))
            print()
            print("🔗 QUICK ACCESS URLS:")
            print(f"   Manager Login: {self.base_url} (manager.user@gmail.com)")
            print(f"   Player Login: {self.base_url} (sarah.johnson@gmail.com)")
            print(f"   Members API: {summary['members_api_url']}")
            print(f"   Join Code: {summary['join_code']}")
            print()
            print("✅ Users can now log in via UI and see QA data immediately!")
            
            return summary
        else:
            print("❌ QA ACCOUNT PROVISIONING FAILED")
            print("Some steps did not complete successfully.")
            return None

def main():
    """Main execution function"""
    provisioner = QAAccountProvisioner()
    result = provisioner.run_full_provisioning()
    
    if result:
        print("\n" + "="*60)
        print("🎯 PROVISIONING COMPLETE - READY FOR UI TESTING")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("💥 PROVISIONING FAILED - CHECK ERRORS ABOVE")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()