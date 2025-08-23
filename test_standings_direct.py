import requests

# Test the standings endpoint directly
base_url = "https://doubles-master.preview.emergentagent.com"
api_url = f"{base_url}/api"

# Use the tier ID from our test
tier_id = "rr-new-features-022228"

response = requests.get(f"{api_url}/rr/standings", params={"tier_id": tier_id})

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json() if response.status_code == 200 else response.text}")