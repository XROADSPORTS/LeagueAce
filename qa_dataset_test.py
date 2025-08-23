#!/usr/bin/env python3
"""
QA Dataset Provisioning Test
Provision a QA test dataset via live APIs and return IDs for manual testing.
"""

import requests
import json
import sys
from datetime import datetime

class QADatasetProvisioner:
    def __init__(self, base_url="https://teamace.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.results = {}
        
    def log(self, message):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def api_call(self, method, endpoint, data=None, params=None, expected_status=200):
        """Make an API call and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            success = response.status_code == expected_status
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                self.log(f"❌ API Error: {method} {endpoint} returned {response.status_code}")
                try:
                    error_detail = response.json()
                    self.log(f"   Error details: {error_detail}")
                except:
                    self.log(f"   Response text: {response.text}")
                return False, {}
                
        except Exception as e:
            self.log(f"❌ Exception: {str(e)}")
            return False, {}
    
    def provision_qa_dataset(self):
        """Execute the complete QA dataset provisioning workflow"""
        self.log("🎾 Starting QA Dataset Provisioning...")
        
        # Step 1: Create Manager user
        self.log("Step 1: Creating Manager user...")
        manager_data = {
            "provider": "Google",
            "token": "qa_manager_token",
            "email": "manager.qa@gmail.com",
            "name": "QA Manager",
            "provider_id": "qa_manager_123",
            "role": "League Manager"
        }
        
        success, response = self.api_call("POST", "auth/social-login", data=manager_data)
        if not success:
            self.log("❌ Failed to create Manager user")
            return None
            
        manager_id = response.get('id')
        if not manager_id:
            self.log("❌ Manager user created but no ID returned")
            return None
            
        self.results['manager_id'] = manager_id
        self.log(f"✅ Manager created: {manager_id}")
        
        # Step 2: Create Player user
        self.log("Step 2: Creating Player user...")
        player_data = {
            "provider": "Google", 
            "token": "qa_player_token",
            "email": "player.qa@gmail.com",
            "name": "QA Player",
            "provider_id": "qa_player_123",
            "role": "Player",
            "rating_level": 4.0
        }
        
        success, response = self.api_call("POST", "auth/social-login", data=player_data)
        if not success:
            self.log("❌ Failed to create Player user")
            return None
            
        player_id = response.get('id')
        if not player_id:
            self.log("❌ Player user created but no ID returned")
            return None
            
        self.results['player_id'] = player_id
        self.log(f"✅ Player created: {player_id}")
        
        # Step 2b: Update player sports preferences
        self.log("Step 2b: Updating player sports preferences...")
        sports_data = {
            "sports_preferences": ["Tennis"]
        }
        
        success, response = self.api_call("PATCH", f"users/{player_id}/sports", data=sports_data)
        if not success:
            self.log("❌ Failed to update player sports preferences")
            return None
            
        self.log("✅ Player sports preferences updated to Tennis")
        
        # Step 3: Create Tennis League
        self.log("Step 3: Creating Tennis League...")
        league_data = {
            "name": "QA RR League",
            "sport_type": "Tennis",
            "description": "QA test league for Round Robin"
        }
        
        success, response = self.api_call("POST", "leagues", data=league_data, params={"created_by": manager_id})
        if not success:
            self.log("❌ Failed to create Tennis League")
            return None
            
        league_id = response.get('id')
        if not league_id:
            self.log("❌ League created but no ID returned")
            return None
            
        self.results['league_id'] = league_id
        self.log(f"✅ League created: {league_id}")
        
        # Step 4: Create Format Tier
        self.log("Step 4: Creating Format Tier...")
        format_data = {
            "league_id": league_id,
            "name": "QA Round Robin Doubles",
            "format_type": "Doubles",
            "description": "QA RR test"
        }
        
        success, response = self.api_call("POST", "format-tiers", data=format_data)
        if not success:
            self.log("❌ Failed to create Format Tier")
            return None
            
        format_tier_id = response.get('id')
        if not format_tier_id:
            self.log("❌ Format Tier created but no ID returned")
            return None
            
        self.results['format_tier_id'] = format_tier_id
        self.log(f"✅ Format Tier created: {format_tier_id}")
        
        # Step 5: Create Rating Tier
        self.log("Step 5: Creating Rating Tier...")
        rating_data = {
            "format_tier_id": format_tier_id,
            "name": "QA 4.0",
            "min_rating": 3.5,
            "max_rating": 4.5,
            "max_players": 36,
            "competition_system": "Team League Format",
            "playoff_spots": 8,
            "region": "QA",
            "surface": "Hard"
        }
        
        success, response = self.api_call("POST", "rating-tiers", data=rating_data)
        if not success:
            self.log("❌ Failed to create Rating Tier")
            return None
            
        rating_tier_id = response.get('id')
        join_code = response.get('join_code')
        if not rating_tier_id or not join_code:
            self.log("❌ Rating Tier created but missing ID or join_code")
            return None
            
        self.results['rating_tier_id'] = rating_tier_id
        self.results['join_code'] = join_code
        self.log(f"✅ Rating Tier created: {rating_tier_id}")
        self.log(f"✅ Join Code generated: {join_code}")
        
        # Step 6: Preview code verification
        self.log("Step 6: Verifying join code preview...")
        success, response = self.api_call("GET", f"rating-tiers/by-code/{join_code}")
        if not success:
            self.log("❌ Failed to preview join code")
            return None
            
        league_name = response.get('league_name')
        tier_name = response.get('name')
        self.log(f"✅ Join code preview verified - League: {league_name}, Tier: {tier_name}")
        
        # Step 7: Join player to tier
        self.log("Step 7: Joining player to tier...")
        join_data = {
            "join_code": join_code
        }
        
        success, response = self.api_call("POST", f"join-by-code/{player_id}", data=join_data)
        if not success:
            self.log("❌ Failed to join player to tier")
            return None
            
        membership_id = response.get('id')
        self.log(f"✅ Player joined tier successfully - Membership ID: {membership_id}")
        
        # Step 8: Verify members endpoint shows 1 member
        self.log("Step 8: Verifying members endpoint...")
        success, response = self.api_call("GET", f"rating-tiers/{rating_tier_id}/members")
        if not success:
            self.log("❌ Failed to get tier members")
            return None
            
        members_count = len(response) if isinstance(response, list) else 0
        if members_count != 1:
            self.log(f"❌ Expected 1 member, found {members_count}")
            return None
            
        member = response[0] if response else {}
        member_name = member.get('name')
        member_email = member.get('email')
        self.log(f"✅ Members endpoint verified - 1 member: {member_name} ({member_email})")
        
        # Generate members API URL
        members_api_url = f"{self.api_url}/rating-tiers/{rating_tier_id}/members"
        self.results['members_api_url'] = members_api_url
        
        self.log("🎉 QA Dataset Provisioning Complete!")
        return self.results
    
    def generate_summary(self):
        """Generate the compact JSON summary as requested"""
        if not self.results:
            return None
            
        summary = {
            "manager_id": self.results.get('manager_id'),
            "player_id": self.results.get('player_id'), 
            "league_id": self.results.get('league_id'),
            "format_tier_id": self.results.get('format_tier_id'),
            "rating_tier_id": self.results.get('rating_tier_id'),
            "join_code": self.results.get('join_code'),
            "members_api_url": self.results.get('members_api_url')
        }
        
        return summary

def main():
    """Main execution function"""
    print("=" * 80)
    print("QA DATASET PROVISIONING TEST")
    print("=" * 80)
    
    provisioner = QADatasetProvisioner()
    
    # Execute the provisioning workflow
    results = provisioner.provision_qa_dataset()
    
    if results:
        # Generate and display the summary
        summary = provisioner.generate_summary()
        
        print("\n" + "=" * 80)
        print("QA DATASET SUMMARY (JSON)")
        print("=" * 80)
        print(json.dumps(summary, indent=2))
        
        print("\n" + "=" * 80)
        print("MANUAL TESTING INSTRUCTIONS")
        print("=" * 80)
        print(f"1. Manager ID: {summary['manager_id']}")
        print(f"2. Player ID: {summary['player_id']}")
        print(f"3. League ID: {summary['league_id']}")
        print(f"4. Format Tier ID: {summary['format_tier_id']}")
        print(f"5. Rating Tier ID: {summary['rating_tier_id']}")
        print(f"6. Join Code: {summary['join_code']}")
        print(f"7. Members API URL: {summary['members_api_url']}")
        
        print(f"\n🔗 Test the members endpoint directly:")
        print(f"   curl '{summary['members_api_url']}'")
        
        print(f"\n🔗 Test join code preview:")
        print(f"   curl 'https://teamace.preview.emergentagent.com/api/rating-tiers/by-code/{summary['join_code']}'")
        
        print("\n✅ QA Dataset provisioned successfully!")
        return 0
    else:
        print("\n❌ QA Dataset provisioning failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())