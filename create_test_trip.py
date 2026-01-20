import requests
import json
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

def create_trip():
    # 1. Login
    login_data = {
        "email": "john@example.com",
        "password": "password123"
    }
    print(f"Logging in as {login_data['email']}...")
    try:
        response = requests.post(f"{API_URL}/auth/login-json", json=login_data)
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")

        # 1.5 Get User ID
        print("Fetching user ID...")
        user_response = requests.get(f"{API_URL}/auth/me", headers=headers)
        if user_response.status_code != 200:
            print(f"Failed to fetch user info: {user_response.text}")
            return
        
        user_id = user_response.json()["id"]
        print(f"User ID: {user_id}")

        # 2. Create Trip
        start_date = datetime.now() + timedelta(days=10)
        # For 2 days duration: Start + 1 day (e.g., Mon - Tue)
        end_date = start_date + timedelta(days=1)

        trip_data = {
            "title": "Explore Indore",
            "description": "2-day AI planned trip to Indore testing",
            "destination": "Indore",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_budget": 10000, # INR
            "currency": "INR",
            "use_ai": True,
            "is_public": False,
            "timezone": "Asia/Kolkata"
        }
        
        print(f"Creating trip to {trip_data['destination']} with AI enabled...")
        # Note: creator_id is a query parameter in the backend route!
        trip_response = requests.post(f"{API_URL}/trips/?creator_id={user_id}", json=trip_data, headers=headers)
        
        if trip_response.status_code in [200, 201]:
            print("✅ Trip created successfully!")
            data = trip_response.json()
            print(f"Trip ID: {data['id']}")
            print(f"Initial AI Status: {data.get('ai_status', 'unknown')}")
            print("AI generation should have started in the background.")
        else:
            print(f"❌ Failed to create trip: {trip_response.text}")

    except Exception as e:
        print(f"Error: {e}")
        print("Hint: Make sure the backend server is running!")

if __name__ == "__main__":
    create_trip()
