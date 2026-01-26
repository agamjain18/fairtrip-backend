from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime, timezone
import enum
import os

DATABASE_URL = "sqlite:///./fairshare.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums
class TripStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ExpenseCategory(str, enum.Enum):
    FOOD_DRINK = "food_drink"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    OTHER = "other"

class ExpenseStatus(str, enum.Enum):
    PENDING = "pending"
    SETTLED = "settled"
    DISPUTED = "disputed"

class ActivityType(str, enum.Enum):
    SIGHTSEEING = "sightseeing"
    DINING = "dining"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    ACTIVITY = "activity"
    OTHER = "other"

# Association Tables
trip_members = Table(
    "trip_members",
    Base.metadata,
    Column("trip_id", Integer, ForeignKey("trips.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True)
)

expense_participants = Table(
    "expense_participants",
    Base.metadata,
    Column("expense_id", Integer, ForeignKey("expenses.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True)
)

checklist_assignees = Table(
    "checklist_assignees",
    Base.metadata,
    Column("checklist_item_id", Integer, ForeignKey("checklist_items.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True)
)

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    password_hash = Column(String)
    avatar_url = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    
    # Settings
    two_factor_enabled = Column(Boolean, default=False)
    biometric_enabled = Column(Boolean, default=False)
    dark_mode = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    profile_visibility = Column(Boolean, default=True)
    share_trends = Column(Boolean, default=False)
    show_active_trips = Column(Boolean, default=True)
    
    # Wallet
    total_balance = Column(Float, default=0.0)
    amount_to_receive = Column(Float, default=0.0)
    amount_to_pay = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    data_version = Column(Integer, default=1)

    # Relationships
    created_trips = relationship("Trip", back_populates="creator")
    trips = relationship("Trip", secondary=trip_members, back_populates="members")
    sessions = relationship("UserSession", back_populates="user")
    payment_methods = relationship("PaymentMethod", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class Friendship(Base):
    __tablename__ = "friendships"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="accepted") # pending, accepted, blocked
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_name = Column(String, nullable=True)
    device_type = Column(String, nullable=True) # mobile, desktop, tablet
    location = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="sessions")

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String, nullable=True) # upi, credit_card, debit_card, bank_account
    name = Column(String, nullable=True)
    identifier = Column(String, nullable=True) # UPI ID or masked card number
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="payment_methods")

class OTP(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    otp_code = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    destination = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(TripStatus), default=TripStatus.PLANNING)
    
    # Financial
    total_budget = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    budget_used_percentage = Column(Float, default=0.0)
    
    # Settings
    currency = Column(String, default="USD")
    timezone = Column(String, nullable=True)
    is_public = Column(Boolean, default=False)
    
    # AI Planning
    use_ai = Column(Boolean, default=False)
    ai_status = Column(String, default="pending") # pending, processing, completed, failed
    ai_progress = Column(Integer, default=0) # 0 to 100 percentage
    itinerary_data = Column(JSON, nullable=True) # Stores JSON itinerary
    
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def member_count(self):
        return len(self.members)


    # Relationships
    creator = relationship("User", back_populates="created_trips")
    members = relationship("User", secondary=trip_members, back_populates="trips")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    itinerary_days = relationship("ItineraryDay", back_populates="trip", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="trip", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="trip")
    polls = relationship("Poll", back_populates="trip")
    bucket_list_items = relationship("BucketListItem", back_populates="trip")
    accommodations = relationship("Accommodation", back_populates="trip")
    flights = relationship("Flight", back_populates="trip")
    settlements = relationship("Settlement", back_populates="trip")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    amount = Column(Float)
    currency = Column(String, default="USD")
    category = Column(SQLEnum(ExpenseCategory), default=ExpenseCategory.OTHER)
    status = Column(SQLEnum(ExpenseStatus), default=ExpenseStatus.PENDING)
    
    paid_by_id = Column(Integer, ForeignKey("users.id"))
    
    receipt_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # Split details
    split_type = Column(String, default="equal") # equal, percentage, custom, shares
    split_data = Column(JSON, nullable=True) # JSON object
    
    recurring_expense_id = Column(Integer, nullable=True)
    
    expense_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="expenses")
    paid_by = relationship("User")
    participants = relationship("User", secondary=expense_participants)
    disputes = relationship("Dispute", back_populates="expense")

class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    raised_by_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(Text, nullable=True)
    status = Column(String, default="open") # open, resolved, rejected
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    expense = relationship("Expense", back_populates="disputes")
    raised_by = relationship("User")

class ItineraryDay(Base):
    __tablename__ = "itinerary_days"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    day_number = Column(Integer)
    date = Column(DateTime, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="itinerary_days")
    activities = relationship("Activity", back_populates="day", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("itinerary_days.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(ActivityType), default=ActivityType.OTHER)
    location = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    cost = Column(Float, default=0.0)
    booking_url = Column(String, nullable=True)
    booking_reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    day = relationship("ItineraryDay", back_populates="activities")

class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True) # documents, packing, tasks, etc.
    priority = Column(String, default="medium") # low, medium, high
    is_completed = Column(Boolean, default=False)
    
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="checklist_items")
    assignees = relationship("User", secondary=checklist_assignees)

class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    url = Column(String)
    thumbnail_url = Column(String, nullable=True)
    caption = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    taken_at = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="photos")
    uploaded_by = relationship("User")

class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"))
    question = Column(String)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    trip = relationship("Trip", back_populates="polls")
    created_by = relationship("User")
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")

class PollOption(Base):
    __tablename__ = "poll_options"
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    text = Column(String)
    votes_count = Column(Integer, default=0)
    
    poll = relationship("Poll", back_populates="options")
    votes = relationship("PollVote", back_populates="option", cascade="all, delete-orphan")

class PollVote(Base):
    __tablename__ = "poll_votes"
    id = Column(Integer, primary_key=True, index=True)
    poll_option_id = Column(Integer, ForeignKey("poll_options.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    option = relationship("PollOption", back_populates="votes")
    user = relationship("User")

class BucketListItem(Base):
    __tablename__ = "bucket_list_items"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    added_by_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="bucket_list_items")
    added_by = relationship("User")

class Accommodation(Base):
    __tablename__ = "accommodations"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    name = Column(String)
    type = Column(String, nullable=True) # hotel, hostel, airbnb, etc.
    address = Column(String, nullable=True)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    
    booking_reference = Column(String, nullable=True)
    cost = Column(Float, nullable=True)
    contact_number = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="accommodations")

class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    airline = Column(String, nullable=True)
    flight_number = Column(String, nullable=True)
    
    departure_airport = Column(String, nullable=True)
    arrival_airport = Column(String, nullable=True)
    departure_time = Column(DateTime, nullable=True)
    arrival_time = Column(DateTime, nullable=True)
    
    booking_reference = Column(String, nullable=True)
    seat_number = Column(String, nullable=True)
    gate = Column(String, nullable=True)
    terminal = Column(String, nullable=True)
    status = Column(String, default="scheduled") # scheduled, boarding, departed, arrived, delayed, cancelled
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="flights")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String, nullable=True) # expense, settlement, refund
    amount = Column(Float)
    description = Column(String, nullable=True)
    status = Column(String, default="completed") # pending, completed, failed
    
    related_expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text, nullable=True)
    type = Column(String, nullable=True) # expense, trip, friend, system, settlement, reminder
    is_read = Column(Boolean, default=False)
    
    action_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")

class Settlement(Base):
    __tablename__ = "settlements"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    currency = Column(String, default="USD")
    
    payment_method = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    status = Column(String, default="pending") # pending, completed, cancelled
    settled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="settlements")

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    amount = Column(Float)
    currency = Column(String, default="USD")
    category = Column(SQLEnum(ExpenseCategory), default=ExpenseCategory.OTHER)
    
    paid_by_id = Column(Integer, ForeignKey("users.id"))
    
    split_type = Column(String, default="equal")
    split_data = Column(JSON, nullable=True)
    
    frequency = Column(String, default="monthly") # daily, weekly, monthly, yearly
    interval = Column(Integer, default=1)
    start_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    next_occurrence = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    is_active = Column(Boolean, default=True)
    last_generated = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    id = Column(Integer, primary_key=True, index=True)
    from_currency = Column(String) # e.g., "USD"
    to_currency = Column(String) # e.g., "EUR"
    rate = Column(Float)
    
    source = Column(String, default="manual")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    emergency_numbers = Column(JSON, nullable=True) # JSON object

# Database Helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

def increment_user_version(db: Session, user_id: int):
    """Utility to increment a user's data version for real-time sync"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.data_version = (user.data_version or 0) + 1
        db.commit()

def increment_trip_members_version(db: Session, trip_id: int):
    """Utility to increment version for all members of a trip"""
    from database_sql import Trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip:
        for member in trip.members:
            member.data_version = (member.data_version or 0) + 1
        db.commit()
