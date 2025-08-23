import requests
import json
from datetime import datetime

# Test the standings endpoint structure
base_url = "https://leagueace-rr.preview.emergentagent.com"
api_url = f"{base_url}/api"

# Create a simple test to verify standings structure
tier_id = f"standings-test-{datetime.now().strftime('%H%M%S')}"

# Create users
user_ids = []
for i in range(4):
    user_data = {
        "name": f"Test User {i+1}",
        "email": f"testuser{i+1}_{datetime.now().strftime('%H%M%S')}@example.com",
        "rating_level": 4.0,
        "lan": f"ST{i+1:03d}"
    }
    
    response = requests.post(f"{api_url}/users", json=user_data)
    if response.status_code == 200:
        user_ids.append(response.json()['id'])
        print(f"Created user {i+1}: {response.json()['id']}")

# Configure tier
config_data = {
    "season_name": "Standings Test",
    "season_length": 3,
    "minimize_repeat_partners": True,
    "track_first_match_badge": True,
    "track_finished_badge": True
}

response = requests.post(f"{api_url}/rr/tiers/{tier_id}/configure", json=config_data)
print(f"Configure tier: {response.status_code}")

# Test standings endpoint structure (should return empty but valid structure)
response = requests.get(f"{api_url}/rr/standings", params={"tier_id": tier_id})
print(f"Standings Status: {response.status_code}")
print(f"Standings Response: {response.json()}")

# Verify the structure has the expected fields
if response.status_code == 200:
    data = response.json()
    if 'rows' in data and 'top8' in data:
        print("✅ Standings endpoint has correct structure with 'rows' and 'top8' fields")
        print("✅ Ready to test pct_game_win and badges once scorecard approval bug is fixed")
    else:
        print("❌ Standings endpoint missing expected fields")