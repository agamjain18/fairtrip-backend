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
import random
import string

def generate_friend_code(k=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

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
SENDER_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "tabm iwxi szlf rdap") # vjkp dmsb fvbw pfpt is a placeholder, REPLACE IT

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
        msg['From'] = f"FairTrip <{SENDER_EMAIL}>"
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
        msg['From'] = f"FairTrip <{SENDER_EMAIL}>"
        msg['To'] = email
        msg['Subject'] = "Welcome to FairShare!"

        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to FairTrip</title>
            <style>
                body {{
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    background-color: #f4f7f6;
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #4A9EFF 0%, #00C896 100%);
                    padding: 40px 20px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                    letter-spacing: 1px;
                }}
                .hero-image {{
                    width: 100%;
                    height: 200px;
                    object-fit: cover;
                    background-image: url('https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=600&q=80');
                    background-size: cover;
                    background-position: center;
                }}
                .content {{
                    padding: 30px;
                    color: #333333;
                    line-height: 1.6;
                }}
                .greeting {{
                    font-size: 24px;
                    font-weight: 600;
                    color: #1E3A5F;
                    margin-bottom: 20px;
                }}
                .feature-list {{
                    list-style: none;
                    padding: 0;
                    margin: 30px 0;
                }}
                .feature-item {{
                    display: flex;
                    align-items: flex-start;
                    margin-bottom: 20px;
                }}
                .feature-icon {{
                    font-size: 24px;
                    margin-right: 15px;
                    min-width: 30px;
                    text-align: center;
                }}
                .cta-button {{
                    display: block;
                    width: 200px;
                    margin: 30px auto;
                    padding: 15px 0;
                    background-color: #4A9EFF;
                    color: white !important;
                    text-decoration: none;
                    text-align: center;
                    border-radius: 30px;
                    font-weight: bold;
                    font-size: 16px;
                    box-shadow: 0 4px 15px rgba(74, 158, 255, 0.3);
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #888888;
                    border-top: 1px solid #eeeeee;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="hero-image"></div>
                <!-- fallback header if image fails loading or for styling -->
                <div class="header">
                    <h1>FairTrip</h1>
                </div>
                
                <div class="content">
                    <div class="greeting">Welcome to the Family, {name}! 🌍</div>
                    
                    <p>We are absolutely thrilled to have you on board. FairTrip isn't just an app; it's your new travel companion that ensures every journey is memorable and every expense is fair.</p>
                    
                    <ul class="feature-list">
                        <li class="feature-item">
                            <span class="feature-icon">✈️</span>
                            <div>
                                <strong>Plan Seamlessly</strong><br>
                                Create detailed itineraries and collaborate with your travel squad in real-time.
                            </div>
                        </li>
                        <li class="feature-item">
                            <span class="feature-icon">💸</span>
                            <div>
                                <strong>Split Expenses, Stress-Free</strong><br>
                                Log costs as you go. Our AI handles the math so you can focus on the fun.
                            </div>
                        </li>
                        <li class="feature-item">
                            <span class="feature-icon">🔒</span>
                            <div>
                                <strong>Secure Your Documents</strong><br>
                                Keep passports and tickets safe in your biometric-secured vault.
                            </div>
                        </li>
                    </ul>

                    <a href="https://agamjain.online" class="cta-button">Start Planning Now</a>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        Need help? Just reply to this email.<br>
                        We're here for you 24/7.
                    </p>
                </div>
                
                <div class="footer">
                    &copy; 2026 FairTrip Inc. • Travel Together, Split Easily<br>
                    <a href="#" style="color: #4A9EFF; text-decoration: none;">Privacy Policy</a> • <a href="#" style="color: #4A9EFF; text-decoration: none;">Unsubscribe</a>
                </div>
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
        friend_code=generate_friend_code(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        is_verified=True # Auto-verify for now to unblock testing/development
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Generate and send OTP for verification
    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    new_otp = OTP(email=user.email, otp_code=otp_code, expires_at=expires_at)
    db.add(new_otp)
    db.commit()
    
    # Send verification email (using background tasks if available)
    try:
        send_otp_email(user.email, otp_code)
    except:
        pass

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
    
    if not getattr(user, 'is_verified', True): # Fallback to True for safety if column missing
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified. Please verify your email."
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
    
    if not getattr(user, 'is_verified', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified. Please verify your email."
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
    db.commit()
    return {"message": "Password reset successfully"}

@router.post("/resend-verification")
def resend_verification(request: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Resend verification OTP if the user is unverified"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_verified:
        return {"message": "User is already verified"}

    # Generate new OTP
    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Store new OTP
    new_otp = OTP(email=user.email, otp_code=otp_code, expires_at=expires_at)
    db.add(new_otp)
    db.commit()
    
    # Send email
    background_tasks.add_task(send_otp_email, user.email, otp_code)
    
    return {"message": "Verification code sent"}

@router.post("/verify-registration")
def verify_registration(request: VerifyOTPRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Verify registration OTP and mark user as verified"""
    otp_record = db.query(OTP).filter(
        OTP.email == request.email,
        OTP.otp_code == request.otp_code,
        OTP.expires_at > datetime.now(timezone.utc)
    ).order_by(OTP.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.delete(otp_record)
    db.commit()

    # Send welcome email
    background_tasks.add_task(send_welcome_email, user.email, user.full_name)

    # Create access token immediately so they are logged in
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "message": "Account verified successfully"
    }

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
    if social_data.provider not in ["google", "apple", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'google', 'apple', or 'github'"
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
            friend_code=generate_friend_code(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_verified=True # Social logins are pre-verified
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"New user created: {social_data.email} via {social_data.provider}")
        except Exception as e:
            db.rollback()
            import traceback
            traceback.print_exc()
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
    
    # Ensure user.created_at is timezone-aware for comparison, or fallback
    created_at = user.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
        
    time_diff = datetime.now(timezone.utc) - created_at
    
    if time_diff.total_seconds() < 10: # Assuming it was created in this request
        is_new_user = True
        # Send welcome email
        background_tasks.add_task(send_welcome_email, user.email, user.full_name)
    
    return {"access_token": access_token, "token_type": "bearer", "is_new_user": is_new_user}
