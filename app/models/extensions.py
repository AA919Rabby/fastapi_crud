from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    profile_picture_url = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("app.models.user.User")


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fcm_token = Column(String, unique=True, index=True, nullable=False)
    device_type = Column(String, default="android")  # android, ios, web
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("app.models.user.User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(String, default="GENERAL")  # ORDER, PAYMENT, PROFILE, SYSTEM
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("app.models.user.User")


class ServiceSlot(Base):
    __tablename__ = "service_slots"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    slot_date = Column(Date, index=True, nullable=False)
    start_time = Column(String, nullable=False)  # e.g., "10:00 AM"
    end_time = Column(String, nullable=False)    # e.g., "11:30 AM"
    is_booked = Column(Boolean, default=False)

    service = relationship("app.models.service.Service")