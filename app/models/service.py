from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)  # hair cut, makeup beauty, ac repair, house painting
    description = Column(Text, nullable=False)
    price_bdt = Column(Float, nullable=False)
    stock = Column(Integer, default=10, nullable=False)  # e.g., 14, 8 slots available
    image_url = Column(String, nullable=False)
    location_area = Column(String, nullable=False)  # e.g., Gulshan, Banani, Dhanmondi, Mirpur
    service_persons = Column(Integer, default=1, nullable=False)  # how many people will come
    is_available = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)  # Initialized to 0
    total_reviews = Column(Integer, default=0)  # Initialized to 0

    reviews = relationship("ServiceReview", back_populates="service", cascade="all, delete-orphan")
    orders = relationship("ServiceOrder", back_populates="service")


class ServiceReview(Base):
    __tablename__ = "service_reviews"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    service = relationship("Service", back_populates="reviews")
    user = relationship("app.models.user.User")


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, index=True)
    tran_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    service_address = Column(Text, nullable=False)
    customer_phone = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, PROCESSING, COMPLETED, CANCELLED
    payment_status = Column(String, default="UNPAID")  # UNPAID, PAID, FAILED, CANCELLED
    payment_session_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    service = relationship("Service", back_populates="orders")
    user = relationship("app.models.user.User")