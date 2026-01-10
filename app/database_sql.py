import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from .db_config import UserDB


def get_user_by_email(db: Session, email: str) -> Optional[dict]:
    """Get user by email."""
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if user:
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "full_name": user.full_name,
            "created_at": user.created_at,
            "is_active": user.is_active,
            "phone": user.phone,
            "address_line1": user.address_line1,
            "address_line2": user.address_line2,
            "city": user.city,
            "state": user.state,
            "postal_code": user.postal_code,
            "country": user.country,
        }
    return None


def get_user_by_id(db: Session, user_id: str) -> Optional[dict]:
    """Get user by ID."""
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user:
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "full_name": user.full_name,
            "created_at": user.created_at,
            "is_active": user.is_active,
            "phone": user.phone,
            "address_line1": user.address_line1,
            "address_line2": user.address_line2,
            "city": user.city,
            "state": user.state,
            "postal_code": user.postal_code,
            "country": user.country,
        }
    return None


def create_user(
    db: Session,
    email: str,
    username: str,
    hashed_password: str,
    full_name: Optional[str] = None,
) -> dict:
    """Create a new user."""
    user_id = str(uuid.uuid4())
    db_user = UserDB(
        id=user_id,
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        created_at=datetime.utcnow(),
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "id": db_user.id,
        "email": db_user.email,
        "username": db_user.username,
        "hashed_password": db_user.hashed_password,
        "full_name": db_user.full_name,
        "created_at": db_user.created_at,
        "is_active": db_user.is_active,
        "phone": db_user.phone,
        "address_line1": db_user.address_line1,
        "address_line2": db_user.address_line2,
        "city": db_user.city,
        "state": db_user.state,
        "postal_code": db_user.postal_code,
        "country": db_user.country,
    }


def update_user_profile(
    db: Session,
    user_id: str,
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None,
) -> Optional[dict]:
    """Update user profile information."""
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        return None

    # Update fields if provided
    if full_name is not None:
        user.full_name = full_name
    if phone is not None:
        user.phone = phone
    if address_line1 is not None:
        user.address_line1 = address_line1
    if address_line2 is not None:
        user.address_line2 = address_line2
    if city is not None:
        user.city = city
    if state is not None:
        user.state = state
    if postal_code is not None:
        user.postal_code = postal_code
    if country is not None:
        user.country = country

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "hashed_password": user.hashed_password,
        "full_name": user.full_name,
        "created_at": user.created_at,
        "is_active": user.is_active,
        "phone": user.phone,
        "address_line1": user.address_line1,
        "address_line2": user.address_line2,
        "city": user.city,
        "state": user.state,
        "postal_code": user.postal_code,
        "country": user.country,
    }


def update_user_password(db: Session, user_id: str, hashed_password: str) -> bool:
    """Update user password."""
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user:
        user.hashed_password = hashed_password
        db.commit()
        return True
    return False


def deactivate_user(db: Session, user_id: str) -> bool:
    """Deactivate user account."""
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
        return True
    return False
