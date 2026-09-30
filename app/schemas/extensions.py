from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

# ==========================================
# 1. PROFILE SCHEMAS
# ==========================================

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_picture_url: Optional[str] = None
    address: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    profile_picture_url: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    total_completed_services: int = 0

    class Config:
        from_attributes = True

# ==========================================
# 2. NOTIFICATIONS & FCM SCHEMAS
# ==========================================

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

# ==========================================
# 3. SLOTS SCHEMAS
# ==========================================

class SlotResponse(BaseModel):
    id: int
    service_id: int
    slot_date: date
    start_time: str
    end_time: str
    is_booked: bool

    class Config:
        from_attributes = True

# ==========================================
# 4. PAYMENT INITIATE SCHEMAS
# ==========================================

class PaymentInitiateRequest(BaseModel):
    order_id: int

class PaymentInitiateResponse(BaseModel):
    tran_id: str
    payment_url: str