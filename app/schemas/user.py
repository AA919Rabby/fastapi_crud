from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True

class UserRegistrationResponse(BaseModel):
    message: str
    user: UserResponse

class UserLoginJSON(BaseModel):
    email: EmailStr
    password: str

class Msg(BaseModel):
    message: str

# Schema allowing Flutter Web/Mobile to send clean JSON for Login
class LoginJSONRequest(BaseModel):
    email: EmailStr
    password: str

# Legacy schemas kept to prevent import errors in older files
class ResetPassword(BaseModel):
    token: str
    new_password: str

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

# Password recovery schemas
class RecoverPasswordRequest(BaseModel):
    email: EmailStr

class RecoverPasswordResponse(BaseModel):
    message: str
    otp: Optional[str] = None

class RecoveryOTPVerify(BaseModel):
    email: EmailStr
    otp: str

class RecoverPasswordTokenResponse(BaseModel):
    message: str
    recover_password_token: str

class RecoverNewPasswordRequest(BaseModel):
    recover_password_token: str
    new_password: str