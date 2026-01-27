from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from utils.email_service import send_friend_added_email
from sqlalchemy.orm import Session
from typing import List
import bcrypt
from database_sql import get_db, User, Friendship, UserSession, PaymentMethod
from schemas_sql import User as UserSchema, UserCreate, UserUpdate, PaymentMethod as PaymentMethodSchema, PaymentMethodCreate
from datetime import datetime, timezone
from routes_sql.auth import get_current_user_sql

router = APIRouter(prefix="/users", tags=["users"])

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

@router.get("/", response_model=List[UserSchema])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/search", response_model=List[UserSchema])
def search_users(q: str, db: Session = Depends(get_db)):
    """Search users by username or email"""
    users = db.query(User).filter(
        (User.username.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).limit(20).all()
    return users

@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/friends", response_model=List[UserSchema])
def get_user_friends(user_id: int, db: Session = Depends(get_db)):
    """Get user's friends"""
    friendships = db.query(Friendship).filter(
        (Friendship.user_id == user_id) | (Friendship.friend_id == user_id),
        Friendship.status == "accepted"
    ).all()
    
    friend_ids = []
    for f in friendships:
        if f.user_id == user_id:
            friend_ids.append(f.friend_id)
        else:
            friend_ids.append(f.user_id)
            
    friends = db.query(User).filter(User.id.in_(friend_ids)).all()
    return friends

@router.post("/friends/{friend_id}/add")
def add_friend(friend_id: int, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user_sql), db: Session = Depends(get_db)):
    """Add a friend (mutual acceptance by default for simplicity)"""
    if friend_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot friend yourself")
    
    # Check if already friends
    existing = db.query(Friendship).filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if existing:
        if existing.status == "accepted":
            return {"message": "Already friends"}
        else:
            existing.status = "accepted"
            db.commit()
            return {"message": "Friendship accepted"}
            
    new_friendship = Friendship(
        user_id=current_user.id,
        friend_id=friend_id,
        status="accepted"
    )
    db.add(new_friendship)
    db.commit()
    
    # Notify friend
    friend_user = db.query(User).filter(User.id == friend_id).first()
    if friend_user and friend_user.email:
        background_tasks.add_task(send_friend_added_email, friend_user.email, current_user.full_name or current_user.username)
        
    return {"message": "Friend added successfully"}

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    existing_user_email = db.query(User).filter(User.email == user.email).first()
    existing_user_username = db.query(User).filter(User.username == user.username).first()
    
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
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update user details"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return None

@router.get("/{user_id}/sessions")
def get_user_sessions(user_id: int, db: Session = Depends(get_db)):
    """Get user's active sessions"""
    sessions = db.query(UserSession).filter(UserSession.user_id == user_id).all()
    return sessions

@router.post("/{user_id}/sessions/{session_id}/revoke")
def revoke_session(user_id: int, session_id: int, db: Session = Depends(get_db)):
    """Revoke a user session"""
    session = db.query(UserSession).filter(
        UserSession.id == session_id, 
        UserSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    db.commit()
    return {"message": "Session revoked successfully"}

@router.get("/{user_id}/payment-methods", response_model=List[PaymentMethodSchema])
def get_payment_methods(user_id: int, db: Session = Depends(get_db)):
    """Get user's payment methods"""
    methods = db.query(PaymentMethod).filter(PaymentMethod.user_id == user_id).all()
    return methods

@router.post("/{user_id}/payment-methods", response_model=PaymentMethodSchema, status_code=status.HTTP_201_CREATED)
def add_payment_method(user_id: int, method: PaymentMethodCreate, db: Session = Depends(get_db)):
    """Add a payment method"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
         raise HTTPException(status_code=404, detail="User not found")

    db_method = PaymentMethod(
        user_id=user_id, 
        type=method.type,
        name=method.name,
        identifier=method.identifier,
        is_primary=method.is_primary,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_method)
    db.commit()
    db.refresh(db_method)
    return db_method

@router.delete("/{user_id}/payment-methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(user_id: int, method_id: int, db: Session = Depends(get_db)):
    """Delete a payment method"""
    method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id, 
        PaymentMethod.user_id == user_id
    ).first()
    
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    db.delete(method)
    db.commit()
    return None
