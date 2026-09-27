from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

# Profile
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_picture_url: Optional[str] = None
    address: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str]
    phone_number: Optional[str]
    profile_picture_url: Optional[str]
    address: Optional[str]
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True

# FCM & Notifications
class FCMTokenCreate(BaseModel):
    fcm_token: str
    device_type: Optional[str] = "android"

class NotificationResponse(BaseModel):
    id: int
    title: str
    body: str
    notification_type: str
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Slots
class SlotResponse(BaseModel):
    id: int
    service_id: int
    slot_date: date
    start_time: str
    end_time: str
    is_booked: bool
    class Config:
        from_attributes = True

# Payment Initiate
class PaymentInitiateRequest(BaseModel):
    order_id: int

class PaymentInitiateResponse(BaseModel):
    tran_id: str
    payment_url: str