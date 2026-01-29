from database_sql import SessionLocal, City, DestinationImage
import json

def update():
    db = SessionLocal()
    # 1. Update City popular spots
    city = db.query(City).filter(City.name == "Udaipur").first()
    images = [
        "/static/udaipur/download.jpg",
        "/static/udaipur/download%20(1).jpg",
        "/static/udaipur/download%20(2).jpg",
        "/static/udaipur/download%20(3).jpg",
        "/static/udaipur/images.jpg"
    ]
    
    if city:
        city.popular_spots = [
            {"name": "City Palace", "image_url": images[0], "description": "A magnificent palace complex"},
            {"name": "Lake Pichola", "image_url": images[1], "description": "An artificial fresh water lake"},
            {"name": "Jag Mandir", "image_url": images[2], "description": "A palace built on an island"},
            {"name": "Saheliyon-ki-Bari", "image_url": images[3], "description": "Courtyard of the Maidens"},
            {"name": "Fateh Sagar Lake", "image_url": images[4], "description": "Another beautiful lake"}
        ]
        print("Updated Udaipur popular spots")
    else:
        print("City Udaipur not found")

    # 2. Add to DestinationImage for general slider
    # Clear old ones if they exist for Udaipur
    db.query(DestinationImage).filter(DestinationImage.destination.like("Udaipur%")).delete(synchronize_session=False)
    
    spots = ["City Palace", "Lake Pichola", "Jag Mandir", "Saheliyon-ki-Bari", "Fateh Sagar Lake"]
    for i, img in enumerate(images):
        dest_img = DestinationImage(
            destination=f"Udaipur {spots[i]}",
            image_url=img,
            famous_spot=spots[i]
        )
        db.add(dest_img)
    
    db.commit()
    print("Updated DestinationImage table")
    db.close()

if __name__ == "__main__":
    update()
