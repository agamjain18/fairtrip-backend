from database_sql import engine, SessionLocal, Base, User, Trip, Expense, ItineraryDay, Activity, ChecklistItem, Photo, Poll, PollOption, BucketListItem, Accommodation, Flight, PaymentMethod, Transaction, Notification, Friendship, TripStatus, ExpenseCategory, ActivityType
import bcrypt
from datetime import datetime, timedelta, timezone
import json

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def seed_sql_data():
    # Create tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Creating demo users...")
        users = [
            User(
                email="john@example.com",
                username="john_doe",
                full_name="John Doe",
                password_hash=hash_password("password123"),
                avatar_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200",
                phone="+1234567890",
                bio="Travel enthusiast and adventure seeker",
                two_factor_enabled=True,
                dark_mode=True,
                total_balance=2450.80,
                amount_to_receive=340.20,
                amount_to_pay=45.00
            ),
            User(
                email="sarah@example.com",
                username="sarah_smith",
                full_name="Sarah Smith",
                password_hash=hash_password("password123"),
                avatar_url="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200",
                phone="+1234567891",
                bio="Foodie and culture lover",
                dark_mode=True,
                total_balance=1800.50,
                amount_to_receive=200.00,
                amount_to_pay=0.00
            ),
            User(
                email="alex@example.com",
                username="alex_johnson",
                full_name="Alex Johnson",
                password_hash=hash_password("password123"),
                avatar_url="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=200",
                phone="+1234567892",
                bio="Photography and nature lover",
                dark_mode=True,
                total_balance=3200.00,
                amount_to_receive=500.00,
                amount_to_pay=120.00
            )
        ]
        
        for user in users:
            db.add(user)
        db.commit()

        print("Creating friendships...")
        friendships = [
            Friendship(user_id=users[0].id, friend_id=users[1].id, status="accepted"),
            Friendship(user_id=users[0].id, friend_id=users[2].id, status="accepted")
        ]
        for f in friendships:
            db.add(f)

        print("Creating payment methods...")
        pm = PaymentMethod(
            user_id=users[0].id,
            type="upi",
            name="UPI / GPAY",
            identifier="fairtrip.user@okaxis",
            is_primary=True
        )
        db.add(pm)

        print("Creating trips...")
        trips = [
            Trip(
                title="Summer in Tokyo",
                description="An amazing summer adventure in Tokyo with friends",
                destination="Tokyo, Japan",
                image_url="https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400",
                start_date=datetime(2024, 7, 15),
                end_date=datetime(2024, 7, 22),
                status=TripStatus.ACTIVE,
                total_budget=2500.00,
                total_spent=625.00,
                currency="USD",
                timezone="Asia/Tokyo",
                creator_id=users[0].id,
                itinerary_data={"days": [{"day": 1, "activities": ["Arrival"]}]}
            )
        ]
        for trip in trips:
            trip.members.append(users[0])
            trip.members.append(users[1])
            trip.members.append(users[2])
            db.add(trip)
        db.commit()

        print("Creating expenses...")
        expense = Expense(
            trip_id=trips[0].id,
            title="Dinner at Izakaya",
            description="Amazing sushi and sake dinner",
            amount=145.00,
            currency="USD",
            category=ExpenseCategory.FOOD_DRINK,
            paid_by_id=users[0].id,
            location="Shibuya, Tokyo",
            split_type="equal"
        )
        expense.participants.append(users[0])
        expense.participants.append(users[1])
        db.add(expense)

        print("Creating itinerary...")
        day = ItineraryDay(
            trip_id=trips[0].id,
            day_number=1,
            date=datetime(2024, 7, 15),
            title="Arrival Day",
            description="Arrive in Tokyo"
        )
        db.add(day)
        db.commit()

        print("Creating activities...")
        activity = Activity(
            day_id=day.id,
            title="Airport Pickup",
            type=ActivityType.TRANSPORT,
            location="Narita Airport",
            start_time=datetime(2024, 7, 15, 14, 0),
            duration_minutes=90,
            cost=32.50
        )
        db.add(activity)

        print("Creating checklist items...")
        item = ChecklistItem(
            trip_id=trips[0].id,
            title="Book flights",
            category="travel",
            priority="high",
            is_completed=True
        )
        item.assignees.append(users[0])
        db.add(item)

        print("Creating polls...")
        poll = Poll(
            trip_id=trips[0].id,
            created_by_id=users[0].id,
            question="Where should we have dinner tonight?"
        )
        db.add(poll)
        db.commit()
        
        option = PollOption(poll_id=poll.id, text="Sushi Restaurant")
        db.add(option)

        db.commit()
        print("SQL Demo data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_sql_data()
