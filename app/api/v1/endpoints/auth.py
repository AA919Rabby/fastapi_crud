from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_recover_password_token,
    verify_recover_password_token,
)
from app.core.email import send_otp_email
from app.crud.crud_user import (
    get_user_by_email,
    create_user,
    generate_and_save_otp,
    verify_only_otp,
    update_user_password,
)
from app.schemas.token import Token
from app.schemas.user import (
    UserCreate,
    UserRegistrationResponse,
    Msg,
    LoginJSONRequest,
    RecoverPasswordRequest,
    RecoverPasswordResponse,
    RecoveryOTPVerify,
    RecoverPasswordTokenResponse,
    RecoverNewPasswordRequest,
)

router = APIRouter()

# 1. Registration with first_name & last_name
@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system."
        )
    user = create_user(db, user=user_in)
    return {"message": "User registered successfully", "user": user}

# 2. Universal Login: Handles BOTH JSON (Flutter Chrome/iOS/Android) AND Form Data (Swagger)
@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    email = None
    password = None

    # Check if request is JSON (Flutter standard) or Form Data (Swagger UI)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email") or body.get("username")
        password = body.get("password")
    else:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both email and password are required."
        )

    user = get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

# 3. Recover Password with OTP
@router.post("/recover_password", response_model=RecoverPasswordResponse)
def recover_password(data: RecoverPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email address not found in our records."
        )

    otp = generate_and_save_otp(db, user)
    send_otp_email(recipient_email=user.email, otp_code=otp)
    return {
        "message": "OTP has been sent to your email.",
        "otp": otp
    }

# 4. Verify OTP
@router.post("/recovery_otp_verify", response_model=RecoverPasswordTokenResponse)
def recovery_otp_verify(data: RecoveryOTPVerify, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or request."
        )

    is_valid = verify_only_otp(db=db, user=user, otp=data.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP."
        )

    token = create_recover_password_token(email=user.email)
    return {
        "message": "OTP verified successfully.",
        "recover_password_token": token
    }

# 5. Set New Password
@router.post("/recover_new_password", response_model=Msg)
def recover_new_password(data: RecoverNewPasswordRequest, db: Session = Depends(get_db)):
    email = verify_recover_password_token(data.recover_password_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired recovery token."
        )

    user = get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    update_user_password(db=db, db_user=user, new_password=data.new_password)
    return {"message": "Password changed successfully. You can now login with your new password."}