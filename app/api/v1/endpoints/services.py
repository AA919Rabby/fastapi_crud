import uuid
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.service import Service, ServiceReview, ServiceOrder
from app.models.extensions import UserProfile
from app.schemas.service import (
    ServiceResponse,
    ServiceDetailResponse,
    PaginatedServiceResponse,
    ReviewCreate,
    ReviewResponse,
    OrderCreate,
    OrderResponse,
    AIChatRequest,
    AIChatResponse
)
from app.core.sslcommerz import ssl_client
from app.core.ws_manager import ws_manager
from app.core.gemini_assistant import run_gemini_service_assistant

router = APIRouter()

# Helper to enrich review with user's full name & profile picture
def format_review_with_user(db: Session, review: ServiceReview) -> dict:
    user = db.query(User).filter(User.id == review.user_id).first()
    profile = db.query(UserProfile).filter(UserProfile.user_id == review.user_id).first() if user else None

    # Determine reviewer name
    user_name = "Anonymous User"
    if profile and profile.full_name:
        user_name = profile.full_name
    elif user and (user.first_name or user.last_name):
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    elif user and user.email:
        user_name = user.email.split("@")[0]

    return {
        "id": review.id,
        "service_id": review.service_id,
        "user_id": review.user_id,
        "user_name": user_name,
        "user_profile_picture": profile.profile_picture_url if profile else None,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at
    }

# =====================================================================
# 1. SERVICES WITH FULL SEARCH, FILTERING, SORTING & PAGINATION
# =====================================================================

@router.get("/", response_model=PaginatedServiceResponse)
def get_all_services(
    search: Optional[str] = Query(None, description="Free text search on title, description, and location area"),
    category: Optional[str] = Query(None, description="Filter by category ('hair cut', 'makeup beauty', 'ac repair', 'house painting')"),
    area: Optional[str] = Query(None, description="Filter by area (e.g., Gulshan, Banani, Dhanmondi, Mirpur)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price in BDT"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price in BDT"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter (0 to 5)"),
    available_only: Optional[bool] = Query(False, description="Filter only services with stock > 0"),
    sort_by: Optional[str] = Query("id", description="Sort by: 'price_asc', 'price_desc', 'rating_desc', 'newest'"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    query = db.query(Service)

    if search:
        search_filter = or_(
            Service.title.ilike(f"%{search}%"),
            Service.description.ilike(f"%{search}%"),
            Service.location_area.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if category:
        query = query.filter(Service.category.ilike(f"%{category}%"))

    if area:
        query = query.filter(Service.location_area.ilike(f"%{area}%"))

    if min_price is not None:
        query = query.filter(Service.price_bdt >= min_price)
    if max_price is not None:
        query = query.filter(Service.price_bdt <= max_price)

    if min_rating is not None:
        query = query.filter(Service.rating >= min_rating)

    if available_only:
        query = query.filter(Service.stock > 0, Service.is_available == True)

    if sort_by == "price_asc":
        query = query.order_by(asc(Service.price_bdt))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Service.price_bdt))
    elif sort_by == "rating_desc":
        query = query.order_by(desc(Service.rating))
    elif sort_by == "newest":
        query = query.order_by(desc(Service.id))
    else:
        query = query.order_by(asc(Service.id))

    total_items = query.count()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 1
    offset = (page - 1) * limit

    items = query.offset(offset).limit(limit).all()

    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "items": items
    }

@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Service.category).distinct().all()
    return [c[0] for c in categories]

@router.get("/{service_id}", response_model=ServiceDetailResponse)
def get_service_details(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")

    # Fetch reviews with user details
    reviews = db.query(ServiceReview).filter(ServiceReview.service_id == service.id).order_by(desc(ServiceReview.id)).all()
    formatted_reviews = [format_review_with_user(db, r) for r in reviews]

    service_dict = {
        "id": service.id,
        "title": service.title,
        "category": service.category,
        "description": service.description,
        "price_bdt": service.price_bdt,
        "stock": service.stock,
        "image_url": service.image_url,
        "location_area": service.location_area,
        "service_persons": service.service_persons,
        "is_available": service.is_available,
        "rating": service.rating,
        "total_reviews": service.total_reviews,
        "reviews": formatted_reviews
    }
    return service_dict

# =====================================================================
# 2. REVIEWS: ADD & GET REVIEWS FOR A SERVICE
# =====================================================================

@router.post("/reviews", response_model=ReviewResponse)
async def add_service_review(
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(Service.id == review_in.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")

    review = ServiceReview(
        service_id=review_in.service_id,
        user_id=current_user.id,
        rating=review_in.rating,
        comment=review_in.comment
    )
    db.add(review)

    # Recalculate average rating
    all_reviews = db.query(ServiceReview).filter(ServiceReview.service_id == service.id).all()
    total_reviews_count = len(all_reviews) + 1
    total_rating_sum = sum([r.rating for r in all_reviews]) + review_in.rating
    new_avg_rating = round(total_rating_sum / total_reviews_count, 1)

    service.rating = new_avg_rating
    service.total_reviews = total_reviews_count

    db.commit()
    db.refresh(review)

    # Broadcast review event
    await ws_manager.broadcast({
        "event": "NEW_REVIEW",
        "service_id": service.id,
        "new_rating": service.rating,
        "total_reviews": service.total_reviews
    })

    return format_review_with_user(db, review)

@router.get("/{service_id}/reviews", response_model=List[ReviewResponse])
def get_service_reviews(
    service_id: int,
    db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")

    reviews = db.query(ServiceReview).filter(ServiceReview.service_id == service_id).order_by(desc(ServiceReview.id)).all()
    return [format_review_with_user(db, r) for r in reviews]

# =====================================================================
# 3. SERVICE ORDERS & SSLCOMMERZ CHECKOUT
# =====================================================================

@router.post("/order", response_model=OrderResponse)
async def create_service_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(Service.id == order_in.service_id).first()
    if not service or not service.is_available:
        raise HTTPException(status_code=400, detail="Service is currently unavailable.")

    if service.stock <= 0:
        raise HTTPException(status_code=400, detail="This service is out of available slots.")

    service.stock -= 1
    if service.stock == 0:
        service.is_available = False

    tran_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"

    order = ServiceOrder(
        tran_id=tran_id,
        user_id=current_user.id,
        service_id=service.id,
        service_address=order_in.service_address,
        customer_phone=order_in.customer_phone,
        total_amount=service.price_bdt,
        status="PENDING",
        payment_status="UNPAID"
    )

    ssl_res = await ssl_client.init_payment(
        tran_id=tran_id,
        total_amount=service.price_bdt,
        cus_name=current_user.email.split("@")[0],
        cus_email=current_user.email,
        cus_phone=order_in.customer_phone,
        cus_address=order_in.service_address,
        service_title=service.title
    )

    if ssl_res.get("status") == "SUCCESS":
        order.payment_session_url = ssl_res.get("GatewayPageURL")

    db.add(order)
    db.commit()
    db.refresh(order)

    await ws_manager.broadcast({
        "event": "NEW_ORDER",
        "order_id": order.id,
        "service_id": service.id,
        "new_stock": service.stock,
        "status": order.status
    })

    return order

@router.post("/order/{order_id}/cancel", response_model=OrderResponse)
async def cancel_service_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(ServiceOrder).filter(
        ServiceOrder.id == order_id,
        ServiceOrder.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel order that is already '{order.status}'.")

    order.status = "CANCELLED"
    if order.payment_status != "PAID":
        order.payment_status = "CANCELLED"

    service = db.query(Service).filter(Service.id == order.service_id).first()
    if service:
        service.stock += 1
        service.is_available = True

    db.commit()
    db.refresh(order)

    await ws_manager.broadcast({
        "event": "ORDER_STATUS_CHANGED",
        "order_id": order.id,
        "status": "CANCELLED",
        "service_id": service.id if service else None,
        "new_stock": service.stock if service else None
    })

    return order

@router.delete("/order/{order_id}", response_model=dict)
def delete_service_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(ServiceOrder).filter(
        ServiceOrder.id == order_id,
        ServiceOrder.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.status == "PENDING":
        service = db.query(Service).filter(Service.id == order.service_id).first()
        if service:
            service.stock += 1
            service.is_available = True

    db.delete(order)
    db.commit()

    return {"message": "Order removed successfully."}

@router.get("/order/history", response_model=List[OrderResponse])
def get_service_history(
    status: Optional[str] = Query(None, description="Filter history by status"),
    exclude_cancelled: bool = Query(False, description="Set to true to hide cancelled orders"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ServiceOrder).filter(ServiceOrder.user_id == current_user.id)

    if status:
        query = query.filter(ServiceOrder.status == status.upper())

    if exclude_cancelled:
        query = query.filter(ServiceOrder.status != "CANCELLED")

    orders = query.order_by(ServiceOrder.id.desc()).all()

    # Attach formatted date string (e.g., "2026-09-29")
    for order in orders:
        if order.created_at:
            order.date = order.created_at.strftime("%Y-%m-%d")
        else:
            order.date = "N/A"

    return orders

# =====================================================================
# 4. SSLCOMMERZ WEBHOOK & USER REDIRECTS
# =====================================================================

@router.post("/payment/success")
async def payment_success(
    tran_id: str = Form(...),
    val_id: str = Form(...),
    db: Session = Depends(get_db)
):
    order = db.query(ServiceOrder).filter(ServiceOrder.tran_id == tran_id).first()
    if order:
        order.payment_status = "PAID"
        order.status = "PROCESSING"
        db.commit()
        await ws_manager.broadcast({
            "event": "PAYMENT_UPDATE",
            "order_id": order.id,
            "payment_status": "PAID",
            "status": "PROCESSING"
        })
    return HTMLResponse(content=f"<h2>Payment Successful for {tran_id}. You may close this window.</h2>")

@router.post("/payment/fail")
async def payment_fail(tran_id: str = Form(...), db: Session = Depends(get_db)):
    order = db.query(ServiceOrder).filter(ServiceOrder.tran_id == tran_id).first()
    if order:
        order.payment_status = "FAILED"
        db.commit()
        await ws_manager.broadcast({
            "event": "PAYMENT_UPDATE",
            "order_id": order.id,
            "payment_status": "FAILED"
        })
    return HTMLResponse(content=f"<h2>Payment Failed for {tran_id}.</h2>")

@router.post("/payment/cancel")
async def payment_cancel(tran_id: str = Form(...), db: Session = Depends(get_db)):
    order = db.query(ServiceOrder).filter(ServiceOrder.tran_id == tran_id).first()
    if order:
        order.payment_status = "CANCELLED"
        db.commit()
        await ws_manager.broadcast({
            "event": "PAYMENT_UPDATE",
            "order_id": order.id,
            "payment_status": "CANCELLED"
        })
    return HTMLResponse(content=f"<h2>Payment Cancelled.</h2>")

# =====================================================================
# 5. GEMINI AI ASSISTANT
# =====================================================================

@router.post("/ai-assistant", response_model=AIChatResponse)
def chat_with_gemini_assistant(data: AIChatRequest, db: Session = Depends(get_db)):
    services = db.query(Service).filter(Service.is_available == True).all()
    service_dicts = [
        {
            "id": s.id,
            "title": s.title,
            "category": s.category,
            "price_bdt": s.price_bdt,
            "stock": s.stock,
            "service_persons": s.service_persons,
            "location_area": s.location_area
        }
        for s in services
    ]
    return run_gemini_service_assistant(data.message, service_dicts)


# ----------------- MARK ORDER AS COMPLETED -----------------

@router.post("/order/{order_id}/complete", response_model=OrderResponse)
async def complete_service_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(ServiceOrder).filter(
        ServiceOrder.id == order_id,
        ServiceOrder.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cannot complete a cancelled order.")

    # 1. Update status to COMPLETED
    order.status = "COMPLETED"
    db.commit()
    db.refresh(order)

    # 2. Broadcast live status change to WebSocket
    await ws_manager.broadcast({
        "event": "ORDER_STATUS_CHANGED",
        "order_id": order.id,
        "status": "COMPLETED"
    })

    return order


# =====================================================================
# 6. LIVE WEBSOCKET
# =====================================================================

@router.websocket("/ws")
async def service_websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)