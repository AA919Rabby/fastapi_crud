from fastapi import APIRouter
from app.api.v1.endpoints import auth, services
from app.api.v1.endpoints.extensions import (
    profile_router,
    notifications_router,
    payment_router,
    slots_router
)

api_router = APIRouter()

# 1. Users & Authentication
api_router.include_router(auth.router, prefix="/users", tags=["users"])

# 2. Services Marketplace
api_router.include_router(services.router, prefix="/services", tags=["services"])

# 3. Profile
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])

# 4. Notifications
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])

# 5. Payment
api_router.include_router(payment_router, prefix="/payment", tags=["payment"])

# 6. Slots / Schedule
api_router.include_router(slots_router, prefix="/slots", tags=["slots"])