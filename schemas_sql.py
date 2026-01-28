from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

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

class ActivityTypeEnum(str, Enum):
    SIGHTSEEING = "sightseeing"
    DINING = "dining"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    ACTIVITY = "activity"
    OTHER = "other"

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    fcm_token: Optional[str] = None

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
    fcm_token: Optional[str] = None

class User(UserBase):
    id: int
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
    friend_code: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

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
    currency: Optional[str] = "USD"
    timezone: Optional[str] = None
    is_public: Optional[bool] = False
    use_ai: Optional[bool] = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    itinerary_data: Optional[dict] = None

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    destination: Optional[str] = None
    start_location: Optional[str] = None
    image_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_budget: Optional[float] = None
    status: Optional[TripStatusEnum] = None
    currency: Optional[str] = None
    is_public: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    itinerary_data: Optional[dict] = None
    ai_status: Optional[str] = None

class Trip(TripBase):
    id: int
    status: TripStatusEnum
    ai_status: Optional[str] = "pending"
    ai_progress: Optional[int] = 0
    total_spent: float
    budget_used_percentage: float
    member_count: Optional[int] = 0
    user_balance: Optional[float] = 0.0
    creator_id: int
    created_at: datetime
    updated_at: datetime

    
    class Config:
        from_attributes = True

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
    trip_id: int
    paid_by_id: int
    participant_ids: List[int]
    receipt_url: Optional[str] = None

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[ExpenseCategoryEnum] = None
    status: Optional[ExpenseStatusEnum] = None
    receipt_url: Optional[str] = None

class Expense(ExpenseBase):
    id: int
    trip_id: int
    trip_title: Optional[str] = None
    paid_by_id: int
    status: ExpenseStatusEnum
    receipt_url: Optional[str] = None
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
    day_id: int

class Activity(ActivityBase):
    id: int
    day_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ItineraryDayBase(BaseModel):
    day_number: int
    date: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None

class ItineraryDayCreate(ItineraryDayBase):
    trip_id: int

class ItineraryDay(ItineraryDayBase):
    id: int
    trip_id: int
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
    trip_id: int
    assignee_ids: Optional[List[int]] = []

class ChecklistItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    is_completed: Optional[bool] = None
    due_date: Optional[datetime] = None

class ChecklistItem(ChecklistItemBase):
    id: int
    trip_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
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
    trip_id: int
    uploaded_by_id: int

class Photo(PhotoBase):
    id: int
    trip_id: int
    uploaded_by_id: int
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# Poll Schemas
class PollOptionBase(BaseModel):
    text: str

class PollOptionCreate(PollOptionBase):
    pass

class PollOption(PollOptionBase):
    id: int
    poll_id: int
    votes_count: int
    
    class Config:
        from_attributes = True

class PollBase(BaseModel):
    question: str
    description: Optional[str] = None
    ends_at: Optional[datetime] = None

class PollCreate(PollBase):
    trip_id: int
    created_by_id: int
    options: List[PollOptionCreate]

class Poll(PollBase):
    id: int
    trip_id: int
    created_by_id: int
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
    trip_id: int
    added_by_id: int

class BucketListItem(BucketListItemBase):
    id: int
    trip_id: int
    added_by_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
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
    google_maps_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class AccommodationCreate(AccommodationBase):
    trip_id: int

class Accommodation(AccommodationBase):
    id: int
    trip_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Transport Schemas
class TransportBase(BaseModel):
    type: Optional[str] = "flight"
    carrier: Optional[str] = None
    flight_number: Optional[str] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    booking_reference: Optional[str] = None
    ticket_url: Optional[str] = None
    seat_number: Optional[str] = None
    tracking_url: Optional[str] = None
    status: Optional[str] = "scheduled"
    cost: Optional[float] = 0.0
    notes: Optional[str] = None

class TransportCreate(TransportBase):
    trip_id: int

class Transport(TransportBase):
    id: int
    trip_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Payment Method Schemas
class PaymentMethodBase(BaseModel):
    type: str
    name: str
    identifier: str
    is_primary: Optional[bool] = False

class PaymentMethodCreate(PaymentMethodBase):
    user_id: int

class PaymentMethod(PaymentMethodBase):
    id: int
    user_id: int
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
    user_id: int
    related_expense_id: Optional[int] = None

class Transaction(TransactionBase):
    id: int
    user_id: int
    related_expense_id: Optional[int] = None
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
    user_id: int

class Notification(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    is_new_user: Optional[bool] = False

class TokenData(BaseModel):
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

class SocialLoginRequest(BaseModel):
    provider: str  # 'google' or 'apple'
    email: str
    display_name: str
    id_token: str

# Settlement Schemas
class SettlementBase(BaseModel):
    amount: float
    currency: Optional[str] = "USD"
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class SettlementCreate(SettlementBase):
    trip_id: int
    from_user_id: int
    to_user_id: int
    status: Optional[str] = "pending"

class SettlementUpdate(BaseModel):
    status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class Settlement(SettlementBase):
    id: int
    trip_id: int
    from_user_id: int
    to_user_id: int
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
    trip_id: Optional[int] = None
    paid_by_id: int
    participant_ids: List[int]

class RecurringExpenseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None

class RecurringExpense(RecurringExpenseBase):
    id: int
    trip_id: Optional[int] = None
    paid_by_id: int
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
    id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True
