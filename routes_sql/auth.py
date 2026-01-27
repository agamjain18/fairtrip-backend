from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from database_sql import get_db, User, OTP
from schemas_sql import Token, LoginRequest, UserCreate, User as UserSchema, ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest, SocialLoginRequest
import os

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "help.agam.online@gmail.com"
# The user should set this environment variable 'EMAIL_APP_PASSWORD' with a Gmail App Password
SENDER_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "vjkp dmsb fvbw pfpt") # vjkp dmsb fvbw pfpt is a placeholder, REPLACE IT

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

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

def send_otp_email(email: str, otp: str):
    """Send OTP via Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Your FairShare OTP Code"

        body = f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #4A9EFF;">FairShare Verification</h2>
                    <p>Hello,</p>
                    <p>You requested a password reset. Use the following OTP code to verify your account:</p>
                    <div style="background: #f4f7f6; padding: 15px; text-align: center; border-radius: 5px;">
                        <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #1E3A5F;">{otp}</span>
                    </div>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #eee;" />
                    <p style="font-size: 12px; color: #888;">FairShare - Travel together, split easily.</p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_welcome_email(email: str, name: str):
    """Send Welcome Email via Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Welcome to FairShare!"

        body = f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #4A9EFF;">Welcome to FairShare, {name}!</h2>
                    <p>We are thrilled to have you on board.</p>
                    <p>FairShare is your ultimate travel companion for splitting expenses, planning itineraries, and keeping memories safe.</p>
                    
                    <h3>Getting Started:</h3>
                    <ul>
                        <li><b>Plan Trips:</b> Create itineraries with real-time collaboration.</li>
                        <li><b>Split Expenses:</b> Add expenses and let our AI handle the math.</li>
                        <li><b>Secure Docs:</b> Keep your travel documents safe with biometric protection.</li>
                    </ul>
                    
                    <p>If you have any questions or need assistance, feel free to reply to this email or contact us at {SENDER_EMAIL}.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee;" />
                    <p style="font-size: 12px; color: #888;">FairShare - Travel together, split easily.</p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, email, text)
        server.quit()
        print(f"Welcome email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

def get_current_user_sql(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user_email = db.query(User).filter(User.email == user.email).first()
    existing_user_username = db.query(User).filter(User.username == user.username).first()
    
    if existing_user_email or existing_user_username:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
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

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email/username and password"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json", response_model=Token)
def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login with JSON payload"""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        user = db.query(User).filter(User.username == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Send OTP to user's email for password reset"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # We return 200 even if user not found to prevent user enumeration
        return {"message": "If this email is registered, an OTP has been sent."}

    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    # Save OTP to DB
    new_otp = OTP(email=request.email, otp_code=otp_code, expires_at=expires_at)
    db.add(new_otp)
    db.commit()

    # Send email in background
    background_tasks.add_task(send_otp_email, request.email, otp_code)

    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify if the OTP is correct and not expired"""
    otp_record = db.query(OTP).filter(
        OTP.email == request.email,
        OTP.otp_code == request.otp_code,
        OTP.expires_at > datetime.now(timezone.utc)
    ).order_by(OTP.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    return {"message": "OTP verified successfully"}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password after OTP verification"""
    # 1. Verify OTP again for security
    otp_record = db.query(OTP).filter(
        OTP.email == request.email,
        OTP.otp_code == request.otp_code,
        OTP.expires_at > datetime.now(timezone.utc)
    ).order_by(OTP.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid verification code session")

    # 2. Update password
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(request.new_password)
    user.updated_at = datetime.now(timezone.utc)
    
    # 3. Clean up OTP (optional but recommended)
    db.delete(otp_record)
    
    db.commit()
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_current_user_sql)):
    """Get current authenticated user"""
    return current_user

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user_sql)):
    """Logout (client should delete token)"""
    return {"message": "Successfully logged out"}

@router.get("/sync-check")
def sync_check(current_user: User = Depends(get_current_user_sql)):
    """Get the current data version of the user for real-time sync"""
    return {"version": current_user.data_version or 1}

@router.post("/social-login", response_model=Token)
def social_login(social_data: SocialLoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
    user = db.query(User).filter(User.email == social_data.email).first()
    
    if user:
        # User already exists - just login
        print(f"Existing user login: {social_data.email} via {social_data.provider}")
    else:
        # Check if username already exists to avoid duplicates
        base_username = social_data.email.split('@')[0]
        username = f"{base_username}_{social_data.provider}"
        existing_username = db.query(User).filter(User.username == username).first()
        
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
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"New user created: {social_data.email} via {social_data.provider}")
        except Exception as e:
            db.rollback()
            print(f"Error creating user: {str(e)}")
            # Try to find user again in case of race condition
            user = db.query(User).filter(User.email == social_data.email).first()
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
    
    is_new_user = False
    
    # Check if we just created the user (created_at is very recent, e.g., within last 10 seconds)
    # Or strict check: if the user object was just added to session. 
    # But since we commit and refresh, we can check a flag or infer from logs/context.
    # Simpler: we printed "New user created" or "Existing user login".
    # Let's enforce the logic:
    
    # Re-check if user was created just now.
    # The variable user is fresh.
    time_diff = datetime.now(timezone.utc) - user.created_at
    if time_diff.total_seconds() < 10: # Assuming it was created in this request
        is_new_user = True
        # Send welcome email
        background_tasks.add_task(send_welcome_email, user.email, user.full_name)
    
    return {"access_token": access_token, "token_type": "bearer", "is_new_user": is_new_user}
