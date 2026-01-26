from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from database import User
from schemas import Token, LoginRequest, UserCreate, User as UserSchema
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])

import os

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Social Login Request Schema
class SocialLoginRequest(BaseModel):
    provider: str  # 'google' or 'apple'
    email: str
    display_name: str
    id_token: str

# Three-Factor Login Request Schema
class ThreeFactorLoginRequest(BaseModel):
    email: str
    phone: str
    password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Beanie Get
    user = await User.get(user_id)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user_email = await User.find_one(User.email == user.email)
    existing_user_username = await User.find_one(User.username == user.username)
    
    if existing_user_email or existing_user_username:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create new user
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

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email/username and password"""
    # Find user by email or username
    user = await User.find_one(User.email == form_data.username)
    if not user:
        user = await User.find_one(User.username == form_data.username)
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json", response_model=Token)
async def login_json(login_data: LoginRequest):
    """Login with JSON payload"""
    user = await User.find_one(User.email == login_data.email)
    if not user:
        user = await User.find_one(User.username == login_data.email)
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-three-factor", response_model=Token)
async def login_three_factor(login_data: ThreeFactorLoginRequest):
    """Login with three-factor authentication: Email, Phone, Password"""
    # Validate email is provided
    if not login_data.email or not login_data.email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    # Validate phone is provided
    if not login_data.phone or not login_data.phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required"
        )
    
    # Validate password is provided
    if not login_data.password or not login_data.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    # Find user by email
    user = await User.find_one(User.email == login_data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not found",
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    
    # Verify phone number matches
    if user.phone != login_data.phone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phone number does not match our records",
        )
    
    # All three factors verified - create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    print(f"Three-factor login successful for: {user.email}")
    
    return {"access_token": access_token, "token_type": "bearer"}
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout (client should delete token)"""
    return {"message": "Successfully logged out"}
@router.post("/social-login", response_model=Token)
async def social_login(social_data: SocialLoginRequest):
    """Login/Register with Google or Apple"""
    import uuid
    
    # Validate provider
    if social_data.provider not in ["google", "apple"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'google' or 'apple'"
        )
    
    # Validate email is provided
    if not social_data.email or not social_data.email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required for social login"
        )
    
    # Check if user already exists by email (primary check)
    user = await User.find_one(User.email == social_data.email)
    
    if user:
        # User already exists - just login (return token without creating new account)
        print(f"Existing user login: {social_data.email} via {social_data.provider}")
    else:
        # Check if username already exists to avoid duplicates
        base_username = social_data.email.split('@')[0]
        username = f"{base_username}_{social_data.provider}"
        existing_username = await User.find_one(User.username == username)
        
        # If username exists, add random suffix
        if existing_username:
            username = f"{base_username}_{social_data.provider}_{str(uuid.uuid4())[:8]}"
        
        # Create new user from social login data
        random_password = str(uuid.uuid4())
        
        user = User(
            email=social_data.email,
            username=username,
            full_name=social_data.display_name or social_data.email.split('@')[0],
            password_hash=hash_password(random_password),
            avatar_url=None,
            phone=None,
            bio=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        try:
            await user.create()
            print(f"New user created: {social_data.email} via {social_data.provider}")
        except Exception as e:
            # Handle race condition where user was created between check and create
            print(f"Error creating user: {str(e)}")
            user = await User.find_one(User.email == social_data.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create or find user account"
                )
    
    # Create access token for login
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    print(f"User {user.email} successfully authenticated via {social_data.provider}")
    
    return {"access_token": access_token, "token_type": "bearer"}