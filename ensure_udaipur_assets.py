import os
import shutil
import json
from database_sql import SessionLocal, City, DestinationImage

def sync_assets_and_data():
    # 1. Define paths
    frontend_assets_dir = os.path.join("..", "frontend", "assets", "udaipure")
    frontend_json_path = os.path.join(frontend_assets_dir, "data", "destinations.json")
    backend_uploads_dir = os.path.join("uploads", "udaipur")

    # 2. Ensure backend uploads directory exists
    if not os.path.exists(backend_uploads_dir):
        os.makedirs(backend_uploads_dir)
        print(f"Created directory: {backend_uploads_dir}")

    # 3. Copy images to backend uploads (simulating server upload)
    print("Uploading images to server (copying to uploads)...")
    for filename in os.listdir(frontend_assets_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            src = os.path.join(frontend_assets_dir, filename)
            dst = os.path.join(backend_uploads_dir, filename)
            shutil.copy2(src, dst)
            print(f"  Uploaded: {filename}")

    # 4. Load JSON data
    if not os.path.exists(frontend_json_path):
        print(f"Error: {frontend_json_path} not found")
        return

    with open(frontend_json_path, 'r') as f:
        data = json.load(f)

    # 5. Push data to database
    db = SessionLocal()
    try:
        city_name = data.get("city")
        city = db.query(City).filter(City.name == city_name).first()
        
        if not city:
            print(f"Creating city record: {city_name}")
            city = City(name=city_name, state=data.get("state"))
            db.add(city)
            db.commit()
            db.refresh(city)

        # Update popular spots with proper URLs
        city.popular_spots = data.get("popular_spots", [])
        print(f"✅ Updated popular spots for {city_name} in DB.")

        # Update DestinationImage table for featured sliders
        # Clear existing ones for this city to prevent duplicates
        db.query(DestinationImage).filter(DestinationImage.destination.like(f"{city_name}%")).delete(synchronize_session=False)
        
        for spot in data.get("popular_spots", []):
            dest_img = DestinationImage(
                destination=f"{city_name} {spot['name']}",
                image_url=spot['image_url'],
                famous_spot=spot['name']
            )
            db.add(dest_img)
            print(f"✅ Added featured slider image for: {spot['name']}")

        db.commit()
        print("🚀 All assets uploaded and database synchronized successfully!")
    except Exception as e:
        print(f"❌ Error during DB sync: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_assets_and_data()
