from pydantic import BaseModel, EmailStr, BeforeValidator, Field
from typing import Optional, List, Annotated, Any
from datetime import datetime
from enum import Enum

# Helper for ObjectId -> str
def str_object_id(v: Any) -> str:
    if v is None:
        return None
    return str(v)

PyObjectId = Annotated[str, BeforeValidator(str_object_id)]

# Enums
class TripStatusEnum(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ExpenseCategoryEnum(str, Enum):
    FOOD_DRINK = "food_drink"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    OTHER = "other"

class ExpenseStatusEnum(str, Enum):
    PENDING = "pending"
    SETTLED = "settled"
    DISPUTED = "disputed"

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    two_factor_enabled: Optional[bool] = None
    biometric_enabled: Optional[bool] = None
    dark_mode: Optional[bool] = None
    push_notifications: Optional[bool] = None
    profile_visibility: Optional[bool] = None
    share_trends: Optional[bool] = None
    show_active_trips: Optional[bool] = None

class User(UserBase):
    id: PyObjectId  # Changed to str
    friend_code: Optional[str] = None
    two_factor_enabled: bool
    biometric_enabled: bool
    dark_mode: bool
    push_notifications: bool
    profile_visibility: bool
    share_trends: bool
    show_active_trips: bool
    total_balance: float
    amount_to_receive: float
    amount_to_pay: float
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True

# Trip Schemas
class TripBase(BaseModel):
    title: str
    description: Optional[str] = None
    destination: Optional[str] = None
    start_location: Optional[str] = None
    image_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_budget: Optional[float] = 0.0
    budget_type: Optional[str] = "total" # total, individual
    currency: Optional[str] = "USD"
    timezone: Optional[str] = None
    is_public: Optional[bool] = False
    use_ai: Optional[bool] = False # AI Planning flag
    itinerary_data: Optional[dict] = None # Stores generated JSON itinerary

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    destination: Optional[str] = None
    image_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_budget: Optional[float] = None
    status: Optional[TripStatusEnum] = None
    currency: Optional[str] = None
    is_public: Optional[bool] = None
    itinerary_data: Optional[dict] = None
    ai_status: Optional[str] = None

class Trip(TripBase):
    id: PyObjectId # Changed to str
    status: TripStatusEnum
    ai_status: Optional[str] = "pending"
    ai_progress: Optional[int] = 0
    ai_status_message: Optional[str] = None
    total_spent: float
    budget_used_percentage: float
    creator_id: Optional[PyObjectId] = None # Changed to str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True

# Expense Schemas
class ExpenseBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float
    currency: Optional[str] = "USD"
    category: Optional[ExpenseCategoryEnum] = ExpenseCategoryEnum.OTHER
    location: Optional[str] = None
    split_type: Optional[str] = "equal"
    split_data: Optional[str] = None
    expense_date: Optional[datetime] = None

class ExpenseCreate(ExpenseBase):
    trip_id: str # Changed to str
    paid_by: str # Changed to str
    participant_ids: List[str] # Changed to str
    receipt_url: Optional[str] = None

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[ExpenseCategoryEnum] = None
    status: Optional[ExpenseStatusEnum] = None
    receipt_url: Optional[str] = None

class Expense(ExpenseBase):
    id: PyObjectId # Changed to str
    trip_id: Optional[PyObjectId] = None # Changed to str
    paid_by: Optional[PyObjectId] = None # Changed to str
    status: ExpenseStatusEnum
    receipt_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Itinerary Schemas
class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: Optional[str] = "other"
    location: Optional[str] = None
    address: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    cost: Optional[float] = 0.0
    booking_url: Optional[str] = None
    booking_reference: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ActivityCreate(ActivityBase):
    day_id: str # Changed to str

class Activity(ActivityBase):
    id: PyObjectId # Changed to str
    # day_id: str # Removed because embedded often, or ensure link
    day_id: Optional[PyObjectId] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ItineraryDayBase(BaseModel):
    day_number: int
    date: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None

class ItineraryDayCreate(ItineraryDayBase):
    trip_id: str # Changed to str

class ItineraryDay(ItineraryDayBase):
    id: PyObjectId # Changed to str
    trip_id: Optional[PyObjectId] = None # Changed to str
    activities: List[Activity] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

# Checklist Schemas
class ChecklistItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None

class ChecklistItemCreate(ChecklistItemBase):
    trip_id: str # Changed to str
    assignee_ids: Optional[List[str]] = [] # Changed to str

class ChecklistItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    is_completed: Optional[bool] = None
    due_date: Optional[datetime] = None

class ChecklistItem(ChecklistItemBase):
    id: PyObjectId # Changed to str
    trip_id: Optional[PyObjectId] = None
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Photo Schemas
class PhotoBase(BaseModel):
    url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    location: Optional[str] = None
    taken_at: Optional[datetime] = None

class PhotoCreate(PhotoBase):
    trip_id: str
    uploaded_by: str

class Photo(PhotoBase):
    id: PyObjectId
    trip_id: Optional[PyObjectId] = None
    uploaded_by: Optional[PyObjectId] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# Poll Schemas
class PollOptionBase(BaseModel):
    text: str

class PollOptionCreate(PollOptionBase):
    pass

class PollOption(PollOptionBase):
    # id: int -> might not need ID if embedded, or generate str
    # If using Mongo embed, items might not have IDs unless we give them
    # Beanie might not give IDs to inner Pydantic models automatically
    votes_count: int
    
    class Config:
        from_attributes = True

class PollBase(BaseModel):
    question: str
    description: Optional[str] = None
    ends_at: Optional[datetime] = None

class PollCreate(PollBase):
    trip_id: str
    created_by: str
    options: List[PollOptionCreate]

class Poll(PollBase):
    id: PyObjectId
    trip_id: Optional[PyObjectId] = None
    created_by: Optional[PyObjectId] = None
    is_active: bool
    options: List[PollOption] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

# Bucket List Schemas
class BucketListItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None

class BucketListItemCreate(BucketListItemBase):
    trip_id: str
    added_by: str

class BucketListItem(BucketListItemBase):
    id: PyObjectId
    trip_id: Optional[PyObjectId] = None
    added_by: Optional[PyObjectId] = None
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Accommodation Schemas
class AccommodationBase(BaseModel):
    name: str
    type: Optional[str] = None
    address: Optional[str] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    booking_reference: Optional[str] = None
    cost: Optional[float] = None
    contact_number: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class AccommodationCreate(AccommodationBase):
    trip_id: str

class Accommodation(AccommodationBase):
    id: PyObjectId
    trip_id: Optional[PyObjectId] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Flight Schemas
class FlightBase(BaseModel):
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
    status: Optional[str] = "scheduled"

class FlightCreate(FlightBase):
    trip_id: str

class Flight(FlightBase):
    id: PyObjectId
    trip_id: Optional[PyObjectId] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Payment Method Schemas
class PaymentMethodBase(BaseModel):
    type: str
    name: str
    identifier: str
    is_primary: Optional[bool] = False

class PaymentMethodCreate(PaymentMethodBase):
    user_id: str

class PaymentMethod(PaymentMethodBase):
    id: PyObjectId
    user_id: Optional[PyObjectId] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionBase(BaseModel):
    type: str
    amount: float
    description: Optional[str] = None
    status: Optional[str] = "completed"

class TransactionCreate(TransactionBase):
    user_id: str
    related_expense_id: Optional[str] = None

class Transaction(TransactionBase):
    id: PyObjectId
    user_id: Optional[PyObjectId] = None
    related_expense_id: Optional[PyObjectId]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Notification Schemas
class NotificationBase(BaseModel):
    title: str
    message: Optional[str] = None
    type: Optional[str] = None
    action_url: Optional[str] = None

class NotificationCreate(NotificationBase):
    user_id: str

class Notification(NotificationBase):
    id: PyObjectId
    user_id: Optional[PyObjectId] = None
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[PyObjectId] = None

class LoginRequest(BaseModel):
    email: str
    password: str

# Settlement Schemas
class SettlementBase(BaseModel):
    amount: float
    currency: Optional[str] = "USD"
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class SettlementCreate(SettlementBase):
    trip_id: str
    from_user_id: str
    to_user_id: str

class SettlementUpdate(BaseModel):
    status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class Settlement(SettlementBase):
    id: PyObjectId
    trip_id: Optional[PyObjectId] = None
    from_user_id: Optional[PyObjectId] = None
    to_user_id: Optional[PyObjectId] = None
    status: str
    settled_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Recurring Expense Schemas
class RecurringExpenseBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float
    currency: Optional[str] = "USD"
    category: Optional[ExpenseCategoryEnum] = ExpenseCategoryEnum.OTHER
    split_type: Optional[str] = "equal"
    split_data: Optional[str] = None
    frequency: str = "monthly"
    interval: int = 1
    start_date: datetime
    end_date: Optional[datetime] = None

class RecurringExpenseCreate(RecurringExpenseBase):
    trip_id: Optional[str] = None
    paid_by: str
    participant_ids: List[str]

class RecurringExpenseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None

class RecurringExpense(RecurringExpenseBase):
    id: PyObjectId
    trip_id: Optional[PyObjectId] = None
    paid_by: Optional[PyObjectId] = None
    next_occurrence: datetime
    is_active: bool
    last_generated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Currency Rate Schemas
class CurrencyRateBase(BaseModel):
    from_currency: str
    to_currency: str
    rate: float
    source: Optional[str] = "manual"

class CurrencyRateCreate(CurrencyRateBase):
    pass

class CurrencyRate(CurrencyRateBase):
    id: PyObjectId
    updated_at: datetime
    
    class Config:
        from_attributes = True

