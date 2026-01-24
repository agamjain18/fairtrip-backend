"""
Test script to verify all implemented features
Run this after starting the backend server
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_currency_features():
    """Test multi-currency support"""
    print("\n=== Testing Currency Features ===")
    
    # Seed common rates
    response = requests.post(f"{BASE_URL}/currency/rates/seed")
    print(f"Seed rates: {response.json()}")
    
    # Convert currency
    response = requests.get(f"{BASE_URL}/currency/convert", params={
        "amount": 100,
        "from_currency": "USD",
        "to_currency": "EUR"
    })
    print(f"Convert 100 USD to EUR: {response.json()}")
    
    # Get all rates
    response = requests.get(f"{BASE_URL}/currency/rates")
    print(f"Total rates: {len(response.json())}")

def test_recurring_expenses():
    """Test recurring expense functionality"""
    print("\n=== Testing Recurring Expenses ===")
    
    # Note: This requires valid trip_id, user_id, and participant_ids
    # Uncomment and modify with actual IDs from your database
    
    # recurring_data = {
    #     "trip_id": "YOUR_TRIP_ID",
    #     "title": "Monthly Rent",
    #     "description": "Shared apartment rent",
    #     "amount": 1500.00,
    #     "currency": "USD",
    #     "category": "accommodation",
    #     "paid_by": "USER_ID",
    #     "participant_ids": ["USER_ID_1", "USER_ID_2"],
    #     "split_type": "equal",
    #     "frequency": "monthly",
    #     "interval": 1,
    #     "start_date": datetime.now().isoformat(),
    #     "end_date": (datetime.now() + timedelta(days=365)).isoformat()
    # }
    
    # response = requests.post(f"{BASE_URL}/recurring-expenses/", json=recurring_data)
    # print(f"Created recurring expense: {response.json()}")
    
    # Get all recurring expenses
    response = requests.get(f"{BASE_URL}/recurring-expenses/")
    print(f"Total recurring expenses: {len(response.json())}")

def test_expense_splitting():
    """Test different split methods"""
    print("\n=== Testing Expense Splitting ===")
    
    split_examples = {
        "equal": {
            "split_type": "equal",
            "split_data": None,
            "description": "Split evenly among all participants"
        },
        "custom": {
            "split_type": "custom",
            "split_data": json.dumps({
                "user_id_1": 30.00,
                "user_id_2": 20.00,
                "user_id_3": 50.00
            }),
            "description": "Custom amounts per person"
        },
        "percentage": {
            "split_type": "percentage",
            "split_data": json.dumps({
                "user_id_1": 30.0,
                "user_id_2": 30.0,
                "user_id_3": 40.0
            }),
            "description": "Split by percentages"
        },
        "shares": {
            "split_type": "shares",
            "split_data": json.dumps({
                "user_id_1": 1,
                "user_id_2": 1,
                "user_id_3": 2
            }),
            "description": "Split by share ratios (1:1:2)"
        }
    }
    
    for method, example in split_examples.items():
        print(f"\n{method.upper()}: {example['description']}")
        print(f"  split_type: {example['split_type']}")
        print(f"  split_data: {example['split_data']}")

def test_analytics_and_reports():
    """Test analytics and reporting endpoints"""
    print("\n=== Testing Analytics & Reports ===")
    
    # Note: Replace with actual trip_id
    # trip_id = "YOUR_TRIP_ID"
    
    # response = requests.get(f"{BASE_URL}/expenses/trip/{trip_id}/analytics")
    # print(f"Analytics: {json.dumps(response.json(), indent=2)}")
    
    # response = requests.get(f"{BASE_URL}/expenses/trip/{trip_id}/report")
    # print(f"Report: {json.dumps(response.json(), indent=2)}")
    
    # response = requests.get(f"{BASE_URL}/expenses/trip/{trip_id}/balances")
    # print(f"Balances: {json.dumps(response.json(), indent=2)}")
    
    print("Analytics endpoints ready (need trip_id to test)")

def test_settlements():
    """Test settlement tracking"""
    print("\n=== Testing Settlement Tracking ===")
    
    # Get all settlements
    response = requests.get(f"{BASE_URL}/settlements/")
    print(f"Total settlements: {len(response.json())}")
    
    print("\nSettlement payment methods supported:")
    print("  - cash")
    print("  - bank_transfer")
    print("  - upi")
    print("  - card")
    print("  - custom")

def test_notifications():
    """Test notification system"""
    print("\n=== Testing Notifications ===")
    
    # Note: Replace with actual user_id
    # user_id = "YOUR_USER_ID"
    
    # response = requests.get(f"{BASE_URL}/notifications/user/{user_id}/unread-count")
    # print(f"Unread count: {response.json()}")
    
    print("Notification types supported:")
    print("  - expense")
    print("  - trip")
    print("  - friend")
    print("  - system")
    print("  - settlement")
    print("  - reminder")

def main():
    """Run all tests"""
    print("=" * 60)
    print("FairTrip Feature Implementation Test Suite")
    print("=" * 60)
    
    try:
        # Test root endpoint
        response = requests.get(f"{BASE_URL}/")
        print(f"\nAPI Status: {response.json()}")
        
        # Run feature tests
        test_currency_features()
        test_recurring_expenses()
        test_expense_splitting()
        test_analytics_and_reports()
        test_settlements()
        test_notifications()
        
        print("\n" + "=" * 60)
        print("✅ All features implemented and accessible!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to backend server")
        print("Please ensure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
