from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- REVIEWS SCHEMAS ---

class ReviewCreate(BaseModel):
    service_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: str

class ReviewResponse(BaseModel):
    id: int
    service_id: int
    user_id: int
    user_name: str
    user_profile_picture: Optional[str] = None
    rating: int
    comment: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- SERVICE SCHEMAS ---

class ServiceResponse(BaseModel):
    id: int
    title: str
    category: str
    description: str
    price_bdt: float
    stock: int
    image_url: str
    location_area: str
    service_persons: int
    is_available: bool
    rating: float
    total_reviews: int
    class Config:
        from_attributes = True

class ServiceDetailResponse(ServiceResponse):
    reviews: List[ReviewResponse] = []

# --- PAGINATION SCHEMA ---

class PaginatedServiceResponse(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    limit: int
    has_next: bool
    has_previous: bool
    items: List[ServiceResponse]

# --- ORDERS SCHEMAS ---

class OrderCreate(BaseModel):
    service_id: int
    service_address: str
    customer_phone: str

class OrderResponse(BaseModel):
    id: int
    tran_id: str
    service_id: int
    service_address: str
    customer_phone: str
    total_amount: float
    status: str
    payment_status: str
    payment_session_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# --- GEMINI AI ASSISTANT SCHEMAS ---

class AIChatRequest(BaseModel):
    message: str

class AIChatResponse(BaseModel):
    reply: str
    suggested_action: Optional[str] = None
    order_details: Optional[dict] = None