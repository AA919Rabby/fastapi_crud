from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

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

class Msg(BaseModel):
    message: str

# Legacy schemas kept so imports never break
class ResetPassword(BaseModel):
    token: str
    new_password: str

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

# --- 3-Step Password Recovery Schemas ---

# Step 1: Request OTP
class RecoverPasswordRequest(BaseModel):
    email: EmailStr

# Step 2: Verify OTP
class RecoveryOTPVerify(BaseModel):
    email: EmailStr
    otp: str

# Step 2 Response: Returns the recovery token
class RecoverPasswordTokenResponse(BaseModel):
    message: str
    recover_password_token: str

# Step 3: Set new password with the token
class RecoverNewPasswordRequest(BaseModel):
    recover_password_token: str
    new_password: str