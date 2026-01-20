from database import init_db
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Indian Cities with Emergency Helpline Numbers
INDIAN_CITIES_DATA = [
    # Major Metro Cities
    {"name": "Mumbai", "state": "Maharashtra", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "1800-22-1111"},
    {"name": "Delhi", "state": "Delhi", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "1800-11-1363"},
    {"name": "Bangalore", "state": "Karnataka", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "080-22212901"},
    {"name": "Hyderabad", "state": "Telangana", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "040-23454444"},
    {"name": "Chennai", "state": "Tamil Nadu", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "044-25361461"},
    {"name": "Kolkata", "state": "West Bengal", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "033-22143526"},
    {"name": "Pune", "state": "Maharashtra", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "020-26128293"},
    {"name": "Ahmedabad", "state": "Gujarat", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "079-26585500"},
    
    # State Capitals & Major Cities
    {"name": "Jaipur", "state": "Rajasthan", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0141-5110598"},
    {"name": "Lucknow", "state": "Uttar Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0522-2308916"},
    {"name": "Chandigarh", "state": "Chandigarh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0172-2704363"},
    {"name": "Bhopal", "state": "Madhya Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0755-2778383"},
    {"name": "Indore", "state": "Madhya Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0731-2493555"},
    {"name": "Nagpur", "state": "Maharashtra", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0712-2561325"},
    {"name": "Surat", "state": "Gujarat", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0261-2424021"},
    {"name": "Vadodara", "state": "Gujarat", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0265-2426426"},
    {"name": "Rajkot", "state": "Gujarat", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0281-2234507"},
    
    # Tourist Destinations
    {"name": "Goa", "state": "Goa", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0832-2438751"},
    {"name": "Agra", "state": "Uttar Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0562-2226368"},
    {"name": "Varanasi", "state": "Uttar Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0542-2506670"},
    {"name": "Amritsar", "state": "Punjab", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0183-2401452"},
    {"name": "Udaipur", "state": "Rajasthan", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0294-2411535"},
    {"name": "Jaisalmer", "state": "Rajasthan", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "02992-252406"},
    {"name": "Shimla", "state": "Himachal Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0177-2652561"},
    {"name": "Manali", "state": "Himachal Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "01902-252175"},
    {"name": "Darjeeling", "state": "West Bengal", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0354-2254102"},
    {"name": "Ooty", "state": "Tamil Nadu", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0423-2443977"},
    {"name": "Mysore", "state": "Karnataka", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0821-2423652"},
    {"name": "Kochi", "state": "Kerala", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0484-2371761"},
    {"name": "Thiruvananthapuram", "state": "Kerala", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0471-2321132"},
    
    # North India
    {"name": "Dehradun", "state": "Uttarakhand", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0135-2746817"},
    {"name": "Rishikesh", "state": "Uttarakhand", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0135-2430209"},
    {"name": "Haridwar", "state": "Uttarakhand", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0133-2427370"},
    {"name": "Srinagar", "state": "Jammu & Kashmir", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0194-2452690"},
    {"name": "Leh", "state": "Ladakh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "01982-252297"},
    
    # East India
    {"name": "Patna", "state": "Bihar", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0612-2235411"},
    {"name": "Ranchi", "state": "Jharkhand", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0651-2491040"},
    {"name": "Bhubaneswar", "state": "Odisha", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0674-2432177"},
    {"name": "Puri", "state": "Odisha", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "06752-222664"},
    {"name": "Guwahati", "state": "Assam", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0361-2547102"},
    {"name": "Gangtok", "state": "Sikkim", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "03592-221634"},
    
    # South India
    {"name": "Coimbatore", "state": "Tamil Nadu", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0422-2211777"},
    {"name": "Madurai", "state": "Tamil Nadu", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0452-2334757"},
    {"name": "Pondicherry", "state": "Puducherry", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0413-2339497"},
    {"name": "Visakhapatnam", "state": "Andhra Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0891-2788939"},
    {"name": "Vijayawada", "state": "Andhra Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0866-2578349"},
    {"name": "Tirupati", "state": "Andhra Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0877-2289333"},
    
    # Central India
    {"name": "Raipur", "state": "Chhattisgarh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0771-2511326"},
    {"name": "Jabalpur", "state": "Madhya Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0761-2677290"},
    {"name": "Gwalior", "state": "Madhya Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0751-2340370"},
    
    # Additional Popular Cities
    {"name": "Nashik", "state": "Maharashtra", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0253-2577059"},
    {"name": "Aurangabad", "state": "Maharashtra", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0240-2331217"},
    {"name": "Jodhpur", "state": "Rajasthan", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0291-2545083"},
    {"name": "Bikaner", "state": "Rajasthan", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0151-2523900"},
    {"name": "Ajmer", "state": "Rajasthan", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0145-2627426"},
    {"name": "Pushkar", "state": "Rajasthan", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0145-2772040"},
    {"name": "Kanpur", "state": "Uttar Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0512-2309988"},
    {"name": "Allahabad", "state": "Uttar Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0532-2408873"},
    {"name": "Mathura", "state": "Uttar Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0565-2420964"},
    {"name": "Vrindavan", "state": "Uttar Pradesh", "police": "100", "ambulance": "102", "fire": "101", "tourist_helpline": "0565-2443769"},
]

async def seed_indian_cities():
    """Seed Indian cities with emergency helpline numbers"""
    try:
        print("Connecting to MongoDB...")
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = client["fairshare"]
        cities_collection = db["indian_cities"]
        
        # Clear existing data
        print("Clearing existing cities data...")
        await cities_collection.delete_many({})
        
        # Insert new data
        print(f"Inserting {len(INDIAN_CITIES_DATA)} Indian cities...")
        result = await cities_collection.insert_many(INDIAN_CITIES_DATA)
        
        print(f"✅ Successfully inserted {len(result.inserted_ids)} cities!")
        print("\nSample cities:")
        for city in INDIAN_CITIES_DATA[:5]:
            print(f"  - {city['name']}, {city['state']}")
            print(f"    Police: {city['police']}, Ambulance: {city['ambulance']}, Fire: {city['fire']}")
        
        # Create index for faster searching
        await cities_collection.create_index("name")
        await cities_collection.create_index("state")
        print("\n✅ Created indexes on 'name' and 'state' fields")
        
        client.close()
        print("\n🎉 Indian cities database seeded successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding cities: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_indian_cities())
