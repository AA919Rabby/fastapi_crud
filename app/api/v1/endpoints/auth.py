from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

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
    RecoverPasswordRequest,
    RecoveryOTPVerify,
    RecoverPasswordTokenResponse,
    RecoverNewPasswordRequest,
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

# 1. Send OTP to Email
@router.post("/recover_password", response_model=Msg)
def recover_password(data: RecoverPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=data.email)
    if not user:
        return {"message": "If this email is registered, an OTP code has been sent."}

    otp = generate_and_save_otp(db, user)
    send_otp_email(recipient_email=user.email, otp_code=otp)
    return {"message": "OTP has been sent to your email."}

# 2. Verify OTP only -> Returns recover_password_token
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

    # Generate the recovery token
    token = create_recover_password_token(email=user.email)
    return {
        "message": "OTP verified successfully.",
        "recover_password_token": token
    }

# 3. Enter new password with recover_password_token
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