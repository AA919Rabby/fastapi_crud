import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.core.config import settings

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, is_active=True)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def update_user_password(db: Session, db_user: User, new_password: str):
    hashed_password = get_password_hash(new_password)
    db_user.hashed_password = hashed_password
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def generate_and_save_otp(db: Session, user: User) -> str:
    otp = "".join(random.choices(string.digits, k=6))
    user.reset_otp = otp
    user.reset_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    db.add(user)
    db.commit()
    db.refresh(user)
    return otp

def verify_only_otp(db: Session, user: User, otp: str) -> bool:
    """Verifies that the OTP matches and hasn't expired. If valid, consumes the OTP."""
    now = datetime.now(timezone.utc)
    if not user.reset_otp or user.reset_otp != otp:
        return False
    if user.reset_otp_expires_at is None or user.reset_otp_expires_at < now:
        return False

    # Consume the OTP so it cannot be reused
    user.reset_otp = None
    user.reset_otp_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return True