from database import init_db, User, Trip, Expense, ItineraryDay, Activity, ChecklistItem, Photo, Poll, PollOption, BucketListItem, Accommodation, Flight, PaymentMethod, Transaction, Notification, Friendship, UserSession
from database import TripStatus, ExpenseCategory, ExpenseStatus, ActivityType
import bcrypt
from datetime import datetime, timedelta, timezone
import asyncio

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


async def seed_demo_data():
    try:
        print("Initializing database...")
        await init_db()
        
        # Clear existing data
        print("Clearing existing data...")
        await PollVote.delete_all()
        await Poll.delete_all()
        await Activity.delete_all()
        await ItineraryDay.delete_all()
        await ChecklistItem.delete_all()
        await Photo.delete_all()
        await BucketListItem.delete_all()
        await Accommodation.delete_all()
        await Flight.delete_all()
        await Transaction.delete_all()
        await Notification.delete_all()
        await Expense.delete_all()
        await Friendship.delete_all()
        await UserSession.delete_all()
        await PaymentMethod.delete_all()
        await Trip.delete_all()
        await User.delete_all()
        
        print("Creating demo users...")
        # Create Users
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
                biometric_enabled=False,
                dark_mode=True,
                push_notifications=True,
                profile_visibility=True,
                share_trends=False,
                show_active_trips=True,
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
            ),
            User(
                email="emma@example.com",
                username="emma_wilson",
                full_name="Emma Wilson",
                password_hash=hash_password("password123"),
                avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200",
                phone="+1234567893",
                bio="Beach lover and sunset chaser",
                dark_mode=True,
                total_balance=1500.00,
                amount_to_receive=0.00,
                amount_to_pay=80.00
            ),
            User(
                email="kevin@example.com",
                username="kevin_brown",
                full_name="Kevin Brown",
                password_hash=hash_password("password123"),
                avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200",
                phone="+1234567894",
                bio="Tech geek and travel planner",
                dark_mode=True,
                total_balance=2800.00,
                amount_to_receive=150.00,
                amount_to_pay=0.00
            )
        ]
        
        for user in users:
            await user.insert()
            
        print("Creating friendships...")
        # Create Friendships
        friendships = [
            Friendship(user_id=users[0].id, friend_id=users[1].id, status="accepted"),
            Friendship(user_id=users[0].id, friend_id=users[2].id, status="accepted"),
            Friendship(user_id=users[0].id, friend_id=users[3].id, status="accepted"),
            Friendship(user_id=users[0].id, friend_id=users[4].id, status="accepted"),
            Friendship(user_id=users[1].id, friend_id=users[2].id, status="accepted"),
            Friendship(user_id=users[1].id, friend_id=users[3].id, status="accepted"),
        ]
        for f in friendships:
            await f.insert()

        print("Creating user sessions...")
        # Create User Sessions
        sessions = [
            UserSession(
                user=users[0].id,
                device_name="iPhone 15 Pro",
                device_type="mobile",
                location="London, UK",
                ip_address="192.168.1.1",
                is_active=True,
                last_activity=datetime.now(timezone.utc)
            ),
            UserSession(
                user=users[0].id,
                device_name="MacBook Pro M3",
                device_type="desktop",
                location="Paris, France",
                ip_address="192.168.1.2",
                is_active=False,
                last_activity=datetime.now(timezone.utc) - timedelta(hours=2)
            )
        ]
        for s in sessions:
            await s.insert()
        
        print("Creating payment methods...")
        # Create Payment Methods
        payment_methods = [
            PaymentMethod(
                user=users[0].id,
                type="upi",
                name="UPI / GPAY",
                identifier="fairtrip.user@okaxis",
                is_primary=True
            ),
            PaymentMethod(
                user=users[0].id,
                type="credit_card",
                name="CHASE BANK",
                identifier="**** **** **** 1234",
                is_primary=False
            )
        ]
        for pm in payment_methods:
            await pm.insert()
        
        print("Creating trips...")
        # Create Trips
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
                budget_used_percentage=25.0,
                currency="USD",
                timezone="Asia/Tokyo",
                is_public=False,
                creator=users[0].id
            ),
            Trip(
                title="European Adventure",
                description="Exploring the best of Europe",
                destination="Paris, France",
                image_url="https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400",
                start_date=datetime(2024, 8, 1),
                end_date=datetime(2024, 8, 15),
                status=TripStatus.PLANNING,
                total_budget=5000.00,
                total_spent=0.00,
                budget_used_percentage=0.0,
                currency="EUR",
                timezone="Europe/Paris",
                is_public=False,
                creator=users[1].id
            ),
            Trip(
                title="Bali Beach Retreat",
                description="Relaxing beach vacation in Bali",
                destination="Bali, Indonesia",
                image_url="https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=400",
                start_date=datetime(2024, 9, 10),
                end_date=datetime(2024, 9, 20),
                status=TripStatus.PLANNING,
                total_budget=3000.00,
                total_spent=0.00,
                budget_used_percentage=0.0,
                currency="USD",
                timezone="Asia/Makassar",
                is_public=True,
                creator=users[2].id
            )
        ]
        
        for trip in trips:
            await trip.insert()
        
        # Add members to trips
        trips[0].members = [users[0], users[1], users[2], users[3], users[4]]
        trips[1].members = [users[1], users[2], users[3]]
        trips[2].members = [users[2], users[3]]
        
        for trip in trips:
            await trip.save()
        
        print("Creating expenses...")
        # Create Expenses for Tokyo Trip
        expenses = [
            Expense(
                trip=trips[0].id,
                title="Dinner at Izakaya",
                description="Amazing sushi and sake dinner",
                amount=145.00,
                currency="USD",
                category=ExpenseCategory.FOOD_DRINK,
                status=ExpenseStatus.PENDING,
                paid_by=users[0].id,
                location="Shibuya, Tokyo",
                split_type="equal",
                expense_date=datetime.now(timezone.utc)
            ),
            Expense(
                trip=trips[0].id,
                title="Taxi to Hotel",
                description="From airport to hotel",
                amount=32.50,
                currency="USD",
                category=ExpenseCategory.TRANSPORT,
                status=ExpenseStatus.SETTLED,
                paid_by=users[2].id,
                location="Narita Airport",
                split_type="equal",
                expense_date=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            Expense(
                trip=trips[0].id,
                title="Museum Tickets",
                description="Tokyo National Museum entry",
                amount=60.00,
                currency="USD",
                category=ExpenseCategory.ENTERTAINMENT,
                status=ExpenseStatus.SETTLED,
                paid_by=users[1].id,
                location="Ueno, Tokyo",
                split_type="equal",
                expense_date=datetime.now(timezone.utc) - timedelta(days=2)
            ),
            Expense(
                trip=trips[0].id,
                title="Sushi Dinner",
                description="Omakase experience",
                amount=45.00,
                currency="USD",
                category=ExpenseCategory.FOOD_DRINK,
                status=ExpenseStatus.PENDING,
                paid_by=users[4].id,
                location="Ginza, Tokyo",
                split_type="equal",
                expense_date=datetime.now(timezone.utc)
            ),
            Expense(
                trip=trips[0].id,
                title="Bullet Train Tickets",
                description="Tokyo to Kyoto",
                amount=128.50,
                currency="USD",
                category=ExpenseCategory.TRANSPORT,
                status=ExpenseStatus.PENDING,
                paid_by=users[0].id,
                location="Tokyo Station",
                split_type="equal",
                expense_date=datetime.now(timezone.utc)
            ),
            Expense(
                trip=trips[0].id,
                title="Museum Souvenirs",
                description="Gifts and memorabilia",
                amount=12.00,
                currency="USD",
                category=ExpenseCategory.SHOPPING,
                status=ExpenseStatus.SETTLED,
                paid_by=users[1].id,
                location="Tokyo",
                split_type="equal",
                expense_date=datetime.now(timezone.utc) - timedelta(days=1)
            )
        ]
        
        for expense in expenses:
            expense.participants = [users[0], users[1], users[2], users[3], users[4]]
            await expense.insert()
        
        print("Creating itinerary...")
        # Create Itinerary Days for Tokyo Trip
        itinerary_days = [
            ItineraryDay(
                trip=trips[0].id,
                day_number=1,
                date=datetime(2024, 7, 15),
                title="Arrival Day",
                description="Arrive in Tokyo and settle in"
            ),
            ItineraryDay(
                trip=trips[0].id,
                day_number=2,
                date=datetime(2024, 7, 16),
                title="Explore Shibuya & Harajuku",
                description="Visit the iconic crossing and trendy neighborhoods"
            ),
            ItineraryDay(
                trip=trips[0].id,
                day_number=3,
                date=datetime(2024, 7, 17),
                title="Traditional Tokyo",
                description="Temples, gardens, and cultural experiences"
            )
        ]
        
        for day in itinerary_days:
            await day.insert()
        
        print("Creating activities...")
        # Create Activities
        activities = [
            Activity(
                day=itinerary_days[0].id,
                title="Airport Pickup",
                description="Arrive at Narita Airport",
                type=ActivityType.TRANSPORT,
                location="Narita Airport",
                start_time=datetime(2024, 7, 15, 14, 0),
                end_time=datetime(2024, 7, 15, 15, 30),
                duration_minutes=90,
                cost=32.50
            ),
            Activity(
                day=itinerary_days[0].id,
                title="Hotel Check-in",
                description="Check into our hotel in Shibuya",
                type=ActivityType.ACCOMMODATION,
                location="Shibuya Hotel",
                address="1-1-1 Shibuya, Tokyo",
                start_time=datetime(2024, 7, 15, 16, 0),
                end_time=datetime(2024, 7, 15, 17, 0),
                duration_minutes=60,
                cost=0.00
            ),
            Activity(
                day=itinerary_days[1].id,
                title="Shibuya Crossing",
                description="Visit the world's busiest pedestrian crossing",
                type=ActivityType.SIGHTSEEING,
                location="Shibuya Crossing",
                address="Shibuya, Tokyo",
                start_time=datetime(2024, 7, 16, 10, 0),
                end_time=datetime(2024, 7, 16, 11, 0),
                duration_minutes=60,
                cost=0.00,
                latitude=35.6595,
                longitude=139.7004
            ),
            Activity(
                day=itinerary_days[1].id,
                title="Lunch at Ramen Shop",
                description="Try authentic Tokyo ramen",
                type=ActivityType.DINING,
                location="Ichiran Ramen",
                start_time=datetime(2024, 7, 16, 12, 30),
                end_time=datetime(2024, 7, 16, 13, 30),
                duration_minutes=60,
                cost=15.00
            ),
            Activity(
                day=itinerary_days[2].id,
                title="Senso-ji Temple",
                description="Visit Tokyo's oldest temple",
                type=ActivityType.SIGHTSEEING,
                location="Senso-ji Temple",
                address="Asakusa, Tokyo",
                start_time=datetime(2024, 7, 17, 9, 0),
                end_time=datetime(2024, 7, 17, 11, 0),
                duration_minutes=120,
                cost=0.00,
                latitude=35.7148,
                longitude=139.7967
            )
        ]
        
        for activity in activities:
            await activity.insert()
        
        print("Creating checklist items...")
        # Create Checklist Items
        checklist_items = [
            ChecklistItem(
                trip=trips[0].id,
                title="Book flights",
                description="Book round-trip flights to Tokyo",
                category="travel",
                priority="high",
                is_completed=True,
                completed_at=datetime.now(timezone.utc) - timedelta(days=30)
            ),
            ChecklistItem(
                trip=trips[0].id,
                title="Get travel insurance",
                description="Purchase comprehensive travel insurance",
                category="documents",
                priority="high",
                is_completed=True,
                completed_at=datetime.now(timezone.utc) - timedelta(days=25)
            ),
            ChecklistItem(
                trip=trips[0].id,
                title="Pack sunscreen",
                description="SPF 50+ for summer weather",
                category="packing",
                priority="medium",
                is_completed=False,
                due_date=datetime(2024, 7, 14)
            ),
            ChecklistItem(
                trip=trips[0].id,
                title="Download offline maps",
                description="Google Maps offline for Tokyo",
                category="tasks",
                priority="medium",
                is_completed=False,
                due_date=datetime(2024, 7, 14)
            ),
            ChecklistItem(
                trip=trips[0].id,
                title="Exchange currency",
                description="Get Japanese Yen",
                category="tasks",
                priority="high",
                is_completed=True,
                completed_at=datetime.now(timezone.utc) - timedelta(days=5)
            ),
            ChecklistItem(
                trip=trips[0].id,
                title="Pack camera",
                description="DSLR with extra batteries",
                category="packing",
                priority="medium",
                is_completed=False,
                due_date=datetime(2024, 7, 14)
            )
        ]
        
        for item in checklist_items:
            await item.insert()
        
        # Assign checklist items
        checklist_items[0].assignees = [users[0]]
        checklist_items[1].assignees = [users[0]]
        checklist_items[2].assignees = [users[0], users[1]]
        checklist_items[3].assignees = [users[2]]
        checklist_items[4].assignees = [users[0]]
        checklist_items[5].assignees = [users[2]]

        for item in checklist_items:
            await item.save()

        print("Creating photos...")
        # Create Photos
        photos = [
            Photo(
                trip=trips[0].id,
                uploaded_by=users[0].id,
                url="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800",
                thumbnail_url="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=200",
                caption="Amazing view of Tokyo Tower at sunset!",
                location="Tokyo Tower",
                taken_at=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            Photo(
                trip=trips[0].id,
                uploaded_by=users[1].id,
                url="https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=800",
                thumbnail_url="https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=200",
                caption="Beautiful cherry blossoms in the park",
                location="Ueno Park",
                taken_at=datetime.now(timezone.utc) - timedelta(days=2)
            ),
            Photo(
                trip=trips[0].id,
                uploaded_by=users[2].id,
                url="https://images.unsplash.com/photo-1513407030348-c983a97b98d8?w=800",
                thumbnail_url="https://images.unsplash.com/photo-1513407030348-c983a97b98d8?w=200",
                caption="Delicious ramen for lunch",
                location="Shibuya",
                taken_at=datetime.now(timezone.utc)
            )
        ]
        
        for photo in photos:
            await photo.insert()
        
        print("Creating polls...")
        # Create Polls
        poll = Poll(
            trip=trips[0].id,
            created_by=users[0].id,
            question="Where should we have dinner tonight?",
            description="Vote for your preferred restaurant",
            is_active=True,
            ends_at=datetime.now(timezone.utc) + timedelta(hours=6),
            options=[
                PollOption(text="Sushi Restaurant", votes_count=3),
                PollOption(text="Ramen Shop", votes_count=1),
                PollOption(text="Izakaya", votes_count=1)
            ]
        )
        await poll.insert()
        
        print("Creating bucket list items...")
        # Create Bucket List Items
        bucket_items = [
            BucketListItem(
                trip=trips[0].id,
                added_by=users[0].id,
                title="Visit Mount Fuji",
                description="See the iconic mountain",
                location="Mount Fuji",
                is_completed=False
            ),
            BucketListItem(
                trip=trips[0].id,
                added_by=users[1].id,
                title="Try authentic sushi",
                description="Omakase experience",
                location="Tsukiji Market",
                is_completed=True,
                completed_at=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            BucketListItem(
                trip=trips[0].id,
                added_by=users[2].id,
                title="Visit TeamLab Borderless",
                description="Digital art museum",
                location="Odaiba",
                is_completed=False
            )
        ]
        
        for item in bucket_items:
            await item.insert()
        
        print("Creating accommodations...")
        # Create Accommodations
        accommodations = [
            Accommodation(
                trip=trips[0].id,
                name="Shibuya Grand Hotel",
                type="hotel",
                address="1-1-1 Shibuya, Shibuya-ku, Tokyo",
                check_in=datetime(2024, 7, 15, 15, 0),
                check_out=datetime(2024, 7, 22, 11, 0),
                booking_reference="HTL-123456",
                cost=1200.00,
                contact_number="+81-3-1234-5678",
                notes="Free breakfast included",
                latitude=35.6595,
                longitude=139.7004
            )
        ]
        
        for acc in accommodations:
            await acc.insert()
        
        print("Creating flights...")
        # Create Flights
        flights = [
            Flight(
                trip=trips[0].id,
                airline="Japan Airlines",
                flight_number="JL005",
                departure_airport="JFK",
                arrival_airport="NRT",
                departure_time=datetime(2024, 7, 15, 11, 0),
                arrival_time=datetime(2024, 7, 16, 14, 30),
                booking_reference="ABC123",
                seat_number="12A",
                gate="B23",
                terminal="1",
                status="scheduled"
            ),
            Flight(
                trip=trips[0].id,
                airline="Japan Airlines",
                flight_number="JL006",
                departure_airport="NRT",
                arrival_airport="JFK",
                departure_time=datetime(2024, 7, 22, 16, 0),
                arrival_time=datetime(2024, 7, 22, 15, 30),
                booking_reference="ABC124",
                seat_number="12A",
                gate="TBA",
                terminal="1",
                status="scheduled"
            )
        ]
        for flight in flights:
            await flight.insert()
        
        print("Creating transactions...")
        # Create Transactions
        transactions = [
            Transaction(
                user=users[0].id,
                type="expense",
                amount=-45.00,
                description="Sushi Dinner",
                status="completed",
                related_expense=expenses[3].id
            ),
            Transaction(
                user=users[0].id,
                type="expense",
                amount=128.50,
                description="Bullet Train Tickets",
                status="completed",
                related_expense=expenses[4].id
            ),
            Transaction(
                user=users[1].id,
                type="settlement",
                amount=12.00,
                description="Museum Souvenirs",
                status="completed",
                related_expense=expenses[5].id
            )
        ]
        
        for t in transactions:
            await t.insert()
        
        print("Creating notifications...")
        # Create Notifications
        notifications = [
            Notification(
                user=users[0].id,
                title="New expense added",
                message="Sarah added 'Museum Tickets' for $60.00",
                type="expense",
                is_read=False,
                action_url="/trip/1/expenses/3"
            ),
            Notification(
                user=users[0].id,
                title="Trip starting soon!",
                message="Summer in Tokyo starts in 2 days",
                type="trip",
                is_read=False,
                action_url="/trip/1"
            ),
            Notification(
                user=users[0].id,
                title="Friend request accepted",
                message="Emma Wilson accepted your friend request",
                type="friend",
                is_read=True,
                action_url="/friends"
            )
        ]
        
        for n in notifications:
            await n.insert()
        
        print("Demo data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        raise

if __name__ == "__main__":
    from database import PollVote
    asyncio.run(seed_demo_data())
