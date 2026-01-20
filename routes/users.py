from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import bcrypt
from database import User, Friendship, UserSession, PaymentMethod
from schemas import User as UserSchema, UserCreate, UserUpdate, PaymentMethod as PaymentMethodSchema, PaymentMethodCreate
from datetime import datetime, timezone

router = APIRouter(prefix="/users", tags=["users"])

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


@router.get("/", response_model=List[UserSchema])
async def get_users(skip: int = 0, limit: int = 100):
    """Get all users"""
    users = await User.find_all().skip(skip).limit(limit).to_list()
    return users

@router.get("/{user_id}", response_model=UserSchema)
async def get_user(user_id: str):
    """Get a specific user"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/friends", response_model=List[UserSchema])
async def get_user_friends(user_id: str):
    """Get user's friends"""
    friendships = await Friendship.find(Friendship.user_id.id == user_id, Friendship.status == "accepted").to_list()
    
    friends = []
    for f in friendships:
         # Beanie's fetch_related approach or explicit get
         # If friendships stores Links, efficient way is to follow them.
         # But Link is lazy, so we may need to fetch.
         if f.friend_id:
             friend = await User.get(f.friend_id.id)
             if friend:
                 friends.append(friend)
    return friends

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Create a new user"""
    # Check if user already exists
    existing_user_email = await User.find_one(User.email == user.email)
    existing_user_username = await User.find_one(User.username == user.username)
    
    if existing_user_email or existing_user_username:
        raise HTTPException(status_code=400, detail="User already exists")
    
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        password_hash=hash_password(user.password),
        avatar_url=user.avatar_url,
        phone=user.phone,
        bio=user.bio,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await db_user.create()
    return db_user

@router.put("/{user_id}", response_model=UserSchema)
async def update_user(user_id: str, user_update: UserUpdate):
    """Update user details"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    
    await user.set(update_data)
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """Delete a user"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await user.delete()
    return None

@router.get("/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """Get user's active sessions"""
    sessions = await UserSession.find(UserSession.user.id == user_id).to_list()
    return sessions

@router.post("/{user_id}/sessions/{session_id}/revoke")
async def revoke_session(user_id: str, session_id: str):
    """Revoke a user session"""
    session = await UserSession.find_one(UserSession.id == session_id, UserSession.user.id == user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    await session.save()
    return {"message": "Session revoked successfully"}

@router.get("/{user_id}/payment-methods", response_model=List[PaymentMethodSchema])
async def get_payment_methods(user_id: str):
    """Get user's payment methods"""
    methods = await PaymentMethod.find(PaymentMethod.user.id == user_id).to_list()
    return methods

@router.post("/{user_id}/payment-methods", response_model=PaymentMethodSchema, status_code=status.HTTP_201_CREATED)
async def add_payment_method(user_id: str, method: PaymentMethodCreate):
    """Add a payment method"""
    # ensure user exists
    user = await User.get(user_id)
    if not user:
         raise HTTPException(status_code=404, detail="User not found")

    db_method = PaymentMethod(
        user=user, 
        type=method.type,
        name=method.name,
        identifier=method.identifier,
        is_primary=method.is_primary,
        created_at=datetime.now(timezone.utc)
    )
    await db_method.insert()
    return db_method

@router.delete("/{user_id}/payment-methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(user_id: str, method_id: str):
    """Delete a payment method"""
    method = await PaymentMethod.find_one(PaymentMethod.id == method_id, PaymentMethod.user.id == user_id)
    
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    await method.delete()
    return None
