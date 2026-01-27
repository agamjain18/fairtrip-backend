
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from utils.email_service import (
    send_trip_created_email,
    send_trip_invitation_email,
    send_trip_deleted_email,
    send_friend_added_email,
    send_settlement_email
)

TEST_EMAIL = "aagamjain152003@gmail.com"

print(f"Sending test emails to {TEST_EMAIL}...")

print("\n1. Sending Trip Created Email...")
send_trip_created_email(TEST_EMAIL, "Aagam Jain", "Summer EuroTrip 2026")

print("\n2. Sending Trip Invitation Email...")
send_trip_invitation_email(TEST_EMAIL, "Sarah Connor", "Bali Adventure")

print("\n3. Sending Trip Deleted Email...")
send_trip_deleted_email(TEST_EMAIL, "Aagam Jain", "Cancelled Weekend Getaway")

print("\n4. Sending Friend Added Email...")
send_friend_added_email(TEST_EMAIL, "John Wick")

print("\n5. Sending Settlement (Payment) Email...")
send_settlement_email(TEST_EMAIL, "Tony Stark", 150.00, "USD", "Avengers Retreat")

print("\nDone! Check your inbox.")
