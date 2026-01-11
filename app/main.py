import os
import time
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    verify_password,
    verify_token,
)
from .metrics import record_http_request
from .models import (
    ChangePassword,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserLogin,
    UserProfileUpdate,
    UserResponse,
)

# Check if we should use SQL database or in-memory
USE_SQL_DB = os.getenv("DATABASE_URL") is not None

if USE_SQL_DB:
    from .database_sql import (
        create_user,
        get_user_by_email,
        get_user_by_id,
        update_user_password,
        update_user_profile,
    )
    from .db_config import get_db, init_db

    # Initialize database tables
    init_db()
else:
    from .database import (
        create_user,
        get_user_by_email,
        get_user_by_id,
        update_user_password,
    )

app = FastAPI(
    title="Swappo Authentication Service",
    description="""## Authentication & User Management API

**Swappo Auth Service** provides secure user authentication and profile management.

### Features
- 🔐 User registration and login
- 🎫 JWT token-based authentication (access + refresh tokens)
- 👤 User profile management
- 🔑 Password management and updates

### Authentication Flow
1. Register a new user at `/api/v1/register`
2. Login to receive access and refresh tokens at `/api/v1/login`
3. Include `Authorization: Bearer <access_token>` header in authenticated requests
4. Refresh expired tokens at `/api/v1/refresh`

### Security
- Passwords are hashed using bcrypt
- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days
    """,
    version="1.0.0",
    contact={
        "name": "Swappo API Support",
        "url": "https://swappo.art",
        "email": "api@swappo.art",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {"name": "Health", "description": "Service health and status endpoints"},
        {
            "name": "Authentication",
            "description": "User login, registration, and token management",
        },
        {"name": "User Profile", "description": "User profile management and updates"},
    ],
)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# Middleware to track HTTP request metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    record_http_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=duration,
    )

    return response


# CORS middleware for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your mobile app domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Conditional database dependency
def get_db_dependency():
    """Returns database session if SQL DB is enabled, otherwise None"""
    if USE_SQL_DB:
        return Depends(get_db)
    return None


@app.get("/")
async def read_root():
    return {
        "message": "Authentication Microservice API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "register": "/api/v1/auth/register",
            "login": "/api/v1/auth/login",
            "refresh": "/api/v1/auth/refresh",
            "me": "/api/v1/auth/me",
            "change-password": "/api/v1/auth/change-password",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post(
    "/api/v1/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db) if USE_SQL_DB else Depends(lambda: None),
):
    """Register a new user."""
    # Check if user already exists
    existing_user = (
        get_user_by_email(db, user_data.email)
        if USE_SQL_DB
        else get_user_by_email(user_data.email)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    if USE_SQL_DB:
        user = create_user(
            db,
            user_data.email,
            user_data.username,
            hashed_password,
            user_data.full_name,
        )
    else:
        user = create_user(
            user_data.email, user_data.username, hashed_password, user_data.full_name
        )

    return UserResponse(**user)


@app.post("/api/v1/auth/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db) if USE_SQL_DB else Depends(lambda: None),
):
    """Login user and return access and refresh tokens."""
    # Get user from database
    user = (
        get_user_by_email(db, user_credentials.email)
        if USE_SQL_DB
        else get_user_by_email(user_credentials.email)
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        data={"sub": user["id"], "email": user["email"]}
    )

    return Token(access_token=access_token, refresh_token=refresh_token)


@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db) if USE_SQL_DB else Depends(lambda: None),
):
    """Refresh access token using refresh token."""
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, "refresh")
    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Verify user still exists and is active
    user = get_user_by_id(db, user_id) if USE_SQL_DB else get_user_by_id(user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
        )

    # Create new tokens
    access_token = create_access_token(
        data={"sub": user_id, "email": email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    new_refresh_token = create_refresh_token(data={"sub": user_id, "email": email})

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) if USE_SQL_DB else Depends(lambda: None),
):
    """Get current authenticated user information."""
    user = (
        get_user_by_id(db, current_user["user_id"])
        if USE_SQL_DB
        else get_user_by_id(current_user["user_id"])
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse(**user)


@app.post("/api/v1/auth/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) if USE_SQL_DB else Depends(lambda: None),
):
    """Change user password."""
    user = (
        get_user_by_id(db, current_user["user_id"])
        if USE_SQL_DB
        else get_user_by_id(current_user["user_id"])
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify old password
    if not verify_password(password_data.old_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )

    # Update password
    new_hashed_password = get_password_hash(password_data.new_password)
    if USE_SQL_DB:
        update_user_password(db, current_user["user_id"], new_hashed_password)
    else:
        update_user_password(current_user["user_id"], new_hashed_password)

    return {"message": "Password changed successfully"}


@app.put("/api/v1/auth/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) if USE_SQL_DB else Depends(lambda: None),
):
    """Update user profile information including shipping address."""
    if not USE_SQL_DB:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Profile updates require SQL database",
        )

    # Update user profile
    updated_user = update_user_profile(
        db,
        current_user["user_id"],
        full_name=profile_data.full_name,
        phone=profile_data.phone,
        address_line1=profile_data.address_line1,
        address_line2=profile_data.address_line2,
        city=profile_data.city,
        state=profile_data.state,
        postal_code=profile_data.postal_code,
        country=profile_data.country,
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse(**updated_user)


@app.post("/api/v1/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (client should delete tokens)."""
    # In a production environment with token blacklisting, add token to blacklist here
    return {"message": "Logged out successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
