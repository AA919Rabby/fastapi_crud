from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.email import send_otp_email
from app.crud.crud_user import (
    get_user_by_email,
    create_user,
    generate_and_save_otp,
    verify_otp_and_reset_password
)
from app.schemas.token import Token
from app.schemas.user import (
    UserCreate,
    UserRegistrationResponse,
    Msg,
    RecoverPasswordRequest,
    RecoveryOTPVerify
)

router = APIRouter()

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

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/recover_password", response_model=Msg)
def recover_password(data: RecoverPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=data.email)
    if not user:
        # Avoid user enumeration (or raise 404 if you prefer explicit feedback)
        return {"message": "If this email is registered, an OTP code has been sent."}

    otp = generate_and_save_otp(db, user)
    send_otp_email(recipient_email=user.email, otp_code=otp)

    return {"message": "OTP has been sent to your email."}

@router.post("/recovery_otp_verify", response_model=Msg)
def recovery_otp_verify(data: RecoveryOTPVerify, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request"
        )

    success = verify_otp_and_reset_password(
        db=db,
        user=user,
        otp=data.otp,
        new_password=data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    return {"message": "Password changed successfully. You can now login with your new password."}