from sqlalchemy.orm import Session
from app.models.extensions import Notification, DeviceToken
from app.core.ws_manager import ws_manager

async def trigger_notification(
    db: Session,
    user_id: int,
    title: str,
    body: str,
    notification_type: str = "GENERAL"
) -> Notification:
    # 1. Store in database
    notif = Notification(
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # 2. Check for registered device tokens (FCM)
    tokens = db.query(DeviceToken).filter(DeviceToken.user_id == user_id).all()
    if tokens:
        print(f">>> [FCM PUSH] Sending to {len(tokens)} devices: {title} | {body}")

    # 3. Live WebSocket broadcast
    await ws_manager.broadcast({
        "event": "NEW_NOTIFICATION",
        "user_id": user_id,
        "notification_id": notif.id,
        "title": title,
        "body": body,
        "type": notification_type
    })

    return notif