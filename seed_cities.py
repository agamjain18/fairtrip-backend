from sqlalchemy.orm import Session
from database_sql import City, SessionLocal

def get_indian_cities():
    return [
        {"name": "Mumbai", "state": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Delhi", "state": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "emergency_numbers": {"police": "100", "ambulance": "102"}},
        {"name": "Bangalore", "state": "Karnataka", "latitude": 12.9716, "longitude": 77.5946, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Hyderabad", "state": "Telangana", "latitude": 17.3850, "longitude": 78.4867, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Ahmedabad", "state": "Gujarat", "latitude": 23.0225, "longitude": 72.5714, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Chennai", "state": "Tamil Nadu", "latitude": 13.0827, "longitude": 80.2707, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Kolkata", "state": "West Bengal", "latitude": 22.5726, "longitude": 88.3639, "emergency_numbers": {"police": "100", "ambulance": "102"}},
        {"name": "Surat", "state": "Gujarat", "latitude": 21.1702, "longitude": 72.8311, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Pune", "state": "Maharashtra", "latitude": 18.5204, "longitude": 73.8567, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Jaipur", "state": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Lucknow", "state": "Uttar Pradesh", "latitude": 26.8467, "longitude": 80.9462, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Kanpur", "state": "Uttar Pradesh", "latitude": 26.4499, "longitude": 80.3319, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Nagpur", "state": "Maharashtra", "latitude": 21.1458, "longitude": 79.0882, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Indore", "state": "Madhya Pradesh", "latitude": 22.7196, "longitude": 75.8577, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Thane", "state": "Maharashtra", "latitude": 19.2183, "longitude": 72.9781, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Bhopal", "state": "Madhya Pradesh", "latitude": 23.2599, "longitude": 77.4126, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Visakhapatnam", "state": "Andhra Pradesh", "latitude": 17.6868, "longitude": 83.2185, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Pimpri-Chinchwad", "state": "Maharashtra", "latitude": 18.6298, "longitude": 73.7997, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Patna", "state": "Bihar", "latitude": 25.5941, "longitude": 85.1376, "emergency_numbers": {"police": "100", "ambulance": "102"}},
        {"name": "Vadodara", "state": "Gujarat", "latitude": 22.3072, "longitude": 73.1812, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Ghaziabad", "state": "Uttar Pradesh", "latitude": 28.6692, "longitude": 77.4538, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Ludhiana", "state": "Punjab", "latitude": 30.9010, "longitude": 75.8573, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Agra", "state": "Uttar Pradesh", "latitude": 27.1767, "longitude": 78.0081, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Nashik", "state": "Maharashtra", "latitude": 19.9975, "longitude": 73.7898, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Faridabad", "state": "Haryana", "latitude": 28.4089, "longitude": 77.3178, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Meerut", "state": "Uttar Pradesh", "latitude": 28.9845, "longitude": 77.7064, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Rajkot", "state": "Gujarat", "latitude": 22.3039, "longitude": 70.8022, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Kalyan-Dombivli", "state": "Maharashtra", "latitude": 19.2319, "longitude": 73.1328, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Vasai-Virar", "state": "Maharashtra", "latitude": 19.3905, "longitude": 72.8252, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Varanasi", "state": "Uttar Pradesh", "latitude": 25.3176, "longitude": 82.9739, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Srinagar", "state": "Jammu and Kashmir", "latitude": 34.0837, "longitude": 74.7973, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Aurangabad", "state": "Maharashtra", "latitude": 19.8762, "longitude": 75.3433, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Dhanbad", "state": "Jharkhand", "latitude": 23.7957, "longitude": 86.4304, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Amritsar", "state": "Punjab", "latitude": 31.6340, "longitude": 74.8723, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Navi Mumbai", "state": "Maharashtra", "latitude": 19.0330, "longitude": 73.0297, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Allahabad", "state": "Uttar Pradesh", "latitude": 25.4358, "longitude": 81.8463, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Howrah", "state": "West Bengal", "latitude": 22.5958, "longitude": 88.2636, "emergency_numbers": {"police": "100", "ambulance": "102"}},
        {"name": "Ranchi", "state": "Jharkhand", "latitude": 23.3441, "longitude": 85.3096, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Gwalior", "state": "Madhya Pradesh", "latitude": 26.2183, "longitude": 78.1828, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Jabalpur", "state": "Madhya Pradesh", "latitude": 23.1815, "longitude": 79.9864, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Coimbatore", "state": "Tamil Nadu", "latitude": 11.0168, "longitude": 76.9558, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Vijayawada", "state": "Andhra Pradesh", "latitude": 16.5062, "longitude": 80.6480, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Jodhpur", "state": "Rajasthan", "latitude": 26.2389, "longitude": 73.0243, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Madurai", "state": "Tamil Nadu", "latitude": 9.9252, "longitude": 78.1198, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Raipur", "state": "Chhattisgarh", "latitude": 21.2514, "longitude": 81.6296, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Kota", "state": "Rajasthan", "latitude": 25.2138, "longitude": 75.8648, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Chandigarh", "state": "Chandigarh", "latitude": 30.7333, "longitude": 76.7794, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Guwahati", "state": "Assam", "latitude": 26.1124, "longitude": 91.7394, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Solapur", "state": "Maharashtra", "latitude": 17.6599, "longitude": 75.9064, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Hubli-Dharwad", "state": "Karnataka", "latitude": 15.3647, "longitude": 75.1240, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Tiruchirappalli", "state": "Tamil Nadu", "latitude": 10.7905, "longitude": 78.7047, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Bareilly", "state": "Uttar Pradesh", "latitude": 28.3670, "longitude": 79.4304, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Moradabad", "state": "Uttar Pradesh", "latitude": 28.8389, "longitude": 78.7768, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Mysore", "state": "Karnataka", "latitude": 12.2958, "longitude": 76.6394, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Gurgaon", "state": "Haryana", "latitude": 28.4595, "longitude": 77.0266, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Aligarh", "state": "Uttar Pradesh", "latitude": 27.8974, "longitude": 78.0880, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Jalandhar", "state": "Punjab", "latitude": 31.3260, "longitude": 75.5762, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Bhubaneswar", "state": "Odisha", "latitude": 20.2961, "longitude": 85.8245, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Salem", "state": "Tamil Nadu", "latitude": 11.6643, "longitude": 78.1460, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Mira-Bhayandar", "state": "Maharashtra", "latitude": 19.2952, "longitude": 72.8546, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Warangal", "state": "Telangana", "latitude": 17.9629, "longitude": 79.6000, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Thiruvananthapuram", "state": "Kerala", "latitude": 8.5241, "longitude": 76.9366, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Guntur", "state": "Andhra Pradesh", "latitude": 16.2997, "longitude": 80.4355, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Bhiwandi", "state": "Maharashtra", "latitude": 19.2813, "longitude": 73.0488, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Saharanpur", "state": "Uttar Pradesh", "latitude": 29.9680, "longitude": 77.5552, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Gorakhpur", "state": "Uttar Pradesh", "latitude": 26.7606, "longitude": 83.3732, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Bikaner", "state": "Rajasthan", "latitude": 28.0195, "longitude": 73.3151, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Amravati", "state": "Maharashtra", "latitude": 20.9320, "longitude": 77.7523, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Noida", "state": "Uttar Pradesh", "latitude": 28.5355, "longitude": 77.3910, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Jamshedpur", "state": "Jharkhand", "latitude": 22.8046, "longitude": 86.2029, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Bhilai", "state": "Chhattisgarh", "latitude": 21.1938, "longitude": 81.3509, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Cuttack", "state": "Odisha", "latitude": 20.4625, "longitude": 85.8830, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Firozabad", "state": "Uttar Pradesh", "latitude": 27.1601, "longitude": 78.4116, "emergency_numbers": {"police": "112", "ambulance": "108"}},
        {"name": "Kochi", "state": "Kerala", "latitude": 9.9312, "longitude": 76.2673, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Bhavnagar", "state": "Gujarat", "latitude": 21.7587, "longitude": 72.1489, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        {"name": "Udaipur", "state": "Rajasthan", "latitude": 24.5787, "longitude": 73.6846, "emergency_numbers": {"police": "100", "ambulance": "108"}},
        
    ]

def seed_indonesian_cities():
    # Placeholder for Indonesian cities if needed in future
    pass

def seed_cities():
    db: Session = SessionLocal()
    try:
        # Check if we already have cities
        count = db.query(City).count()
        if count > 0:
            print(f"Cities already seeded. Count: {count}")
            return

        print("Seeding Indian Cities...")
        cities = get_indian_cities()
        
        for city_data in cities:
            city = City(
                name=city_data["name"],
                state=city_data["state"],
                latitude=city_data["latitude"],
                longitude=city_data["longitude"],
                emergency_numbers=city_data["emergency_numbers"]
            )
            db.add(city)
        
        db.commit()
        print(f"Successfully seeded {len(cities)} cities.")
        
    except Exception as e:
        print(f"Error seeding cities: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_cities()
