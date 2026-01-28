import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

try:
    from routes_sql import emergency
    print(f"Successfully imported emergency. Trip is in globals: {'Trip' in dir(emergency)}")
    if 'Trip' not in dir(emergency):
      print("Trip is MISSING from emergency module!")
    else:
      print("Trip IS present in emergency module.")
except Exception as e:
    print(f"Failed to import: {e}")
