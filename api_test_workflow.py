import requests
import sys
import time
import random
import string
import json

class APITester:
    def __init__(self, base_url="http://localhost:8005"):
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        self.user_id = None
        self.temp_trip_id = None
        self.failed_tests = []

    def log(self, msg):
        print(f"[TEST] {msg}")

    def test(self, name, method, path, expected_status=200, json_data=None, params=None):
        if not path.startswith("/"):
            path = "/" + path
        url = f"{self.base_url}{path}"
        print(f"Testing {name} ({method} {path})...", end=" ", flush=True)
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=json_data, headers=self.headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=json_data, headers=self.headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                print("FAILED: Invalid method")
                self.failed_tests.append(name)
                return None

            if response.status_code == expected_status or (isinstance(expected_status, list) and response.status_code in expected_status):
                print("PASSED")
                return response
            else:
                print(f"FAILED (Status: {response.status_code})")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append(name)
                return None
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed_tests.append(name)
            return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run API tests.")
    parser.add_argument("--url", default="http://localhost:8005", help="Target API URL")
    args = parser.parse_args()
    
    tester = APITester(base_url=args.url)
    tester.log(f"Starting EXTENSIVE API Testing Workflow targeting {tester.base_url}")

    # 1. Basic Public Endpoints
    tester.test("Health Check", "GET", "/health")
    tester.test("Root Check", "GET", "/")
    tester.test("Cities List", "GET", "/cities/")
    tester.test("Currency Rates", "GET", "/currency/rates/")

    # 2. Authentication Flow
    email = f"test_{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"
    password = "password123"
    
    login_data = {"email": "john@example.com", "password": "password123"}
    login_res = tester.test("Login Demo", "POST", "/auth/login-json", json_data=login_data)
    
    if not login_res:
        tester.log("Demo user login failed or not present, registering new test user...")
        reg_data = {
            "email": email,
            "username": email.split('@')[0],
            "password": password,
            "full_name": "QA Automator"
        }
        tester.test("Register User", "POST", "/auth/register", expected_status=201, json_data=reg_data)
        login_res = tester.test("Login New User", "POST", "/auth/login-json", json_data={"email": email, "password": password})

    if not login_res:
        tester.log("CRITICAL FAILURE: Could not authenticate. Skipping authenticated tests.")
    else:
        # 3. Authenticated Tests
        data = login_res.json()
        token = data.get("access_token") or data.get("token")
        tester.headers = {"Authorization": f"Bearer {token}"}
        
        # Get Me
        me_res = tester.test("Get Profile (Me)", "GET", "/auth/me")
        if me_res:
            tester.user_id = me_res.json().get("id")

        # Users List & Search
        tester.test("Get All Users", "GET", "/users/")
        tester.test("Search Users", "GET", "/users/search/", params={"q": "QA"})
        
        # 4. Trip Logic
        trip_data = {
            "title": "QA Test Trip " + str(random.randint(1000, 9999)),
            "destination": "London, UK",
            "total_budget": 5000.0,
            "currency": "GBP",
            "start_date": "2024-12-01T00:00:00",
            "end_date": "2024-12-10T00:00:00"
        }
        
        if tester.user_id:
            trip_res = tester.test("Create Trip", "POST", f"/trips?creator_id={tester.user_id}", expected_status=201, json_data=trip_data)
            if trip_res:
                tester.temp_trip_id = trip_res.json().get("id")

        if tester.temp_trip_id:
            tester.test("Get My Trips", "GET", "/trips/", params={"user_id": tester.user_id})
            tester.test("Get Trip Detail", "GET", f"/trips/{tester.temp_trip_id}/")
            tester.test("Get Trip Members", "GET", f"/trips/{tester.temp_trip_id}/members/")
            tester.test("Get Trip Summary", "GET", f"/trips/{tester.temp_trip_id}/summary/")

            # 5. Expense Logic
            expense_data = {
                "trip_id": tester.temp_trip_id,
                "title": "Initial QA Expense",
                "amount": 150.0,
                "paid_by_id": tester.user_id,
                "participant_ids": [tester.user_id],
                "category": "other"
            }
            tester.test("Create Expense", "POST", "/expenses/", expected_status=201, json_data=expense_data)
            tester.test("Get Trip Expenses", "GET", f"/expenses/trip/{tester.temp_trip_id}/")
            tester.test("Get User Expenses", "GET", f"/expenses/user/{tester.user_id}/")
            
            # 6. Additional Modules
            tester.test("Get Transports", "GET", f"/transports/trip/{tester.temp_trip_id}/")
            tester.test("Get Accommodations", "GET", f"/accommodations/trip/{tester.temp_trip_id}/")
            tester.test("Get Itinerary", "GET", f"/itinerary/trip/{tester.temp_trip_id}/")
            tester.test("Get Checklist", "GET", f"/checklist/trip/{tester.temp_trip_id}/")
            tester.test("Get Settlements", "GET", "/settlements/", params={"trip_id": tester.temp_trip_id})
            tester.test("Get Recurring Expenses", "GET", "/recurring-expenses/")
            
            # Emergency
            tester.test("Get Emergency Contacts", "GET", "/emergency/contacts/", params={"trip_id": tester.temp_trip_id})

        # 7. Friends
        if tester.user_id:
            tester.test("Get User Friends", "GET", f"/users/{tester.user_id}/friends")

        # 8. Notifications
        tester.test("Get Notifications", "GET", "/notifications/", params={"user_id": tester.user_id})
        
        # 9. Sync Services
        tester.test("Sync Version Check", "GET", "/sync/version-check/")

    # Final Result
    print("\n" + "="*30)
    if not tester.failed_tests:
        print("PASS: ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"FAIL: {len(tester.failed_tests)} TESTS FAILED:")
        for ft in tester.failed_tests:
            print(f"   - {ft}")
        sys.exit(1)

if __name__ == "__main__":
    main()
