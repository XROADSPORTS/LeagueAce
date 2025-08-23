#!/usr/bin/env python3
"""
Test notification functionality by directly inserting a notification
and then retrieving it via the API
"""

import requests
import json
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

async def test_notification_functionality():
    """Test that notifications can be created and retrieved"""
    
    # Connect to MongoDB directly
    MONGO_URL = "mongodb://localhost:27017/test_database"
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.get_default_database()
    
    # Create a test user first via API
    api_url = "https://teamace.preview.emergentagent.com/api"
    
    # Create user via social login
    timestamp = datetime.now().strftime('%H%M%S')
    social_data = {
        "provider": "Google",
        "token": f"notification_test_token_{timestamp}",
        "email": f"notification.test_{timestamp}@gmail.com",
        "name": "Notification Test User",
        "provider_id": f"google_notification_{timestamp}"
    }
    
    response = requests.post(f"{api_url}/auth/social-login", json=social_data)
    if response.status_code != 200:
        print(f"❌ Failed to create test user: {response.status_code}")
        return False
    
    user_data = response.json()
    user_id = user_data['id']
    print(f"✅ Created test user: {user_id}")
    
    # Create a notification directly in the database using rr_notify logic
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_ids": [user_id],
        "message": "Test notification for API testing",
        "meta": {"test": True, "source": "notification_test"},
        "created_at": datetime.now().isoformat(),
        "read_by": []
    }
    
    await db.rr_notifications.insert_one(notification_doc)
    print(f"✅ Created notification in database")
    
    # Now retrieve notifications via API
    response = requests.get(f"{api_url}/users/{user_id}/notifications")
    if response.status_code != 200:
        print(f"❌ Failed to retrieve notifications: {response.status_code}")
        return False
    
    notifications = response.json()
    print(f"✅ Retrieved {len(notifications)} notifications via API")
    
    # Verify our notification is there
    found_notification = False
    for notification in notifications:
        if notification.get('message') == "Test notification for API testing":
            found_notification = True
            print(f"✅ Found our test notification:")
            print(f"   - ID: {notification.get('id')}")
            print(f"   - Message: {notification.get('message')}")
            print(f"   - Created: {notification.get('created_at')}")
            print(f"   - Meta: {notification.get('meta')}")
            break
    
    if not found_notification:
        print(f"❌ Test notification not found in API response")
        return False
    
    # Clean up
    await db.rr_notifications.delete_one({"id": notification_doc["id"]})
    client.close()
    
    print(f"✅ Notification functionality test completed successfully")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_notification_functionality())
    exit(0 if result else 1)