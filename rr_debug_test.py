#!/usr/bin/env python3
"""
Debug Round Robin Scheduling Issues
"""

import requests
import json
from datetime import datetime

def debug_rr_scheduling():
    base_url = "https://leagueace-rr.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # QA Tier IDs
    qa_doubles_tier_id = "82830a8f-6f02-48ac-99fc-dbc445f4385a"
    qa_singles_tier_id = "dbaf7ed9-b507-4983-bd92-44c561e912ee"
    
    print("🔍 Debugging Round Robin Scheduling...")
    
    # Check tier members for doubles
    print(f"\n📋 Checking Doubles Tier Members ({qa_doubles_tier_id}):")
    response = requests.get(f"{api_url}/rating-tiers/{qa_doubles_tier_id}/members")
    if response.status_code == 200:
        members = response.json()
        print(f"   Found {len(members)} members:")
        for member in members:
            print(f"   - {member['name']} (ID: {member['user_id']}, Rating: {member['rating_level']})")
    
    # Check tier members for singles
    print(f"\n📋 Checking Singles Tier Members ({qa_singles_tier_id}):")
    response = requests.get(f"{api_url}/rating-tiers/{qa_singles_tier_id}/members")
    if response.status_code == 200:
        members = response.json()
        print(f"   Found {len(members)} members:")
        for member in members:
            print(f"   - {member['name']} (ID: {member['user_id']}, Rating: {member['rating_level']})")
    
    # Check RR config for doubles
    print(f"\n⚙️ Checking RR Config for Doubles:")
    # Try to get config by checking if it exists in the database
    # Since there's no direct endpoint, let's try to configure again and see the response
    config_data = {
        "season_length": 3,
        "track_first_match_badge": True,
        "track_finished_badge": True
    }
    response = requests.post(f"{api_url}/rr/tiers/{qa_doubles_tier_id}/configure", json=config_data)
    if response.status_code == 200:
        config = response.json()
        print(f"   Config: {json.dumps(config, indent=2)}")
    
    # Try scheduling with explicit player IDs for doubles
    print(f"\n🗓️ Attempting to Schedule Doubles Tier:")
    doubles_members = requests.get(f"{api_url}/rating-tiers/{qa_doubles_tier_id}/members").json()
    player_ids = [member['user_id'] for member in doubles_members]
    print(f"   Player IDs: {player_ids}")
    
    schedule_data = {
        "player_ids": player_ids
    }
    response = requests.post(f"{api_url}/rr/tiers/{qa_doubles_tier_id}/schedule", json=schedule_data)
    print(f"   Schedule Response Status: {response.status_code}")
    if response.status_code == 200:
        schedule_result = response.json()
        print(f"   Schedule Result: {json.dumps(schedule_result, indent=2)}")
    else:
        print(f"   Error: {response.text}")
    
    # Check if any matches were created
    print(f"\n🏓 Checking for Created Matches:")
    if player_ids:
        response = requests.get(f"{api_url}/rr/weeks", params={"player_id": player_ids[0], "tier_id": qa_doubles_tier_id})
        if response.status_code == 200:
            weeks_data = response.json()
            print(f"   Weeks Data: {json.dumps(weeks_data, indent=2)}")
        else:
            print(f"   Error getting weeks: {response.text}")
    
    # Check availability for players
    print(f"\n📅 Checking Player Availability:")
    for player_id in player_ids[:2]:  # Check first 2 players
        response = requests.get(f"{api_url}/rr/availability", params={"user_id": player_id})
        if response.status_code == 200:
            availability = response.json()
            print(f"   Player {player_id}: {availability}")
        else:
            print(f"   Error getting availability for {player_id}: {response.text}")

if __name__ == "__main__":
    debug_rr_scheduling()