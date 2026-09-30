from fastapi import APIRouter, Depends, HTTPException, status, Form, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta, datetime, timezone

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.service import ServiceOrder, Service
from app.models.extensions import UserProfile, DeviceToken, Notification, ServiceSlot
from app.schemas.extensions import (
    ProfileUpdate, ProfileResponse,
    FCMTokenCreate, NotificationResponse,
    SlotResponse, PaymentInitiateRequest, PaymentInitiateResponse
)
from app.schemas.user import Msg
from app.core.sslcommerz import ssl_client
from app.core.ws_manager import ws_manager
from app.core.notification_service import trigger_notification

profile_router = APIRouter()
notifications_router = APIRouter()
payment_router = APIRouter()
slots_router = APIRouter()

# ==========================================
# 1. PROFILE SECTION
# ==========================================

def get_completed_orders_count(db: Session, user_id: int) -> int:
    return db.query(ServiceOrder).filter(
        ServiceOrder.user_id == user_id,
        ServiceOrder.status == "COMPLETED"
    ).count()

@profile_router.get("", response_model=ProfileResponse)
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    # Combined First Name + Last Name from user registration
    registered_full_name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip()
    if not registered_full_name:
        registered_full_name = current_user.email.split("@")[0]

    # If new user has no profile row yet, create it immediately with their registered data!
    if not profile:
        profile = UserProfile(
            user_id=current_user.id,
            full_name=registered_full_name,
            phone_number="",
            profile_picture_url="",
            address="Dhaka, Bangladesh"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    elif not profile.full_name or profile.full_name.strip() == "":
        profile.full_name = registered_full_name
        db.commit()
        db.refresh(profile)

    completed_count = get_completed_orders_count(db, current_user.id)
    user_created_at = current_user.created_at or datetime.now(timezone.utc)

    return {
        "id": profile.id,
        "user_id": current_user.id,
        "full_name": profile.full_name,
        "email": current_user.email,
        "phone_number": profile.phone_number or "",
        "profile_picture_url": profile.profile_picture_url or "",
        "address": profile.address or "",
        "created_at": user_created_at,
        "updated_at": profile.updated_at,
        "total_completed_services": completed_count
    }

@profile_router.put("", response_model=ProfileResponse)
async def update_user_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if data.full_name is not None:
        profile.full_name = data.full_name.strip()
    if data.phone_number is not None:
        profile.phone_number = data.phone_number.strip()
    if data.profile_picture_url is not None:
        profile.profile_picture_url = data.profile_picture_url.strip()
    if data.address is not None:
        profile.address = data.address.strip()

    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)

    await trigger_notification(
        db=db,
        user_id=current_user.id,
        title="Profile Updated",
        body="Your personal profile details were updated successfully.",
        notification_type="PROFILE"
    )

    completed_count = get_completed_orders_count(db, current_user.id)
    user_created_at = current_user.created_at or datetime.now(timezone.utc)

    await ws_manager.broadcast({
        "event": "PROFILE_UPDATED",
        "user_id": current_user.id,
        "full_name": profile.full_name,
        "profile_picture_url": profile.profile_picture_url,
        "total_completed_services": completed_count
    })

    return {
        "id": profile.id,
        "user_id": current_user.id,
        "full_name": profile.full_name,
        "email": current_user.email,
        "phone_number": profile.phone_number or "",
        "profile_picture_url": profile.profile_picture_url or "",
        "address": profile.address or "",
        "created_at": user_created_at,
        "updated_at": profile.updated_at,
        "total_completed_services": completed_count
    }

# ==========================================
# 2. NOTIFICATIONS SECTION
# ==========================================

@notifications_router.post("/device-token", response_model=Msg)
def save_fcm_token(
    data: FCMTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    token = db.query(DeviceToken).filter(DeviceToken.fcm_token == data.fcm_token).first()
    if token:
        token.user_id = current_user.id
        token.device_type = data.device_type
    else:
        token = DeviceToken(
            user_id=current_user.id,
            fcm_token=data.fcm_token,
            device_type=data.device_type
        )
        db.add(token)

    db.commit()
    return {"message": "FCM device token registered successfully."}

@notifications_router.get("", response_model=List[NotificationResponse])
def get_notifications_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.id.desc()).all()

@notifications_router.patch("/{notification_id}/read", response_model=Msg)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}

# ==========================================
# 3. PAYMENT SECTION
# ==========================================

@payment_router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    data: PaymentInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(ServiceOrder).filter(
        ServiceOrder.id == data.order_id,
        ServiceOrder.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.payment_status == "PAID":
        raise HTTPException(status_code=400, detail="This order has already been paid.")

    service = db.query(Service).filter(Service.id == order.service_id).first()
    service_title = service.title if service else "Service Booking"

    ssl_res = await ssl_client.init_payment(
        tran_id=order.tran_id,
        total_amount=order.total_amount,
        cus_name=current_user.email.split("@")[0],
        cus_email=current_user.email,
        cus_phone=order.customer_phone,
        cus_address=order.service_address,
        service_title=service_title
    )

    if ssl_res.get("status") != "SUCCESS" or not ssl_res.get("GatewayPageURL"):
        error_msg = ssl_res.get("failedreason") or ssl_res.get("message") or "Gateway initiation failed."
        raise HTTPException(status_code=400, detail=f"SSLCommerz error: {error_msg}")

    order.payment_session_url = ssl_res.get("GatewayPageURL")
    db.commit()

    return {
        "tran_id": order.tran_id,
        "payment_url": order.payment_session_url
    }

@payment_router.post("/ipn")
async def payment_ipn(
    tran_id: str = Form(...),
    val_id: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    amount: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    order = db.query(ServiceOrder).filter(ServiceOrder.tran_id == tran_id).first()
    if not order:
        return {"status": "FAILED", "message": "Order not found for tran_id"}

    if status in ["VALID", "VALIDATED"]:
        if val_id:
            validation_res = await ssl_client.validate_transaction(val_id)
            if validation_res.get("status") not in ["VALID", "VALIDATED"]:
                order.payment_status = "FAILED"
                db.commit()
                return {"status": "FAILED", "message": "Validation signature failed"}

        order.payment_status = "PAID"
        order.status = "PROCESSING"
        db.commit()

        await trigger_notification(
            db=db,
            user_id=order.user_id,
            title="Payment Confirmed (IPN)",
            body=f"Your payment of {order.total_amount} BDT for transaction {order.tran_id} was confirmed via SSLCommerz.",
            notification_type="PAYMENT"
        )
        return {"status": "SUCCESS", "message": "Payment verified via IPN"}
    else:
        order.payment_status = "FAILED"
        db.commit()

        await trigger_notification(
            db=db,
            user_id=order.user_id,
            title="Payment Failed",
            body=f"Payment for transaction {order.tran_id} could not be completed.",
            notification_type="PAYMENT"
        )
        return {"status": "FAILED", "message": f"Payment status {status}"}

# ==========================================
# 4. SLOTS / SCHEDULE SECTION
# ==========================================

@slots_router.get("", response_model=List[SlotResponse])
def get_available_slots(
    service_id: int,
    slot_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    target_date = slot_date or (datetime.now(timezone.utc).date() + timedelta(days=1))

    existing = db.query(ServiceSlot).filter(
        ServiceSlot.service_id == service_id,
        ServiceSlot.slot_date == target_date
    ).all()

    if not existing:
        time_windows = [
            ("09:00 AM", "11:00 AM"),
            ("11:30 AM", "01:30 PM"),
            ("03:00 PM", "05:00 PM"),
            ("05:30 PM", "07:30 PM")
        ]
        created = []
        for start_t, end_t in time_windows:
            s = ServiceSlot(
                service_id=service_id,
                slot_date=target_date,
                start_time=start_t,
                end_time=end_t,
                is_booked=False
            )
            db.add(s)
            created.append(s)
        db.commit()
        return created

    return existing

@slots_router.websocket("/ws")
async def slot_websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)