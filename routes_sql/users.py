import shutil
import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from utils.email_service import send_friend_added_email
from sqlalchemy.orm import Session
from typing import List
import bcrypt
from database_sql import get_db, User, Friendship, UserSession, PaymentMethod, increment_user_version
from .notifications import send_notification_sql
from schemas_sql import User as UserSchema, UserCreate, UserUpdate, PaymentMethod as PaymentMethodSchema, PaymentMethodCreate
from datetime import datetime, timezone
from routes_sql.auth import get_current_user_sql
import random
import string

def generate_friend_code(k=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

UPLOAD_DIRECTORY = "uploads"
PROFILE_PICS_DIR = os.path.join(UPLOAD_DIRECTORY, "profile_pics")

if not os.path.exists(PROFILE_PICS_DIR):
    os.makedirs(PROFILE_PICS_DIR, exist_ok=True)

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/upload-avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    """Upload/Update user avatar"""
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"avatar_{current_user.id}_{timestamp}_{file.filename}"
        file_path = os.path.join(PROFILE_PICS_DIR, filename)

        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate URL
        url = f"/static/profile_pics/{filename}"

        # Update user record
        current_user.avatar_url = url
        db.commit()
        db.refresh(current_user)
        
        # Real-time sync
        increment_user_version(db, current_user.id)

        return {"url": url, "message": "Avatar updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            
            # Real-time sync
            increment_user_version(db, current_user.id)
            increment_user_version(db, friend_id)
            
            return {"message": "Friendship accepted"}
            
    new_friendship = Friendship(
        user_id=current_user.id,
        friend_id=friend_id,
        status="accepted"
    )
    db.add(new_friendship)
    db.commit()
    
    # Real-time sync
    increment_user_version(db, current_user.id)
    increment_user_version(db, friend_id)
    
    # Notify friend
    friend_user = db.query(User).filter(User.id == friend_id).first()
    if friend_user:
        send_notification_sql(
            db,
            user_id=friend_id,
            title="New Friend Added",
            message=f"{current_user.full_name or current_user.username} added you as a friend!",
            notification_type="friend",
            action_url="/friends"
        )
        if friend_user.email:
            background_tasks.add_task(send_friend_added_email, friend_user.email, current_user.full_name or current_user.username)
        
    return {"message": "Friend added successfully"}

@router.post("/{user_id}/friends/add-by-code")
def add_friend_by_code(user_id: int, friend_code: str, db: Session = Depends(get_db)):
    """Add a friend by their unique friend code"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    target_user = db.query(User).filter(User.friend_code == friend_code).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Invalid Friend Code")
    
    if target_user.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
        
    # Check existing friendship
    existing = db.query(Friendship).filter(
        ((Friendship.user_id == user.id) & (Friendship.friend_id == target_user.id)) |
        ((Friendship.user_id == target_user.id) & (Friendship.friend_id == user.id))
    ).first()
    
    if existing:
        if existing.status == "accepted":
            return {"message": "Already friends"}
        else:
             existing.status = "accepted"
             # Regenerate target user code
             target_user.friend_code = generate_friend_code()
             db.commit()
             increment_user_version(db, user.id)
             increment_user_version(db, target_user.id)
             return {"message": "Friend added successfully"}

    # Create bi-directional friendship
    f1 = Friendship(user_id=user.id, friend_id=target_user.id, status="accepted")
    db.add(f1)
    
    # Regenerate target user code
    target_user.friend_code = generate_friend_code()
    
    db.commit()
    
    increment_user_version(db, user.id)
    increment_user_version(db, target_user.id)
    
    return {"message": "Friend added successfully. Friend code rotated."}

@router.post("/{user_id}/friend-code/regenerate")
def regenerate_friend_code(user_id: int, db: Session = Depends(get_db)):
    """Regenerate friend code"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
         
    user.friend_code = generate_friend_code()
    db.commit()
    db.refresh(user)
    
    increment_user_version(db, user.id)
    
    return {"friend_code": user.friend_code}

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
        friend_code=generate_friend_code(),
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
    
    # Real-time sync
    increment_user_version(db, user_id)
    return user

@router.put("/fcm-token")
def update_fcm_token(
    token: str,
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    """Update user's FCM token for push notifications"""
    current_user.fcm_token = token
    db.commit()
    return {"message": "FCM token updated successfully"}

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
