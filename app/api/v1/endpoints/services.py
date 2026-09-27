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

    # 1. Search filter across multiple fields
    if search:
        search_filter = or_(
            Service.title.ilike(f"%{search}%"),
            Service.description.ilike(f"%{search}%"),
            Service.location_area.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # 2. Filter by Category
    if category:
        query = query.filter(Service.category.ilike(f"%{category}%"))

    # 3. Filter by Location Area
    if area:
        query = query.filter(Service.location_area.ilike(f"%{area}%"))

    # 4. Filter by Price Range
    if min_price is not None:
        query = query.filter(Service.price_bdt >= min_price)
    if max_price is not None:
        query = query.filter(Service.price_bdt <= max_price)

    # 5. Filter by Minimum Rating
    if min_rating is not None:
        query = query.filter(Service.rating >= min_rating)

    # 6. Filter by Stock Availability
    if available_only:
        query = query.filter(Service.stock > 0, Service.is_available == True)

    # 7. Sorting
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

    # 8. Pagination calculation
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
    return service

# =====================================================================
# 2. ADD REVIEW (UPDATES 0.0 RATING IN REAL-TIME)
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

    # Recalculate average rating dynamically
    all_reviews = db.query(ServiceReview).filter(ServiceReview.service_id == service.id).all()
    total_reviews_count = len(all_reviews) + 1
    total_rating_sum = sum([r.rating for r in all_reviews]) + review_in.rating
    new_avg_rating = round(total_rating_sum / total_reviews_count, 1)

    service.rating = new_avg_rating
    service.total_reviews = total_reviews_count

    db.commit()
    db.refresh(review)

    # Broadcast review update to all WebSocket clients
    await ws_manager.broadcast({
        "event": "NEW_REVIEW",
        "service_id": service.id,
        "new_rating": service.rating,
        "total_reviews": service.total_reviews
    })

    return review

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

    # Decrement available stock
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

    # Request Sandbox Gateway URL from SSLCommerz
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

    # Broadcast new order and updated stock via WebSocket
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
        raise HTTPException(status_code=400, detail=f"Cannot cancel order in '{order.status}' status.")

    order.status = "CANCELLED"

    # Restore stock slot
    service = db.query(Service).filter(Service.id == order.service_id).first()
    if service:
        service.stock += 1
        service.is_available = True

    db.commit()
    db.refresh(order)

    # Broadcast cancelled order and restored stock
    await ws_manager.broadcast({
        "event": "ORDER_STATUS_CHANGED",
        "order_id": order.id,
        "status": "CANCELLED",
        "service_id": service.id if service else None,
        "new_stock": service.stock if service else None
    })

    return order

@router.get("/order/history", response_model=List[OrderResponse])
def get_service_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ServiceOrder).filter(
        ServiceOrder.user_id == current_user.id
    ).order_by(ServiceOrder.id.desc()).all()

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
# 5. GEMINI AI ASSISTANT (CAN ASSIST/BOOK, CANNOT CLICK PAYMENT)
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

# =====================================================================
# 6. LIVE WEBSOCKET CONNECTION
# =====================================================================

@router.websocket("/ws")
async def service_websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)