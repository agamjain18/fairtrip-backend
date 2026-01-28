
import os
import sys
from datetime import datetime, timedelta

# Ensure current directory is in path
sys.path.append(os.path.dirname(__file__))

from utils.email_service import send_trip_created_email

TEST_EMAIL = "aagamjain9015@gmail.com"

print(f"Sending redesigned Trip Created email to {TEST_EMAIL}...")

# Sample Data
user_name = "Aagam Jain"
trip_title = "Swiss Alps Adventure 🏔️"
destination = "Zermatt, Switzerland"
start_date = (datetime.now() + timedelta(days=60)).isoformat()
end_date = (datetime.now() + timedelta(days=67)).isoformat()
budget = 2500.0
currency = "USD"
description = "A dream trip to experience the Matterhorn, glacier skiing, and the world's most scenic train rides with the squad."
use_ai = True

success = send_trip_created_email(
    email=TEST_EMAIL,
    user_name=user_name,
    trip_title=trip_title,
    destination=destination,
    start_date=start_date,
    end_date=end_date,
    budget=budget,
    currency=currency,
    description=description,
    use_ai=use_ai,
    start_location="New Delhi, India"
)

if success:
    print("\n✅ Success! The redesigned email has been sent.")
    print("Check your inbox (and spam folder just in case).")
else:
    print("\n❌ Failed to send the email. Check the backend logs for details.")
