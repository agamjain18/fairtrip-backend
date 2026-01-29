from typing import Optional, List, Union
from datetime import datetime, timezone
import enum
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, Indexed, Link, init_beanie, PydanticObjectId
from pydantic import Field, BaseModel

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

# Models

class User(Document):
    email: Indexed(str, unique=True)
    username: Indexed(str, unique=True)
    full_name: Optional[str] = None
    password_hash: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    friend_code: Optional[Indexed(str, unique=True)] = None
    
    # Settings
    two_factor_enabled: bool = False
    biometric_enabled: bool = False
    dark_mode: bool = True
    push_notifications: bool = True
    profile_visibility: bool = True
    share_trends: bool = False
    show_active_trips: bool = True
    
    # Wallet
    total_balance: float = 0.0
    amount_to_receive: float = 0.0
    amount_to_pay: float = 0.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "users"

class Friendship(Document):
    user_id: Link[User]
    friend_id: Link[User]
    status: str = "accepted"  # pending, accepted, blocked
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "friendships"

class UserSession(Document):
    user: Link[User]
    device_name: Optional[str] = None
    device_type: Optional[str] = None  # mobile, desktop, tablet
    location: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool = True
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "user_sessions"

class PaymentMethod(Document):
    user: Link[User]
    type: Optional[str] = None # upi, credit_card, debit_card, bank_account
    name: Optional[str] = None
    identifier: Optional[str] = None # UPI ID or masked card number
    is_primary: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "payment_methods"

class Trip(Document):
    title: str
    description: Optional[str] = None
    destination: Optional[str] = None
    start_location: Optional[str] = None
    image_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: TripStatus = TripStatus.PLANNING
    
    # Financial
    total_budget: float = 0.0
    budget_type: str = "total"
    total_spent: float = 0.0
    budget_used_percentage: float = 0.0
    
    # Settings
    currency: str = "USD"
    timezone: Optional[str] = None
    is_public: bool = False
    
    # AI Planning
    use_ai: bool = False
    ai_status: str = "pending" # pending, processing, completed, failed
    ai_progress: int = 0 # 0 to 100 percentage
    ai_status_message: Optional[str] = None # Current step description
    itinerary_data: Optional[dict] = None  # Stores generated JSON itinerary
    
    creator: Link[User]
    members: List[Link[User]] = []
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "trips"

class Expense(Document):
    trip: Link[Trip]
    title: str
    description: Optional[str] = None
    amount: float
    currency: str = "USD"
    category: ExpenseCategory = ExpenseCategory.OTHER
    status: ExpenseStatus = ExpenseStatus.PENDING
    
    paid_by: Link[User]
    participants: List[Link[User]] = []
    
    receipt_url: Optional[str] = None
    location: Optional[str] = None
    
    # Split details
    split_type: str = "equal"  # equal, percentage, custom, shares
    split_data: Optional[str] = None  # JSON string for custom splits
    
    # Recurring expense reference
    recurring_expense_id: Optional[str] = None
    
    expense_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "expenses"

class Dispute(Document):
    expense: Link[Expense]
    raised_by: Link[User]
    reason: Optional[str] = None
    status: str = "open"  # open, resolved, rejected
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

    class Settings:
        name = "disputes"

class ItineraryDay(Document):
    trip: Link[Trip]
    day_number: int
    date: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "itinerary_days"

class Activity(Document):
    day: Link[ItineraryDay]
    title: str
    description: Optional[str] = None
    type: ActivityType = ActivityType.OTHER
    location: Optional[str] = None
    address: Optional[str] = None
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    
    cost: float = 0.0
    booking_url: Optional[str] = None
    booking_reference: Optional[str] = None
    notes: Optional[str] = None
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "activities"

class ChecklistItem(Document):
    trip: Link[Trip]
    title: str
    description: Optional[str] = None
    category: Optional[str] = None  # documents, packing, tasks, etc.
    priority: str = "medium"  # low, medium, high
    is_completed: bool = False
    
    assignees: List[Link[User]] = []
    
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "checklist_items"

class Photo(Document):
    trip: Link[Trip]
    uploaded_by: Link[User]
    url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    location: Optional[str] = None
    
    taken_at: Optional[datetime] = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "photos"

class Poll(Document):
    trip: Link[Trip]
    created_by: Link[User]
    question: str
    description: Optional[str] = None
    is_active: bool = True
    
    ends_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # In Mongo, we can embed options directly!
    options: List["PollOption"] = []

    class Settings:
        name = "polls"

class PollOption(BaseModel):
    # Embedded in Poll
    text: str
    votes_count: int = 0
    # managing votes separately might be better if we want to track WHO voted
    
class PollVote(Document):
    poll_id: Link[Poll] # Reference to the Poll document
    option_index: int # Index of the option in the poll's option list
    user: Link[User]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "poll_votes"

class BucketListItem(Document):
    trip: Link[Trip]
    added_by: Link[User]
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    is_completed: bool = False
    
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "bucket_list_items"

class Accommodation(Document):
    trip: Link[Trip]
    name: str
    type: Optional[str] = None  # hotel, hostel, airbnb, etc.
    address: Optional[str] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    
    booking_reference: Optional[str] = None
    cost: Optional[float] = None
    contact_number: Optional[str] = None
    notes: Optional[str] = None
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "accommodations"

class Flight(Document):
    trip: Link[Trip]
    airline: Optional[str] = None
    flight_number: Optional[str] = None
    
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    
    booking_reference: Optional[str] = None
    seat_number: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    status: str = "scheduled"  # scheduled, boarding, departed, arrived, delayed, cancelled
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "flights"

class Transaction(Document):
    user: Link[User]
    type: Optional[str] = None  # expense, settlement, refund
    amount: float
    description: Optional[str] = None
    status: str = "completed"  # pending, completed, failed
    
    related_expense: Optional[Link[Expense]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "transactions"

class Notification(Document):
    user: Link[User]
    title: str
    message: Optional[str] = None
    type: Optional[str] = None  # expense, trip, friend, system, settlement, reminder
    is_read: bool = False
    
    action_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notifications"

class Settlement(Document):
    """Track debt settlements between users"""
    trip: Link[Trip]
    from_user: Link[User]
    to_user: Link[User]
    amount: float
    currency: str = "USD"
    
    payment_method: Optional[str] = None  # cash, bank_transfer, upi, card, etc.
    payment_reference: Optional[str] = None  # Transaction ID, UPI ref, etc.
    notes: Optional[str] = None
    
    status: str = "pending"  # pending, completed, cancelled
    settled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "settlements"

class RecurringExpense(Document):
    """Template for recurring expenses like rent, subscriptions"""
    trip: Optional[Link[Trip]] = None  # Can be trip-specific or general
    title: str
    description: Optional[str] = None
    amount: float
    currency: str = "USD"
    category: ExpenseCategory = ExpenseCategory.OTHER
    
    paid_by: Link[User]
    participants: List[Link[User]] = []
    
    split_type: str = "equal"
    split_data: Optional[str] = None
    
    # Recurrence settings
    frequency: str = "monthly"  # daily, weekly, monthly, yearly
    interval: int = 1  # Every X frequency (e.g., every 2 weeks)
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None  # None means indefinite
    next_occurrence: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    is_active: bool = True
    last_generated: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "recurring_expenses"

class CurrencyRate(Document):
    """Store currency exchange rates for multi-currency support"""
    from_currency: str  # e.g., "USD"
    to_currency: str    # e.g., "EUR"
    rate: float         # Exchange rate
    
    # Metadata
    source: Optional[str] = "manual"  # manual, api, etc.
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "currency_rates"

import os

# Database setup
DATABASE_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "fairshare")

async def init_db():
    client = AsyncIOMotorClient(DATABASE_URL)
    await init_beanie(database=client[DATABASE_NAME], document_models=[
        User, Friendship, UserSession, PaymentMethod, Trip, Expense, Dispute,
        ItineraryDay, Activity, ChecklistItem, Photo, Poll, PollVote,
        BucketListItem, Accommodation, Flight, Transaction, Notification,
        Settlement, RecurringExpense, CurrencyRate
    ])
